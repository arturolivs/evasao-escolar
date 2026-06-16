"""
Explicabilidade do modelo final — Fase 7 (SHAP + análise de resíduos).

Opera sobre o XGBoost serializado (`models/xgboost_v1.joblib`), que é um
`TransformedTargetRegressor` embrulhando um `Pipeline([preprocess, model])`.

Duas frentes, atadas às perguntas de pesquisa:

  P2 (previsão) — explicabilidade do ranking de risco:
    • SHAP global  → quais indicadores mais movem a predição (e em que direção)
    • SHAP local   → por que UMA escola foi pontuada como ela foi

  P3 (diagnóstico) — escolas fora do esperado:
    • resíduo = abandono real − abandono previsto pelo perfil institucional
    • resíduo ≫ 0 → escola abandona MAIS do que seu perfil prevê (alerta)
    • resíduo ≪ 0 → escola abandona MENOS do que seu perfil prevê (resiliente)

NOTA SOBRE A ESCALA DOS VALORES SHAP
------------------------------------
O modelo final foi treinado com transformação `sqrt` no target. O
`TreeExplainer` é montado sobre o `XGBRegressor` interno, logo os valores
SHAP explicam a predição no espaço **sqrt(taxa de abandono)**, não em
pontos percentuais. Como `sqrt` é monotônica crescente, o ranking de
importância e o SINAL das contribuições continuam válidos para
interpretação — apenas as magnitudes estão em unidades de raiz. As
predições e os resíduos, por outro lado, são sempre devolvidos pelo
`predict()` na escala original (%), porque o `TransformedTargetRegressor`
aplica a inversa automaticamente.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap
from sklearn.compose import TransformedTargetRegressor

from sklearn.base import clone

from src.models.train import (
    ANO_COL,
    TARGET_COL,
    carregar_dataset,
    colunas_features,
    preparar_xy,
    split_temporal,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ACESSO ÀS PARTES DO MODELO
# =============================================================================

def extrair_pipeline(modelo):
    """Devolve o `Pipeline` subjacente, esteja ou não embrulhado num
    `TransformedTargetRegressor` já ajustado (mesma convenção do notebook 08)."""
    if isinstance(modelo, TransformedTargetRegressor):
        return modelo.regressor_
    return modelo


def nomes_features_transformadas(modelo) -> list[str]:
    """Nomes das colunas APÓS o pré-processamento (numéricas + dummies da
    mesorregião), sem os prefixos `num__`/`cat__` do ColumnTransformer."""
    pipe = extrair_pipeline(modelo)
    nomes = pipe.named_steps["preprocess"].get_feature_names_out()
    return [n.split("__", 1)[-1] for n in nomes]


def preparar_matriz_shap(modelo, X: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica o pré-processador ajustado a X e devolve a matriz que de fato
    entra no XGBoost, como DataFrame com os nomes de coluna corretos.

    É essa matriz (não o X cru) que deve ser passada ao explainer, pois o
    booster só conhece as colunas pós-transformação.
    """
    pipe = extrair_pipeline(modelo)
    Xt = pipe.named_steps["preprocess"].transform(X)
    return pd.DataFrame(
        Xt, columns=nomes_features_transformadas(modelo), index=X.index
    )


def booster_xgb(modelo):
    """O `XGBRegressor` ajustado dentro do pipeline."""
    return extrair_pipeline(modelo).named_steps["model"]


# =============================================================================
# SHAP — VALORES E IMPORTÂNCIA GLOBAL
# =============================================================================

def calcular_shap_values(modelo, X: pd.DataFrame) -> shap.Explanation:
    """
    Calcula os valores SHAP do XGBoost para as observações de X.

    Usa `TreeExplainer` com `feature_perturbation="tree_path_dependent"`
    (exato e determinístico para árvores, dispensa dados de background).
    O objeto `Explanation` retornado carrega `.values`, `.base_values` e
    `.feature_names`, prontos para os gráficos do `shap`.
    """
    Xt = preparar_matriz_shap(modelo, X)
    explainer = shap.TreeExplainer(
        booster_xgb(modelo), feature_perturbation="tree_path_dependent"
    )
    shap_values = explainer(Xt)
    logger.info("Valores SHAP calculados: %d obs × %d features.",
                *shap_values.values.shape)
    return shap_values


def importancia_shap(shap_values: shap.Explanation) -> pd.DataFrame:
    """
    Importância global = média do |valor SHAP| por feature (unidades de
    sqrt(%)). Tabela ordenada do mais para o menos influente.
    """
    mean_abs = np.abs(shap_values.values).mean(axis=0)
    return (
        pd.DataFrame({
            "feature": shap_values.feature_names,
            "shap_mean_abs": mean_abs,
        })
        .sort_values("shap_mean_abs", ascending=False)
        .reset_index(drop=True)
    )


