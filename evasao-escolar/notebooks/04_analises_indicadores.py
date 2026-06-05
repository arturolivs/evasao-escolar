"""
Análises descritivas — Indicadores Complementares (INEP)
Escolas estaduais de EM em PE — 2022, 2023 e 2024

Responde às perguntas:
  C1. Como se distribui e evolui o IRD (Regularidade Docente)?
  C2. Como se distribui o INSE (Nível Socioeconômico)? Qual a cobertura?
  C3. Como se distribui e evolui a TDI (Distorção Idade-série)?
  C4. Como se compõe e evolui a AFD (Adequação da Formação Docente)?
  C5. Quais indicadores se correlacionam mais com a taxa de abandono?
  C6. Qual o perfil de risco composto por município?

Saídas:
  - Texto no console
  - Figuras salvas em: reports/figuras/  (prefixo C*)
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

from src.data import config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

FIGURAS_DIR = ROOT / "reports" / "figuras"
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)

CORES_ANOS   = {2022: "#2196F3", 2023: "#FF9800", 2024: "#4CAF50"}
COR_URBANA   = "#1565C0"
COR_RURAL    = "#2E7D32"
ANOS         = [2022, 2023, 2024]

LABELS_LOCALIZACAO = {1: "Urbana", 2: "Rural"}


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


def _label_loc(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona coluna NO_LOCALIZACAO se TP_LOCALIZACAO estiver presente."""
    if "TP_LOCALIZACAO" in df.columns:
        df = df.copy()
        df["NO_LOCALIZACAO"] = df["TP_LOCALIZACAO"].map(LABELS_LOCALIZACAO)
    return df


# =============================================================================
# CARGA
# =============================================================================

