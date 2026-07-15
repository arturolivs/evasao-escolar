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

from comum import (
    COR_RURAL,
    COR_URBANA,
    FIGURAS_DIR,
    NOMES_CURTOS_MESORREGIOES,
    carregar_parquet,
    salvar_figura,
    sep,
)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src.data import config
from src.features.build_features import ID_COLS

FEATURES_PATH = config.PROCESSED_DIR / "features.parquet"

ANOS_FEATURE = [2022, 2023]
CORES_ANOS_FEATURE = {2022: "#2196F3", 2023: "#FF9800"}
COR_PRINCIPAL = "#1565C0"

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


def carregar() -> pd.DataFrame:
    return carregar_parquet(FEATURES_PATH, "python -m src.features.build_features")


def feature_cols(df: pd.DataFrame) -> list[str]:
    excluir = set(ID_COLS + ["taxa_abandono_t1"])
    return [c for c in df.columns if c not in excluir]


# =============================================================================
# F1 — PERFIL E COBERTURA DO DATASET
# =============================================================================

def relatorio_perfil(df: pd.DataFrame) -> None:
    fcols = feature_cols(df)
    print(f"\nShape: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
    print(f"Features: {len(fcols)}  |  IDs: {len(ID_COLS)}  |  Target: 1")
    print(f"Escolas únicas: {df['CO_ENTIDADE'].nunique():,}")
    print(f"Anos feature: {sorted(df['NU_ANO_CENSO'].unique())}")

    print("\nDistribuição por ano-feature:")
    for ano in ANOS_FEATURE:
        sub = df[df["NU_ANO_CENSO"] == ano]
        urb = (sub["is_rural"] == 0).sum()
        rur = (sub["is_rural"] == 1).sum()
        print(f"  {ano}: {len(sub):,} linhas  |  Urbana: {urb:,}  Rural: {rur:,}")

    print("\nDistribuição por mesorregião (2022 + 2023 combinados):")
    for cod, n in df["CO_MESORREGIAO"].value_counts().sort_index().items():
        label = NOMES_CURTOS_MESORREGIOES.get(cod, str(cod))
        print(f"  {label} ({cod}): {n:,} ({n/len(df)*100:.1f}%)")

    print("\nEscolas com dados nos 2 anos:")
    por_escola = df.groupby("CO_ENTIDADE")["NU_ANO_CENSO"].nunique()
    print(f"  2 anos: {(por_escola == 2).sum():,} ({(por_escola==2).mean()*100:.1f}%)")
    print(f"  1 ano:  {(por_escola == 1).sum():,} ({(por_escola==1).mean()*100:.1f}%)")


def figura_perfil(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    ax = axes[0]
    for i, ano in enumerate(ANOS_FEATURE):
        sub = df[df["NU_ANO_CENSO"] == ano]
        urb = (sub["is_rural"] == 0).sum()
        rur = (sub["is_rural"] == 1).sum()
        ax.bar(i - 0.2, urb, 0.35, color=COR_URBANA, alpha=0.8, label="Urbana" if i == 0 else "")
        ax.bar(i + 0.2, rur, 0.35, color=COR_RURAL, alpha=0.8, label="Rural" if i == 0 else "")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(ANOS_FEATURE)
    ax.set_ylabel("N observações")
    ax.set_title("Observações por ano")
    ax.legend()

    ax = axes[1]
    meso = df["CO_MESORREGIAO"].value_counts().sort_index()
    labels_meso = [NOMES_CURTOS_MESORREGIOES.get(c, str(c)) for c in meso.index]
    bars = ax.bar(labels_meso, meso.values, color=COR_PRINCIPAL, alpha=0.8, edgecolor="white")
    for bar, val in zip(bars, meso.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                str(val), ha="center", fontsize=8)
    ax.set_ylabel("N observações")
    ax.set_title("Por mesorregião")
    ax.tick_params(axis="x", rotation=20)

    ax = axes[2]
    ax.hist(df["taxa_abandono_t1"], bins=40, color="#C62828", edgecolor="white", alpha=0.85)
    ax.axvline(df["taxa_abandono_t1"].median(), color="black", lw=1.5, ls="--",
               label=f"Mediana={df['taxa_abandono_t1'].median():.1f}%")
    ax.set_xlabel("taxa_abandono_t1 (%)")
    ax.set_ylabel("N escolas")
    ax.set_title("Distribuição do target")
    ax.legend(fontsize=9)

    fig.suptitle("F1 — Perfil do dataset final", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F1_perfil_dataset.png")


def analise_perfil(df: pd.DataFrame) -> None:
    sep("F1 — PERFIL E COBERTURA DO DATASET FINAL")
    relatorio_perfil(df)
    figura_perfil(df)


# =============================================================================
# F2 — DISTRIBUIÇÃO DO TARGET
# =============================================================================

def relatorio_target(df: pd.DataFrame) -> None:
    y = df["taxa_abandono_t1"]
    print(f"\nN: {len(y):,}  |  Média: {y.mean():.2f}%  |  Mediana: {y.median():.2f}%")
    print(f"DP: {y.std():.2f}  |  Mín: {y.min():.1f}%  |  Máx: {y.max():.1f}%")
    print(f"Skewness: {y.skew():.2f}  |  Kurtosis: {y.kurtosis():.2f}")

    print("\nPercentis:")
    for p in [50, 75, 90, 95, 99]:
        print(f"  P{p:2d}: {np.percentile(y, p):.1f}%")

    print("\nDistribuição por faixa:")
    faixas = [(0, 0), (0, 2), (2, 5), (5, 10), (10, 100)]
    labels_faixa = ["= 0%", "0–2%", "2–5%", "5–10%", "> 10%"]
    for (lo, hi), lbl in zip(faixas, labels_faixa):
        if lo == hi == 0:
            n = (y == 0).sum()
        else:
            n = ((y > lo) & (y <= hi)).sum()
        print(f"  {lbl}: {n:,} ({n/len(y)*100:.1f}%)")

    print("\nPor ano-feature:")
    for ano in ANOS_FEATURE:
        sub = df[df["NU_ANO_CENSO"] == ano]["taxa_abandono_t1"]
        print(f"  {ano} → {ano+1}: média={sub.mean():.2f}%  mediana={sub.median():.2f}%  "
              f"P90={np.percentile(sub,90):.1f}%")


def figura_target(df: pd.DataFrame) -> None:
    y = df["taxa_abandono_t1"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    ax = axes[0]
    ax.hist(y, bins=50, color="#C62828", edgecolor="white", alpha=0.85)
    ax.set_xlabel("Taxa de abandono t+1 (%)")
    ax.set_ylabel("N escolas")
    ax.set_title("Distribuição completa")

    ax = axes[1]
    ax.hist(y[y <= 15], bins=40, color="#E53935", edgecolor="white", alpha=0.85)
    ax.set_xlabel("Taxa de abandono t+1 (%)")
    ax.set_ylabel("N escolas")
    ax.set_title("Zoom: abandono ≤ 15%")

    ax = axes[2]
    data_plot = [df[df["NU_ANO_CENSO"] == a]["taxa_abandono_t1"] for a in ANOS_FEATURE]
    labels_anos = [f"{a}→{a+1}" for a in ANOS_FEATURE]
    bp = ax.boxplot(data_plot, tick_labels=labels_anos, patch_artist=True,
                    medianprops=dict(color="black", lw=2))
    for patch, ano in zip(bp["boxes"], ANOS_FEATURE):
        patch.set_facecolor(CORES_ANOS_FEATURE[ano])
        patch.set_alpha(0.7)
    ax.set_ylabel("Taxa de abandono t+1 (%)")
    ax.set_title("Target por par ano")

    fig.suptitle("F2 — Distribuição do target (taxa_abandono_t1)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F2_target.png")


def analise_target(df: pd.DataFrame) -> None:
    sep("F2 — DISTRIBUIÇÃO DO TARGET (taxa_abandono_t1)")
    relatorio_target(df)
    figura_target(df)


# =============================================================================
# F3 — QUALIDADE DAS FEATURES
# =============================================================================

def relatorio_qualidade(df: pd.DataFrame, missing: pd.Series, variancia: pd.Series) -> None:
    print(f"\nFeatures com missing > 0%: {(missing > 0).sum()}")
    if (missing > 0).any():
        print(missing[missing > 0].round(2).to_string())
    else:
        print("  Nenhuma — imputação completa.")

    baixa_var = variancia[variancia < 0.001].index.tolist()
    print(f"\nFeatures com variância ≈ 0: {len(baixa_var)}")
    for c in baixa_var:
        print(f"  {c}: var={variancia[c]:.6f}  unique={df[c].nunique()}")

    print("\nEstatísticas por grupo de features:")
    for grupo, cols in GRUPOS_FEATURES.items():
        cols_presentes = [c for c in cols if c in df.columns]
        if not cols_presentes:
            continue
        print(f"\n  [{grupo}]")
        for c in cols_presentes:
            vals = df[c].dropna()
            if vals.dtype in [np.float64, np.float32]:
                print(f"    {c:<30}: média={vals.mean():7.2f}  DP={vals.std():6.2f}  "
                      f"[{vals.min():.1f} ; {vals.max():.1f}]")
            else:
                print(f"    {c:<30}: {vals.value_counts().to_dict()}")


def figura_qualidade(df: pd.DataFrame, missing: pd.Series, variancia: pd.Series) -> None:
    fcols = feature_cols(df)
    num_cols = [c for c in fcols if df[c].dtype in [np.float64, np.float32, float]]
    var_sorted = variancia[num_cols].sort_values(ascending=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    colors = ["#C62828" if v < 1 else "#1565C0" for v in var_sorted.values]
    ax.barh(range(len(var_sorted)), var_sorted.values, color=colors, alpha=0.8)
    ax.set_yticks(range(len(var_sorted)))
    ax.set_yticklabels(var_sorted.index, fontsize=7)
    ax.set_xlabel("Variância")
    ax.set_title("Variância por feature (vermelhas < 1)")
    ax.axvline(1, color="red", lw=1, ls="--", alpha=0.5)

    ax = axes[1]
    if (missing > 0).any():
        miss_plot = missing[missing > 0]
        ax.barh(miss_plot.index, miss_plot.values, color="#FB8C00", alpha=0.8)
        ax.set_xlabel("% Missing")
        ax.set_title("Features com missing (pós-imputação)")
    else:
        ax.text(0.5, 0.5, "Zero missing após imputação", ha="center", va="center",
                fontsize=14, color="#2E7D32", transform=ax.transAxes)
        ax.set_title("Missing values")
        ax.axis("off")

    fig.suptitle("F3 — Qualidade das features", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F3_qualidade_features.png")


def analise_qualidade(df: pd.DataFrame) -> None:
    sep("F3 — QUALIDADE DAS FEATURES (missing, variância zero)")

    fcols = feature_cols(df)
    missing = (df[fcols].isnull().mean() * 100).sort_values(ascending=False)
    variancia = df[fcols].var()

    relatorio_qualidade(df, missing, variancia)
    figura_qualidade(df, missing, variancia)


# =============================================================================
# F4 — CORRELAÇÕES COM O TARGET
# =============================================================================

def correlacoes_com_target(df: pd.DataFrame) -> dict[str, tuple[float, float]]:
    resultados = {}
    for col in feature_cols(df):
        par = df[[col, "taxa_abandono_t1"]].dropna()
        if len(par) < 30 or par[col].nunique() < 3:
            continue
        r, p = stats.spearmanr(par[col], par["taxa_abandono_t1"])
        resultados[col] = (r, p)
    return resultados


def relatorio_correlacoes_target(sorted_r: list) -> None:
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


def figura_correlacoes_target(df: pd.DataFrame, sorted_r: list) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

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

    ax = axes[1]
    top_pos = [(c, r) for c, (r, p) in sorted_r if r > 0][:5]
    if top_pos:
        col_top = top_pos[0][0]
        par = df[[col_top, "taxa_abandono_t1"]].dropna()
        ax.scatter(par[col_top], par["taxa_abandono_t1"],
                   alpha=0.25, s=12, color="#C62828")
        m, b = np.polyfit(par[col_top], par["taxa_abandono_t1"], 1)
        x_line = np.linspace(par[col_top].min(), par[col_top].max(), 100)
        ax.plot(x_line, m * x_line + b, color="black", lw=1.5)
        r, _ = stats.spearmanr(par[col_top], par["taxa_abandono_t1"])
        ax.set_xlabel(col_top)
        ax.set_ylabel("Taxa abandono t+1 (%)")
        ax.set_title(f"Feature mais correlacionada: {col_top}\nr Spearman = {r:+.3f}")

    fig.suptitle("F4 — Correlações features × target", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F4_correlacoes_target.png")


def analise_correlacoes_target(df: pd.DataFrame) -> dict:
    sep("F4 — CORRELAÇÕES DAS FEATURES COM O TARGET (Spearman)")

    resultados = correlacoes_com_target(df)
    sorted_r = sorted(resultados.items(), key=lambda x: abs(x[1][0]), reverse=True)

    relatorio_correlacoes_target(sorted_r)
    figura_correlacoes_target(df, sorted_r)
    return resultados


# =============================================================================
# F5 — MULTICOLINEARIDADE ENTRE FEATURES
# =============================================================================

def pares_correlacionados(corr: pd.DataFrame) -> list[tuple[str, str, float]]:
    pares = []
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            pares.append((corr.columns[i], corr.columns[j], corr.iloc[i, j]))
    return pares


def relatorio_multicolinearidade(corr: pd.DataFrame) -> None:
    pares = pares_correlacionados(corr)

    print("\nPares de features com |r Spearman| > 0.80 (risco de multicolinearidade):")
    altos = sorted([p for p in pares if abs(p[2]) > 0.80],
                   key=lambda x: abs(x[2]), reverse=True)
    if altos:
        for c1, c2, r in altos:
            print(f"  {c1} × {c2}: r={r:+.3f}")
    else:
        print("  Nenhum par com |r| > 0.80")

    print("\nPares com |r| > 0.70:")
    medios = [p for p in pares if 0.70 < abs(p[2]) <= 0.80]
    for c1, c2, r in sorted(medios, key=lambda x: abs(x[2]), reverse=True)[:10]:
        print(f"  {c1} × {c2}: r={r:+.3f}")


def figura_multicolinearidade(df: pd.DataFrame, num_cols: list[str]) -> None:
    cols_heatmap = []
    for cols in GRUPOS_FEATURES.values():
        cols_heatmap += [c for c in cols if c in num_cols]
    cols_heatmap = list(dict.fromkeys(cols_heatmap))

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


def analise_multicolinearidade(df: pd.DataFrame) -> None:
    sep("F5 — MULTICOLINEARIDADE ENTRE FEATURES")

    num_cols = [c for c in feature_cols(df)
                if df[c].dtype in [np.float64, np.float32, float, int, np.int64]
                and df[c].nunique() > 5]

    relatorio_multicolinearidade(df[num_cols].corr(method="spearman"))
    figura_multicolinearidade(df, num_cols)


# =============================================================================
# F6 — FEATURE IMPORTANCE PRELIMINAR (XGBoost)
# =============================================================================

def features_numericas_para_modelo(df: pd.DataFrame) -> list[str]:
    fcols = [c for c in feature_cols(df) if df[c].nunique() > 2 or df[c].dtype == float]
    return [c for c in fcols if df[c].dtype in [np.float64, np.float32, float, int, np.int64]]


def relatorio_importancias(importancias: pd.Series) -> None:
    print(f"\nTop 20 features mais importantes (XGBoost — gain):")
    for feat, imp in importancias.head(20).items():
        barra = "█" * int(imp * 200)
        print(f"  {feat:<30}: {imp:.4f}  {barra}")

    print(f"\nFeatures com importância ≈ 0 (candidatas ao descarte):")
    zero = importancias[importancias < 0.001]
    print(f"  {list(zero.index)}")


def relatorio_score_preliminar(model, X: pd.DataFrame, y: pd.Series) -> None:
    from sklearn.model_selection import cross_val_score

    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    print(f"\nR² em cross-validation (5-fold): {scores.mean():.3f} ± {scores.std():.3f}")

    rmse_scores = cross_val_score(model, X, y, cv=5,
                                  scoring="neg_root_mean_squared_error")
    print(f"RMSE em cross-validation (5-fold): {-rmse_scores.mean():.3f} ± {rmse_scores.std():.3f}")


def figura_importancias(importancias: pd.Series) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    ax = axes[0]
    top25 = importancias.head(25)
    cores = ["#1B5E20" if v > 0.05 else "#43A047" if v > 0.02 else "#A5D6A7"
             for v in top25.values]
    ax.barh(top25.index[::-1], top25.values[::-1], color=cores[::-1], edgecolor="white")
    ax.set_xlabel("Importância (gain)")
    ax.set_title("Top 25 features — XGBoost")
    ax.tick_params(axis="y", labelsize=8)
    ax.axvline(0.02, color="orange", lw=1, ls="--", alpha=0.7, label="Limiar 0.02")
    ax.legend(fontsize=9)

    ax = axes[1]
    imp_cum = importancias.cumsum() / importancias.sum() * 100
    ax.plot(range(1, len(imp_cum) + 1), imp_cum.values, "o-", color="#1565C0", lw=2, ms=4)
    ax.axhline(80, color="orange", lw=1.5, ls="--", label="80%")
    ax.axhline(95, color="red", lw=1.5, ls="--", label="95%")
    n80 = (imp_cum <= 80).sum() + 1
    ax.axvline(n80, color="orange", lw=1, ls=":", alpha=0.7)
    ax.set_xlabel("N features (ordenadas por importância)")
    ax.set_ylabel("Importância acumulada (%)")
    ax.set_title(f"Curva de importância acumulada\n({n80} features explicam 80%)")
    ax.legend()

    fig.suptitle("F6 — Feature importance preliminar (XGBoost)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "F6_feature_importance.png")


def analise_importancia_xgboost(df: pd.DataFrame) -> None:
    sep("F6 — FEATURE IMPORTANCE PRELIMINAR (XGBoost)")

    try:
        import xgboost as xgb
    except ImportError:
        print("XGBoost não instalado. Pulando análise F6.")
        return

    fcols = features_numericas_para_modelo(df)
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

    relatorio_importancias(importancias)
    relatorio_score_preliminar(model, X, y)
    figura_importancias(importancias)


# =============================================================================
# SUMÁRIO
# =============================================================================

def sumario(df: pd.DataFrame, corrs: dict | None = None) -> None:
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
    corrs = analise_correlacoes_target(df)
    analise_multicolinearidade(df)
    analise_importancia_xgboost(df)
    sumario(df, corrs)

    print("\nFiguras salvas em:", FIGURAS_DIR)


if __name__ == "__main__":
    main()
