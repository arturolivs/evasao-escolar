# `indicador_regularidade_docente/` — Regularidade do Corpo Docente (IRD)

Mede a permanência dos professores na escola ao longo dos anos, numa escala
contínua (aprox. 0 a 5): valores altos indicam corpo docente estável, valores
baixos indicam rotatividade.

## Onde baixar

Página oficial:
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/regularidade-do-corpo-docente>

Links diretos (aba do ano → "Escolas"):

| Ano | URL | Tamanho |
|---|---|---|
| 2022 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022/IRD_2022_ESCOLAS.zip> | 19 MB |
| 2023 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2023/IRD_2023_ESCOLAS.zip> | 19 MB |
| 2024 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2024/IRD_2024_ESCOLAS.zip> | 19 MB |

Repare na inversão: o ZIP é `IRD_<ano>_ESCOLAS.zip`, o XLSX dentro dele é
`IRD_ESCOLAS_<ano>.xlsx`.

## O que extrair e como nomear

Dentro do ZIP: `IRD_<ano>_ESCOLAS/IRD_ESCOLAS_<ano>.xlsx`.

```
data/raw/indicador_regularidade_docente/
├── IRD_ESCOLAS_2022.xlsx     ~11 MB
├── IRD_ESCOLAS_2023.xlsx     ~11 MB
└── IRD_ESCOLAS_2024.xlsx     ~11 MB
```

Nome esperado: `IRD_ESCOLAS_<ano>.xlsx` (`config.IRD_DIR` +
`build_ird.py:41`). Renomeie se o INEP publicar com sufixo de versão.

## Formato

- **10 linhas de cabeçalho institucional**; o ETL lê com `header=10`.
- `--` vira `NaN`.
- Filtro do ETL: `SG_UF == "PE"` e `NO_DEPENDENCIA == "Estadual"`.

## Colunas usadas

| Coluna do INEP | Nome no projeto |
|---|---|
| `EDU_BAS_CAT_0` | `IRD_MED` |

O IRD é publicado para o conjunto da educação básica da escola, não por etapa —
por isso a coluna de origem é `EDU_BAS_*` e não `MED_*`. O nome `IRD_MED` segue a
convenção das demais características do projeto; o valor é o da escola inteira.

Mais identificação: `CO_ENTIDADE`, `CO_MUNICIPIO`, `NO_MUNICIPIO`, `NO_ENTIDADE`,
`NO_CATEGORIA`.

## Consumido por

```bash
python -m src.data.build_ird
```

Saída: `data/interim/ird_pe_estadual.parquet`

## SHA-256 dos arquivos de referência

```
d2aa5651dd5c4555389491577ea6894273b45d100f12137ddd33fcd1ab12cb3f  IRD_ESCOLAS_2022.xlsx
e598e7a4382d1347340c5e517ac1fe5aced3bd2da7f1d89d4c6716c82e4d5f83  IRD_ESCOLAS_2023.xlsx
3a21d5ecd03fbae387894c3967cd4447bca9e92ec43221265a2624a894cf3125  IRD_ESCOLAS_2024.xlsx
```