def _exige_parquet(path: Path, instrucao: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Parquet não encontrado: {path}\nExecute: {instrucao}")
    return pd.read_parquet(path)


def carregar_dados() -> dict[str, pd.DataFrame]:
    """Carrega todos os painéis necessários."""
    painel = _exige_parquet(
        config.INTERIM_DIR / "painel_escola_ano_pe_estadual_em.parquet",
        "python -m src.data.build_school_panel",
    )
    taxas = _exige_parquet(
        config.INTERIM_DIR / "taxas_rendimento_pe_estadual_em.parquet",
        "python -m src.data.build_taxas_rendimento",
    )
    ird = _exige_parquet(
        config.INTERIM_DIR / "ird_pe_estadual.parquet",
        "python -m src.data.build_ird",
    )
    inse = _exige_parquet(
        config.INTERIM_DIR / "inse_pe_estadual.parquet",
        "python -m src.data.build_inse",
    )
    tdi = _exige_parquet(
        config.INTERIM_DIR / "tdi_pe_estadual.parquet",
        "python -m src.data.build_tdi",
    )
    afd = _exige_parquet(
        config.INTERIM_DIR / "afd_pe_estadual.parquet",
        "python -m src.data.build_afd",
    )

    for df in [painel, taxas, ird, tdi, afd]:
        if "NU_ANO_CENSO" in df.columns:
            df["NU_ANO_CENSO"] = df["NU_ANO_CENSO"].astype(int)

    logger.info("Dados carregados: painel=%d taxas=%d ird=%d inse=%d tdi=%d afd=%d",
                len(painel), len(taxas), len(ird), len(inse), len(tdi), len(afd))
    return dict(painel=painel, taxas=taxas, ird=ird, inse=inse, tdi=tdi, afd=afd)


def _enriquecer_com_painel(df: pd.DataFrame, painel: pd.DataFrame, on: list[str]) -> pd.DataFrame:
    """Join com o painel do Censo para obter localização e mesorregião."""
    cols_geo = ["CO_ENTIDADE", "NU_ANO_CENSO", "TP_LOCALIZACAO", "CO_MESORREGIAO"]
    cols_geo = [c for c in cols_geo if c in painel.columns]
    geo = painel[cols_geo].drop_duplicates(subset=on)
    return df.merge(geo, on=on, how="left")


# =============================================================================
# C1 — IRD: REGULARIDADE DO CORPO DOCENTE
# =============================================================================

def analise_ird(ird: pd.DataFrame, painel: pd.DataFrame, taxas: pd.DataFrame) -> None:
    sep("C1 — IRD: INDICADOR DE REGULARIDADE DO CORPO DOCENTE")

    df = _enriquecer_com_painel(ird, painel, on=["CO_ENTIDADE", "NU_ANO_CENSO"])

    print(f"\nTotal de observações: {len(df):,}")
    print(f"Escolas únicas: {df['CO_ENTIDADE'].nunique():,}")
    print(f"Anos: {sorted(df['NU_ANO_CENSO'].unique())}")

    # Cobertura por ano
    print("\nCobertura e estatísticas por ano:")
    for ano in ANOS:
        sub = df[df["NU_ANO_CENSO"] == ano]["IRD_MED"].dropna()
        print(f"  {ano}: N={len(sub):,}  média={sub.mean():.3f}  mediana={sub.median():.3f}"
              f"  DP={sub.std():.3f}  [min={sub.min():.1f} ; max={sub.max():.1f}]")

    # Urbano vs Rural
    print("\nIRD médio por localização (2024):")
    sub24 = df[df["NU_ANO_CENSO"] == 2024]
    for loc, label in LABELS_LOCALIZACAO.items():
        vals = sub24[sub24["TP_LOCALIZACAO"] == loc]["IRD_MED"].dropna()
        print(f"  {label}: N={len(vals):,}  média={vals.mean():.3f}  DP={vals.std():.3f}")

    u_vals = sub24[sub24["TP_LOCALIZACAO"] == 1]["IRD_MED"].dropna()
    r_vals = sub24[sub24["TP_LOCALIZACAO"] == 2]["IRD_MED"].dropna()
    if len(u_vals) > 0 and len(r_vals) > 0:
        stat, p = stats.mannwhitneyu(u_vals, r_vals, alternative="two-sided")
        print(f"  Mann-Whitney U={stat:.0f}, p={p:.4f}")

    # --- Figura C1 ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Distribuição por ano
    ax = axes[0]
    data_plot = [df[df["NU_ANO_CENSO"] == a]["IRD_MED"].dropna() for a in ANOS]
    bp = ax.boxplot(data_plot, tick_labels=ANOS, patch_artist=True, medianprops=dict(color="black", lw=2))
    for patch, ano in zip(bp["boxes"], ANOS):
        patch.set_facecolor(CORES_ANOS[ano])
        patch.set_alpha(0.7)
    ax.set_xlabel("Ano")
    ax.set_ylabel("IRD Médio")
    ax.set_title("Distribuição do IRD por ano")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))

    # Evolução temporal — médias com IC 95%
    ax = axes[1]
    medias, ci_low, ci_high = [], [], []
    for ano in ANOS:
        vals = df[df["NU_ANO_CENSO"] == ano]["IRD_MED"].dropna()
        m = vals.mean()
        sem = stats.sem(vals)
        ic = stats.t.ppf(0.975, len(vals) - 1) * sem
        medias.append(m); ci_low.append(m - ic); ci_high.append(m + ic)
    ax.plot(ANOS, medias, "o-", color="#333333", lw=2)
    ax.fill_between(ANOS, ci_low, ci_high, alpha=0.2, color="#999999")
    ax.set_xticks(ANOS)
    ax.set_xlabel("Ano")
    ax.set_ylabel("IRD Médio (com IC 95%)")
    ax.set_title("Evolução temporal do IRD")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f"))

    # Urbana vs Rural por ano
    ax = axes[2]
    x = np.arange(len(ANOS))
    w = 0.35
    for i, (loc, label, cor) in enumerate([(1, "Urbana", COR_URBANA), (2, "Rural", COR_RURAL)]):
        vals = [df[(df["NU_ANO_CENSO"] == a) & (df["TP_LOCALIZACAO"] == loc)]["IRD_MED"].mean() for a in ANOS]
        ax.bar(x + i * w, vals, w, label=label, color=cor, alpha=0.8)
    ax.set_xticks(x + w / 2)
    ax.set_xticklabels(ANOS)
    ax.set_xlabel("Ano"); ax.set_ylabel("IRD Médio")
    ax.set_title("IRD por localização")
    ax.legend()

    fig.suptitle("C1 — Indicador de Regularidade do Corpo Docente (IRD)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C1_ird.png")


# =============================================================================
# C2 — INSE: NÍVEL SOCIOECONÔMICO
# =============================================================================

