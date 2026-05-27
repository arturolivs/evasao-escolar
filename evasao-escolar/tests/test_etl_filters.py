"""
Testes unitários para o módulo de filtragem do universo.

Rodar com:
    pytest tests/test_etl_filters.py -v

Os testes usam DataFrames sintéticos pequenos para não depender dos
microdados reais (que são grandes e podem não estar disponíveis no CI).
"""

import pandas as pd
import pytest

from src.data import filter_pe_estadual_em as flt


def fazer_df_dummy():
    """DataFrame sintético cobrindo todos os casos relevantes."""
    return pd.DataFrame({
        "CO_ENTIDADE": [1, 2, 3, 4, 5, 6, 7],
        "SG_UF": ["PE", "PE", "PE", "PB", "PE", "PE", "pe"],  # 'pe' minúsculo testa normalização
        "CO_UF": [26, 26, 26, 25, 26, 26, 26],
        "TP_DEPENDENCIA": [2, 2, 1, 2, 4, 2, 2],  # 1=fed, 2=est, 3=mun, 4=priv
        "TP_SITUACAO_FUNCIONAMENTO": [1, 1, 1, 1, 1, 2, 1],  # 2=paralisada
        "QT_MAT_MED": [150, 0, 200, 100, 50, 300, 80],
    })


# -----------------------------------------------------------------------------
# Testes individuais por filtro
# -----------------------------------------------------------------------------

def test_filtrar_uf_pe_via_sg_uf():
    df = fazer_df_dummy()
    out = flt.filtrar_uf_pe(df)
    # 6 linhas de PE (incluindo 'pe' minúsculo); 1 de PB sai
    assert len(out) == 6
    assert (out["SG_UF"].str.upper() == "PE").all()


def test_filtrar_uf_pe_via_co_uf_fallback():
    df = fazer_df_dummy().drop(columns=["SG_UF"])
    out = flt.filtrar_uf_pe(df)
    assert len(out) == 6
    assert (out["CO_UF"] == 26).all()


def test_filtrar_uf_pe_sem_coluna_levanta_erro():
    df = fazer_df_dummy().drop(columns=["SG_UF", "CO_UF"])
    with pytest.raises(ValueError, match="SG_UF / CO_UF"):
        flt.filtrar_uf_pe(df)


def test_filtrar_rede_estadual():
    df = fazer_df_dummy()
    out = flt.filtrar_rede_estadual(df)
    # 5 linhas com TP_DEPENDENCIA == 2
    assert len(out) == 5
    assert (out["TP_DEPENDENCIA"] == 2).all()


def test_filtrar_em_atividade():
    df = fazer_df_dummy()
    out = flt.filtrar_em_atividade(df)
    # 6 linhas com TP_SITUACAO_FUNCIONAMENTO == 1
    assert len(out) == 6
    assert (out["TP_SITUACAO_FUNCIONAMENTO"] == 1).all()


def test_filtrar_em_atividade_sem_coluna_avisa_mas_nao_falha():
    df = fazer_df_dummy().drop(columns=["TP_SITUACAO_FUNCIONAMENTO"])
    out = flt.filtrar_em_atividade(df)
    # Sem a coluna, mantém todas
    assert len(out) == len(df)


def test_filtrar_oferta_em_exclui_zero_e_nulo():
    df = fazer_df_dummy()
    # Adiciona uma linha com NaN em QT_MAT_MED
    df.loc[len(df)] = {
        "CO_ENTIDADE": 999, "SG_UF": "PE", "CO_UF": 26,
        "TP_DEPENDENCIA": 2, "TP_SITUACAO_FUNCIONAMENTO": 1,
        "QT_MAT_MED": pd.NA,
    }
    out = flt.filtrar_oferta_ensino_medio(df)
    # Exclui as linhas com QT_MAT_MED == 0 e == NaN
    assert (out["QT_MAT_MED"] > 0).all()
    assert 999 not in out["CO_ENTIDADE"].values


# -----------------------------------------------------------------------------
# Teste de orquestração
# -----------------------------------------------------------------------------

def test_aplicar_recorte_universo_completo():
    df = fazer_df_dummy()
    out, rel = flt.aplicar_recorte_universo(df, incluir_filtro_em=True)

    # Expectativa: começa com 7, após todos filtros deve ter apenas escolas
    # que são: PE & estadual & em atividade & com EM
    # CO_ENTIDADE=1 (PE, est, ativ, 150 mat) ✓
    # CO_ENTIDADE=2 (PE, est, ativ, 0 mat)   ✗ (sem EM)
    # CO_ENTIDADE=3 (PE, fed, ativ, 200 mat) ✗ (não estadual)
    # CO_ENTIDADE=4 (PB, est, ativ, 100 mat) ✗ (não PE)
    # CO_ENTIDADE=5 (PE, priv, ativ, 50 mat) ✗ (não estadual)
    # CO_ENTIDADE=6 (PE, est, paralis, 300)  ✗ (não em atividade)
    # CO_ENTIDADE=7 (PE/pe, est, ativ, 80)   ✓
    assert len(out) == 2
    assert set(out["CO_ENTIDADE"].tolist()) == {1, 7}

    # Relatório deve registrar cada etapa
    assert rel.inicial == 7
    assert len(rel.etapas) == 4
    nomes_etapas = [nome for nome, _ in rel.etapas]
    assert any("UF" in n for n in nomes_etapas)
    assert any("Estadual" in n for n in nomes_etapas)
    assert any("atividade" in n for n in nomes_etapas)
    assert any("oferta EM" in n for n in nomes_etapas)


def test_aplicar_recorte_sem_filtro_em():
    df = fazer_df_dummy()
    out, rel = flt.aplicar_recorte_universo(df, incluir_filtro_em=False)
    # Sem o filtro de EM, CO_ENTIDADE=2 (0 matrículas) entra também
    assert len(out) == 3
    assert set(out["CO_ENTIDADE"].tolist()) == {1, 2, 7}
    assert len(rel.etapas) == 3  # uma etapa a menos


# -----------------------------------------------------------------------------
# Teste de erro esperado
# -----------------------------------------------------------------------------

def test_filtrar_rede_estadual_sem_coluna_levanta_erro():
    df = fazer_df_dummy().drop(columns=["TP_DEPENDENCIA"])
    with pytest.raises(ValueError, match="TP_DEPENDENCIA"):
        flt.filtrar_rede_estadual(df)


def test_filtrar_em_sem_coluna_levanta_erro():
    df = fazer_df_dummy().drop(columns=["QT_MAT_MED"])
    with pytest.raises(ValueError, match="QT_MAT_MED"):
        flt.filtrar_oferta_ensino_medio(df)
