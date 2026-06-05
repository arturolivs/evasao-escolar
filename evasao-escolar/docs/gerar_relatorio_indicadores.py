"""
Gera o relatório DOCX da Fase 2 — ETL e análises dos indicadores complementares.
Execução: python docs/gerar_relatorio_indicadores.py
Saída: docs/relatorio_indicadores_complementares.docx
"""

from __future__ import annotations
from pathlib import Path
from datetime import date

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOCS_DIR   = Path(__file__).resolve().parent
OUTPUT     = DOCS_DIR / "relatorio_indicadores_complementares.docx"
FIGURAS    = DOCS_DIR.parent / "reports" / "figuras"


# ---------------------------------------------------------------------------
# Helpers de formatação
# ---------------------------------------------------------------------------

def _set_cell_bg(cell, hex_color: str) -> None:
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)


def heading(doc: Document, text: str, level: int) -> None:
    doc.add_heading(text, level=level)


def body(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.style.font.size = Pt(11)


def bullet(doc: Document, text: str, level: int = 0) -> None:
    p = doc.add_paragraph(text, style="List Bullet")
    p.style.font.size = Pt(11)
    if level > 0:
        p.paragraph_format.left_indent = Cm(level * 0.75)


def table_header(doc: Document, headers: list[str], widths_cm: list[float],
                 header_color: str = "1F4E79") -> object:
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, (h, w) in enumerate(zip(headers, widths_cm)):
        hdr[i].text = h
        hdr[i].width = Cm(w)
        _set_cell_bg(hdr[i], header_color)
        run = hdr[i].paragraphs[0].runs[0]
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(9)
    return t


def table_row(t, values: list[str]) -> None:
    row = t.add_row().cells
    for i, v in enumerate(values):
        row[i].text = v
        row[i].paragraphs[0].runs[0].font.size = Pt(9)


def add_figure(doc: Document, filename: str, caption: str, width_cm: float = 15.0) -> None:
    path = FIGURAS / filename
    if path.exists():
        doc.add_picture(str(path), width=Cm(width_cm))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(caption)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].italic = True
        p.runs[0].font.size = Pt(9)
    else:
        body(doc, f"[Figura não encontrada: {filename}]")


# ---------------------------------------------------------------------------
# Construção do documento
# ---------------------------------------------------------------------------

