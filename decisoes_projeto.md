# Projeto TCC — Decisões Consolidadas e Roadmap

---

## 1. Definição do problema

### 1.1 Perguntas de pesquisa

**Principal (P2):** É possível prever, a partir de indicadores institucionais e contextuais do ano *t*, quais escolas estaduais de ensino médio de Pernambuco terão alta taxa de abandono no ano *t+1*?

**Secundária (P3):** Quais escolas apresentam taxa de abandono significativamente acima (ou abaixo) do que seria esperado pelo seu perfil contextual, e como essas escolas se diferenciam?

> P3 é derivada do mesmo modelo de P2 (análise de resíduos), não constitui pipeline paralelo.

### 1.2 Reescrita do objetivo geral (proposta para revisar com orientador)

**Original:** "Desenvolver um sistema de software baseado em aprendizado de máquina para predição precoce do risco de evasão escolar de **estudantes** do ensino médio…"

**Proposto:** "Desenvolver um sistema de software baseado em aprendizado de máquina para identificação precoce de **escolas** estaduais de ensino médio de Pernambuco com elevado risco de evasão, utilizando o algoritmo XGBoost em conjunto com técnicas de Inteligência Artificial Explicável (SHAP), com vistas a subsidiar a priorização de intervenções pela Secretaria Estadual de Educação."

> Atenção: este reposicionamento exige revisão dos objetivos específicos (em especial e, f, h) e do escopo da monografia.

---

## 2. Decisões metodológicas

| Item | Decisão |
|------|---------|
| **Unidade de análise** | Escola |
| **Universo** | Escolas com oferta de Ensino Médio Regular |
| **Rede** | Apenas estadual (`TP_DEPENDENCIA == 2`) |
| **UF** | Pernambuco (`SG_UF == 'PE'`) |
| **Etapa de ensino** | Ensino Médio Regular |
| **Anos de treino** | Censo 2022 e 2023 (features) → Abandono 2023 e 2024 (target) |
| **Tipo de problema** | Regressão (target contínuo) |
| **Target** | Taxa de Abandono Escolar do EM no ano *t+1* (em %) |
| **Fonte do target** | Taxas de Rendimento Escolar / INEP |
| **N esperado** | ~1.000 escolas × 2 anos = ~2.000 observações |

### 2.1 Justificativa das decisões

**Por que escola (e não aluno):**
- Dados de aluno apresentam inconsistências e dificuldades de linkage entre anos.
- O usuário-alvo (gestor de Secretaria de Educação) decide em nível de escola.
- Permite aproveitar indicadores agregados de qualidade já calculados pelo INEP.
- N gerenciável (~2.000 obs) — viável em qualquer ambiente computacional.

**Por que apenas rede estadual:**
- EM é responsabilidade constitucional do estado (CF art. 211, §3º).
- Garante homogeneidade institucional do universo (validade interna do modelo).
- Rede federal (IFs) tem dinâmica de seleção e evasão muito distinta — contaminaria o modelo.

**Por que regressão (e não classificação binária):**
- Preserva granularidade da taxa de abandono.
- Permite ranking flexível (top-N) sem retreinar.
- Métricas como Spearman correlation são naturais para problema de priorização.
- Análise complementar binarizada pode ser feita pós-hoc para comparação com literatura.

**Riscos conhecidos a mitigar:**
- N pequeno → risco de overfitting → mitigar com regularização e validação cruzada.
- Distribuição de target assimétrica → testar transformação (log, raiz quadrada).
- Possível autocorrelação espacial (escolas próximas têm dinâmica similar) → considerar agrupamento por município na validação cruzada (`GroupKFold`).

---

## 3. Dados e fontes

### 3.1 Fontes obrigatórias

| Fonte | Conteúdo | Granularidade | Status |
|-------|----------|---------------|--------|
| Microdados Censo Escolar 2022 | Características das escolas | Por escola | Disponível localmente |
| Microdados Censo Escolar 2023 | Características das escolas | Por escola | Disponível localmente |
| Microdados Censo Escolar 2024 | Características das escolas | Por escola | Disponível localmente |
| **Taxas de Rendimento Escolar** | Aprovação, reprovação, abandono | Por escola × etapa × ano | A baixar |
| **INSE** (Nível Socioeconômico) | Indicador socioeconômico | Por escola | A baixar |
| **Taxa de Distorção Idade-Série** | % alunos com 2+ anos de atraso | Por escola × etapa | A baixar |
| **Adequação Formação Docente** | Adequação do professor à disciplina | Por escola | A baixar |
| **Regularidade do Corpo Docente** | Estabilidade do quadro (0-5) | Por escola | A baixar |

