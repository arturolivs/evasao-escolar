"""
Testes para src/models/explain.py (Fase 7 — SHAP + resíduos).

Riscos centrais:
  1. Desembrulhar errado o TransformedTargetRegressor → explicar o modelo errado.
  2. Matriz SHAP com colunas/ordem trocadas → atribuições sem sentido.
  3. Resíduo com sinal invertido → "alerta" e "resiliente" trocados.
  4. Importância SHAP não ordenada → ranking de drivers incorreto.

Rodar com:
    pytest tests/test_explain.py -v
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.compose import TransformedTargetRegressor

from src.models.explain import (
    agrupar_localizacao,
    analise_residuos,
    calcular_shap_values,
    direcao_features,
    extrair_pipeline,
    importancia_shap,
    nomes_features_transformadas,
    preparar_matriz_shap,
    residuos_validacao_temporal,
    resumo_residuos_por_grupo,
)
from src.models.train import (
    aplicar_transformacao_target,
    criar_xgboost,
    preparar_xy,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def df_modelagem():
    """Dataset sintético no formato do features.parquet (60 escolas × 2 anos).
    feature_x1 tem relação forte e crescente com o target → SHAP positivo."""
    rng = np.random.RandomState(7)
    n_escolas = 60
    linhas = []
    for ano in [2022, 2023]:
        for i in range(n_escolas):
            x1 = rng.uniform(0, 10)
            linhas.append({
                "CO_ENTIDADE": 1000 + i,
                "NU_ANO_CENSO": ano,
                "NO_ENTIDADE": f"ESCOLA {i}",
                "CO_MUNICIPIO": 2600000 + (i % 10),
                "NO_MUNICIPIO": f"MUN {i % 10}",
                "CO_MESORREGIAO": 2601 + (i % 5),
                "feature_x1": x1,
                "feature_x2": rng.normal(),
                "taxa_abandono_t1": max(0.0, 2 * x1 + rng.normal(0, 0.5)),
            })
    return pd.DataFrame(linhas)


@pytest.fixture
def modelo_treinado(df_modelagem):
    """XGBoost + transformação sqrt, ajustado — espelha o modelo serializado."""
    X, y, _ = preparar_xy(df_modelagem)
    modelo = aplicar_transformacao_target(criar_xgboost(X), "sqrt")
    modelo.fit(X, y)
    return modelo


# ---------------------------------------------------------------------------
# Acesso às partes do modelo
# ---------------------------------------------------------------------------

def test_extrair_pipeline_desembrulha_transformed_target(modelo_treinado):
    assert isinstance(modelo_treinado, TransformedTargetRegressor)
    pipe = extrair_pipeline(modelo_treinado)
    assert "preprocess" in pipe.named_steps
    assert "model" in pipe.named_steps


def test_extrair_pipeline_passa_pipeline_simples(df_modelagem):
    X, _, _ = preparar_xy(df_modelagem)
    pipe = criar_xgboost(X)  # Pipeline sem TransformedTargetRegressor
    assert extrair_pipeline(pipe) is pipe


def test_matriz_shap_alinha_colunas_e_linhas(modelo_treinado, df_modelagem):
    X, _, _ = preparar_xy(df_modelagem)
    Xt = preparar_matriz_shap(modelo_treinado, X)
    nomes = nomes_features_transformadas(modelo_treinado)
    assert list(Xt.columns) == nomes
    assert len(Xt) == len(X)
    # one-hot da mesorregião (5 níveis) expande o nº de colunas além das 3 cruas
    assert Xt.shape[1] > 3
    # sem prefixos num__/cat__ remanescentes
    assert all("__" not in c for c in Xt.columns)


# ---------------------------------------------------------------------------
# SHAP
# ---------------------------------------------------------------------------

def test_shap_values_dimensao_e_aditividade(modelo_treinado, df_modelagem):
    """SHAP é aditivo: base + soma das contribuições = predição do booster."""
    X, _, _ = preparar_xy(df_modelagem)
    sv = calcular_shap_values(modelo_treinado, X)
    assert sv.values.shape[0] == len(X)
    assert sv.values.shape[1] == len(nomes_features_transformadas(modelo_treinado))

    booster = extrair_pipeline(modelo_treinado).named_steps["model"]
    Xt = preparar_matriz_shap(modelo_treinado, X)
    pred_booster = booster.predict(Xt.to_numpy())  # espaço sqrt
    recon = sv.base_values + sv.values.sum(axis=1)
    np.testing.assert_allclose(recon, pred_booster, rtol=1e-4, atol=1e-4)


def test_importancia_shap_ordenada_e_destaca_feature_relevante(
    modelo_treinado, df_modelagem
):
    X, _, _ = preparar_xy(df_modelagem)
    sv = calcular_shap_values(modelo_treinado, X)
    imp = importancia_shap(sv)
    # ordenada de forma decrescente
    assert imp["shap_mean_abs"].is_monotonic_decreasing
    # feature_x1 (sinal forte) deve superar feature_x2 (ruído)
    val = imp.set_index("feature")["shap_mean_abs"]
    assert val["feature_x1"] > val["feature_x2"]


def test_direcao_feature_relevante_positiva(modelo_treinado, df_modelagem):
    """feature_x1 cresce com o target → correlação valor×SHAP > 0."""
    X, _, _ = preparar_xy(df_modelagem)
    sv = calcular_shap_values(modelo_treinado, X)
    dirs = direcao_features(sv).set_index("feature")
    assert dirs.loc["feature_x1", "corr_valor_shap"] > 0


# ---------------------------------------------------------------------------
# Resíduos (P3)
# ---------------------------------------------------------------------------

def test_residuo_sinal_e_ordenacao(modelo_treinado, df_modelagem):
    res = analise_residuos(modelo_treinado, df_modelagem, top_n=5)
    # resíduo = real − previsto
    esperado = res.df["y_real"] - res.df["y_pred"]
    np.testing.assert_allclose(res.df["residuo"].to_numpy(), esperado.to_numpy())
    # ordenado do maior resíduo (mais alerta) para o menor
    assert res.df["residuo"].is_monotonic_decreasing
    # extremos coerentes: 'acima' tem resíduo ≥ 'abaixo'
    assert res.acima["residuo"].min() >= res.abaixo["residuo"].max()


def test_residuo_z_padronizado(modelo_treinado, df_modelagem):
    res = analise_residuos(modelo_treinado, df_modelagem)
    z = res.df["residuo_z"]
    assert z.std() == pytest.approx(1.0, rel=0.05)


def test_acima_abaixo_tamanho_top_n(modelo_treinado, df_modelagem):
    res = analise_residuos(modelo_treinado, df_modelagem, top_n=15)
    assert len(res.acima) == 15
    assert len(res.abaixo) == 15


# ---------------------------------------------------------------------------
# Equidade por grupo de localização
# ---------------------------------------------------------------------------

def test_agrupar_localizacao_precedencia_diferenciada():
    df = pd.DataFrame({
        "is_rural": [0, 1, 1, 0],
        "is_loc_diferenciada": [0, 0, 1, 0],
    })
    g = agrupar_localizacao(df).tolist()
    # diferenciada tem precedência mesmo sendo também rural
    assert g == ["urbana", "rural", "diferenciada", "urbana"]


def test_residuos_temporais_grupo_e_sinal(df_modelagem):
    # injeta colunas de localização exigidas pela análise de equidade
    rng = np.random.RandomState(1)
    df_modelagem = df_modelagem.copy()
    df_modelagem["is_rural"] = rng.randint(0, 2, len(df_modelagem))
    df_modelagem["is_loc_diferenciada"] = 0
    X, y, _ = preparar_xy(df_modelagem)
    modelo = aplicar_transformacao_target(criar_xgboost(X), "sqrt")
    modelo.fit(X, y)

    res = residuos_validacao_temporal(modelo, df_modelagem)
    # só o ano de teste (2023) entra
    assert set(res["NU_ANO_CENSO"]) == {2023}
    np.testing.assert_allclose(
        res["residuo"].to_numpy(),
        (res["y_real"] - res["y_pred"]).to_numpy(),
    )
    resumo = resumo_residuos_por_grupo(res)
    assert set(resumo["grupo"]) == {"urbana", "rural", "diferenciada"}
    assert int(resumo["n"].sum()) == len(res)
