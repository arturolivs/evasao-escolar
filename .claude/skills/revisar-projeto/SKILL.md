---
name: revisar-projeto
description: Executa a auditoria completa (7 pilares) do projeto de predição de evasão escolar de PE — casamento temporal t→t+1, vazamento espacial por município, engenharia das 39 features, Precision@K e Spearman, consistência SHAP, viés em escolas indígenas/quilombolas e qualidade de software. Usar quando o usuário pedir revisão, auditoria, validação do pipeline, checagem de vazamento de dados ou verificação antes de entregar a monografia.
---

# Revisão Completa do Projeto (Code Review & Audit)

Checklist rigorosa e procedimento de auditoria do projeto de predição de evasão escolar.

**Todos os comandos rodam a partir de `evasao-escolar/`** (é lá que vive o pacote `src/`), com o venv ativo.

Esta skill audita o **código**. Para as outras dimensões, use as skills irmãs:
`/validar-ambiente` (versões fixadas), `/validar-numeros` (valores do `.docx` × pipeline),
`/validar-documento` (estrutura e edição da monografia).

## Linha de base da última auditoria

Use para detectar regressão. Achados que **permanecem abertos** estão marcados.

| Pilar | Resultado |
|---|---|
| 1. Casamento temporal | ✅ `features.parquet` só tem 2022 e 2023; 2024 só em predição |
| 2. Vazamento espacial | ✅ `GroupKFold` por `CO_MUNICIPIO`, disjunção travada por teste |
| 3. Features | ✅ 39 confirmadas, 0 NaN, nenhuma de vazamento — o fallback de média global de `build_features.py:193` **nunca dispara** (medido) |
| 4. Métricas | ⚠️ funciona como ranking, **não** como regressão: RMSE 2,874 > dummy 2,540, R² −0,33 |
| 5. SHAP | ✅ aditividade travada — nota: ordem SHAP ≠ ordem por ganho |
| 6. Equidade | ✅ viés de −6,12 p.p. medido **e** exibido no painel (`ressalva_equidade`) |
| 7. Arquitetura | ✅ 138 testes, sem ciclos, `features.parquet` regerado em 31/07 e bit-idêntico |

## Checklist de Revisão (7 Pilares)

### 1. Integridade Teórica e Casamento Temporal (t → t+1)
- [ ] Verificar se as features de treino usam estritamente o ano `t` para prever o abandono no ano `t+1`.
- [ ] Confirmar que 2024 não está sendo usado como ano de origem em pipelines de **treino** (não existe alvo de 2025); 2024 só entra em modo predição.
- [ ] Testar a consistência temporal: `pytest tests/test_build_target.py`.

### 2. Prevenção de Vazamento Espacial/Geográfico
- [ ] Garantir que na validação cruzada (`GroupKFold` / split espacial) escolas de um mesmo município **nunca** estejam simultaneamente em treino e teste.
- [ ] Revisar `tests/test_models.py` para assegurar que nenhum município vaza entre folds.
- [ ] Conferir o `split_temporal` em `src/models/train.py`.

### 3. Engenharia de Features (39 Características)
- [ ] Verificar se imputações de dados faltantes usam a média regional do mesmo ano, sem informação do futuro.
- [ ] Confirmar que o fallback de média global **continua sem disparar** (ver bloco abaixo).
- [ ] Confirmar que variáveis redundantes ou com vazamento de resposta (ex.: taxa de aprovação do próprio t+1) foram descartadas.
- [ ] Checar o tratamento de escolas não seriadas (EJA/módulos) no cálculo do TDI e das taxas por série: `pytest tests/test_nao_seriado.py`.
- [ ] Conferir a rastreabilidade da amostra: `reports/rastreabilidade_amostra.csv` e `pytest tests/test_rastreabilidade_amostra.py`.

