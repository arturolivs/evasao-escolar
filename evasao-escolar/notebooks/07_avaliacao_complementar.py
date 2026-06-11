"""
Fase 5 (complemento) — análises de avaliação previstas na metodologia
que não foram cobertas pelo notebook 06.

Responde às perguntas:
  M5. Como Precision@K e captura de escolas críticas variam com K?
      (decisoes_projeto.md §2.1: "ranking flexível top-N sem retreinar")
  M6. Quão estáveis são as métricas sob repetições da validação cruzada?
      (§8.3: "reportar erro padrão das métricas via repetições do CV")
  M7. Como o modelo se compara à literatura em avaliação binarizada pós-hoc?
      (§2.1: "análise complementar binarizada pode ser feita pós-hoc")
  M8. Quais as top-20 escolas com resíduo extremo e como os resíduos se
      distribuem por grupo? (§8.4: análise qualitativa de resíduos)

Saídas:
  - Texto no console
  - Figuras salvas em: reports/figuras/  (M5–M8)
  - reports/metricas_cv_repetida.csv
  - reports/residuos_top20_temporal.csv
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import auc, precision_recall_curve, roc_auc_score, roc_curve
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.models.evaluate import calcular_metricas, precision_at_k
from src.models.train import (
    RANDOM_STATE,
    aplicar_transformacao_target,
    carregar_dataset,
    criar_pipeline,
    preparar_xy,
    split_temporal,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

FIGURAS_DIR = ROOT / "reports" / "figuras"
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = ROOT / "reports"

# Configurações vencedoras da Fase 5 (notebook 06)
PARAMS_RIDGE = {"alpha": 100.0}
PARAMS_RF = {"n_estimators": 300, "max_depth": 8, "min_samples_leaf": 5}
TRANSF_RIDGE = "sqrt"        # melhor transformação p/ Ridge (M2)
TRANSF_RF = "identidade"     # melhor p/ Random Forest (M2)

N_REPETICOES_CV = 20         # repetições da CV agrupada (M6)

CORES = {"ridge": "#1565C0", "random_forest": "#2E7D32", "dummy": "#9E9E9E"}
LABELS = {"ridge": "Ridge", "random_forest": "Random Forest", "dummy": "Dummy (média)"}

LABELS_MESO = {
    2601: "São Francisco",
    2602: "Sertão",
    2603: "Agreste",
    2604: "Mata",
    2605: "Metropolitana",
}


def sep(titulo: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {titulo}")
    print("=" * 70)


def salvar_figura(fig: plt.Figure, nome: str) -> None:
    caminho = FIGURAS_DIR / nome
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Figura salva: %s", caminho)


def criar_modelos_vencedores(X: pd.DataFrame) -> dict:
    """Reconstrói os baselines com os hiperparâmetros vencedores do notebook 06."""
    ridge = criar_pipeline(X, Ridge(random_state=RANDOM_STATE, **PARAMS_RIDGE))
    rf = criar_pipeline(X, RandomForestRegressor(
        random_state=RANDOM_STATE, n_jobs=-1, **PARAMS_RF))
    return {
        "ridge": aplicar_transformacao_target(ridge, TRANSF_RIDGE),
        "random_forest": aplicar_transformacao_target(rf, TRANSF_RF),
    }


def predicoes_temporais(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Treina os modelos vencedores no par 2022→2023 e prediz o par 2023→2024."""
    treino, teste = split_temporal(df)
    X_tr, y_tr, _ = preparar_xy(treino)
    X_te, y_te, _ = preparar_xy(teste)
    preds = {}
    for nome, modelo in criar_modelos_vencedores(X_tr).items():
        m = clone(modelo)
        m.fit(X_tr, y_tr)
        preds[nome] = m.predict(X_te)
    return teste.reset_index(drop=True), y_te.reset_index(drop=True), preds


