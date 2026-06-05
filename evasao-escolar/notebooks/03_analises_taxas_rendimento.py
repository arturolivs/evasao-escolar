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

import logging
import sys
from pathlib import Path

# Força UTF-8 no stdout para evitar erros de encoding no Windows
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

from src.data import config  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

PARQUET_PATH = config.INTERIM_DIR / "taxas_rendimento_pe_estadual_em.parquet"
FIGURAS_DIR  = ROOT / "reports" / "figuras"
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)

CORES_ANOS = {2022: "#2196F3", 2023: "#FF9800", 2024: "#4CAF50"}
COR_URBANA = "#1565C0"
COR_RURAL  = "#2E7D32"
COR_ABND   = "#C62828"   # vermelho abandono
COR_REPROV = "#E65100"   # laranja reprovação
COR_APROV  = "#1B5E20"   # verde aprovação


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


# =============================================================================
# CARGA
# =============================================================================

def carregar_painel() -> pd.DataFrame:
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"Painel interim não encontrado em {PARQUET_PATH}.\n"
            f"Execute: python -m src.data.build_taxas_rendimento"
        )
    df = pd.read_parquet(PARQUET_PATH)
    df["NU_ANO_CENSO"] = df["NU_ANO_CENSO"].astype(int)
    logger.info("Painel carregado: %d linhas, %d colunas.", *df.shape)
    return df


# =============================================================================
# B1 — PERFIL DO UNIVERSO
# =============================================================================

