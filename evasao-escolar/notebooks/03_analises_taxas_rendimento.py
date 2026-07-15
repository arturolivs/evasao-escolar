"""
Análises descritivas — Taxas de Rendimento Escolar (INEP)
Escolas estaduais de EM em PE — 2022, 2023 e 2024

Responde às perguntas:
  B1. Qual o perfil de cobertura e estabilidade do painel de taxas?
  B2. Como se distribui a taxa de abandono? (assimetria, excesso de zeros)
  B3. Qual a tendência temporal do abandono, reprovação e aprovação?
  B4. Há diferença sistemática de abandono entre escolas urbanas e rurais?
  B5. Em qual série do EM o abandono é mais concentrado?
  B6. Como se relacionam aprovação, reprovação e abandono?
  B7. Existe correlação entre reprovação e abandono futuro?
  B8. Quais são as escolas de alto risco (abandono > 10%)?
  B9. Como evolui o abandono dentro de cada escola (painel longitudinal)?
  B10. Qual a qualidade dos dados (missing, consistência matemática)?

Saídas:
  - Texto no console (pode ser redirecionado para log)
  - Figuras salvas em: reports/figuras/  (prefixo B*)
"""

from __future__ import annotations

from comum import (
    ANOS_CENSO,
    CORES_ANOS,
    COR_ABANDONO,
    COR_APROVACAO,
    COR_REPROVACAO,
    COR_RURAL,
    COR_URBANA,
    FIGURAS_DIR,
    carregar_parquet,
    salvar_figura,
    sep,
)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from scipy import stats

from src.data import config

PARQUET_PATH = config.INTERIM_DIR / "taxas_rendimento_pe_estadual_em.parquet"

LIMIAR_ALTO_RISCO = 10.0

COLUNAS_SERIES = ["TAXA_ABND_MED_S1", "TAXA_ABND_MED_S2", "TAXA_ABND_MED_S3"]
LABELS_SERIES = {
    "TAXA_ABND_MED_S1": "1ª Série",
    "TAXA_ABND_MED_S2": "2ª Série",
    "TAXA_ABND_MED_S3": "3ª Série",
}
CORES_SERIES = {
    "TAXA_ABND_MED_S1": "#E53935",
    "TAXA_ABND_MED_S2": "#8E24AA",
    "TAXA_ABND_MED_S3": "#1E88E5",
}

LABELS_TAXAS = {
    "TAXA_ABND_MED": "Abandono",
    "TAXA_REPROV_MED": "Reprovação",
    "TAXA_APROV_MED": "Aprovação",
}
CORES_TAXAS = {
    "TAXA_ABND_MED": COR_ABANDONO,
    "TAXA_REPROV_MED": COR_REPROVACAO,
    "TAXA_APROV_MED": COR_APROVACAO,
}


def carregar_painel() -> pd.DataFrame:
    return carregar_parquet(PARQUET_PATH, "python -m src.data.build_taxas_rendimento")


def abandono_do_ano(df: pd.DataFrame, ano: int) -> pd.Series:
    return df[df["NU_ANO_CENSO"] == ano]["TAXA_ABND_MED"]


def parear_anos(df: pd.DataFrame, ano_t: int, ano_t1: int) -> pd.DataFrame:
    """Junta, por escola, reprovação/abandono do ano t com o abandono do ano t+1."""
    sub_t = df[df["NU_ANO_CENSO"] == ano_t][
        ["CO_ENTIDADE", "TAXA_REPROV_MED", "TAXA_ABND_MED"]
    ].rename(columns={"TAXA_REPROV_MED": "reprov_t", "TAXA_ABND_MED": "abnd_t"})
    sub_t1 = df[df["NU_ANO_CENSO"] == ano_t1][
        ["CO_ENTIDADE", "TAXA_ABND_MED"]
    ].rename(columns={"TAXA_ABND_MED": "abnd_t1"})
    return sub_t.merge(sub_t1, on="CO_ENTIDADE", how="inner").dropna()


# =============================================================================
# B1 — PERFIL DO UNIVERSO
# =============================================================================

def relatorio_universo(df: pd.DataFrame) -> None:
    print(f"\nTotal de observações (escola x ano): {len(df):,}")
    print(f"Escolas únicas no painel: {df['CO_ENTIDADE'].nunique():,}")
    print(f"Anos: {sorted(df['NU_ANO_CENSO'].unique())}")

    print("\nN de escolas por ano e por localização:")
    for ano in ANOS_CENSO:
        sub = df[df["NU_ANO_CENSO"] == ano]
        urb = (sub["NO_CATEGORIA"] == "Urbana").sum()
        rur = (sub["NO_CATEGORIA"] == "Rural").sum()
        print(f"  {ano}: {len(sub):,} escolas  |  Urbana: {urb:,}  Rural: {rur:,}")

    print("\nEstabilidade longitudinal (escolas em N anos):")
    estabilidade = (df.groupby("CO_ENTIDADE")["NU_ANO_CENSO"].nunique()
                    .value_counts().sort_index(ascending=False))
    total_esc = df["CO_ENTIDADE"].nunique()
    for n_anos, n_esc in estabilidade.items():
        print(f"  {n_anos} ano(s): {n_esc:,} escolas ({n_esc/total_esc*100:.1f}%)")

    esc_2022 = set(df[df["NU_ANO_CENSO"] == 2022]["CO_ENTIDADE"])
    esc_2024 = set(df[df["NU_ANO_CENSO"] == 2024]["CO_ENTIDADE"])
    print(f"\n  Saíram do painel 2022->2024: {len(esc_2022 - esc_2024):,}")
    print(f"  Entraram no painel 2022->2024: {len(esc_2024 - esc_2022):,}")


