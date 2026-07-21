# Previsão de Evasão Escolar — Ensino Médio Estadual de Pernambuco

Sistema que identifica antecipadamente as escolas estaduais de Ensino Médio de
Pernambuco com maior risco de abandono, e explica cada indicação. Desenvolvido
como TCC de Engenharia de Software.

A unidade de análise é a **escola** (não o aluno): os dados públicos existem
nesse nível, o gestor decide nesse nível e o volume resultante permite um
sistema auditável.

---

## O problema

A taxa média de abandono da rede vem caindo — 2,05% (2022), 1,37% (2023),
0,96% (2024) — mas a média esconde o problema. Em 2024:

- **2.043 alunos** abandonaram o Ensino Médio na rede estadual;
- **67% das escolas** não registraram nenhum caso;
- as **79 escolas mais críticas (10% da rede)** concentraram **76%** dos alunos
  que saíram.

O problema é concentrado, não difuso. Por isso o sistema precisa acertar *quem
está no topo da lista*, e não estimar bem a média — decisão que orienta a
seleção de dados, o modelo e o critério de avaliação.

### Questões de pesquisa

- **P2 — Previsão:** é possível prever quais escolas terão abandono elevado no
  ano **t+1** a partir de indicadores do ano **t**?
- **P3 — Diagnóstico:** quais escolas abandonam significativamente acima ou
  abaixo do que seu perfil prevê? (análise de resíduos)

---

## Resultados

Medidas sob validação repetida (20 repetições, agrupadas por município):

| Modelo | Erro médio (p.p.) | Acerto da ordenação | Acerto na lista prioritária |
|---|---|---|---|
| Sem sistema (média da rede) | 3,154 | — | 0,068 |
| Ridge | 2,627 | 0,426 | 0,516 |
| Random Forest | 2,546 | 0,431 | 0,500 |
| **XGBoost (adotado)** | 2,695 | **0,458** | 0,499 |

No teste temporal (treino 2022→2023, teste 2023→2024), com o modelo treinado
apenas no par anterior:

- capacidade de separar críticas de não críticas (ROC-AUC): **0,830**;
- lista das **50** primeiras alcança **30%** das escolas críticas (acaso: 6%);
- lista das **100** primeiras alcança **54%** (acaso: 13%);
- lista das **150** primeiras alcança **64%** (acaso: 19%).

O sistema **erra o valor** da taxa e **acerta a ordem**. Como o objetivo é
priorizar, é a ordenação que define a utilidade.

> **Limitação declarada:** o modelo superprevê risco em escolas de localização
> diferenciada (indígenas e quilombolas): resíduo médio de −4,09 p.p., contra
> +0,42 nas urbanas. A causa provável são fatores de proteção comunitários que
> os dados públicos não capturam. Está documentado na monografia e exposto no
> painel.

---

## Arquitetura

```
Fontes de Dados (INEP)
        │
        ▼
┌────────────────────────────────────────────┐
│  Camada de dados  (src/data/)              │
│                                            │
│  Censo Escolar  ──┐                        │
│  Taxas Rendimento─┤                        │
│  INSE ────────────┼─► painel + parquets    │
│  IRD / TDI / AFD ─┘    por indicador       │
│                                            │
│  IED / ICG ──────► apenas descritivo *     │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│  Preparação  (src/features/)               │
│  casamento temporal: ano t → alvo t+1      │
│  38 informações, sem lacunas               │
└──────────────────────┬─────────────────────┘
                       │ data/processed/features.parquet
                       ▼
┌────────────────────────────────────────────┐
│  Modelo  (src/models/train.py, evaluate.py)│
│  Dummy ► Ridge ► Random Forest ► XGBoost   │
│  CV agrupada por município + teste temporal│
└──────────────────────┬─────────────────────┘
                       │ models/xgboost_v1.joblib
                       ▼
┌────────────────────────────────────────────┐
│  Explicação  (src/models/explain.py)       │
│  contribuição por indicador (SHAP)         │
│  + análise de resíduos por grupo           │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│  Serviço  (src/recommend/service.py)       │
│  ranking · explicação · diagnóstico        │
│                  ▼                         │
│  Painel  (app/dashboard.py) — só tela      │
└────────────────────────────────────────────┘
```

