"""
Testes para a flag `oferta_em_nao_seriado` (src/features/build_features.py).

As taxas de EM publicadas pelo INEP (`*_CAT_MED`) agregam 1ª a 3ª série,
4ª série e o não seriado (EJA/modular). Só S1–S3 entram como features, então
nessas escolas a taxa do EM não é redutível às três séries — o total pode
inclusive superar o máximo delas. A flag existe para tornar esse subgrupo
explícito; se ela deixar de ser criada ou de marcar as escolas certas, as
estatísticas descritivas do Quadro 5 voltam a parecer contraditórias sem
que nada quebre.

Rodar com:
    pytest tests/test_nao_seriado.py -v
"""

import pandas as pd
import pytest

from src.features.build_features import COL_NAO_SERIADO, _adicionar_nao_seriado


@pytest.fixture
def taxas_mistas() -> pd.DataFrame:
    """Três escolas: só séries regulares, com não seriado, e com 4ª série."""
    return pd.DataFrame({
        "CO_ENTIDADE": [101, 102, 103],
        "NU_ANO_CENSO": [2022, 2022, 2022],
        "TAXA_REPROV_MED": [4.0, 55.3, 22.8],
        "TAXA_REPROV_MED_S1": [4.0, None, None],
        "TAXA_REPROV_MED_S2": [4.0, None, 20.6],
        "TAXA_REPROV_MED_S3": [4.0, None, 22.2],
        "TAXA_REPROV_MED_S4": [None, None, 40.0],
        "TAXA_REPROV_MED_NS": [None, 55.3, None],
    })


@pytest.fixture
def base() -> pd.DataFrame:
    return pd.DataFrame({
        "CO_ENTIDADE": [101, 102, 103],
        "NU_ANO_CENSO": [2022, 2022, 2022],
    })


def test_marca_apenas_escolas_fora_das_series_regulares(base, taxas_mistas):
    """Só as escolas com 4ª série ou não seriado recebem a marca."""
    resultado = _adicionar_nao_seriado(base, taxas_mistas)
    marca = resultado.set_index("CO_ENTIDADE")[COL_NAO_SERIADO]

    assert marca[101] == 0, "escola só com séries regulares não deve ser marcada"
    assert marca[102] == 1, "escola com não seriado deve ser marcada"
    assert marca[103] == 1, "escola com 4ª série deve ser marcada"


def test_flag_e_binaria_e_sem_missing(base, taxas_mistas):
    resultado = _adicionar_nao_seriado(base, taxas_mistas)
    assert resultado[COL_NAO_SERIADO].isna().sum() == 0
    assert set(resultado[COL_NAO_SERIADO].unique()) <= {0, 1}


def test_escola_ausente_nas_taxas_nao_e_marcada(taxas_mistas):
    """Sem linha correspondente nas taxas, a marca cai para 0 (não para NaN)."""
    base = pd.DataFrame({"CO_ENTIDADE": [999], "NU_ANO_CENSO": [2022]})
    resultado = _adicionar_nao_seriado(base, taxas_mistas)
    assert resultado[COL_NAO_SERIADO].iloc[0] == 0


def test_nao_altera_numero_de_linhas(base, taxas_mistas):
    """O merge não pode duplicar linhas do painel."""
    resultado = _adicionar_nao_seriado(base, taxas_mistas)
    assert len(resultado) == len(base)


def test_ausencia_das_colunas_do_inep_nao_quebra(base):
    """Sem as colunas de 4ª série/não seriado, o pipeline segue sem a flag."""
    taxas = pd.DataFrame({
        "CO_ENTIDADE": [101],
        "NU_ANO_CENSO": [2022],
        "TAXA_REPROV_MED": [4.0],
    })
    resultado = _adicionar_nao_seriado(base, taxas)
    assert COL_NAO_SERIADO not in resultado.columns
    assert len(resultado) == len(base)


# ---------------------------------------------------------------------------
# Coerência do dataset final (o que o Quadro 5 mostra)
# ---------------------------------------------------------------------------

def test_taxa_em_acima_das_series_so_ocorre_em_escolas_marcadas():
    """
    A taxa do EM só pode superar o máximo de S1–S3 quando há matrícula fora
    das séries regulares. Se isso ocorrer numa escola não marcada, a flag
    está capturando o subgrupo errado.
    """
    from src.data import config

    caminho = config.PROCESSED_DIR / "features.parquet"
    if not caminho.exists():
        pytest.skip("features.parquet ausente — rode src.features.build_features")

    df = pd.read_parquet(caminho)
    if COL_NAO_SERIADO not in df.columns:
        pytest.skip("dataset gerado antes da criação da flag")

    series = df[["reprov_s1_t", "reprov_s2_t", "reprov_s3_t"]].max(axis=1)
    acima = df["reprov_t"] > series + 0.05
    assert not (acima & (df[COL_NAO_SERIADO] == 0)).any(), (
        "há escola com taxa de EM acima do máximo das séries sem estar "
        "marcada como oferta fora das séries regulares"
    )