def direcao_features(shap_values: shap.Explanation) -> pd.DataFrame:
    """
    Para cada feature, correlação (Pearson) entre o valor da feature e seu
    valor SHAP, somada à importância. Sinal > 0 → valores altos da feature
    EMPURRAM o abandono previsto para cima; < 0 → para baixo.
    """
    valores = shap_values.values
    dados = shap_values.data
    linhas = []
    for j, nome in enumerate(shap_values.feature_names):
        col = dados[:, j]
        sj = valores[:, j]
        # corr indefinida se a feature (ou o SHAP) for constante na amostra
        if np.std(col) < 1e-12 or np.std(sj) < 1e-12:
            corr = np.nan
        else:
            corr = float(np.corrcoef(col, sj)[0, 1])
        linhas.append({
            "feature": nome,
            "shap_mean_abs": float(np.abs(sj).mean()),
            "corr_valor_shap": corr,
            "direcao": "↑ aumenta risco" if corr > 0
            else ("↓ reduz risco" if corr < 0 else "—"),
        })
    return (
        pd.DataFrame(linhas)
        .sort_values("shap_mean_abs", ascending=False)
        .reset_index(drop=True)
    )


# =============================================================================
# P3 — ANÁLISE DE RESÍDUOS (escolas fora do esperado)
# =============================================================================

@dataclass
class ResultadoResiduos:
    """Resíduos por escola + recortes dos extremos (acima/abaixo do esperado)."""
    df: pd.DataFrame            # todas as obs com y_real, y_pred, residuo, residuo_z
    acima: pd.DataFrame         # maiores resíduos positivos (alerta)
    abaixo: pd.DataFrame        # maiores resíduos negativos (resilientes)


def analise_residuos(
    modelo,
    df: pd.DataFrame | None = None,
    top_n: int = 20,
) -> ResultadoResiduos:
    """
    Resíduo = abandono real − abandono previsto pelo modelo (escala %).

    Identifica as escolas cujo abandono mais se afasta do que o perfil
    institucional prevê. Padroniza o resíduo (z-score) para leitura
    relativa e separa os `top_n` extremos de cada lado.

    Se `df` for None, carrega o dataset de features completo.
    """
    if df is None:
        df = carregar_dataset()

    fcols = colunas_features(df)
    X = df[fcols].copy()
    y = df[TARGET_COL].to_numpy(dtype=float)
    y_pred = np.asarray(modelo.predict(X), dtype=float)

    residuo = y - y_pred
    desvio = residuo.std()
    residuo_z = residuo / desvio if desvio > 0 else np.zeros_like(residuo)

    cols_id = [c for c in
               ["CO_ENTIDADE", "NO_ENTIDADE", "NO_MUNICIPIO", ANO_COL]
               if c in df.columns]
    out = df[cols_id].copy()
    out["y_real"] = y
    out["y_pred"] = y_pred
    out["residuo"] = residuo
    out["residuo_z"] = residuo_z
    out = out.sort_values("residuo", ascending=False).reset_index(drop=True)

    logger.info(
        "Resíduos: média=%.3f  DP=%.3f  (real − previsto, em p.p.)",
        residuo.mean(), desvio,
    )
    return ResultadoResiduos(
        df=out,
        acima=out.head(top_n).reset_index(drop=True),
        abaixo=out.tail(top_n).iloc[::-1].reset_index(drop=True),
    )


# =============================================================================
# EQUIDADE — RESÍDUOS POR GRUPO DE LOCALIZAÇÃO (validação temporal)
# =============================================================================

def agrupar_localizacao(df: pd.DataFrame) -> pd.Series:
    """
    Rótulo de localização por escola-ano: 'diferenciada' (terra indígena /
    quilombola), 'rural' ou 'urbana'. A categoria diferenciada tem
    precedência sobre rural (toda escola diferenciada é também rural).
    """
    def rotulo(r) -> str:
        if r.get("is_loc_diferenciada", 0) == 1:
            return "diferenciada"
        return "rural" if r.get("is_rural", 0) == 1 else "urbana"
    return df.apply(rotulo, axis=1)


def residuos_validacao_temporal(
    modelo, df: pd.DataFrame | None = None
) -> pd.DataFrame:
    """
    Resíduos na validação temporal (simula o uso real): clona o modelo,
    treina no par 2022→2023 e prediz o par 2023→2024 — nunca visto no
    treino. Devolve um DataFrame com `residuo` (real − previsto, em p.p.)
    e `grupo` de localização, base da reavaliação de equidade do XGBoost.
    """
    if df is None:
        df = carregar_dataset()

    treino, teste = split_temporal(df)
    X_tr, y_tr, _ = preparar_xy(treino)
    X_te, _, _ = preparar_xy(teste)

    m = clone(modelo)
    m.fit(X_tr, y_tr)
    y_pred = np.asarray(m.predict(X_te), dtype=float)

    out = teste[[c for c in ["CO_ENTIDADE", "NO_ENTIDADE", "NO_MUNICIPIO",
                             "is_rural", "is_loc_diferenciada", ANO_COL]
                 if c in teste.columns]].copy()
    out["y_real"] = teste[TARGET_COL].to_numpy(dtype=float)
    out["y_pred"] = y_pred
    out["residuo"] = out["y_real"] - out["y_pred"]
    out["grupo"] = agrupar_localizacao(out)
    return out.reset_index(drop=True)


def resumo_residuos_por_grupo(df_residuos: pd.DataFrame) -> pd.DataFrame:
    """Média, desvio e n dos resíduos por grupo de localização."""
    return (
        df_residuos.groupby("grupo")["residuo"]
        .agg(media="mean", desvio="std", n="count")
        .reindex(["urbana", "rural", "diferenciada"])
        .reset_index()
    )
