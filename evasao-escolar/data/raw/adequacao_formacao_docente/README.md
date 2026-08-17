# `adequacao_formacao_docente/` — Adequação da Formação Docente (AFD)

Distribuição percentual dos professores da escola em cinco grupos de adequação
entre a formação e a disciplina que lecionam.

## Onde baixar

Página oficial:
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/adequacao-da-formacao-docente>

Links diretos (aba do ano → "Escolas"):

| Ano | URL | Tamanho |
|---|---|---|
| 2022 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022/AFD_2022_ESCOLAS.zip> | 57 MB |
| 2023 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2023/AFD_2023_ESCOLAS.zip> | 57 MB |
| 2024 | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2024/AFD_2024_ESCOLAS.zip> | 57 MB |

## O que extrair e como nomear

Dentro do ZIP: `AFD_<ano>_ESCOLAS/AFD_ESCOLAS_<ano>.xlsx`.

> **Atenção ao ano de 2023.** O arquivo vem como
> `AFD_ESCOLAS_2023_v1.1.xlsx` (o ZIP inclui também uma nota de retificação em
> PDF). **Renomeie para `AFD_ESCOLAS_2023.xlsx`** — é o único caso, entre todos
> os indicadores, em que o nome publicado difere do esperado.

```
data/raw/adequacao_formacao_docente/
├── AFD_ESCOLAS_2022.xlsx     ~35 MB
├── AFD_ESCOLAS_2023.xlsx     ~35 MB   ← renomeado de AFD_ESCOLAS_2023_v1.1.xlsx
└── AFD_ESCOLAS_2024.xlsx     ~35 MB
```

Nome esperado: `AFD_ESCOLAS_<ano>.xlsx` (`config.AFD_DIR` + `build_afd.py:52`).

## Formato

- **10 linhas de cabeçalho institucional**; o ETL lê com `header=10`.
- `--` significa ausência de docentes naquela etapa e vira `NaN`.
- Filtro do ETL: `SG_UF == "PE"` e `NO_DEPENDENCIA == "Estadual"`.
- Escolas com todos os cinco grupos nulos (sem oferta de EM) são removidas.

## Colunas usadas

| Coluna do INEP | Nome no projeto | Significado |
|---|---|---|
| `MED_CAT_1` | `AFD_MED_G1` | licenciatura na disciplina que leciona (formação ideal) |
| `MED_CAT_2` | `AFD_MED_G2` | bacharelado na disciplina, sem licenciatura |
| `MED_CAT_3` | `AFD_MED_G3` | licenciatura em área diferente da disciplina |
| `MED_CAT_4` | `AFD_MED_G4` | outra formação superior, não relacionada |
| `MED_CAT_5` | `AFD_MED_G5` | sem ensino superior |

Todos em percentual de docentes do Ensino Médio da escola.

## Consumido por

```bash
python -m src.data.build_afd
```

Saída: `data/interim/afd_pe_estadual.parquet`

## SHA-256 dos arquivos de referência

```
f85d46aa28bbca68d1e257c425d4bdd4c7a9e2b8d2b0b1b903e9670577e3ce72  AFD_ESCOLAS_2022.xlsx
f07e19917b01d31f4945524b059e717e6842a81d0aa2eb67056f418c238daede  AFD_ESCOLAS_2023.xlsx
3c6b2d457341d7059289c27b412f02a53f30d525f0c84f52c4dbdaf36c512531  AFD_ESCOLAS_2024.xlsx
```