def analise_inse(inse: pd.DataFrame, painel: pd.DataFrame) -> None:
    sep("C2 — INSE: NÍVEL SOCIOECONÔMICO")

    # Cobertura: quantas escolas do painel têm INSE
    escolas_painel = painel["CO_ENTIDADE"].unique()
    n_painel       = len(escolas_painel)
    n_com_inse     = inse["CO_ENTIDADE"].isin(escolas_painel).sum()
    print(f"\nEscolas no painel EM: {n_painel:,}")
    print(f"Escolas com INSE 2021: {n_com_inse:,} ({n_com_inse/n_painel*100:.1f}%)")
    print(f"Escolas sem INSE: {n_painel - n_com_inse:,} ({(n_painel - n_com_inse)/n_painel*100:.1f}%)")

    # Estatísticas gerais
    vals = inse["INSE_MEDIA"].dropna()
    print(f"\nINSE_MEDIA — N={len(vals):,}  média={vals.mean():.3f}  mediana={vals.median():.3f}"
          f"  DP={vals.std():.3f}  [min={vals.min():.2f} ; max={vals.max():.2f}]")

    # Distribuição por nível
    print("\nDistribuição por nível INSE (PE estadual EM):")
    niveis = inse["INSE_NIVEL"].value_counts().sort_index()
    for nivel, n in niveis.items():
        print(f"  {nivel}: {n:,} ({n/len(inse)*100:.1f}%)")

    # Urbano vs Rural — INSE já tem TP_LOCALIZACAO do SAEB (mesma codificação do Censo)
    df_loc = inse
    print("\nINSE médio por localização:")
    for loc, label in LABELS_LOCALIZACAO.items():
        sub = df_loc[df_loc["TP_LOCALIZACAO"] == loc]["INSE_MEDIA"].dropna()
        print(f"  {label}: N={len(sub):,}  média={sub.mean():.3f}  DP={sub.std():.3f}")

    u_vals = df_loc[df_loc["TP_LOCALIZACAO"] == 1]["INSE_MEDIA"].dropna()
    r_vals = df_loc[df_loc["TP_LOCALIZACAO"] == 2]["INSE_MEDIA"].dropna()
    if len(u_vals) > 0 and len(r_vals) > 0:
        stat, p = stats.mannwhitneyu(u_vals, r_vals, alternative="two-sided")
        print(f"  Mann-Whitney U={stat:.0f}, p={p:.4f}")

    # --- Figura C2 ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Histograma INSE_MEDIA
    ax = axes[0]
    ax.hist(inse["INSE_MEDIA"].dropna(), bins=25, color="#5C6BC0", edgecolor="white", alpha=0.85)
    ax.axvline(inse["INSE_MEDIA"].median(), color="red", linestyle="--", lw=1.5, label=f"Mediana={inse['INSE_MEDIA'].median():.2f}")
    ax.set_xlabel("INSE Médio")
    ax.set_ylabel("N escolas")
    ax.set_title("Distribuição do INSE")
    ax.legend(fontsize=9)

    # Barras por nível
    ax = axes[1]
    cores_nivel = ["#B71C1C", "#E53935", "#FB8C00", "#FDD835", "#7CB342", "#1B5E20"]
    nv = inse["INSE_NIVEL"].value_counts().sort_index()
    bars = ax.barh(nv.index.astype(str), nv.values,
                   color=cores_nivel[:len(nv)], edgecolor="white")
    for bar, val in zip(bars, nv.values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{val}", va="center", fontsize=8)
    ax.set_xlabel("N escolas")
    ax.set_title("Escolas por nível INSE")

    # Boxplot Urbana vs Rural
    ax = axes[2]
    data_loc = [
        df_loc[df_loc["TP_LOCALIZACAO"] == 1]["INSE_MEDIA"].dropna(),
        df_loc[df_loc["TP_LOCALIZACAO"] == 2]["INSE_MEDIA"].dropna(),
    ]
    bp = ax.boxplot(data_loc, tick_labels=["Urbana", "Rural"], patch_artist=True,
                    medianprops=dict(color="black", lw=2))
    bp["boxes"][0].set_facecolor(COR_URBANA); bp["boxes"][0].set_alpha(0.7)
    bp["boxes"][1].set_facecolor(COR_RURAL);  bp["boxes"][1].set_alpha(0.7)
    ax.set_ylabel("INSE Médio")
    ax.set_title("INSE por localização")

    fig.suptitle("C2 — Nível Socioeconômico (INSE 2021)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C2_inse.png")


# =============================================================================
# C3 — TDI: TAXA DE DISTORÇÃO IDADE-SÉRIE
# =============================================================================

def analise_tdi(tdi: pd.DataFrame, painel: pd.DataFrame) -> None:
    sep("C3 — TDI: TAXA DE DISTORÇÃO IDADE-SÉRIE (ENSINO MÉDIO)")

    df = _enriquecer_com_painel(tdi, painel, on=["CO_ENTIDADE", "NU_ANO_CENSO"])

    print(f"\nTotal de observações: {len(df):,}")
    print(f"Escolas únicas: {df['CO_ENTIDADE'].nunique():,}")

    # Estatísticas por ano
    print("\nTDI_MED por ano:")
    for ano in ANOS:
        sub = df[df["NU_ANO_CENSO"] == ano]["TDI_MED"].dropna()
        print(f"  {ano}: N={len(sub):,}  média={sub.mean():.1f}%  mediana={sub.median():.1f}%"
              f"  DP={sub.std():.1f}  [min={sub.min():.1f} ; max={sub.max():.1f}]")

    # Kruskal-Wallis entre anos
    grupos = [df[df["NU_ANO_CENSO"] == a]["TDI_MED"].dropna() for a in ANOS]
    if all(len(g) > 0 for g in grupos):
        h, p = stats.kruskal(*grupos)
        print(f"\nKruskal-Wallis (diferença entre anos): H={h:.2f}, p={p:.4f}")

    # Comparação por série (2024)
    series_cols = [c for c in ["TDI_MED_S1", "TDI_MED_S2", "TDI_MED_S3"] if c in df.columns]
    if series_cols:
        print("\nTDI por série (2024):")
        sub24 = df[df["NU_ANO_CENSO"] == 2024]
        for col in series_cols:
            vals = sub24[col].dropna()
            serie = col.replace("TDI_MED_S", "")
            print(f"  Série {serie}: N={len(vals):,}  média={vals.mean():.1f}%  mediana={vals.median():.1f}%")

    # Urbano vs Rural 2024
    sub24 = df[df["NU_ANO_CENSO"] == 2024]
    print("\nTDI_MED por localização (2024):")
    for loc, label in LABELS_LOCALIZACAO.items():
        vals = sub24[sub24["TP_LOCALIZACAO"] == loc]["TDI_MED"].dropna()
        print(f"  {label}: N={len(vals):,}  média={vals.mean():.1f}%  DP={vals.std():.1f}")

    u_vals = sub24[sub24["TP_LOCALIZACAO"] == 1]["TDI_MED"].dropna()
    r_vals = sub24[sub24["TP_LOCALIZACAO"] == 2]["TDI_MED"].dropna()
    if len(u_vals) > 0 and len(r_vals) > 0:
        stat, p = stats.mannwhitneyu(u_vals, r_vals, alternative="two-sided")
        print(f"  Mann-Whitney U={stat:.0f}, p={p:.4f}")

    # --- Figura C3 ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Boxplot por ano
    ax = axes[0]
    data_plot = [df[df["NU_ANO_CENSO"] == a]["TDI_MED"].dropna() for a in ANOS]
    bp = ax.boxplot(data_plot, tick_labels=ANOS, patch_artist=True, medianprops=dict(color="black", lw=2))
    for patch, ano in zip(bp["boxes"], ANOS):
        patch.set_facecolor(CORES_ANOS[ano]); patch.set_alpha(0.7)
    ax.set_xlabel("Ano"); ax.set_ylabel("TDI Ensino Médio (%)")
    ax.set_title("Distribuição TDI por ano")

    # Evolução temporal
    ax = axes[1]
    for loc, label, cor in [(1, "Urbana", COR_URBANA), (2, "Rural", COR_RURAL)]:
        vals = [df[(df["NU_ANO_CENSO"] == a) & (df["TP_LOCALIZACAO"] == loc)]["TDI_MED"].mean() for a in ANOS]
        ax.plot(ANOS, vals, "o-", label=label, color=cor, lw=2)
    ax.set_xticks(ANOS); ax.set_xlabel("Ano"); ax.set_ylabel("TDI Médio (%)")
    ax.set_title("Evolução TDI — Urbana vs Rural")
    ax.legend()

    # TDI por série (2024)
    if series_cols:
        ax = axes[2]
        labels_serie = [c.replace("TDI_MED_S", "Série ") for c in series_cols]
        sub24 = df[df["NU_ANO_CENSO"] == 2024]
        medias = [sub24[c].mean() for c in series_cols]
        bars = ax.bar(labels_serie, medias, color=["#1565C0", "#FF8F00", "#2E7D32"], alpha=0.8, edgecolor="white")
        for bar, val in zip(bars, medias):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val:.1f}%", ha="center", fontsize=9)
        ax.set_ylabel("TDI Médio (%)"); ax.set_title("TDI por série — EM 2024")
    else:
        axes[2].set_visible(False)

    fig.suptitle("C3 — Taxa de Distorção Idade-Série — Ensino Médio", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C3_tdi.png")


# =============================================================================
# C4 — AFD: ADEQUAÇÃO DA FORMAÇÃO DOCENTE
# =============================================================================

def analise_afd(afd: pd.DataFrame, painel: pd.DataFrame) -> None:
    sep("C4 — AFD: ADEQUAÇÃO DA FORMAÇÃO DOCENTE — ENSINO MÉDIO")

    df = _enriquecer_com_painel(afd, painel, on=["CO_ENTIDADE", "NU_ANO_CENSO"])

    afd_cols = [c for c in ["AFD_MED_G1", "AFD_MED_G2", "AFD_MED_G3", "AFD_MED_G4", "AFD_MED_G5"] if c in df.columns]
    labels_grupo = {
        "AFD_MED_G1": "G1 — Licenc. na disciplina (ideal)",
        "AFD_MED_G2": "G2 — Bacharelado na área",
        "AFD_MED_G3": "G3 — Licenc. em outra área",
        "AFD_MED_G4": "G4 — Outra formação superior",
        "AFD_MED_G5": "G5 — Sem ensino superior",
    }

    print(f"\nTotal de observações: {len(df):,}")

    # Composição média 2024
    print("\nComposição média dos grupos — EM (2024):")
    sub24 = df[df["NU_ANO_CENSO"] == 2024]
    for col in afd_cols:
        vals = sub24[col].dropna()
        print(f"  {labels_grupo.get(col, col)}: média={vals.mean():.1f}%  mediana={vals.median():.1f}%")

    # Evolução do G1 (adequado)
    if "AFD_MED_G1" in df.columns:
        print("\nEvolução do G1 (formação ideal) por ano:")
        for ano in ANOS:
            vals = df[df["NU_ANO_CENSO"] == ano]["AFD_MED_G1"].dropna()
            print(f"  {ano}: média={vals.mean():.1f}%  mediana={vals.median():.1f}%")

    # Urbano vs Rural para G1 (2024)
    if "AFD_MED_G1" in df.columns:
        print("\nAFD_MED_G1 por localização (2024):")
        for loc, label in LABELS_LOCALIZACAO.items():
            vals = sub24[sub24["TP_LOCALIZACAO"] == loc]["AFD_MED_G1"].dropna()
            print(f"  {label}: N={len(vals):,}  média={vals.mean():.1f}%")

        u_vals = sub24[sub24["TP_LOCALIZACAO"] == 1]["AFD_MED_G1"].dropna()
        r_vals = sub24[sub24["TP_LOCALIZACAO"] == 2]["AFD_MED_G1"].dropna()
        if len(u_vals) > 0 and len(r_vals) > 0:
            stat, p = stats.mannwhitneyu(u_vals, r_vals, alternative="two-sided")
            print(f"  Mann-Whitney U={stat:.0f}, p={p:.4f}")

    # --- Figura C4 ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Composição em barras empilhadas por ano
    ax = axes[0]
    cores_grupos = ["#1B5E20", "#43A047", "#FDD835", "#FB8C00", "#B71C1C"]
    bottoms = np.zeros(len(ANOS))
    for col, cor in zip(afd_cols, cores_grupos):
        vals = [df[df["NU_ANO_CENSO"] == a][col].mean() for a in ANOS]
        ax.bar(ANOS, vals, bottom=bottoms, color=cor, alpha=0.85, label=labels_grupo.get(col, col).split("—")[0].strip())
        bottoms += np.array(vals)
    ax.set_xticks(ANOS); ax.set_xlabel("Ano"); ax.set_ylabel("%")
    ax.set_title("Composição AFD EM (média)")
    ax.legend(fontsize=7, loc="lower right")

    # Evolução G1 por ano
    ax = axes[1]
    if "AFD_MED_G1" in df.columns:
        for loc, label, cor in [(1, "Urbana", COR_URBANA), (2, "Rural", COR_RURAL)]:
            vals = [df[(df["NU_ANO_CENSO"] == a) & (df["TP_LOCALIZACAO"] == loc)]["AFD_MED_G1"].mean() for a in ANOS]
            ax.plot(ANOS, vals, "o-", label=label, color=cor, lw=2)
        ax.set_xticks(ANOS); ax.set_xlabel("Ano"); ax.set_ylabel("AFD G1 (%)")
        ax.set_title("Evolução G1 — Urbana vs Rural")
        ax.legend()

    # Distribuição G1 2024
    ax = axes[2]
    if "AFD_MED_G1" in df.columns:
        sub24 = df[df["NU_ANO_CENSO"] == 2024]
        ax.hist(sub24["AFD_MED_G1"].dropna(), bins=25, color="#1B5E20", edgecolor="white", alpha=0.85)
        med = sub24["AFD_MED_G1"].median()
        ax.axvline(med, color="red", linestyle="--", lw=1.5, label=f"Mediana={med:.1f}%")
        ax.set_xlabel("AFD G1 (%)"); ax.set_ylabel("N escolas")
        ax.set_title("Distribuição G1 (2024)")
        ax.legend(fontsize=9)

    fig.suptitle("C4 — Adequação da Formação Docente — Ensino Médio", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C4_afd.png")


# =============================================================================
# C5 — CORRELAÇÕES COM TAXA DE ABANDONO
# =============================================================================

def analise_correlacoes(dados: dict[str, pd.DataFrame]) -> None:
    sep("C5 — CORRELAÇÕES DOS INDICADORES COM TAXA DE ABANDONO")

    painel = dados["painel"]
    taxas  = dados["taxas"]
    ird    = dados["ird"]
    inse   = dados["inse"]
    tdi    = dados["tdi"]
    afd    = dados["afd"]

    # Base: taxas com localização
    base = taxas[["CO_ENTIDADE", "NU_ANO_CENSO", "TAXA_ABND_MED"]].copy()
    base = base.merge(
        painel[["CO_ENTIDADE", "NU_ANO_CENSO", "TP_LOCALIZACAO", "CO_MESORREGIAO"]].drop_duplicates(),
        on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left",
    )

    # Join IRD
    base = base.merge(ird[["CO_ENTIDADE", "NU_ANO_CENSO", "IRD_MED"]], on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")

    # Join TDI
    tdi_cols = [c for c in ["TDI_MED", "TDI_MED_S1", "TDI_MED_S2", "TDI_MED_S3"] if c in tdi.columns]
    base = base.merge(tdi[["CO_ENTIDADE", "NU_ANO_CENSO"] + tdi_cols], on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")

    # Join AFD
    afd_cols = [c for c in ["AFD_MED_G1", "AFD_MED_G2", "AFD_MED_G3", "AFD_MED_G4", "AFD_MED_G5"] if c in afd.columns]
    base = base.merge(afd[["CO_ENTIDADE", "NU_ANO_CENSO"] + afd_cols], on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")

    # Join INSE (estático — apenas por CO_ENTIDADE)
    base = base.merge(inse[["CO_ENTIDADE", "INSE_MEDIA"]], on="CO_ENTIDADE", how="left")

    feature_cols = ["INSE_MEDIA", "IRD_MED", "TDI_MED"] + afd_cols
    feature_cols = [c for c in feature_cols if c in base.columns]

    print(f"\nBase de correlação: {len(base):,} observações")
    print(f"Features analisadas: {feature_cols}")

    # Correlações Spearman com abandono
    print("\nCorrelações Spearman com TAXA_ABND_MED:")
    resultados = {}
    for col in feature_cols:
        par = base[["TAXA_ABND_MED", col]].dropna()
        if len(par) < 30:
            continue
        r, p = stats.spearmanr(par["TAXA_ABND_MED"], par[col])
        resultados[col] = (r, p, len(par))
        sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
        print(f"  {col:<18}: r={r:+.3f}  p={p:.4f} {sig}  N={len(par):,}")

    # Interpretação dos mais relevantes
    if resultados:
        mais_forte = max(resultados, key=lambda k: abs(resultados[k][0]))
        print(f"\nCorrelação mais forte: {mais_forte} (r={resultados[mais_forte][0]:+.3f})")

    # --- Figura C5 ---
    n_cols = min(len(feature_cols), 4)
    if n_cols == 0:
        return

    fig, axes = plt.subplots(1, n_cols, figsize=(5 * n_cols, 4))
    if n_cols == 1:
        axes = [axes]

    cores_scatter = ["#5C6BC0", "#43A047", "#FB8C00", "#C62828", "#00838F"]
    for ax, col, cor in zip(axes, feature_cols[:n_cols], cores_scatter):
        par = base[["TAXA_ABND_MED", col]].dropna()
        ax.scatter(par[col], par["TAXA_ABND_MED"], alpha=0.3, s=12, color=cor)
        if len(par) > 2:
            m, b = np.polyfit(par[col], par["TAXA_ABND_MED"], 1)
            x_line = np.linspace(par[col].min(), par[col].max(), 100)
            ax.plot(x_line, m * x_line + b, color="red", lw=1.5)
            r, _ = stats.spearmanr(par["TAXA_ABND_MED"], par[col])
            ax.set_title(f"{col}\nr Spearman = {r:+.3f}", fontsize=9)
        ax.set_xlabel(col, fontsize=8)
        ax.set_ylabel("Taxa Abandono (%)" if ax == axes[0] else "")

    fig.suptitle("C5 — Correlação dos indicadores com taxa de abandono", fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C5_correlacoes.png")


# =============================================================================
# C6 — PERFIL DE RISCO COMPOSTO POR MUNICÍPIO
# =============================================================================

def analise_risco_composto(dados: dict[str, pd.DataFrame]) -> None:
    sep("C6 — PERFIL DE RISCO COMPOSTO POR MUNICÍPIO (2024)")

    painel = dados["painel"]
    taxas  = dados["taxas"]
    ird    = dados["ird"]
    inse   = dados["inse"]
    tdi    = dados["tdi"]

    # Usa o ano mais recente
    ano_ref = 2024
    base = painel[painel["NU_ANO_CENSO"] == ano_ref][
        ["CO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO", "TP_LOCALIZACAO"]
    ].copy()

    base = base.merge(taxas[taxas["NU_ANO_CENSO"] == ano_ref][["CO_ENTIDADE", "TAXA_ABND_MED"]],
                      on="CO_ENTIDADE", how="left")
    base = base.merge(ird[ird["NU_ANO_CENSO"] == ano_ref][["CO_ENTIDADE", "IRD_MED"]],
                      on="CO_ENTIDADE", how="left")
    base = base.merge(tdi[tdi["NU_ANO_CENSO"] == ano_ref][["CO_ENTIDADE", "TDI_MED"]],
                      on="CO_ENTIDADE", how="left")
    base = base.merge(inse[["CO_ENTIDADE", "INSE_MEDIA"]], on="CO_ENTIDADE", how="left")

    # Agrega por município
    mun = base.groupby(["CO_MUNICIPIO", "NO_MUNICIPIO"]).agg(
        n_escolas=("CO_ENTIDADE", "count"),
        abnd_medio=("TAXA_ABND_MED", "mean"),
        ird_medio=("IRD_MED", "mean"),
        tdi_medio=("TDI_MED", "mean"),
        inse_medio=("INSE_MEDIA", "mean"),
    ).reset_index()

    # Filtra municípios com mínimo de escolas para robustez
    mun = mun[mun["n_escolas"] >= 3].copy()

    # Índice de risco: alto abandono, alta TDI, baixo IRD, baixo INSE
    # Normaliza [0,1] e cria score de risco (maior = mais risco)
    def normaliza(serie):
        mn, mx = serie.min(), serie.max()
        return (serie - mn) / (mx - mn) if mx > mn else serie * 0

    mun["score_risco"] = (
        normaliza(mun["abnd_medio"])          # maior abandono = mais risco
        + normaliza(mun["tdi_medio"])          # maior distorção = mais risco
        + (1 - normaliza(mun["ird_medio"]))    # menor regularidade = mais risco
        + (1 - normaliza(mun["inse_medio"]))   # menor INSE = mais risco
    ) / 4  # média simples entre dimensões disponíveis

    mun = mun.sort_values("score_risco", ascending=False)

    print(f"\nMunicípios analisados: {len(mun)} (mín. 3 escolas)")
    print("\nTop 10 municípios de MAIOR risco composto:")
    print(mun[["NO_MUNICIPIO", "n_escolas", "abnd_medio", "tdi_medio", "ird_medio", "inse_medio", "score_risco"]]
          .head(10).to_string(index=False, float_format="%.2f"))

    print("\nTop 10 municípios de MENOR risco composto:")
    print(mun[["NO_MUNICIPIO", "n_escolas", "abnd_medio", "tdi_medio", "ird_medio", "inse_medio", "score_risco"]]
          .tail(10).to_string(index=False, float_format="%.2f"))

    # --- Figura C6 ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Top 15 maiores riscos
    ax = axes[0]
    top15 = mun.head(15)
    cores_bar = ["#C62828" if s > 0.6 else "#FB8C00" if s > 0.4 else "#FDD835" for s in top15["score_risco"]]
    bars = ax.barh(top15["NO_MUNICIPIO"][::-1], top15["score_risco"][::-1], color=cores_bar[::-1], edgecolor="white")
    ax.set_xlabel("Score de Risco Composto")
    ax.set_title("Top 15 municípios — maior risco")
    ax.set_xlim(0, 1)

    # Scatter abandono vs INSE com tamanho = TDI
    ax = axes[1]
    scatter_data = mun.dropna(subset=["abnd_medio", "inse_medio"])
    sc = ax.scatter(
        scatter_data["inse_medio"],
        scatter_data["abnd_medio"],
        s=scatter_data["tdi_medio"].fillna(10) * 3,
        c=scatter_data["score_risco"],
        cmap="RdYlGn_r", alpha=0.7, edgecolors="grey", linewidths=0.3,
    )
    plt.colorbar(sc, ax=ax, label="Score de Risco")
    ax.set_xlabel("INSE Médio do Município")
    ax.set_ylabel("Taxa de Abandono Média (%)")
    ax.set_title("Abandono vs INSE\n(tamanho = TDI médio)")

    fig.suptitle("C6 — Perfil de Risco Composto por Município (2024)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C6_risco_composto.png")


# =============================================================================
# SUMÁRIO EXECUTIVO
# =============================================================================

def sumario(dados: dict[str, pd.DataFrame]) -> None:
    sep("SUMÁRIO EXECUTIVO — INDICADORES COMPLEMENTARES")

    ird  = dados["ird"]
    inse = dados["inse"]
    tdi  = dados["tdi"]
    afd  = dados["afd"]
    painel = dados["painel"]

    n_painel = painel["CO_ENTIDADE"].nunique()
    n_inse   = inse["CO_ENTIDADE"].isin(painel["CO_ENTIDADE"]).sum()

    print(f"""
IRD (Regularidade Docente)
  • IRD médio 2024: {ird[ird['NU_ANO_CENSO']==2024]['IRD_MED'].mean():.3f}
  • Variação 2022→2024: {ird[ird['NU_ANO_CENSO']==2022]['IRD_MED'].mean():.3f} → {ird[ird['NU_ANO_CENSO']==2024]['IRD_MED'].mean():.3f}

INSE (Nível Socioeconômico — edição 2021)
  • Cobertura: {n_inse}/{n_painel} escolas ({n_inse/n_painel*100:.1f}%)
  • INSE médio: {inse['INSE_MEDIA'].mean():.3f}  |  mediana: {inse['INSE_MEDIA'].median():.3f}
  • LIMITAÇÃO: apenas 2021 disponível em nível escolar.

TDI (Distorção Idade-série — Ensino Médio)
  • TDI médio 2024: {tdi[tdi['NU_ANO_CENSO']==2024]['TDI_MED'].mean():.1f}%
  • Variação 2022→2024: {tdi[tdi['NU_ANO_CENSO']==2022]['TDI_MED'].mean():.1f}% → {tdi[tdi['NU_ANO_CENSO']==2024]['TDI_MED'].mean():.1f}%

AFD (Adequação Formação Docente — EM)
  • G1 (formação ideal) 2024: {afd[afd['NU_ANO_CENSO']==2024]['AFD_MED_G1'].mean():.1f}% (média escolar)
  • G5 (sem superior) 2024:   {afd[afd['NU_ANO_CENSO']==2024]['AFD_MED_G5'].mean():.1f}% (média escolar)

Próximos passos:
  → Feature engineering: incorporar IRD, TDI, AFD como features temporais (lag t-1)
  → INSE: usar 2021 como proxy estático; avaliar impacto da cobertura incompleta
  → Considerar baixar INSE 2023 em nível escolar (quando disponível no site do INEP)
""")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    dados = carregar_dados()

    analise_ird(dados["ird"],   dados["painel"], dados["taxas"])
    analise_inse(dados["inse"], dados["painel"])
    analise_tdi(dados["tdi"],   dados["painel"])
    analise_afd(dados["afd"],   dados["painel"])
    analise_correlacoes(dados)
    analise_risco_composto(dados)
    sumario(dados)

    print("\nFiguras salvas em:", FIGURAS_DIR)


if __name__ == "__main__":
    main()