### 3.2 Fontes recomendadas (fortalecem o modelo)

- **IDEB** — usar com cautela (data leakage parcial): preferir nota Saeb separada OU IDEB de anos defasados (ex.: IDEB 2021 para prever abandono 2024).
- **Esforço Docente** — preditor estrutural relevante.
- **Média de Alunos por Turma** — controle de tamanho de turma.
- **Complexidade de Gestão da Escola** — controle de complexidade institucional.
- **Média de Horas-aula Diária** — diferencia integrais de regulares.

### 3.3 Apoio metodológico (não viram features)

- **Taxas de Não-resposta (TNR)** — filtro de qualidade dos dados: excluir escolas com TNR alta.

### 3.4 Excluídos do escopo

- Indicadores Financeiros (granularidade municipal/UF, não por escola).
- Remuneração Média de Docentes (verificar granularidade; se UF, descartar).
- Percentual de Docentes com Curso Superior (redundante com Adequação da Formação).
- Taxas de Transição (alto risco de data leakage com o target).

---

## 4. Stack tecnológica

### 4.1 Decisões já tomadas

| Camada | Tecnologia |
|--------|-----------|
| Linguagem principal | Python 3.10+ |
| Manipulação de dados | pandas |
| Modelagem (framework) | **scikit-learn** |
| Algoritmo principal | **XGBoost** (`XGBRegressor`, API compatível com sklearn) |
| Algoritmos comparação | Regressão Ridge (sklearn) e Random Forest (sklearn) |
| Explicabilidade | SHAP |
| Versionamento de modelos | MLflow (opcional) |
| Dashboard | **Streamlit** |
| Controle de versão | Git + GitHub |
| Containerização | Docker (opcional, para entrega) |

> **Importante:** XGBoost não faz parte do scikit-learn, mas sua API é compatível e pode ser usada dentro de `sklearn.pipeline.Pipeline` e `GridSearchCV` sem adaptações.

### 4.2 Pendente: nível de profundidade arquitetural — confirmar com orientador

A escolha de Streamlit cria uma tensão com o escopo original do TCC, que mencionava arquitetura full-stack (API REST + frontend SPA). A definição abaixo precisa ser alinhada com o orientador.

#### Cenário A — Streamlit puro (POC funcional)

Streamlit é o único frontend. Não há API REST. Modelo serializado em `.pkl` carregado diretamente pelo app.

**Vantagens:**
- Tempo de implementação compatível com prazo de TCC.
- Foco da contribuição fica no pipeline de ML e na análise de evasão.
- Reduz superfície de bugs e complexidade de deploy.

**Desvantagens / pontos a defender:**
- Reduz profundidade arquitetural típica de TCC em Engenharia de Software.
- Streamlit é apresentado como prova de conceito, não solução de produção.
- Limitação a ser declarada na monografia: "para uso em produção, seria necessária camada de API e frontend dedicado".

#### Cenário B — Arquitetura híbrida (Streamlit + API)

Streamlit consome uma API FastAPI separada que serve as predições. Mantém a arquitetura em camadas do escopo original, com o dashboard simplificado.

**Vantagens:**
- Preserva o caráter de Engenharia de Software do TCC.
- Permite separação de responsabilidades testável.
- API pode ser reutilizada por outros clientes (mobile, integração com sistemas escolares).

**Desvantagens:**
- Mais código, mais testes, mais complexidade de deploy.
- Streamlit como cliente de uma API local é "arquitetura desnecessária" se não for justificada.

#### Recomendação a discutir com orientador

Apresentar os dois cenários e perguntar qual o nível de profundidade arquitetural esperado para um TCC de Engenharia de Software. **Se ele aceitar o Cenário A, registrar isso explicitamente como limitação na monografia.**

---

## 5. Arquitetura proposta (Cenário A — Streamlit puro)

