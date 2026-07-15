"""
Fase 5 — Baselines de modelagem (Ridge e Random Forest).
Escolas estaduais de EM em PE — prever taxa_abandono_t1.

Responde às perguntas:
  M1. Como os baselines se comparam em validação cruzada (GroupKFold por município)?
  M2. Transformar o target (log1p, sqrt) melhora as métricas?
  M3. Como o melhor baseline se comporta em validação temporal (2022→2023 treina, 2023→2024 testa)?
  M4. Como são os resíduos do melhor baseline (preview da análise P3)?

Saídas:
  - Texto no console
  - Figuras salvas em: reports/figuras/  (prefixo M*)
  - Métricas em: reports/metricas_baselines.csv
  - Melhor baseline serializado em: models/
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

from src.models.evaluate import (
    calcular_metricas,
    resumir_cv,
    validacao_cruzada_grupos,
)
from src.models.train import (
    GRID_RF,
    GRID_RIDGE,
    TRANSFORMACOES_TARGET,
    aplicar_transformacao_target,
    buscar_hiperparametros,
    carregar_dataset,
    criar_baselines,
    preparar_xy,
    salvar_modelo,
    split_temporal,
)

logger = logging.getLogger(__name__)

METRICAS_PATH = REPORTS_DIR / "metricas_baselines.csv"


# =============================================================================
# M1 — COMPARAÇÃO DOS BASELINES EM VALIDAÇÃO CRUZADA
# =============================================================================

def tunar_baselines(X: pd.DataFrame, y: pd.Series, grupos: pd.Series) -> dict:
    baselines = criar_baselines(X)
    print("\nBusca de hiperparâmetros (GridSearchCV, 5 folds agrupados):")
    gs_ridge = buscar_hiperparametros(baselines["ridge"], GRID_RIDGE, X, y, grupos)
    print(f"  Ridge          → {gs_ridge.best_params_}  (RMSE CV={-gs_ridge.best_score_:.3f})")
    gs_rf = buscar_hiperparametros(baselines["random_forest"], GRID_RF, X, y, grupos)
    print(f"  Random Forest  → {gs_rf.best_params_}  (RMSE CV={-gs_rf.best_score_:.3f})")

    return {
        "dummy_media": baselines["dummy_media"],
        "ridge": gs_ridge.best_estimator_,
        "random_forest": gs_rf.best_estimator_,
    }


def figura_baselines_cv(modelos: dict, folds_por_modelo: dict) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, metrica, titulo in zip(
        axes,
        ["rmse", "spearman", "precision_at_k"],
        ["RMSE (p.p., menor=melhor)", "Spearman (maior=melhor)", "Precision@K (K=10%)"],
    ):
        dados = [folds_por_modelo[m][metrica] for m in modelos]
        bp = ax.boxplot(dados, tick_labels=[LABELS_MODELOS[m] for m in modelos],
                        patch_artist=True, medianprops=dict(color="black", lw=2))
        for patch, nome in zip(bp["boxes"], modelos):
            patch.set_facecolor(CORES_MODELOS[nome])
            patch.set_alpha(0.75)
        ax.set_title(titulo)
        ax.tick_params(axis="x", rotation=10)
    fig.suptitle("M1 — Baselines em validação cruzada (GroupKFold por município)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "M1_baselines_cv.png")


def comparacao_baselines(df: pd.DataFrame) -> tuple[dict, dict]:
    sep("M1 — BASELINES EM VALIDAÇÃO CRUZADA (GroupKFold por município)")

    X, y, grupos = preparar_xy(df)
    print(f"\nX: {X.shape[0]:,} obs × {X.shape[1]} features  |  "
          f"grupos (municípios): {grupos.nunique()}")

    modelos = tunar_baselines(X, y, grupos)

    folds_por_modelo: dict[str, pd.DataFrame] = {}
    resumos: dict[str, dict[str, str]] = {}
    for nome, modelo in modelos.items():
        logger.info("Validação cruzada: %s", nome)
        df_folds = validacao_cruzada_grupos(modelo, X, y, grupos)
        folds_por_modelo[nome] = df_folds
        resumos[nome] = resumir_cv(df_folds)

    print("\nMétricas em CV (média ± DP entre 5 folds, escala original em p.p.):")
    imprimir_tabela_metricas(resumos)

    figura_baselines_cv(modelos, folds_por_modelo)
    return modelos, folds_por_modelo


# =============================================================================
# M2 — TRANSFORMAÇÃO DO TARGET
# =============================================================================

def avaliar_transformacoes(df: pd.DataFrame, modelos: dict) -> pd.DataFrame:
    X, y, grupos = preparar_xy(df)
    resultados = []
    for nome_modelo in ["ridge", "random_forest"]:
        for nome_tr in TRANSFORMACOES_TARGET:
            modelo_tr = aplicar_transformacao_target(modelos[nome_modelo], nome_tr)
            df_folds = validacao_cruzada_grupos(modelo_tr, X, y, grupos)
            resultados.append({
                "modelo": nome_modelo,
                "transformacao": nome_tr,
                "rmse": df_folds["rmse"].mean(),
                "rmse_dp": df_folds["rmse"].std(),
                "spearman": df_folds["spearman"].mean(),
                "precision_at_k": df_folds["precision_at_k"].mean(),
            })
    return pd.DataFrame(resultados)


def relatorio_transformacoes(res: pd.DataFrame) -> dict[str, str]:
    print(f"\n{'Modelo':<16}{'Transformação':<15}{'RMSE':>12}{'Spearman':>12}{'P@K':>10}")
    print("-" * 65)
    for _, r in res.iterrows():
        print(f"  {r['modelo']:<14}{r['transformacao']:<15}"
              f"{r['rmse']:>9.3f} ±{r['rmse_dp']:.2f}{r['spearman']:>12.3f}"
              f"{r['precision_at_k']:>10.3f}")

    melhores = {}
    for nome_modelo in ["ridge", "random_forest"]:
        sub = res[res["modelo"] == nome_modelo]
        melhor = sub.loc[sub["rmse"].idxmin(), "transformacao"]
        melhores[nome_modelo] = melhor
        print(f"\nMelhor transformação para {nome_modelo}: {melhor}")
    return melhores


def figura_transformacoes(res: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    for ax, metrica, titulo in zip(
        axes, ["rmse", "spearman"],
        ["RMSE por transformação (menor=melhor)", "Spearman por transformação"],
    ):
        largura = 0.35
        transformacoes = list(TRANSFORMACOES_TARGET)
        xpos = np.arange(len(transformacoes))
        for i, nome_modelo in enumerate(["ridge", "random_forest"]):
            sub = res[res["modelo"] == nome_modelo].set_index("transformacao")
            vals = [sub.loc[t, metrica] for t in transformacoes]
            ax.bar(xpos + (i - 0.5) * largura, vals, largura,
                   color=CORES_MODELOS[nome_modelo], alpha=0.85,
                   label=LABELS_MODELOS[nome_modelo])
        ax.set_xticks(xpos)
        ax.set_xticklabels(transformacoes)
        ax.set_title(titulo)
        ax.legend(fontsize=9)
    fig.suptitle("M2 — Efeito da transformação do target", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "M2_transformacao_target.png")


def comparacao_transformacoes(df: pd.DataFrame, modelos: dict) -> dict[str, str]:
    sep("M2 — TRANSFORMAÇÃO DO TARGET (identidade × log1p × sqrt)")

    res = avaliar_transformacoes(df, modelos)
    melhores = relatorio_transformacoes(res)
    figura_transformacoes(res)

    res.to_csv(METRICAS_PATH.parent / "metricas_transformacoes.csv", index=False)
    return melhores


# =============================================================================
# M3 — VALIDAÇÃO TEMPORAL
# =============================================================================

def relatorio_metricas_temporais(resultados: dict) -> None:
    print(f"\n{'Modelo':<22}{'RMSE':>9}{'MAE':>9}{'R²':>9}{'Spearman':>10}{'P@K':>8}")
    print("-" * 70)
    for nome, m in resultados.items():
        print(f"  {LABELS_MODELOS[nome]:<20}{m['rmse']:>9.3f}{m['mae']:>9.3f}"
              f"{m['r2']:>9.3f}{m['spearman']:>10.3f}{m['precision_at_k']:>8.3f}")


def figura_validacao_temporal(resultados: dict, y_te: pd.Series,
                              y_pred: np.ndarray, melhor_nome: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    ax.scatter(y_te, y_pred, alpha=0.3, s=14, color=CORES_MODELOS[melhor_nome])
    lim = max(y_te.max(), float(np.max(y_pred))) * 1.05
    ax.plot([0, lim], [0, lim], "k--", lw=1.2, label="Predição perfeita")
    ax.set_xlabel("Taxa de abandono real 2024 (%)")
    ax.set_ylabel("Taxa de abandono predita (%)")
    m = resultados[melhor_nome]
    ax.set_title(f"{LABELS_MODELOS[melhor_nome]} — predito × real\n"
                 f"RMSE={m['rmse']:.2f}  Spearman={m['spearman']:.3f}")
    ax.legend(fontsize=9)

    ax = axes[1]
    metricas_plot = ["rmse", "mae"]
    xpos = np.arange(len(metricas_plot))
    largura = 0.25
    for i, nome in enumerate(resultados):
        vals = [resultados[nome][mt] for mt in metricas_plot]
        ax.bar(xpos + (i - 1) * largura, vals, largura,
               color=CORES_MODELOS[nome], alpha=0.85, label=LABELS_MODELOS[nome])
    ax.set_xticks(xpos)
    ax.set_xticklabels(["RMSE", "MAE"])
    ax.set_ylabel("Erro (pontos percentuais)")
    ax.set_title("Erro no conjunto de teste temporal")
    ax.legend(fontsize=9)

    fig.suptitle("M3 — Validação temporal (2022→2023 treina, 2023→2024 testa)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "M3_validacao_temporal.png")


def validacao_temporal(df: pd.DataFrame, modelos: dict, melhores_tr: dict) -> dict:
    sep("M3 — VALIDAÇÃO TEMPORAL (treina 2022→2023, testa 2023→2024)")

    treino, teste = split_temporal(df)
    X_tr, y_tr, _ = preparar_xy(treino)
    X_te, y_te, _ = preparar_xy(teste)
    print(f"\nTreino: {len(X_tr):,} obs (features 2022, abandono 2023)")
    print(f"Teste:  {len(X_te):,} obs (features 2023, abandono 2024)")

    resultados = {}
    predicoes = {}
    for nome in ["dummy_media", "ridge", "random_forest"]:
        modelo = modelos[nome]
        if nome in melhores_tr:
            modelo = aplicar_transformacao_target(modelo, melhores_tr[nome])
        modelo = clone(modelo)
        modelo.fit(X_tr, y_tr)
        y_pred = modelo.predict(X_te)
        resultados[nome] = calcular_metricas(y_te, y_pred)
        predicoes[nome] = y_pred

    relatorio_metricas_temporais(resultados)

    melhor_nome = min(
        (n for n in resultados if n != "dummy_media"),
        key=lambda n: resultados[n]["rmse"],
    )
    print(f"\nMelhor baseline na validação temporal: {LABELS_MODELOS[melhor_nome]}")

    figura_validacao_temporal(resultados, y_te, predicoes[melhor_nome], melhor_nome)

    return {
        "resultados": resultados,
        "predicoes": predicoes,
        "melhor_nome": melhor_nome,
        "teste": teste,
        "y_te": y_te,
    }


# =============================================================================
# M4 — ANÁLISE PRELIMINAR DE RESÍDUOS (preview da P3)
# =============================================================================

def relatorio_residuos_extremos(teste: pd.DataFrame) -> None:
    print("\nTop 10 — abandono ACIMA do esperado pelo perfil (resíduo +):")
    for _, r in teste.nlargest(10, "residuo").iterrows():
        print(f"  {r['NO_ENTIDADE'][:45]:<47} ({r['NO_MUNICIPIO']}): "
              f"real={r['taxa_abandono_t1']:.1f}%  pred={r['y_pred']:.1f}%")

    print("\nTop 10 — abandono ABAIXO do esperado (escolas resilientes, resíduo −):")
    for _, r in teste.nsmallest(10, "residuo").iterrows():
        print(f"  {r['NO_ENTIDADE'][:45]:<47} ({r['NO_MUNICIPIO']}): "
              f"real={r['taxa_abandono_t1']:.1f}%  pred={r['y_pred']:.1f}%")


def figura_residuos(teste: pd.DataFrame, melhor: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    ax = axes[0]
    ax.hist(teste["residuo"], bins=40, color="#6A1B9A", edgecolor="white", alpha=0.85)
    ax.axvline(0, color="black", lw=1.2)
    ax.set_xlabel("Resíduo (real − predito, p.p.)")
    ax.set_ylabel("N escolas")
    ax.set_title("Distribuição dos resíduos")

    ax = axes[1]
    ax.scatter(teste["y_pred"], teste["residuo"], alpha=0.3, s=14, color="#6A1B9A")
    ax.axhline(0, color="black", lw=1.2)
    ax.set_xlabel("Taxa de abandono predita (%)")
    ax.set_ylabel("Resíduo (p.p.)")
    ax.set_title("Resíduo × predito (heterocedasticidade?)")

    fig.suptitle(f"M4 — Resíduos do {LABELS_MODELOS[melhor]} na validação temporal",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "M4_residuos.png")


def analise_residuos(temporal: dict) -> None:
    sep("M4 — RESÍDUOS DO MELHOR BASELINE (preview da análise P3)")

    melhor = temporal["melhor_nome"]
    teste = temporal["teste"].copy()
    teste["y_pred"] = temporal["predicoes"][melhor]
    teste["residuo"] = teste["taxa_abandono_t1"] - teste["y_pred"]

    print(f"\nModelo: {LABELS_MODELOS[melhor]}")
    print(f"Resíduo (real − predito): média={teste['residuo'].mean():.2f}  "
          f"DP={teste['residuo'].std():.2f}")

    relatorio_residuos_extremos(teste)
    figura_residuos(teste, melhor)


# =============================================================================
# REGISTRO DE MÉTRICAS E SERIALIZAÇÃO
# =============================================================================

def registrar_e_salvar(
    df: pd.DataFrame,
    modelos: dict,
    folds_por_modelo: dict,
    melhores_tr: dict,
    temporal: dict,
) -> None:
    sep("REGISTRO DE MÉTRICAS E SERIALIZAÇÃO")

    salvar_metricas_cv_e_temporal(folds_por_modelo, temporal["resultados"], METRICAS_PATH)

    melhor = temporal["melhor_nome"]
    X, y, _ = preparar_xy(df)
    modelo_final = aplicar_transformacao_target(modelos[melhor], melhores_tr[melhor])
    modelo_final = clone(modelo_final)
    modelo_final.fit(X, y)
    out = salvar_modelo(modelo_final, f"baseline_{melhor}_v1")
    print(f"Melhor baseline ({LABELS_MODELOS[melhor]}, target={melhores_tr[melhor]}) "
          f"treinado com todos os dados e salvo em:\n  {out}")


# =============================================================================
# SUMÁRIO
# =============================================================================

def sumario(folds_por_modelo: dict, melhores_tr: dict, temporal: dict) -> None:
    sep("SUMÁRIO EXECUTIVO — FASE 5 (BASELINES)")

    melhor = temporal["melhor_nome"]
    m_cv = resumir_cv(folds_por_modelo[melhor])
    m_tmp = temporal["resultados"][melhor]
    dummy_cv = resumir_cv(folds_por_modelo["dummy_media"])

    print(f"""
