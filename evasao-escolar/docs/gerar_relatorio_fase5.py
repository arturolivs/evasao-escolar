"""
Gera o relatório DOCX da Fase 5 — Baselines de modelagem (Ridge e Random Forest).
Execução: python docs/gerar_relatorio_fase5.py
Saída: docs/relatorio_fase5_baselines.docx
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

DOCS_DIR = Path(__file__).resolve().parent
OUTPUT   = DOCS_DIR / "relatorio_fase5_baselines.docx"
FIGURAS  = DOCS_DIR.parent / "reports" / "figuras"


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
    doc.add_heading("Relatório Técnico — Fase 5", 0)
    doc.add_heading("Baselines de Modelagem: Ridge e Random Forest", 1)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for label, valor in [
        ("Versão",  "1.1"),
        ("Data",    date.today().strftime("%Y-%m-%d")),
        ("Escopo",  "Pipelines sklearn, validação cruzada agrupada, transformações de target, "
                    "validação temporal, análise de resíduos e avaliação complementar da "
                    "metodologia (M1–M8)"),
        ("Entrada", "data/processed/features.parquet (1.586 obs × 38 features + target)"),
        ("Saídas",  "src/models/{train,evaluate}.py · notebooks/06_baseline_modelos.py · "
                    "notebooks/07_avaliacao_complementar.py · reports/metricas_*.csv · "
                    "reports/residuos_top20_temporal.csv · models/baseline_ridge_v1.joblib · "
                    "reports/figuras/M*.png"),
    ]:
        run = meta.add_run(f"{label}: ")
        run.bold = True
        run.font.size = Pt(11)
        run2 = meta.add_run(f"{valor}\n")
        run2.font.size = Pt(11)

    doc.add_page_break()

    # ── 1. Contexto ──────────────────────────────────────────────────────────
    heading(doc, "1. Contexto e objetivo da fase", 1)
    body(doc,
         "A Fase 3 (feature engineering) produziu o dataset final de modelagem com 1.586 "
         "observações (escola × ano-feature), 38 features e o target taxa_abandono_t1 — "
         "a taxa de abandono do EM observada no ano seguinte ao das features. A Fase 5 "
         "inaugura a etapa de modelagem: treinar e avaliar modelos de referência (baselines) "
         "que estabelecem o patamar de desempenho que o XGBoost (Fase 6) precisará superar.")
    body(doc,
         "Conforme a metodologia (decisoes_projeto.md, seções 4.1 e 8), os baselines são a "
         "Regressão Ridge (linear) e o Random Forest (não-linear), acompanhados de um "
         "DummyRegressor (prediz a média do treino) como piso trivial de referência. "
         "O problema é de regressão: prever a taxa contínua de abandono em pontos percentuais.")

    # ── 2. Módulos implementados ─────────────────────────────────────────────
    heading(doc, "2. Módulos implementados", 1)

    t = table_header(doc,
                     ["Arquivo", "Responsabilidade"],
                     [6.5, 9.5])
    for row in [
        ("src/models/evaluate.py",
         "Métricas (RMSE, MAE, R², Spearman, Precision@K) e loop de validação "
         "cruzada agrupada (GroupKFold por município)"),
        ("src/models/train.py",
         "Carga do dataset, pipelines de pré-processamento + modelo, grades de "
         "hiperparâmetros, transformações de target, split temporal e serialização"),
        ("notebooks/06_baseline_modelos.py",
         "Script de análise M1–M4: executa comparações, gera figuras, registra "
         "métricas em CSV e serializa o melhor baseline"),
        ("notebooks/07_avaliacao_complementar.py",
         "Script de análise M5–M8: cobre os itens da metodologia não contemplados "
         "pelo notebook 06 (ranking flexível, erro padrão via CV repetida, avaliação "
         "binarizada pós-hoc e top-20 resíduos)"),
        ("tests/test_models.py",
         "13 testes unitários: precision@K, não-vazamento de grupos na CV, "
         "split temporal e escala das predições com target transformado"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()

    heading(doc, "2.1 src/models/evaluate.py — métricas e validação", 2)
    body(doc, "Funções principais:")
    bullet(doc, "precision_at_k(y_true, y_pred, k): das K observações com maior valor predito, "
                "quantas estão entre as K com maior valor real. Mede diretamente a utilidade do "
                "modelo para o caso de uso de priorização (ranking top-K de escolas em risco). "
                "K = 10% do conjunto avaliado.")
    bullet(doc, "calcular_metricas(): consolida RMSE, MAE, R², correlação de Spearman e "
                "Precision@K, sempre na escala original do target (pontos percentuais).")
    bullet(doc, "validacao_cruzada_grupos(): loop manual de GroupKFold com 5 folds, agrupado por "
                "CO_MUNICIPIO. O modelo é clonado e re-treinado em cada fold; o loop manual (em vez "
                "de cross_validate) permite calcular Spearman e Precision@K por fold na escala original.")
    body(doc,
         "O agrupamento por município na validação cruzada implementa a mitigação de "
         "autocorrelação espacial prevista na metodologia: escolas do mesmo município nunca "
         "aparecem simultaneamente em treino e teste, evitando métricas otimistas por "
         "vazamento de contexto local. Os 185 municípios do dataset são distribuídos entre os folds.")

    heading(doc, "2.2 src/models/train.py — pipelines e preparação", 2)
    body(doc, "Decisões de pré-processamento (sklearn ColumnTransformer):")
    bullet(doc, "Features numéricas (37): imputação por mediana + StandardScaler. A padronização "
                "é necessária para o Ridge (regularização L2 sensível à escala); é inócua para "
                "Random Forest e Dummy, mantida por uniformidade do pipeline.")
    bullet(doc, "CO_MESORREGIAO: tratada como categórica nominal via OneHotEncoder "
                "(handle_unknown='ignore'). O código IBGE (2601–2605) não tem ordem significativa.")
    bullet(doc, "Identificadores (CO_ENTIDADE, NO_ENTIDADE, CO_MUNICIPIO, NO_MUNICIPIO, "
                "NU_ANO_CENSO) são excluídos das features; CO_MUNICIPIO é usado apenas como "
                "variável de agrupamento da CV.")
    body(doc, "Transformações de target testadas (via TransformedTargetRegressor):")
    bullet(doc, "identidade — sem transformação (referência).")
    bullet(doc, "log1p / expm1 — comprime a cauda direita (skewness ≈ 3 do target).")
    bullet(doc, "sqrt / square — compressão intermediária.")
    body(doc,
         "O TransformedTargetRegressor garante que o predict() devolva valores já na escala "
         "original (%), de modo que todas as métricas são comparáveis entre transformações.")

    heading(doc, "2.3 Busca de hiperparâmetros", 2)
    body(doc,
         "GridSearchCV com a mesma validação agrupada (GroupKFold 5 folds por município), "
         "otimizando RMSE. As grades são deliberadamente leves — o tuning fino é reservado "
         "ao XGBoost na Fase 6:")
    t = table_header(doc,
                     ["Modelo", "Grade", "Melhor configuração", "RMSE CV"],
                     [3.0, 6.0, 4.5, 2.5])
    for row in [
        ("Ridge", "alpha ∈ {0.1, 1, 10, 100}", "alpha = 100", "2,735"),
        ("Random Forest",
         "max_depth ∈ {None, 8} × min_samples_leaf ∈ {1, 5} (300 árvores)",
         "max_depth = 8, min_samples_leaf = 5", "2,703"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()

    # ── 3. M1 ────────────────────────────────────────────────────────────────
    heading(doc, "3. M1 — Baselines em validação cruzada", 1)
    body(doc,
         "Métricas em validação cruzada (média ± desvio-padrão entre os 5 folds, escala "
         "original em pontos percentuais):")
    t = table_header(doc,
                     ["Modelo", "RMSE", "MAE", "R²", "Spearman", "P@K (10%)"],
                     [3.5, 2.6, 2.6, 2.6, 2.6, 2.6])
    for row in [
        ("Dummy (média)", "3,316 ± 1,166", "1,695 ± 0,271", "−0,030 ± 0,035", "—", "0,069 ± 0,041"),
        ("Ridge",         "2,735 ± 0,642", "1,321 ± 0,177", "0,203 ± 0,326",  "0,393 ± 0,092", "0,500 ± 0,115"),
        ("Random Forest", "2,703 ± 0,626", "1,192 ± 0,193", "0,209 ± 0,353",  "0,438 ± 0,076", "0,506 ± 0,075"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    body(doc, "Leituras principais:")
    bullet(doc, "Os dois baselines superam claramente o piso trivial: RMSE ~18% menor que o Dummy "
                "e Precision@K sete vezes maior (0,50 vs 0,07).")
    bullet(doc, "Random Forest e Ridge são estatisticamente próximos em RMSE; o RF tem leve "
                "vantagem em Spearman (0,44 vs 0,39) e MAE.")
    bullet(doc, "O R² modesto (~0,20) reflete a dificuldade do problema: a maior parte da "
                "variância do abandono escolar não é explicada pelos indicadores institucionais "
                "disponíveis — consistente com a literatura e com a limitação nº 6 declarada "
                "na metodologia.")
    bullet(doc, "O Spearman do Dummy é indefinido (predição constante não produz ranking) — "
                "por construção, qualquer ranking informativo já é ganho sobre o piso.")
    add_figure(doc, "M1_baselines_cv.png",
               "Figura M1 — Distribuição das métricas por fold (GroupKFold por município).")

    # ── 4. M2 ────────────────────────────────────────────────────────────────
    heading(doc, "4. M2 — Transformação do target", 1)
    body(doc,
         "O target tem distribuição fortemente assimétrica (skewness ≈ 3; 29% das escolas com "
         "abandono zero). Testou-se se comprimir a cauda melhora os modelos:")
    t = table_header(doc,
                     ["Modelo", "Transformação", "RMSE", "Spearman", "P@K"],
                     [3.2, 3.2, 3.4, 2.8, 2.6])
    for row in [
        ("Ridge", "identidade", "2,735 ± 0,64", "0,393", "0,500"),
        ("Ridge", "log1p",      "2,845 ± 1,02", "0,419", "0,519"),
        ("Ridge", "sqrt",       "2,727 ± 0,90", "0,412", "0,512"),
        ("Random Forest", "identidade", "2,703 ± 0,63", "0,438", "0,506"),
        ("Random Forest", "log1p",      "2,766 ± 0,93", "0,454", "0,519"),
        ("Random Forest", "sqrt",       "2,735 ± 0,88", "0,458", "0,506"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    bullet(doc, "O efeito é pequeno e com trade-off: log1p melhora as métricas de ranking "
                "(Spearman, P@K) mas piora o RMSE — a compressão da cauda sacrifica a "
                "calibração das escolas de abandono alto, justamente as mais relevantes.")
    bullet(doc, "Critério de escolha: RMSE (métrica primária). Melhor configuração: "
                "Ridge + sqrt e Random Forest + identidade.")
    add_figure(doc, "M2_transformacao_target.png",
               "Figura M2 — Efeito das transformações de target em RMSE e Spearman.")

    # ── 5. M3 ────────────────────────────────────────────────────────────────
    heading(doc, "5. M3 — Validação temporal", 1)
    body(doc,
         "Simulação do uso real do sistema: o modelo é treinado com os dados disponíveis em um "
         "ciclo (features 2022 → abandono 2023, n=797) e testado no ciclo seguinte "
         "(features 2023 → abandono 2024, n=789).")
    t = table_header(doc,
                     ["Modelo", "RMSE", "MAE", "R²", "Spearman", "P@K"],
                     [3.5, 2.6, 2.6, 2.6, 2.6, 2.6])
    for row in [
        ("Dummy (média)", "2,540", "1,617", "−0,038", "—",     "0,089"),
        ("Ridge",         "2,749", "0,973", "−0,216", "0,370", "0,418"),
        ("Random Forest", "2,751", "1,138", "−0,217", "0,343", "0,405"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    body(doc, "Achado central da fase — deslocamento de distribuição entre anos:")
    bullet(doc, "Em nível (RMSE/R²), os modelos NÃO superam o Dummy no split temporal: o perfil "
                "médio de abandono mudou de 2023 para 2024 e os modelos, calibrados no nível de "
                "2023, erram sistematicamente o nível de 2024 (R² negativo).")
    bullet(doc, "Em ranking, os modelos seguem muito superiores: Spearman 0,37 vs — e "
                "Precision@K 0,42 vs 0,09 do Dummy. O modelo continua identificando QUAIS "
                "escolas terão abandono alto, ainda que erre QUANTO.")
    bullet(doc, "Implicação para a pesquisa: como a pergunta P2 é de priorização (ranking top-K "
                "para a Secretaria), as métricas de ranking sustentam a viabilidade. O resultado "
                "deve ser reportado na monografia como evidência de mudança de distribuição "
                "entre ciclos (consequência da janela curta de dados, 2 pares de anos).")
    bullet(doc, "Mitigações a testar na Fase 6: recalibração do intercepto por ano, inclusão de "
                "efeito de ano, ou foco explícito em métricas de ranking como critério de tuning.")
    add_figure(doc, "M3_validacao_temporal.png",
               "Figura M3 — Predito × real (Ridge) e erro por modelo no teste temporal 2023→2024.")

    # ── 6. M4 ────────────────────────────────────────────────────────────────
    heading(doc, "6. M4 — Análise preliminar de resíduos (preview da P3)", 1)
    body(doc,
         "Resíduo = real − predito, calculado no teste temporal com o Ridge "
         "(média 0,22 p.p., DP 2,74 p.p.). Esta análise antecipa a pergunta secundária P3 "
         "(escolas fora do esperado pelo perfil), que será aprofundada na Fase 7 com o "
         "modelo definitivo.")
    body(doc, "Padrões já visíveis:")
    bullet(doc, "Resíduos positivos (abandono acima do esperado): EREMs da Região Metropolitana "
                "e escolas de referência aparecem com abandono real muito acima do predito — "
                "candidatas a investigação qualitativa.")
    bullet(doc, "Resíduos negativos (escolas resilientes): escolas indígenas do Sertão de "
                "Itaparica (Jatobá, Tacaratu, Inajá, Carnaubeira da Penha) têm abandono real "
                "próximo de zero apesar de perfil contextual que prediz abandono alto (15–28%). "
                "O modelo aprende que o perfil 'rural + INSE baixo + TDI alto' prediz abandono, "
                "mas essas escolas contrariam o padrão — possível efeito de vínculo comunitário, "
                "não capturado pelas features.")
    bullet(doc, "Leve heterocedasticidade: o erro cresce com o valor predito, comportamento "
                "esperado dado o piso em zero do target.")
    add_figure(doc, "M4_residuos.png",
               "Figura M4 — Distribuição dos resíduos e resíduo × predito (Ridge, teste temporal).")

    # ── 7. M5 ────────────────────────────────────────────────────────────────
    heading(doc, "7. M5 — Ranking flexível: Precision@K e captura por K", 1)
    body(doc,
         "A metodologia (§2.1) justifica a escolha de regressão — em vez de classificação — "
         "pela possibilidade de ranking flexível top-N sem retreinar o modelo. Esta análise "
         "demonstra essa propriedade variando K (tamanho da lista de priorização) no teste "
         "temporal 2023→2024 e medindo duas grandezas: a Precision@K (sobreposição entre os "
         "top-K preditos e os top-K reais) e a captura de escolas críticas (fração das escolas "
         "com abandono real no decil superior, ≥ 2,7%, incluídas na lista priorizada).")
    t = table_header(doc,
                     ["K", "P@K Ridge", "P@K RF", "Captura Ridge", "Captura RF", "Aleatório"],
                     [2.0, 2.7, 2.7, 2.9, 2.9, 2.6])
    for row in [
        ("10",  "0,40", "0,30", "0,05", "0,04", "0,01"),
        ("30",  "0,33", "0,37", "0,17", "0,17", "0,04"),
        ("50",  "0,36", "0,38", "0,28", "0,30", "0,06"),
        ("100", "0,46", "0,48", "0,49", "0,49", "0,13"),
        ("150", "0,51", "0,53", "0,66", "0,65", "0,19"),
        ("200", "0,53", "0,52", "0,72", "0,72", "0,25"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    bullet(doc, "Leitura gerencial: intervindo nas top-50 escolas indicadas, a Secretaria "
                "alcança 28–30% das escolas críticas — cinco vezes mais que a seleção "
                "aleatória (6%); nas top-150, alcança cerca de dois terços delas.")
    bullet(doc, "O desempenho cresce de forma aproximadamente monotônica com K, confirmando "
                "que o mesmo modelo serve a diferentes capacidades de intervenção sem retreino.")
    add_figure(doc, "M5_precision_por_k.png",
               "Figura M5 — Precision@K e captura de escolas críticas por tamanho da lista (teste temporal).")

    # ── 8. M6 ────────────────────────────────────────────────────────────────
    heading(doc, "8. M6 — Estabilidade das métricas (CV repetida)", 1)
    body(doc,
         "A metodologia (§8.3) pede o erro padrão das métricas via repetições da validação "
         "cruzada. Foram executadas 20 repetições de partição agrupada (GroupShuffleSplit, "
         "20% dos municípios em teste a cada repetição), gerando a distribuição amostral "
         "das métricas — registrada em reports/metricas_cv_repetida.csv.")
    t = table_header(doc,
                     ["Modelo", "Métrica", "Média", "DP", "Erro padrão", "IC 95%"],
                     [3.0, 2.8, 2.2, 2.2, 2.4, 3.4])
    for row in [
        ("Dummy (média)", "RMSE",        "3,154", "0,965", "0,216", "[2,730; 3,577]"),
        ("Ridge",         "RMSE",        "2,627", "0,636", "0,142", "[2,348; 2,905]"),
        ("Ridge",         "Spearman",    "0,426", "0,080", "0,018", "[0,391; 0,461]"),
        ("Ridge",         "P@K",         "0,516", "0,091", "0,020", "[0,477; 0,556]"),
        ("Random Forest", "RMSE",        "2,546", "0,606", "0,135", "[2,281; 2,812]"),
        ("Random Forest", "Spearman",    "0,431", "0,072", "0,016", "[0,399; 0,463]"),
        ("Random Forest", "P@K",         "0,500", "0,100", "0,022", "[0,457; 0,544]"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    body(doc, "Comparação pareada (diferença RF − Ridge calculada repetição a repetição):")
    bullet(doc, "RMSE: −0,080 ± 0,065 (IC 95%) — o intervalo exclui zero: o Random Forest é "
                "significativamente melhor que o Ridge em erro de magnitude.")
    bullet(doc, "Spearman: +0,005 ± 0,023 — estatisticamente empatados em qualidade de ranking.")
    bullet(doc, "Implicação para a Fase 6: como a pergunta de pesquisa é de ranking, os dois "
                "baselines são patamares equivalentes em Spearman; em RMSE, o patamar a "
                "superar é o do Random Forest (2,55).")
    add_figure(doc, "M6_cv_repetida.png",
               "Figura M6 — Distribuição das métricas em 20 repetições de validação agrupada.")

    # ── 9. M7 ────────────────────────────────────────────────────────────────
    heading(doc, "9. M7 — Avaliação binarizada pós-hoc", 1)
    body(doc,
         "A metodologia (§2.1) prevê análise binarizada pós-hoc para comparação com a "
         "literatura, que majoritariamente trata evasão como classificação. Definiu-se alto "
         "risco como abandono 2024 no decil superior (≥ 2,7%; 80 escolas; prevalência 10,1%) "
         "e usaram-se as predições contínuas da regressão como scores — sem retreinar.")
    t = table_header(doc,
                     ["Modelo", "ROC-AUC", "PR-AUC", "PR-AUC / prevalência"],
                     [4.0, 3.5, 3.5, 5.0])
    for row in [
        ("Ridge",         "0,812", "0,340", "3,4×"),
        ("Random Forest", "0,829", "0,343", "3,4×"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    bullet(doc, "ROC-AUC de 0,81–0,83 situa os baselines na faixa tipicamente reportada pela "
                "literatura de predição de evasão (AUC ≈ 0,80), dando referência externa de "
                "qualidade antes mesmo do tuning do XGBoost.")
    bullet(doc, "O limiar P90 de apenas 2,7% de abandono em 2024 é confirmação independente do "
                "deslocamento de nível observado no M3: o abandono geral caiu de 2023 para 2024.")
    add_figure(doc, "M7_avaliacao_binarizada.png",
               "Figura M7 — Curvas ROC e Precision-Recall da avaliação binarizada (teste temporal).")

    # ── 10. M8 ───────────────────────────────────────────────────────────────
    heading(doc, "10. M8 — Top-20 resíduos e viés por grupo", 1)
    body(doc,
         "Atendendo à §8.4 da metodologia, as 20 escolas com maior resíduo positivo (abandono "
         "acima do esperado) e as 20 com maior resíduo negativo (escolas resilientes) foram "
         "persistidas em reports/residuos_top20_temporal.csv, com identificação, município, "
         "mesorregião, valores reais e preditos — insumo direto para a análise qualitativa "
         "da P3 na Fase 7.")
    body(doc, "A análise do resíduo médio por grupo revelou viés sistemático do modelo:")
    t = table_header(doc,
                     ["Grupo", "Resíduo médio (real − predito)", "N"],
                     [5.0, 7.0, 2.0])
    for row in [
        ("Urbana",                  "+0,42 p.p.", "680"),
        ("Rural",                   "−1,02 p.p.", "109"),
        ("Localização comum",       "+0,45 p.p.", "748"),
        ("Localização diferenciada (indígenas/quilombolas)", "−4,09 p.p.", "41"),
        ("Sertão",                  "−0,57 p.p.", "114"),
        ("Demais mesorregiões",     "+0,23 a +0,48 p.p.", "675"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()
    bullet(doc, "O modelo superprediz fortemente o abandono em escolas de localização "
                "diferenciada (−4,1 p.p.): o perfil contextual dessas escolas (rural, INSE "
                "baixo, TDI alta) está associado a abandono alto, mas o abandono observado é "
                "próximo de zero — consistente com fatores de vínculo comunitário não "
                "capturados pelas features (limitação nº 6 da metodologia).")
    bullet(doc, "Este resultado deve ser reportado na monografia como análise de equidade do "
                "modelo e reavaliado após o XGBoost; se o viés persistir, considerar feature "
                "de vínculo comunitário ou calibração por grupo.")
    add_figure(doc, "M8_residuos_grupos.png",
               "Figura M8 — Distribuição dos resíduos por mesorregião e por tipo de localização.")

    # ── 11. Testes ───────────────────────────────────────────────────────────
    heading(doc, "11. Testes automatizados", 1)
    body(doc,
         "tests/test_models.py adiciona 13 testes (suíte total: 55, todos passando). "
         "Riscos cobertos:")
    t = table_header(doc,
                     ["Risco", "Teste"],
                     [7.0, 9.0])
    for row in [
        ("precision@K incorreta → ranking de priorização sem sentido",
         "Casos de ranking perfeito (1,0), invertido (0,0), parcial (0,5) e k inválido"),
        ("Vazamento espacial na CV → métricas otimistas",
         "Nenhum município aparece em treino e teste do mesmo fold (GroupKFold)"),
        ("Erro no split temporal → contaminação 2023/2024",
         "Treino contém apenas 2022 e teste apenas 2023; partição completa"),
        ("Transformação de target sem inversa → predições em escala errada",
         "predict() com log1p/sqrt devolve valores na escala original (%)"),
        ("Features contaminadas por IDs",
         "CO_ENTIDADE, NO_ENTIDADE e CO_MUNICIPIO excluídos; CO_MESORREGIAO mantida"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()

    # ── 12. Artefatos ────────────────────────────────────────────────────────
    heading(doc, "12. Artefatos gerados", 1)
    t = table_header(doc,
                     ["Artefato", "Conteúdo"],
                     [7.5, 8.5])
    for row in [
        ("reports/metricas_baselines.csv",
         "Métricas por modelo × fold (CV) e do split temporal — registro da Fase 5"),
        ("reports/metricas_transformacoes.csv",
         "Métricas por modelo × transformação de target"),
        ("reports/metricas_cv_repetida.csv",
         "Métricas por modelo × repetição da CV agrupada (20 repetições) — base do M6"),
        ("reports/residuos_top20_temporal.csv",
         "Top-20 escolas com resíduo positivo e negativo no teste temporal — insumo da P3"),
        ("models/baseline_ridge_v1.joblib",
         "Melhor baseline (Ridge alpha=100, target sqrt) re-treinado com os 1.586 registros"),
        ("reports/figuras/M1–M8.png",
         "Figuras das análises desta fase"),
    ]:
        table_row(t, list(row))
    doc.add_paragraph()

    # ── 13. Conclusões ───────────────────────────────────────────────────────
    heading(doc, "13. Conclusões e próximos passos", 1)
    body(doc,
         "Com as análises M5–M8, todos os itens de avaliação previstos na metodologia para "
         "esta etapa possuem artefato correspondente: métricas primárias e de ranking (M1/M3), "
         "transformação de target (M2), ranking flexível top-N (M5), erro padrão via "
         "repetições (M6), avaliação binarizada pós-hoc (M7) e top-20 resíduos (M8).")
    body(doc, "Patamar estabelecido para a Fase 6 (tuning do XGBoost):")
    bullet(doc, "CV agrupada repetida: RMSE ≤ 2,55 (Random Forest, significativamente melhor "
                "que o Ridge na comparação pareada) · Spearman ≥ 0,43 · Precision@K ≥ 0,50.")
    bullet(doc, "Validação temporal: Spearman ≥ 0,37 · Precision@K ≥ 0,42 · ROC-AUC ≥ 0,83 "
                "na binarização pós-hoc.")
    body(doc, "Encaminhamentos:")
    bullet(doc, "Fase 6 — tuning do XGBRegressor com a mesma validação (GroupKFold + temporal), "
                "grade da seção 7 da metodologia; avaliar mitigações para o deslocamento de "
                "nível entre anos.")
    bullet(doc, "Discutir na monografia o achado do M3/M7: predição de nível não generaliza "
                "entre ciclos com 2 pares de anos (o abandono geral caiu em 2024), mas o "
                "ranking (objetivo da pesquisa) sim.")
    bullet(doc, "Reavaliar após o XGBoost o viés por grupo identificado no M8 (superpredição "
                "em escolas rurais e de localização diferenciada) — análise de equidade do "
                "modelo a reportar na monografia.")
    bullet(doc, "Fase 7 — análise SHAP e aprofundamento dos resíduos (P3), partindo do "
                "residuos_top20_temporal.csv, incluindo o caso das escolas indígenas "
                "resilientes.")

    doc.save(OUTPUT)
    print(f"Relatório salvo em: {OUTPUT}")


if __name__ == "__main__":
    build()
