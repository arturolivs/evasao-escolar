# Previsão de Evasão Escolar — Ensino Médio Estadual de Pernambuco

Sistema de aprendizado de máquina para prever o risco de abandono escolar em escolas estaduais de Ensino Médio em Pernambuco, com explicabilidade por SHAP. Desenvolvido como TCC em Engenharia de Software.

---

## Proposta

O projeto responde a duas questões de pesquisa:

- **P2 — Previsão:** É possível prever quais escolas estaduais de Ensino Médio em Pernambuco terão taxas de abandono elevadas no ano **t+1**, com base em indicadores institucionais do ano **t**?
- **P3 — Diagnóstico:** Quais escolas apresentam taxas de abandono significativamente acima ou abaixo do que seu perfil institucional prevê? (análise por resíduos)

A unidade de análise é a **escola** (não o aluno), e o modelo produz um **ranking de risco** que pode orientar intervenções prioritárias da rede estadual.

---

## Arquitetura

```
Fontes de Dados (INEP)
        │
        ▼
┌───────────────────────────────────────┐
│  Camada ETL  (src/data/)              │
│                                       │
│  Censo Escolar  ──┐                   │
│  Taxas Rendimento─┤                   │
│  INSE ────────────┼─► painel parquet  │
│  IRD  ────────────┤                   │
│  TDI  ────────────┤                   │
│  AFD  ────────────┘                   │
└──────────────────────┬────────────────┘
                       │
                       ▼
┌───────────────────────────────────────┐
│  Feature Engineering                  │
│  (src/features/build_features.py)     │
│                                       │
│  join temporal: features_t → alvo_t+1 │
│  derivação, imputação, codificação    │
└──────────────────────┬────────────────┘
                       │ dataset ML-ready
                       ▼
┌───────────────────────────────────────┐
│  Modelagem  (notebooks 06-07)         │
│                                       │
│  Dummy ► Ridge ► Random Forest        │
│        ► XGBoost (modelo principal)   │
│                                       │
│  CV por município (GroupKFold)        │
│  Validação temporal 2022→2023→2024    │
└──────────────────────┬────────────────┘
                       │ modelo + resíduos
                       ▼
┌───────────────────────────────────────┐
│  Explicabilidade SHAP                 │
│  Global (feature importance) +        │
│  Local (por escola)                   │
└──────────────────────┬────────────────┘
                       │
                       ▼
┌───────────────────────────────────────┐
│  Dashboard Streamlit  [planejado]     │
│  Ranking de risco · SHAP visual       │
│  Filtros por município / mesorregião  │
└───────────────────────────────────────┘
```

### Lógica temporal

| Ano das features | Ano do alvo (abandono) | Papel           |
|------------------|------------------------|-----------------|
| 2022             | 2023                   | Treino          |
| 2023             | 2024                   | Treino / Teste  |
| 2024             | 2025 (indisponível)    | Previsão futura |

---

## Estrutura de Pastas

```
evasao-escolar/
│
├── data/
│   ├── raw/                                   # Dados brutos — não versionados
│   │   ├── censo/                             # Microdados Censo Escolar (2022–2024)
│   │   ├── taxas_rendimento/                  # Aprovação, reprovação e abandono (INEP)
│   │   ├── inse/                              # Índice Socioeconômico das Escolas
│   │   ├── indicador_regularidade_docente/    # IRD — estabilidade do corpo docente
│   │   ├── taxa_distorcao_idade/              # TDI — distorção idade-série
│   │   └── adequacao_formacao_docente/        # AFD — adequação da formação docente
│   │
│   ├── interim/                               # Artefatos intermediários de ETL
│   │   └── painel_escola_ano_pe_estadual_em.parquet
│   │
│   └── processed/                             # Dataset final pronto para modelagem
│
├── src/                                       # Código de produção (módulos reutilizáveis)
│   ├── data/                                  # Pipeline ETL
│   │   ├── config.py                          # Caminhos, constantes e nomes de colunas
│   │   ├── load.py                            # Carregamento genérico de CSVs
│   │   ├── filter_pe_estadual_em.py           # Filtragem do universo de escolas
│   │   ├── build_school_panel.py              # Painel escola × ano
│   │   ├── build_target.py                    # Variável-alvo: abandono t+1
│   │   ├── build_taxas_rendimento.py          # ETL das taxas de rendimento INEP
│   │   ├── build_inse.py                      # ETL do índice socioeconômico
│   │   ├── build_ird.py                       # ETL do indicador de regularidade docente
│   │   ├── build_tdi.py                       # ETL da taxa de distorção idade-série
│   │   └── build_afd.py                       # ETL da adequação da formação docente
│   │
│   ├── features/
│   │   └── build_features.py                  # Pipeline de feature engineering
│   │
│   ├── models/                                # [em desenvolvimento]
│   │   └── __init__.py
│   │
│   └── recommend/                             # Regras de recomendação [planejado]
│       └── __init__.py
│
├── notebooks/                                 # Análises executáveis (scripts Python)
│   ├── 01_exploracao_inicial.py               # EDA: carga, filtragem, sanidade
│   ├── 02_analises_descritivas.py             # Estatísticas descritivas e visualizações
│   ├── 03_analises_taxas_rendimento.py        # Análise das taxas de rendimento
│   ├── 04_analises_indicadores.py             # Análise dos indicadores complementares
│   ├── 05_feature_engineering.py             # Construção e seleção de features
│   ├── 06_baseline_modelos.py                 # Modelos baseline (Ridge, Random Forest)
│   └── 07_avaliacao_complementar.py           # Avaliação adicional e análise de resíduos
│
├── tests/                                     # Testes automatizados
│   ├── conftest.py                            # Fixtures compartilhadas
│   ├── test_etl_filters.py                    # Testes de filtragem ETL
│   ├── test_panel.py                          # Testes de construção do painel
│   ├── test_taxas.py                          # Testes das taxas de rendimento
│   ├── test_build_target.py                   # Testes de construção da variável-alvo
│   └── test_models.py                         # Testes de avaliação dos modelos
│
├── docs/                                      # Relatórios técnicos
│   ├── relatorio_fase1_eda.md/.docx
│   ├── relatorio_etl_taxas_rendimento.md/.docx
│   ├── relatorio_indicadores_complementares.docx
│   └── relatorio_fase5_baselines.docx
│
├── reports/                                   # Saídas geradas automaticamente
│   ├── figuras/                               # Gráficos PNG
│   ├── metricas_baselines.csv
│   ├── metricas_cv_repetida.csv
│   ├── metricas_transformacoes.csv
│   └── residuos_top20_temporal.csv
│
├── requirements.txt
└── README.md
```

