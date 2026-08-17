# `taxas_rendimento/` — Taxas de Rendimento Escolar

A fonte mais importante do projeto: dela sai a **taxa de abandono do Ensino
Médio** (`TAXA_ABND_MED`), que é o alvo previsto. Traz também aprovação e
reprovação, por escola e por série.

## Onde baixar

Página oficial:
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/taxas-de-rendimento-escolar>

Links diretos (aba do ano → arquivo "Escolas"):

| Ano | URL | Tamanho |
|---|---|---|
| 2022 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022/tx_rend_escolas_2022.zip> | 69 MB |
| 2023 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2023/tx_rend_escolas_2023.zip> | 67 MB |
| 2024 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2024/tx_rend_escolas_2024.zip> | 67 MB |

Baixe a versão **por escola**, não a por município, estado ou Brasil — o projeto
precisa da granularidade escolar.

## O que extrair e como nomear

Dentro do ZIP: `tx_rend_escolas_<ano>/tx_rend_escolas_<ano>.xlsx`.

Copie o `.xlsx` para esta pasta:

```
data/raw/taxas_rendimento/
├── tx_rend_escolas_2022.xlsx     ~38 MB
├── tx_rend_escolas_2023.xlsx     ~37 MB
└── tx_rend_escolas_2024.xlsx     ~37 MB
```

Nome esperado: `tx_rend_escolas_<ano>.xlsx` (literal em
`build_taxas_rendimento.py:75`). Qualquer divergência gera `FileNotFoundError`.

## Formato

- **8 linhas de cabeçalho institucional** antes do cabeçalho real; o ETL lê com
  `header=8`.
- `--` significa "a escola não oferta esta série/etapa" e vira `NaN`.
- Filtro do ETL: `SG_UF == "PE"` e `NO_DEPENDENCIA == "Estadual"`.

## Colunas usadas

Prefixo `1_CAT` = aprovação, `2_CAT` = reprovação, `3_CAT` = abandono.

| Coluna do INEP | Nome no projeto | |
|---|---|---|
| `3_CAT_MED` | `TAXA_ABND_MED` | **alvo do modelo** |
| `3_CAT_MED_01..04`, `_NS` | `TAXA_ABND_MED_S1..S4`, `_NS` | abandono por série |
| `1_CAT_MED*` | `TAXA_APROV_MED*` | aprovação, total e por série |
| `2_CAT_MED*` | `TAXA_REPROV_MED*` | reprovação, total e por série |

Mais identificação: `CO_ENTIDADE`, `CO_MUNICIPIO`, `NO_MUNICIPIO`, `NO_ENTIDADE`,
`NO_CATEGORIA`.

## Consumido por

```bash
python -m src.data.build_taxas_rendimento
```

Saída: `data/interim/taxas_rendimento_pe_estadual_em.parquet`

O casamento temporal t → t+1 (característica do ano `t` prevê abandono em `t+1`)
é feito depois, em `src/data/build_target.py` e `src/features/build_features.py`,
e é coberto por `tests/test_build_target.py`.

## Por que os três anos são necessários

O alvo é sempre do ano seguinte. Com anos-característica 2022 e 2023, o abandono
vem de 2023 e 2024 — sem o arquivo de 2024 não existe alvo para as observações de
2023. O ano 2024 entra **somente** como origem em modo predição (alvo 2025),
nunca no treino.

## SHA-256 dos arquivos de referência

```
56f06980a6dd4129fa8c3a73786dabdb6750ef3e95b20a5dfc658a475246707c  tx_rend_escolas_2022.xlsx
23189652c505a919ba71d999240c7775db47e66beef48c934cadd0fe46f9181e  tx_rend_escolas_2023.xlsx
39ec73652775d9af5ef9ae870eb0af9eadebfd84c94b14ab0d4a45b8d009b9cf  tx_rend_escolas_2024.xlsx
```
