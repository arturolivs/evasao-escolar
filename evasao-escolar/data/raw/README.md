# `data/raw/` — dados brutos do INEP

Os arquivos desta pasta **não são versionados** (somam cerca de 1 GB e têm licença
própria do INEP). O Git guarda apenas a estrutura de pastas e estes `README.md`.
Cada subpasta tem o seu, com a fonte, o link direto e o nome exato que o arquivo
precisa ter para o ETL encontrá-lo.

Todas as fontes são públicas e gratuitas, sem cadastro.

## O que baixar

| Pasta | Indicador | Anos | Download aprox. |
|---|---|---|---|
| [`censo/`](censo/README.md) | Microdados do Censo Escolar — tabela ESCOLA | 2022, 2023, 2024 | 88 MB |
| [`taxas_rendimento/`](taxas_rendimento/README.md) | Taxas de Rendimento Escolar (aprovação, reprovação, **abandono**) | 2022, 2023, 2024 | 202 MB |
| [`inse/`](inse/README.md) | Nível Socioeconômico (INSE/Saeb) | 2021 | 9 MB |
| [`indicador_regularidade_docente/`](indicador_regularidade_docente/README.md) | Regularidade do Corpo Docente (IRD) | 2022, 2023, 2024 | 58 MB |
| [`taxa_distorcao_idade/`](taxa_distorcao_idade/README.md) | Distorção Idade-Série (TDI) | 2022, 2023, 2024 | 101 MB |
| [`adequacao_formacao_docente/`](adequacao_formacao_docente/README.md) | Adequação da Formação Docente (AFD) | 2022, 2023, 2024 | 171 MB |
| [`esforco_docente/`](esforco_docente/README.md) | Esforço Docente (IED) | 2022, 2023, 2024 | 111 MB |
| [`complexidade_gestao_escola/`](complexidade_gestao_escola/README.md) | Complexidade de Gestão da Escola (ICG) | 2022, 2023, 2024 | 52 MB |

IED e ICG foram avaliados e **descartados** por não agregarem sinal (notebook
`11_avaliacao_ied_icg.py`), mas continuam no ETL porque essa avaliação faz parte
do resultado documentado na monografia.

## Estrutura final esperada

```
data/raw/
├── censo/
│   ├── microdados_ed_basica_2022.csv
│   ├── microdados_ed_basica_2023.csv
│   └── microdados_ed_basica_2024.csv
├── taxas_rendimento/
│   ├── tx_rend_escolas_2022.xlsx
│   ├── tx_rend_escolas_2023.xlsx
│   └── tx_rend_escolas_2024.xlsx
├── inse/
│   └── INSE_2021_escolas.xlsx
├── indicador_regularidade_docente/
│   ├── IRD_ESCOLAS_2022.xlsx
│   ├── IRD_ESCOLAS_2023.xlsx
│   └── IRD_ESCOLAS_2024.xlsx
├── taxa_distorcao_idade/
│   ├── TDI_ESCOLAS_2022.xlsx
│   ├── TDI_ESCOLAS_2023.xlsx
│   └── TDI_ESCOLAS_2024.xlsx
├── adequacao_formacao_docente/
│   ├── AFD_ESCOLAS_2022.xlsx
│   ├── AFD_ESCOLAS_2023.xlsx
│   └── AFD_ESCOLAS_2024.xlsx
├── esforco_docente/
│   ├── IED_ESCOLAS_2022.xlsx
│   ├── IED_ESCOLAS_2023.xlsx
│   └── IED_ESCOLAS_2024.xlsx
└── complexidade_gestao_escola/
    ├── ICG_ESCOLAS_2022.xlsx
    ├── ICG_ESCOLAS_2023.xlsx
    └── ICG_ESCOLAS_2024.xlsx
```

**O nome importa.** Os módulos de ETL montam o caminho a partir do ano
(`config.AFD_DIR / f"AFD_ESCOLAS_{ano}.xlsx"`) e falham com `FileNotFoundError`
se o nome divergir. O INEP muda a nomenclatura entre edições — em 2023, por
exemplo, o AFD vem como `AFD_ESCOLAS_2023_v1.1.xlsx` e precisa ser renomeado.
Renomeie o arquivo; não mude o código. A exceção é o Censo, cujo `load.py` tem
busca heurística por nome (qualquer CSV com `ed_basica` ou `escola` no nome).

Se preferir apontar para outra estrutura local, o único lugar a editar é
`src/data/config.py`.

## Onde os caminhos são definidos

Todos em `src/data/config.py`, derivados de `RAW_DIR`:

| Constante | Pasta |
|---|---|
| `CENSO_DIR` | `censo/` |
| — (literal em `build_taxas_rendimento.py`) | `taxas_rendimento/` |
| `INSE_DIR` | `inse/` |
| `IRD_DIR` | `indicador_regularidade_docente/` |
| `TDI_DIR` | `taxa_distorcao_idade/` |
| `AFD_DIR` | `adequacao_formacao_docente/` |
| `IED_DIR` | `esforco_docente/` |
| `ICG_DIR` | `complexidade_gestao_escola/` |

## Depois de baixar tudo

A partir de `evasao-escolar/`, com o ambiente do `requirements.txt` ativo:

```bash
python -m src.data.build_taxas_rendimento
python -m src.data.build_inse
python -m src.data.build_ird
python -m src.data.build_tdi
python -m src.data.build_afd
python -m src.data.build_esforco_docente
python -m src.data.build_complexidade_gestao

python notebooks/01_exploracao_inicial.py    # monta o painel escola × ano
python -m src.features.build_features        # → data/processed/features.parquet
```

A ordem completa do pipeline (que **não** é a ordem numérica dos notebooks) está
no `CLAUDE.md` da raiz e no `README.md` do projeto.

## Conferindo o que você baixou

As somas SHA-256 dos arquivos usados para gerar os números da monografia estão em
cada README de subpasta. Se a sua cópia divergir, o INEP republicou o arquivo —
os números do Capítulo 6 podem não reproduzir.

## Licença dos dados

Microdados e indicadores do INEP são de uso público, com condições definidas pelo
próprio instituto. Cite a fonte: Instituto Nacional de Estudos e Pesquisas
Educacionais Anísio Teixeira (INEP), Censo Escolar da Educação Básica e
Indicadores Educacionais.
