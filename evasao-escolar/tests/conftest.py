import pandas as pd
import pytest


@pytest.fixture
def painel_3escolas():
    """Painel Censo com 3 escolas × anos variados.

    Escola 101: anos 2022, 2023, 2024
    Escola 102: anos 2022, 2023
    Escola 103: apenas 2022

    Usado em test_build_target.py para validar o join temporal t → t+1.
    """
    return pd.DataFrame({
        "CO_ENTIDADE": [101, 101, 101, 102, 102, 103],
        "NU_ANO_CENSO": [2022, 2023, 2024, 2022, 2023, 2022],
        "feature_a": [1.0, 1.1, 1.2, 2.0, 2.1, 3.0],
    })


@pytest.fixture
def taxas_3escolas():
    """Painel mínimo de taxas de rendimento (substitui build_taxas_rendimento).

    Escola 101: tem dados em 2023 e 2024
        → gera pares de join (t=2022→target 2023) e (t=2023→target 2024)
    Escola 102: tem dados apenas em 2023
        → gera par (t=2022→target 2023); linha (102, 2023) fica sem match
    Escola 103: ausente em taxas → todas as linhas do painel são descartadas
    """
    return pd.DataFrame({
        "NU_ANO_CENSO": [2023, 2024, 2023],
        "CO_ENTIDADE": [101, 101, 102],
        "TAXA_ABND_MED": [5.0, 6.0, 8.0],
    })