MODELOS AVALIADOS
  • Dummy (média) — piso de referência
  • Ridge — baseline linear (grid de alpha)
  • Random Forest — baseline não-linear (grid leve)

VALIDAÇÃO
  • CV: GroupKFold 5 folds agrupado por município (anti-vazamento espacial)
  • Temporal: treina 2022→2023, testa 2023→2024
  • Transformações de target testadas: {', '.join(TRANSFORMACOES_TARGET)}

MELHOR BASELINE: {LABELS_MODELOS[melhor]} (target: {melhores_tr.get(melhor, 'identidade')})
  • CV       → RMSE={m_cv['rmse']}  Spearman={m_cv['spearman']}  P@K={m_cv['precision_at_k']}
  • Temporal → RMSE={m_tmp['rmse']:.3f}  Spearman={m_tmp['spearman']:.3f}  P@K={m_tmp['precision_at_k']:.3f}
  • Dummy CV → RMSE={dummy_cv['rmse']} (referência de piso)

PRÓXIMA FASE (6)
  → Tuning do XGBoost com a mesma validação (GroupKFold + temporal)
  → Meta: superar o melhor baseline em RMSE e Spearman
""")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    df = carregar_dataset()

    modelos, folds_por_modelo = comparacao_baselines(df)
    melhores_tr = comparacao_transformacoes(df, modelos)
    temporal = validacao_temporal(df, modelos, melhores_tr)
    analise_residuos(temporal)
    registrar_e_salvar(df, modelos, folds_por_modelo, melhores_tr, temporal)
    sumario(folds_por_modelo, melhores_tr, temporal)

    print("Figuras salvas em:", FIGURAS_DIR)


if __name__ == "__main__":
    main()
