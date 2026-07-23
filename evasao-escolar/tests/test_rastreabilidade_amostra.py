"""
Testes para o rastro que vai do painel histórico ao conjunto de modelagem
(src/features/build_features.py::rastrear_reducao_amostra).

A redução de 2.392 para 1.586 linhas não é perda de amostra: é a estrutura de
pares (ano t → abandono em t+1). Com três anos de painel só se formam dois
pares, e o último ano entra como alvo, não como origem. A revisão da banca
apontou que isso não estava explicitado.

O rastro é o que sustenta essa explicação na monografia, então precisa fechar
por aritmética: cada etapa tem de descontar exatamente o que remove, e a última
tem de coincidir com o dataset efetivamente gravado.

Rodar com:
    pytest tests/test_rastreabilidade_amostra.py -v
"""

import pandas as pd
import pytest

from src.features.build_features import rastrear_reducao_amostra


@pytest.fixture(scope="module")
def rastro() -> pd.DataFrame:
    return rastrear_reducao_amostra()


def test_cada_etapa_desconta_o_que_remove(rastro):
    """linhas_restantes[i] = linhas_restantes[i-1] − linhas_removidas[i]."""
    for anterior, atual in zip(rastro.itertuples(), rastro.iloc[1:].itertuples()):
        assert atual.linhas_restantes == (
            anterior.linhas_restantes - atual.linhas_removidas
        ), f"etapa '{atual.etapa}' não fecha com a anterior"


def test_a_amostra_nunca_cresce(rastro):
    assert rastro["linhas_restantes"].is_monotonic_decreasing
    assert rastro["escolas_restantes"].is_monotonic_decreasing


def test_primeira_etapa_nao_remove_nada(rastro):
    """O painel é o ponto de partida, não um filtro."""
    assert rastro["linhas_removidas"].iloc[0] == 0


def test_ultima_etapa_bate_com_o_dataset_gravado(rastro):
    """Se o rastro divergir do parquet, a explicação da monografia mente."""
    from src.data import config

    caminho = config.PROCESSED_DIR / "features.parquet"
    if not caminho.exists():
        pytest.skip("features.parquet ausente — rode src.features.build_features")

    df = pd.read_parquet(caminho)
    assert rastro["linhas_restantes"].iloc[-1] == len(df)
    assert rastro["escolas_restantes"].iloc[-1] == df["CO_ENTIDADE"].nunique()


def test_ano_final_sai_inteiro_como_ano_origem(rastro):
    """
    O ano mais recente do painel não pode sobrar como origem: sem o ano
    seguinte, não há abandono a observar. Se um dia sobrar, houve vazamento.
    """
    from src.data import config

    caminho = config.PROCESSED_DIR / "features.parquet"
    if not caminho.exists():
        pytest.skip("features.parquet ausente")

    df = pd.read_parquet(caminho)
    painel = pd.read_parquet(
        config.INTERIM_DIR / "painel_escola_ano_pe_estadual_em.parquet"
    )
    assert painel["NU_ANO_CENSO"].max() not in set(df["NU_ANO_CENSO"])


def test_criterio_documentado_em_toda_etapa(rastro):
    """Cada linha precisa dizer por que remove — é o que vai para o quadro."""
    assert not rastro["criterio"].isna().any()
    assert (rastro["criterio"].str.len() > 20).all()
