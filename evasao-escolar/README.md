# TCC — Sistema de Identificação Precoce de Escolas em Risco de Evasão

Projeto de monografia em Engenharia de Software. Predição da taxa de
abandono em escolas estaduais de ensino médio de Pernambuco, com
explicabilidade via SHAP.

> **Status atual:** Frente B — ETL inicial implementado. Falta integrar
> indicadores externos (Taxas de Rendimento, INSE, Distorção, etc.) e
> construir o target.

---

## Setup

```bash
# Python 3.10 ou superior
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

## Estrutura esperada de dados

```
data/raw/
├── censo_2022/
│   └── microdados_ed_basica_2022.csv
├── censo_2023/
│   └── microdados_ed_basica_2023.csv
└── censo_2024/
    └── microdados_ed_basica_2024.csv
```

Se os nomes dos arquivos forem diferentes (o INEP nem sempre é consistente),
ajuste `src/data/config.py` ou deixe que `load.py` busque heuristicamente
por arquivos contendo `ed_basica` ou `escola` no nome.

## Como rodar a ETL inicial

```bash
# Da raiz do projeto:
python notebooks/01_exploracao_inicial.py
```

Esse script:
1. Carrega o CSV de escolas de cada ano (2022, 2023, 2024).
2. Aplica filtros: PE + rede estadual + em atividade + com EM.
3. Imprime estatísticas de sanity check.
4. Salva o painel longitudinal em `data/interim/painel_escola_ano_pe_estadual_em.parquet`.

## Rodar os testes

```bash
pytest tests/ -v
```

## Próximos passos do projeto

- [ ] Baixar Taxas de Rendimento Escolar do INEP (target).
- [ ] Baixar indicadores: INSE, Distorção Idade-Série, Adequação Formação Docente, Regularidade Corpo Docente.
- [ ] Implementar `src/data/build_target.py` — construção do alvo `taxa_abandono_t1`.
- [ ] Implementar `src/features/feature_engineer.py` — features derivadas.
- [ ] Treinar baseline (Ridge, Random Forest) e XGBoost.
- [ ] Análise SHAP global e local; análise de resíduos (P3).
- [ ] Dashboard Streamlit.

Ver `docs/decisoes_projeto.md` para o roadmap completo e justificativas
metodológicas.
