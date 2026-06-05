"""
Testes para src/data/build_taxas_rendimento.py.

Rodar com:
    pytest tests/test_taxas.py -v
"""

import logging
from unittest.mock import patch

import pandas as pd
import pytest

from src.data.build_taxas_rendimento import (
    _validar_consistencia,
    carregar_ano,
    construir_painel_taxas,
)


# ---------------------------------------------------------------------------
# Fixtures locais
# ---------------------------------------------------------------------------

def _df_consistente():
    """3 escolas onde Aprov + Reprov + Abnd = 100."""
    return pd.DataFrame({
        "TAXA_APROV_MED": [90.0, 80.0, 70.0],
        "TAXA_REPROV_MED": [5.0, 10.0, 20.0],
        "TAXA_ABND_MED": [5.0, 10.0, 10.0],
    })


def _df_inconsistente():
    """1 escola com soma = 110 (fora da tolerância de 1 pp)."""
    return pd.DataFrame({
        "TAXA_APROV_MED": [100.0],
        "TAXA_REPROV_MED": [5.0],
        "TAXA_ABND_MED": [5.0],
    })


def _raw_excel_df():
    """Simula o DataFrame retornado por pd.read_excel no xlsx do INEP (após header=8).

    Escola A (26001): PE, Estadual, tem EM → deve ser mantida
    Escola B (26002): PE, Estadual, sem EM ('--' em 3_CAT_MED) → removida
    Escola C (35001): SP, Estadual, tem EM → filtrada pela UF
    """
    # Colunas brutas conforme _RENAME em build_taxas_rendimento.py
    taxa_cols_brutos = [
        "1_CAT_MED", "1_CAT_MED_01", "1_CAT_MED_02", "1_CAT_MED_03",
        "1_CAT_MED_04", "1_CAT_MED_NS",
        "2_CAT_MED", "2_CAT_MED_01", "2_CAT_MED_02", "2_CAT_MED_03",
        "2_CAT_MED_04", "2_CAT_MED_NS",
        "3_CAT_MED", "3_CAT_MED_01", "3_CAT_MED_02", "3_CAT_MED_03",
        "3_CAT_MED_04", "3_CAT_MED_NS",
    ]
    data = {
        "SG_UF":          ["PE",       "PE",       "SP"],
        "NO_DEPENDENCIA": ["Estadual", "Estadual", "Estadual"],
        "CO_ENTIDADE":    ["26001",    "26002",    "35001"],
        "CO_MUNICIPIO":   ["260000",   "260010",   "350000"],
        "NO_MUNICIPIO":   ["Recife",   "Olinda",   "São Paulo"],
        "NO_ENTIDADE":    ["Escola A", "Escola B", "Escola C"],
        "NO_CATEGORIA":   ["Estadual", "Estadual", "Estadual"],
    }
    # Defaults: escola A e C com valores numéricos, escola B com "--"
    for col in taxa_cols_brutos:
        data[col] = [5.0, "--", 5.0]

    # Valores realistas para aprovação/reprovação/abandono total (soma = 100)
    data["1_CAT_MED"] = [90.0, "--", 80.0]
    data["2_CAT_MED"] = [5.0,  "--", 15.0]
    data["3_CAT_MED"] = [5.0,  "--", 5.0]

    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# _validar_consistencia
# ---------------------------------------------------------------------------

def test_consistencia_soma_100_nao_emite_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="src.data.build_taxas_rendimento"):
        _validar_consistencia(_df_consistente(), ano=2023)
    assert caplog.records == []


def test_consistencia_fora_de_tolerancia_emite_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="src.data.build_taxas_rendimento"):
        _validar_consistencia(_df_inconsistente(), ano=2023)
    assert len(caplog.records) == 1
    assert "110" in caplog.records[0].message or "1" in caplog.records[0].message


def test_consistencia_df_vazio_nao_falha():
    df_vazio = pd.DataFrame(columns=["TAXA_APROV_MED", "TAXA_REPROV_MED", "TAXA_ABND_MED"])
    _validar_consistencia(df_vazio, ano=2023)  # não deve lançar exceção


def test_consistencia_df_com_nans_ignora_linhas_incompletas(caplog):
    df = pd.DataFrame({
        "TAXA_APROV_MED": [90.0, None],
        "TAXA_REPROV_MED": [5.0, None],
        "TAXA_ABND_MED": [5.0, None],
    })
    with caplog.at_level(logging.WARNING, logger="src.data.build_taxas_rendimento"):
        _validar_consistencia(df, ano=2023)
    # A linha com NaN é ignorada; a linha completa soma 100 → sem warning
    assert caplog.records == []


# ---------------------------------------------------------------------------
# carregar_ano
# ---------------------------------------------------------------------------

def test_carregar_ano_sentinel_vira_nan():
    """Valores '--' devem ser convertidos para NaN em todas as colunas de taxa."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_excel_df()),
    ):
        df = carregar_ano(2023)

    # Escola A tem valores numéricos; series sem EM (Escola B) foi removida
    # Colunas por série (ex: S4, NS) podem ter NaN — verificar que são float, não string
    for col in df.columns:
        if col.startswith("TAXA_"):
            assert df[col].dtype in [float, "float64"], f"{col} deveria ser float"


def test_carregar_ano_escola_sem_em_removida():
    """Escola com TAXA_ABND_MED='--' (→ NaN) deve ser removida do output."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_excel_df()),
    ):
        df = carregar_ano(2023)

    assert "26002" not in df["CO_ENTIDADE"].astype(str).values


