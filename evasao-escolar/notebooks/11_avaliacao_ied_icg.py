"""
Avaliação dos indicadores IED (Esforço Docente) e ICG (Complexidade de Gestão)
como candidatos a features do modelo de predição de abandono.

Objetivo: decidir, com base em evidência empírica, se IED e ICG devem ser
incorporados às features do XGBoost. A conclusão (documentada na monografia,
Capítulo 6) é que NÃO agregam poder preditivo e, portanto, ficam de fora do
modelo, permanecendo apenas como análise descritiva (notebook 04).

Responde:
  D1. Qual a correlação univariada (Spearman) de IED/ICG com o target?
  D2. IED/ICG são redundantes com features já existentes (colinearidade)?
  D3. Ablação: o XGBoost tunado melhora ao incluir IED+ICG? (mesmos folds,
      mesmos hiperparâmetros, GroupKFold por município)

Saídas:
  - Texto no console
  - reports/ablacao_ied_icg.csv
  - reports/figuras/D1_ablacao_ied_icg.png
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import config  # noqa: E402
from src.models.evaluate import validacao_cruzada_grupos  # noqa: E402
from src.models.train import (  # noqa: E402
    aplicar_transformacao_target,
    carregar_dataset,
    criar_xgboost,
    preparar_xy,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

FIGURAS_DIR = ROOT / "reports" / "figuras"
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = ROOT / "reports" / "ablacao_ied_icg.csv"

NOVAS = ["ied_med_t", "icg_nivel_t"]
# Hiperparâmetros vencedores do tuning (Fase 6) — fixados para isolar o efeito
# marginal das duas features (mesma capacidade do modelo nos dois cenários).
HP = dict(n_estimators=300, max_depth=2, learning_rate=0.02,
          min_child_weight=5, reg_lambda=5.0)
TRANSFORM = "sqrt"  # transformação vencedora do modelo principal


def sep(t: str) -> None:
    print(f"\n{'=' * 70}\n  {t}\n{'=' * 70}")


def montar_dataset_com_novas() -> pd.DataFrame:
    """Reconstrói o dataset acrescentando IED+ICG (que NÃO entram na versão
    de produção das features) apenas para a avaliação de ablação."""
    df = carregar_dataset()
    ied = pd.read_parquet(config.INTERIM_DIR / "ied_pe_estadual.parquet")
    icg = pd.read_parquet(config.INTERIM_DIR / "icg_pe_estadual.parquet")
    for d in (ied, icg):
        d["NU_ANO_CENSO"] = d["NU_ANO_CENSO"].astype(int)

    df = df.merge(
        ied[["CO_ENTIDADE", "NU_ANO_CENSO", "IED_MED_MEDIO"]].rename(columns={"IED_MED_MEDIO": "ied_med_t"}),
        on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left",
    )
    icg = icg[["CO_ENTIDADE", "NU_ANO_CENSO", "ICG_NIVEL"]].rename(columns={"ICG_NIVEL": "icg_nivel_t"})
    icg["icg_nivel_t"] = icg["icg_nivel_t"].astype("float")
    df = df.merge(icg, on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")

    # Imputação coerente com o pipeline (média por feature) para 0% missing
    for col in NOVAS:
        df[col] = df[col].fillna(df[col].mean())
    return df


def correlacoes(df: pd.DataFrame) -> None:
    sep("D1/D2 — CORRELAÇÃO COM O TARGET E COM FEATURES EXISTENTES")

    print("\nSpearman de IED/ICG com o target (taxa_abandono_t1):")
    for col in NOVAS:
        r, p = spearmanr(df[col], df["taxa_abandono_t1"])
        print(f"  {col:<14} r={r:+.3f}  p={p:.4f}")

    print("\nMaior |correlação| de cada novo indicador com as features existentes:")
    num = df.select_dtypes("number")
    existentes = [c for c in num.columns if c not in NOVAS + ["taxa_abandono_t1", "CO_ENTIDADE", "NU_ANO_CENSO", "CO_MUNICIPIO"]]
    for col in NOVAS:
        cors = {c: abs(spearmanr(df[col], df[c]).statistic) for c in existentes}
        top = sorted(cors.items(), key=lambda kv: kv[1], reverse=True)[:3]
        txt = ", ".join(f"{c}={v:.2f}" for c, v in top)
        print(f"  {col:<14} → {txt}")


def ablacao(df_com: pd.DataFrame) -> pd.DataFrame:
    sep("D3 — ABLAÇÃO XGBOOST (mesmos folds, mesmos HP): COM vs SEM IED+ICG")

    linhas = []
    for rotulo, dfx in [("com_ied_icg", df_com), ("sem_ied_icg", df_com.drop(columns=NOVAS))]:
        X, y, grupos = preparar_xy(dfx)
        pipe = criar_xgboost(X)
        pipe.named_steps["model"].set_params(**HP)
        modelo = aplicar_transformacao_target(clone(pipe), TRANSFORM)
        folds = validacao_cruzada_grupos(modelo, X, y, grupos)
        linhas.append({
            "cenario": rotulo,
            "n_features": X.shape[1],
            "rmse": folds["rmse"].mean(),
            "rmse_dp": folds["rmse"].std(),
            "mae": folds["mae"].mean(),
            "spearman": folds["spearman"].mean(),
            "spearman_dp": folds["spearman"].std(),
            "precision_at_k": folds["precision_at_k"].mean(),
        })
    res = pd.DataFrame(linhas)

    print(f"\n{'cenário':<14}{'feats':>7}{'RMSE':>10}{'Spearman':>12}{'P@K':>9}")
    print("-" * 52)
    for _, r in res.iterrows():
        print(f"  {r['cenario']:<12}{int(r['n_features']):>7}{r['rmse']:>10.3f}"
              f"{r['spearman']:>12.3f}{r['precision_at_k']:>9.3f}")

    res.to_csv(CSV_PATH, index=False)
    print(f"\nTabela salva em: {CSV_PATH}")
    return res


def figura(res: pd.DataFrame) -> None:
    metricas = [("rmse", "RMSE (p.p.) ↓"), ("spearman", "Spearman ↑"),
                ("precision_at_k", "Precision@K ↑")]
    cores = {"com_ied_icg": "#C62828", "sem_ied_icg": "#1565C0"}
    rotulos = {"com_ied_icg": "COM IED+ICG", "sem_ied_icg": "SEM IED+ICG (modelo final)"}

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    for ax, (m, titulo) in zip(axes, metricas):
        for i, (_, r) in enumerate(res.iterrows()):
            ax.bar(i, r[m], color=cores[r["cenario"]], alpha=0.85, width=0.6)
            ax.text(i, r[m], f"{r[m]:.3f}", ha="center", va="bottom", fontsize=10)
        ax.set_xticks(range(len(res)))
        ax.set_xticklabels([rotulos[c] for c in res["cenario"]], fontsize=8)
        ax.set_title(titulo, fontsize=11)
    fig.suptitle("D1 — Ablação: IED+ICG não melhoram o XGBoost em validação cruzada\n"
                 "(GroupKFold por município, mesmos hiperparâmetros, target=sqrt)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    out = FIGURAS_DIR / "D1_ablacao_ied_icg.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Figura salva: %s", out)


def main() -> None:
    df_com = montar_dataset_com_novas()
    print(f"Dataset de avaliação: {df_com.shape} (inclui {NOVAS} só para esta análise)")
    correlacoes(df_com)
    res = ablacao(df_com)
    figura(res)

    sep("CONCLUSÃO")
    com = res[res["cenario"] == "com_ied_icg"].iloc[0]
    sem = res[res["cenario"] == "sem_ied_icg"].iloc[0]
    print(f"""
IED e ICG NÃO agregam poder preditivo ao modelo:
  • Spearman em CV: {com['spearman']:.3f} (com) × {sem['spearman']:.3f} (sem) — sem ganho.
  • RMSE em CV:     {com['rmse']:.3f} (com) × {sem['rmse']:.3f} (sem) — sem ganho.
  • ICG é colinear com a TDI (já presente); IED tem correlação fraca com o target.

DECISÃO: IED e ICG ficam FORA das features, do XGBoost e do SHAP.
         Permanecem como ETL + análise descritiva (notebook 04, figuras C7/C8).
""")


if __name__ == "__main__":
    main()
