# `taxa_distorcao_idade/` — Taxa de Distorção Idade-Série (TDI)

Percentual de alunos com dois anos ou mais de atraso em relação à série. É um dos
sinais mais fortes de risco de abandono no Ensino Médio.

## Onde baixar

Página oficial:
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/taxas-de-distorcao-idade-serie>

Links diretos (aba do ano → "Escolas"):

| Ano | URL | Tamanho |
|---|---|---|
| 2022 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022/TDI_2022_ESCOLAS.zip> | 34 MB |
| 2023 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2023/TDI_2023_ESCOLAS.zip> | 34 MB |
| 2024 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2024/TDI_2024_ESCOLAS.zip> | 33 MB |

## O que extrair e como nomear

Dentro do ZIP: `TDI_<ano>_ESCOLAS/TDI_ESCOLAS_<ano>.xlsx`.

```
data/raw/taxa_distorcao_idade/
├── TDI_ESCOLAS_2022.xlsx     ~18 MB
├── TDI_ESCOLAS_2023.xlsx     ~18 MB
└── TDI_ESCOLAS_2024.xlsx     ~18 MB
```

Nome esperado: `TDI_ESCOLAS_<ano>.xlsx` (`config.TDI_DIR` + `build_tdi.py:52`).

## Formato

- **8 linhas de cabeçalho institucional** (não 10, como nos indicadores docentes);
  o ETL lê com `header=8`.
- `--` significa "a escola não oferta esta série" e vira `NaN`.
- Filtro do ETL: `SG_UF == "PE"` e `NO_DEPENDENCIA == "Estadual"`.
- Escolas com `TDI_MED` nulo (sem oferta de EM) são removidas.

## Colunas usadas

| Coluna do INEP | Nome no projeto | |
|---|---|---|
| `MED_CAT_0` | `TDI_MED` | total do Ensino Médio |
| `MED_01_CAT_0` | `TDI_MED_S1` | 1ª série |
| `MED_02_CAT_0` | `TDI_MED_S2` | 2ª série |
| `MED_03_CAT_0` | `TDI_MED_S3` | 3ª série |
| `MED_04_CAT_0` | `TDI_MED_S4` | 4ª série (profissional integrada) |

`MED_04_CAT_0` pode não existir em alguns anos; o ETL seleciona apenas as colunas
presentes no arquivo, sem quebrar.

## Consumido por

```bash
python -m src.data.build_tdi
```

Saída: `data/interim/tdi_pe_estadual.parquet`

## SHA-256 dos arquivos de referência

```
6e436653599e97ed32fe156a42d0ea69cc355c2ea701afa88208bcaaf16f2980  TDI_ESCOLAS_2022.xlsx
cfa556493d82ebec06c107d796ad25ffb33bfacee30ab58a92d6eb86c381fd8f  TDI_ESCOLAS_2023.xlsx
303da1f591671d9db3ed7e2ced79466ebde87bd52b52829a1bd95a07c5de439a  TDI_ESCOLAS_2024.xlsx
```