# =============================================================================
# M5 — RANKING FLEXÍVEL: PRECISION@K E CAPTURA POR K
# =============================================================================

def analise_ranking_por_k(teste: pd.DataFrame, y_te: pd.Series, preds: dict) -> None:
    sep("M5 — RANKING FLEXÍVEL TOP-N (Precision@K e captura de críticas por K)")

    n = len(y_te)
    limiar_critico = np.percentile(y_te, 90)
    criticas = set(np.flatnonzero(y_te.values >= limiar_critico))
    print(f"\nTeste temporal: {n} escolas  |  limiar crítico (P90): "
          f"{limiar_critico:.1f}% de abandono  |  escolas críticas: {len(criticas)}")

    ks = [10, 20, 30, 50, 75, 100, 125, 150, 200]
    linhas = []
    for nome, y_pred in preds.items():
        for k in ks:
            top_pred = set(np.argsort(y_pred)[::-1][:k])
            linhas.append({
                "modelo": nome,
                "k": k,
                "precision_at_k": precision_at_k(y_te.values, y_pred, k),
                "captura_criticas": len(top_pred & criticas) / len(criticas),
                "aleatorio_precision": k / n,
                "aleatorio_captura": k / n,
            })
    res = pd.DataFrame(linhas)

    print(f"\n{'Modelo':<16}{'K':>6}{'P@K':>8}{'Captura críticas':>18}{'Aleatório':>11}")
    print("-" * 60)
    for _, r in res.iterrows():
        print(f"  {r['modelo']:<14}{r['k']:>6.0f}{r['precision_at_k']:>8.2f}"
              f"{r['captura_criticas']:>18.2f}{r['aleatorio_precision']:>11.2f}")

    # Leitura gerencial: quantas escolas críticas a Secretaria alcança intervindo em K?
    for nome in preds:
        r50 = res[(res["modelo"] == nome) & (res["k"] == 50)].iloc[0]
        print(f"\n  Intervindo nas top-50 indicadas pelo {LABELS[nome]}: "
              f"alcança {r50['captura_criticas']*100:.0f}% das escolas críticas "
              f"(aleatório: {r50['aleatorio_captura']*100:.0f}%).")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, metrica, titulo in zip(
        axes,
        ["precision_at_k", "captura_criticas"],
        ["Precision@K (sobreposição dos top-K)",
         f"Captura de escolas críticas (abandono ≥ {limiar_critico:.1f}%)"],
    ):
        for nome in preds:
            sub = res[res["modelo"] == nome]
            ax.plot(sub["k"], sub[metrica], "o-", color=CORES[nome],
                    lw=2, ms=5, label=LABELS[nome])
        sub0 = res[res["modelo"] == "ridge"]
        ax.plot(sub0["k"], sub0["aleatorio_precision"], "--", color="#9E9E9E",
                lw=1.5, label="Seleção aleatória")
        ax.set_xlabel("K (nº de escolas priorizadas)")
        ax.set_ylabel(titulo.split(" (")[0])
        ax.set_title(titulo)
        ax.set_ylim(0, 1)
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3)
    fig.suptitle("M5 — Ranking flexível: desempenho por tamanho da lista de priorização "
                 "(teste temporal 2023→2024)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "M5_precision_por_k.png")


# =============================================================================
# M6 — ERRO PADRÃO DAS MÉTRICAS VIA CV REPETIDA
# =============================================================================

def analise_cv_repetida(df: pd.DataFrame) -> None:
    sep(f"M6 — ESTABILIDADE DAS MÉTRICAS ({N_REPETICOES_CV} repetições de CV agrupada)")

    X, y, grupos = preparar_xy(df)
    modelos = criar_modelos_vencedores(X)

    # GroupShuffleSplit: a cada repetição, 20% dos municípios vão para teste.
    # Repetir com seeds distintas gera a distribuição amostral das métricas
    # (a "análise de Monte Carlo" prevista no roadmap para robustez).
    gss = GroupShuffleSplit(n_splits=N_REPETICOES_CV, test_size=0.2,
                            random_state=RANDOM_STATE)
    linhas = []
    for rep, (idx_tr, idx_te) in enumerate(gss.split(X, y, groups=grupos), start=1):
        for nome, modelo in modelos.items():
            m = clone(modelo)
            m.fit(X.iloc[idx_tr], y.iloc[idx_tr])
            y_pred = m.predict(X.iloc[idx_te])
            met = calcular_metricas(y.iloc[idx_te], y_pred)
            linhas.append({"repeticao": rep, "modelo": nome, **met})
        # piso trivial
        media_tr = y.iloc[idx_tr].mean()
        met = calcular_metricas(y.iloc[idx_te], np.full(len(idx_te), media_tr))
        linhas.append({"repeticao": rep, "modelo": "dummy", **met})
    res = pd.DataFrame(linhas)
    res.to_csv(REPORTS_DIR / "metricas_cv_repetida.csv", index=False)

    print(f"\n{'Modelo':<16}{'Métrica':<16}{'Média':>8}{'DP':>8}{'EP':>8}{'IC 95%':>20}")
    print("-" * 76)
    for nome in ["dummy", "ridge", "random_forest"]:
        sub = res[res["modelo"] == nome]
        for metrica in ["rmse", "mae", "spearman", "precision_at_k"]:
            vals = sub[metrica].dropna()
            media, dp = vals.mean(), vals.std()
            ep = dp / np.sqrt(len(vals))
            ic = (media - 1.96 * ep, media + 1.96 * ep)
            print(f"  {nome:<14}{metrica:<16}{media:>8.3f}{dp:>8.3f}{ep:>8.3f}"
                  f"{f'[{ic[0]:.3f}; {ic[1]:.3f}]':>20}")

    # Sobreposição dos ICs entre Ridge e RF (há diferença significativa?)
    print("\nComparação Ridge × Random Forest (diferença por repetição pareada):")
    for metrica in ["rmse", "spearman"]:
        ridge = res[res["modelo"] == "ridge"].set_index("repeticao")[metrica]
        rf = res[res["modelo"] == "random_forest"].set_index("repeticao")[metrica]
        dif = (rf - ridge).dropna()
        ep = dif.std() / np.sqrt(len(dif))
        print(f"  {metrica}: RF − Ridge = {dif.mean():+.3f} ± {1.96*ep:.3f} (IC 95%)")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    ordem = ["dummy", "ridge", "random_forest"]
    for ax, metrica, titulo in zip(
        axes, ["rmse", "spearman", "precision_at_k"],
        ["RMSE (p.p.)", "Spearman", "Precision@K (10%)"],
    ):
        dados, labels_plot, cores_plot = [], [], []
        for nome in ordem:
            vals = res[res["modelo"] == nome][metrica].dropna()
            if len(vals) > 0:
                dados.append(vals)
                labels_plot.append(LABELS[nome])
                cores_plot.append(CORES[nome])
        bp = ax.boxplot(dados, tick_labels=labels_plot, patch_artist=True,
                        medianprops=dict(color="black", lw=2))
        for patch, cor in zip(bp["boxes"], cores_plot):
            patch.set_facecolor(cor)
            patch.set_alpha(0.75)
        ax.set_title(f"{titulo} — {N_REPETICOES_CV} repetições")
        ax.tick_params(axis="x", rotation=10)
        ax.grid(axis="y", alpha=0.3)
    fig.suptitle("M6 — Distribuição amostral das métricas (CV agrupada repetida, "
                 "20% dos municípios em teste)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "M6_cv_repetida.png")


# =============================================================================
# M7 — AVALIAÇÃO BINARIZADA PÓS-HOC
# =============================================================================

def analise_binarizada(teste: pd.DataFrame, y_te: pd.Series, preds: dict) -> None:
    sep("M7 — AVALIAÇÃO BINARIZADA PÓS-HOC (comparação com a literatura)")

    limiar = np.percentile(y_te, 90)
    y_bin = (y_te.values >= limiar).astype(int)
    prevalencia = y_bin.mean()
    print(f"\nDefinição de alto risco: abandono 2024 ≥ P90 = {limiar:.1f}% "
          f"({y_bin.sum()} escolas, prevalência {prevalencia*100:.1f}%)")
    print("Os scores são as predições contínuas da regressão — sem retreinar.")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    print(f"\n{'Modelo':<16}{'ROC-AUC':>10}{'PR-AUC':>10}{'PR-AUC/prevalência':>20}")
    print("-" * 58)
    for nome, y_pred in preds.items():
        roc_auc = roc_auc_score(y_bin, y_pred)
        prec, rec, _ = precision_recall_curve(y_bin, y_pred)
        pr_auc = auc(rec, prec)
        print(f"  {nome:<14}{roc_auc:>10.3f}{pr_auc:>10.3f}{pr_auc/prevalencia:>20.1f}x")

        fpr, tpr, _ = roc_curve(y_bin, y_pred)
        axes[0].plot(fpr, tpr, color=CORES[nome], lw=2,
                     label=f"{LABELS[nome]} (AUC={roc_auc:.3f})")
        axes[1].plot(rec, prec, color=CORES[nome], lw=2,
                     label=f"{LABELS[nome]} (PR-AUC={pr_auc:.3f})")

    axes[0].plot([0, 1], [0, 1], "--", color="#9E9E9E", lw=1.5, label="Aleatório (AUC=0,5)")
    axes[0].set_xlabel("Taxa de falsos positivos")
    axes[0].set_ylabel("Taxa de verdadeiros positivos")
    axes[0].set_title("Curva ROC")
    axes[0].legend(fontsize=9)
    axes[0].grid(alpha=0.3)

    axes[1].axhline(prevalencia, ls="--", color="#9E9E9E", lw=1.5,
                    label=f"Aleatório (prevalência={prevalencia:.2f})")
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title("Curva Precision-Recall")
    axes[1].set_ylim(0, 1)
    axes[1].legend(fontsize=9)
    axes[1].grid(alpha=0.3)

    fig.suptitle(f"M7 — Avaliação binarizada pós-hoc: alto risco = abandono ≥ {limiar:.1f}% "
                 "(teste temporal 2023→2024)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "M7_avaliacao_binarizada.png")


# =============================================================================
# M8 — RESÍDUOS: TOP-20 E DISTRIBUIÇÃO POR GRUPO
# =============================================================================

def analise_residuos_grupos(teste: pd.DataFrame, y_te: pd.Series, preds: dict) -> None:
    sep("M8 — RESÍDUOS: TOP-20 PERSISTIDOS E DISTRIBUIÇÃO POR GRUPO (§8.4)")

    res = teste[["CO_ENTIDADE", "NO_ENTIDADE", "NO_MUNICIPIO", "CO_MESORREGIAO",
                 "is_rural", "is_loc_diferenciada", "taxa_abandono_t1"]].copy()
    res["predito"] = preds["ridge"]
    res["residuo"] = res["taxa_abandono_t1"] - res["predito"]
    res["mesorregiao"] = res["CO_MESORREGIAO"].map(LABELS_MESO)

    top_pos = res.nlargest(20, "residuo").assign(grupo="acima_do_esperado")
    top_neg = res.nsmallest(20, "residuo").assign(grupo="abaixo_do_esperado")
    out = pd.concat([top_pos, top_neg])
    out_path = REPORTS_DIR / "residuos_top20_temporal.csv"
    out.to_csv(out_path, index=False)
    print(f"\nTop-20 ± resíduos salvos em: {out_path}")

    print("\nTop-20 ACIMA do esperado (resíduo +) — 5 primeiras:")
    for _, r in top_pos.head(5).iterrows():
        print(f"  {r['NO_ENTIDADE'][:50]:<52} ({r['NO_MUNICIPIO']}): "
              f"real={r['taxa_abandono_t1']:.1f}%  pred={r['predito']:.1f}%")
    print("\nTop-20 ABAIXO do esperado (resíduo −) — 5 primeiras:")
    for _, r in top_neg.head(5).iterrows():
        print(f"  {r['NO_ENTIDADE'][:50]:<52} ({r['NO_MUNICIPIO']}): "
              f"real={r['taxa_abandono_t1']:.1f}%  pred={r['predito']:.1f}%")

    print("\nResíduo médio por grupo (viés sistemático do modelo?):")
    for col, labels in [("mesorregiao", None),
                        ("is_rural", {0: "Urbana", 1: "Rural"}),
                        ("is_loc_diferenciada", {0: "Comum", 1: "Diferenciada*"})]:
        print(f"\n  Por {col}:")
        for valor, sub in res.groupby(col):
            label = labels.get(valor, valor) if labels else valor
            print(f"    {str(label):<16}: resíduo médio={sub['residuo'].mean():+.2f} p.p.  "
                  f"(n={len(sub)})")
    print("\n  * Localização diferenciada inclui terras indígenas e quilombolas.")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    ordem_meso = [LABELS_MESO[c] for c in sorted(LABELS_MESO)]
    dados = [res[res["mesorregiao"] == m]["residuo"] for m in ordem_meso]
    bp = ax.boxplot(dados, tick_labels=ordem_meso, patch_artist=True,
                    medianprops=dict(color="black", lw=2))
    for patch in bp["boxes"]:
        patch.set_facecolor("#6A1B9A")
        patch.set_alpha(0.7)
    ax.axhline(0, color="black", lw=1)
    ax.set_ylabel("Resíduo (real − predito, p.p.)")
    ax.set_title("Resíduo por mesorregião")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.3)

    ax = axes[1]
    grupos_plot = [
        ("Urbana", res[res["is_rural"] == 0]["residuo"]),
        ("Rural", res[res["is_rural"] == 1]["residuo"]),
        ("Loc. comum", res[res["is_loc_diferenciada"] == 0]["residuo"]),
        ("Loc. diferenciada", res[res["is_loc_diferenciada"] == 1]["residuo"]),
    ]
    bp = ax.boxplot([g[1] for g in grupos_plot],
                    tick_labels=[g[0] for g in grupos_plot], patch_artist=True,
                    medianprops=dict(color="black", lw=2))
    for patch, cor in zip(bp["boxes"], ["#1565C0", "#2E7D32", "#1565C0", "#C62828"]):
        patch.set_facecolor(cor)
        patch.set_alpha(0.7)
    ax.axhline(0, color="black", lw=1)
    ax.set_title("Resíduo por localização")
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.3)

    fig.suptitle("M8 — Distribuição dos resíduos por grupo (Ridge, teste temporal)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "M8_residuos_grupos.png")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    df = carregar_dataset()
    teste, y_te, preds = predicoes_temporais(df)

    analise_ranking_por_k(teste, y_te, preds)
    analise_cv_repetida(df)
    analise_binarizada(teste, y_te, preds)
    analise_residuos_grupos(teste, y_te, preds)

    sep("CONCLUSÃO")
    print("""
Lacunas da metodologia agora cobertas:
  §2.1 ranking flexível top-N      → M5 (Precision@K e captura por K)
  §8.3 erro padrão via repetições  → M6 (20 repetições, ICs e teste pareado)
  §2.1 análise binarizada pós-hoc  → M7 (ROC-AUC e PR-AUC sem retreinar)
  §8.4 top-20 resíduos             → M8 (CSV persistido + viés por grupo)
""")
    print("Figuras salvas em:", FIGURAS_DIR)


if __name__ == "__main__":
    main()