\* **IED e ICG foram avaliados e não incorporados.** Ablação controlada
(`notebooks/11`) mostrou ausência de ganho: a ordenação ficou praticamente
idêntica (0,454 com, 0,455 sem) e o erro piorou levemente. O ICG é redundante
com a TDI. Os ETLs permanecem, apenas para caracterização descritiva.

As dependências fluem em sentido único, sem ciclos:
`data → features → models → recommend`. A comunicação entre etapas é sempre por
artefato em disco (Parquet, joblib) — nunca por chamada direta —, o que permite
reexecutar qualquer etapa isoladamente.

### Casamento temporal

| Informações do ano | Alvo (abandono) | Papel                   |
|--------------------|-----------------|-------------------------|
| 2022               | 2023            | Treino                  |
| 2023               | 2024            | Teste em ano nunca visto|
| 2024               | 2025            | Lista entregue ao gestor|

---

## Como executar

### 1. Pré-requisitos

- Python 3.10+
- Dados brutos posicionados em `data/raw/` (ver *Fontes de dados*)

### 2. Ambiente

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Pipeline completo

Execute na ordem, a partir da raiz do projeto (`evasao-escolar/`). Cada script
grava seus artefatos em disco; do passo 6 em diante, é possível reexecutar um
script isolado sem repetir os anteriores.

```bash
# Dados e exploração
python notebooks/01_exploracao_inicial.py        # carga, filtros, painel escola × ano
python notebooks/02_analises_descritivas.py      # perfil da rede (figuras A*)
python notebooks/03_analises_taxas_rendimento.py # taxas de rendimento (figuras B*)
python notebooks/04_analises_indicadores.py      # INSE, IRD, TDI, AFD, IED, ICG (C*)

# Preparação
python notebooks/05_feature_engineering.py       # → data/processed/features.parquet
python notebooks/13_estatisticas_features.py     # análise estatística das 38 colunas (E5–E8)

# Modelo
python notebooks/06_baseline_modelos.py          # Dummy, Ridge, Random Forest (M*)
python notebooks/08_tuning_xgboost.py            # busca de configuração → xgboost_v1.joblib
python notebooks/07_avaliacao_complementar.py    # avaliação dos 4 modelos (M5–M8)
python notebooks/11_avaliacao_ied_icg.py         # ablação IED/ICG (D1)

# Explicação e material da monografia
python notebooks/09_shap_diagnostico.py          # contribuições e resíduos (S*)
python notebooks/10_diagramas_arquitetura.py     # diagramas UML (arq*)
python notebooks/12_figuras_monografia.py        # figuras em linguagem de gestor (E1–E4)
```

> **Ordem importa entre 08 e 07:** o notebook 07 avalia também o XGBoost, que
> ele carrega de `models/xgboost_v1.joblib`. Rode o 08 antes.

Figuras vão para `reports/figuras/`, métricas e tabelas para `reports/*.csv`.

### 4. Dashboard

```bash
# a partir de evasao-escolar/, com o ambiente ativo
streamlit run app/dashboard.py
```

Abre em `http://localhost:8501`. O primeiro carregamento leva alguns segundos:
o serviço carrega o modelo e calcula as contribuições de todas as escolas de
uma vez, na construção.

Para rodar sem abrir o navegador automaticamente (útil em servidor):

```bash
streamlit run app/dashboard.py --server.port 8501 --server.headless true
```

**Pré-requisitos:** `models/xgboost_v1.joblib` e `data/processed/features.parquet`
gerados (passos 5 e 8 acima).

**O que o painel oferece** — três abas:

| Aba | Função |
|---|---|
| Ranking de risco | Escolas ordenadas por risco para o ano seguinte, com filtros por região e município, marcação das mais críticas e exportação em CSV |
| Detalhe da escola | Risco previsto, posição no ranking e quais indicadores puxaram a previsão para cima ou para baixo |
| Panorama | Visão agregada por grupo de escolas |