def test_carregar_ano_filtra_apenas_pe_estadual():
    """Escola de SP deve ser removida pelo filtro de UF."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_excel_df()),
    ):
        df = carregar_ano(2023)

    assert "35001" not in df["CO_ENTIDADE"].astype(str).values


def test_carregar_ano_co_entidade_e_int64():
    """CO_ENTIDADE deve ser convertida para Int64 (nullable integer)."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_excel_df()),
    ):
        df = carregar_ano(2023)

    assert str(df["CO_ENTIDADE"].dtype) == "Int64"


def test_carregar_ano_nu_ano_censo_injetado():
    """NU_ANO_CENSO deve ser o ano passado como argumento."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pandas.read_excel", return_value=_raw_excel_df()),
    ):
        df = carregar_ano(2023)

    assert (df["NU_ANO_CENSO"] == 2023).all()


def test_carregar_ano_arquivo_ausente_levanta_file_not_found():
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            carregar_ano(2023)


# ---------------------------------------------------------------------------
# construir_painel_taxas
# ---------------------------------------------------------------------------

def _frame_ano(ano: int) -> pd.DataFrame:
    """Retorno de carregar_ano para uso nos testes de painel.

    Inclui todas as colunas que construir_painel_taxas espera (id_cols + TAXA_COLS).
    """
    taxa_cols = [
        "TAXA_APROV_MED", "TAXA_APROV_MED_S1", "TAXA_APROV_MED_S2", "TAXA_APROV_MED_S3",
        "TAXA_APROV_MED_S4", "TAXA_APROV_MED_NS",
        "TAXA_REPROV_MED", "TAXA_REPROV_MED_S1", "TAXA_REPROV_MED_S2", "TAXA_REPROV_MED_S3",
        "TAXA_REPROV_MED_S4", "TAXA_REPROV_MED_NS",
        "TAXA_ABND_MED", "TAXA_ABND_MED_S1", "TAXA_ABND_MED_S2", "TAXA_ABND_MED_S3",
        "TAXA_ABND_MED_S4", "TAXA_ABND_MED_NS",
    ]
    data: dict = {
        "NU_ANO_CENSO": [ano, ano],
        "CO_ENTIDADE": pd.array([100 + ano, 200 + ano], dtype="Int64"),
        "NO_ENTIDADE": [f"Escola A {ano}", f"Escola B {ano}"],
        "CO_MUNICIPIO": pd.array([2600001, 2600002], dtype="Int64"),
        "NO_MUNICIPIO": ["Recife", "Olinda"],
        "NO_CATEGORIA": ["Estadual", "Estadual"],
    }
    for col in taxa_cols:
        data[col] = [5.0, 8.0]
    return pd.DataFrame(data)


def test_construir_painel_concatena_anos():
    """Painel deve ter linhas de todos os anos solicitados."""
    def mock_carregar(ano):
        return _frame_ano(ano)

    with patch("src.data.build_taxas_rendimento.carregar_ano", side_effect=mock_carregar):
        painel = construir_painel_taxas(anos=[2023, 2024])

    assert set(painel["NU_ANO_CENSO"].unique()) == {2023, 2024}
    assert len(painel) == 4


def test_construir_painel_ignora_ano_sem_arquivo():
    """FileNotFoundError em um ano não deve interromper os demais."""
    def mock_carregar(ano):
        if ano == 2022:
            raise FileNotFoundError("arquivo ausente")
        return _frame_ano(ano)

    with patch("src.data.build_taxas_rendimento.carregar_ano", side_effect=mock_carregar):
        painel = construir_painel_taxas(anos=[2022, 2023])

    assert list(painel["NU_ANO_CENSO"].unique()) == [2023]


def test_construir_painel_sem_nenhum_arquivo_levanta_runtime_error():
    with patch(
        "src.data.build_taxas_rendimento.carregar_ano",
        side_effect=FileNotFoundError("arquivo ausente"),
    ):
        with pytest.raises(RuntimeError, match="Nenhum arquivo"):
            construir_painel_taxas(anos=[2023])


def test_construir_painel_ordenado_por_escola_e_ano():
    """Painel deve estar ordenado por (CO_ENTIDADE, NU_ANO_CENSO)."""
    def mock_carregar(ano):
        # Retorna propositalmente com CO_ENTIDADE fora de ordem (200 antes de 100)
        frame = _frame_ano(ano)
        frame["CO_ENTIDADE"] = pd.array([200, 100], dtype="Int64")
        return frame

    with patch("src.data.build_taxas_rendimento.carregar_ano", side_effect=mock_carregar):
        painel = construir_painel_taxas(anos=[2023, 2024])

    entidades = painel["CO_ENTIDADE"].tolist()
    assert entidades == sorted(entidades)
