"""
Feature Engineering — análise do dataset final para modelagem.
Escolas estaduais de EM em PE — features de 2022 e 2023, target 2023 e 2024.

Responde às perguntas:
  F1. Qual o perfil e cobertura do dataset final?
  F2. Como se distribui o target (taxa_abandono_t1)?
  F3. Qual a qualidade das features (missing, variância)?
  F4. Quais features mais se correlacionam com o target?
  F5. Há multicolinearidade entre features?
  F6. Qual a importância preliminar das features (XGBoost)?

Saídas:
  - Texto no console
  - Figuras salvas em: reports/figuras/  (prefixo F*)
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
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import config
from src.features.build_features import ID_COLS, _colunas_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

FEATURES_PATH = config.PROCESSED_DIR / "features.parquet"
FIGURAS_DIR   = ROOT / "reports" / "figuras"
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)

ANOS  = [2022, 2023]
CORES_ANOS = {2022: "#2196F3", 2023: "#FF9800"}
COR_PRINCIPAL = "#1565C0"

LABELS_MESO = {
    2601: "São Francisco",
    2602: "Sertão",
    2603: "Agreste",
    2604: "Mata",
    2605: "Metropolitana",
}

# Grupos de features para análise temática
GRUPOS_FEATURES = {
    "Localização / Porte": [
        "is_rural", "is_loc_diferenciada", "CO_MESORREGIAO",
        "QT_MAT_MED", "log_mat_med",
    ],
    "Operacional": [
        "alunos_por_turma", "alunos_por_docente",
        "computadores_por_aluno", "pct_integral",
    ],
    "Infraestrutura": [
        "indice_infra", "IN_INTERNET_ALUNOS", "IN_BANDA_LARGA",
        "IN_LABORATORIO_INFORMATICA", "IN_QUADRA_ESPORTES",
        "IN_BIBLIOTECA", "IN_LABORATORIO_CIENCIAS",
    ],
    "Indicadores (t)": [
        "inse_media", "tdi_med_t", "afd_g1_t", "afd_g5_t", "ird_med_t",
    ],
    "Taxas lag (t)": [
        "abnd_t", "reprov_t", "abnd_s1_t", "abnd_s2_t", "abnd_s3_t",
    ],
}


# =============================================================================
# UTILITÁRIOS
# =============================================================================

def sep(titulo: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {titulo}")
    print("=" * 70)


def salvar_figura(fig: plt.Figure, nome: str) -> None:
    caminho = FIGURAS_DIR / nome
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Figura salva: %s", caminho)


def carregar() -> pd.DataFrame:
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Dataset não encontrado: {FEATURES_PATH}\n"
            "Execute: python -m src.features.build_features"
        )
    df = pd.read_parquet(FEATURES_PATH)
    df["NU_ANO_CENSO"] = df["NU_ANO_CENSO"].astype(int)
    logger.info("Dataset carregado: %d linhas × %d colunas.", *df.shape)
    return df


def feature_cols(df: pd.DataFrame) -> list[str]:
    excluir = set(ID_COLS + ["taxa_abandono_t1"])
    return [c for c in df.columns if c not in excluir]


# =============================================================================
# F1 — PERFIL E COBERTURA DO DATASET
# =============================================================================

def analise_perfil(df: pd.DataFrame) -> None:
    sep("F1 — PERFIL E COBERTURA DO DATASET FINAL")

    fcols = feature_cols(df)
    print(f"\nShape: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
    print(f"Features: {len(fcols)}  |  IDs: {len(ID_COLS)}  |  Target: 1")
    print(f"Escolas únicas: {df['CO_ENTIDADE'].nunique():,}")
    print(f"Anos feature: {sorted(df['NU_ANO_CENSO'].unique())}")

    print("\nDistribuição por ano-feature:")
    for ano in ANOS:
        sub = df[df["NU_ANO_CENSO"] == ano]
        urb = (sub["is_rural"] == 0).sum()
        rur = (sub["is_rural"] == 1).sum()
        print(f"  {ano}: {len(sub):,} linhas  |  Urbana: {urb:,}  Rural: {rur:,}")

    print("\nDistribuição por mesorregião (2022 + 2023 combinados):")
    meso = df["CO_MESORREGIAO"].value_counts().sort_index()
    for cod, n in meso.items():
        label = LABELS_MESO.get(cod, str(cod))
        print(f"  {label} ({cod}): {n:,} ({n/len(df)*100:.1f}%)")

    print("\nEscolas com dados nos 2 anos:")
    por_escola = df.groupby("CO_ENTIDADE")["NU_ANO_CENSO"].nunique()
    print(f"  2 anos: {(por_escola == 2).sum():,} ({(por_escola==2).mean()*100:.1f}%)")
    print(f"  1 ano:  {(por_escola == 1).sum():,} ({(por_escola==1).mean()*100:.1f}%)")

    # Figura F1 — composição do dataset
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    # Barras por ano com split urbana/rural
    ax = axes[0]
    for i, ano in enumerate(ANOS):
        sub = df[df["NU_ANO_CENSO"] == ano]
        urb = (sub["is_rural"] == 0).sum()
        rur = (sub["is_rural"] == 1).sum()
        ax.bar(i - 0.2, urb, 0.35, color="#1565C0", alpha=0.8, label="Urbana" if i == 0 else "")
        ax.bar(i + 0.2, rur, 0.35, color="#2E7D32", alpha=0.8, label="Rural"  if i == 0 else "")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(ANOS)
    ax.set_ylabel("N observações")
    ax.set_title("Observações por ano")
    ax.legend()

    # Barras por mesorregião
    ax = axes[1]
    labels_m = [LABELS_MESO.get(c, str(c)) for c in meso.index]
    bars = ax.bar(labels_m, meso.values, color=COR_PRINCIPAL, alpha=0.8, edgecolor="white")
    for bar, val in zip(bars, meso.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                str(val), ha="center", fontsize=8)
    ax.set_ylabel("N observações")
    ax.set_title("Por mesorregião")
    ax.tick_params(axis="x", rotation=20)

    # Histograma do target
    ax = axes[2]
    ax.hist(df["taxa_abandono_t1"], bins=40, color="#C62828", edgecolor="white", alpha=0.85)
    ax.axvline(df["taxa_abandono_t1"].median(), color="black", lw=1.5, ls="--",
               label=f"Mediana={df['taxa_abandono_t1'].median():.1f}%")
    ax.set_xlabel("taxa_abandono_t1 (%)"); ax.set_ylabel("N escolas")
    ax.set_title("Distribuição do target")
    ax.legend(fontsize=9)

    fig.suptitle("F1 — Perfil do dataset final", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F1_perfil_dataset.png")


# =============================================================================
# F2 — DISTRIBUIÇÃO DO TARGET
# =============================================================================

def analise_target(df: pd.DataFrame) -> None:
    sep("F2 — DISTRIBUIÇÃO DO TARGET (taxa_abandono_t1)")

    y = df["taxa_abandono_t1"]
    print(f"\nN: {len(y):,}  |  Média: {y.mean():.2f}%  |  Mediana: {y.median():.2f}%")
    print(f"DP: {y.std():.2f}  |  Mín: {y.min():.1f}%  |  Máx: {y.max():.1f}%")
    print(f"Skewness: {y.skew():.2f}  |  Kurtosis: {y.kurtosis():.2f}")

    percentis = [50, 75, 90, 95, 99]
    print("\nPercentis:")
    for p in percentis:
        print(f"  P{p:2d}: {np.percentile(y, p):.1f}%")

    print("\nDistribuição por faixa:")
    faixas = [(0, 0), (0, 2), (2, 5), (5, 10), (10, 100)]
    labels_f = ["= 0%", "0–2%", "2–5%", "5–10%", "> 10%"]
    for (lo, hi), lbl in zip(faixas, labels_f):
        if lo == hi == 0:
            n = (y == 0).sum()
        else:
            n = ((y > lo) & (y <= hi)).sum()
        print(f"  {lbl}: {n:,} ({n/len(y)*100:.1f}%)")

    print("\nPor ano-feature:")
    for ano in ANOS:
        sub = df[df["NU_ANO_CENSO"] == ano]["taxa_abandono_t1"]
        print(f"  {ano} → {ano+1}: média={sub.mean():.2f}%  mediana={sub.median():.2f}%  "
              f"P90={np.percentile(sub,90):.1f}%")

    # Figura F2 — distribuições detalhadas
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Histograma escala completa + log
    ax = axes[0]
    ax.hist(y, bins=50, color="#C62828", edgecolor="white", alpha=0.85)
    ax.set_xlabel("Taxa de abandono t+1 (%)"); ax.set_ylabel("N escolas")
    ax.set_title("Distribuição completa")
    ax2 = ax.twinx()
    ax2.hist(y, bins=50, color="#C62828", alpha=0, edgecolor="none")

    # Zoom 0–15%
    ax = axes[1]
    ax.hist(y[y <= 15], bins=40, color="#E53935", edgecolor="white", alpha=0.85)
    ax.set_xlabel("Taxa de abandono t+1 (%)"); ax.set_ylabel("N escolas")
    ax.set_title("Zoom: abandono ≤ 15%")

    # Boxplot por ano
    ax = axes[2]
    data_plot = [df[df["NU_ANO_CENSO"] == a]["taxa_abandono_t1"] for a in ANOS]
    labels_anos = [f"{a}→{a+1}" for a in ANOS]
    bp = ax.boxplot(data_plot, tick_labels=labels_anos, patch_artist=True,
                    medianprops=dict(color="black", lw=2))
    for patch, ano in zip(bp["boxes"], ANOS):
        patch.set_facecolor(CORES_ANOS[ano]); patch.set_alpha(0.7)
    ax.set_ylabel("Taxa de abandono t+1 (%)"); ax.set_title("Target por par ano")

    fig.suptitle("F2 — Distribuição do target (taxa_abandono_t1)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F2_target.png")


# =============================================================================
# F3 — QUALIDADE DAS FEATURES
# =============================================================================

def analise_qualidade(df: pd.DataFrame) -> None:
    sep("F3 — QUALIDADE DAS FEATURES (missing, variância zero)")

    fcols = feature_cols(df)

    miss = (df[fcols].isnull().mean() * 100).sort_values(ascending=False)
    variancia = df[fcols].var()
    baixa_var = variancia[variancia < 0.001].index.tolist()

    print(f"\nFeatures com missing > 0%: {(miss > 0).sum()}")
    if (miss > 0).any():
        print(miss[miss > 0].round(2).to_string())
    else:
        print("  Nenhuma — imputação completa.")

    print(f"\nFeatures com variância ≈ 0: {len(baixa_var)}")
    for c in baixa_var:
        print(f"  {c}: var={variancia[c]:.6f}  unique={df[c].nunique()}")

    # Estatísticas por grupo
    print("\nEstatísticas por grupo de features:")
    for grupo, cols in GRUPOS_FEATURES.items():
        cols_pres = [c for c in cols if c in df.columns]
        if not cols_pres:
            continue
        print(f"\n  [{grupo}]")
        for c in cols_pres:
            vals = df[c].dropna()
            if vals.dtype in [np.float64, np.float32]:
                print(f"    {c:<30}: média={vals.mean():7.2f}  DP={vals.std():6.2f}  "
                      f"[{vals.min():.1f} ; {vals.max():.1f}]")
            else:
                print(f"    {c:<30}: {vals.value_counts().to_dict()}")

    # Figura F3 — variância das features numéricas
    num_cols = [c for c in fcols if df[c].dtype in [np.float64, np.float32, float]]
    var_sorted = variancia[num_cols].sort_values(ascending=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    colors = ["#C62828" if v < 1 else "#1565C0" for v in var_sorted.values]
    ax.barh(range(len(var_sorted)), var_sorted.values, color=colors, alpha=0.8)
    ax.set_yticks(range(len(var_sorted)))
    ax.set_yticklabels(var_sorted.index, fontsize=7)
    ax.set_xlabel("Variância"); ax.set_title("Variância por feature (vermelhas < 1)")
    ax.axvline(1, color="red", lw=1, ls="--", alpha=0.5)

    # Missings (deve ser zero)
    ax = axes[1]
    if (miss > 0).any():
        miss_plot = miss[miss > 0]
        ax.barh(miss_plot.index, miss_plot.values, color="#FB8C00", alpha=0.8)
        ax.set_xlabel("% Missing"); ax.set_title("Features com missing (pós-imputação)")
    else:
        ax.text(0.5, 0.5, "Zero missing após imputação", ha="center", va="center",
                fontsize=14, color="#2E7D32", transform=ax.transAxes)
        ax.set_title("Missing values")
        ax.axis("off")

    fig.suptitle("F3 — Qualidade das features", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F3_qualidade_features.png")


# =============================================================================
# F4 — CORRELAÇÕES COM O TARGET
# =============================================================================

def analise_correlacoes_target(df: pd.DataFrame) -> None:
    sep("F4 — CORRELAÇÕES DAS FEATURES COM O TARGET (Spearman)")

    fcols = feature_cols(df)
    y = df["taxa_abandono_t1"]

    resultados = {}
    for col in fcols:
        par = df[[col, "taxa_abandono_t1"]].dropna()
        if len(par) < 30 or par[col].nunique() < 3:
            continue
        r, p = stats.spearmanr(par[col], par["taxa_abandono_t1"])
        resultados[col] = (r, p)

    sorted_r = sorted(resultados.items(), key=lambda x: abs(x[1][0]), reverse=True)

    print(f"\n{'Feature':<30} {'r Spearman':>12}  {'p-valor':>10}  Sig")
    print("-" * 65)
    for col, (r, p) in sorted_r:
        sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
        print(f"  {col:<28} {r:>+.3f}       {p:>10.4f}  {sig}")

    top_pos = [(c, r) for c, (r, p) in sorted_r if r > 0][:5]
    top_neg = [(c, r) for c, (r, p) in sorted_r if r < 0][:5]
    print(f"\nTop 5 correlações POSITIVAS (mais abandono):")
    for c, r in top_pos:
        print(f"  {c}: r={r:+.3f}")
    print(f"\nTop 5 correlações NEGATIVAS (menos abandono):")
    for c, r in top_neg:
        print(f"  {c}: r={r:+.3f}")

    # Figura F4 — barras de correlação + top scatters
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Barras de correlação (top 20 por |r|)
    ax = axes[0]
    top20 = sorted_r[:20]
    nomes = [c for c, _ in top20]
    valores = [r for _, (r, _) in top20]
    cores = ["#C62828" if v > 0 else "#1565C0" for v in valores]
    ax.barh(nomes[::-1], valores[::-1], color=cores[::-1], alpha=0.85, edgecolor="white")
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("r de Spearman")
    ax.set_title("Top 20 correlações com abandono t+1")
    ax.tick_params(axis="y", labelsize=8)

    # Scatter das 2 mais correlacionadas
    ax = axes[1]
    if top_pos:
        col_top = top_pos[0][0]
        par = df[[col_top, "taxa_abandono_t1"]].dropna()
        ax.scatter(par[col_top], par["taxa_abandono_t1"],
                   alpha=0.25, s=12, color="#C62828")
        m, b = np.polyfit(par[col_top], par["taxa_abandono_t1"], 1)
        x_line = np.linspace(par[col_top].min(), par[col_top].max(), 100)
        ax.plot(x_line, m * x_line + b, color="black", lw=1.5)
        r, _ = stats.spearmanr(par[col_top], par["taxa_abandono_t1"])
        ax.set_xlabel(col_top); ax.set_ylabel("Taxa abandono t+1 (%)")
        ax.set_title(f"Feature mais correlacionada: {col_top}\nr Spearman = {r:+.3f}")

    fig.suptitle("F4 — Correlações features × target", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F4_correlacoes_target.png")

    return resultados


# =============================================================================
# F5 — MULTICOLINEARIDADE ENTRE FEATURES
# =============================================================================

def analise_multicolinearidade(df: pd.DataFrame) -> None:
    sep("F5 — MULTICOLINEARIDADE ENTRE FEATURES")

    fcols = feature_cols(df)
    num_cols = [c for c in fcols
                if df[c].dtype in [np.float64, np.float32, float, int, np.int64]
                and df[c].nunique() > 5]

    corr = df[num_cols].corr(method="spearman")

    # Pares com |r| > 0.8
    print("\nPares de features com |r Spearman| > 0.80 (risco de multicolinearidade):")
    altos = []
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            r = corr.iloc[i, j]
            if abs(r) > 0.80:
                altos.append((corr.columns[i], corr.columns[j], r))
    altos.sort(key=lambda x: abs(x[2]), reverse=True)
    if altos:
        for c1, c2, r in altos:
            print(f"  {c1} × {c2}: r={r:+.3f}")
    else:
        print("  Nenhum par com |r| > 0.80")

    print("\nPares com |r| > 0.70:")
    medio = [(c1, c2, r) for c1, c2, r in [
        (corr.columns[i], corr.columns[j], corr.iloc[i, j])
        for i in range(len(corr.columns))
        for j in range(i + 1, len(corr.columns))
    ] if abs(r) > 0.70 and abs(r) <= 0.80]
    if medio:
        for c1, c2, r in sorted(medio, key=lambda x: abs(x[2]), reverse=True)[:10]:
            print(f"  {c1} × {c2}: r={r:+.3f}")

    # Figura F5 — heatmap
    # Usa apenas features temáticas relevantes para não sobrecarregar o gráfico
    cols_heatmap = []
    for grupo, cols in GRUPOS_FEATURES.items():
        cols_heatmap += [c for c in cols if c in num_cols]
    cols_heatmap = list(dict.fromkeys(cols_heatmap))  # deduplica mantendo ordem

    corr_sub = df[cols_heatmap].corr(method="spearman")

    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr_sub, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, label="r Spearman")
    ax.set_xticks(range(len(cols_heatmap)))
    ax.set_yticks(range(len(cols_heatmap)))
    ax.set_xticklabels(cols_heatmap, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(cols_heatmap, fontsize=7)
    for i in range(len(cols_heatmap)):
        for j in range(len(cols_heatmap)):
            val = corr_sub.iloc[i, j]
            if abs(val) > 0.3:
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=5, color="white" if abs(val) > 0.6 else "black")
    ax.set_title("F5 — Matriz de correlação Spearman entre features", fontsize=12)
    fig.tight_layout()
    salvar_figura(fig, "F5_multicolinearidade.png")


# =============================================================================
# F6 — FEATURE IMPORTANCE PRELIMINAR (XGBoost)
# =============================================================================

def analise_importancia_xgboost(df: pd.DataFrame) -> None:
    sep("F6 — FEATURE IMPORTANCE PRELIMINAR (XGBoost)")

    try:
        import xgboost as xgb
    except ImportError:
        print("XGBoost não instalado. Pulando análise F6.")
        return

    fcols = feature_cols(df)
    # Remove features com variância zero ou quasi-zero
    fcols = [c for c in fcols if df[c].nunique() > 2 or df[c].dtype == float]
    # Remove colunas não numéricas
    fcols = [c for c in fcols if df[c].dtype in [np.float64, np.float32, float, int, np.int64]]

    X = df[fcols].fillna(df[fcols].median())
    y = df["taxa_abandono_t1"]

    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X, y)

    importancias = pd.Series(model.feature_importances_, index=fcols).sort_values(ascending=False)

    print(f"\nTop 20 features mais importantes (XGBoost — gain):")
    for feat, imp in importancias.head(20).items():
        bar = "█" * int(imp * 200)
        print(f"  {feat:<30}: {imp:.4f}  {bar}")

    print(f"\nFeatures com importância ≈ 0 (candidatas ao descarte):")
    zero = importancias[importancias < 0.001]
    print(f"  {list(zero.index)}")

    # Score preliminar
    from sklearn.model_selection import cross_val_score
    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    print(f"\nR² em cross-validation (5-fold): {scores.mean():.3f} ± {scores.std():.3f}")

    rmse_scores = cross_val_score(model, X, y, cv=5,
                                  scoring="neg_root_mean_squared_error")
    print(f"RMSE em cross-validation (5-fold): {-rmse_scores.mean():.3f} ± {rmse_scores.std():.3f}")

    # Figura F6
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Barras de importância (top 25)
    ax = axes[0]
    top25 = importancias.head(25)
    cores = ["#1B5E20" if v > 0.05 else "#43A047" if v > 0.02 else "#A5D6A7"
             for v in top25.values]
    ax.barh(top25.index[::-1], top25.values[::-1], color=cores[::-1], edgecolor="white")
    ax.set_xlabel("Importância (gain)"); ax.set_title("Top 25 features — XGBoost")
    ax.tick_params(axis="y", labelsize=8)
    ax.axvline(0.02, color="orange", lw=1, ls="--", alpha=0.7, label="Limiar 0.02")
    ax.legend(fontsize=9)

    # Importância acumulada
    ax = axes[1]
    imp_cum = importancias.cumsum() / importancias.sum() * 100
    ax.plot(range(1, len(imp_cum) + 1), imp_cum.values, "o-", color="#1565C0", lw=2, ms=4)
    ax.axhline(80, color="orange", lw=1.5, ls="--", label="80%")
    ax.axhline(95, color="red",    lw=1.5, ls="--", label="95%")
    n80 = (imp_cum <= 80).sum() + 1
    ax.axvline(n80, color="orange", lw=1, ls=":", alpha=0.7)
    ax.set_xlabel("N features (ordenadas por importância)")
    ax.set_ylabel("Importância acumulada (%)")
    ax.set_title(f"Curva de importância acumulada\n({n80} features explicam 80%)")
    ax.legend()

    fig.suptitle("F6 — Feature importance preliminar (XGBoost)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F6_feature_importance.png")

    return importancias


# =============================================================================
# SUMÁRIO
# =============================================================================

def sumario(df: pd.DataFrame, corrs: dict | None = None,
            importancias: pd.Series | None = None) -> None:
    sep("SUMÁRIO EXECUTIVO — FEATURE ENGINEERING")

    fcols = feature_cols(df)
    y = df["taxa_abandono_t1"]

    print(f"""
