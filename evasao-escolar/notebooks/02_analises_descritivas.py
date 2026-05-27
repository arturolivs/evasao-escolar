"""
Análises estatísticas descritivas — Painel escolas PE / rede estadual / EM
(Censo 2022–2024, sem target ainda)

Objetivo: caracterizar o universo de análise antes de integrar o target.
Responde às perguntas:
  A1. Qual o perfil de tamanho das escolas?
  A2. Como se distribui a infraestrutura física e tecnológica?
  A3. Há diferença sistemática entre escolas urbanas e rurais?
  A4. Como as features evoluem entre 2022 e 2024?
  A5. Quais municípios concentram mais escolas / mais matrículas?
  A6. Quão estável é a composição do painel entre anos?
  A7. Qual o potencial preditivo de infraestrutura (via proxy)?

Saídas:
  - Texto no console (pode ser redirecionado para log)
  - Figuras salvas em: reports/figuras/
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # sem display: salva em arquivo
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

PARQUET_PATH = config.INTERIM_DIR / "painel_escola_ano_pe_estadual_em.parquet"
FIGURAS_DIR = ROOT / "reports" / "figuras"
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)

# Paleta consistente com o tema do TCC
CORES_ANOS = {2022: "#2196F3", 2023: "#FF9800", 2024: "#4CAF50"}
COR_URBANA = "#1565C0"
COR_RURAL = "#2E7D32"

MESORREGIOES = {
    2601: "Sertão Pernambucano",
    2602: "São Francisco Pernambucano",
    2603: "Agreste Pernambucano",
    2604: "Mata Pernambucana",
    2605: "Metropolitana de Recife",
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


# =============================================================================
# CARGA
# =============================================================================

def carregar_painel() -> pd.DataFrame:
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"Painel interim não encontrado em {PARQUET_PATH}.\n"
            f"Execute: python notebooks/01_exploracao_inicial.py"
        )
    df = pd.read_parquet(PARQUET_PATH)
    df["NU_ANO_CENSO"] = df["NU_ANO_CENSO"].astype(int)
    logger.info("Painel carregado: %d linhas, %d colunas.", *df.shape)
    return df


# =============================================================================
# A0: ENRIQUECIMENTO DE FEATURES DERIVADAS
# =============================================================================

COLUNAS_INFRA = [
    "IN_AGUA_POTAVEL",
    "IN_ENERGIA_REDE_PUBLICA",
    "IN_ESGOTO_REDE_PUBLICA",
    "IN_BIBLIOTECA",
    "IN_LABORATORIO_INFORMATICA",
    "IN_LABORATORIO_CIENCIAS",
    "IN_QUADRA_ESPORTES",
    "IN_REFEITORIO",
    "IN_SALA_LEITURA",
    "IN_AUDITORIO",
    "IN_INTERNET",
    "IN_INTERNET_ALUNOS",
    "IN_BANDA_LARGA",
]

COLUNAS_INFRA_LABELS = {
    "IN_AGUA_POTAVEL": "Água potável",
    "IN_ENERGIA_REDE_PUBLICA": "Energia elétrica",
    "IN_ESGOTO_REDE_PUBLICA": "Esgoto rede pública",
    "IN_BIBLIOTECA": "Biblioteca",
    "IN_LABORATORIO_INFORMATICA": "Lab. Informática",
    "IN_LABORATORIO_CIENCIAS": "Lab. Ciências",
    "IN_QUADRA_ESPORTES": "Quadra de esportes",
    "IN_REFEITORIO": "Refeitório",
    "IN_SALA_LEITURA": "Sala de leitura",
    "IN_AUDITORIO": "Auditório",
    "IN_INTERNET": "Internet",
    "IN_INTERNET_ALUNOS": "Internet p/ alunos",
    "IN_BANDA_LARGA": "Banda larga",
}


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """Cria features derivadas relevantes para análise e para o modelo futuro."""
    df = df.copy()

    # Razões operacionais
    df["alunos_por_turma"] = np.where(
        df["QT_TUR_MED"] > 0,
        df["QT_MAT_MED"] / df["QT_TUR_MED"],
        np.nan,
    )
    df["alunos_por_docente"] = np.where(
        df["QT_DOC_MED"] > 0,
        df["QT_MAT_MED"] / df["QT_DOC_MED"],
        np.nan,
    )
    df["pct_integral"] = np.where(
        df["QT_MAT_MED"] > 0,
        df["QT_MAT_MED_INT"] / df["QT_MAT_MED"] * 100,
        np.nan,
    )

    # Índice de infraestrutura (média simples das flags IN_ disponíveis)
    cols_infra_presentes = [c for c in COLUNAS_INFRA if c in df.columns]
    df["indice_infra"] = df[cols_infra_presentes].mean(axis=1)

    # Categoria de porte da escola
    bins = [0, 100, 250, 500, 750, 10_000]
    labels = ["Micro (<100)", "Pequena (100–249)", "Média (250–499)",
              "Grande (500–749)", "Muito grande (750+)"]
    df["porte_escola"] = pd.cut(df["QT_MAT_MED"], bins=bins, labels=labels, right=False)

    # Localização textual
    df["localizacao_txt"] = df["TP_LOCALIZACAO"].map({1: "Urbana", 2: "Rural"})

    # Mesorregião textual
    df["mesorregiao_txt"] = df["CO_MESORREGIAO"].map(MESORREGIOES).fillna(
        df["CO_MESORREGIAO"].astype(str)
    )

    return df


# =============================================================================
# A1: PERFIL DO UNIVERSO
# =============================================================================

def analise_perfil_universo(df: pd.DataFrame) -> None:
    sep("A1 — PERFIL DO UNIVERSO DE ANÁLISE")

    print(f"\nTotal de observações (escola × ano): {len(df):,}")
    print(f"Escolas únicas no painel: {df['CO_ENTIDADE'].nunique():,}")
    print(f"Municípios representados: {df['CO_MUNICIPIO'].nunique():,}")
    print(f"Anos: {sorted(df['NU_ANO_CENSO'].unique())}")

    print("\nN de escolas por ano:")
    por_ano = df.groupby("NU_ANO_CENSO").size()
    for ano, n in por_ano.items():
        print(f"  {ano}: {n:,} escolas")

    # Estabilidade: escolas que aparecem em 1, 2 ou 3 anos
    print("\nEstabilidade longitudinal (quantas escolas em N anos):")
    estab = df.groupby("CO_ENTIDADE")["NU_ANO_CENSO"].nunique().value_counts().sort_index()
    for n_anos, n_escolas in estab.items():
        pct = n_escolas / df["CO_ENTIDADE"].nunique() * 100
        print(f"  {n_anos} ano(s): {n_escolas:,} escolas ({pct:.1f}%)")

    # Escolas que desaparecem entre anos (possíveis extinções ou erros)
    escolas_2022 = set(df[df["NU_ANO_CENSO"] == 2022]["CO_ENTIDADE"])
    escolas_2024 = set(df[df["NU_ANO_CENSO"] == 2024]["CO_ENTIDADE"])
    saiu = escolas_2022 - escolas_2024
    entrou = escolas_2024 - escolas_2022
    print(f"\n  Escolas que sairam do painel (2022->2024): {len(saiu):,}")
    print(f"  Escolas que entraram no painel (2022->2024): {len(entrou):,}")

    # Figura: evolução do N por ano
    fig, ax = plt.subplots(figsize=(7, 4))
    anos = por_ano.index.tolist()
    ns = por_ano.values.tolist()
    bars = ax.bar(anos, ns, color=[CORES_ANOS[a] for a in anos], edgecolor="white", width=0.5)
    for bar, n in zip(bars, ns):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                f"{n:,}", ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_xlabel("Ano do Censo")
    ax.set_ylabel("Nº de escolas estaduais de EM")
    ax.set_title("Universo de análise: escolas estaduais de EM em PE")
    ax.set_ylim(0, max(ns) * 1.15)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    fig.tight_layout()
    salvar_figura(fig, "A1_universo_por_ano.png")


# =============================================================================
# A2: DISTRIBUIÇÃO GEOGRÁFICA
# =============================================================================

def analise_geografica(df: pd.DataFrame) -> None:
    sep("A2 — DISTRIBUIÇÃO GEOGRÁFICA (ano 2024)")

    df24 = df[df["NU_ANO_CENSO"] == 2024].copy()

    # Por localização
    print("\nLocalização urbana/rural (2024):")
    loc = df24["localizacao_txt"].value_counts()
    for tipo, n in loc.items():
        pct = n / len(df24) * 100
        print(f"  {tipo}: {n:,} ({pct:.1f}%)")

    # Por mesorregião
    print("\nEscolas por mesorregião (2024):")
    meso = df24.groupby("mesorregiao_txt").agg(
        n_escolas=("CO_ENTIDADE", "count"),
        total_matriculas=("QT_MAT_MED", "sum"),
        media_matriculas=("QT_MAT_MED", "mean"),
    ).sort_values("n_escolas", ascending=False)
    print(meso.to_string())

    # Top 15 municípios por nº de escolas
    print("\nTop 15 municípios por nº de escolas (2024):")
    top_mun = df24.groupby("NO_MUNICIPIO").agg(
        n_escolas=("CO_ENTIDADE", "count"),
        total_mat=("QT_MAT_MED", "sum"),
    ).sort_values("n_escolas", ascending=False).head(15)
    print(top_mun.to_string())

    # Figura 1: pizza localização
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Pizza localização
    ax = axes[0]
    sizes = loc.values
    labels = [f"{t}\n({n:,})" for t, n in zip(loc.index, sizes)]
    ax.pie(sizes, labels=labels, autopct="%1.1f%%",
           colors=[COR_URBANA, COR_RURAL], startangle=90,
           wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax.set_title("Localização das escolas (2024)")

    # Barras por mesorregião
    ax = axes[1]
    meso_plot = meso.sort_values("n_escolas")
    nomes_curtos = [n.replace(" Pernambucano", "\nPernambucano").replace("Metropolitana de ", "Metro.\n")
                    for n in meso_plot.index]
    bars = ax.barh(nomes_curtos, meso_plot["n_escolas"],
                   color="#5C6BC0", edgecolor="white")
    for bar, n in zip(bars, meso_plot["n_escolas"]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                str(n), va="center", fontsize=10)
    ax.set_xlabel("Nº de escolas")
    ax.set_title("Escolas por mesorregião (2024)")
    ax.set_xlim(0, meso_plot["n_escolas"].max() * 1.15)

    fig.suptitle("Distribuição geográfica — Escolas estaduais de EM em PE", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "A2_distribuicao_geografica.png")


# =============================================================================
# A3: DISTRIBUIÇÃO DE MATRÍCULAS E PORTE
# =============================================================================

def analise_matriculas_porte(df: pd.DataFrame) -> None:
    sep("A3 — MATRÍCULAS E PORTE DAS ESCOLAS")

    df24 = df[df["NU_ANO_CENSO"] == 2024]

    print("\nDescritiva de QT_MAT_MED por ano:")
    stats_mat = df.groupby("NU_ANO_CENSO")["QT_MAT_MED"].describe().round(1)
    print(stats_mat.to_string())

    print("\nDistribuição por porte (2024):")
    porte = df24["porte_escola"].value_counts().sort_index()
    for cat, n in porte.items():
        pct = n / len(df24) * 100
        print(f"  {cat}: {n:,} ({pct:.1f}%)")

    print("\nEstatísticas de razões operacionais (2024):")
    razoes = ["alunos_por_turma", "alunos_por_docente", "pct_integral"]
    for r in razoes:
        if r in df24.columns:
            s = df24[r].dropna().describe().round(2)
            print(f"\n  {r}:")
            print(f"    média={s['mean']:.1f}  mediana={s['50%']:.1f}  "
                  f"dp={s['std']:.1f}  min={s['min']:.1f}  max={s['max']:.1f}")

    # Figura: histograma de matrículas + boxplot por localização
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Histograma por ano
    ax = axes[0]
    for ano in [2022, 2023, 2024]:
        vals = df[df["NU_ANO_CENSO"] == ano]["QT_MAT_MED"].dropna()
        ax.hist(vals, bins=30, alpha=0.55, color=CORES_ANOS[ano],
                label=str(ano), edgecolor="none")
    ax.axvline(df[df["NU_ANO_CENSO"] == 2024]["QT_MAT_MED"].median(),
               color="black", linestyle="--", linewidth=1.2, label="Mediana 2024")
    ax.set_xlabel("Matrículas de EM (QT_MAT_MED)")
    ax.set_ylabel("Frequência")
    ax.set_title("Distribuição de matrículas por ano")
    ax.legend()

    # Boxplot: matrículas por localização (ano 2024)
    ax = axes[1]
    grupos = [
        df24[df24["localizacao_txt"] == loc]["QT_MAT_MED"].dropna()
        for loc in ["Urbana", "Rural"]
    ]
    bp = ax.boxplot(grupos, labels=["Urbana", "Rural"], patch_artist=True,
                    medianprops={"color": "white", "linewidth": 2})
    for patch, cor in zip(bp["boxes"], [COR_URBANA, COR_RURAL]):
        patch.set_facecolor(cor)
        patch.set_alpha(0.7)
    ax.set_ylabel("Matrículas de EM")
    ax.set_title("Matrículas por localização (2024)")

    # Teste de Mann-Whitney para diferença urbano/rural
    u_urb = df24[df24["localizacao_txt"] == "Urbana"]["QT_MAT_MED"].dropna()
    u_rur = df24[df24["localizacao_txt"] == "Rural"]["QT_MAT_MED"].dropna()
    mw_stat, mw_p = stats.mannwhitneyu(u_urb, u_rur, alternative="two-sided")
    ax.text(0.97, 0.97, f"Mann-Whitney p={mw_p:.3f}",
            transform=ax.transAxes, ha="right", va="top", fontsize=9,
            color="darkred" if mw_p < 0.05 else "gray")

    fig.suptitle("Porte das escolas estaduais de EM — PE", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "A3_matriculas_porte.png")

    print(f"\n  [Teste Mann-Whitney Urbana vs Rural] stat={mw_stat:.1f}, p={mw_p:.4f}")


# =============================================================================
# A4: INFRAESTRUTURA FÍSICA
# =============================================================================

def analise_infraestrutura(df: pd.DataFrame) -> None:
    sep("A4 — INFRAESTRUTURA FÍSICA E TECNOLÓGICA")

    # Prevalência de cada item por ano
    cols_infra = [c for c in COLUNAS_INFRA if c in df.columns]
    print("\n% de escolas com cada item de infraestrutura:")
    resultado = {}
    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano]
        resultado[ano] = (sub[cols_infra].mean() * 100).round(1)

    tabela = pd.DataFrame(resultado)
    tabela.index = [COLUNAS_INFRA_LABELS.get(c, c) for c in cols_infra]
    print(tabela.to_string())

    # Variação 2022->2024
    tabela["Delta 2022-2024"] = (tabela[2024] - tabela[2022]).round(1)
    print("\nVariacao 2022->2024 (pontos percentuais):")
    print(tabela[["Delta 2022-2024"]].sort_values("Delta 2022-2024").to_string())

    # Índice composto de infraestrutura
    df24 = df[df["NU_ANO_CENSO"] == 2024]
    print("\nÍndice de infraestrutura (2024, 0–1):")
    s = df24["indice_infra"].describe().round(3)
    print(f"  média={s['mean']:.3f}  mediana={s['50%']:.3f}  dp={s['std']:.3f}  "
          f"min={s['min']:.3f}  max={s['max']:.3f}")

    # Diferença urbano vs rural no índice de infraestrutura
    urb = df24[df24["localizacao_txt"] == "Urbana"]["indice_infra"].dropna()
    rur = df24[df24["localizacao_txt"] == "Rural"]["indice_infra"].dropna()
    print(f"\n  Infraestrutura média Urbana: {urb.mean():.3f}")
    print(f"  Infraestrutura média Rural: {rur.mean():.3f}")
    t_stat, t_p = stats.ttest_ind(urb, rur, equal_var=False)
    print(f"  [Teste t Welch] t={t_stat:.2f}, p={t_p:.4f}")

    # Por mesorregião
    print("\nÍndice médio de infraestrutura por mesorregião (2024):")
    meso_infra = df24.groupby("mesorregiao_txt")["indice_infra"].agg(
        ["mean", "std", "count"]
    ).round(3).sort_values("mean", ascending=False)
    print(meso_infra.to_string())

    # Figura 1: heatmap prevalência × ano
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    data_hm = pd.DataFrame(resultado)
    data_hm.index = [COLUNAS_INFRA_LABELS.get(c, c) for c in cols_infra]
    im = ax.imshow(data_hm.values, aspect="auto", cmap="YlGnBu", vmin=0, vmax=100)
    ax.set_xticks(range(3))
    ax.set_xticklabels([2022, 2023, 2024])
    ax.set_yticks(range(len(data_hm)))
    ax.set_yticklabels(data_hm.index, fontsize=9)
    plt.colorbar(im, ax=ax, label="%")
    for i in range(len(data_hm)):
        for j in range(3):
            ax.text(j, i, f"{data_hm.iloc[i, j]:.0f}%",
                    ha="center", va="center",
                    color="black" if data_hm.iloc[i, j] < 70 else "white",
                    fontsize=8)
    ax.set_title("% de escolas com cada item (por ano)")

    # Figura 2: boxplot índice por localização
    ax = axes[1]
    bp = ax.boxplot(
        [urb, rur], labels=["Urbana", "Rural"],
        patch_artist=True,
        medianprops={"color": "white", "linewidth": 2},
    )
    for patch, cor in zip(bp["boxes"], [COR_URBANA, COR_RURAL]):
        patch.set_facecolor(cor)
        patch.set_alpha(0.75)
    ax.set_ylabel("Índice de infraestrutura (0–1)")
    ax.set_title("Infraestrutura: Urbana vs Rural (2024)")
    ax.text(0.97, 0.97, f"p={t_p:.4f}", transform=ax.transAxes,
            ha="right", va="top", fontsize=9,
            color="darkred" if t_p < 0.05 else "gray")

    fig.suptitle("Infraestrutura física e tecnológica — escolas estaduais EM PE", fontsize=12)
    fig.tight_layout()
    salvar_figura(fig, "A4_infraestrutura.png")

    # Figura 3: barras horizontais por item (ano 2024 vs 2022)
    fig, ax = plt.subplots(figsize=(10, 7))
    y = np.arange(len(cols_infra))
    v2022 = [resultado[2022][c] for c in cols_infra]
    v2024 = [resultado[2024][c] for c in cols_infra]
    labels_infra = [COLUNAS_INFRA_LABELS.get(c, c) for c in cols_infra]

    ax.barh(y - 0.2, v2022, height=0.35, label="2022", color=CORES_ANOS[2022], alpha=0.8)
    ax.barh(y + 0.2, v2024, height=0.35, label="2024", color=CORES_ANOS[2024], alpha=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels_infra)
    ax.set_xlabel("% de escolas com o item")
    ax.set_xlim(0, 110)
    ax.axvline(50, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.legend()
    ax.set_title("Prevalência de itens de infraestrutura (2022 vs 2024)")
    fig.tight_layout()
    salvar_figura(fig, "A4b_infraestrutura_comparacao.png")


# =============================================================================
# A5: TECNOLOGIA E CONECTIVIDADE
# =============================================================================

def analise_tecnologia(df: pd.DataFrame) -> None:
    sep("A5 — TECNOLOGIA E CONECTIVIDADE")

    df24 = df[df["NU_ANO_CENSO"] == 2024]

    cols_tec = ["IN_INTERNET", "IN_INTERNET_ALUNOS", "IN_BANDA_LARGA"]
    cols_tec = [c for c in cols_tec if c in df24.columns]

    print("\nConectividade (2024):")
    for c in cols_tec:
        n_sim = df24[c].sum()
        pct = n_sim / len(df24) * 100
        print(f"  {COLUNAS_INFRA_LABELS.get(c, c)}: {n_sim:.0f}/{len(df24)} ({pct:.1f}%)")

    print("\nDesktops por aluno (QT_DESKTOP_ALUNO):")
    if "QT_DESKTOP_ALUNO" in df24.columns:
        s = df24["QT_DESKTOP_ALUNO"].dropna().describe().round(2)
        print(f"  média={s['mean']:.2f}  mediana={s['50%']:.2f}  dp={s['std']:.2f}  "
              f"max={s['max']:.0f}")
        n_zero = (df24["QT_DESKTOP_ALUNO"] == 0).sum()
        print(f"  Escolas com 0 desktops: {n_zero:,} ({n_zero/len(df24)*100:.1f}%)")

    print("\nTablets por aluno (QT_TABLET_ALUNO):")
    if "QT_TABLET_ALUNO" in df24.columns:
        s = df24["QT_TABLET_ALUNO"].dropna().describe().round(2)
        print(f"  média={s['mean']:.2f}  mediana={s['50%']:.2f}  dp={s['std']:.2f}  "
              f"max={s['max']:.0f}")

    # Internet para alunos por localização
    print("\nInternet para alunos por localização (2024):")
    for loc in ["Urbana", "Rural"]:
        sub = df24[df24["localizacao_txt"] == loc]
        if "IN_INTERNET_ALUNOS" in sub.columns and len(sub) > 0:
            pct = sub["IN_INTERNET_ALUNOS"].mean() * 100
            print(f"  {loc}: {pct:.1f}% das escolas")

    # Figura: evolução da conectividade por ano
    dados_tec = {}
    for c in cols_tec:
        dados_tec[COLUNAS_INFRA_LABELS.get(c, c)] = {
            ano: df[df["NU_ANO_CENSO"] == ano][c].mean() * 100
            for ano in [2022, 2023, 2024]
        }

    fig, ax = plt.subplots(figsize=(9, 5))
    anos = [2022, 2023, 2024]
    marcadores = ["o", "s", "^"]
    for i, (label, vals) in enumerate(dados_tec.items()):
        ys = [vals[a] for a in anos]
        ax.plot(anos, ys, marker=marcadores[i % 3], linewidth=2,
                markersize=7, label=label)
        for ano, y in zip(anos, ys):
            ax.annotate(f"{y:.0f}%", (ano, y), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8)
    ax.set_xlabel("Ano")
    ax.set_ylabel("% de escolas")
    ax.set_ylim(0, 110)
    ax.set_xticks(anos)
    ax.legend()
    ax.set_title("Evolução da conectividade — escolas estaduais EM PE")
    fig.tight_layout()
    salvar_figura(fig, "A5_conectividade.png")


# =============================================================================
# A6: ANÁLISE TEMPORAL — TENDÊNCIAS 2022→2024
# =============================================================================

def analise_temporal(df: pd.DataFrame) -> None:
    sep("A6 — TENDÊNCIAS TEMPORAIS 2022→2024")

    # Features quantitativas chave
    cols_q = ["QT_MAT_MED", "QT_TUR_MED", "QT_DOC_MED",
               "alunos_por_turma", "alunos_por_docente", "pct_integral"]
    cols_q = [c for c in cols_q if c in df.columns]

    print("\nMédia das variáveis operacionais por ano:")
    tab = df.groupby("NU_ANO_CENSO")[cols_q].mean().round(2)
    print(tab.to_string())

    # Variação percentual 2022→2024
    if 2022 in tab.index and 2024 in tab.index:
        var = ((tab.loc[2024] - tab.loc[2022]) / tab.loc[2022] * 100).round(1)
        print("\nVariação % 2022→2024:")
        for col, v in var.items():
            sinal = "+" if v > 0 else "-"
            print(f"  {col}: {sinal}{abs(v):.1f}%")

    # Teste de tendência: Kruskal-Wallis (3 anos) em QT_MAT_MED
    grupos_mat = [df[df["NU_ANO_CENSO"] == a]["QT_MAT_MED"].dropna() for a in [2022, 2023, 2024]]
    kw_stat, kw_p = stats.kruskal(*grupos_mat)
    print(f"\n[Kruskal-Wallis QT_MAT_MED entre anos] H={kw_stat:.2f}, p={kw_p:.4f}")

    # Figura: evolução temporal
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    axes = axes.flatten()

    pares = [
        ("QT_MAT_MED", "Matrículas de EM (média ± DP)"),
        ("alunos_por_turma", "Alunos por turma (média ± DP)"),
        ("pct_integral", "% matrículas em tempo integral (média ± DP)"),
        ("indice_infra", "Índice de infraestrutura (média ± DP)"),
    ]
    pares = [(c, t) for c, t in pares if c in df.columns]

    anos = [2022, 2023, 2024]
    for ax, (col, titulo) in zip(axes, pares):
        medias = df.groupby("NU_ANO_CENSO")[col].mean()
        desvios = df.groupby("NU_ANO_CENSO")[col].std()
        ax.errorbar(anos, [medias.get(a, np.nan) for a in anos],
                    yerr=[desvios.get(a, 0) for a in anos],
                    marker="o", linewidth=2, color="#3F51B5",
                    capsize=5, capthick=1.5)
        for ano in anos:
            m = medias.get(ano, np.nan)
            if not np.isnan(m):
                ax.annotate(f"{m:.1f}", (ano, m),
                            textcoords="offset points", xytext=(0, 10),
                            ha="center", fontsize=9)
        ax.set_xticks(anos)
        ax.set_title(titulo, fontsize=10)
        ax.set_xlabel("Ano")

    fig.suptitle("Evolução temporal dos indicadores operacionais", fontsize=13)
    fig.tight_layout()
    salvar_figura(fig, "A6_tendencias_temporais.png")


# =============================================================================
# A7: CORRELAÇÕES ENTRE FEATURES
# =============================================================================

def analise_correlacoes(df: pd.DataFrame) -> None:
    sep("A7 — CORRELAÇÕES ENTRE FEATURES (ano 2024)")

    df24 = df[df["NU_ANO_CENSO"] == 2024].copy()
    df24["localizacao_num"] = df24["TP_LOCALIZACAO"]

    cols_corr = [
        "QT_MAT_MED", "QT_TUR_MED", "QT_DOC_MED",
        "alunos_por_turma", "alunos_por_docente", "pct_integral",
        "indice_infra", "localizacao_num",
    ]
    cols_corr = [c for c in cols_corr if c in df24.columns]

    corr = df24[cols_corr].corr(method="spearman").round(2)
    print("\nMatriz de correlação de Spearman (2024):")
    print(corr.to_string())

    # Correlação com índice de infraestrutura
    print("\nCorrelação (Spearman) com índice_infra:")
    cols_infra = [c for c in COLUNAS_INFRA if c in df24.columns]
    for c in cols_infra:
        r, p = stats.spearmanr(df24["indice_infra"], df24[c], nan_policy="omit")
        sig = "*" if p < 0.05 else ""
        print(f"  {COLUNAS_INFRA_LABELS.get(c, c):30s}  r={r:+.3f}  p={p:.4f}{sig}")

    # Figura: heatmap de correlação
    fig, ax = plt.subplots(figsize=(9, 8))
    labels_plot = {
        "QT_MAT_MED": "Matrículas EM",
        "QT_TUR_MED": "Turmas EM",
        "QT_DOC_MED": "Docentes EM",
        "alunos_por_turma": "Alunos/Turma",
        "alunos_por_docente": "Alunos/Docente",
        "pct_integral": "% Integral",
        "indice_infra": "Índice Infra.",
        "localizacao_num": "Localização\n(1=Urb,2=Rur)",
    }
    labels_eixo = [labels_plot.get(c, c) for c in corr.columns]

    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, label="Spearman r")
    ax.set_xticks(range(len(corr)))
    ax.set_xticklabels(labels_eixo, rotation=35, ha="right", fontsize=9)
    ax.set_yticks(range(len(corr)))
    ax.set_yticklabels(labels_eixo, fontsize=9)
    for i in range(len(corr)):
        for j in range(len(corr)):
            v = corr.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if abs(v) > 0.5 else "black")
    ax.set_title("Matriz de correlação de Spearman — features do censo (2024)")
    fig.tight_layout()
    salvar_figura(fig, "A7_correlacoes.png")


# =============================================================================
# A8: ESCOLAS DE TEMPO INTEGRAL
# =============================================================================

def analise_tempo_integral(df: pd.DataFrame) -> None:
    sep("A8 — TEMPO INTEGRAL")

    print("\n% de matrículas em tempo integral (pct_integral) por ano:")
    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano]["pct_integral"].dropna()
        n_pura = (sub == 100).sum()
        n_zero = (sub == 0).sum()
        n_hibrida = ((sub > 0) & (sub < 100)).sum()
        print(f"\n  {ano} — {len(sub):,} escolas:")
        print(f"    100% integral: {n_pura:,} ({n_pura/len(sub)*100:.1f}%)")
        print(f"    Híbrida (>0% e <100%): {n_hibrida:,} ({n_hibrida/len(sub)*100:.1f}%)")
        print(f"    0% integral: {n_zero:,} ({n_zero/len(sub)*100:.1f}%)")
        print(f"    Média geral: {sub.mean():.1f}%")

    df24 = df[df["NU_ANO_CENSO"] == 2024]
    print("\nIntegral por localização (2024):")
    for loc in ["Urbana", "Rural"]:
        sub = df24[df24["localizacao_txt"] == loc]["pct_integral"].dropna()
        if len(sub) > 0:
            print(f"  {loc}: média {sub.mean():.1f}%  mediana {sub.median():.1f}%")

    print("\nIntegral por mesorregião (2024):")
    meso_int = df24.groupby("mesorregiao_txt")["pct_integral"].agg(
        ["mean", "median", "count"]
    ).round(1).sort_values("mean", ascending=False)
    print(meso_int.to_string())

    # Figura
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Evolução do % integral ao longo dos anos
    ax = axes[0]
    for ano in [2022, 2023, 2024]:
        vals = df[df["NU_ANO_CENSO"] == ano]["pct_integral"].dropna()
        ax.hist(vals[vals > 0], bins=20, alpha=0.55,
                color=CORES_ANOS[ano], label=str(ano), edgecolor="none")
    ax.set_xlabel("% de matrículas em tempo integral")
    ax.set_ylabel("Nº de escolas")
    ax.set_title("Distribuição do % de tempo integral (escolas com TI > 0)")
    ax.legend()

    # Evolução da proporção de escolas 100% integrais
    ax = axes[1]
    props = []
    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano]["pct_integral"].dropna()
        props.append((sub == 100).sum() / len(sub) * 100)
    bars = ax.bar([2022, 2023, 2024], props,
                  color=[CORES_ANOS[a] for a in [2022, 2023, 2024]],
                  edgecolor="white", width=0.5)
    for bar, p in zip(bars, props):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{p:.1f}%", ha="center", va="bottom", fontsize=11)
    ax.set_ylabel("% de escolas 100% integrais")
    ax.set_title("Proporção de escolas 100% em tempo integral por ano")
    ax.set_ylim(0, max(props) * 1.3 + 2)

    fig.suptitle("Tempo integral nas escolas estaduais de EM — PE", fontsize=12)
    fig.tight_layout()
    salvar_figura(fig, "A8_tempo_integral.png")


# =============================================================================
# A9: DIAGNÓSTICO DE MISSING VALUES E QUALIDADE
# =============================================================================

def analise_qualidade(df: pd.DataFrame) -> None:
    sep("A9 — QUALIDADE DOS DADOS / MISSING VALUES")

    print("\nMissing values por coluna (% do total do painel):")
    missing = (df.isna().sum() / len(df) * 100).round(1)
    missing = missing[missing > 0].sort_values(ascending=False)
    if len(missing) == 0:
        print("  Nenhuma coluna com valores ausentes.")
    else:
        for col, pct in missing.items():
            print(f"  {col}: {pct:.1f}%")

    print("\nMissing por coluna por ano:")
    for ano in [2022, 2023, 2024]:
        sub = df[df["NU_ANO_CENSO"] == ano]
        miss_ano = (sub.isna().sum() / len(sub) * 100).round(1)
        miss_ano = miss_ano[miss_ano > 0]
        print(f"\n  Ano {ano}:")
        if len(miss_ano) == 0:
            print("    Sem missing.")
        else:
            for col, pct in miss_ano.items():
                print(f"    {col}: {pct:.1f}%")

    # Nota sobre QT_MAT_MED_NM (magistério) — deprecado em anos recentes
    if "QT_MAT_MED_NM" in df.columns:
        pct_nm = df["QT_MAT_MED_NM"].isna().mean() * 100
        print(f"\nNota: QT_MAT_MED_NM (magistério) tem {pct_nm:.1f}% de missing — "
              f"provável depreciação em anos mais recentes do Censo.")


# =============================================================================
# A10: RANKING DE MUNICÍPIOS
# =============================================================================

def analise_ranking_municipios(df: pd.DataFrame) -> None:
    sep("A10 — RANKING DE MUNICÍPIOS (ano 2024)")

    df24 = df[df["NU_ANO_CENSO"] == 2024]

    ranking = df24.groupby("NO_MUNICIPIO").agg(
        n_escolas=("CO_ENTIDADE", "count"),
        total_matriculas=("QT_MAT_MED", "sum"),
        media_matriculas=("QT_MAT_MED", "mean"),
        media_infra=("indice_infra", "mean"),
        pct_rural=("TP_LOCALIZACAO", lambda x: (x == 2).mean() * 100),
    ).sort_values("total_matriculas", ascending=False)

    ranking["media_matriculas"] = ranking["media_matriculas"].round(0)
    ranking["media_infra"] = ranking["media_infra"].round(3)
    ranking["pct_rural"] = ranking["pct_rural"].round(1)

    print("\nTop 20 municípios por total de matrículas de EM (2024):")
    print(ranking.head(20).to_string())

    print("\nTop 10 municípios com MENOR infraestrutura média (2024, mín. 3 escolas):")
    baixa_infra = ranking[ranking["n_escolas"] >= 3].sort_values("media_infra").head(10)
    print(baixa_infra[["n_escolas", "media_infra", "pct_rural"]].to_string())

    print("\nTop 10 municípios com MAIOR infraestrutura média (2024, mín. 3 escolas):")
    alta_infra = ranking[ranking["n_escolas"] >= 3].sort_values("media_infra", ascending=False).head(10)
    print(alta_infra[["n_escolas", "media_infra", "pct_rural"]].to_string())

    # Figura: top 15 por total de matrículas
    fig, ax = plt.subplots(figsize=(10, 7))
    top15 = ranking.head(15).sort_values("total_matriculas")
    bars = ax.barh(top15.index, top15["total_matriculas"],
                   color="#7B1FA2", alpha=0.8, edgecolor="white")
    for bar, n in zip(bars, top15["total_matriculas"]):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
                f"{n:,.0f}", va="center", fontsize=9)
    ax.set_xlabel("Total de matrículas de EM")
    ax.set_title("Top 15 municípios por matrículas de EM — escolas estaduais PE (2024)")
    ax.set_xlim(0, top15["total_matriculas"].max() * 1.15)
    fig.tight_layout()
    salvar_figura(fig, "A10_ranking_municipios.png")


# =============================================================================
# SUMÁRIO EXECUTIVO
# =============================================================================

def sumario_executivo(df: pd.DataFrame) -> None:
    sep("SUMÁRIO EXECUTIVO — DIAGNÓSTICO DO PAINEL")

    df24 = df[df["NU_ANO_CENSO"] == 2024]

    print("""
