# `esforco_docente/` — Indicador de Esforço Docente (IED)

Classifica os professores em seis níveis de esforço exigido pelo exercício da
profissão (número de escolas, turnos, turmas, alunos e etapas em que atuam).
Nível 1 = menor esforço, nível 6 = maior.

> **Avaliado e descartado.** O notebook `11_avaliacao_ied_icg.py` mostrou que IED
> e ICG não agregam sinal ao modelo, e nenhum dos dois entra nas 39
> características finais. O ETL permanece porque essa avaliação é um resultado
> documentado na monografia — sem os arquivos, a ablação não reproduz.

## Onde baixar

Página oficial:
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/esforco-docente>

Links diretos (aba do ano → "Escolas"):

| Ano | URL | Tamanho |
|---|---|---|
| 2022 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022/IED_2022_ESCOLAS.zip> | 37 MB |
| 2023 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2023/IED_2023_ESCOLAS.zip> | 37 MB |
| 2024 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2024/IED_2024_ESCOLAS.zip> | 37 MB |

## O que extrair e como nomear

Dentro do ZIP: `IED_<ano>_ESCOLAS/IED_ESCOLAS_<ano>.xlsx`.

```
data/raw/esforco_docente/
├── IED_ESCOLAS_2022.xlsx     ~21 MB
├── IED_ESCOLAS_2023.xlsx     ~21 MB
└── IED_ESCOLAS_2024.xlsx     ~21 MB
```

Nome esperado: `IED_ESCOLAS_<ano>.xlsx` (`config.IED_DIR` +
`build_esforco_docente.py:71`).

## Formato

- **10 linhas de cabeçalho institucional**; o ETL lê com `header=10`.
- `--` vira `NaN`.
- Filtro do ETL: `SG_UF == "PE"` e `NO_DEPENDENCIA == "Estadual"`.

## Colunas usadas

| Coluna do INEP | Nome no projeto |
|---|---|
| `MED_CAT_1` … `MED_CAT_6` | `IED_MED_N1` … `IED_MED_N6` |

Cada uma é o **percentual** de docentes do Ensino Médio naquele nível.

O ETL deriva ainda `IED_MED_MEDIO`: a média dos níveis 1–6 ponderada pelos
percentuais, dividida pela soma observada (robusto a arredondamento do INEP).
Resume o esforço docente típico da escola numa única variável ordinal. Escolas
sem docentes em nenhum nível ficam com `NaN`.

## Consumido por

```bash
python -m src.data.build_esforco_docente
```

Saída: `data/interim/ied_pe_estadual.parquet`

Avaliação da contribuição ao modelo:

```bash
python notebooks/11_avaliacao_ied_icg.py    # → reports/ablacao_ied_icg.csv
```

## SHA-256 dos arquivos de referência

```
0c99a0caf77cc7b2a04a3d70f6880e026ac7ac229cb75c217451fd8383377804  IED_ESCOLAS_2022.xlsx
207b7c3cf1a15ecbe82b1f3b59dd86d7920e6a74c18bb5d2ca04997fbeef06c5  IED_ESCOLAS_2023.xlsx
899bed82980b3d7fece8892d69b9199e11b9ed5798da70f7089fcc432391ad45  IED_ESCOLAS_2024.xlsx
```