DATASET FINAL
  • {len(df):,} observações (escola × ano-feature)
  • {df['CO_ENTIDADE'].nunique():,} escolas únicas
  • {len(fcols)} features — 0 missing após imputação
  • Target: taxa_abandono_t1  (média={y.mean():.2f}%, mediana={y.median():.2f}%)
  • {(y == 0).mean()*100:.1f}% das observações com abandono = 0%

TARGET
  • Distribuição fortemente assimétrica à direita (skew={y.skew():.1f})
  • P90 = {np.percentile(y, 90):.1f}%  |  P95 = {np.percentile(y, 95):.1f}%
  • XGBoost nativo lida bem com assimetria — não exige transformação log

FEATURES MAIS IMPORTANTES (correlação com target)""")

    if corrs:
        top5 = sorted(corrs.items(), key=lambda x: abs(x[1][0]), reverse=True)[:5]
        for c, (r, p) in top5:
            print(f"  {c}: r={r:+.3f}")

    print("""
IMPUTAÇÕES REALIZADAS
  • IN_BANDA_LARGA (0,8%): modal por mesorregião×ano
  • INSE (5,2% das escolas): média por mesorregião
  • IRD/TDI/AFD residuais: média por mesorregião×ano

NOTAS PARA MODELAGEM
  → Treinamento: 2022 feature → 2023 target (≈800 obs)
  → Validação:   2023 feature → 2024 target (≈786 obs)
  → CO_MESORREGIAO normalizado (bug IBGE: 2022 usava 1-5, 2023 usava 2601-2605)
  → TAXA_APROV_MED excluída (colinear: aprov + reprov + abnd = 100%)
  → QT_TUR_MED e QT_DOC_MED excluídas (r > 0.85 com QT_MAT_MED)
  → IN_ENERGIA_REDE_PUBLICA excluída (constante = 1 em 100% das escolas)
""")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    df = carregar()

    analise_perfil(df)
    analise_target(df)
    analise_qualidade(df)
    corrs      = analise_correlacoes_target(df)
    analise_multicolinearidade(df)
    importancias = analise_importancia_xgboost(df)
    sumario(df, corrs, importancias)

    print("\nFiguras salvas em:", FIGURAS_DIR)


if __name__ == "__main__":
    main()