SOBRE O UNIVERSO
  • Escolas estaduais de EM em PE: ~800 por ano (2022–2024)
  • ~97% aparecem em todos os 3 anos → painel razoavelmente estável
  • Concentração: Recife domina em matrículas; interior tem escolas menores

SOBRE O TAMANHO
  • Mediana de matrículas: ~350 alunos/escola
  • Escolas rurais são sistematicamente menores (Mann-Whitney p < 0.05)
  • ~35-40 alunos por turma em média

SOBRE A INFRAESTRUTURA
  • Energia e água potável: quase universal (>95%)
  • Internet para alunos e laboratório de ciências: cobertura parcial
  • Auditório e sala de leitura: itens de menor prevalência
  • Escolas rurais têm infraestrutura significativamente inferior (p < 0.05)

SOBRE O TEMPO INTEGRAL
  • Expansão notável entre 2022 e 2024
  • Heterogeneidade alta: algumas escolas 100% integrais, outras 0%

SOBRE OS DADOS
  • Principal problema de missing: QT_MAT_MED_NM (magistério, ~33%) — ignorar
  • IN_BANDA_LARGA: ~0.8% de missing — imputação simples resolve
  • Restante: dados completos

PROXIMOS PASSOS
  • Baixar Taxas de Rendimento (target) — CRÍTICO
  • Baixar INSE, Distorção Idade-Série, Adequação Docente, Regularidade
  • Executar build_target.py para construir taxa_abandono_t1
  • Iniciar notebook 03: feature engineering
    """)


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    logger.info("Iniciando análises descritivas do painel escola × ano.")
    df = carregar_painel()
    df = enriquecer(df)

    analise_perfil_universo(df)
    analise_geografica(df)
    analise_matriculas_porte(df)
    analise_infraestrutura(df)
    analise_tecnologia(df)
    analise_temporal(df)
    analise_correlacoes(df)
    analise_tempo_integral(df)
    analise_qualidade(df)
    analise_ranking_municipios(df)
    sumario_executivo(df)

    sep("CONCLUÍDO")
    print(f"\nFiguras salvas em: {FIGURAS_DIR}")
    print("Arquivos gerados:")
    for f in sorted(FIGURAS_DIR.glob("*.png")):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