O painel é **apoio à decisão**, não recomendação prescritiva: o modelo é
correlacional e a leitura das contribuições é diagnóstica, não causal. Ele
responde *onde intervir primeiro e por quê*; como agir continua com o gestor.

A lógica vive em `src/recommend/service.py` (coberta por `tests/test_recommend.py`);
`app/dashboard.py` é apenas apresentação.

### 5. Testes

```bash
pytest tests/ -q

# com cobertura
pytest tests/ -v --cov=src --cov-report=term-missing
```

**98 testes**, todos passando. Eles cobrem sobretudo os erros que *não* lançam
exceção — em um sistema que aprende com dados, um deslocamento de um ano no
casamento temporal destruiria o valor preditivo sem nenhum sintoma em execução.

---

## Estrutura de pastas

```
evasao-escolar/
│
├── data/
│   ├── raw/                                   # Dados brutos — não versionados
│   │   ├── censo/                             # Microdados do Censo Escolar (2022–2024)
│   │   ├── taxas_rendimento/                  # Aprovação, reprovação e abandono
│   │   ├── inse/                              # Nível socioeconômico das escolas
│   │   ├── indicador_regularidade_docente/    # IRD
│   │   ├── taxa_distorcao_idade/              # TDI
│   │   ├── adequacao_formacao_docente/        # AFD
│   │   ├── esforco_docente/                   # IED — só descritivo
│   │   └── complexidade_gestao_escola/        # ICG — só descritivo
│   │
│   ├── interim/                               # Um parquet padronizado por fonte
│   │   ├── painel_escola_ano_pe_estadual_em.parquet
│   │   ├── taxas_rendimento_pe_estadual_em.parquet
│   │   ├── inse_pe_estadual.parquet
│   │   ├── ird_pe_estadual.parquet
│   │   ├── tdi_pe_estadual.parquet
│   │   ├── afd_pe_estadual.parquet
│   │   ├── ied_pe_estadual.parquet
│   │   └── icg_pe_estadual.parquet
│   │
│   └── processed/
│       └── features.parquet                   # 1.586 obs × 38 informações + alvo
│
├── models/                                    # Modelos treinados (não versionados)
│   ├── xgboost_v1.joblib                      # Modelo adotado
│   └── baseline_ridge_v1.joblib
│
├── src/                                       # Código de produção
│   ├── data/                                  # Aquisição e padronização
│   │   ├── config.py                          # Caminhos, anos e constantes
│   │   ├── load.py                            # Carga com resolução heurística de nomes
│   │   ├── filter_pe_estadual_em.py           # Filtros do universo de estudo
│   │   ├── build_school_panel.py              # Painel escola × ano
│   │   ├── build_target.py                    # Alvo: abandono em t+1
│   │   ├── build_taxas_rendimento.py
│   │   ├── build_inse.py
│   │   ├── build_ird.py
│   │   ├── build_tdi.py
│   │   ├── build_afd.py
│   │   ├── build_esforco_docente.py           # IED (descritivo)
│   │   └── build_complexidade_gestao.py       # ICG (descritivo)
│   │
│   ├── features/
│   │   └── build_features.py                  # Casamento temporal, derivações, imputação
│   │
│   ├── models/
│   │   ├── train.py                           # Pipelines, grades e protocolos de validação
│   │   ├── evaluate.py                        # Métricas, incluindo Precision@K
│   │   └── explain.py                         # Contribuições por indicador e resíduos
│   │
│   └── recommend/                             # Camada de serviço do painel
│       ├── service.py                         # Ranking, explicação por escola, diagnóstico
│       └── labels.py                          # Nomes técnicos → linguagem de gestor
│
├── app/
│   └── dashboard.py                           # Painel Streamlit (só apresentação)
│
├── notebooks/                                 # Análises executáveis (scripts, não .ipynb)
│   ├── comum.py                               # Infraestrutura compartilhada
│   ├── 01_exploracao_inicial.py
│   ├── 02_analises_descritivas.py
│   ├── 03_analises_taxas_rendimento.py
│   ├── 04_analises_indicadores.py
│   ├── 05_feature_engineering.py
│   ├── 06_baseline_modelos.py
│   ├── 07_avaliacao_complementar.py           # Ranking por K, CV repetida, ROC, resíduos
│   ├── 08_tuning_xgboost.py
│   ├── 09_shap_diagnostico.py
│   ├── 10_diagramas_arquitetura.py            # Diagramas UML da monografia
│   ├── 11_avaliacao_ied_icg.py                # Ablação que excluiu IED e ICG
│   ├── 12_figuras_monografia.py               # Figuras em linguagem de gestor
│   └── 13_estatisticas_features.py            # Análise estatística das 38 informações
│
├── tests/                                     # 98 testes
│   ├── conftest.py
│   ├── test_etl_filters.py                    # Filtros do universo
│   ├── test_panel.py                          # Integridade do painel
│   ├── test_taxas.py                          # Parser das planilhas do INEP
│   ├── test_build_target.py                   # Casamento temporal t → t+1
│   ├── test_models.py                         # Métricas e não-vazamento
│   ├── test_explain.py                        # Consistência das contribuições
│   ├── test_indicadores_gestao.py             # ETLs de IED e ICG
│   └── test_recommend.py                      # Camada de serviço do painel
│
├── reports/                                   # Saídas geradas automaticamente
│   ├── figuras/                               # A* B* C* D* E* F* M* S* X* arq*
│   ├── metricas_baselines.csv
│   ├── metricas_cv_repetida.csv               # 20 repetições × 4 modelos
│   ├── metricas_xgboost.csv
│   ├── metricas_transformacoes.csv
│   ├── estatisticas_features.csv              # Descritivas das 37 informações numéricas
│   ├── estatisticas_mesorregiao.csv
│   ├── shap_importancia.csv
│   ├── xgboost_feature_importance.csv
│   ├── ablacao_ied_icg.csv
│   ├── residuos_diagnostico.csv
│   ├── residuos_grupo_temporal.csv
│   └── residuos_top20_temporal.csv
│
├── requirements.txt
└── README.md
```

