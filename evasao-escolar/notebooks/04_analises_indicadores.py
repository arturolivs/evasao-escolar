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
  C7. Como se distribui o IED (Esforço Docente)?
  C8. Como se distribui o ICG (Complexidade de Gestão)?

Saídas:
  - Texto no console
  - Figuras salvas em: reports/figuras/  (prefixo C*)
"""

from __future__ import annotations

from comum import (
    ANOS_CENSO,
    CORES_ANOS,
    COR_RURAL,
    COR_URBANA,
    FIGURAS_DIR,
    LABELS_LOCALIZACAO,
    carregar_parquet,
    salvar_figura,
    sep,
)

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy import stats

from src.data import config

CORES_NIVEIS = ["#1B5E20", "#7CB342", "#FDD835", "#FB8C00", "#E53935", "#B71C1C"]

IED_NIVEL_COLS = [f"IED_MED_N{i}" for i in range(1, 7)]

AFD_COLS = ["AFD_MED_G1", "AFD_MED_G2", "AFD_MED_G3", "AFD_MED_G4", "AFD_MED_G5"]
AFD_LABELS = {
    "AFD_MED_G1": "G1 — Licenc. na disciplina (ideal)",
    "AFD_MED_G2": "G2 — Bacharelado na área",
    "AFD_MED_G3": "G3 — Licenc. em outra área",
    "AFD_MED_G4": "G4 — Outra formação superior",
    "AFD_MED_G5": "G5 — Sem ensino superior",
}


# =============================================================================
# CARGA E HELPERS
# =============================================================================

def carregar_dados() -> dict[str, pd.DataFrame]:
    fontes = {
        "painel": ("painel_escola_ano_pe_estadual_em.parquet", "python -m src.data.build_school_panel"),
        "taxas": ("taxas_rendimento_pe_estadual_em.parquet", "python -m src.data.build_taxas_rendimento"),
        "ird": ("ird_pe_estadual.parquet", "python -m src.data.build_ird"),
        "inse": ("inse_pe_estadual.parquet", "python -m src.data.build_inse"),
        "tdi": ("tdi_pe_estadual.parquet", "python -m src.data.build_tdi"),
        "afd": ("afd_pe_estadual.parquet", "python -m src.data.build_afd"),
        "ied": ("ied_pe_estadual.parquet", "python -m src.data.build_esforco_docente"),
        "icg": ("icg_pe_estadual.parquet", "python -m src.data.build_complexidade_gestao"),
    }
    return {
        nome: carregar_parquet(config.INTERIM_DIR / arquivo, comando)
        for nome, (arquivo, comando) in fontes.items()
    }


def juntar_geografia_do_painel(df: pd.DataFrame, painel: pd.DataFrame, on: list[str]) -> pd.DataFrame:
    """Join com o painel do Censo para obter localização e mesorregião."""
    cols_geo = ["CO_ENTIDADE", "NU_ANO_CENSO", "TP_LOCALIZACAO", "CO_MESORREGIAO"]
    cols_geo = [c for c in cols_geo if c in painel.columns]
    geo = painel[cols_geo].drop_duplicates(subset=on)
    return df.merge(geo, on=on, how="left")


def serie_por_localizacao(df: pd.DataFrame, coluna: str, codigo: int) -> pd.Series:
    return df[df["TP_LOCALIZACAO"] == codigo][coluna].dropna()


def imprimir_mann_whitney_urbana_rural(df: pd.DataFrame, coluna: str) -> None:
    urbana = serie_por_localizacao(df, coluna, 1)
    rural = serie_por_localizacao(df, coluna, 2)
    if len(urbana) > 0 and len(rural) > 0:
        stat, p = stats.mannwhitneyu(urbana, rural, alternative="two-sided")
        print(f"  Mann-Whitney U={stat:.0f}, p={p:.4f}")


def boxplot_por_ano(ax: plt.Axes, df: pd.DataFrame, coluna: str, ylabel: str, titulo: str) -> None:
    dados = [df[df["NU_ANO_CENSO"] == a][coluna].dropna() for a in ANOS_CENSO]
    bp = ax.boxplot(dados, tick_labels=ANOS_CENSO, patch_artist=True,
                    medianprops=dict(color="black", lw=2))
    for patch, ano in zip(bp["boxes"], ANOS_CENSO):
        patch.set_facecolor(CORES_ANOS[ano])
        patch.set_alpha(0.7)
    ax.set_xlabel("Ano")
    ax.set_ylabel(ylabel)
    ax.set_title(titulo)


def linhas_urbana_rural(ax: plt.Axes, df: pd.DataFrame, coluna: str, ylabel: str, titulo: str) -> None:
    for codigo, label, cor in [(1, "Urbana", COR_URBANA), (2, "Rural", COR_RURAL)]:
        medias = [df[(df["NU_ANO_CENSO"] == a) & (df["TP_LOCALIZACAO"] == codigo)][coluna].mean()
                  for a in ANOS_CENSO]
        ax.plot(ANOS_CENSO, medias, "o-", label=label, color=cor, lw=2)
    ax.set_xticks(ANOS_CENSO)
    ax.set_xlabel("Ano")
    ax.set_ylabel(ylabel)
    ax.set_title(titulo)
    ax.legend()


def histograma_com_mediana(ax: plt.Axes, valores: pd.Series, cor: str,
                           xlabel: str, titulo: str, formato_mediana: str) -> None:
    ax.hist(valores.dropna(), bins=25, color=cor, edgecolor="white", alpha=0.85)
    mediana = valores.median()
    ax.axvline(mediana, color="red", linestyle="--", lw=1.5,
               label=f"Mediana={formato_mediana.format(mediana)}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("N escolas")
    ax.set_title(titulo)
    ax.legend(fontsize=9)


def barras_empilhadas_por_ano(ax: plt.Axes, df: pd.DataFrame, colunas: list[str],
                              cores: list[str], labels: list[str],
                              ylabel: str, titulo: str, **legenda) -> None:
    bottoms = np.zeros(len(ANOS_CENSO))
    for coluna, cor, label in zip(colunas, cores, labels):
        medias = [df[df["NU_ANO_CENSO"] == a][coluna].mean() for a in ANOS_CENSO]
        ax.bar(ANOS_CENSO, medias, bottom=bottoms, color=cor, alpha=0.85, label=label)
        bottoms += np.array(medias)
    ax.set_xticks(ANOS_CENSO)
    ax.set_xlabel("Ano")
    ax.set_ylabel(ylabel)
    ax.set_title(titulo)
    ax.legend(**legenda)


# =============================================================================
# C1 — IRD: REGULARIDADE DO CORPO DOCENTE
# =============================================================================

def relatorio_ird(df: pd.DataFrame) -> None:
    print(f"\nTotal de observações: {len(df):,}")
    print(f"Escolas únicas: {df['CO_ENTIDADE'].nunique():,}")
    print(f"Anos: {sorted(df['NU_ANO_CENSO'].unique())}")

    print("\nCobertura e estatísticas por ano:")
    for ano in ANOS_CENSO:
        sub = df[df["NU_ANO_CENSO"] == ano]["IRD_MED"].dropna()
        print(f"  {ano}: N={len(sub):,}  média={sub.mean():.3f}  mediana={sub.median():.3f}"
              f"  DP={sub.std():.3f}  [min={sub.min():.1f} ; max={sub.max():.1f}]")

    print("\nIRD médio por localização (2024):")
    sub24 = df[df["NU_ANO_CENSO"] == 2024]
    for codigo, label in LABELS_LOCALIZACAO.items():
        vals = serie_por_localizacao(sub24, "IRD_MED", codigo)
        print(f"  {label}: N={len(vals):,}  média={vals.mean():.3f}  DP={vals.std():.3f}")
    imprimir_mann_whitney_urbana_rural(sub24, "IRD_MED")


def figura_ird(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    boxplot_por_ano(axes[0], df, "IRD_MED", "IRD Médio", "Distribuição do IRD por ano")
    axes[0].yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))

    ax = axes[1]
    medias, ci_low, ci_high = [], [], []
    for ano in ANOS_CENSO:
        vals = df[df["NU_ANO_CENSO"] == ano]["IRD_MED"].dropna()
        media = vals.mean()
        ic = stats.t.ppf(0.975, len(vals) - 1) * stats.sem(vals)
        medias.append(media)
        ci_low.append(media - ic)
        ci_high.append(media + ic)
    ax.plot(ANOS_CENSO, medias, "o-", color="#333333", lw=2)
    ax.fill_between(ANOS_CENSO, ci_low, ci_high, alpha=0.2, color="#999999")
    ax.set_xticks(ANOS_CENSO)
    ax.set_xlabel("Ano")
    ax.set_ylabel("IRD Médio (com IC 95%)")
    ax.set_title("Evolução temporal do IRD")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f"))

    ax = axes[2]
    x = np.arange(len(ANOS_CENSO))
    largura = 0.35
    for i, (codigo, label, cor) in enumerate([(1, "Urbana", COR_URBANA), (2, "Rural", COR_RURAL)]):
        vals = [df[(df["NU_ANO_CENSO"] == a) & (df["TP_LOCALIZACAO"] == codigo)]["IRD_MED"].mean()
                for a in ANOS_CENSO]
        ax.bar(x + i * largura, vals, largura, label=label, color=cor, alpha=0.8)
    ax.set_xticks(x + largura / 2)
    ax.set_xticklabels(ANOS_CENSO)
    ax.set_xlabel("Ano")
    ax.set_ylabel("IRD Médio")
    ax.set_title("IRD por localização")
    ax.legend()

    fig.suptitle("C1 — Indicador de Regularidade do Corpo Docente (IRD)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C1_ird.png")


def analise_ird(ird: pd.DataFrame, painel: pd.DataFrame) -> None:
    sep("C1 — IRD: INDICADOR DE REGULARIDADE DO CORPO DOCENTE")

    df = juntar_geografia_do_painel(ird, painel, on=["CO_ENTIDADE", "NU_ANO_CENSO"])
    relatorio_ird(df)
    figura_ird(df)


# =============================================================================
# C2 — INSE: NÍVEL SOCIOECONÔMICO
# =============================================================================

def relatorio_inse(inse: pd.DataFrame, painel: pd.DataFrame) -> None:
    escolas_painel = painel["CO_ENTIDADE"].unique()
    n_painel = len(escolas_painel)
    n_com_inse = inse["CO_ENTIDADE"].isin(escolas_painel).sum()
    print(f"\nEscolas no painel EM: {n_painel:,}")
    print(f"Escolas com INSE 2021: {n_com_inse:,} ({n_com_inse/n_painel*100:.1f}%)")
    print(f"Escolas sem INSE: {n_painel - n_com_inse:,} ({(n_painel - n_com_inse)/n_painel*100:.1f}%)")

    vals = inse["INSE_MEDIA"].dropna()
    print(f"\nINSE_MEDIA — N={len(vals):,}  média={vals.mean():.3f}  mediana={vals.median():.3f}"
          f"  DP={vals.std():.3f}  [min={vals.min():.2f} ; max={vals.max():.2f}]")

    print("\nDistribuição por nível INSE (PE estadual EM):")
    for nivel, n in inse["INSE_NIVEL"].value_counts().sort_index().items():
        print(f"  {nivel}: {n:,} ({n/len(inse)*100:.1f}%)")

    # O INSE já traz TP_LOCALIZACAO do SAEB (mesma codificação do Censo)
    print("\nINSE médio por localização:")
    for codigo, label in LABELS_LOCALIZACAO.items():
        sub = serie_por_localizacao(inse, "INSE_MEDIA", codigo)
        print(f"  {label}: N={len(sub):,}  média={sub.mean():.3f}  DP={sub.std():.3f}")
    imprimir_mann_whitney_urbana_rural(inse, "INSE_MEDIA")


def figura_inse(inse: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    histograma_com_mediana(axes[0], inse["INSE_MEDIA"], "#5C6BC0",
                           "INSE Médio", "Distribuição do INSE", "{:.2f}")

    ax = axes[1]
    niveis = inse["INSE_NIVEL"].value_counts().sort_index()
    cores_vermelho_para_verde = list(reversed(CORES_NIVEIS))
    bars = ax.barh(niveis.index.astype(str), niveis.values,
                   color=cores_vermelho_para_verde[:len(niveis)], edgecolor="white")
    for bar, val in zip(bars, niveis.values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{val}", va="center", fontsize=8)
    ax.set_xlabel("N escolas")
    ax.set_title("Escolas por nível INSE")

    ax = axes[2]
    dados_loc = [serie_por_localizacao(inse, "INSE_MEDIA", 1),
                 serie_por_localizacao(inse, "INSE_MEDIA", 2)]
    bp = ax.boxplot(dados_loc, tick_labels=["Urbana", "Rural"], patch_artist=True,
                    medianprops=dict(color="black", lw=2))
    for patch, cor in zip(bp["boxes"], [COR_URBANA, COR_RURAL]):
        patch.set_facecolor(cor)
        patch.set_alpha(0.7)
    ax.set_ylabel("INSE Médio")
    ax.set_title("INSE por localização")

    fig.suptitle("C2 — Nível Socioeconômico (INSE 2021)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C2_inse.png")


def analise_inse(inse: pd.DataFrame, painel: pd.DataFrame) -> None:
    sep("C2 — INSE: NÍVEL SOCIOECONÔMICO")
    relatorio_inse(inse, painel)
    figura_inse(inse)


# =============================================================================
# C3 — TDI: TAXA DE DISTORÇÃO IDADE-SÉRIE
# =============================================================================

def relatorio_tdi(df: pd.DataFrame, series_cols: list[str]) -> None:
    print(f"\nTotal de observações: {len(df):,}")
    print(f"Escolas únicas: {df['CO_ENTIDADE'].nunique():,}")

    print("\nTDI_MED por ano:")
    for ano in ANOS_CENSO:
        sub = df[df["NU_ANO_CENSO"] == ano]["TDI_MED"].dropna()
        print(f"  {ano}: N={len(sub):,}  média={sub.mean():.1f}%  mediana={sub.median():.1f}%"
              f"  DP={sub.std():.1f}  [min={sub.min():.1f} ; max={sub.max():.1f}]")

    grupos = [df[df["NU_ANO_CENSO"] == a]["TDI_MED"].dropna() for a in ANOS_CENSO]
    if all(len(g) > 0 for g in grupos):
        h, p = stats.kruskal(*grupos)
        print(f"\nKruskal-Wallis (diferença entre anos): H={h:.2f}, p={p:.4f}")

    sub24 = df[df["NU_ANO_CENSO"] == 2024]
    if series_cols:
        print("\nTDI por série (2024):")
        for col in series_cols:
            vals = sub24[col].dropna()
            serie = col.replace("TDI_MED_S", "")
            print(f"  Série {serie}: N={len(vals):,}  média={vals.mean():.1f}%  mediana={vals.median():.1f}%")

    print("\nTDI_MED por localização (2024):")
    for codigo, label in LABELS_LOCALIZACAO.items():
        vals = serie_por_localizacao(sub24, "TDI_MED", codigo)
        print(f"  {label}: N={len(vals):,}  média={vals.mean():.1f}%  DP={vals.std():.1f}")
    imprimir_mann_whitney_urbana_rural(sub24, "TDI_MED")


def figura_tdi(df: pd.DataFrame, series_cols: list[str]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    boxplot_por_ano(axes[0], df, "TDI_MED", "TDI Ensino Médio (%)", "Distribuição TDI por ano")
    linhas_urbana_rural(axes[1], df, "TDI_MED", "TDI Médio (%)", "Evolução TDI — Urbana vs Rural")

    if series_cols:
        ax = axes[2]
        labels_serie = [c.replace("TDI_MED_S", "Série ") for c in series_cols]
        sub24 = df[df["NU_ANO_CENSO"] == 2024]
        medias = [sub24[c].mean() for c in series_cols]
        bars = ax.bar(labels_serie, medias, color=["#1565C0", "#FF8F00", "#2E7D32"],
                      alpha=0.8, edgecolor="white")
        for bar, val in zip(bars, medias):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val:.1f}%", ha="center", fontsize=9)
        ax.set_ylabel("TDI Médio (%)")
        ax.set_title("TDI por série — EM 2024")
    else:
        axes[2].set_visible(False)

    fig.suptitle("C3 — Taxa de Distorção Idade-Série — Ensino Médio",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C3_tdi.png")


def analise_tdi(tdi: pd.DataFrame, painel: pd.DataFrame) -> None:
    sep("C3 — TDI: TAXA DE DISTORÇÃO IDADE-SÉRIE (ENSINO MÉDIO)")

    df = juntar_geografia_do_painel(tdi, painel, on=["CO_ENTIDADE", "NU_ANO_CENSO"])
    series_cols = [c for c in ["TDI_MED_S1", "TDI_MED_S2", "TDI_MED_S3"] if c in df.columns]
    relatorio_tdi(df, series_cols)
    figura_tdi(df, series_cols)


# =============================================================================
# C4 — AFD: ADEQUAÇÃO DA FORMAÇÃO DOCENTE
# =============================================================================

def relatorio_afd(df: pd.DataFrame, afd_cols: list[str]) -> None:
    print(f"\nTotal de observações: {len(df):,}")

    print("\nComposição média dos grupos — EM (2024):")
    sub24 = df[df["NU_ANO_CENSO"] == 2024]
    for col in afd_cols:
        vals = sub24[col].dropna()
        print(f"  {AFD_LABELS.get(col, col)}: média={vals.mean():.1f}%  mediana={vals.median():.1f}%")

    if "AFD_MED_G1" not in df.columns:
        return

    print("\nEvolução do G1 (formação ideal) por ano:")
    for ano in ANOS_CENSO:
        vals = df[df["NU_ANO_CENSO"] == ano]["AFD_MED_G1"].dropna()
        print(f"  {ano}: média={vals.mean():.1f}%  mediana={vals.median():.1f}%")

    print("\nAFD_MED_G1 por localização (2024):")
    for codigo, label in LABELS_LOCALIZACAO.items():
        vals = serie_por_localizacao(sub24, "AFD_MED_G1", codigo)
        print(f"  {label}: N={len(vals):,}  média={vals.mean():.1f}%")
    imprimir_mann_whitney_urbana_rural(sub24, "AFD_MED_G1")


def figura_afd(df: pd.DataFrame, afd_cols: list[str]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    cores_grupos = ["#1B5E20", "#43A047", "#FDD835", "#FB8C00", "#B71C1C"]
    labels_curto = [AFD_LABELS.get(c, c).split("—")[0].strip() for c in afd_cols]
    barras_empilhadas_por_ano(axes[0], df, afd_cols, cores_grupos, labels_curto,
                              "%", "Composição AFD EM (média)",
                              fontsize=7, loc="lower right")

    if "AFD_MED_G1" in df.columns:
        linhas_urbana_rural(axes[1], df, "AFD_MED_G1", "AFD G1 (%)",
                            "Evolução G1 — Urbana vs Rural")

        sub24 = df[df["NU_ANO_CENSO"] == 2024]
        histograma_com_mediana(axes[2], sub24["AFD_MED_G1"], "#1B5E20",
                               "AFD G1 (%)", "Distribuição G1 (2024)", "{:.1f}%")

    fig.suptitle("C4 — Adequação da Formação Docente — Ensino Médio",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C4_afd.png")


def analise_afd(afd: pd.DataFrame, painel: pd.DataFrame) -> None:
    sep("C4 — AFD: ADEQUAÇÃO DA FORMAÇÃO DOCENTE — ENSINO MÉDIO")

    df = juntar_geografia_do_painel(afd, painel, on=["CO_ENTIDADE", "NU_ANO_CENSO"])
    afd_cols = [c for c in AFD_COLS if c in df.columns]
    relatorio_afd(df, afd_cols)
    figura_afd(df, afd_cols)


# =============================================================================
# C7 — IED: INDICADOR DE ESFORÇO DOCENTE
# =============================================================================

def relatorio_ied(df: pd.DataFrame) -> None:
    print(f"\nTotal de observações: {len(df):,}")
    print(f"Escolas únicas: {df['CO_ENTIDADE'].nunique():,}")
    print(f"Anos: {sorted(df['NU_ANO_CENSO'].unique())}")

    print("\nÍndice de esforço docente (IED_MED_MEDIO, escala 1–6) por ano:")
    for ano in ANOS_CENSO:
        sub = df[df["NU_ANO_CENSO"] == ano]["IED_MED_MEDIO"].dropna()
        print(f"  {ano}: N={len(sub):,}  média={sub.mean():.2f}  mediana={sub.median():.2f}"
              f"  DP={sub.std():.2f}  [min={sub.min():.2f} ; max={sub.max():.2f}]")

    sub24 = df[df["NU_ANO_CENSO"] == 2024]
    print("\nComposição média dos níveis de esforço — EM (2024):")
    for i, col in enumerate(IED_NIVEL_COLS, start=1):
        if col in df.columns:
            print(f"  Nível {i}: média={sub24[col].mean():.1f}% das docências")

    print("\nIED_MED_MEDIO por localização (2024):")
    for codigo, label in LABELS_LOCALIZACAO.items():
        vals = serie_por_localizacao(sub24, "IED_MED_MEDIO", codigo)
        print(f"  {label}: N={len(vals):,}  média={vals.mean():.2f}  DP={vals.std():.2f}")
    imprimir_mann_whitney_urbana_rural(sub24, "IED_MED_MEDIO")


def figura_ied(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    boxplot_por_ano(axes[0], df, "IED_MED_MEDIO", "IED médio (escala 1–6)",
                    "Distribuição do IED por ano")

    cols_presentes = [c for c in IED_NIVEL_COLS if c in df.columns]
    labels_niveis = [f"Nível {IED_NIVEL_COLS.index(c) + 1}" for c in cols_presentes]
    cores = [CORES_NIVEIS[IED_NIVEL_COLS.index(c)] for c in cols_presentes]
    barras_empilhadas_por_ano(axes[1], df, cols_presentes, cores, labels_niveis,
                              "% das docências (média)", "Composição dos níveis de esforço",
                              fontsize=7, ncol=2, loc="lower center")

    sub24 = df[df["NU_ANO_CENSO"] == 2024]
    histograma_com_mediana(axes[2], sub24["IED_MED_MEDIO"], "#6A1B9A",
                           "IED médio (escala 1–6)", "Distribuição do IED (2024)", "{:.2f}")

    fig.suptitle("C7 — Indicador de Esforço Docente (IED) — Ensino Médio",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C7_ied.png")


def analise_ied(ied: pd.DataFrame, painel: pd.DataFrame) -> None:
    sep("C7 — IED: INDICADOR DE ESFORÇO DOCENTE (ENSINO MÉDIO)")

    df = juntar_geografia_do_painel(ied, painel, on=["CO_ENTIDADE", "NU_ANO_CENSO"])
    relatorio_ied(df)
    figura_ied(df)


# =============================================================================
# C8 — ICG: INDICADOR DE COMPLEXIDADE DE GESTÃO
# =============================================================================

def restringir_ao_painel_em(icg: pd.DataFrame, painel: pd.DataFrame) -> pd.DataFrame:
    """O ICG cobre toda a rede estadual; mantém apenas as escolas do painel de EM."""
    return icg.merge(
        painel[["CO_ENTIDADE", "NU_ANO_CENSO", "TP_LOCALIZACAO", "CO_MESORREGIAO"]].drop_duplicates(),
        on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="inner",
    )


def relatorio_icg(df: pd.DataFrame) -> None:
    print(f"\nObservações (após restringir ao painel de EM): {len(df):,}")
    print(f"Escolas únicas: {df['CO_ENTIDADE'].nunique():,}")

    print("\nDistribuição dos níveis de complexidade (ICG_NIVEL) — todos os anos:")
    for nivel, n in df["ICG_NIVEL"].value_counts().sort_index().items():
        print(f"  Nível {int(nivel)}: {n:,} ({n/len(df)*100:.1f}%)")

    print("\nICG_NIVEL médio por ano:")
    for ano in ANOS_CENSO:
        sub = df[df["NU_ANO_CENSO"] == ano]["ICG_NIVEL"].dropna()
        print(f"  {ano}: N={len(sub):,}  média={sub.mean():.2f}  mediana={sub.median():.1f}")

    sub24 = df[df["NU_ANO_CENSO"] == 2024]
    print("\nICG_NIVEL por localização (2024):")
    for codigo, label in LABELS_LOCALIZACAO.items():
        vals = serie_por_localizacao(sub24, "ICG_NIVEL", codigo)
        print(f"  {label}: N={len(vals):,}  média={vals.mean():.2f}")


def relatorio_colinearidade_icg_tdi(base_tdi: pd.DataFrame) -> None:
    par = base_tdi[["ICG_NIVEL", "TDI_MED"]].dropna()
    if len(par) > 30:
        r, p = stats.spearmanr(par["ICG_NIVEL"], par["TDI_MED"])
        print(f"\nCorrelação ICG_NIVEL × TDI_MED: Spearman r={r:+.3f} (p={p:.4f}, N={len(par):,})")
        print("  → forte sobreposição com a TDI: justifica o descarte como feature.")


def figura_icg(df: pd.DataFrame, base_tdi: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    ax = axes[0]
    niveis = sorted(df["ICG_NIVEL"].dropna().unique())
    contagens = [int((df["ICG_NIVEL"] == n).sum()) for n in niveis]
    bars = ax.bar([f"N{int(n)}" for n in niveis], contagens,
                  color=[CORES_NIVEIS[int(n) - 1] for n in niveis], edgecolor="white")
    for bar, val in zip(bars, contagens):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                f"{val}", ha="center", fontsize=8)
    ax.set_xlabel("Nível de complexidade")
    ax.set_ylabel("N observações")
    ax.set_title("Escolas por nível de ICG")

    linhas_urbana_rural(axes[1], df, "ICG_NIVEL", "ICG médio (1–6)",
                        "Evolução do ICG — Urbana vs Rural")

    ax = axes[2]
    par_plot = base_tdi[["ICG_NIVEL", "TDI_MED"]].dropna()
    ax.scatter(par_plot["ICG_NIVEL"] + np.random.uniform(-0.15, 0.15, len(par_plot)),
               par_plot["TDI_MED"], alpha=0.25, s=12, color="#00838F")
    if len(par_plot) > 2:
        m, b = np.polyfit(par_plot["ICG_NIVEL"], par_plot["TDI_MED"], 1)
        xs = np.linspace(par_plot["ICG_NIVEL"].min(), par_plot["ICG_NIVEL"].max(), 50)
        ax.plot(xs, m * xs + b, color="red", lw=1.5)
        r, _ = stats.spearmanr(par_plot["ICG_NIVEL"], par_plot["TDI_MED"])
        ax.set_title(f"ICG × TDI (colinearidade)\nr Spearman = {r:+.3f}", fontsize=10)
    ax.set_xlabel("ICG (nível)")
    ax.set_ylabel("TDI Ensino Médio (%)")

    fig.suptitle("C8 — Indicador de Complexidade de Gestão (ICG)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C8_icg.png")


def analise_icg(icg: pd.DataFrame, painel: pd.DataFrame, tdi: pd.DataFrame) -> None:
    sep("C8 — ICG: INDICADOR DE COMPLEXIDADE DE GESTÃO DA ESCOLA")

    df = restringir_ao_painel_em(icg, painel)
    relatorio_icg(df)

    base_tdi = df.merge(tdi[["CO_ENTIDADE", "NU_ANO_CENSO", "TDI_MED"]],
                        on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")
    relatorio_colinearidade_icg_tdi(base_tdi)
    figura_icg(df, base_tdi)


# =============================================================================
# C5 — CORRELAÇÕES COM TAXA DE ABANDONO
# =============================================================================

def montar_base_correlacao(dados: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, list[str]]:
    painel, taxas = dados["painel"], dados["taxas"]
    chaves = ["CO_ENTIDADE", "NU_ANO_CENSO"]

    base = taxas[chaves + ["TAXA_ABND_MED"]].copy()
    base = base.merge(
        painel[chaves + ["TP_LOCALIZACAO", "CO_MESORREGIAO"]].drop_duplicates(),
        on=chaves, how="left",
    )
    base = base.merge(dados["ird"][chaves + ["IRD_MED"]], on=chaves, how="left")

    tdi_cols = [c for c in ["TDI_MED", "TDI_MED_S1", "TDI_MED_S2", "TDI_MED_S3"]
                if c in dados["tdi"].columns]
    base = base.merge(dados["tdi"][chaves + tdi_cols], on=chaves, how="left")

    afd_cols = [c for c in AFD_COLS if c in dados["afd"].columns]
    base = base.merge(dados["afd"][chaves + afd_cols], on=chaves, how="left")

    # INSE é estático (edição 2021): join apenas por escola
    base = base.merge(dados["inse"][["CO_ENTIDADE", "INSE_MEDIA"]], on="CO_ENTIDADE", how="left")

    base = base.merge(dados["ied"][chaves + ["IED_MED_MEDIO"]], on=chaves, how="left")
    base = base.merge(dados["icg"][chaves + ["ICG_NIVEL"]], on=chaves, how="left")

    feature_cols = ["INSE_MEDIA", "IRD_MED", "TDI_MED"] + afd_cols + ["IED_MED_MEDIO", "ICG_NIVEL"]
    feature_cols = [c for c in feature_cols if c in base.columns]
    return base, feature_cols


def relatorio_correlacoes(base: pd.DataFrame, feature_cols: list[str]) -> dict:
    print(f"\nBase de correlação: {len(base):,} observações")
    print(f"Features analisadas: {feature_cols}")

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

    if resultados:
        mais_forte = max(resultados, key=lambda k: abs(resultados[k][0]))
        print(f"\nCorrelação mais forte: {mais_forte} (r={resultados[mais_forte][0]:+.3f})")
    return resultados


def figura_correlacoes(base: pd.DataFrame, feature_cols: list[str]) -> None:
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

    fig.suptitle("C5 — Correlação dos indicadores com taxa de abandono",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C5_correlacoes.png")


def analise_correlacoes(dados: dict[str, pd.DataFrame]) -> None:
    sep("C5 — CORRELAÇÕES DOS INDICADORES COM TAXA DE ABANDONO")

    base, feature_cols = montar_base_correlacao(dados)
    relatorio_correlacoes(base, feature_cols)
    figura_correlacoes(base, feature_cols)


# =============================================================================
# C6 — PERFIL DE RISCO COMPOSTO POR MUNICÍPIO
# =============================================================================

def normalizar_0_1(serie: pd.Series) -> pd.Series:
    minimo, maximo = serie.min(), serie.max()
    return (serie - minimo) / (maximo - minimo) if maximo > minimo else serie * 0


def montar_risco_por_municipio(dados: dict[str, pd.DataFrame], ano_ref: int = 2024) -> pd.DataFrame:
    painel = dados["painel"]
    base = painel[painel["NU_ANO_CENSO"] == ano_ref][
        ["CO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO", "TP_LOCALIZACAO"]
    ].copy()

    for nome, coluna in [("taxas", "TAXA_ABND_MED"), ("ird", "IRD_MED"), ("tdi", "TDI_MED")]:
        indicador = dados[nome]
        indicador_ano = indicador[indicador["NU_ANO_CENSO"] == ano_ref]
        base = base.merge(indicador_ano[["CO_ENTIDADE", coluna]], on="CO_ENTIDADE", how="left")
    base = base.merge(dados["inse"][["CO_ENTIDADE", "INSE_MEDIA"]], on="CO_ENTIDADE", how="left")

    municipios = base.groupby(["CO_MUNICIPIO", "NO_MUNICIPIO"]).agg(
        n_escolas=("CO_ENTIDADE", "count"),
        abnd_medio=("TAXA_ABND_MED", "mean"),
        ird_medio=("IRD_MED", "mean"),
        tdi_medio=("TDI_MED", "mean"),
        inse_medio=("INSE_MEDIA", "mean"),
    ).reset_index()

    municipios = municipios[municipios["n_escolas"] >= 3].copy()

    # Risco cresce com abandono e TDI, e decresce com regularidade docente e INSE
    municipios["score_risco"] = (
        normalizar_0_1(municipios["abnd_medio"])
        + normalizar_0_1(municipios["tdi_medio"])
        + (1 - normalizar_0_1(municipios["ird_medio"]))
        + (1 - normalizar_0_1(municipios["inse_medio"]))
    ) / 4

    return municipios.sort_values("score_risco", ascending=False)


def relatorio_risco_composto(municipios: pd.DataFrame) -> None:
    colunas = ["NO_MUNICIPIO", "n_escolas", "abnd_medio", "tdi_medio",
               "ird_medio", "inse_medio", "score_risco"]

    print(f"\nMunicípios analisados: {len(municipios)} (mín. 3 escolas)")
    print("\nTop 10 municípios de MAIOR risco composto:")
    print(municipios[colunas].head(10).to_string(index=False, float_format="%.2f"))

    print("\nTop 10 municípios de MENOR risco composto:")
    print(municipios[colunas].tail(10).to_string(index=False, float_format="%.2f"))


def figura_risco_composto(municipios: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    top15 = municipios.head(15)
    cores_bar = ["#C62828" if s > 0.6 else "#FB8C00" if s > 0.4 else "#FDD835"
                 for s in top15["score_risco"]]
    ax.barh(top15["NO_MUNICIPIO"][::-1], top15["score_risco"][::-1],
            color=cores_bar[::-1], edgecolor="white")
    ax.set_xlabel("Score de Risco Composto")
    ax.set_title("Top 15 municípios — maior risco")
    ax.set_xlim(0, 1)

    ax = axes[1]
    scatter_data = municipios.dropna(subset=["abnd_medio", "inse_medio"])
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

    fig.suptitle("C6 — Perfil de Risco Composto por Município (2024)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "C6_risco_composto.png")


def analise_risco_composto(dados: dict[str, pd.DataFrame]) -> None:
    sep("C6 — PERFIL DE RISCO COMPOSTO POR MUNICÍPIO (2024)")

    municipios = montar_risco_por_municipio(dados)
    relatorio_risco_composto(municipios)
    figura_risco_composto(municipios)


# =============================================================================
# SUMÁRIO EXECUTIVO
# =============================================================================

def sumario(dados: dict[str, pd.DataFrame]) -> None:
    sep("SUMÁRIO EXECUTIVO — INDICADORES COMPLEMENTARES")

    ird, inse, tdi, afd, painel = (dados["ird"], dados["inse"], dados["tdi"],
                                   dados["afd"], dados["painel"])

    n_painel = painel["CO_ENTIDADE"].nunique()
    n_inse = inse["CO_ENTIDADE"].isin(painel["CO_ENTIDADE"]).sum()

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

    analise_ird(dados["ird"], dados["painel"])
    analise_inse(dados["inse"], dados["painel"])
    analise_tdi(dados["tdi"], dados["painel"])
    analise_afd(dados["afd"], dados["painel"])
    analise_ied(dados["ied"], dados["painel"])
    analise_icg(dados["icg"], dados["painel"], dados["tdi"])
    analise_correlacoes(dados)
    analise_risco_composto(dados)
    sumario(dados)

    print("\nFiguras salvas em:", FIGURAS_DIR)


if __name__ == "__main__":
    main()