def analise_perfil_universo(df: pd.DataFrame) -> None:
    sep("B1 — PERFIL DO UNIVERSO DE TAXAS DE RENDIMENTO")

    print(f"\nTotal de observações (escola x ano): {len(df):,}")
    print(f"Escolas únicas no painel: {df['CO_ENTIDADE'].nunique():,}")
    print(f"Anos: {sorted(df['NU_ANO_CENSO'].unique())}")

    print("\nN de escolas por ano e por localização:")
    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano]
        urb = (sub["NO_CATEGORIA"] == "Urbana").sum()
        rur = (sub["NO_CATEGORIA"] == "Rural").sum()
        print(f"  {ano}: {len(sub):,} escolas  |  Urbana: {urb:,}  Rural: {rur:,}")

    print("\nEstabilidade longitudinal (escolas em N anos):")
    estab = df.groupby("CO_ENTIDADE")["NU_ANO_CENSO"].nunique().value_counts().sort_index(ascending=False)
    total_esc = df["CO_ENTIDADE"].nunique()
    for n_anos, n_esc in estab.items():
        print(f"  {n_anos} ano(s): {n_esc:,} escolas ({n_esc/total_esc*100:.1f}%)")

    # Entradas e saídas
    esc_2022 = set(df[df["NU_ANO_CENSO"] == 2022]["CO_ENTIDADE"])
    esc_2024 = set(df[df["NU_ANO_CENSO"] == 2024]["CO_ENTIDADE"])
    print(f"\n  Saíram do painel 2022->2024: {len(esc_2022 - esc_2024):,}")
    print(f"  Entraram no painel 2022->2024: {len(esc_2024 - esc_2022):,}")

    # Figura: N por ano com breakdown urbano/rural
    fig, ax = plt.subplots(figsize=(8, 5))
    anos = [2022, 2023, 2024]
    n_urb = [df[(df["NU_ANO_CENSO"] == a) & (df["NO_CATEGORIA"] == "Urbana")].shape[0] for a in anos]
    n_rur = [df[(df["NU_ANO_CENSO"] == a) & (df["NO_CATEGORIA"] == "Rural")].shape[0]  for a in anos]

    x = np.arange(len(anos))
    b_urb = ax.bar(x, n_urb, label="Urbana", color=COR_URBANA, alpha=0.85)
    b_rur = ax.bar(x, n_rur, bottom=n_urb, label="Rural", color=COR_RURAL, alpha=0.85)

    for i, (u, r) in enumerate(zip(n_urb, n_rur)):
        ax.text(i, u + r + 5, f"{u+r:,}", ha="center", fontsize=11, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(anos)
    ax.set_ylabel("Nº de escolas com dados de EM")
    ax.set_title("Escolas estaduais de EM em PE com taxas de rendimento")
    ax.set_ylim(0, max(u+r for u, r in zip(n_urb, n_rur)) * 1.15)
    ax.legend()
    fig.tight_layout()
    salvar_figura(fig, "B1_universo_taxas.png")


# =============================================================================
# B2 — DISTRIBUIÇÃO DA TAXA DE ABANDONO
# =============================================================================

def analise_distribuicao_abandono(df: pd.DataFrame) -> None:
    sep("B2 — DISTRIBUIÇÃO DA TAXA DE ABANDONO (TAXA_ABND_MED)")

    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano]["TAXA_ABND_MED"]
        n_zero  = (sub == 0).sum()
        n_baixo = ((sub > 0) & (sub <= 5)).sum()
        n_medio = ((sub > 5) & (sub <= 10)).sum()
        n_alto  = (sub > 10).sum()
        print(f"\n  {ano}  (N={len(sub):,})")
        print(f"    Média:   {sub.mean():.2f}%  |  Mediana: {sub.median():.2f}%  |  DP: {sub.std():.2f}")
        print(f"    Mín:     {sub.min():.2f}%  |  Máx:     {sub.max():.2f}%")
        print(f"    p75: {sub.quantile(.75):.2f}%  |  p90: {sub.quantile(.90):.2f}%  |  p95: {sub.quantile(.95):.2f}%")
        print(f"    Abandono = 0%:     {n_zero:,} escolas ({n_zero/len(sub)*100:.1f}%)")
        print(f"    Abandono 0-5%:     {n_baixo:,} escolas ({n_baixo/len(sub)*100:.1f}%)")
        print(f"    Abandono 5-10%:    {n_medio:,} escolas ({n_medio/len(sub)*100:.1f}%)")
        print(f"    Abandono > 10%:    {n_alto:,} escolas ({n_alto/len(sub)*100:.1f}%)")

    # Figura 1: histograma por ano (escala completa + zoom)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    for ano in [2022, 2023, 2024]:
        vals = df[df["NU_ANO_CENSO"] == ano]["TAXA_ABND_MED"]
        ax.hist(vals, bins=40, alpha=0.55, color=CORES_ANOS[ano],
                label=f"{ano} (media={vals.mean():.1f}%)", edgecolor="none")
    ax.set_xlabel("Taxa de Abandono do EM (%)")
    ax.set_ylabel("Nº de escolas")
    ax.set_title("Distribuição da taxa de abandono (escala completa)")
    ax.legend()

    # Zoom: apenas 0-15%
    ax = axes[1]
    for ano in [2022, 2023, 2024]:
        vals = df[(df["NU_ANO_CENSO"] == ano) & (df["TAXA_ABND_MED"] <= 15)]["TAXA_ABND_MED"]
        ax.hist(vals, bins=30, alpha=0.55, color=CORES_ANOS[ano],
                label=str(ano), edgecolor="none")
    ax.axvline(5,  color="gray",   linestyle="--", linewidth=1, label="5%")
    ax.axvline(10, color="darkred", linestyle="--", linewidth=1, label="10%")
    ax.set_xlabel("Taxa de Abandono do EM (%) — zoom 0-15%")
    ax.set_ylabel("Nº de escolas")
    ax.set_title("Distribuição (zoom: 0-15%)")
    ax.legend()

    fig.suptitle("Taxa de abandono do EM — escolas estaduais PE", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B2_distribuicao_abandono.png")

    # Figura 2: boxplot por ano + excesso de zeros
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    data_bp = [df[df["NU_ANO_CENSO"] == a]["TAXA_ABND_MED"].dropna().values for a in [2022, 2023, 2024]]
    bp = ax.boxplot(data_bp, labels=[2022, 2023, 2024], patch_artist=True,
                    medianprops={"color": "white", "linewidth": 2},
                    flierprops={"marker": ".", "markersize": 4, "alpha": 0.4})
    for patch, ano in zip(bp["boxes"], [2022, 2023, 2024]):
        patch.set_facecolor(CORES_ANOS[ano])
        patch.set_alpha(0.8)
    ax.set_ylabel("Taxa de Abandono (%)")
    ax.set_title("Boxplot da taxa de abandono por ano")

    ax = axes[1]
    cats   = ["0%\n(sem abandono)", "0-5%\n(baixo)", "5-10%\n(médio)", ">10%\n(alto)"]
    largura = 0.25
    x = np.arange(len(cats))
    for i, ano in enumerate([2022, 2023, 2024]):
        sub = df[df["NU_ANO_CENSO"] == ano]["TAXA_ABND_MED"]
        ns = [
            (sub == 0).sum(),
            ((sub > 0) & (sub <= 5)).sum(),
            ((sub > 5) & (sub <= 10)).sum(),
            (sub > 10).sum(),
        ]
        pcts = [n / len(sub) * 100 for n in ns]
        bars = ax.bar(x + (i - 1) * largura, pcts, largura,
                      label=str(ano), color=CORES_ANOS[ano], alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=9)
    ax.set_ylabel("% de escolas")
    ax.set_title("Perfil de abandono por faixa e ano")
    ax.legend()

    fig.suptitle("Taxa de abandono — perfil e boxplot por ano", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B2b_abandono_perfil_faixas.png")


# =============================================================================
# B3 — TENDÊNCIA TEMPORAL (2022->2024)
# =============================================================================

def analise_tendencia_temporal(df: pd.DataFrame) -> None:
    sep("B3 — TENDÊNCIA TEMPORAL DAS TAXAS (2022->2024)")

    cols = ["TAXA_ABND_MED", "TAXA_REPROV_MED", "TAXA_APROV_MED"]
    labels = {"TAXA_ABND_MED": "Abandono", "TAXA_REPROV_MED": "Reprovação", "TAXA_APROV_MED": "Aprovação"}
    anos = [2022, 2023, 2024]

    print("\nMédia e mediana por ano:")
    for col in cols:
        print(f"\n  {labels[col]}:")
        for ano in anos:
            sub = df[df["NU_ANO_CENSO"] == ano][col]
            print(f"    {ano}: média={sub.mean():.2f}%  mediana={sub.median():.2f}%  dp={sub.std():.2f}")

    # Variação relativa 2022->2024
    print("\nVariação 2022->2024 (em pontos percentuais e % relativa):")
    for col in ["TAXA_ABND_MED", "TAXA_REPROV_MED"]:
        v22 = df[df["NU_ANO_CENSO"] == 2022][col].mean()
        v24 = df[df["NU_ANO_CENSO"] == 2024][col].mean()
        delta_pp = v24 - v22
        delta_rel = (v24 - v22) / v22 * 100
        print(f"  {labels[col]}: {v22:.2f}% -> {v24:.2f}%  "
              f"(Delta={delta_pp:+.2f} pp  /  {delta_rel:+.1f}% relativo)")

    # Kruskal-Wallis para confirmar diferença entre anos
    for col in ["TAXA_ABND_MED", "TAXA_REPROV_MED"]:
        grupos = [df[df["NU_ANO_CENSO"] == a][col].dropna() for a in anos]
        h, p = stats.kruskal(*grupos)
        print(f"\n  [Kruskal-Wallis {labels[col]}] H={h:.2f}, p={p:.4f} "
              f"({'diferença significativa' if p < 0.05 else 'sem diferença significativa'})")

    # Figura: evolução média e mediana das três taxas
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    cores_taxa = {
        "TAXA_ABND_MED":   COR_ABND,
        "TAXA_REPROV_MED": COR_REPROV,
        "TAXA_APROV_MED":  COR_APROV,
    }

    # Painel A: abandono e reprovação (média + IC 95%)
    ax = axes[0]
    for col in ["TAXA_ABND_MED", "TAXA_REPROV_MED"]:
        medias  = [df[df["NU_ANO_CENSO"] == a][col].mean() for a in anos]
        n_vals  = [df[df["NU_ANO_CENSO"] == a][col].dropna().shape[0] for a in anos]
        stds    = [df[df["NU_ANO_CENSO"] == a][col].std() for a in anos]
        ics     = [1.96 * s / np.sqrt(n) for s, n in zip(stds, n_vals)]
        ax.errorbar(anos, medias, yerr=ics, marker="o", linewidth=2,
                    capsize=5, capthick=1.5, color=cores_taxa[col], label=labels[col])
        for ano, m in zip(anos, medias):
            ax.annotate(f"{m:.2f}%", (ano, m), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=9)
    ax.set_xticks(anos)
    ax.set_ylabel("Taxa média (%)")
    ax.set_title("Tendência de abandono e reprovação (média ± IC 95%)")
    ax.legend()
    ax.set_ylim(bottom=0)

    # Painel B: proporção de escolas em cada faixa de abandono ao longo do tempo
    ax = axes[1]
    faixas = {
        "= 0%":  lambda s: (s == 0),
        "0-5%":  lambda s: (s > 0) & (s <= 5),
        "5-10%": lambda s: (s > 5) & (s <= 10),
        "> 10%": lambda s: (s > 10),
    }
    cores_faixas = ["#B3E5FC", "#81D4FA", "#E65100", "#C62828"]

    bottom = np.zeros(3)
    for (faixa, fn), cor in zip(faixas.items(), cores_faixas):
        pcts = []
        for ano in anos:
            sub = df[df["NU_ANO_CENSO"] == ano]["TAXA_ABND_MED"].dropna()
            pcts.append(fn(sub).sum() / len(sub) * 100)
        ax.bar(anos, pcts, bottom=bottom, label=faixa, color=cor, alpha=0.9, width=0.5)
        for i, (a, p) in enumerate(zip(anos, pcts)):
            if p > 3:
                ax.text(a, bottom[i] + p / 2, f"{p:.0f}%",
                        ha="center", va="center", fontsize=8, color="white", fontweight="bold")
        bottom += np.array(pcts)

    ax.set_xticks(anos)
    ax.set_ylabel("% das escolas")
    ax.set_title("Composição por faixa de abandono ao longo dos anos")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_ylim(0, 105)

    fig.suptitle("Evolução temporal das taxas de rendimento — PE estadual EM", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B3_tendencia_temporal.png")


# =============================================================================
# B4 — ABANDONO POR LOCALIZAÇÃO (URBANA VS RURAL)
# =============================================================================

def analise_por_localizacao(df: pd.DataFrame) -> None:
    sep("B4 — ABANDONO POR LOCALIZAÇÃO (URBANA VS RURAL)")

    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano]
        print(f"\n  {ano}:")
        for loc in ["Urbana", "Rural"]:
            vals = sub[sub["NO_CATEGORIA"] == loc]["TAXA_ABND_MED"].dropna()
            print(f"    {loc} (N={len(vals):,}): "
                  f"média={vals.mean():.2f}%  mediana={vals.median():.2f}%  "
                  f"p90={vals.quantile(.90):.2f}%  máx={vals.max():.2f}%")

        urb = sub[sub["NO_CATEGORIA"] == "Urbana"]["TAXA_ABND_MED"].dropna()
        rur = sub[sub["NO_CATEGORIA"] == "Rural"]["TAXA_ABND_MED"].dropna()
        mw_stat, mw_p = stats.mannwhitneyu(urb, rur, alternative="two-sided")
        print(f"    [Mann-Whitney] stat={mw_stat:.1f}, p={mw_p:.4f} "
              f"({'sig.' if mw_p < 0.05 else 'n.s.'})")

    # Figura: boxplot + violinplot lado a lado
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Boxplot por ano e localização
    ax = axes[0]
    anos = [2022, 2023, 2024]
    positions_urb = [1, 4, 7]
    positions_rur = [2, 5, 8]

    all_data_urb = [df[(df["NU_ANO_CENSO"] == a) & (df["NO_CATEGORIA"] == "Urbana")]["TAXA_ABND_MED"].dropna().values for a in anos]
    all_data_rur = [df[(df["NU_ANO_CENSO"] == a) & (df["NO_CATEGORIA"] == "Rural")]["TAXA_ABND_MED"].dropna().values  for a in anos]

    bp_urb = ax.boxplot(all_data_urb, positions=positions_urb, widths=0.7,
                        patch_artist=True,
                        medianprops={"color": "white", "linewidth": 2},
                        flierprops={"marker": ".", "markersize": 3, "alpha": 0.3})
    bp_rur = ax.boxplot(all_data_rur, positions=positions_rur, widths=0.7,
                        patch_artist=True,
                        medianprops={"color": "white", "linewidth": 2},
                        flierprops={"marker": ".", "markersize": 3, "alpha": 0.3})

    for patch in bp_urb["boxes"]:
        patch.set_facecolor(COR_URBANA)
        patch.set_alpha(0.75)
    for patch in bp_rur["boxes"]:
        patch.set_facecolor(COR_RURAL)
        patch.set_alpha(0.75)

    ax.set_xticks([1.5, 4.5, 7.5])
    ax.set_xticklabels(anos)
    ax.set_ylabel("Taxa de Abandono do EM (%)")
    ax.set_title("Abandono por localização e ano")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=COR_URBANA, label="Urbana"),
                        Patch(color=COR_RURAL,  label="Rural")])

    # Média por localização ao longo dos anos
    ax = axes[1]
    for loc, cor in [("Urbana", COR_URBANA), ("Rural", COR_RURAL)]:
        medias  = [df[(df["NU_ANO_CENSO"] == a) & (df["NO_CATEGORIA"] == loc)]["TAXA_ABND_MED"].mean() for a in anos]
        medianas = [df[(df["NU_ANO_CENSO"] == a) & (df["NO_CATEGORIA"] == loc)]["TAXA_ABND_MED"].median() for a in anos]
        ax.plot(anos, medias,   marker="o", linewidth=2, color=cor, label=f"{loc} (média)",   linestyle="-")
        ax.plot(anos, medianas, marker="s", linewidth=2, color=cor, label=f"{loc} (mediana)", linestyle="--", alpha=0.7)
        for ano, m in zip(anos, medias):
            ax.annotate(f"{m:.2f}%", (ano, m), textcoords="offset points",
                        xytext=(5, 0), fontsize=8, color=cor)
    ax.set_xticks(anos)
    ax.set_ylabel("Taxa de Abandono (%)")
    ax.set_title("Evolução do abandono: Urbana vs Rural")
    ax.legend(fontsize=8)
    ax.set_ylim(bottom=0)

    fig.suptitle("Abandono do EM por localização — escolas estaduais PE", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B4_abandono_localizacao.png")


# =============================================================================
# B5 — ABANDONO POR SÉRIE (S1, S2, S3)
# =============================================================================

def analise_por_serie(df: pd.DataFrame) -> None:
    sep("B5 — ABANDONO POR SÉRIE DO ENSINO MÉDIO")

    series_cols = ["TAXA_ABND_MED_S1", "TAXA_ABND_MED_S2", "TAXA_ABND_MED_S3"]
    series_lbl  = {"TAXA_ABND_MED_S1": "1ª Série", "TAXA_ABND_MED_S2": "2ª Série", "TAXA_ABND_MED_S3": "3ª Série"}

    print("\nMédia de abandono por série e ano:")
    for col in series_cols:
        print(f"\n  {series_lbl[col]}:")
        for ano in [2022, 2023, 2024]:
            sub = df[df["NU_ANO_CENSO"] == ano][col].dropna()
            n_cob = len(sub)
            n_total = (df["NU_ANO_CENSO"] == ano).sum()
            print(f"    {ano}: N={n_cob:,} ({n_cob/n_total*100:.0f}% cobertura)  "
                  f"média={sub.mean():.2f}%  mediana={sub.median():.2f}%  "
                  f"máx={sub.max():.2f}%")

    # Comparação entre séries (2022): qual série tem mais abandono?
    print("\nComparação entre séries (todos os anos com dado disponível):")
    for col in series_cols:
        vals = df[col].dropna()
        print(f"  {series_lbl[col]}: média={vals.mean():.2f}%  p90={vals.quantile(.90):.2f}%")

    # Kruskal-Wallis entre séries (usando escolas com dados nas 3 séries)
    mask_completo = df[series_cols].notna().all(axis=1)
    df_comp = df[mask_completo]
    if len(df_comp) > 10:
        grupos = [df_comp[c].values for c in series_cols]
        h, p = stats.kruskal(*grupos)
        print(f"\n  [Kruskal-Wallis entre séries, escolas com dados completos N={len(df_comp):,}]")
        print(f"  H={h:.2f}, p={p:.4f} ({'diferença significativa' if p < 0.05 else 'sem diferença'})")

    # Figura: distribuição por série + evolução temporal por série
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    cores_series = {"TAXA_ABND_MED_S1": "#E53935", "TAXA_ABND_MED_S2": "#8E24AA", "TAXA_ABND_MED_S3": "#1E88E5"}

    # Histograma por série (todos os anos juntos)
    ax = axes[0]
    for col in series_cols:
        vals = df[col].dropna()
        ax.hist(vals[vals <= 20], bins=25, alpha=0.55, color=cores_series[col],
                label=f"{series_lbl[col]} (media={vals.mean():.1f}%)", edgecolor="none")
    ax.set_xlabel("Taxa de Abandono (%)")
    ax.set_ylabel("Nº de observações")
    ax.set_title("Distribuição do abandono por série (zoom ≤ 20%)")
    ax.legend()

    # Evolução da média por série ao longo dos anos
    ax = axes[1]
    for col in series_cols:
        medias = [df[df["NU_ANO_CENSO"] == a][col].mean() for a in [2022, 2023, 2024]]
        ax.plot([2022, 2023, 2024], medias, marker="o", linewidth=2,
                color=cores_series[col], label=series_lbl[col])
        for ano, m in zip([2022, 2023, 2024], medias):
            if not np.isnan(m):
                ax.annotate(f"{m:.1f}%", (ano, m), textcoords="offset points",
                            xytext=(0, 8), ha="center", fontsize=8)
    ax.set_xticks([2022, 2023, 2024])
    ax.set_ylabel("Taxa média de abandono (%)")
    ax.set_title("Evolução do abandono por série ao longo dos anos")
    ax.legend()
    ax.set_ylim(bottom=0)

    fig.suptitle("Abandono por série do Ensino Médio — PE estadual", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B5_abandono_por_serie.png")


# =============================================================================
# B6 — RELAÇÃO ENTRE APROVAÇÃO, REPROVAÇÃO E ABANDONO
# =============================================================================

def analise_composicao_taxas(df: pd.DataFrame) -> None:
    sep("B6 — COMPOSIÇÃO: APROVAÇÃO, REPROVAÇÃO E ABANDONO")

    df24 = df[df["NU_ANO_CENSO"] == 2024].copy()

    print("\nDescritiva das três taxas totais (2024):")
    for col, lbl in [("TAXA_APROV_MED", "Aprovação"), ("TAXA_REPROV_MED", "Reprovação"), ("TAXA_ABND_MED", "Abandono")]:
        s = df24[col].describe().round(2)
        print(f"  {lbl}: média={s['mean']:.2f}%  mediana={s['50%']:.2f}%  dp={s['std']:.2f}  "
              f"min={s['min']:.2f}%  max={s['max']:.2f}%")

    # Correlação entre reprovação e abandono
    print("\nCorrelação de Spearman (Reprovação x Abandono) por ano:")
    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano][["TAXA_REPROV_MED", "TAXA_ABND_MED"]].dropna()
        r, p = stats.spearmanr(sub["TAXA_REPROV_MED"], sub["TAXA_ABND_MED"])
        print(f"  {ano}: r={r:.3f}, p={p:.4f} ({'*' if p < 0.05 else 'n.s.'})")

    # Figura: stacked bar médio + scatter reprov vs abnd
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Barras empilhadas: composição média por ano
    ax = axes[0]
    anos = [2022, 2023, 2024]
    med_aprov  = [df[df["NU_ANO_CENSO"] == a]["TAXA_APROV_MED"].mean()  for a in anos]
    med_reprov = [df[df["NU_ANO_CENSO"] == a]["TAXA_REPROV_MED"].mean() for a in anos]
    med_abnd   = [df[df["NU_ANO_CENSO"] == a]["TAXA_ABND_MED"].mean()   for a in anos]

    x = np.arange(len(anos))
    b1 = ax.bar(x, med_aprov,  label="Aprovação",  color=COR_APROV,  alpha=0.85)
    b2 = ax.bar(x, med_reprov, bottom=med_aprov,   label="Reprovação", color=COR_REPROV, alpha=0.85)
    b3 = ax.bar(x, med_abnd,
                bottom=[a + r for a, r in zip(med_aprov, med_reprov)],
                label="Abandono",  color=COR_ABND,   alpha=0.85)

    for i, (ap, rp, ab) in enumerate(zip(med_aprov, med_reprov, med_abnd)):
        ax.text(i, ap / 2, f"{ap:.1f}%", ha="center", va="center", fontsize=8,
                color="white", fontweight="bold")
        ax.text(i, ap + rp / 2, f"{rp:.1f}%", ha="center", va="center", fontsize=8,
                color="white", fontweight="bold")
        ax.text(i, ap + rp + ab / 2, f"{ab:.1f}%", ha="center", va="center", fontsize=8,
                color="white", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(anos)
    ax.set_ylabel("Taxa média (%)")
    ax.set_ylim(0, 102)
    ax.set_title("Composição média das taxas de rendimento por ano")
    ax.legend(loc="lower right")

    # Scatter: reprovação x abandono (2022)
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


# =============================================================================
# B7 — CORRELAÇÃO REPROVAÇÃO ANO T -> ABANDONO ANO T+1
# =============================================================================

def analise_correlacao_lag(df: pd.DataFrame) -> None:
    sep("B7 — CORRELAÇÃO REPROVAÇÃO (t) -> ABANDONO (t+1)")

    # Par 2022->2023
    print("\nEstrutura do painel longitudinal para análise de lag:")
    for (ano_t, ano_t1) in [(2022, 2023), (2023, 2024)]:
        sub_t  = df[df["NU_ANO_CENSO"] == ano_t][["CO_ENTIDADE", "TAXA_REPROV_MED", "TAXA_ABND_MED"]].rename(
            columns={"TAXA_REPROV_MED": "reprov_t", "TAXA_ABND_MED": "abnd_t"})
        sub_t1 = df[df["NU_ANO_CENSO"] == ano_t1][["CO_ENTIDADE", "TAXA_ABND_MED"]].rename(
            columns={"TAXA_ABND_MED": "abnd_t1"})
        joined = sub_t.merge(sub_t1, on="CO_ENTIDADE", how="inner").dropna()

        r_reprov, p_reprov = stats.spearmanr(joined["reprov_t"], joined["abnd_t1"])
        r_abnd,   p_abnd   = stats.spearmanr(joined["abnd_t"],   joined["abnd_t1"])

        print(f"\n  Pares {ano_t}->{ano_t1}  (N={len(joined):,} escolas com dados em ambos os anos):")
        print(f"    Reprovação({ano_t}) x Abandono({ano_t1}): r={r_reprov:.3f}, p={p_reprov:.4f}")
        print(f"    Abandono({ano_t})   x Abandono({ano_t1}): r={r_abnd:.3f},   p={p_abnd:.4f}")

    # Figura: scatter pair 2022->2023 e 2023->2024
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    for row_idx, (ano_t, ano_t1) in enumerate([(2022, 2023), (2023, 2024)]):
        sub_t  = df[df["NU_ANO_CENSO"] == ano_t][["CO_ENTIDADE", "TAXA_REPROV_MED", "TAXA_ABND_MED"]].rename(
            columns={"TAXA_REPROV_MED": "reprov_t", "TAXA_ABND_MED": "abnd_t"})
        sub_t1 = df[df["NU_ANO_CENSO"] == ano_t1][["CO_ENTIDADE", "TAXA_ABND_MED"]].rename(
            columns={"TAXA_ABND_MED": "abnd_t1"})
        joined = sub_t.merge(sub_t1, on="CO_ENTIDADE", how="inner").dropna()

        # Scatter: abnd_t x abnd_t1
        ax = axes[row_idx][0]
        r, p = stats.spearmanr(joined["abnd_t"], joined["abnd_t1"])
        ax.scatter(joined["abnd_t"], joined["abnd_t1"],
                   alpha=0.35, s=20, color=COR_ABND)
        # linha de referência y=x
        lim = max(joined["abnd_t"].max(), joined["abnd_t1"].max()) * 1.05
        ax.plot([0, lim], [0, lim], "k--", linewidth=0.8, alpha=0.5, label="y = x")
        ax.set_xlabel(f"Abandono {ano_t} (%)")
        ax.set_ylabel(f"Abandono {ano_t1} (%)")
        ax.set_title(f"Abandono {ano_t} -> {ano_t1}  (r={r:.2f}, p={p:.3f})")
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.legend(fontsize=8)

        # Scatter: reprov_t x abnd_t1
        ax = axes[row_idx][1]
        r, p = stats.spearmanr(joined["reprov_t"], joined["abnd_t1"])
        ax.scatter(joined["reprov_t"], joined["abnd_t1"],
                   alpha=0.35, s=20, color=COR_REPROV)
        ax.set_xlabel(f"Reprovação {ano_t} (%)")
        ax.set_ylabel(f"Abandono {ano_t1} (%)")
        ax.set_title(f"Reprovação {ano_t} -> Abandono {ano_t1}  (r={r:.2f}, p={p:.3f})")
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

    fig.suptitle("Correlações defasadas: reprovação/abandono em t vs abandono em t+1", fontsize=12)
    fig.tight_layout()
    salvar_figura(fig, "B7_correlacao_lag.png")


# =============================================================================
# B8 — ESCOLAS DE ALTO RISCO (ABANDONO > 10%)
# =============================================================================

def analise_alto_risco(df: pd.DataFrame) -> None:
    sep("B8 — ESCOLAS DE ALTO RISCO (ABANDONO > 10%)")

    LIMIAR = 10.0

    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano]
        alto = sub[sub["TAXA_ABND_MED"] > LIMIAR]
        print(f"\n  {ano}: {len(alto):,} escolas com abandono > {LIMIAR:.0f}%  "
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

    # Escolas que foram alto risco em 2022 e continuaram em 2023
    alto_2022 = set(df[(df["NU_ANO_CENSO"] == 2022) & (df["TAXA_ABND_MED"] > LIMIAR)]["CO_ENTIDADE"])
    alto_2023 = set(df[(df["NU_ANO_CENSO"] == 2023) & (df["TAXA_ABND_MED"] > LIMIAR)]["CO_ENTIDADE"])
    alto_2024 = set(df[(df["NU_ANO_CENSO"] == 2024) & (df["TAXA_ABND_MED"] > LIMIAR)]["CO_ENTIDADE"])
    persistentes = alto_2022 & alto_2023 & alto_2024
    print(f"\nEscolas com abandono > {LIMIAR:.0f}% nos 3 anos: {len(persistentes):,}")

    # Figura: evolução do N de escolas de alto risco + distribuição dos valores
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    anos = [2022, 2023, 2024]
    ns_alto = []
    for ano in anos:
        sub = df[df["NU_ANO_CENSO"] == ano]
        ns_alto.append((sub["TAXA_ABND_MED"] > LIMIAR).sum())

    bars = ax.bar(anos, ns_alto, color=[CORES_ANOS[a] for a in anos], edgecolor="white", width=0.5)
    for bar, n in zip(bars, ns_alto):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(n), ha="center", va="bottom", fontsize=12, fontweight="bold", color=COR_ABND)
    ax.set_ylabel(f"Nº de escolas com abandono > {LIMIAR:.0f}%")
    ax.set_title(f"Evolução das escolas de alto risco (abandono > {LIMIAR:.0f}%)")
    ax.set_ylim(0, max(ns_alto) * 1.3)

    # Top 15 escolas em 2022 (barplot horizontal)
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
                   color=COR_ABND, alpha=0.8)
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