def build() -> None:
    doc = Document()

    # Margens
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.0)

    # ── Capa ────────────────────────────────────────────────────────────────
    doc.add_heading("Relatório Técnico — Fase 2", 0)
    doc.add_heading("ETL e Análises Descritivas dos Indicadores Complementares", 1)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for label, valor in [
        ("Versão",  "1.0"),
        ("Data",    date.today().strftime("%Y-%m-%d")),
        ("Escopo",  "ETL de IRD, INSE, TDI e AFD + análises descritivas (C1–C6)"),
        ("Fontes",  "INEP — Microdados indicadores complementares da Educação Básica"),
        ("Saídas",  "data/interim/{ird,inse,tdi,afd}_pe_estadual.parquet · reports/figuras/C*.png"),
    ]:
        run = meta.add_run(f"{label}: ")
        run.bold = True
        run.font.size = Pt(11)
        run2 = meta.add_run(f"{valor}\n")
        run2.font.size = Pt(11)

    doc.add_page_break()

    # ── 1. Contexto ──────────────────────────────────────────────────────────
    heading(doc, "1. Contexto e motivação", 1)
    body(doc,
         "A Fase 1 do projeto (EDA do Censo Escolar) produziu um painel de 806 escolas "
         "estaduais de EM em PE com features de infraestrutura, porte e localização. "
         "Para construir um modelo preditivo de evasão com poder explicativo real, "
         "é necessário incorporar indicadores que descrevam a qualidade do corpo docente "
         "e o perfil socioeconômico dos alunos — dimensões não cobertas pelo Censo.")
    body(doc,
         "Esta fase adiciona quatro indicadores do INEP: Indicador de Regularidade do "
         "Docente (IRD), Nível Socioeconômico (INSE), Taxa de Distorção Idade-série (TDI) "
         "e Adequação da Formação Docente (AFD). Cada um recebeu um módulo ETL independente "
         "e foi analisado descritivamente antes de entrar no pipeline de feature engineering.")

    # ── 2. Arquitetura do pipeline ────────────────────────────────────────────
    heading(doc, "2. Alterações na arquitetura do pipeline", 1)

    heading(doc, "2.1 Refatoração do config.py — pasta única do Censo", 2)
    body(doc,
         "A estrutura anterior usava uma subpasta por ano (censo_2022/, censo_2023/, censo_2024/). "
         "Com a consolidação dos arquivos em uma única pasta censo/, o config.py foi atualizado:")
    bullet(doc, "CENSO_DIR = RAW_DIR / 'censo'  — nova constante para a pasta única")
    bullet(doc, "CENSO_DIRS = {ano: CENSO_DIR for ano in [2022, 2023, 2024]}  — mantém compatibilidade com load.py sem quebrar a API")
    body(doc,
         "A função _resolver_caminho_csv_escola() em load.py não precisou de alteração: "
         "ela já busca pelo template microdados_ed_basica_{ano}.csv dentro da pasta informada, "
         "que agora é sempre a mesma para todos os anos.")

    heading(doc, "2.2 Novos caminhos em config.py", 2)
    body(doc, "Foram adicionadas quatro constantes de caminho para os novos indicadores:")
    t = table_header(doc,
                     ["Constante", "Caminho", "Indicador"],
                     [4.5, 7.0, 4.5])
    for row in [
        ("IRD_DIR",  "data/raw/indicador_regularidade_docente/", "IRD"),
        ("INSE_DIR", "data/raw/inse/",                           "INSE"),
        ("TDI_DIR",  "data/raw/taxa_distorcao_idade/",           "TDI"),
        ("AFD_DIR",  "data/raw/adequacao_formacao_docente/",     "AFD"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()

    heading(doc, "2.3 Módulos ETL criados", 2)
    t = table_header(doc,
                     ["Módulo", "Saída parquet", "Linhas", "Escolas únicas"],
                     [5.5, 6.0, 2.0, 3.0])
    for row in [
        ("src/data/build_ird.py",  "ird_pe_estadual.parquet",  "3.110", "1.044"),
        ("src/data/build_inse.py", "inse_pe_estadual.parquet",   "874",   "874"),
        ("src/data/build_tdi.py",  "tdi_pe_estadual.parquet",  "2.366",   "797"),
        ("src/data/build_afd.py",  "afd_pe_estadual.parquet",  "2.392",   "806"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()

    # ── 3. ETL por indicador ─────────────────────────────────────────────────
    heading(doc, "3. Decisões de ETL por indicador", 1)

    # 3.1 IRD
    heading(doc, "3.1 IRD — Indicador de Regularidade do Docente", 2)
    body(doc,
         "Arquivos: IRD_ESCOLAS_{2022,2023,2024}.xlsx. "
         "Estrutura: 10 linhas de cabeçalho institucional antes dos dados reais "
         "(header=10 no pandas).")
    body(doc, "Decisões:")
    bullet(doc, "Filtro: SG_UF == 'PE' e NO_DEPENDENCIA == 'Estadual'. Mesma lógica dos módulos anteriores.")
    bullet(doc, "Coluna relevante: EDU_BAS_CAT_0 → renomeada para IRD_MED. "
                "O IRD é calculado sobre toda a educação básica da escola, sem desagregação por etapa.")
    bullet(doc, "Sem filtro de EM no ETL: o IRD cobre todas as etapas; "
                "o filtro para escolas com EM ocorre no join com o painel. "
                "Por isso o painel IRD tem 1.044 escolas vs. 806 do Censo EM.")
    bullet(doc, "Sentinel '--' tratado como NaN; nenhum registro apresentou missings na coluna IRD_MED.")

    # 3.2 INSE
    heading(doc, "3.2 INSE — Nível Socioeconômico", 2)
    body(doc,
         "Situação dos arquivos: o INSE é calculado nos ciclos do SAEB (bienal). "
         "Apenas o arquivo escola-level de 2021 (INSE_2021_escolas.xlsx) está disponível. "
         "O arquivo 2023 baixado (INSE_2023_estados.xlsx) é agregado por estado e "
         "não possui granularidade escolar — portanto não foi utilizado.")
    body(doc, "Decisões:")
    bullet(doc, "Header: o arquivo 2021 já inicia com nomes de colunas na linha 0 (header=0).")
    bullet(doc, "Filtro: SG_UF == 'PE' e TP_TIPO_REDE == 2 (estadual no SAEB).")
    bullet(doc, "Coluna de identificação: ID_ESCOLA → renomeada para CO_ENTIDADE "
                "para compatibilidade com o painel do Censo.")
    bullet(doc, "INSE_CLASSIFICACAO contém texto ('Nível IV') — tratado como string "
                "(INSE_NIVEL), sem conversão numérica. Os demais campos são convertidos para float.")
    bullet(doc, "Uso no modelo: INSE de 2021 como atributo estático para todos os anos do painel "
                "(2022–2024). Cobertura: 94,8% das 806 escolas do painel EM.")
    bullet(doc, "Colunas exportadas: INSE_MEDIA, INSE_NIVEL, INSE_QTD_ALUNOS e percentuais por nível (PC_NIVEL_1 a 8).")

    # 3.3 TDI
    heading(doc, "3.3 TDI — Taxa de Distorção Idade-série", 2)
    body(doc,
         "Arquivos: TDI_ESCOLAS_{2022,2023,2024}.xlsx. "
         "Estrutura: 8 linhas de cabeçalho (header=8).")
    body(doc, "Decisões:")
    bullet(doc, "Colunas selecionadas: apenas as de Ensino Médio — "
                "MED_CAT_0 (total EM), MED_01_CAT_0 a MED_03_CAT_0 (séries 1–3) e "
                "MED_04_CAT_0 (4ª série, para escolas de educação profissional integrada).")
    bullet(doc, "Renomeação: MED_CAT_0 → TDI_MED; MED_0x_CAT_0 → TDI_MED_Sx.")
    bullet(doc, "Filtro de EM: escolas com TDI_MED nulo (sentinel '--') foram removidas. "
                "Isso exclui as ~237 escolas estaduais que não ofertam EM presentes no arquivo nacional.")
    bullet(doc, "MED_04_CAT_0 (S4): disponível mas com 98,3% de missing — "
                "mantida no parquet para rastreabilidade; não será usada como feature.")

    # 3.4 AFD
    heading(doc, "3.4 AFD — Adequação da Formação Docente", 2)
    body(doc,
         "Arquivos: AFD_ESCOLAS_{2022,2023,2024}.xlsx. "
         "Estrutura: 10 linhas de cabeçalho (header=10). "
         "O arquivo é o mais amplo dos quatro — cada escola tem 44 colunas de grupos "
         "por etapa/modalidade; foram selecionadas apenas as 5 colunas de Ensino Médio.")
    body(doc, "Decisões:")
    bullet(doc, "Colunas selecionadas: MED_CAT_1 a MED_CAT_5 → AFD_MED_G1 a AFD_MED_G5.")
    bullet(doc, "Semântica dos grupos: G1 = licenciatura na disciplina (ideal); "
                "G2 = bacharelado na área sem licença; G3 = licenciatura em outra área; "
                "G4 = outra formação superior; G5 = sem ensino superior.")
    bullet(doc, "Filtro de EM: escolas com todos os grupos nulos foram removidas "
                "(mesma lógica do TDI). Resultado: 800/801/791 escolas por ano, "
                "alinhado com o painel do Censo.")
    bullet(doc, "Sem missing nas colunas de EM após a remoção das escolas sem oferta.")

    # ── 4. Análises descritivas ──────────────────────────────────────────────
    heading(doc, "4. Análises descritivas — Notebook 04", 1)
    body(doc,
         "O notebook notebooks/04_analises_indicadores.py executa 6 análises (C1–C6) "
         "que cobrem distribuição, evolução temporal, disparidade urbana/rural, "
         "correlação com abandono e perfil de risco composto por município.")

    # C1
    heading(doc, "C1 — IRD: Regularidade do Corpo Docente", 2)
    t = table_header(doc, ["Ano", "N", "Média", "Mediana", "DP", "Mín", "Máx"],
                     [1.5, 1.5, 2.0, 2.0, 2.0, 1.5, 1.5])
    for row in [
        ("2022", "1.034", "3,352", "3,296", "0,612", "1,6", "5,0"),
        ("2023", "1.037", "3,462", "3,425", "0,556", "1,7", "5,0"),
        ("2024", "1.039", "3,438", "3,422", "0,535", "1,6", "5,0"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    body(doc,
         "IRD cresceu de 3,35 → 3,44 entre 2022 e 2024, indicando leve melhora na "
         "estabilidade do corpo docente. Escolas rurais apresentam IRD significativamente "
         "maior que urbanas (3,62 vs. 3,36, Mann-Whitney p<0,001) — resultado contraintuitivo "
         "que pode refletir menor rotatividade em municípios com poucas alternativas de emprego "
         "para docentes, ou perfil diferente de contratação nas escolas rurais da rede estadual.")
    add_figure(doc, "C1_ird.png", "Figura C1 — Distribuição, evolução e disparidade urbana/rural do IRD")

    # C2
    heading(doc, "C2 — INSE: Nível Socioeconômico", 2)
    body(doc,
         "Cobertura: 764 das 806 escolas do painel EM têm INSE (94,8%). "
         "As 42 escolas sem cobertura são provavelmente novas ou com turmas muito pequenas "
         "para o cálculo do SAEB. A distribuição é concentrada nos níveis III e IV (91,6%), "
         "consistente com o perfil socioeconômico da rede estadual pernambucana.")
    t = table_header(doc, ["Nível INSE", "N", "%", "Interpretação"],
                     [2.5, 1.5, 1.5, 10.0])
    for row in [
        ("Nível I",   "1",   "0,1%", "Muito baixo"),
        ("Nível II",  "43",  "4,9%", "Baixo"),
        ("Nível III", "380", "43,5%","Médio-baixo"),
        ("Nível IV",  "420", "48,1%","Médio"),
        ("Nível V",   "27",  "3,1%", "Médio-alto"),
        ("Nível VI–VII", "3","0,3%", "Alto / Muito alto"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    body(doc,
         "Escolas urbanas têm INSE médio 0,24 pontos acima das rurais (4,51 vs. 4,28, p<0,001). "
         "A variável será usada como atributo estático no feature engineering — o INSE de 2021 "
         "serve de proxy para todos os anos do painel, assumindo estabilidade socioeconômica "
         "relativa entre escolas ao longo de 3 anos.")
    add_figure(doc, "C2_inse.png", "Figura C2 — Distribuição do INSE, frequência por nível e comparação urbana/rural")

    # C3
    heading(doc, "C3 — TDI: Taxa de Distorção Idade-série", 2)
    t = table_header(doc, ["Ano", "N", "Média", "Mediana", "DP", "Kruskal-Wallis"],
                     [1.5, 1.5, 2.0, 2.0, 2.0, 4.0])
    for row in [
        ("2022", "788", "24,1%", "22,2%", "13,6", "—"),
        ("2023", "789", "22,5%", "20,6%", "12,4", "H=16,32"),
        ("2024", "789", "21,6%", "19,9%", "11,9", "p=0,0003"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    body(doc,
         "A TDI caiu de forma consistente e estatisticamente significativa — queda de 2,5 pp "
         "em 3 anos. A 1ª série concentra a maior distorção (25,0% em 2024) e a 3ª série "
         "a menor (16,9%), padrão esperado: alunos com distorção tendem a evadir antes de "
         "chegar às séries finais. Escolas rurais têm TDI 12,4 pp acima das urbanas "
         "(32,3% vs. 19,9%, p<0,001), a segunda maior disparidade encontrada nos indicadores.")
    add_figure(doc, "C3_tdi.png", "Figura C3 — Distribuição da TDI, evolução urbana/rural e comparação por série")

    # C4
    heading(doc, "C4 — AFD: Adequação da Formação Docente", 2)
    t = table_header(doc, ["Grupo", "Significado", "2022", "2023", "2024"],
                     [1.5, 6.5, 2.0, 2.0, 2.0])
    for row in [
        ("G1", "Licenciatura na disciplina (ideal)", "52,6%", "55,5%", "61,9%"),
        ("G2", "Bacharelado na área (sem licença)",   "0,8%",  "0,9%",  "1,0%"),
        ("G3", "Licenciatura em outra área",          "41,6%", "38,9%", "31,8%"),
        ("G4", "Outra formação superior",              "2,0%",  "2,1%",  "2,0%"),
        ("G5", "Sem ensino superior",                  "3,0%",  "2,6%",  "3,3%"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    body(doc,
         "O G1 cresceu 9,3 pp em 3 anos — tendência positiva relevante para a rede. "
         "A disparidade urbana/rural no G1 é a maior encontrada nos quatro indicadores: "
         "65,0% (urbana) vs. 43,3% (rural), diferença de 21,7 pp (p<0,001). "
         "Escolas rurais têm proporcionalmente mais docentes com licenciatura fora da "
         "disciplina (G3), refletindo dificuldade de atrair especialistas para municípios pequenos.")
    add_figure(doc, "C4_afd.png", "Figura C4 — Composição dos grupos AFD, evolução do G1 e distribuição 2024")

    # C5
    heading(doc, "C5 — Correlações com a taxa de abandono", 2)
    body(doc,
         "Base: 2.392 observações (escola × ano, join entre taxas de rendimento e "
         "indicadores). INSE foi vinculado apenas por CO_ENTIDADE (sem ano), "
         "resultando em 2.271 pares válidos.")
    t = table_header(doc,
                     ["Indicador", "r Spearman", "p-valor", "N", "Interpretação"],
                     [3.5, 2.5, 2.0, 1.5, 6.0])
    for row in [
        ("TDI_MED",    "+0,300", "<0,001", "2.366", "Maior distorção → mais abandono (mais forte)"),
        ("AFD_MED_G5", "+0,239", "<0,001", "2.392", "Mais docentes sem superior → mais abandono"),
        ("AFD_MED_G1", "−0,169", "<0,001", "2.392", "Melhor formação → menos abandono"),
        ("INSE_MEDIA",  "−0,141", "<0,001", "2.271", "Melhor INSE → menos abandono"),
        ("IRD_MED",    "+0,047",  "0,022",  "2.370", "Correlação fraca — interpretar com cautela"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    body(doc,
         "TDI e AFD_G5 têm as correlações mais fortes com abandono. O IRD apresenta "
         "correlação estatisticamente significativa mas com magnitude baixa (r=0,05) — "
         "pode ser que o indicador capture regularidade em toda a escola, diluindo o "
         "efeito específico sobre o EM. A combinação TDI + AFD_G1 + INSE representa "
         "o trio de maior potencial preditivo entre os novos indicadores.")
    add_figure(doc, "C5_correlacoes.png", "Figura C5 — Scatter plots dos indicadores vs. taxa de abandono")

    # C6
    heading(doc, "C6 — Perfil de risco composto por município (2024)", 2)
    body(doc,
         "Foi criado um índice de risco composto para os 78 municípios com pelo menos "
         "3 escolas estaduais de EM. O índice agrega, com pesos iguais, quatro dimensões "
         "normalizadas [0,1]: abandono médio, TDI média, (1 − IRD normalizado) e "
         "(1 − INSE normalizado). Score final = média simples das 4 dimensões.")
    t = table_header(doc,
                     ["Município", "N esc.", "Abandono", "TDI", "IRD", "INSE", "Score"],
                     [4.0, 1.5, 2.0, 1.5, 1.5, 1.5, 1.5])
    for row in [
        ("Floresta",              "10", "10,22%", "49,11%", "2,99", "4,14", "0,80"),
        ("Itacuruba",              "3",  "4,83%", "47,47%", "3,67", "4,40", "0,50"),
        ("Carnaubeira da Penha",  "11",  "4,61%", "39,31%", "4,07", "4,02", "0,49"),
        ("Buíque",                 "7",  "1,50%", "33,71%", "3,57", "3,98", "0,45"),
        ("Tacaratu",               "8",  "4,21%", "40,07%", "4,06", "4,17", "0,45"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    body(doc,
         "Floresta se destaca com o maior score (0,80) puxado pela combinação de "
         "abandono elevado (10,22%) e TDI altíssima (49,11%). Os demais municípios "
         "de alto risco têm abandono individual baixo mas TDI estruturalmente alta — "
         "sinal de vulnerabilidade latente não capturada apenas pelo abandono.")
    add_figure(doc, "C6_risco_composto.png", "Figura C6 — Top 15 municípios de risco e scatter abandono × INSE")

    # ── 5. Limitações ────────────────────────────────────────────────────────
    heading(doc, "5. Limitações e pontos de atenção", 1)
    bullet(doc, "INSE disponível apenas para 2021 (escola-level). "
                "O arquivo 2023 baixado é estado-level e não foi utilizado. "
                "Recomenda-se baixar o INSE_2023_escolas.xlsx do site do INEP para "
                "ter dados mais recentes.")
    bullet(doc, "IRD cobre a educação básica integralmente, sem desagregação por etapa. "
                "Escolas com EM e EF podem ter o IRD 'diluído' por docentes de séries "
                "iniciais, reduzindo a precisão do indicador para o EM especificamente.")
    bullet(doc, "TDI_MED_S4 (4ª série) tem 98,3% de missing — "
                "manter no parquet por rastreabilidade mas excluir do feature engineering.")
    bullet(doc, "Correlações da análise C5 são bivariadas. "
                "Efeitos de confundimento (ex.: INSE e TDI são altamente correlacionados "
                "entre si) só serão resolvidos no modelo multivariado.")
    bullet(doc, "IRD com correlação fraca (r=0,05) com abandono. "
                "Avaliar descarte no feature engineering após teste de importância no XGBoost.")

    # ── 6. Próximos passos ────────────────────────────────────────────────────
    heading(doc, "6. Próximos passos", 1)
    t = table_header(doc, ["Prioridade", "Ação", "Arquivo"],
                     [2.5, 9.5, 4.5])
    for row in [
        ("ALTA",  "Feature engineering: criar lags t-1 de TDI e AFD_G1",       "Notebook 05"),
        ("ALTA",  "Incorporar INSE como feature estática (join por CO_ENTIDADE)", "Notebook 05"),
        ("ALTA",  "Construir dataset final (painel + target + todos indicadores)", "build_target.py"),
        ("MÉDIA", "Baixar INSE_2023_escolas.xlsx para ampliar cobertura temporal", "data/raw/inse/"),
        ("MÉDIA", "Avaliar descarte de IRD_MED após análise de importância",      "Notebook 05"),
        ("BAIXA", "Excluir TDI_MED_S4 (98,3% missing) do feature set",           "Notebook 05"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()

    # ── Salvar ───────────────────────────────────────────────────────────────
    doc.save(OUTPUT)
    print(f"Relatório salvo em: {OUTPUT}")


if __name__ == "__main__":
    build()
