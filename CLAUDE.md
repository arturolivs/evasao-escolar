# CLAUDE.md — Projeto de Priorização de Escolas em Risco de Evasão (PE)

TCC de Especialização em Engenharia de Software (PUC-SP), autor Artur Oliveira Santiago,
orientador prof. Silvio Luiz Stanzani. O repositório contém **duas coisas acopladas**: o
sistema preditivo (`evasao-escolar/`) e a monografia que o descreve (`documentos/`).
Todo número escrito na monografia tem de vir de um artefato do pipeline — essa é a regra
que organiza o resto deste arquivo.

## Visão Geral

Sistema preditivo para a Secretaria Estadual de Educação de Pernambuco que identifica
antecipadamente escolas de Ensino Médio com alto risco de abandono no ano seguinte.

- **Unidade de análise**: escola (não aluno).
- **Alvo**: taxa de abandono do ano seguinte (t+1).
- **Modelo adotado**: XGBoost + explicações SHAP. Baselines: Dummy (média), Ridge, Random Forest.
- **Dados**: microdados públicos do Censo Escolar e Indicadores Educacionais do INEP, 2022–2024.
- **Escala atual**: 39 características, 1.586 observações escola×ano, 801 escolas, 185 municípios.
  Treino usa anos-feature 2022 e 2023; 2024 entra **somente** em modo predição (alvo 2025).

---

## Estrutura do Repositório

```
monografia/
├── evasao-escolar/          # o sistema (pacote src/, testes, dados, relatórios)
│   ├── src/                 # código de produção
│   ├── notebooks/           # scripts de análise numerados 01..16 (não .ipynb)
│   ├── tests/               # 138 testes pytest
│   ├── data/                # raw/ interim/ processed/  (fora do Git)
│   ├── models/              # *.joblib (fora do Git)
│   ├── reports/             # métricas .csv + figuras/ (75 PNGs)
│   └── requirements.txt     # versões FIXADAS com == (ver Ambiente)
├── documentos/              # a monografia e todo o material de escrita
│   ├── monografia-artur-oliveira-engenharia-de-software-2026.docx   # documento principal
│   ├── TCC_ANTES_*.docx               # backups por rodada de edição
│   ├── COMENTARIOS_ORIENTADOR.md      # os 13 comentários (SS1..SS13) e status
│   ├── PLANO_DE_FINALIZACAO.md        # pendências em 5 tiers
│   ├── SS*_TEXTO_PARA_O_TCC.md        # texto+números prontos por comentário
│   └── referencias/                   # 21 PDFs + README que liga PDF→citação→¶
└── .claude/skills/          # skills de validação (ver seção final)
```

**Todos os comandos de código rodam a partir de `evasao-escolar/`.** É onde vive o pacote
`src/` e o `requirements.txt`.

---

## Comandos Reais

Os nomes abaixo foram verificados contra o código. Não existem `src.data.build_datasets`,
`src.models.train_model` nem `src.recommend.predict_year`.

### Ambiente
A venv fica na **raiz do repositório** (`.venv/` ao lado deste arquivo), não dentro de
`evasao-escolar/`. O `python` global da máquina não tem nenhum pacote do projeto — sem a
venv ativa tudo falha com `ModuleNotFoundError`.
```bash
python -m venv .venv                         # na raiz do repositório
.venv\Scripts\activate                       # Windows (ambiente de referência)
pip install -r evasao-escolar\requirements.txt
cd evasao-escolar                            # todos os comandos abaixo rodam daqui
```

A ativação vale só para a janela do terminal: cada terminal novo precisa ativar de novo.
O sintoma de venv inativa no PowerShell é
`streamlit : O termo 'streamlit' não é reconhecido como nome de cmdlet…` (ou
`ModuleNotFoundError` nos scripts Python). Com a venv ativa, o prompt começa com `(.venv)`.

```powershell
# a partir de evasao-escolar/
..\.venv\Scripts\Activate.ps1

# se o PowerShell bloquear o script ("execução de scripts foi desabilitada"),
# liberar só para esta janela e ativar de novo:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
..\.venv\Scripts\Activate.ps1

# alternativa sem ativar: chamar os executáveis da venv direto
..\.venv\Scripts\python.exe -m src.features.build_features
..\.venv\Scripts\streamlit.exe run app/dashboard.py
```

### Testes
```bash
pytest              # 138 testes, ~25 s
pytest tests/test_build_target.py           # casamento temporal t→t+1
pytest tests/test_models.py                 # vazamento espacial entre folds
pytest tests/test_explain.py                # aditividade SHAP
pytest tests/test_rastreabilidade_amostra.py  # cadeia 2.392→1.586
```