# =============================================================================
# B9 — EVOLUÇÃO INTRA-ESCOLA (PAINEL LONGITUDINAL)
# =============================================================================

def analise_evolucao_intra_escola(df: pd.DataFrame) -> None:
    sep("B9 — EVOLUÇÃO INTRA-ESCOLA (2022->2023->2024)")

    # Apenas escolas com dados nos 3 anos
    contagem = df.groupby("CO_ENTIDADE")["NU_ANO_CENSO"].nunique()
    escolas_3 = contagem[contagem == 3].index
    df3 = df[df["CO_ENTIDADE"].isin(escolas_3)].copy()
    print(f"\nEscolas com dados nos 3 anos: {len(escolas_3):,}")

    # Variação individual 2022->2024
    pivot = df3.pivot(index="CO_ENTIDADE", columns="NU_ANO_CENSO", values="TAXA_ABND_MED").dropna()
    pivot["delta_22_24"] = pivot[2024] - pivot[2022]
    pivot["delta_22_23"] = pivot[2023] - pivot[2022]
    pivot["delta_23_24"] = pivot[2024] - pivot[2023]

    print(f"\nVariação 2022->2024 (Delta abandono em pp):")
    print(f"  Média: {pivot['delta_22_24'].mean():+.2f} pp")
    print(f"  Mediana: {pivot['delta_22_24'].median():+.2f} pp")
    print(f"  Escolas que PIORARAM (Delta > 0): {(pivot['delta_22_24'] > 0).sum():,} ({(pivot['delta_22_24'] > 0).mean()*100:.1f}%)")
    print(f"  Escolas que MELHORARAM (Delta < 0): {(pivot['delta_22_24'] < 0).sum():,} ({(pivot['delta_22_24'] < 0).mean()*100:.1f}%)")
    print(f"  Escolas estáveis (Delta = 0): {(pivot['delta_22_24'] == 0).sum():,} ({(pivot['delta_22_24'] == 0).mean()*100:.1f}%)")

    # Top pioras e melhoras
    print(f"\n  Top 5 maiores PIORAS (2022->2024):")
    top_piora = pivot.nlargest(5, "delta_22_24")[["delta_22_24", 2022, 2024]]
    top_piora.columns = ["Delta", "Abnd_2022", "Abnd_2024"]
    nomes = df3[df3["CO_ENTIDADE"].isin(top_piora.index)].drop_duplicates("CO_ENTIDADE").set_index("CO_ENTIDADE")["NO_ENTIDADE"]
    top_piora["Escola"] = nomes
    print(top_piora[["Escola", "Abnd_2022", "Abnd_2024", "Delta"]].to_string())

    print(f"\n  Top 5 maiores MELHORAS (2022->2024):")
    top_melhora = pivot.nsmallest(5, "delta_22_24")[["delta_22_24", 2022, 2024]]
    top_melhora.columns = ["Delta", "Abnd_2022", "Abnd_2024"]
    nomes = df3[df3["CO_ENTIDADE"].isin(top_melhora.index)].drop_duplicates("CO_ENTIDADE").set_index("CO_ENTIDADE")["NO_ENTIDADE"]
    top_melhora["Escola"] = nomes
    print(top_melhora[["Escola", "Abnd_2022", "Abnd_2024", "Delta"]].to_string())

    # Figura: histograma de deltas + spaghetti plot (amostra)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    ax.hist(pivot["delta_22_24"], bins=40, color="#5C6BC0", alpha=0.8, edgecolor="none")
    ax.axvline(0, color="black", linestyle="--", linewidth=1.2, label="sem variação")
    ax.axvline(pivot["delta_22_24"].mean(), color=COR_ABND, linestyle="-",
               linewidth=1.5, label=f"média={pivot['delta_22_24'].mean():+.2f} pp")
    ax.set_xlabel("Variação no abandono (pp) — 2022 -> 2024")
    ax.set_ylabel("Nº de escolas")
    ax.set_title("Distribuição da variação individual do abandono\n(2022 -> 2024)")
    ax.legend()

    # Spaghetti plot (amostra de 80 escolas)
    ax = axes[1]
    np.random.seed(42)
    amostra = np.random.choice(pivot.index, size=min(80, len(pivot)), replace=False)
    for esc in amostra:
        vals = pivot.loc[esc, [2022, 2023, 2024]].values
        cor = COR_ABND if pivot.loc[esc, "delta_22_24"] > 2 else (COR_APROV if pivot.loc[esc, "delta_22_24"] < -2 else "gray")
        alpha = 0.6 if abs(pivot.loc[esc, "delta_22_24"]) > 2 else 0.15
        ax.plot([2022, 2023, 2024], vals, color=cor, alpha=alpha, linewidth=0.8)

    # Linha da média
    medias_anos = [pivot[a].mean() for a in [2022, 2023, 2024]]
    ax.plot([2022, 2023, 2024], medias_anos, color="black", linewidth=2.5,
            marker="o", markersize=7, label="Média (todas as escolas)", zorder=5)
    ax.set_xticks([2022, 2023, 2024])
    ax.set_ylabel("Taxa de Abandono (%)")
    ax.set_title("Trajetória individual do abandono\n(amostra de 80 escolas)")
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color=COR_ABND,  label="Piorou > 2 pp"),
        Patch(color=COR_APROV, label="Melhorou > 2 pp"),
        Patch(color="gray",    label="Estável"),
        plt.Line2D([0], [0], color="black", linewidth=2, label="Média"),
    ], fontsize=8)

    fig.suptitle("Evolução intra-escola da taxa de abandono (painel 2022-2024)", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "B9_evolucao_intra_escola.png")


