"""
Fase 6 — Tuning do XGBoost.
Escolas estaduais de EM em PE — prever taxa_abandono_t1.

Responde às perguntas:
  X1. Quais hiperparâmetros do XGBoost minimizam o RMSE em validação cruzada
      agrupada por município (GroupKFold)?
  X2. Transformar o target (log1p, sqrt) melhora o XGBoost tunado?
  X3. O XGBoost supera os baselines (Ridge, Random Forest) na MESMA validação?
  X4. Como o XGBoost final se comporta na validação temporal (2022→2023 treina,
      2023→2024 testa)?
  X5. Quais features o XGBoost considera mais importantes (ganho) e como ficam
      os resíduos?

Saídas:
  - Texto no console
  - Figuras salvas em: reports/figuras/  (prefixo X*)
  - Métricas em: reports/metricas_xgboost.csv
  - Melhor modelo serializado em: models/xgboost_v1.joblib
"""

from __future__ import annotations

import logging

from comum import (
    CORES_MODELOS,
    FIGURAS_DIR,
    LABELS_MODELOS,
    REPORTS_DIR,
    imprimir_tabela_metricas,
    salvar_figura,
    salvar_metricas_cv_e_temporal,
    sep,
)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import average_precision_score, roc_auc_score

from src.models.evaluate import (
    calcular_metricas,
    resumir_cv,
    validacao_cruzada_grupos,
)
from src.models.train import (
    GRID_RF,
    GRID_RIDGE,
    GRID_XGB,
    TRANSFORMACOES_TARGET,
    aplicar_transformacao_target,
    buscar_hiperparametros,
    carregar_dataset,
    criar_baselines,
    criar_xgboost,
    preparar_xy,
    salvar_modelo,
    split_temporal,
)

logger = logging.getLogger(__name__)

METRICAS_PATH = REPORTS_DIR / "metricas_xgboost.csv"


def extrair_pipeline(modelo):
    """Devolve o Pipeline subjacente, esteja ou não embrulhado num
    TransformedTargetRegressor já ajustado."""
    if isinstance(modelo, TransformedTargetRegressor):
        return modelo.regressor_
    return modelo


# =============================================================================
# X1 — TUNING DO XGBOOST
# =============================================================================

def tuning_xgboost(df: pd.DataFrame):
    sep("X1 — TUNING DO XGBOOST (GridSearchCV, GroupKFold por município)")

    X, y, grupos = preparar_xy(df)
    print(f"\nX: {X.shape[0]:,} obs × {X.shape[1]} features  |  "
          f"grupos (municípios): {grupos.nunique()}")

    n_combos = int(np.prod([len(v) for v in GRID_XGB.values()]))
    print(f"\nGrade: {n_combos} combinações × 5 folds = {n_combos * 5} ajustes.")
    print("Hiperparâmetros buscados:")
    for k, v in GRID_XGB.items():
        print(f"  {k.replace('model__', ''):<18} {v}")

    pipe = criar_xgboost(X)
    gs = buscar_hiperparametros(pipe, GRID_XGB, X, y, grupos)
    print(f"\nMelhores parâmetros: "
          f"{ {k.replace('model__', ''): v for k, v in gs.best_params_.items()} }")
    print(f"RMSE CV (melhor): {-gs.best_score_:.3f} p.p.")

    return gs.best_estimator_, (X, y, grupos)


# =============================================================================
# X2 — TRANSFORMAÇÃO DO TARGET NO XGBOOST TUNADO
# =============================================================================

def avaliar_transformacoes_xgb(xgb_best, dados) -> pd.DataFrame:
    X, y, grupos = dados
    resultados = []
    for nome_tr in TRANSFORMACOES_TARGET:
        modelo_tr = aplicar_transformacao_target(clone(xgb_best), nome_tr)
        df_folds = validacao_cruzada_grupos(modelo_tr, X, y, grupos)
        resultados.append({
            "transformacao": nome_tr,
            "rmse": df_folds["rmse"].mean(),
            "rmse_dp": df_folds["rmse"].std(),
            "spearman": df_folds["spearman"].mean(),
            "precision_at_k": df_folds["precision_at_k"].mean(),
        })
    return pd.DataFrame(resultados)