### ETL (um entry-point por indicador)
```bash
python -m src.data.build_taxas_rendimento
python -m src.data.build_inse
python -m src.data.build_ird
python -m src.data.build_tdi
python -m src.data.build_afd
python -m src.data.build_esforco_docente
python -m src.data.build_complexidade_gestao
```
`src/data/build_school_panel.py` **não tem `__main__`** — o painel escola×ano é montado
por `python notebooks/01_exploracao_inicial.py`. Alguns comentários antigos nos notebooks
04 e 12 citam `python -m src.data.build_school_panel`; está errado.

### Features, treino e predição
```bash
python -m src.features.build_features       # → data/processed/features.parquet
python notebooks/06_baseline_modelos.py     # → models/baseline_*_v1.joblib
python notebooks/08_tuning_xgboost.py       # → models/xgboost_v1.joblib
python notebooks/09_shap_diagnostico.py     # SHAP + resíduos
python -m src.models.predict 2024           # prevê 2025 (ano POSICIONAL, não --year)
```

### Reexecução completa — a ordem NÃO é a numérica dos notebooks

O número no nome do arquivo é ordem de criação, não de execução. Reexecutar na ordem
`01, 02, … 15` **quebra**: `07_avaliacao_complementar.py` carrega
`models/xgboost_v1.joblib` (via `criar_modelos_vencedores` → `carregar_modelo`), que só
existe depois do `08_tuning_xgboost.py`. Verificado em 31/07/2026 numa reconstrução do zero,
que abortou exatamente aí com `FileNotFoundError: Modelo não encontrado`.

Ordem correta, do bruto ao ranking:

```bash
# 0. dados brutos — os 22 arquivos do INEP em data/raw/ (ver data/raw/README.md)
# 1. ETL — TODOS os 7, em qualquer ordem entre si (→ data/interim/*.parquet)
python -m src.data.build_taxas_rendimento    # → taxas_rendimento_pe_estadual_em  (alvo)
python -m src.data.build_inse                # → inse_pe_estadual
python -m src.data.build_ird                 # → ird_pe_estadual
python -m src.data.build_tdi                 # → tdi_pe_estadual
python -m src.data.build_afd                 # → afd_pe_estadual
python -m src.data.build_esforco_docente     # → ied_pe_estadual  (só notebooks 04 e 11)
python -m src.data.build_complexidade_gestao # → icg_pe_estadual  (só notebooks 04 e 11)
# 2. painel escola×ano — SEMPRE reexecutar quando o Censo bruto mudar
python notebooks/01_exploracao_inicial.py    # → painel_escola_ano_pe_estadual_em
# 3. características — exige os 6 parquets acima (painel, taxas, inse, ird, tdi, afd)
python -m src.features.build_features        # → data/processed/features.parquet
pytest tests/test_rastreabilidade_amostra.py # conferência: 1.586 linhas, 801 escolas
# 4. descritivas (independentes entre si)
python notebooks/02_analises_descritivas.py
python notebooks/03_analises_taxas_rendimento.py
python notebooks/04_analises_indicadores.py
python notebooks/05_feature_engineering.py
python notebooks/11_avaliacao_ied_icg.py
python notebooks/13_estatisticas_features.py
# 5. modelagem — 08 ANTES de 07
python notebooks/06_baseline_modelos.py
python notebooks/08_tuning_xgboost.py
python notebooks/07_avaliacao_complementar.py
# 6. explicação e diagnóstico
python notebooks/09_shap_diagnostico.py
python notebooks/14_ss13_cenarios_temporais.py
# 7. figuras
python notebooks/10_diagramas_arquitetura.py
python notebooks/12_figuras_monografia.py
python notebooks/16_figuras_simplificadas.py
# 8. predição
python -m src.models.predict 2024
```

Duas armadilhas vistas numa reconstrução em 28/10/2026:

- **ETL pulado.** O `build_features` só falha quando chega ao parquet ausente
  (`FileNotFoundError: Parquet não encontrado: …\data\interim\afd_pe_estadual.parquet`).
  Antes de rodar o passo 3, conferir que `data/interim/` tem os 6 parquets de entrada.
- **Painel velho.** O `painel_escola_ano_pe_estadual_em.parquet` em `data/interim/` pode
  ter sobrado de uma execução anterior. O `build_features` o aceita sem reclamar. Por isso,
  depois de baixar dados novos, rodar o passo 2 é obrigatório.

Depois do passo 3 o dataset deve ter 1.586 linhas (797 de 2022 e 789 de 2023), 801
escolas, 185 municípios e 39 características, sem valores ausentes. Se não tiver, o
problema está no dado bruto ou no ETL, não no modelo.