>  ✅ **Ressalva fechada em 31/07.** `_imputar_por_meso` agrupa por
> `["CO_MESORREGIAO", "NU_ANO_CENSO"]` nas três chamadas, mas tem um fallback de **média
> global** (linha 193) que agruparia 2022+2023 — vazamento transdutivo em potencial.
> Instrumentei a função e contei quantos valores cairiam nele: **zero**. Todo grupo
> mesorregião×ano tem ao menos um valor observado, então o caminho existe no código e nunca
> é percorrido com os dados atuais.
>
> Vale para **estes** dados. Se uma edição futura do INEP trouxer indicador ausente em toda
> uma mesorregião num ano, o fallback passa a disparar e o problema deixa de ser teórico.
> Reconferir com:
> ```bash
> python - <<'PY'
> import logging; logging.disable(logging.INFO)
> import src.features.build_features as bf
> disparos = []
> orig = bf._imputar_por_meso
> def espiao(df, cols, group_cols):
>     for c in cols:
>         if c not in df.columns: continue
>         medias = df.groupby(group_cols)[c].transform("mean")
>         n = int((df[c].isna() & medias.isna()).sum())
>         if n: disparos.append((c, n))
>     return orig(df, cols, group_cols)
> bf._imputar_por_meso = espiao
> bf.construir_dataset()
> print(disparos or "fallback global nunca disparou")
> PY
> ```
> Blindagem opcional de uma linha, caso queira eliminar o risco futuro: trocar a média
> global por média **por ano** (`df.groupby("NU_ANO_CENSO")[col].transform("mean")`).
> Preserva o comportamento atual e fecha o caminho.

### 4. Desempenho do Modelo e Métricas de Priorização
- [ ] Avaliar `Precision@K` (Top 10% / Top 150 escolas) em `reports/metricas_xgboost.csv`.
- [ ] Avaliar a correlação de Spearman (ordenação): o ranking é consistente de um ano para o outro? Ver `reports/metricas_cv_repetida.csv` e `reports/metricas_ss13_cenarios.csv`.
- [ ] Verificar se os baselines (Ridge, Random Forest) seguem comparados ao XGBoost: `reports/metricas_baselines.csv`.
- [ ] Confirmar que nenhum texto do projeto afirma superioridade geral do XGBoost.

**Referência medida** (não suavizar em nenhum texto gerado):

| | Dummy | Ridge | Random Forest | XGBoost |
|---|---|---|---|---|
| CV repetida — Spearman / P@K | — / 0,068 | 0,428 / **0,513** | **0,431** / 0,501 | 0,416 / 0,504 |
| Temporal — Spearman / P@K | — / 0,089 | 0,330 / 0,380 | 0,343 / 0,405 | **0,348** / **0,418** |
| Temporal — RMSE | **2,540** | 2,891 | 2,751 | 2,874 |

Duas leituras obrigatórias: o XGBoost tem **RMSE pior que o dummy** no teste temporal
(R² −0,33) — o ganho é de ordenação, 0,418 vs 0,089 (4,7×); e os três modelos são
**estatisticamente indistinguíveis**. Por transição anual (SS13), 2022→2023 rende mais
(0,469 / 0,627) que 2023→2024 (0,367 / 0,381), acompanhando a queda do abandono médio
(1,36% → 0,88%).

### 5. Interpretabilidade e Explicação (SHAP)
- [ ] Garantir que soma das contribuições SHAP + base value == valor predito: `pytest tests/test_explain.py`.
- [ ] Validar a tradução amigável das variáveis técnicas para linguagem de gestor (`src/recommend/labels.py`).
- [ ] Conferir `reports/shap_importancia.csv` contra `reports/xgboost_feature_importance.csv`.

### 6. Equidade e Análise de Viés
- [ ] Monitorar resíduos em escolas de localização diferenciada (indígenas e quilombolas): `reports/residuos_diagnostico.csv` e `reports/residuos_grupo_temporal.csv`.
- [ ] Garantir que o painel exiba a ressalva sobre superestimação de risco nesses grupos (`app/dashboard.py`).

**Viés medido** (agregando `residuos_grupo_temporal.csv`, ano-feature 2023):

| grupo | n | real | previsto | resíduo médio |
|---|---|---|---|---|
| diferenciada (indígena/quilombola) | 41 | 4,96 | **11,08** | **−6,12** |
| rural | 69 | 0,88 | 0,50 | +0,38 |
| urbana | 679 | 0,63 | 0,56 | +0,07 |

Agrava que `is_loc_diferenciada` é a característica **nº 1 por ganho** no XGBoost (0,239) —
o modelo usa a flag do grupo como atalho preditivo.