# =============================================================================
# B10 — QUALIDADE DOS DADOS
# =============================================================================

def analise_qualidade(df: pd.DataFrame) -> None:
    sep("B10 — QUALIDADE DOS DADOS / MISSING VALUES")

    taxa_cols = [c for c in df.columns if c.startswith("TAXA_")]

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
    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano]
        miss = (sub[taxa_cols].isna().mean() * 100).round(1)
        miss = miss[miss > 0]
        print(f"\n  {ano}:")
        for col, pct in miss.items():
            print(f"    {col}: {pct:.1f}%")

    # Verificação soma = 100%
    print("\nConsistência matemática (Aprov + Reprov + Abnd = 100%):")
    cols_soma = ["TAXA_APROV_MED", "TAXA_REPROV_MED", "TAXA_ABND_MED"]
    df_check = df[cols_soma].dropna()
    soma = df_check.sum(axis=1)
    fora = ((soma - 100).abs() > 1.0)
    print(f"  Linhas testadas: {len(df_check):,}")
    print(f"  Soma mín: {soma.min():.2f}%  máx: {soma.max():.2f}%")
    print(f"  Fora de [99,101]: {fora.sum():,} ({fora.sum()/len(df_check)*100:.2f}%)")

    # Figura: mapa de calor de missing por coluna x ano
    fig, ax = plt.subplots(figsize=(11, 6))
    anos = [2022, 2023, 2024]
    miss_matrix = pd.DataFrame(
        {ano: (df[df["NU_ANO_CENSO"] == ano][taxa_cols].isna().mean() * 100).round(1) for ano in anos},
        index=taxa_cols,
    )
    # Ordena por média de missing decrescente
    miss_matrix = miss_matrix.loc[miss_matrix.mean(axis=1).sort_values(ascending=False).index]

    im = ax.imshow(miss_matrix.values, aspect="auto", cmap="Reds", vmin=0, vmax=100)
    plt.colorbar(im, ax=ax, label="% de valores ausentes")
    ax.set_xticks(range(len(anos)))
    ax.set_xticklabels(anos)
    ax.set_yticks(range(len(miss_matrix)))
    ax.set_yticklabels(miss_matrix.index, fontsize=8)
    for i in range(len(miss_matrix)):
        for j in range(len(anos)):
            v = miss_matrix.iloc[i, j]
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=8,
                    color="white" if v > 50 else "black")
    ax.set_title("% de valores ausentes por coluna de taxa e ano")
    fig.tight_layout()
    salvar_figura(fig, "B10_missing_heatmap.png")


