"""
Testes para os ETLs dos indicadores de gestão/esforço docente:
  - src/data/build_esforco_docente.py  (IED)
  - src/data/build_complexidade_gestao.py (ICG)

Rodar com:
    pytest tests/test_indicadores_gestao.py -v
"""

from unittest.mock import patch

import pandas as pd
import pytest

from src.data.build_esforco_docente import (
    IED_NIVEL_COLS,
    _indice_medio,
    carregar_ano as carregar_ied,
    construir_painel_ied,
)
from src.data.build_complexidade_gestao import (
    _parse_nivel,
    carregar_ano as carregar_icg,
    construir_painel_icg,
)


# ===========================================================================
# IED — Esforço Docente
# ===========================================================================

def _raw_ied() -> pd.DataFrame:
    """Simula o xlsx do INEP após header=10.

    Escola A (26001): PE, Estadual, tem EM → mantida
    Escola B (26002): PE, Estadual, sem EM ('--' em todos os níveis) → removida
    Escola C (35001): SP, Estadual → filtrada pela UF
    """
    data = {
        "SG_UF":          ["PE",       "PE",       "SP"],
        "NO_DEPENDENCIA": ["Estadual", "Estadual", "Estadual"],
        "CO_ENTIDADE":    ["26001",    "26002",    "35001"],
        "CO_MUNICIPIO":   ["260000",   "260010",   "350000"],
        "NO_MUNICIPIO":   ["Recife",   "Olinda",   "São Paulo"],
        "NO_ENTIDADE":    ["Escola A", "Escola B", "Escola C"],
        "NO_CATEGORIA":   ["Estadual", "Estadual", "Estadual"],
        # Escola A: 100% no nível 3 → índice = 3.0
        "MED_CAT_1": [0.0,  "--", 0.0],
        "MED_CAT_2": [0.0,  "--", 0.0],
        "MED_CAT_3": [100.0, "--", 50.0],
        "MED_CAT_4": [0.0,  "--", 50.0],
        "MED_CAT_5": [0.0,  "--", 0.0],
        "MED_CAT_6": [0.0,  "--", 0.0],
    }
    return pd.DataFrame(data)


def test_indice_medio_ponderacao():
    """100% no nível 3 → índice 3.0; 50/50 entre 2 e 4 → 3.0."""
    df = pd.DataFrame({
        "IED_MED_N1": [0.0, 0.0],
        "IED_MED_N2": [0.0, 50.0],
        "IED_MED_N3": [100.0, 0.0],
        "IED_MED_N4": [0.0, 50.0],
        "IED_MED_N5": [0.0, 0.0],
        "IED_MED_N6": [0.0, 0.0],
    })
    idx = _indice_medio(df)
    assert idx.iloc[0] == pytest.approx(3.0)
    assert idx.iloc[1] == pytest.approx(3.0)


def test_indice_medio_soma_zero_vira_nan():
    """Escola sem docentes em nenhum nível (soma 0) → índice NaN."""
    df = pd.DataFrame({c: [0.0] for c in IED_NIVEL_COLS})
    assert _indice_medio(df).isna().all()


def test_ied_sentinel_vira_nan_e_escola_sem_em_removida():
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_ied()),
    ):
        df = carregar_ied(2023)

    assert "26002" not in df["CO_ENTIDADE"].astype(str).values  # sem EM removida
    for col in IED_NIVEL_COLS:
        assert df[col].dtype in (float, "float64")


def test_ied_filtra_apenas_pe_estadual():
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_ied()),
    ):
        df = carregar_ied(2023)

    assert "35001" not in df["CO_ENTIDADE"].astype(str).values


def test_ied_indice_calculado_na_carga():
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_ied()),
    ):
        df = carregar_ied(2023)

    escola_a = df[df["CO_ENTIDADE"] == 26001].iloc[0]
    assert escola_a["IED_MED_MEDIO"] == pytest.approx(3.0)


def test_ied_co_entidade_int64_e_ano_injetado():
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_ied()),
    ):
        df = carregar_ied(2023)

    assert str(df["CO_ENTIDADE"].dtype) == "Int64"
    assert (df["NU_ANO_CENSO"] == 2023).all()


def test_ied_arquivo_ausente_levanta_file_not_found():
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            carregar_ied(2023)


