"""
Testes para a função _validar_painel em src/data/build_school_panel.py.

A função já existe no código de produção; os testes garantem que as
validações continuam funcionando se a lógica for alterada.

Rodar com:
    pytest tests/test_panel.py -v
"""

import pandas as pd
import pytest

from src.data.build_school_panel import _validar_painel


def _painel_valido():
    """Painel mínimo sem duplicatas e sem nulos nas chaves."""
    return pd.DataFrame({
        "CO_ENTIDADE": [1, 2, 1],
        "NU_ANO_CENSO": [2022, 2022, 2023],
        "feature_x": [10.0, 20.0, 11.0],
    })


# ---------------------------------------------------------------------------
# Painel válido
# ---------------------------------------------------------------------------

def test_painel_valido_nao_levanta():
    _validar_painel(_painel_valido())  # não deve lançar exceção


# ---------------------------------------------------------------------------
# Chave primária duplicada
# ---------------------------------------------------------------------------

def test_chave_duplicada_levanta_value_error():
    df = pd.DataFrame({
        "CO_ENTIDADE": [1, 1],
        "NU_ANO_CENSO": [2022, 2022],
    })
    with pytest.raises(ValueError, match="duplicadas"):
        _validar_painel(df)


def test_chave_duplicada_mensagem_informa_n_linhas():
    df = pd.DataFrame({
        "CO_ENTIDADE": [5, 5, 5],
        "NU_ANO_CENSO": [2023, 2023, 2023],
    })
    with pytest.raises(ValueError, match="3"):
        _validar_painel(df)


def test_chave_diferente_em_ano_nao_duplicata():
    """Mesma escola em anos distintos não é duplicata."""
    df = pd.DataFrame({
        "CO_ENTIDADE": [1, 1],
        "NU_ANO_CENSO": [2022, 2023],
    })
    _validar_painel(df)  # não deve lançar exceção


# ---------------------------------------------------------------------------
# CO_ENTIDADE nulo
# ---------------------------------------------------------------------------

def test_co_entidade_nulo_levanta_value_error():
    df = pd.DataFrame({
        "CO_ENTIDADE": [None, 2],
        "NU_ANO_CENSO": [2022, 2022],
    })
    with pytest.raises(ValueError, match="CO_ENTIDADE nulo"):
        _validar_painel(df)


def test_co_entidade_todos_nulos_levanta_value_error():
    df = pd.DataFrame({
        "CO_ENTIDADE": [None, None],
        "NU_ANO_CENSO": [2022, 2023],
    })
    with pytest.raises(ValueError, match="CO_ENTIDADE nulo"):
        _validar_painel(df)


# ---------------------------------------------------------------------------
# NU_ANO_CENSO nulo
# ---------------------------------------------------------------------------

def test_nu_ano_censo_nulo_levanta_value_error():
    df = pd.DataFrame({
        "CO_ENTIDADE": [1, 2],
        "NU_ANO_CENSO": [None, 2023],
    })
    with pytest.raises(ValueError, match="NU_ANO_CENSO nulo"):
        _validar_painel(df)


# ---------------------------------------------------------------------------
# Ordem das validações
# ---------------------------------------------------------------------------

def test_duplicata_detectada_antes_de_nulo():
    """Se o painel tem duplicata E nulo, o erro de duplicata vem primeiro."""
    df = pd.DataFrame({
        "CO_ENTIDADE": [1, 1, None],
        "NU_ANO_CENSO": [2022, 2022, 2023],
    })
    with pytest.raises(ValueError, match="duplicadas"):
        _validar_painel(df)