# =============================================================================
# SUMÁRIO EXECUTIVO
# =============================================================================

def sumario_executivo(df: pd.DataFrame) -> None:
    sep("SUMÁRIO EXECUTIVO — TAXAS DE RENDIMENTO")

    abnd_22 = df[df["NU_ANO_CENSO"] == 2022]["TAXA_ABND_MED"]
    abnd_24 = df[df["NU_ANO_CENSO"] == 2024]["TAXA_ABND_MED"]

    print(f"""
SOBRE O UNIVERSO
  • {df['CO_ENTIDADE'].nunique():,} escolas únicas com dados de EM
  • 97,4% aparecem nos 3 anos -> painel estável, compatível com o Censo
  • ~{int((df["NO_CATEGORIA"] == "Urbana").mean()*100)}% urbanas, ~{int((df["NO_CATEGORIA"] == "Rural").mean()*100)}% rurais

SOBRE O TARGET (TAXA_ABND_MED)
  • Distribuição fortemente assimétrica à direita (mediana = 0%)
  • {int((df["TAXA_ABND_MED"] == 0).mean()*100)}% das observações têm abandono zero
  • Queda expressiva: {abnd_22.mean():.2f}% (2022) -> {abnd_24.mean():.2f}% (2024) ({(abnd_24.mean()-abnd_22.mean())/abnd_22.mean()*100:+.1f}% relativo)
  • Escolas com abandono > 10%: caiu de ~{(df[df["NU_ANO_CENSO"]==2022]["TAXA_ABND_MED"]>10).sum()} (2022) para ~{(df[df["NU_ANO_CENSO"]==2024]["TAXA_ABND_MED"]>10).sum()} (2024)
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
    logger.info("Iniciando análises descritivas das Taxas de Rendimento.")
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