### Convenção das figuras

| Prefixo | Conteúdo |
|---|---|
| `A*` | Perfil da rede (Censo) |
| `B*` | Taxas de rendimento e abandono |
| `C*` | Indicadores complementares |
| `D1` | Ablação IED/ICG |
| `E1`–`E4` | Figuras da monografia em linguagem de gestor |
| `E5`–`E8` | Análise estatística das 38 informações |
| `F*` | Preparação das informações |
| `M*` | Avaliação dos modelos |
| `S*` | Explicação das previsões e resíduos |
| `X*` | Ajuste do XGBoost |
| `arq*` | Diagramas UML da arquitetura |

---

## Fontes de dados

| Fonte | Descrição | Período | Usada na previsão |
|-------|-----------|---------|-------------------|
| Censo Escolar (INEP) | Infraestrutura, matrículas, docentes, turmas | 2022–2024 | Sim |
| Taxas de Rendimento (INEP) | Aprovação, reprovação e **abandono** por série | 2022–2024 | Sim |
| INSE | Nível socioeconômico das escolas | 2021 (estático) | Sim |
| IRD | Regularidade do corpo docente | 2022–2024 | Sim |
| TDI | Distorção idade-série | 2022–2024 | Sim |
| AFD | Adequação da formação docente | 2022–2024 | Sim |
| IED | Esforço docente | 2022–2024 | Não — só descritivo |
| ICG | Complexidade de gestão | 2022–2024 | Não — só descritivo |

Estrutura esperada em `data/raw/`:

```
data/raw/
├── censo/
│   ├── microdados_ed_basica_2022.csv
│   ├── microdados_ed_basica_2023.csv
│   └── microdados_ed_basica_2024.csv
├── taxas_rendimento/
│   ├── tx_rend_escolas_2022.xlsx
│   ├── tx_rend_escolas_2023.xlsx
│   └── tx_rend_escolas_2024.xlsx
├── inse/
├── indicador_regularidade_docente/
├── taxa_distorcao_idade/
├── adequacao_formacao_docente/
├── esforco_docente/                # IED_ESCOLAS_<ano>.xlsx
└── complexidade_gestao_escola/     # ICG_ESCOLAS_<ano>.xlsx
```