---

## Fontes de Dados

| Fonte | Descrição | Período |
|-------|-----------|---------|
| Censo Escolar (INEP) | Infraestrutura, matrículas, docentes, turmas | 2022–2024 |
| Taxas de Rendimento (INEP) | Aprovação, reprovação e **abandono** por série | 2022–2024 |
| INSE | Índice Socioeconômico das Escolas | 2021–2022 |
| IRD | Regularidade/estabilidade do corpo docente | 2022–2024 |
| TDI | Taxa de Distorção Idade-Série | 2022–2024 |
| AFD | Adequação da Formação Docente | 2022–2024 |

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
└── adequacao_formacao_docente/
```

Se os nomes de arquivos diferirem, ajuste `src/data/config.py` ou deixe que `load.py` faça a resolução heurística por padrão de nome.

---

## Stack Tecnológico

| Camada | Tecnologias |
|--------|-------------|
| ETL e análise | `pandas`, `numpy`, `scipy` |
| Modelos | `scikit-learn`, `xgboost` |
| Explicabilidade | `shap` |
| Visualizações | `matplotlib`, `seaborn`, `plotly` |
| Dashboard | `streamlit` (planejado) |
| Testes | `pytest`, `pytest-cov` |

---

## Como Executar

### 1. Pré-requisitos

- Python 3.10+
- Dados brutos baixados e posicionados em `data/raw/` (ver seção acima)

### 2. Instalar dependências

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Executar o pipeline por fase

Os notebooks são scripts Python executáveis. Rode-os em ordem a partir da raiz do projeto:

```bash
# Fase 1 — Exploração inicial e filtragem do universo de escolas
python notebooks/01_exploracao_inicial.py

# Fase 2 — Estatísticas descritivas e visualizações
python notebooks/02_analises_descritivas.py

# Fase 3 — ETL e análise das taxas de rendimento
python notebooks/03_analises_taxas_rendimento.py

# Fase 4 — ETL e análise dos indicadores complementares (INSE, IRD, TDI, AFD)
python notebooks/04_analises_indicadores.py

# Fase 5 — Feature engineering: dataset final para modelagem
python notebooks/05_feature_engineering.py

# Fase 6 — Treinamento e avaliação dos modelos baseline
python notebooks/06_baseline_modelos.py

# Fase 7 — Avaliação complementar e análise de resíduos (P3)
python notebooks/07_avaliacao_complementar.py
```

Figuras são salvas em `reports/figuras/` e métricas em `reports/*.csv`.

### 4. Executar os testes

```bash
pytest tests/ -v

# Com cobertura
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Métricas de Avaliação

| Tipo | Métricas |
|------|----------|
| Regressão | RMSE, MAE, R² |
| Ranqueamento | Correlação de Spearman |
| Classificação pós-hoc | Precision@K (top-K escolas de maior risco) |
| Validação cruzada | `GroupKFold` agrupado por município |
| Validação temporal | Treino 2022→2023, teste 2023→2024 |

---

## Status das Fases

| Fase | Atividade | Status |
|------|-----------|--------|
| 1 | Exploração inicial (EDA) | Concluída |
| 2 | ETL das taxas de rendimento | Concluída |
| 3 | ETL dos indicadores complementares | Concluída |
| 4 | Feature engineering | Concluída |
| 5 | Modelos baseline (Ridge, Random Forest) | Concluída |
| 6 | Avaliação complementar e análise de resíduos | Concluída |
| 7 | Tuning do XGBoost | Em andamento |
| 8 | Explicabilidade com SHAP | Planejada |
| 9 | Dashboard Streamlit | Planejada |
| 10 | Documentação final e testes | Em andamento |

---

Para justificativas metodológicas, decisões de arquitetura e roadmap detalhado, consulte `../decisoes_projeto.md`.
