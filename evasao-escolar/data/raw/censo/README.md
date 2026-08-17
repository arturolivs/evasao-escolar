# `censo/` — Microdados do Censo Escolar (tabela ESCOLA)

Base do painel escola × ano: matrículas, docentes, infraestrutura, localização,
dependência administrativa e situação de funcionamento. É de onde saem os filtros
do universo (PE, rede estadual, EM regular, escola em atividade) e a maior parte
das 39 características.

## Onde baixar

Página oficial:
<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar>

Links diretos (ZIP completo do ano):

| Ano | URL | Tamanho |
|---|---|---|
| 2022 | <https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2022.zip> | 25 MB |
| 2023 | <https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2023.zip> | 31 MB |
| 2024 | <https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2024.zip> | 32 MB |

## O que extrair e como nomear

Cada ZIP traz cinco tabelas (escola, turma, aluno, docente, gestor), dicionário de
dados e leia-me. **Só a tabela ESCOLA é usada.** Ela fica em:

```
microdados_censo_escolar_<ano>/dados/microdados_ed_basica_<ano>.csv
```

Em 2024 a pasta interna se chama `microdados_censo_escolar_2024_defeso/`; o nome
do CSV é o mesmo.

Copie os três CSVs para esta pasta, sem subpastas:

```
data/raw/censo/
├── microdados_ed_basica_2022.csv     ~181 MB
├── microdados_ed_basica_2023.csv     ~200 MB
└── microdados_ed_basica_2024.csv     ~208 MB
```

As demais tabelas do ZIP podem ser descartadas — as de aluno e docente somam
vários GB e não são lidas pelo projeto.

## Nome do arquivo

Padrão esperado: `microdados_ed_basica_<ano>.csv`, definido em
`config.CENSO_ESCOLA_FILENAME_TEMPLATE`.

Esta é a única pasta com tolerância a nome divergente: se o arquivo padrão não
existir, `src/data/load.py` procura recursivamente qualquer `.csv` cujo nome
contenha `ed_basica` ou `escola` (e avisa no log se achar mais de um). Ainda
assim, prefira renomear para o padrão.

## Formato

- Separador `;`, codificação `latin-1` (constantes `CSV_SEPARATOR` e
  `CSV_ENCODING` em `config.py`).
- Sem linhas de cabeçalho institucional — a primeira linha já é o cabeçalho.
- A carga é seletiva por coluna (`load.py`): o CSV inteiro nunca é lido em memória.

## Filtros aplicados pelo ETL

Definidos em `config.py` e aplicados em `filter_pe_estadual_em.py`:

| Filtro | Coluna | Valor |
|---|---|---|
| Pernambuco | `SG_UF` / `CO_UF` | `PE` / `26` |
| Rede estadual | `TP_DEPENDENCIA` | `2` |
| Em atividade | `TP_SITUACAO_FUNCIONAMENTO` | `1` |
| Oferta Ensino Médio | `QT_MAT_MED` | `> 0` |

## Consumido por

`src/data/load.py` → `src/data/filter_pe_estadual_em.py` →
`src/data/build_school_panel.py`, executado por:

```bash
python notebooks/01_exploracao_inicial.py
```

`build_school_panel.py` **não tem `__main__`** — rodar `python -m
src.data.build_school_panel` não funciona, apesar do que dizem comentários
antigos nos notebooks 04 e 12.

Saída: `data/interim/painel_escola_ano_pe_estadual_em.parquet`

## SHA-256 dos arquivos de referência

Estes são os arquivos usados para gerar os números da monografia:

```
dfa3b5e8ce977f4e650c84c19b741e063f4c94fe63841c6cbce60831deb52602  microdados_ed_basica_2022.csv
b2dd87c32cf25af4af89202adb908d17b0d3fea99e2ea046229aa86a9d69679a  microdados_ed_basica_2023.csv
3fb4d93c714b7d9303e34430f0287ca102bf984a4769d5abaca21eb4d1453bc9  microdados_ed_basica_2024.csv
```