`15_varredura_numeros.py` roda por último, depois de tudo — é validação, não pipeline.
Ele tem caminhos fixos de outra máquina (`C:\Users\Suporte\Documents\monografia\…`) e só
roda nesta depois de ajustar `RAIZ` e `DOC` no topo do arquivo.

### Painel
```bash
streamlit run app/dashboard.py              # com a venv ativa (ver Ambiente)
```
Exige `models/xgboost_v1.joblib` (notebook 08) e `data/processed/features.parquet`.
Sem a venv ativa, o PowerShell não encontra o `streamlit`.

---

## Arquitetura (`src/`)

Fluxo estritamente unidirecional, sem ciclos: `data` → `features` → `models` → `recommend`.

- `src/data/config.py` — caminhos, constantes e mapeamentos. (Não existe `src/config.py`.)
- `src/data/` — leitura e padronização do INEP (Censo, Taxas de Rendimento, INSE, IRD, TDI, AFD, IED, ICG) e construção do target longitudinal.
- `src/features/build_features.py` — as 39 características, imputação por mesorregião×ano, casamento t→t+1, e `rastrear_reducao_amostra()` (a cadeia 2.392→1.586 do Quadro 5).
- `src/models/` — `train.py` (pipelines, GroupKFold por município, split temporal), `predict.py` (modo predição), `explain.py` (SHAP), `evaluate.py` (Precision@K, Spearman).
- `src/recommend/` — `service.py` (camada de serviço do painel), `labels.py` (tradução de variável técnica → linguagem de gestor).

---

## Diretrizes

### 1. Anti-vazamento (não negociável)
- Ordem temporal estrita: características de t preveem abandono em t+1. O ano mais recente
  nunca sobra como ano de origem no treino.
- Nunca dividir o mesmo município entre treino e teste — `GroupKFold(groups=CO_MUNICIPIO)`.
  `CO_MUNICIPIO` está em `ID_COLS`, logo fora das features.
- Imputação sempre por **mesorregião × mesmo ano**, nunca com informação de anos futuros.
  O fallback de média global em `build_features.py:193` foi medido em 31/07 e **nunca
  dispara** — todo grupo mesorregião×ano tem ao menos um valor observado. Se um dado novo
  do INEP mudar isso, o caminho passa a agrupar anos: reconferir com `/revisar-projeto`.

### 2. Ambiente fixado — condição para regerar qualquer número
O `requirements.txt` fixa tudo com `==` por um motivo já custeado: **a partição do
`GroupKFold` mudou entre versões do scikit-learn e alterou as métricas dos Quadros 9 e 10**
sem que dados ou código mudassem. Referência: Python 3.14, Windows, scikit-learn 1.8.0,
xgboost 3.2.0, shap 0.51.0.

- **Nunca regerar números do Capítulo 6 fora deste ambiente.** Rodar `/validar-ambiente` antes.
- `GroupShuffleSplit` (usado no experimento SS13, notebook 14) é estável entre versões;
  `GroupKFold` não é.

### 3. Métricas de sucesso — e a ressalva honesta
O critério é **ordenação**: Precision@K (top 10% ≈ 150 escolas) e Spearman. Não é RMSE.
Isso não é preferência de estilo, é consequência dos resultados:

| | Dummy (média) | Ridge | Random Forest | XGBoost |
|---|---|---|---|---|
| CV repetida — Spearman | — | 0,428 | **0,431** | 0,416 |
| CV repetida — Precision@K | 0,068 | **0,513** | 0,501 | 0,504 |
| Teste temporal — Spearman | — | 0,330 | 0,343 | **0,348** |
| Teste temporal — Precision@K | 0,089 | 0,380 | 0,405 | **0,418** |
| Teste temporal — RMSE | **2,540** | 2,891 | 2,751 | 2,874 |

Duas coisas que **não** devem ser suavizadas em nenhum texto gerado:
- No teste temporal o XGBoost tem **RMSE pior que o dummy** e R² negativo (−0,33). O ganho
  está no ranking: Precision@K 0,418 vs 0,089 (4,7×).
- Os três modelos são **estatisticamente indistinguíveis** (ICs sobrepostos); o RF empata ou
  supera em vários pontos. A escolha do XGBoost se justifica pelo teste temporal, pelo SHAP
  construído sobre ele, e explicitamente **não** por superioridade geral.

Desempenho por transição anual (SS13): 2022→2023 rende mais (Spearman 0,469 / P@K 0,627)
que 2023→2024 (0,367 / 0,381), acompanhando a queda do abandono médio (1,36% → 0,88%).