def figura_transformacoes_xgb(res: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    xpos = np.arange(len(res))
    ax.bar(xpos, res["rmse"], yerr=res["rmse_dp"], capsize=4,
           color=CORES_MODELOS["xgboost"], alpha=0.85)
    ax.set_xticks(xpos)
    ax.set_xticklabels(res["transformacao"])
    ax.set_ylabel("RMSE em CV (p.p., menor=melhor)")
    ax.set_title("X2 — Transformação do target no XGBoost tunado",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "X2_transformacao_target.png")


def transformacao_target_xgb(xgb_best, dados) -> str:
    sep("X2 — TRANSFORMAÇÃO DO TARGET NO XGBOOST (identidade × log1p × sqrt)")

    res = avaliar_transformacoes_xgb(xgb_best, dados)

    print(f"\n{'Transformação':<15}{'RMSE':>14}{'Spearman':>12}{'P@K':>10}")
    print("-" * 51)
    for _, r in res.iterrows():
        print(f"  {r['transformacao']:<13}{r['rmse']:>9.3f} ±{r['rmse_dp']:.2f}"
              f"{r['spearman']:>12.3f}{r['precision_at_k']:>10.3f}")

    melhor = res.loc[res["rmse"].idxmin(), "transformacao"]
    print(f"\nMelhor transformação para o XGBoost: {melhor}")

    figura_transformacoes_xgb(res)
    return melhor


# =============================================================================
# X3 — COMPARAÇÃO CV: XGBOOST × BASELINES
# =============================================================================

def figura_comparacao_cv(modelos: dict, folds_por_modelo: dict) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    for ax, metrica, titulo in zip(
        axes,
        ["rmse", "spearman", "precision_at_k"],
        ["RMSE (p.p., menor=melhor)", "Spearman (maior=melhor)", "Precision@K (K=10%)"],
    ):
        dados_plot = [folds_por_modelo[m][metrica] for m in modelos]
        bp = ax.boxplot(dados_plot, tick_labels=[LABELS_MODELOS[m] for m in modelos],
                        patch_artist=True, medianprops=dict(color="black", lw=2))
        for patch, nome in zip(bp["boxes"], modelos):
            patch.set_facecolor(CORES_MODELOS[nome])
            patch.set_alpha(0.75)
        ax.set_title(titulo)
        ax.tick_params(axis="x", rotation=12)
    fig.suptitle("X3 — XGBoost × baselines em validação cruzada (GroupKFold por município)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "X3_comparacao_cv.png")


def comparacao_cv(df: pd.DataFrame, xgb_final, dados):
    sep("X3 — COMPARAÇÃO EM VALIDAÇÃO CRUZADA (XGBoost × baselines)")

    X, y, grupos = dados

    # Baselines tunados na MESMA CV agrupada (folds idênticos → comparação justa)
    baselines = criar_baselines(X)
    gs_ridge = buscar_hiperparametros(baselines["ridge"], GRID_RIDGE, X, y, grupos)
    gs_rf = buscar_hiperparametros(baselines["random_forest"], GRID_RF, X, y, grupos)

    modelos = {
        "dummy_media": baselines["dummy_media"],
        "ridge": gs_ridge.best_estimator_,
        "random_forest": gs_rf.best_estimator_,
        "xgboost": xgb_final,
    }

    folds_por_modelo: dict[str, pd.DataFrame] = {}
    resumos: dict[str, dict[str, str]] = {}
    for nome, modelo in modelos.items():
        logger.info("Validação cruzada: %s", nome)
        df_folds = validacao_cruzada_grupos(clone(modelo), X, y, grupos)
        folds_por_modelo[nome] = df_folds
        resumos[nome] = resumir_cv(df_folds)

    print("\nMétricas em CV (média ± DP entre 5 folds, escala original em p.p.):")
    imprimir_tabela_metricas(resumos)

    figura_comparacao_cv(modelos, folds_por_modelo)
    return modelos, folds_por_modelo


# =============================================================================
# X4 — VALIDAÇÃO TEMPORAL
# =============================================================================

def relatorio_metricas_temporais(resultados: dict) -> None:
    print(f"\n{'Modelo':<22}{'RMSE':>9}{'MAE':>9}{'R²':>9}{'Spearman':>10}{'P@K':>8}")
    print("-" * 70)
    for nome, m in resultados.items():
        print(f"  {LABELS_MODELOS[nome]:<20}{m['rmse']:>9.3f}{m['mae']:>9.3f}"
              f"{m['r2']:>9.3f}{m['spearman']:>10.3f}{m['precision_at_k']:>8.3f}")


def avaliacao_binarizada(y_te: pd.Series, predicoes: dict) -> dict:
    """Avaliação binarizada pós-hoc (mesma metodologia do notebook 07):
    escolas críticas = decil superior de abandono em 2024; predições contínuas
    usadas como scores de risco. Permite comparar com a literatura (AUC)."""
    y_bin = (y_te >= y_te.quantile(0.90)).astype(int).to_numpy()
    binarizado = {}
    print(f"\n{'Modelo':<22}{'ROC-AUC':>10}{'PR-AUC':>10}")
    print("-" * 42)
    for nome, y_pred in predicoes.items():
        roc = roc_auc_score(y_bin, y_pred)
        pr = average_precision_score(y_bin, y_pred)
        binarizado[nome] = {"roc_auc": float(roc), "pr_auc": float(pr)}
        print(f"  {LABELS_MODELOS[nome]:<20}{roc:>10.3f}{pr:>10.3f}")
    return binarizado


def figura_validacao_temporal(resultados: dict, y_te: pd.Series, y_pred: np.ndarray) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    ax.scatter(y_te, y_pred, alpha=0.3, s=14, color=CORES_MODELOS["xgboost"])
    lim = max(y_te.max(), float(np.max(y_pred))) * 1.05
    ax.plot([0, lim], [0, lim], "k--", lw=1.2, label="Predição perfeita")
    ax.set_xlabel("Taxa de abandono real 2024 (%)")
    ax.set_ylabel("Taxa de abandono predita (%)")
    mx = resultados["xgboost"]
    ax.set_title(f"XGBoost — predito × real\n"
                 f"RMSE={mx['rmse']:.2f}  Spearman={mx['spearman']:.3f}")
    ax.legend(fontsize=9)

    ax = axes[1]
    metricas_plot = ["rmse", "mae"]
    xpos = np.arange(len(metricas_plot))
    largura = 0.2
    for i, nome in enumerate(resultados):
        vals = [resultados[nome][mt] for mt in metricas_plot]
        ax.bar(xpos + (i - 1.5) * largura, vals, largura,
               color=CORES_MODELOS[nome], alpha=0.85, label=LABELS_MODELOS[nome])
    ax.set_xticks(xpos)
    ax.set_xticklabels(["RMSE", "MAE"])
    ax.set_ylabel("Erro (pontos percentuais)")
    ax.set_title("Erro no conjunto de teste temporal")
    ax.legend(fontsize=8)

    fig.suptitle("X4 — Validação temporal (2022→2023 treina, 2023→2024 testa)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "X4_validacao_temporal.png")


def validacao_temporal(df: pd.DataFrame, modelos: dict) -> dict:
    sep("X4 — VALIDAÇÃO TEMPORAL (treina 2022→2023, testa 2023→2024)")

    treino, teste = split_temporal(df)
    X_tr, y_tr, _ = preparar_xy(treino)
    X_te, y_te, _ = preparar_xy(teste)
    print(f"\nTreino: {len(X_tr):,} obs (features 2022, abandono 2023)")
    print(f"Teste:  {len(X_te):,} obs (features 2023, abandono 2024)")

    resultados = {}
    predicoes = {}
    modelos_fit = {}
    for nome, modelo in modelos.items():
        m = clone(modelo)
        m.fit(X_tr, y_tr)
        y_pred = m.predict(X_te)
        resultados[nome] = calcular_metricas(y_te, y_pred)
        predicoes[nome] = y_pred
        modelos_fit[nome] = m

    relatorio_metricas_temporais(resultados)

    melhor_nome = min(
        (n for n in resultados if n != "dummy_media"),
        key=lambda n: resultados[n]["rmse"],
    )
    print(f"\nMelhor modelo na validação temporal: {LABELS_MODELOS[melhor_nome]}")

    binarizado = avaliacao_binarizada(y_te, predicoes)
    figura_validacao_temporal(resultados, y_te, predicoes["xgboost"])

    return {
        "resultados": resultados,
        "predicoes": predicoes,
        "modelos_fit": modelos_fit,
        "binarizado": binarizado,
        "melhor_nome": melhor_nome,
        "teste": teste,
        "y_te": y_te,
    }


# =============================================================================
# X5 — IMPORTÂNCIA DAS FEATURES E RESÍDUOS
# =============================================================================

def importancias_do_xgboost(xgb_temporal) -> pd.DataFrame:
    pipe = extrair_pipeline(xgb_temporal)
    nomes = pipe.named_steps["preprocess"].get_feature_names_out()
    nomes = [n.split("__", 1)[-1] for n in nomes]
    importancias = pipe.named_steps["model"].feature_importances_

    return (pd.DataFrame({"feature": nomes, "ganho": importancias})
            .sort_values("ganho", ascending=False)
            .reset_index(drop=True))


def figura_importancia_e_residuos(imp: pd.DataFrame, teste: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    top = imp.head(15).iloc[::-1]
    ax.barh(top["feature"], top["ganho"], color=CORES_MODELOS["xgboost"], alpha=0.85)
    ax.set_xlabel("Ganho (importância relativa)")
    ax.set_title("Top 15 features — importância (ganho)")

    ax = axes[1]
    ax.scatter(teste["y_pred"], teste["residuo"], alpha=0.3, s=14,
               color=CORES_MODELOS["xgboost"])
    ax.axhline(0, color="black", lw=1.2)
    ax.set_xlabel("Taxa de abandono predita (%)")
    ax.set_ylabel("Resíduo (p.p.)")
    ax.set_title("Resíduo × predito (validação temporal)")

    fig.suptitle("X5 — Importância das features e resíduos do XGBoost",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "X5_importancia_residuos.png")


def importancia_e_residuos(temporal: dict, xgb_temporal) -> None:
    sep("X5 — IMPORTÂNCIA DAS FEATURES (ganho) E RESÍDUOS DO XGBOOST")

    imp = importancias_do_xgboost(xgb_temporal)

    print("\nTop 15 features por ganho (importância do XGBoost):")
    for _, r in imp.head(15).iterrows():
        print(f"  {r['feature']:<28} {r['ganho']:.4f}")

    teste = temporal["teste"].copy()
    teste["y_pred"] = temporal["predicoes"]["xgboost"]
    teste["residuo"] = teste["taxa_abandono_t1"] - teste["y_pred"]
    print(f"\nResíduo XGBoost (real − predito): média={teste['residuo'].mean():.2f}  "
          f"DP={teste['residuo'].std():.2f}")

    figura_importancia_e_residuos(imp, teste)
    imp.to_csv(METRICAS_PATH.parent / "xgboost_feature_importance.csv", index=False)


# =============================================================================
# REGISTRO DE MÉTRICAS E SERIALIZAÇÃO
# =============================================================================

def registrar_e_salvar(df, folds_por_modelo, temporal, melhor_tr, xgb_best) -> None:
    sep("REGISTRO DE MÉTRICAS E SERIALIZAÇÃO")

    salvar_metricas_cv_e_temporal(folds_por_modelo, temporal["resultados"], METRICAS_PATH)

    # Modelo final: XGBoost tunado + melhor transformação, re-treinado em TODOS os dados
    X, y, _ = preparar_xy(df)
    modelo_final = aplicar_transformacao_target(clone(xgb_best), melhor_tr)
    modelo_final.fit(X, y)
    out = salvar_modelo(modelo_final, "xgboost_v1")
    print(f"XGBoost final (target={melhor_tr}) treinado com todos os dados "
          f"e salvo em:\n  {out}")


# =============================================================================
# SUMÁRIO
# =============================================================================

def sumario(folds_por_modelo, temporal, melhor_tr) -> None:
    sep("SUMÁRIO EXECUTIVO — FASE 6 (TUNING XGBOOST)")

    xgb_cv = resumir_cv(folds_por_modelo["xgboost"])
    rf_cv = resumir_cv(folds_por_modelo["random_forest"])
    ridge_cv = resumir_cv(folds_por_modelo["ridge"])
    xgb_tmp = temporal["resultados"]["xgboost"]

    print(f"""
MODELO PRINCIPAL: XGBoost (target: {melhor_tr})

VALIDAÇÃO
  • CV: GroupKFold 5 folds agrupado por município (anti-vazamento espacial)
  • Temporal: treina 2022→2023, testa 2023→2024
  • Comparação justa: baselines re-tunados nos MESMOS folds

XGBOOST EM CV
  • RMSE={xgb_cv['rmse']}  Spearman={xgb_cv['spearman']}  P@K={xgb_cv['precision_at_k']}
  • Ridge CV → RMSE={ridge_cv['rmse']}  Spearman={ridge_cv['spearman']}
  • RF CV    → RMSE={rf_cv['rmse']}  Spearman={rf_cv['spearman']}

XGBOOST NA VALIDAÇÃO TEMPORAL
  • RMSE={xgb_tmp['rmse']:.3f}  MAE={xgb_tmp['mae']:.3f}  R²={xgb_tmp['r2']:.3f}
  • Spearman={xgb_tmp['spearman']:.3f}  P@K={xgb_tmp['precision_at_k']:.3f}
  • Melhor modelo no split temporal: {LABELS_MODELOS[temporal['melhor_nome']]}

ARTEFATOS
  • models/xgboost_v1.joblib (modelo principal serializado)
  • reports/metricas_xgboost.csv
  • reports/xgboost_feature_importance.csv
  • reports/figuras/X2–X5

PRÓXIMA FASE (7)
  → Explicabilidade com SHAP (global e local) sobre o XGBoost final
  → Análise de resíduos aprofundada (P3: escolas acima/abaixo do esperado)
""")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    df = carregar_dataset()

    xgb_best, dados = tuning_xgboost(df)
    melhor_tr = transformacao_target_xgb(xgb_best, dados)
    xgb_final = aplicar_transformacao_target(clone(xgb_best), melhor_tr)

    modelos, folds_por_modelo = comparacao_cv(df, xgb_final, dados)
    temporal = validacao_temporal(df, modelos)
    importancia_e_residuos(temporal, temporal["modelos_fit"]["xgboost"])
    registrar_e_salvar(df, folds_por_modelo, temporal, melhor_tr, xgb_best)
    sumario(folds_por_modelo, temporal, melhor_tr)

    print("Figuras salvas em:", FIGURAS_DIR)


if __name__ == "__main__":
    main()
