# Notebooks de apresentação

Dois notebooks para executar diante da banca. Eles **não substituem** os scripts
`notebooks/01..16_*.py`, que continuam sendo o pipeline. Aqui só se leem os
artefatos já gerados e se chamam as mesmas funções de `src/`. Nada é gravado em
disco, e os dois juntos rodam em menos de 20 segundos.

| Notebook | Conteúdo | Slides |
|---|---|---|
| `01_dados_e_caracteristicas.ipynb` | Concentração do abandono, funil 2.392 → 1.586, alvo, os 6 grupos de características, correlações, os 138 testes | 4, 8, 9, 10, 12 |
| `02_resultados_e_predicao.ipynb` | Teste do ano nunca visto com os 4 modelos treinados ao vivo (Quadro 10), alcance da lista, SHAP, laudo de uma escola, equidade, ranking de 2025 | 14–20 |

## Pré-requisitos

- Venv da raiz ativa, com `requirements.txt` e `requirements-apresentacao.txt`.
- `data/interim/` com os parquets do ETL, `data/processed/features.parquet`
  e `models/xgboost_v1.joblib`.

## Como abrir

**VS Code:** abrir o `.ipynb`, escolher o kernel `.venv` e usar *Run All*.

**Navegador:** `pip install jupyterlab` e, de dentro de `evasao-escolar/`,
`jupyter lab notebooks/apresentacao`.

Os arquivos já estão salvos com as saídas, e servem de plano B se a execução
ao vivo falhar.

## Conferência

Na execução de 30/10/2026, todos os números bateram com a monografia e os slides:
- Quadro 10: XGBoost com 0,348, 0,418 e 2,874;
- ganho de 4,7× sobre o acaso;
- ROC AUC de 0,798;
- alcance de 28%, 46% e 57%;
- resíduo de −6,12 p.p. nas escolas diferenciadas;
- 30 de 38 características com relação significativa;
- 138 testes passando.
