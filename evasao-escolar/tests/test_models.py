"""
Testes para src/models/evaluate.py e src/models/train.py.

Os riscos centrais aqui são:
  1. precision_at_k errada → ranking de priorização sem sentido.
  2. Vazamento de grupo na CV → métricas otimistas.
  3. Transformação de target sem inversa correta → predições em escala errada.

Rodar com:
    pytest tests/test_models.py -v
"""

import numpy as np
import pandas as pd
import pytest

from src.models.evaluate import (
    calcular_metricas,
    precision_at_k,
    validacao_cruzada_grupos,
)
from src.models.train import (
    TARGET_COL,
    aplicar_transformacao_target,
    colunas_features,
    criar_baselines,
    preparar_xy,
    split_temporal,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def df_modelagem():
    """Dataset sintético no formato do features.parquet (60 escolas × 2 anos)."""
    rng = np.random.RandomState(42)
    n_escolas = 60
    linhas = []
    for ano in [2022, 2023]:
        for i in range(n_escolas):
            x1 = rng.uniform(0, 10)
            linhas.append({
                "CO_ENTIDADE": 1000 + i,
                "NU_ANO_CENSO": ano,
                "NO_ENTIDADE": f"ESCOLA {i}",
                "CO_MUNICIPIO": 2600000 + (i % 10),  # 10 municípios
                "NO_MUNICIPIO": f"MUN {i % 10}",
                "CO_MESORREGIAO": 2601 + (i % 5),
                "feature_x1": x1,
                "feature_x2": rng.normal(),
                "taxa_abandono_t1": max(0.0, 2 * x1 + rng.normal(0, 1)),
            })
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# precision_at_k
# ---------------------------------------------------------------------------

def test_precision_at_k_ranking_perfeito():
    y = np.array([1.0, 5.0, 3.0, 9.0, 2.0])
    assert precision_at_k(y, y, k=2) == 1.0


def test_precision_at_k_ranking_invertido():
    """Predição invertida: o top-2 predito são os 2 piores reais."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y_pred = -y_true
    assert precision_at_k(y_true, y_pred, k=2) == 0.0


def test_precision_at_k_parcial():
    """Top-2 predito acerta exatamente 1 dos top-2 reais."""
    y_true = np.array([10.0, 9.0, 1.0, 2.0])   # top-2 reais: idx 0, 1
    y_pred = np.array([10.0, 1.0, 9.0, 2.0])   # top-2 preditos: idx 0, 2
    assert precision_at_k(y_true, y_pred, k=2) == 0.5


def test_precision_at_k_invalido():
    y = np.array([1.0, 2.0])
    with pytest.raises(ValueError):
        precision_at_k(y, y, k=0)
    with pytest.raises(ValueError):
        precision_at_k(y, y, k=3)


# ---------------------------------------------------------------------------
# calcular_metricas
# ---------------------------------------------------------------------------

def test_metricas_predicao_perfeita():
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0] * 4)
    m = calcular_metricas(y, y)
    assert m["rmse"] == 0.0
    assert m["mae"] == 0.0
    assert m["r2"] == 1.0
    assert m["spearman"] == pytest.approx(1.0)
    assert m["precision_at_k"] == 1.0


def test_metricas_k_proporcional():
    y = np.arange(100, dtype=float)
    m = calcular_metricas(y, y, k_fracao=0.10)
    assert m["k"] == 10


# ---------------------------------------------------------------------------
# Preparação dos dados
# ---------------------------------------------------------------------------

def test_colunas_features_exclui_ids_e_target(df_modelagem):
    fcols = colunas_features(df_modelagem)
    assert TARGET_COL not in fcols
    assert "CO_ENTIDADE" not in fcols
    assert "NO_ENTIDADE" not in fcols
    assert "CO_MUNICIPIO" not in fcols
    # CO_MESORREGIAO é feature (categórica), não ID
    assert "CO_MESORREGIAO" in fcols
    assert "feature_x1" in fcols


def test_split_temporal_sem_sobreposicao(df_modelagem):
    treino, teste = split_temporal(df_modelagem)
    assert set(treino["NU_ANO_CENSO"]) == {2022}
    assert set(teste["NU_ANO_CENSO"]) == {2023}
    assert len(treino) + len(teste) == len(df_modelagem)


# ---------------------------------------------------------------------------
# Validação cruzada agrupada
# ---------------------------------------------------------------------------

def test_cv_municipios_nao_vazam_entre_folds(df_modelagem):
    """Nenhum município pode aparecer em treino e teste do mesmo fold."""
    from sklearn.model_selection import GroupKFold

    X, y, grupos = preparar_xy(df_modelagem)
    for idx_tr, idx_te in GroupKFold(n_splits=5).split(X, y, groups=grupos):
        municipios_tr = set(grupos.iloc[idx_tr])
        municipios_te = set(grupos.iloc[idx_te])
        assert municipios_tr.isdisjoint(municipios_te)


def test_cv_retorna_metricas_por_fold(df_modelagem):
    X, y, grupos = preparar_xy(df_modelagem)
    baselines = criar_baselines(X)
    df_folds = validacao_cruzada_grupos(
        baselines["ridge"], X, y, grupos, n_splits=3
    )
    assert len(df_folds) == 3
    assert {"rmse", "mae", "r2", "spearman", "precision_at_k"} <= set(df_folds.columns)
    # Ridge num target quase-linear deve bater o piso trivial
    assert df_folds["r2"].mean() > 0.5


# ---------------------------------------------------------------------------
# Transformação do target
# ---------------------------------------------------------------------------

def test_transformacao_identidade_devolve_mesmo_objeto(df_modelagem):
    X, _, _ = preparar_xy(df_modelagem)
    pipe = criar_baselines(X)["ridge"]
    assert aplicar_transformacao_target(pipe, "identidade") is pipe


@pytest.mark.parametrize("transformacao", ["log1p", "sqrt"])
def test_transformacao_prediz_na_escala_original(df_modelagem, transformacao):
    """predict() do modelo transformado deve devolver valores em %, não log/raiz."""
    X, y, _ = preparar_xy(df_modelagem)
    pipe = criar_baselines(X)["ridge"]
    modelo = aplicar_transformacao_target(pipe, transformacao)
    modelo.fit(X, y)
    y_pred = modelo.predict(X)
    # Na escala original, as predições têm a mesma ordem de grandeza do target
    assert y_pred.mean() == pytest.approx(y.mean(), rel=0.5)
    assert y_pred.max() > 5  # escala de %, não de log (log1p(20) ≈ 3)