### 4. Transparência e equidade
- Explicação SHAP individual em toda predição; aditividade travada por teste.
- **Viés medido, não hipotético**: nas 41 escolas de localização diferenciada
  (indígenas/quilombolas) o modelo prevê 11,08% contra 4,96% observados — resíduo médio
  **−6,12 p.p.**, enquanto urbanas (+0,07) e rurais (+0,38) ficam calibradas. Agrava que
  `is_loc_diferenciada` é a característica **nº 1 por ganho** no XGBoost (0,239).
  Toda saída dirigida a gestor deve carregar essa ressalva. Implementada em
  `service.ressalva_equidade()` (regra no domínio, exibição no painel) — reusar essa função
  em qualquer nova superfície de saída em vez de reescrever o texto.
- A leitura SHAP é diagnóstica, não causal. Nada de recomendação prescritiva derivada dela.

### 5. Qualidade de código
- Acoplamento fraco: troca entre etapas por `.parquet` em `data/interim/` e `data/processed/`.
- Regra de negócio fora do Streamlit, testada por `pytest` sem tocar a interface.
- Verificação forte de reprodutibilidade: `features.parquet` foi regerado em 31/07 e saiu
  **bit-idêntico** — mesmo tamanho, 0 células alteradas, rastreabilidade igual. O pipeline
  de características é determinístico.

---

## Trabalhando na Monografia

- **Documento canônico e único**: `documentos/monografia-artur-oliveira-engenharia-de-software-2026.docx`
  (637 parágrafos, 13 tabelas). Renomeado em 31/07/2026; antes era `TCC_Evasao_Escolar.docx`.
  É o alvo da varredura do notebook 15. Os `TCC_ANTES_*.docx` são backups históricos, nunca
  alvo de edição.
- **Sempre criar backup** antes de alterar o `.docx`, seguindo a convenção existente:
  `TCC_ANTES_<ASSUNTO>.docx` em `documentos/`.
- **Estado atual**: 7 capítulos, 22 figuras, 12 quadros, 24 referências (21 com PDF em
  `documentos/referencias/`). Numeração de figuras e quadros sem lacunas.
- **Figuras do Capítulo 6 em linguagem de gestor** (`notebooks/16_figuras_simplificadas.py`):
  as versões técnicas M5, M6 e o beeswarm S1 **não** entram mais no corpo do texto — foram
  substituídas por `G3`, `G4` e `G5`, que usam os mesmos números com os rótulos dos Quadros 9
  e 10. `G1` (funil 2.392→1.586) e `G2` (erro do valor × acerto da ordem) são as Figuras 7 e
  14, sem equivalente técnico anterior. Ao mexer nessas figuras, editar o notebook 16, nunca
  o 07 ou o 09.
- **Nunca digitar um número no `.docx` sem que ele saia de um artefato do pipeline.** Depois
  de qualquer edição numérica, rodar `/validar-numeros` — a varredura confere 178 valores do
  documento contra os parquets/CSVs.
- **Terminologia (comentário SS7)**: usar "característica", não "informação" nem "feature".
  Exceções legítimas já auditadas: o *abstract* em inglês, o título da referência
  Guyon & Elisseeff, o caminho `src/features`, e 4 usos de "informação" no sentido comum.
- **Quadros foram renumerados** quando o Quadro 5 (rastreabilidade) entrou: antigo 5→6, 6→7,
  7→8, 8→9, 9→10. Os comentários do orientador citam a numeração **antiga**.
- Campos do Word (Sumário, Listas de Ilustrações/Quadros) são automáticos e não se
  preenchem fora do Word. O `settings.xml` já tem `<w:updateFields w:val="true"/>`: o autor
  só aceita a atualização ao abrir.
- Pendências que **dependem do autor** e não devem ser "resolvidas" por conta própria:
  ficha catalográfica (link da PUC-SP), composição da banca (55 linhas `___`),
  agradecimentos. Status detalhado em `documentos/PLANO_DE_FINALIZACAO.md`.

---

## Skills de Validação

Em `.claude/skills/`. Rodar antes de qualquer entrega ou defesa:

| Skill | Para quê |
|---|---|
| `/validar-ambiente` | Confere o ambiente contra os pins do `requirements.txt`. **Rodar primeiro** — número gerado em ambiente errado é número inválido. |
| `/validar-numeros` | Varredura de cada número do `.docx` contra o artefato que o gera (notebook 15) + suíte de testes. |
| `/validar-documento` | Consistência estrutural do `.docx`: numeração, terminologia, placeholders pendentes. |
| `/validar-escrita` | Qualidade do texto: sintaxe PT-BR, ABNT (citações, referências, citação longa), clareza, e marcadores de escrita automática com guia de humanização. |
| `/revisar-projeto` | Auditoria de código nos 7 pilares (vazamento, features, métricas, SHAP, equidade, arquitetura). |
| `/prever-novo-ano` | Gera o ranking de priorização de um novo ano letivo. |
