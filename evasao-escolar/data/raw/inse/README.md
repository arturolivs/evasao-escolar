# `inse/` — Nível Socioeconômico (INSE/Saeb)

Média do nível socioeconômico dos alunos da escola e a distribuição percentual
deles em 8 níveis. É a principal característica de contexto social do modelo.

## Onde baixar

Página oficial:
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/nivel-socioeconomico>

Link direto (aba 2021 → "Escolas"), `.xlsx` avulso, sem ZIP:

| Edição | URL | Tamanho |
|---|---|---|
| 2021 — escolas | <https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2021/nivel_socioeconomico/INSE_2021_escolas.xlsx> | 8,7 MB |

## Como nomear

```
data/raw/inse/
└── INSE_2021_escolas.xlsx
```

Nome esperado: `INSE_2021_escolas.xlsx` (montado em `build_inse.py:57` a partir da
constante `_ANO_INSE = 2021`). O arquivo já vem baixado com esse nome — não
renomeie.

## Por que só 2021

O INSE é calculado nos ciclos bienais do Saeb, não todo ano. **A edição 2021 é
tratada como atributo estático da escola**, válida para todo o painel 2022–2024.
Isso está documentado na monografia como limitação, não como descuido.

Existe também uma edição 2023 por escola no site do INEP
(`INSE_2023_escolas.xlsx`, mesma pasta, ano 2023). **O pipeline atual não a
utiliza** — quando os dados do projeto foram coletados, só o agregado estadual de
2023 estava publicado, e é esse arquivo que ainda está na pasta local
(`INSE_2023_estados.xlsx`, sem granularidade escolar, não lido por nenhum
módulo). Incorporar o INSE 2023 escolar mudaria as características e exigiria
regerar todos os números do Capítulo 6; é decisão de projeto, não ajuste de ETL.

## Formato

- **Sem linhas de cabeçalho institucional**: o ETL lê com `header=0`.
- Filtro do ETL: `SG_UF == "PE"` e `TP_TIPO_REDE == 2` (estadual).
- A chave da escola vem como `ID_ESCOLA` (não `CO_ENTIDADE`) e é renomeada.

## Colunas usadas

| Coluna do INEP | Nome no projeto |
|---|---|
| `ID_ESCOLA` | `CO_ENTIDADE` |
| `MEDIA_INSE` | `INSE_MEDIA` |
| `INSE_CLASSIFICACAO` | `INSE_NIVEL` |
| `QTD_ALUNOS_INSE` | `INSE_QTD_ALUNOS` |
| `PC_NIVEL_1..8` | `INSE_PC_N1..N8` |
| `CO_MUNICIPIO`, `NO_MUNICIPIO`, `NO_ESCOLA`, `TP_LOCALIZACAO` | idem / `NO_ENTIDADE` |

## Consumido por

```bash
python -m src.data.build_inse
```

Saída: `data/interim/inse_pe_estadual.parquet`

## SHA-256 dos arquivos de referência

```
8b5c5e3841d9ff591460b294b78c2ce9e1f7b430dc74c6c8e03a3acc980c38d8  INSE_2021_escolas.xlsx
9fc2f0c16128527ce05e4b4f8db79291c16aad34351511b277427b738803caa8  INSE_2023_estados.xlsx   (presente, não usado)
```
