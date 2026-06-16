"""
Métricas de avaliação dos modelos de regressão.

Implementa as métricas definidas na metodologia (decisoes_projeto.md, seção 8):
  - Primárias:   RMSE, MAE, R²
  - De ranking:  correlação de Spearman, Precision@K
e o loop de validação cruzada agrupada por município (GroupKFold),
que evita vazamento entre escolas vizinhas.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold

logger = logging.getLogger(__name__)

# Fração do fold usada como K no Precision@K (top 10% de maior abandono)
K_FRACAO_PADRAO = 0.10


def precision_at_k(y_true: np.ndarray, y_pred: np.ndarray, k: int) -> float:
    """
    Das K observações com maior valor PREDITO, quantas estão entre as K
    com maior valor REAL? Mede a utilidade do modelo para priorização
    (ranking top-K de escolas em risco).
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if k <= 0 or k > len(y_true):
        raise ValueError(f"k inválido: {k} (n={len(y_true)})")
    top_pred = set(np.argsort(y_pred)[::-1][:k])
    top_true = set(np.argsort(y_true)[::-1][:k])
    return len(top_pred & top_true) / k


def calcular_metricas(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    k_fracao: float = K_FRACAO_PADRAO,
) -> dict[str, float]:
    """Calcula o conjunto completo de métricas na escala original do target."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    k = max(1, int(round(len(y_true) * k_fracao)))
    rho, _ = spearmanr(y_true, y_pred)
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "spearman": float(rho),
        "precision_at_k": float(precision_at_k(y_true, y_pred, k)),
        "k": k,
    }


def validacao_cruzada_grupos(
    modelo,
    X: pd.DataFrame,
    y: pd.Series,
    grupos: pd.Series,
    n_splits: int = 5,
    k_fracao: float = K_FRACAO_PADRAO,
) -> pd.DataFrame:
    """
    Validação cruzada com GroupKFold (grupos = município).

    O modelo é clonado e re-treinado em cada fold; as métricas são
    calculadas no fold de teste, na escala original do target (se o
    modelo for um TransformedTargetRegressor, o predict já devolve
    valores na escala original).

    Retorna um DataFrame com uma linha por fold.
    """
    cv = GroupKFold(n_splits=n_splits)
    linhas = []
    for i, (idx_tr, idx_te) in enumerate(cv.split(X, y, groups=grupos), start=1):
        est = clone(modelo)
        est.fit(X.iloc[idx_tr], y.iloc[idx_tr])
        y_pred = est.predict(X.iloc[idx_te])
        metricas = calcular_metricas(y.iloc[idx_te], y_pred, k_fracao=k_fracao)
        metricas["fold"] = i
        metricas["n_teste"] = len(idx_te)
        linhas.append(metricas)
        logger.info(
            "Fold %d/%d: RMSE=%.3f  Spearman=%.3f",
            i, n_splits, metricas["rmse"], metricas["spearman"],
        )
    return pd.DataFrame(linhas)


def resumir_cv(df_folds: pd.DataFrame) -> dict[str, str]:
    """Formata média ± desvio-padrão das métricas entre folds."""
    metricas = ["rmse", "mae", "r2", "spearman", "precision_at_k"]
    return {
        m: f"{df_folds[m].mean():.3f} ± {df_folds[m].std():.3f}"
        for m in metricas
    }