def test_ied_painel_concatena_anos():
    def _frame(ano):
        return pd.DataFrame({
            "NU_ANO_CENSO": [ano],
            "CO_ENTIDADE": pd.array([100 + ano], dtype="Int64"),
            "NO_ENTIDADE": [f"Escola {ano}"],
            "CO_MUNICIPIO": pd.array([2600001], dtype="Int64"),
            "NO_MUNICIPIO": ["Recife"],
            "NO_CATEGORIA": ["Estadual"],
            **{c: [10.0] for c in IED_NIVEL_COLS},
            "IED_MED_MEDIO": [3.5],
        })

    with patch("src.data.build_esforco_docente.carregar_ano", side_effect=_frame):
        painel = construir_painel_ied(anos=[2022, 2023])

    assert set(painel["NU_ANO_CENSO"]) == {2022, 2023}
    assert list(painel.columns)[-len(IED_NIVEL_COLS) - 1:] == IED_NIVEL_COLS + ["IED_MED_MEDIO"]


def test_ied_painel_sem_arquivo_levanta_runtime_error():
    with patch(
        "src.data.build_esforco_docente.carregar_ano",
        side_effect=FileNotFoundError("ausente"),
    ):
        with pytest.raises(RuntimeError, match="Nenhum arquivo"):
            construir_painel_ied(anos=[2023])


# ===========================================================================
# ICG — Complexidade de Gestão
# ===========================================================================

def _raw_icg() -> pd.DataFrame:
    """Simula o xlsx do INEP após header=10.

    Escola A (26001): PE, Estadual, nível 4 → mantida
    Escola B (26002): PE, Estadual, '--' → removida (sem nível)
    Escola C (35001): SP → filtrada pela UF
    """
    return pd.DataFrame({
        "SG_UF":          ["PE",       "PE",       "SP"],
        "NO_DEPENDENCIA": ["Estadual", "Estadual", "Estadual"],
        "CO_ENTIDADE":    ["26001",    "26002",    "35001"],
        "CO_MUNICIPIO":   ["260000",   "260010",   "350000"],
        "NO_MUNICIPIO":   ["Recife",   "Olinda",   "São Paulo"],
        "NO_ENTIDADE":    ["Escola A", "Escola B", "Escola C"],
        "NO_CATEGORIA":   ["Estadual", "Estadual", "Estadual"],
        "COMPLEX":        ["Nível  4", "--",       "Nível  2"],
    })


def test_parse_nivel_extrai_inteiro():
    s = pd.Series(["Nível  1", "Nível  6", "--", None])
    out = _parse_nivel(s)
    assert out.tolist()[:2] == [1, 6]
    assert out.isna().tolist()[2:] == [True, True]
    assert str(out.dtype) == "Int64"


def test_icg_remove_sem_nivel_e_filtra_uf():
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_icg()),
    ):
        df = carregar_icg(2023)

    codigos = df["CO_ENTIDADE"].astype(str).values
    assert "26002" not in codigos  # sem nível removida
    assert "35001" not in codigos  # SP filtrada
    assert df[df["CO_ENTIDADE"] == 26001].iloc[0]["ICG_NIVEL"] == 4


def test_icg_co_entidade_int64_e_ano_injetado():
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_icg()),
    ):
        df = carregar_icg(2023)

    assert str(df["CO_ENTIDADE"].dtype) == "Int64"
    assert str(df["ICG_NIVEL"].dtype) == "Int64"
    assert (df["NU_ANO_CENSO"] == 2023).all()


def test_icg_arquivo_ausente_levanta_file_not_found():
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            carregar_icg(2023)


def test_icg_painel_concatena_anos():
    def _frame(ano):
        return pd.DataFrame({
            "NU_ANO_CENSO": [ano],
            "CO_ENTIDADE": pd.array([100 + ano], dtype="Int64"),
            "NO_ENTIDADE": [f"Escola {ano}"],
            "CO_MUNICIPIO": pd.array([2600001], dtype="Int64"),
            "NO_MUNICIPIO": ["Recife"],
            "NO_CATEGORIA": ["Estadual"],
            "ICG_NIVEL": pd.array([4], dtype="Int64"),
        })

    with patch("src.data.build_complexidade_gestao.carregar_ano", side_effect=_frame):
        painel = construir_painel_icg(anos=[2022, 2023])

    assert set(painel["NU_ANO_CENSO"]) == {2022, 2023}
    assert painel.columns[-1] == "ICG_NIVEL"


def test_icg_painel_sem_arquivo_levanta_runtime_error():
    with patch(
        "src.data.build_complexidade_gestao.carregar_ano",
        side_effect=FileNotFoundError("ausente"),
    ):
        with pytest.raises(RuntimeError, match="Nenhum arquivo"):
            construir_painel_icg(anos=[2023])
