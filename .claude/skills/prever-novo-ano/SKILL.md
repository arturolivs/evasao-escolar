---
name: prever-novo-ano
description: Gera a lista de priorização de escolas para um novo ano letivo (ex.: risco de abandono em 2025 a partir das características de 2024) sem vazamento de dados, e atualiza o painel Streamlit. Usar quando o usuário pedir predição de um novo ano, ranking de risco atualizado, rodar o modo predição ou incorporar dados novos do Censo/INEP.
---

# Predição para Novos Anos

Passo a passo para gerar a lista de priorização de um novo ano letivo sem vazamento de dados.

O modelo aprende uma função geral (características da escola em `t` → taxa de abandono em `t+1`), então vale para qualquer ano. **Nunca retreine incluindo o ano-alvo**: a predição precisa ser fora da amostra.

**Todos os comandos rodam a partir de `evasao-escolar/`**, com o venv ativo.

Rodar `/validar-ambiente` antes: a predição aplica um modelo serializado, e ambiente fora do
de referência produz números que não conversam com os do Capítulo 6.

## Passos Operacionais

### 1. Validação das Fontes
Confirmar que os dados do ano `N` existem em `data/raw/`, nas subpastas:
`censo/`, `taxas_rendimento/`, `inse/`, `indicador_regularidade_docente/`,
`taxa_distorcao_idade/`, `adequacao_formacao_docente/`, `esforco_docente/`,
`complexidade_gestao_escola/`.

Se o ano é novo, rodar o ETL do indicador correspondente antes (ver a skill `revisar-projeto`, Passo 2) e reconstruir o painel com `python notebooks/01_exploracao_inicial.py`.

### 2. Geração da Predição
Modo predição — monta as features do ano `N` (dispensa o alvo `N+1`) e aplica o modelo serializado:

```bash
python -m src.models.predict 2024      # prevê o abandono de 2025
```

O ano é **argumento posicional**, não `--year`. Padrão: 2024.

Saídas:
- `data/processed/predicao_abandono_2025.csv` — ranking com `posicao`, `CO_ENTIDADE`, `NO_ENTIDADE`, `NO_MUNICIPIO`, `risco_abandono_previsto`
- `data/processed/features_predicao_2025.parquet` — features usadas (salvas por `salvar_features=True`)

### 3. Inspeção de Resultados
- [ ] O CSV cobre todas as escolas estaduais de EM ativas, sem `NaN` nas colunas de saída.
- [ ] O risco médio previsto é plausível frente ao histórico (comparar com a distribuição de `taxa_abandono_t1` em `data/processed/features.parquet`).
- [ ] O Top 10 impresso pelo comando não tem escola repetida nem risco negativo (a saída é clipada em 0).
- [ ] Sanidade automatizada: `pytest tests/test_predicao.py`.

### 4. Atualização do Painel
```bash
streamlit run app/dashboard.py
```
O serviço (`ServicoPriorizacao`) é cacheado por sessão via `@st.cache_resource` — reinicie o processo do Streamlit para carregar as novas predições.

## Ressalva obrigatória
Ao entregar o ranking, repetir o aviso de viés: o modelo tende a **superestimar** o risco em escolas indígenas e quilombolas. A leitura SHAP é diagnóstica, não causal — não derive recomendação prescritiva dela.
