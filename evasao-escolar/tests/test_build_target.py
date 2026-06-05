"""
Testes para src/data/build_target.py.

O risco central deste módulo é o join temporal: features do ano t
devem casar com target do ano t+1. Um erro aqui (ex: off-by-one)
produz um modelo errado sem lançar exceção.

Rodar com:
    pytest tests/test_build_target.py -v
"""

from unittest.mock import patch

import pytest

from src.data.build_target import construir_target_abandono_t1

_PATCH = "src.data.build_target.construir_painel_taxas"


# ---------------------------------------------------------------------------
# Correção do join temporal
# ---------------------------------------------------------------------------

def test_escola_ano_t_recebe_target_de_t1(painel_3escolas, taxas_3escolas):
    """(escola, 2022) deve receber a taxa de abandono observada em 2023."""
    with patch(_PATCH, return_value=taxas_3escolas):
        resultado = construir_target_abandono_t1(painel_3escolas, anos_target=[2023, 2024])

    linha = resultado.loc[
        (resultado["CO_ENTIDADE"] == 101) & (resultado["NU_ANO_CENSO"] == 2022)
    ]
    assert len(linha) == 1
    assert linha["taxa_abandono_t1"].iloc[0] == 5.0


def test_escola_ano_t1_recebe_target_de_t2(painel_3escolas, taxas_3escolas):
    """(escola, 2023) deve receber a taxa de abandono observada em 2024."""
    with patch(_PATCH, return_value=taxas_3escolas):
        resultado = construir_target_abandono_t1(painel_3escolas, anos_target=[2023, 2024])

    linha = resultado.loc[
        (resultado["CO_ENTIDADE"] == 101) & (resultado["NU_ANO_CENSO"] == 2023)
    ]
    assert len(linha) == 1
    assert linha["taxa_abandono_t1"].iloc[0] == 6.0


# ---------------------------------------------------------------------------
# Descarte de linhas sem par no ano seguinte (inner join)
# ---------------------------------------------------------------------------

def test_escola_sem_target_no_ano_seguinte_e_descartada(painel_3escolas, taxas_3escolas):
    """Escola 102 no ano 2023 não tem par em 2024 nas taxas → linha descartada."""
    with patch(_PATCH, return_value=taxas_3escolas):
        resultado = construir_target_abandono_t1(painel_3escolas, anos_target=[2023, 2024])

    assert not (
        (resultado["CO_ENTIDADE"] == 102) & (resultado["NU_ANO_CENSO"] == 2023)
    ).any()


def test_escola_ausente_em_taxas_e_descartada(painel_3escolas, taxas_3escolas):
    """Escola 103 não aparece nas taxas → todas as suas linhas são descartadas."""
    with patch(_PATCH, return_value=taxas_3escolas):
        resultado = construir_target_abandono_t1(painel_3escolas, anos_target=[2023, 2024])

    assert 103 not in resultado["CO_ENTIDADE"].values


def test_shape_correto(painel_3escolas, taxas_3escolas):
    """Output deve ter exatamente 3 linhas: (101,2022), (101,2023), (102,2022)."""
    with patch(_PATCH, return_value=taxas_3escolas):
        resultado = construir_target_abandono_t1(painel_3escolas, anos_target=[2023, 2024])

    assert len(resultado) == 3


# ---------------------------------------------------------------------------
# Ausência de data leakage
# ---------------------------------------------------------------------------

def test_taxa_abnd_med_do_proprio_ano_nao_vaza(painel_3escolas, taxas_3escolas):
    """A coluna TAXA_ABND_MED (abandono do ano t) não pode aparecer no output."""
    with patch(_PATCH, return_value=taxas_3escolas):
        resultado = construir_target_abandono_t1(painel_3escolas, anos_target=[2023, 2024])

    assert "TAXA_ABND_MED" not in resultado.columns


def test_coluna_target_existe_no_output(painel_3escolas, taxas_3escolas):
    """Output deve conter a coluna 'taxa_abandono_t1'."""
    with patch(_PATCH, return_value=taxas_3escolas):
        resultado = construir_target_abandono_t1(painel_3escolas, anos_target=[2023, 2024])

    assert "taxa_abandono_t1" in resultado.columns


def test_anos_de_target_nao_aparecem_em_nu_ano_censo(painel_3escolas, taxas_3escolas):
    """NU_ANO_CENSO no output deve conter apenas anos de features (t), nunca t+1."""
    with patch(_PATCH, return_value=taxas_3escolas):
        resultado = construir_target_abandono_t1(painel_3escolas, anos_target=[2023, 2024])

    anos_no_output = set(resultado["NU_ANO_CENSO"].unique())
    # 2024 é ano de target — não deve aparecer como chave de features
    assert 2024 not in anos_no_output
    assert anos_no_output.issubset({2022, 2023})


# ---------------------------------------------------------------------------
# Features do painel são preservadas
# ---------------------------------------------------------------------------

def test_features_do_painel_original_sao_preservadas(painel_3escolas, taxas_3escolas):
    """Merge não deve descartar colunas de features existentes no painel."""
    with patch(_PATCH, return_value=taxas_3escolas):
        resultado = construir_target_abandono_t1(painel_3escolas, anos_target=[2023, 2024])

    assert "feature_a" in resultado.columns