> ✅ **Achado fechado.** A ressalva vive no domínio, não na UI: `service.ressalva_equidade()`
> devolve o texto para `LOC_DIFERENCIADA` e `None` para os demais grupos, com os números
> vindos da constante `VIES_DIFERENCIADA`. O painel exibe em três pontos — aba de detalhe da
> escola, gráfico de equidade do Panorama e rodapé. Coberto por 12 testes em
> `tests/test_recommend.py` (inclusive a ausência de aviso nos grupos calibrados).
>
> Verificar em auditorias futuras:
> ```bash
> grep -c -E "ressalva_equidade|RESSALVA_DIFERENCIADA" app/dashboard.py   # espera-se >= 2
> pytest tests/test_recommend.py -q -k ressalva
> ```
> **Fechado também no CSV** (30/07): `exportar_ranking()` acrescenta a coluna «Ressalva»,
> preenchida por `service.ressalva_equidade_curta()`. A predição não circula mais fora do
> painel sem o contexto — 41 das 789 linhas do ranking de 2023 saem com o aviso.

### 7. Qualidade de Software e Arquitetura
- [ ] Executar a suíte completa: `pytest` (138 testes na última verificação).
- [ ] Verificar dependências cíclicas entre `src.data`, `src.features`, `src.models` e `src.recommend` (o fluxo é unidirecional nessa ordem).
- [ ] Garantir que os `.parquet` de `data/interim/` e `data/processed/` estejam mais novos que os `.joblib` de `models/` — modelo treinado em features velhas é erro silencioso.
  Satisfeito desde 31/07: `features.parquet` foi regerado (155.894 bytes, 0 células
  alteradas, rastreabilidade idêntica) e agora é mais recente que `xgboost_v1.joblib`.

---

## Roteiro de Execução

### Passo 0 — Ambiente
```bash
python -c "import sklearn, xgboost; print(sklearn.__version__, xgboost.__version__)"
```
Deve dar `1.8.0 3.2.0`. Se divergir, **parar** e rodar `/validar-ambiente` — a partição do
`GroupKFold` muda com a versão do scikit-learn e invalida as métricas.

### Passo 1 — Sanidade do código
```bash
pytest -v
```

### Passo 2 — Reexecução do pipeline (só se as fontes em `data/raw/` mudaram)
ETL por indicador (cada um tem entry-point próprio):
```bash
python -m src.data.build_taxas_rendimento
python -m src.data.build_inse
python -m src.data.build_ird
python -m src.data.build_tdi
python -m src.data.build_afd
python -m src.data.build_esforco_docente
python -m src.data.build_complexidade_gestao
```

Painel escola×ano, features e treino:
```bash
python notebooks/01_exploracao_inicial.py   # monta e salva o painel escola×ano
python -m src.features.build_features       # gera data/processed/features.parquet
python notebooks/06_baseline_modelos.py     # baselines -> models/baseline_*_v1.joblib
python notebooks/08_tuning_xgboost.py       # XGBoost   -> models/xgboost_v1.joblib
python notebooks/09_shap_diagnostico.py     # SHAP + resíduos
```

> `src/data/build_school_panel.py` **não** tem bloco `__main__` — apesar de alguns comentários citarem `python -m src.data.build_school_panel`, o painel é montado pelo notebook 01.

### Passo 3 — Auditoria de resíduos e equidade
Inspecionar os artefatos de saída:
- `reports/figuras/` (72 figuras)
- `reports/residuos_*.csv`
- `reports/metricas_*.csv`

### Passo 4 — Verificação forte de sincronia
Comparar o `features.parquet` em disco com o que o código atual produz, sem sobrescrever nada:

```bash
python - <<'PY'
import logging, pandas as pd
logging.disable(logging.INFO)
from src.features.build_features import construir_dataset, ID_COLS
from src.data import config
disco = pd.read_parquet(config.PROCESSED_DIR / "features.parquet")
novo = construir_dataset()
print("disco:", disco.shape, "| recalculado:", novo.shape)
print("mesmas colunas:", list(disco.columns) == list(novo.columns))
num = disco.select_dtypes("number").columns
print("maior diferenca numerica:",
      (disco[num].fillna(-999).reset_index(drop=True)
       - novo[num].fillna(-999).reset_index(drop=True)).abs().max().max())
PY
```
Esperado: `(1586, 45)` nos dois lados, colunas iguais, diferença **0.0**. Isso torna
irrelevante o fato de `features.parquet` ter data mais recente que `models/*.joblib`.

### Passo 5 — Relatório
Reportar por pilar: o que passou, o que falhou (com a saída real do comando) e o que não foi
verificado. Não declarar um pilar como aprovado sem a saída do comando correspondente.