Se os nomes diferirem, ajuste `src/data/config.py` — `load.py` também resolve
por padrão de nome, porque o INEP muda a nomenclatura entre edições.

### As 38 informações usadas

| Grupo | Colunas | Conteúdo |
|---|---|---|
| Contexto e localização | 3 | Zona rural, localização diferenciada, região do estado |
| Porte e proporções | 5 | Matrículas, alunos por turma e por professor, computadores por aluno, tempo integral |
| Infraestrutura | 13 | Água, esgoto, biblioteca, laboratórios, quadra, refeitório, internet e índice-resumo |
| Corpo docente | 4 | Regularidade e adequação da formação em três faixas |
| Perfil dos alunos | 5 | Nível socioeconômico e distorção idade-série (total e por série) |
| Histórico de rendimento | 8 | Abandono e reprovação do próprio ano (total e por série) |

Partiu-se de mais de 400 colunas do Censo. Os cortes seguiram três critérios:
informação repetida (turmas e docentes acompanham matrículas, r > 0,85),
consequência aritmética de outra (a taxa de aprovação é o complemento das
demais) e ausência na maior parte das escolas.

Análise estatística individual em `notebooks/13` e `reports/estatisticas_features.csv`:
**29 das 37** informações numéricas têm relação estatisticamente comprovada com
o abandono do ano seguinte.

---

## Stack tecnológico

| Camada | Tecnologias |
|--------|-------------|
| Dados e análise | `pandas`, `numpy`, `scipy`, `pyarrow` |
| Modelo | `scikit-learn`, `xgboost` |
| Explicação | `shap` |
| Visualização | `matplotlib`, `seaborn`, `plotly` |
| Painel | `streamlit` |
| Testes | `pytest`, `pytest-cov` |

---

## Métricas de avaliação

| Tipo | Métricas |
|------|----------|
| Erro de magnitude | RMSE, MAE, R² |
| Qualidade da ordenação | Correlação de Spearman |
| Utilidade prática | Precision@K (K = 10% das escolas) e captura por tamanho de lista |
| Comparação com a literatura | ROC-AUC e PR-AUC, binarizados *post hoc* |
| Validação cruzada | `GroupKFold` por município, repetida 20 vezes |
| Validação temporal | Treino 2022→2023, teste 2023→2024 |

O agrupamento por município evita que escolas da mesma cidade fiquem dos dois
lados da divisão — sem ele, as métricas saem otimistas.

---

## Status das fases

| Fase | Atividade | Status |
|------|-----------|--------|
| 1 | Exploração inicial e painel escola × ano | Concluída |
| 2 | ETL das taxas de rendimento | Concluída |
| 3 | ETL dos indicadores complementares | Concluída |
| 4 | Preparação das informações (38 colunas) | Concluída |
| 5 | Modelos de referência (Ridge, Random Forest) | Concluída |
| 6 | Avaliação complementar e resíduos | Concluída |
| 7 | Ajuste do XGBoost | Concluída |
| 8 | Explicação das previsões | Concluída |
| 9 | Painel Streamlit | Concluída |
| 10 | Avaliação e exclusão de IED/ICG | Concluída |
| 11 | Análise estatística das 38 informações | Concluída |
| 12 | Empacotamento em contêiner (Docker) | Pendente |

---

## Documentos do TCC

Na pasta acima (`../`):

| Arquivo | Conteúdo |
|---|---|
| `TCC_Evasao_Escolar_2026.docx` | **Monografia — versão de referência** |
| `Guia_Apresentacao_TCC_Consolidado.docx` | Roteiro de defesa, demonstração e arguição |
| `PROXIMOS_PASSOS.md` | Estado do projeto e o que falta fazer |
| `Modelo TCC Engenharia de Software 2022.docx` | Versão de trabalho anterior, com alterações marcadas em cor |