```
┌──────────────────────────────────────────────────────────┐
│                  DASHBOARD (Streamlit)                    │
│  - Ranking de escolas por risco                           │
│  - Visualização SHAP global e por escola                  │
│  - Análise de resíduos (P3): outliers acima/abaixo        │
│    do esperado pelo perfil                                │
│  - Filtros: município, mesorregião, localização           │
└────────────────────────┬─────────────────────────────────┘
                         │ (joblib.load)
                         ▼
┌──────────────────────────────────────────────────────────┐
│           CAMADA DE INFERÊNCIA (Python)                   │
│  - Carrega modelo treinado (.pkl ou MLflow)               │
│  - Aplica predições                                       │
│  - Calcula SHAP values                                    │
│  - Computa resíduos (predito − real)                      │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│         CAMADA DE MODELAGEM (sklearn + xgboost)           │
│  - sklearn Pipeline + ColumnTransformer                   │
│  - sklearn preprocessing (Scaler, OneHotEncoder)          │
│  - sklearn model_selection (KFold, GridSearchCV)          │
│  - sklearn metrics (RMSE, MAE, R², Spearman)              │
│  - xgboost.XGBRegressor (modelo principal)                │
│  - sklearn.linear_model.Ridge (baseline)                  │
│  - sklearn.ensemble.RandomForestRegressor (comparação)    │
│  - shap (explicabilidade)                                 │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              CAMADA DE DADOS (pandas)                     │
│  - ETL: integração Censo + Indicadores                    │
│  - Feature engineering                                    │
│  - Construção do target (taxa de abandono t+1)            │
│  - Validação e qualidade dos dados                        │
└──────────────────────────────────────────────────────────┘
```

---

## 6. Estrutura de pastas do projeto

```
tcc-evasao-escolar/
├── data/
│   ├── raw/                       # CSVs originais (não versionar; usar .gitignore)
│   │   ├── censo_2022/
│   │   ├── censo_2023/
│   │   ├── censo_2024/
│   │   ├── taxas_rendimento/
│   │   ├── inse/
│   │   └── outros_indicadores/
│   ├── interim/                   # Dados parciais do ETL
│   └── processed/                 # Tabela final pronta pra modelagem
│       └── dataset_modelagem.parquet
├── notebooks/
│   ├── 01_exploracao_inicial.ipynb
│   ├── 02_construcao_target.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_baseline_modelos.ipynb
│   ├── 05_tuning_xgboost.ipynb
│   └── 06_analise_shap_e_residuos.ipynb
├── src/
│   ├── data/
│   │   ├── load.py                # Funções de carga dos CSVs
│   │   ├── clean.py               # Limpeza e padronização
│   │   └── build_target.py        # Construção do target abandono t+1
│   ├── features/
│   │   ├── feature_engineer.py    # Engenharia de features
│   │   └── feature_selector.py    # Seleção de features
│   ├── models/
│   │   ├── train.py               # Treino (sklearn Pipeline + xgboost)
│   │   ├── evaluate.py            # Métricas
│   │   └── explain.py             # SHAP
│   └── recommend/
│       └── rules.py               # Recomendações baseadas em regras
├── app/
│   ├── dashboard.py               # App Streamlit (entrypoint)
│   └── pages/
│       ├── 1_ranking.py
│       ├── 2_escola_detalhe.py
│       └── 3_analise_residuos.py
├── models/
│   └── xgb_abandono_v1.pkl        # Modelo treinado serializado
├── tests/
│   ├── test_etl.py
│   ├── test_features.py
│   └── test_models.py
├── docs/
│   └── decisoes_projeto.md        # Este documento
├── requirements.txt
├── README.md
└── Dockerfile                     # opcional
```

### 6.1 Justificativa da estrutura para um TCC de Engenharia de Software

Esta organização aplica princípios reconhecidos:

- **Separação de responsabilidades:** ETL, modelagem, inferência e apresentação isoladas.
- **Reprodutibilidade:** notebooks numerados refletem a ordem do pipeline; código de produção em `src/`.
- **Testabilidade:** módulos em `src/` são unitários e podem ser testados isoladamente.
- **Versionamento:** Git para código; MLflow ou arquivos `.pkl` versionados manualmente para modelos.

---

## 7. Pipeline de ML (esboço do código com sklearn + xgboost)

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupKFold, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy.stats import spearmanr
from xgboost import XGBRegressor
import numpy as np

# Pré-processamento
preprocessor = ColumnTransformer([
    ('num', Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ]), features_numericas),
    ('cat', Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ]), features_categoricas)
])

# Pipeline completo
pipeline = Pipeline([
    ('preprocess', preprocessor),
    ('model', XGBRegressor(
        objective='reg:squarederror',
        random_state=42,
        n_jobs=-1
    ))
])

