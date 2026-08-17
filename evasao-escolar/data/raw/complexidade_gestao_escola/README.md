# `complexidade_gestao_escola/` — Complexidade de Gestão da Escola (ICG)

Classifica a escola em seis níveis de complexidade de gestão, combinando porte,
número de turnos, etapas e modalidades ofertadas. Nível 1 = menor complexidade,
nível 6 = maior.

> **Avaliado e descartado.** O notebook `11_avaliacao_ied_icg.py` mostrou que ICG
> e IED não agregam sinal ao modelo, e nenhum dos dois entra nas 39
> características finais. O ETL permanece porque essa avaliação é um resultado
> documentado na monografia — sem os arquivos, a ablação não reproduz.

## Onde baixar

Página oficial:
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/complexidade-de-gestao-da-escola>

Links diretos (aba do ano → "Escolas"):

| Ano | URL | Tamanho |
|---|---|---|
| 2022 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022/ICG_2022_ESCOLAS.zip> | 17 MB |
| 2023 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2023/ICG_2023_ESCOLAS.zip> | 17 MB |
| 2024 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2024/ICG_2024_ESCOLAS.zip> | 17 MB |

## O que extrair e como nomear

Dentro do ZIP: `ICG_<ano>_ESCOLAS/ICG_ESCOLAS_<ano>.xlsx`.

```
data/raw/complexidade_gestao_escola/
├── ICG_ESCOLAS_2022.xlsx     ~10 MB
├── ICG_ESCOLAS_2023.xlsx     ~10 MB
└── ICG_ESCOLAS_2024.xlsx     ~11 MB
```

Nome esperado: `ICG_ESCOLAS_<ano>.xlsx` (`config.ICG_DIR` +
`build_complexidade_gestao.py:55`).

## Formato

- **10 linhas de cabeçalho institucional**; o ETL lê com `header=10`.
- `--` vira `NaN`.
- Filtro do ETL: `SG_UF == "PE"` e `NO_DEPENDENCIA == "Estadual"`.

## Colunas usadas

| Coluna do INEP | Nome no projeto |
|---|---|
| `COMPLEX` | `ICG_TEXTO` → `ICG_NIVEL` |

`COMPLEX` vem como texto (`"Nível  1"` … `"Nível  6"`, com espaço duplo). O ETL
extrai o inteiro por expressão regular e o converte na variável ordinal
`ICG_NIVEL` (1–6). Escolas sem nível atribuído são removidas.

## Diferença em relação aos demais indicadores

O ICG é definido para **toda escola em atividade**, não por etapa de ensino — não
há colunas `MED_*`. Por isso o ETL não consegue filtrar "escola com EM" na
origem; esse recorte só acontece na junção com o painel, em
`src/features/build_features.py`.

## Consumido por

```bash
python -m src.data.build_complexidade_gestao
```

Saída: `data/interim/icg_pe_estadual.parquet`

Avaliação da contribuição ao modelo:

```bash
python notebooks/11_avaliacao_ied_icg.py    # → reports/ablacao_ied_icg.csv
```

## SHA-256 dos arquivos de referência

```
2e7d76ffef5f5ed7837a1580a76cf57d16b591b044354e171651f8d1c27a138e  ICG_ESCOLAS_2022.xlsx
99a6908e99ff5b399ede8a84b619b1ca87f110c5f1db98bfc8e3b6eccd99fada  ICG_ESCOLAS_2023.xlsx
7e9f858aa6b5bb8fe9fb8f47b9a14d83ff7f2b048e4b3d163d8f8bf6a438cb9e  ICG_ESCOLAS_2024.xlsx
```