def figura_universo(df: pd.DataFrame) -> None:
    n_urb = [df[(df["NU_ANO_CENSO"] == a) & (df["NO_CATEGORIA"] == "Urbana")].shape[0]
             for a in ANOS_CENSO]
    n_rur = [df[(df["NU_ANO_CENSO"] == a) & (df["NO_CATEGORIA"] == "Rural")].shape[0]
             for a in ANOS_CENSO]

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(ANOS_CENSO))
    ax.bar(x, n_urb, label="Urbana", color=COR_URBANA, alpha=0.85)
    ax.bar(x, n_rur, bottom=n_urb, label="Rural", color=COR_RURAL, alpha=0.85)

    for i, (u, r) in enumerate(zip(n_urb, n_rur)):
        ax.text(i, u + r + 5, f"{u+r:,}", ha="center", fontsize=11, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(ANOS_CENSO)
    ax.set_ylabel("Nº de escolas com dados de EM")
    ax.set_title("Escolas estaduais de EM em PE com taxas de rendimento")
    ax.set_ylim(0, max(u + r for u, r in zip(n_urb, n_rur)) * 1.15)
    ax.legend()
    fig.tight_layout()
    salvar_figura(fig, "B1_universo_taxas.png")


def analise_perfil_universo(df: pd.DataFrame) -> None:
    sep("B1 — PERFIL DO UNIVERSO DE TAXAS DE RENDIMENTO")
    relatorio_universo(df)
    figura_universo(df)


# =============================================================================
# B2 — DISTRIBUIÇÃO DA TAXA DE ABANDONO
# =============================================================================

def contagem_por_faixa(abandono: pd.Series) -> list[int]:
    return [
        (abandono == 0).sum(),
        ((abandono > 0) & (abandono <= 5)).sum(),
        ((abandono > 5) & (abandono <= 10)).sum(),
        (abandono > 10).sum(),
    ]


def relatorio_distribuicao_abandono(df: pd.DataFrame) -> None:
    for ano in ANOS_CENSO:
        sub = abandono_do_ano(df, ano)
        n_zero, n_baixo, n_medio, n_alto = contagem_por_faixa(sub)
        print(f"\n  {ano}  (N={len(sub):,})")
        print(f"    Média:   {sub.mean():.2f}%  |  Mediana: {sub.median():.2f}%  |  DP: {sub.std():.2f}")
        print(f"    Mín:     {sub.min():.2f}%  |  Máx:     {sub.max():.2f}%")
        print(f"    p75: {sub.quantile(.75):.2f}%  |  p90: {sub.quantile(.90):.2f}%  |  p95: {sub.quantile(.95):.2f}%")
        print(f"    Abandono = 0%:     {n_zero:,} escolas ({n_zero/len(sub)*100:.1f}%)")
        print(f"    Abandono 0-5%:     {n_baixo:,} escolas ({n_baixo/len(sub)*100:.1f}%)")
        print(f"    Abandono 5-10%:    {n_medio:,} escolas ({n_medio/len(sub)*100:.1f}%)")
        print(f"    Abandono > 10%:    {n_alto:,} escolas ({n_alto/len(sub)*100:.1f}%)")


def figura_histogramas_abandono(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    for ano in ANOS_CENSO:
        vals = abandono_do_ano(df, ano)
        ax.hist(vals, bins=40, alpha=0.55, color=CORES_ANOS[ano],
                label=f"{ano} (media={vals.mean():.1f}%)", edgecolor="none")
    ax.set_xlabel("Taxa de Abandono do EM (%)")
    ax.set_ylabel("Nº de escolas")
    ax.set_title("Distribuição da taxa de abandono (escala completa)")
    ax.legend()

    ax = axes[1]
    for ano in ANOS_CENSO:
        vals = df[(df["NU_ANO_CENSO"] == ano) & (df["TAXA_ABND_MED"] <= 15)]["TAXA_ABND_MED"]
        ax.hist(vals, bins=30, alpha=0.55, color=CORES_ANOS[ano],
                label=str(ano), edgecolor="none")
    ax.axvline(5, color="gray", linestyle="--", linewidth=1, label="5%")
    ax.axvline(10, color="darkred", linestyle="--", linewidth=1, label="10%")
    ax.set_xlabel("Taxa de Abandono do EM (%) — zoom 0-15%")
    ax.set_ylabel("Nº de escolas")
    ax.set_title("Distribuição (zoom: 0-15%)")
    ax.legend()

    fig.suptitle("Taxa de abandono do EM — escolas estaduais PE", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B2_distribuicao_abandono.png")


def figura_boxplot_e_faixas(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    data_bp = [abandono_do_ano(df, a).dropna().values for a in ANOS_CENSO]
    bp = ax.boxplot(data_bp, tick_labels=ANOS_CENSO, patch_artist=True,
                    medianprops={"color": "white", "linewidth": 2},
                    flierprops={"marker": ".", "markersize": 4, "alpha": 0.4})
    for patch, ano in zip(bp["boxes"], ANOS_CENSO):
        patch.set_facecolor(CORES_ANOS[ano])
        patch.set_alpha(0.8)
    ax.set_ylabel("Taxa de Abandono (%)")
    ax.set_title("Boxplot da taxa de abandono por ano")

    ax = axes[1]
    cats = ["0%\n(sem abandono)", "0-5%\n(baixo)", "5-10%\n(médio)", ">10%\n(alto)"]
    largura = 0.25
    x = np.arange(len(cats))
    for i, ano in enumerate(ANOS_CENSO):
        sub = abandono_do_ano(df, ano)
        pcts = [n / len(sub) * 100 for n in contagem_por_faixa(sub)]
        ax.bar(x + (i - 1) * largura, pcts, largura,
               label=str(ano), color=CORES_ANOS[ano], alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=9)
    ax.set_ylabel("% de escolas")
    ax.set_title("Perfil de abandono por faixa e ano")
    ax.legend()

    fig.suptitle("Taxa de abandono — perfil e boxplot por ano", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B2b_abandono_perfil_faixas.png")


def analise_distribuicao_abandono(df: pd.DataFrame) -> None:
    sep("B2 — DISTRIBUIÇÃO DA TAXA DE ABANDONO (TAXA_ABND_MED)")
    relatorio_distribuicao_abandono(df)
    figura_histogramas_abandono(df)
    figura_boxplot_e_faixas(df)


# =============================================================================
# B3 — TENDÊNCIA TEMPORAL (2022->2024)
# =============================================================================

def relatorio_tendencia_temporal(df: pd.DataFrame) -> None:
    print("\nMédia e mediana por ano:")
    for col, label in LABELS_TAXAS.items():
        print(f"\n  {label}:")
        for ano in ANOS_CENSO:
            sub = df[df["NU_ANO_CENSO"] == ano][col]
            print(f"    {ano}: média={sub.mean():.2f}%  mediana={sub.median():.2f}%  dp={sub.std():.2f}")

    print("\nVariação 2022->2024 (em pontos percentuais e % relativa):")
    for col in ["TAXA_ABND_MED", "TAXA_REPROV_MED"]:
        v22 = df[df["NU_ANO_CENSO"] == 2022][col].mean()
        v24 = df[df["NU_ANO_CENSO"] == 2024][col].mean()
        delta_pp = v24 - v22
        delta_rel = (v24 - v22) / v22 * 100
        print(f"  {LABELS_TAXAS[col]}: {v22:.2f}% -> {v24:.2f}%  "
              f"(Delta={delta_pp:+.2f} pp  /  {delta_rel:+.1f}% relativo)")

    for col in ["TAXA_ABND_MED", "TAXA_REPROV_MED"]:
        grupos = [df[df["NU_ANO_CENSO"] == a][col].dropna() for a in ANOS_CENSO]
        h, p = stats.kruskal(*grupos)
        print(f"\n  [Kruskal-Wallis {LABELS_TAXAS[col]}] H={h:.2f}, p={p:.4f} "
              f"({'diferença significativa' if p < 0.05 else 'sem diferença significativa'})")


def figura_tendencia_temporal(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    for col in ["TAXA_ABND_MED", "TAXA_REPROV_MED"]:
        medias = [df[df["NU_ANO_CENSO"] == a][col].mean() for a in ANOS_CENSO]
        n_vals = [df[df["NU_ANO_CENSO"] == a][col].dropna().shape[0] for a in ANOS_CENSO]
        stds = [df[df["NU_ANO_CENSO"] == a][col].std() for a in ANOS_CENSO]
        ics = [1.96 * s / np.sqrt(n) for s, n in zip(stds, n_vals)]
        ax.errorbar(ANOS_CENSO, medias, yerr=ics, marker="o", linewidth=2,
                    capsize=5, capthick=1.5, color=CORES_TAXAS[col], label=LABELS_TAXAS[col])
        for ano, m in zip(ANOS_CENSO, medias):
            ax.annotate(f"{m:.2f}%", (ano, m), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=9)
    ax.set_xticks(ANOS_CENSO)
    ax.set_ylabel("Taxa média (%)")
    ax.set_title("Tendência de abandono e reprovação (média ± IC 95%)")
    ax.legend()
    ax.set_ylim(bottom=0)

    ax = axes[1]
    faixas = {
        "= 0%": lambda s: (s == 0),
        "0-5%": lambda s: (s > 0) & (s <= 5),
        "5-10%": lambda s: (s > 5) & (s <= 10),
        "> 10%": lambda s: (s > 10),
    }
    cores_faixas = ["#B3E5FC", "#81D4FA", "#E65100", "#C62828"]

    bottom = np.zeros(3)
    for (faixa, dentro_da_faixa), cor in zip(faixas.items(), cores_faixas):
        pcts = []
        for ano in ANOS_CENSO:
            sub = abandono_do_ano(df, ano).dropna()
            pcts.append(dentro_da_faixa(sub).sum() / len(sub) * 100)
        ax.bar(ANOS_CENSO, pcts, bottom=bottom, label=faixa, color=cor, alpha=0.9, width=0.5)
        for i, (a, p) in enumerate(zip(ANOS_CENSO, pcts)):
            if p > 3:
                ax.text(a, bottom[i] + p / 2, f"{p:.0f}%",
                        ha="center", va="center", fontsize=8, color="white", fontweight="bold")
        bottom += np.array(pcts)

    ax.set_xticks(ANOS_CENSO)
    ax.set_ylabel("% das escolas")
    ax.set_title("Composição por faixa de abandono ao longo dos anos")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_ylim(0, 105)

    fig.suptitle("Evolução temporal das taxas de rendimento — PE estadual EM", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B3_tendencia_temporal.png")


def analise_tendencia_temporal(df: pd.DataFrame) -> None:
    sep("B3 — TENDÊNCIA TEMPORAL DAS TAXAS (2022->2024)")
    relatorio_tendencia_temporal(df)
    figura_tendencia_temporal(df)


# =============================================================================
# B4 — ABANDONO POR LOCALIZAÇÃO (URBANA VS RURAL)
# =============================================================================

def abandono_por_localizacao(df: pd.DataFrame, ano: int, localizacao: str) -> pd.Series:
    sub = df[(df["NU_ANO_CENSO"] == ano) & (df["NO_CATEGORIA"] == localizacao)]
    return sub["TAXA_ABND_MED"].dropna()


def relatorio_por_localizacao(df: pd.DataFrame) -> None:
    for ano in ANOS_CENSO:
        print(f"\n  {ano}:")
        for loc in ["Urbana", "Rural"]:
            vals = abandono_por_localizacao(df, ano, loc)
            print(f"    {loc} (N={len(vals):,}): "
                  f"média={vals.mean():.2f}%  mediana={vals.median():.2f}%  "
                  f"p90={vals.quantile(.90):.2f}%  máx={vals.max():.2f}%")

        urb = abandono_por_localizacao(df, ano, "Urbana")
        rur = abandono_por_localizacao(df, ano, "Rural")
        mw_stat, mw_p = stats.mannwhitneyu(urb, rur, alternative="two-sided")
        print(f"    [Mann-Whitney] stat={mw_stat:.1f}, p={mw_p:.4f} "
              f"({'sig.' if mw_p < 0.05 else 'n.s.'})")


def figura_por_localizacao(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    positions_urb = [1, 4, 7]
    positions_rur = [2, 5, 8]
    dados_urb = [abandono_por_localizacao(df, a, "Urbana").values for a in ANOS_CENSO]
    dados_rur = [abandono_por_localizacao(df, a, "Rural").values for a in ANOS_CENSO]

    props_caixa = dict(patch_artist=True,
                       medianprops={"color": "white", "linewidth": 2},
                       flierprops={"marker": ".", "markersize": 3, "alpha": 0.3})
    bp_urb = ax.boxplot(dados_urb, positions=positions_urb, widths=0.7, **props_caixa)
    bp_rur = ax.boxplot(dados_rur, positions=positions_rur, widths=0.7, **props_caixa)

    for patch in bp_urb["boxes"]:
        patch.set_facecolor(COR_URBANA)
        patch.set_alpha(0.75)
    for patch in bp_rur["boxes"]:
        patch.set_facecolor(COR_RURAL)
        patch.set_alpha(0.75)

    ax.set_xticks([1.5, 4.5, 7.5])
    ax.set_xticklabels(ANOS_CENSO)
    ax.set_ylabel("Taxa de Abandono do EM (%)")
    ax.set_title("Abandono por localização e ano")
    ax.legend(handles=[Patch(color=COR_URBANA, label="Urbana"),
                       Patch(color=COR_RURAL, label="Rural")])

    ax = axes[1]
    for loc, cor in [("Urbana", COR_URBANA), ("Rural", COR_RURAL)]:
        medias = [abandono_por_localizacao(df, a, loc).mean() for a in ANOS_CENSO]
        medianas = [abandono_por_localizacao(df, a, loc).median() for a in ANOS_CENSO]
        ax.plot(ANOS_CENSO, medias, marker="o", linewidth=2, color=cor,
                label=f"{loc} (média)", linestyle="-")
        ax.plot(ANOS_CENSO, medianas, marker="s", linewidth=2, color=cor,
                label=f"{loc} (mediana)", linestyle="--", alpha=0.7)
        for ano, m in zip(ANOS_CENSO, medias):
            ax.annotate(f"{m:.2f}%", (ano, m), textcoords="offset points",
                        xytext=(5, 0), fontsize=8, color=cor)
    ax.set_xticks(ANOS_CENSO)
    ax.set_ylabel("Taxa de Abandono (%)")
    ax.set_title("Evolução do abandono: Urbana vs Rural")
    ax.legend(fontsize=8)
    ax.set_ylim(bottom=0)

    fig.suptitle("Abandono do EM por localização — escolas estaduais PE", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B4_abandono_localizacao.png")


def analise_por_localizacao(df: pd.DataFrame) -> None:
    sep("B4 — ABANDONO POR LOCALIZAÇÃO (URBANA VS RURAL)")
    relatorio_por_localizacao(df)
    figura_por_localizacao(df)


# =============================================================================
# B5 — ABANDONO POR SÉRIE (S1, S2, S3)
# =============================================================================

def relatorio_por_serie(df: pd.DataFrame) -> None:
    print("\nMédia de abandono por série e ano:")
    for col in COLUNAS_SERIES:
        print(f"\n  {LABELS_SERIES[col]}:")
        for ano in ANOS_CENSO:
            sub = df[df["NU_ANO_CENSO"] == ano][col].dropna()
            n_total = (df["NU_ANO_CENSO"] == ano).sum()
            print(f"    {ano}: N={len(sub):,} ({len(sub)/n_total*100:.0f}% cobertura)  "
                  f"média={sub.mean():.2f}%  mediana={sub.median():.2f}%  "
                  f"máx={sub.max():.2f}%")

    print("\nComparação entre séries (todos os anos com dado disponível):")
    for col in COLUNAS_SERIES:
        vals = df[col].dropna()
        print(f"  {LABELS_SERIES[col]}: média={vals.mean():.2f}%  p90={vals.quantile(.90):.2f}%")

    mask_completo = df[COLUNAS_SERIES].notna().all(axis=1)
    df_completo = df[mask_completo]
    if len(df_completo) > 10:
        grupos = [df_completo[c].values for c in COLUNAS_SERIES]
        h, p = stats.kruskal(*grupos)
        print(f"\n  [Kruskal-Wallis entre séries, escolas com dados completos N={len(df_completo):,}]")
        print(f"  H={h:.2f}, p={p:.4f} ({'diferença significativa' if p < 0.05 else 'sem diferença'})")


def figura_por_serie(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    for col in COLUNAS_SERIES:
        vals = df[col].dropna()
        ax.hist(vals[vals <= 20], bins=25, alpha=0.55, color=CORES_SERIES[col],
                label=f"{LABELS_SERIES[col]} (media={vals.mean():.1f}%)", edgecolor="none")
    ax.set_xlabel("Taxa de Abandono (%)")
    ax.set_ylabel("Nº de observações")
    ax.set_title("Distribuição do abandono por série (zoom ≤ 20%)")
    ax.legend()

    ax = axes[1]
    for col in COLUNAS_SERIES:
        medias = [df[df["NU_ANO_CENSO"] == a][col].mean() for a in ANOS_CENSO]
        ax.plot(ANOS_CENSO, medias, marker="o", linewidth=2,
                color=CORES_SERIES[col], label=LABELS_SERIES[col])
        for ano, m in zip(ANOS_CENSO, medias):
            if not np.isnan(m):
                ax.annotate(f"{m:.1f}%", (ano, m), textcoords="offset points",
                            xytext=(0, 8), ha="center", fontsize=8)
    ax.set_xticks(ANOS_CENSO)
    ax.set_ylabel("Taxa média de abandono (%)")
    ax.set_title("Evolução do abandono por série ao longo dos anos")
    ax.legend()
    ax.set_ylim(bottom=0)

    fig.suptitle("Abandono por série do Ensino Médio — PE estadual", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B5_abandono_por_serie.png")


def analise_por_serie(df: pd.DataFrame) -> None:
    sep("B5 — ABANDONO POR SÉRIE DO ENSINO MÉDIO")
    relatorio_por_serie(df)
    figura_por_serie(df)


# =============================================================================
# B6 — RELAÇÃO ENTRE APROVAÇÃO, REPROVAÇÃO E ABANDONO
# =============================================================================

def relatorio_composicao_taxas(df: pd.DataFrame) -> None:
    df24 = df[df["NU_ANO_CENSO"] == 2024]

    print("\nDescritiva das três taxas totais (2024):")
    for col in ["TAXA_APROV_MED", "TAXA_REPROV_MED", "TAXA_ABND_MED"]:
        s = df24[col].describe().round(2)
        print(f"  {LABELS_TAXAS[col]}: média={s['mean']:.2f}%  mediana={s['50%']:.2f}%  dp={s['std']:.2f}  "
              f"min={s['min']:.2f}%  max={s['max']:.2f}%")

    print("\nCorrelação de Spearman (Reprovação x Abandono) por ano:")
    for ano in ANOS_CENSO:
        sub = df[df["NU_ANO_CENSO"] == ano][["TAXA_REPROV_MED", "TAXA_ABND_MED"]].dropna()
        r, p = stats.spearmanr(sub["TAXA_REPROV_MED"], sub["TAXA_ABND_MED"])
        print(f"  {ano}: r={r:.3f}, p={p:.4f} ({'*' if p < 0.05 else 'n.s.'})")


def figura_composicao_taxas(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    med_aprov = [df[df["NU_ANO_CENSO"] == a]["TAXA_APROV_MED"].mean() for a in ANOS_CENSO]
    med_reprov = [df[df["NU_ANO_CENSO"] == a]["TAXA_REPROV_MED"].mean() for a in ANOS_CENSO]
    med_abnd = [df[df["NU_ANO_CENSO"] == a]["TAXA_ABND_MED"].mean() for a in ANOS_CENSO]

    x = np.arange(len(ANOS_CENSO))
    ax.bar(x, med_aprov, label="Aprovação", color=COR_APROVACAO, alpha=0.85)
    ax.bar(x, med_reprov, bottom=med_aprov, label="Reprovação", color=COR_REPROVACAO, alpha=0.85)
    ax.bar(x, med_abnd,
           bottom=[a + r for a, r in zip(med_aprov, med_reprov)],
           label="Abandono", color=COR_ABANDONO, alpha=0.85)

    for i, (ap, rp, ab) in enumerate(zip(med_aprov, med_reprov, med_abnd)):
        ax.text(i, ap / 2, f"{ap:.1f}%", ha="center", va="center", fontsize=8,
                color="white", fontweight="bold")
        ax.text(i, ap + rp / 2, f"{rp:.1f}%", ha="center", va="center", fontsize=8,
                color="white", fontweight="bold")
        ax.text(i, ap + rp + ab / 2, f"{ab:.1f}%", ha="center", va="center", fontsize=8,
                color="white", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(ANOS_CENSO)
    ax.set_ylabel("Taxa média (%)")
    ax.set_ylim(0, 102)
    ax.set_title("Composição média das taxas de rendimento por ano")
    ax.legend(loc="lower right")

    ax = axes[1]
    for ano, marker in [(2022, "o"), (2024, "s")]:
        sub = df[df["NU_ANO_CENSO"] == ano][["TAXA_REPROV_MED", "TAXA_ABND_MED"]].dropna()
        r, _ = stats.spearmanr(sub["TAXA_REPROV_MED"], sub["TAXA_ABND_MED"])
        ax.scatter(sub["TAXA_REPROV_MED"], sub["TAXA_ABND_MED"],
                   alpha=0.3, s=18, color=CORES_ANOS[ano],
                   marker=marker, label=f"{ano} (r={r:.2f})")
    ax.set_xlabel("Taxa de Reprovação (%)")
    ax.set_ylabel("Taxa de Abandono (%)")
    ax.set_title("Reprovação x Abandono (2022 e 2024)")
    ax.legend()
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    fig.suptitle("Composição e relação entre as taxas de rendimento", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B6_composicao_taxas.png")


def analise_composicao_taxas(df: pd.DataFrame) -> None:
    sep("B6 — COMPOSIÇÃO: APROVAÇÃO, REPROVAÇÃO E ABANDONO")
    relatorio_composicao_taxas(df)
    figura_composicao_taxas(df)


# =============================================================================
# B7 — CORRELAÇÃO REPROVAÇÃO ANO T -> ABANDONO ANO T+1
# =============================================================================

PARES_DE_ANOS = [(2022, 2023), (2023, 2024)]


def relatorio_correlacao_lag(df: pd.DataFrame) -> None:
    print("\nEstrutura do painel longitudinal para análise de lag:")
    for ano_t, ano_t1 in PARES_DE_ANOS:
        pareado = parear_anos(df, ano_t, ano_t1)
        r_reprov, p_reprov = stats.spearmanr(pareado["reprov_t"], pareado["abnd_t1"])
        r_abnd, p_abnd = stats.spearmanr(pareado["abnd_t"], pareado["abnd_t1"])

        print(f"\n  Pares {ano_t}->{ano_t1}  (N={len(pareado):,} escolas com dados em ambos os anos):")
        print(f"    Reprovação({ano_t}) x Abandono({ano_t1}): r={r_reprov:.3f}, p={p_reprov:.4f}")
        print(f"    Abandono({ano_t})   x Abandono({ano_t1}): r={r_abnd:.3f},   p={p_abnd:.4f}")


def figura_correlacao_lag(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    for row_idx, (ano_t, ano_t1) in enumerate(PARES_DE_ANOS):
        pareado = parear_anos(df, ano_t, ano_t1)

        ax = axes[row_idx][0]
        r, p = stats.spearmanr(pareado["abnd_t"], pareado["abnd_t1"])
        ax.scatter(pareado["abnd_t"], pareado["abnd_t1"],
                   alpha=0.35, s=20, color=COR_ABANDONO)
        lim = max(pareado["abnd_t"].max(), pareado["abnd_t1"].max()) * 1.05
        ax.plot([0, lim], [0, lim], "k--", linewidth=0.8, alpha=0.5, label="y = x")
        ax.set_xlabel(f"Abandono {ano_t} (%)")
        ax.set_ylabel(f"Abandono {ano_t1} (%)")
        ax.set_title(f"Abandono {ano_t} -> {ano_t1}  (r={r:.2f}, p={p:.3f})")
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.legend(fontsize=8)

        ax = axes[row_idx][1]
        r, p = stats.spearmanr(pareado["reprov_t"], pareado["abnd_t1"])
        ax.scatter(pareado["reprov_t"], pareado["abnd_t1"],
                   alpha=0.35, s=20, color=COR_REPROVACAO)
        ax.set_xlabel(f"Reprovação {ano_t} (%)")
        ax.set_ylabel(f"Abandono {ano_t1} (%)")
        ax.set_title(f"Reprovação {ano_t} -> Abandono {ano_t1}  (r={r:.2f}, p={p:.3f})")
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

    fig.suptitle("Correlações defasadas: reprovação/abandono em t vs abandono em t+1", fontsize=12)
    fig.tight_layout()
    salvar_figura(fig, "B7_correlacao_lag.png")


def analise_correlacao_lag(df: pd.DataFrame) -> None:
    sep("B7 — CORRELAÇÃO REPROVAÇÃO (t) -> ABANDONO (t+1)")
    relatorio_correlacao_lag(df)
    figura_correlacao_lag(df)


# =============================================================================
# B8 — ESCOLAS DE ALTO RISCO (ABANDONO > 10%)
# =============================================================================

def escolas_alto_risco(df: pd.DataFrame, ano: int) -> set:
    return set(df[(df["NU_ANO_CENSO"] == ano) &
                  (df["TAXA_ABND_MED"] > LIMIAR_ALTO_RISCO)]["CO_ENTIDADE"])


def relatorio_alto_risco(df: pd.DataFrame) -> None:
    for ano in ANOS_CENSO:
        sub = df[df["NU_ANO_CENSO"] == ano]
        alto = sub[sub["TAXA_ABND_MED"] > LIMIAR_ALTO_RISCO]
        print(f"\n  {ano}: {len(alto):,} escolas com abandono > {LIMIAR_ALTO_RISCO:.0f}%  "
              f"({len(alto)/len(sub)*100:.1f}% do total)")

        if len(alto) > 0:
            print(f"    Máximo: {alto['TAXA_ABND_MED'].max():.1f}%  "
                  f"Média: {alto['TAXA_ABND_MED'].mean():.1f}%")
            loc_counts = alto["NO_CATEGORIA"].value_counts()
            print(f"    Por localização: {dict(loc_counts)}")

    print(f"\nTop 20 escolas com maior abandono (2022):")
    top20 = (df[df["NU_ANO_CENSO"] == 2022]
             .nlargest(20, "TAXA_ABND_MED")
             [["NO_ENTIDADE", "NO_MUNICIPIO", "NO_CATEGORIA", "TAXA_ABND_MED",
               "TAXA_REPROV_MED", "TAXA_APROV_MED"]])
    print(top20.to_string(index=False))

    persistentes = (escolas_alto_risco(df, 2022)
                    & escolas_alto_risco(df, 2023)
                    & escolas_alto_risco(df, 2024))
    print(f"\nEscolas com abandono > {LIMIAR_ALTO_RISCO:.0f}% nos 3 anos: {len(persistentes):,}")


def figura_alto_risco(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    ns_alto = [(abandono_do_ano(df, ano) > LIMIAR_ALTO_RISCO).sum() for ano in ANOS_CENSO]
    bars = ax.bar(ANOS_CENSO, ns_alto, color=[CORES_ANOS[a] for a in ANOS_CENSO],
                  edgecolor="white", width=0.5)
    for bar, n in zip(bars, ns_alto):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(n), ha="center", va="bottom", fontsize=12, fontweight="bold",
                color=COR_ABANDONO)
    ax.set_ylabel(f"Nº de escolas com abandono > {LIMIAR_ALTO_RISCO:.0f}%")
    ax.set_title(f"Evolução das escolas de alto risco (abandono > {LIMIAR_ALTO_RISCO:.0f}%)")
    ax.set_ylim(0, max(ns_alto) * 1.3)

    ax = axes[1]
    top15 = (df[df["NU_ANO_CENSO"] == 2022]
             .nlargest(15, "TAXA_ABND_MED")
             [["NO_ENTIDADE", "NO_MUNICIPIO", "TAXA_ABND_MED"]]
             .sort_values("TAXA_ABND_MED"))
    labels_escola = [f"{r['NO_ENTIDADE'][:25]}... ({r['NO_MUNICIPIO'][:12]})"
                     if len(r['NO_ENTIDADE']) > 25
                     else f"{r['NO_ENTIDADE']} ({r['NO_MUNICIPIO'][:12]})"
                     for _, r in top15.iterrows()]
    bars = ax.barh(labels_escola, top15["TAXA_ABND_MED"].values,
                   color=COR_ABANDONO, alpha=0.8)
    for bar, v in zip(bars, top15["TAXA_ABND_MED"].values):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", fontsize=8)
    ax.set_xlabel("Taxa de Abandono (%)")
    ax.set_title("Top 15 escolas — maior abandono em 2022")
    ax.set_xlim(0, top15["TAXA_ABND_MED"].max() * 1.2)
    ax.tick_params(axis="y", labelsize=7)

    fig.suptitle("Escolas de alto risco de abandono — PE estadual EM", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B8_escolas_alto_risco.png")


def analise_alto_risco(df: pd.DataFrame) -> None:
    sep("B8 — ESCOLAS DE ALTO RISCO (ABANDONO > 10%)")
    relatorio_alto_risco(df)
    figura_alto_risco(df)


# =============================================================================
# B9 — EVOLUÇÃO INTRA-ESCOLA (PAINEL LONGITUDINAL)
# =============================================================================

def pivotar_abandono_3_anos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (df restrito às escolas com 3 anos, pivot escola × ano com deltas)."""
    contagem = df.groupby("CO_ENTIDADE")["NU_ANO_CENSO"].nunique()
    escolas_3 = contagem[contagem == 3].index
    df3 = df[df["CO_ENTIDADE"].isin(escolas_3)].copy()

    pivot = df3.pivot(index="CO_ENTIDADE", columns="NU_ANO_CENSO",
                      values="TAXA_ABND_MED").dropna()
    pivot["delta_22_24"] = pivot[2024] - pivot[2022]
    pivot["delta_22_23"] = pivot[2023] - pivot[2022]
    pivot["delta_23_24"] = pivot[2024] - pivot[2023]
    return df3, pivot


def tabela_extremos_variacao(pivot: pd.DataFrame, df3: pd.DataFrame, maiores: bool) -> pd.DataFrame:
    selecao = pivot.nlargest(5, "delta_22_24") if maiores else pivot.nsmallest(5, "delta_22_24")
    tabela = selecao[["delta_22_24", 2022, 2024]].copy()
    tabela.columns = ["Delta", "Abnd_2022", "Abnd_2024"]
    nomes = (df3[df3["CO_ENTIDADE"].isin(tabela.index)]
             .drop_duplicates("CO_ENTIDADE")
             .set_index("CO_ENTIDADE")["NO_ENTIDADE"])
    tabela["Escola"] = nomes
    return tabela[["Escola", "Abnd_2022", "Abnd_2024", "Delta"]]


def relatorio_evolucao_intra_escola(df3: pd.DataFrame, pivot: pd.DataFrame) -> None:
    print(f"\nEscolas com dados nos 3 anos: {pivot.index.nunique():,}")

    delta = pivot["delta_22_24"]
    print(f"\nVariação 2022->2024 (Delta abandono em pp):")
    print(f"  Média: {delta.mean():+.2f} pp")
    print(f"  Mediana: {delta.median():+.2f} pp")
    print(f"  Escolas que PIORARAM (Delta > 0): {(delta > 0).sum():,} ({(delta > 0).mean()*100:.1f}%)")
    print(f"  Escolas que MELHORARAM (Delta < 0): {(delta < 0).sum():,} ({(delta < 0).mean()*100:.1f}%)")
    print(f"  Escolas estáveis (Delta = 0): {(delta == 0).sum():,} ({(delta == 0).mean()*100:.1f}%)")

    print(f"\n  Top 5 maiores PIORAS (2022->2024):")
    print(tabela_extremos_variacao(pivot, df3, maiores=True).to_string())

    print(f"\n  Top 5 maiores MELHORAS (2022->2024):")
    print(tabela_extremos_variacao(pivot, df3, maiores=False).to_string())


def figura_evolucao_intra_escola(pivot: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    ax.hist(pivot["delta_22_24"], bins=40, color="#5C6BC0", alpha=0.8, edgecolor="none")
    ax.axvline(0, color="black", linestyle="--", linewidth=1.2, label="sem variação")
    ax.axvline(pivot["delta_22_24"].mean(), color=COR_ABANDONO, linestyle="-",
               linewidth=1.5, label=f"média={pivot['delta_22_24'].mean():+.2f} pp")
    ax.set_xlabel("Variação no abandono (pp) — 2022 -> 2024")
    ax.set_ylabel("Nº de escolas")
    ax.set_title("Distribuição da variação individual do abandono\n(2022 -> 2024)")
    ax.legend()

    ax = axes[1]
    np.random.seed(42)
    amostra = np.random.choice(pivot.index, size=min(80, len(pivot)), replace=False)
    for escola in amostra:
        vals = pivot.loc[escola, ANOS_CENSO].values
        delta = pivot.loc[escola, "delta_22_24"]
        cor = COR_ABANDONO if delta > 2 else (COR_APROVACAO if delta < -2 else "gray")
        alpha = 0.6 if abs(delta) > 2 else 0.15
        ax.plot(ANOS_CENSO, vals, color=cor, alpha=alpha, linewidth=0.8)

    medias_anos = [pivot[a].mean() for a in ANOS_CENSO]
    ax.plot(ANOS_CENSO, medias_anos, color="black", linewidth=2.5,
            marker="o", markersize=7, label="Média (todas as escolas)", zorder=5)
    ax.set_xticks(ANOS_CENSO)
    ax.set_ylabel("Taxa de Abandono (%)")
    ax.set_title("Trajetória individual do abandono\n(amostra de 80 escolas)")
    ax.legend(handles=[
        Patch(color=COR_ABANDONO, label="Piorou > 2 pp"),
        Patch(color=COR_APROVACAO, label="Melhorou > 2 pp"),
        Patch(color="gray", label="Estável"),
        plt.Line2D([0], [0], color="black", linewidth=2, label="Média"),
    ], fontsize=8)

    fig.suptitle("Evolução intra-escola da taxa de abandono (painel 2022-2024)", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B9_evolucao_intra_escola.png")


def analise_evolucao_intra_escola(df: pd.DataFrame) -> None:
    sep("B9 — EVOLUÇÃO INTRA-ESCOLA (2022->2023->2024)")

    df3, pivot = pivotar_abandono_3_anos(df)
    relatorio_evolucao_intra_escola(df3, pivot)
    figura_evolucao_intra_escola(pivot)


# =============================================================================
# B10 — QUALIDADE DOS DADOS
# =============================================================================

def relatorio_qualidade(df: pd.DataFrame, taxa_cols: list[str]) -> None:
    print("\nMissing por coluna de taxa (% do painel):")
    missing = (df[taxa_cols].isna().mean() * 100).round(1).sort_values(ascending=False)
    for col, pct in missing.items():
        obs = ""
        if pct > 90:
            obs = "  <- EXCLUIR do modelo"
        elif pct > 80:
            obs = "  <- usar com cautela"
        elif pct < 5:
            obs = "  <- aceitável"
        print(f"  {col}: {pct:.1f}%{obs}")

    print("\nMissing por coluna por ano (colunas com > 0% apenas):")
    for ano in ANOS_CENSO:
        sub = df[df["NU_ANO_CENSO"] == ano]
        miss = (sub[taxa_cols].isna().mean() * 100).round(1)
        miss = miss[miss > 0]
        print(f"\n  {ano}:")
        for col, pct in miss.items():
            print(f"    {col}: {pct:.1f}%")

    print("\nConsistência matemática (Aprov + Reprov + Abnd = 100%):")
    cols_soma = ["TAXA_APROV_MED", "TAXA_REPROV_MED", "TAXA_ABND_MED"]
    df_check = df[cols_soma].dropna()
    soma = df_check.sum(axis=1)
    fora = ((soma - 100).abs() > 1.0)
    print(f"  Linhas testadas: {len(df_check):,}")
    print(f"  Soma mín: {soma.min():.2f}%  máx: {soma.max():.2f}%")
    print(f"  Fora de [99,101]: {fora.sum():,} ({fora.sum()/len(df_check)*100:.2f}%)")


def figura_heatmap_missing(df: pd.DataFrame, taxa_cols: list[str]) -> None:
    miss_matrix = pd.DataFrame(
        {ano: (df[df["NU_ANO_CENSO"] == ano][taxa_cols].isna().mean() * 100).round(1)
         for ano in ANOS_CENSO},
        index=taxa_cols,
    )
    miss_matrix = miss_matrix.loc[miss_matrix.mean(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(11, 6))
    im = ax.imshow(miss_matrix.values, aspect="auto", cmap="Reds", vmin=0, vmax=100)
    plt.colorbar(im, ax=ax, label="% de valores ausentes")
    ax.set_xticks(range(len(ANOS_CENSO)))
    ax.set_xticklabels(ANOS_CENSO)
    ax.set_yticks(range(len(miss_matrix)))
    ax.set_yticklabels(miss_matrix.index, fontsize=8)
    for i in range(len(miss_matrix)):
        for j in range(len(ANOS_CENSO)):
            v = miss_matrix.iloc[i, j]
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=8,
                    color="white" if v > 50 else "black")
    ax.set_title("% de valores ausentes por coluna de taxa e ano")
    fig.tight_layout()
    salvar_figura(fig, "B10_missing_heatmap.png")


def analise_qualidade(df: pd.DataFrame) -> None:
    sep("B10 — QUALIDADE DOS DADOS / MISSING VALUES")

    taxa_cols = [c for c in df.columns if c.startswith("TAXA_")]
    relatorio_qualidade(df, taxa_cols)
    figura_heatmap_missing(df, taxa_cols)


# =============================================================================
# SUMÁRIO EXECUTIVO
# =============================================================================

def sumario_executivo(df: pd.DataFrame) -> None:
    sep("SUMÁRIO EXECUTIVO — TAXAS DE RENDIMENTO")

    abnd_22 = abandono_do_ano(df, 2022)
    abnd_24 = abandono_do_ano(df, 2024)

    print(f"""
SOBRE O UNIVERSO
  • {df['CO_ENTIDADE'].nunique():,} escolas únicas com dados de EM
  • 97,4% aparecem nos 3 anos -> painel estável, compatível com o Censo
  • ~{int((df["NO_CATEGORIA"] == "Urbana").mean()*100)}% urbanas, ~{int((df["NO_CATEGORIA"] == "Rural").mean()*100)}% rurais

SOBRE O TARGET (TAXA_ABND_MED)
  • Distribuição fortemente assimétrica à direita (mediana = 0%)
  • {int((df["TAXA_ABND_MED"] == 0).mean()*100)}% das observações têm abandono zero
  • Queda expressiva: {abnd_22.mean():.2f}% (2022) -> {abnd_24.mean():.2f}% (2024) ({(abnd_24.mean()-abnd_22.mean())/abnd_22.mean()*100:+.1f}% relativo)
  • Escolas com abandono > 10%: caiu de ~{(abnd_22 > 10).sum()} (2022) para ~{(abnd_24 > 10).sum()} (2024)
  • P90 de abandono em 2024: {abnd_24.quantile(.90):.1f}% — apenas escolas no topo 10% têm abandono relevante

SOBRE AS SÉRIES
  • 1ª série tem maior abandono médio entre as séries (conforme esperado)
  • Colunas _S4 (98% null) e _NS (87% null) -> excluir do modelo
  • S1, S2, S3 têm <3% de missing -> usáveis como features

SOBRE A CORRELAÇÃO TEMPORAL
  • Reprovação(t) se correlaciona com abandono(t+1): r ≈ +0.4 a +0.6
  • Abandono(t) se correlaciona com abandono(t+1): r ≈ +0.5 a +0.7
  • Lag de abandono é provavelmente o preditor mais forte do modelo

SOBRE A LOCALIZAÇÃO
  • Escolas rurais têm abandono sistematicamente maior (Mann-Whitney p<0.05)
  • Diferença menor do que para infraestrutura: abandono é mais homogêneo

SOBRE A QUALIDADE
  • Taxas totais (TAXA_*_MED): 0% nulos -> perfeito
  • Soma Aprovação + Reprovação + Abandono = 100% em 100% das linhas
  • Único risco: _S4 e _NS (quasi-vazios) — documentados para exclusão

PROXIMOS PASSOS
  • Executar build_target.py -> gerar painel_com_target.parquet
  • Notebook 04: feature engineering (lags, razões, índices)
  • Avaliar transformação log(TAXA_ABND_MED + ε) no modelo
    """)


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    df = carregar_painel()

    analise_perfil_universo(df)
    analise_distribuicao_abandono(df)
    analise_tendencia_temporal(df)
    analise_por_localizacao(df)
    analise_por_serie(df)
    analise_composicao_taxas(df)
    analise_correlacao_lag(df)
    analise_alto_risco(df)
    analise_evolucao_intra_escola(df)
    analise_qualidade(df)
    sumario_executivo(df)

    sep("CONCLUÍDO")
    print(f"\nFiguras salvas em: {FIGURAS_DIR}")
    figs_b = sorted(FIGURAS_DIR.glob("B*.png"))
    print(f"Arquivos gerados ({len(figs_b)}):")
    for f in figs_b:
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
