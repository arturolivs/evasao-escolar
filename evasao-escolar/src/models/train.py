"""
Treino dos modelos de regressão — Fase 5 (baselines).

Constrói os pipelines sklearn definidos na metodologia
(decisoes_projeto.md, seções 4.1 e 7):
  - DummyRegressor (média)        → piso de referência
  - Ridge                         → baseline linear
  - RandomForestRegressor         → baseline não-linear

Decisões de pré-processamento:
  - Numéricas: imputação por mediana + StandardScaler (necessário p/ Ridge)
  - CO_MESORREGIAO: one-hot (código IBGE é categórico, não ordinal)
  - Transformação opcional do target (log1p, sqrt) via
    TransformedTargetRegressor — métricas sempre na escala original.

Validação:
  - GroupKFold por CO_MUNICIPIO (autocorrelação espacial)
  - Split temporal: treino 2022→2023, teste 2023→2024
"""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

from src.data import config
from src.features.build_features import ID_COLS

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES
# =============================================================================

TARGET_COL = "taxa_abandono_t1"
GRUPO_COL = "CO_MUNICIPIO"   # grupos da validação cruzada
ANO_COL = "NU_ANO_CENSO"

# Única feature tratada como categórica nominal
CAT_COLS = ["CO_MESORREGIAO"]

# Grades de hiperparâmetros dos baselines (leves de propósito —
# o tuning pesado é só do XGBoost, na Fase 6)
GRID_RIDGE = {"model__alpha": [0.1, 1.0, 10.0, 100.0]}
GRID_RF = {
    "model__max_depth": [None, 8],
    "model__min_samples_leaf": [1, 5],
}

# Grade do XGBoost (Fase 6). N pequeno (~800 obs de treino por fold) →
# árvores rasas e regularização forte para conter overfitting; learning
# rate baixo com mais estimadores. Mantida enxuta para CV agrupada viável.
GRID_XGB = {
    "model__n_estimators": [300, 600],
    "model__max_depth": [2, 3, 4],
    "model__learning_rate": [0.02, 0.05],
    "model__min_child_weight": [3, 5],
    "model__reg_lambda": [1.0, 5.0],
}

# Transformações de target a testar (a distribuição é assimétrica, skew ≈ 3)
TRANSFORMACOES_TARGET = {
    "identidade": None,
    "log1p": (np.log1p, np.expm1),
    "sqrt": (np.sqrt, np.square),
}

RANDOM_STATE = 42


# =============================================================================
# CARGA E PREPARAÇÃO
# =============================================================================

def carregar_dataset() -> pd.DataFrame:
    path = config.PROCESSED_DIR / "features.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset não encontrado: {path}\n"
            "Execute: python -m src.features.build_features"
        )
    df = pd.read_parquet(path)
    df[ANO_COL] = df[ANO_COL].astype(int)
    logger.info("Dataset carregado: %d linhas × %d colunas.", *df.shape)
    return df


def colunas_features(df: pd.DataFrame) -> list[str]:
    """Features do modelo = tudo que não é ID nem target."""
    excluir = set(ID_COLS + [TARGET_COL])
    return [c for c in df.columns if c not in excluir]


def preparar_xy(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Separa X (features), y (target) e grupos (município) para a CV."""
    fcols = colunas_features(df)
    X = df[fcols].copy()
    y = df[TARGET_COL].copy()
    grupos = df[GRUPO_COL].copy()
    return X, y, grupos


def split_temporal(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split temporal para validação prospectiva simulada:
      treino = features 2022 (target = abandono 2023)
      teste  = features 2023 (target = abandono 2024)
    """
    treino = df[df[ANO_COL] == 2022].copy()
    teste = df[df[ANO_COL] == 2023].copy()
    logger.info("Split temporal: treino=%d (2022→2023), teste=%d (2023→2024).",
                len(treino), len(teste))
    return treino, teste


# =============================================================================
# PIPELINES
# =============================================================================

def criar_preprocessador(X: pd.DataFrame) -> ColumnTransformer:
    cat_cols = [c for c in CAT_COLS if c in X.columns]
    num_cols = [c for c in X.columns if c not in cat_cols]
    return ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), num_cols),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), cat_cols),
    ])


def criar_pipeline(X: pd.DataFrame, estimador) -> Pipeline:
    return Pipeline([
        ("preprocess", criar_preprocessador(X)),
        ("model", estimador),
    ])


def criar_baselines(X: pd.DataFrame) -> dict[str, Pipeline]:
    """Baselines da Fase 5 (Dummy como piso; Ridge e RF como comparação)."""
    return {
        "dummy_media": criar_pipeline(X, DummyRegressor(strategy="mean")),
        "ridge": criar_pipeline(X, Ridge(random_state=RANDOM_STATE)),
        "random_forest": criar_pipeline(X, RandomForestRegressor(
            n_estimators=300,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )),
    }


def criar_xgboost(X: pd.DataFrame) -> Pipeline:
    """
    Pipeline do XGBoost (Fase 6).

    Reaproveita o mesmo pré-processador dos baselines (imputação +
    one-hot da mesorregião). O StandardScaler nas numéricas é
    desnecessário para árvores, mas é uma transformação monotônica que
    não altera os splits — mantido por consistência de pipeline.

    `subsample` e `colsample_bytree` ficam fixos (não no grid) para
    conter o tamanho da busca; a regularização varia via GRID_XGB.
    """
    estimador = XGBRegressor(
        objective="reg:squarederror",
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method="hist",
        importance_type="gain",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    return criar_pipeline(X, estimador)


def aplicar_transformacao_target(modelo, nome_transformacao: str):
    """
    Embala o pipeline num TransformedTargetRegressor.
    predict() devolve valores já na escala original (%).
    """
    par = TRANSFORMACOES_TARGET[nome_transformacao]
    if par is None:
        return modelo
    func, inverse_func = par
    return TransformedTargetRegressor(
        regressor=modelo, func=func, inverse_func=inverse_func,
    )


def buscar_hiperparametros(
    pipeline: Pipeline,
    grid: dict,
    X: pd.DataFrame,
    y: pd.Series,
    grupos: pd.Series,
    n_splits: int = 5,
) -> GridSearchCV:
    """Grid search com GroupKFold por município, otimizando RMSE."""
    gs = GridSearchCV(
        pipeline,
        grid,
        cv=GroupKFold(n_splits=n_splits),
        scoring="neg_root_mean_squared_error",
        n_jobs=-1,
        refit=True,
    )
    gs.fit(X, y, groups=grupos)
    logger.info("Melhores parâmetros: %s (RMSE CV=%.3f)",
                gs.best_params_, -gs.best_score_)
    return gs


# =============================================================================
# SERIALIZAÇÃO
# =============================================================================

def salvar_modelo(modelo, nome: str) -> Path:
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    out = config.MODELS_DIR / f"{nome}.joblib"
    joblib.dump(modelo, out)
    logger.info("Modelo salvo em: %s", out)
    return out


def carregar_modelo(nome: str):
    path = config.MODELS_DIR / f"{nome}.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {path}")
    return joblib.load(path)