# Grid search com validação cruzada agrupada por município
# (evita data leakage de escolas vizinhas)
param_grid = {
    'model__n_estimators': [100, 300, 500],
    'model__max_depth': [3, 5, 7],
    'model__learning_rate': [0.01, 0.05, 0.1],
    'model__reg_alpha': [0, 0.1, 1],
    'model__reg_lambda': [1, 5, 10]
}

cv = GroupKFold(n_splits=5)
grid = GridSearchCV(
    pipeline,
    param_grid,
    cv=cv,
    scoring='neg_root_mean_squared_error',
    n_jobs=-1
)
grid.fit(X_train, y_train, groups=municipios_train)
```

---

## 8. Métricas de avaliação

### 8.1 Métricas primárias (regressão)
- **RMSE** — em pontos percentuais; principal métrica reportada.
- **MAE** — robusta a outliers; complementar ao RMSE.
- **R²** — explicação de variância (cuidado com overfitting).

### 8.2 Métricas de ranking (alinhadas à pergunta de pesquisa)
- **Spearman correlation** entre predito e real (mede qualidade do ranking).
- **Precision@K** — das top-K escolas previstas como risco, quantas estavam de fato no top-K real (binarização pós-hoc).

### 8.3 Métricas comparativas (validação de robustez)
- Comparar XGBoost vs Ridge vs Random Forest com mesma validação cruzada.
- Reportar erro padrão das métricas (via repetições do CV).

### 8.4 Avaliação qualitativa
- Análise de resíduos (P3): listar top-20 escolas com maior resíduo positivo (evasão acima do esperado) e top-20 com maior resíduo negativo (escolas resilientes).
- Inspeção qualitativa dos padrões dessas escolas.

---

## 9. Roadmap de execução

| Fase | Atividade | Critério de saída |
|------|-----------|-------------------|
| 1 | Download e organização das fontes de dados (Censo + indicadores) | Todos os arquivos em `data/raw/` |
| 2 | EDA inicial dos dados de Pernambuco | Notebook 01 concluído |
| 3 | Construção do target (taxa de abandono t+1) | Notebook 02; tabela com `(CO_ENTIDADE, ano, abandono_t1)` |
| 4 | Feature engineering e integração das fontes | Notebook 03; dataset final em `data/processed/` |
| 5 | Baseline com Ridge e Random Forest | Notebook 04; métricas registradas |
| 6 | Tuning de XGBoost | Notebook 05; melhor modelo serializado |
| 7 | Análise SHAP + análise de resíduos (P3) | Notebook 06 |
| 8 | Dashboard Streamlit | App rodando localmente |
| 9 | Documentação, testes e deploy via Docker | README + Dockerfile |
| 10 | Redação final da monografia | Texto pronto para qualificação |

---

## 10. Limitações a declarar na monografia

1. **Granularidade temporal:** Censo é anual; preditores dinâmicos (frequência, notas) não estão disponíveis. O modelo prevê risco baseado em perfil institucional, não em comportamento em tempo real.
2. **Definição operacional de evasão:** usa-se a "Taxa de Abandono" do INEP, que mede não-conclusão do ano letivo, não evasão escolar definitiva.
3. **N pequeno:** ~2.000 observações limita a capacidade de modelos complexos generalizarem.
4. **Sem validação prospectiva real:** o modelo é validado em dados históricos; não há acompanhamento de intervenções reais derivadas do sistema.
5. **Limitações arquiteturais do dashboard:** Streamlit é prova de conceito; uso em produção requereria arquitetura full-stack adicional. **(condicionado ao Cenário A)**
6. **Possíveis vieses não controlados:** seleção de variáveis disponíveis no Censo pode omitir fatores relevantes (clima escolar, violência local, contexto familiar).

---

## 11. Pendências para resolver com orientador

- [ ] Confirmar nível arquitetural esperado (Cenário A vs Cenário B da seção 4.2).
- [ ] Validar reposicionamento do objetivo geral (seção 1.2).
- [ ] Validar reescrita dos objetivos específicos para refletir "escola" no lugar de "aluno".
- [ ] Definir se MLflow é obrigatório ou opcional.
- [ ] Definir se Docker é obrigatório ou opcional.
- [ ] Validar uso de Taxa de Abandono como target (ao invés de evasão por linkage longitudinal).

---

*Documento gerado em colaboração com Claude, com discussões críticas registradas turno a turno.*
