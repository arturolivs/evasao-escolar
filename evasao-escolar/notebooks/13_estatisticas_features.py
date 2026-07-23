"""
Análise estatística de todas as 38 informações usadas na predição.

Para cada coluna do conjunto de modelagem produz: (i) estatísticas descritivas
adequadas ao seu tipo — resumo de posição e dispersão para as contínuas,
prevalência para as binárias, distribuição para a categórica; e (ii) a relação
com o abandono do ano seguinte, com teste de significância.

Saídas: `reports/estatisticas_features.csv` e as figuras E5 a E8 em
`reports/figuras/`, com rótulos em linguagem de gestor.

Execução: python notebooks/13_estatisticas_features.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from comum import ROOT, salvar_figura, sep
from matplotlib import pyplot as plt
from scipy import stats

from src.models.train import TARGET_COL, carregar_dataset, colunas_features
from src.recommend.labels import MESORREGIAO_NOMES, rotular_feature

COR_AUMENTA = "#C62828"
COR_REDUZ = "#1565C0"
COR_NEUTRA = "#9E9E9E"
COR_BARRA = "#546E7A"
# Na figura das binárias, "tem/não tem" é uma categoria, não uma direção de
# risco: cores próprias, para não colidir com a leitura vermelho/azul das demais.
COR_COM = "#00695C"
COR_SEM = "#B0BEC5"

ALFA = 0.05
CATEGORICAS = ["CO_MESORREGIAO"]


def classificar(serie: pd.Series, nome: str) -> str:
    if nome in CATEGORICAS:
        return "categórica"
    if set(serie.dropna().unique()) <= {0, 1}:
        return "binária"
    return "contínua"


def estrelas(p: float) -> str:
    """Marca a significância do teste, na convenção usual."""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < ALFA:
        return "*"
    return ""


# =============================================================================
# ESTATÍSTICAS POR TIPO DE COLUNA
# =============================================================================

def descrever_continuas(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Posição, dispersão e relação com o alvo para as colunas contínuas."""
    alvo = df[TARGET_COL]
    linhas = []
    for coluna in colunas:
        valores = df[coluna]
        rho, p = stats.spearmanr(valores, alvo)
        linhas.append({
            "coluna": coluna,
            "informacao": rotular_feature(coluna),
            "tipo": "contínua",
            "n": int(valores.notna().sum()),
            "media": valores.mean(),
            "desvio": valores.std(),
            "minimo": valores.min(),
            "mediana": valores.median(),
            "maximo": valores.max(),
            "assimetria": valores.skew(),
            "relacao": rho,
            "p_valor": p,
            "significancia": estrelas(p),
        })
    return pd.DataFrame(linhas).sort_values("relacao", key=abs, ascending=False)


def descrever_binarias(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """
    Prevalência e efeito das colunas de sim/não.

    Duas grandezas distintas convivem aqui, e confundi-las inverte a leitura
    da tabela. `n_tem`/`n_nao` (e seus percentuais) repartem as escolas em dois
    grupos — somam o total da rede. Já `abandono_com`/`abandono_sem` são a
    média do abandono dentro de cada grupo: duas médias da mesma variável, que
    não se somam a nada. Por isso as contagens são reportadas junto dos
    percentuais: sem elas o leitor não vê que atributos quase universais
    (internet, água potável) deixam um grupo de comparação minúsculo.
    """
    alvo = df[TARGET_COL]
    linhas = []
    for coluna in colunas:
        tem = df[coluna] == 1
        com, sem = alvo[tem], alvo[~tem]
        if len(com) and len(sem):
            _, p = stats.mannwhitneyu(com, sem, alternative="two-sided")
        else:
            p = np.nan
        rho, _ = stats.spearmanr(df[coluna], alvo)
        linhas.append({
            "coluna": coluna,
            "informacao": rotular_feature(coluna),
            "tipo": "binária",
            "n": int(df[coluna].notna().sum()),
            # Repartição das escolas: n_tem + n_nao = n, prevalencia + pct_nao = 100
            "n_tem": int(tem.sum()),
            "n_nao": int((~tem).sum()),
            "prevalencia": tem.mean() * 100,
            "pct_nao": (~tem).mean() * 100,
            # Médias do abandono dentro de cada grupo — não se somam
            "abandono_com": com.mean(),
            "abandono_sem": sem.mean(),
            "diferenca": com.mean() - sem.mean(),
            "relacao": rho,
            "p_valor": p,
            "significancia": estrelas(p),
        })
    return pd.DataFrame(linhas).sort_values("diferenca", key=abs, ascending=False)


def descrever_categorica(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Distribuição e abandono médio por categoria, com teste entre grupos."""
    grupos = [g[TARGET_COL].values for _, g in df.groupby(coluna)]
    _, p = stats.kruskal(*grupos) if len(grupos) > 1 else (np.nan, np.nan)
    resumo = (df.groupby(coluna)[TARGET_COL]
              .agg(escolas="size", abandono_medio="mean", mediana="median")
              .reset_index())
    resumo["categoria"] = resumo[coluna].map(
        lambda c: MESORREGIAO_NOMES.get(int(c), str(c))
    )
    resumo["participacao"] = resumo["escolas"] / len(df) * 100
    resumo["p_valor"] = p
    resumo["significancia"] = estrelas(p)
    return resumo.sort_values("abandono_medio", ascending=False)


# =============================================================================
# FIGURAS
# =============================================================================

def figura_distribuicoes(df: pd.DataFrame, resumo: pd.DataFrame) -> None:
    """E5 — como cada informação contínua se distribui na rede."""
    colunas = list(resumo["coluna"])
    n_col = 4
    n_lin = int(np.ceil(len(colunas) / n_col))
    fig, eixos = plt.subplots(n_lin, n_col, figsize=(16, 3.0 * n_lin))
    for eixo, coluna in zip(eixos.flat, colunas):
        valores = df[coluna].dropna()
        eixo.hist(valores, bins=30, color=COR_BARRA, edgecolor="white", linewidth=0.4)
        eixo.axvline(valores.median(), color=COR_AUMENTA, linestyle="--", linewidth=1.5)
        eixo.set_title(rotular_feature(coluna), fontsize=9)
        eixo.tick_params(labelsize=8)
        eixo.grid(axis="y", alpha=0.25)
    for eixo in eixos.flat[len(colunas):]:
        eixo.axis("off")
    fig.suptitle("Como cada informação contínua se distribui na rede estadual\n"
                 "(linha tracejada: mediana)", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    salvar_figura(fig, "E5_distribuicoes.png")


def figura_binarias(resumo: pd.DataFrame) -> None:
    """E6 — prevalência dos atributos de sim/não e o abandono associado."""
    dados = resumo.sort_values("prevalencia")
    rotulos = list(dados["informacao"])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), sharey=True)

    # Barra empilhada: torna explícito que os dois grupos repartem a rede e
    # somam 100% — leitura que a barra simples de prevalência não sustentava.
    ax1.barh(rotulos, dados["prevalencia"], color=COR_COM, label="Têm o atributo")
    ax1.barh(rotulos, dados["pct_nao"], left=dados["prevalencia"],
             color=COR_SEM, label="Não têm")
    # Barras verdes curtas não comportam o rótulo: nelas o texto vai para fora,
    # em cor escura sobre o trecho cinza.
    for pos, (pct, n) in enumerate(zip(dados["prevalencia"], dados["n_tem"])):
        texto = f"{pct:.0f}%  (n={n})"
        if pct >= 25:
            ax1.text(pct / 2, pos, texto, ha="center", va="center",
                     fontsize=8, color="white")
        else:
            ax1.text(pct + 1.5, pos, texto, ha="left", va="center",
                     fontsize=8, color="#37474F")
    ax1.set_xlim(0, 100)
    ax1.set_xlabel("Repartição das escolas da rede (%) — os dois grupos somam 100%")
    ax1.set_title("Quantas escolas têm o atributo")
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2,
               framealpha=1.0, fontsize=9)
    ax1.grid(axis="x", alpha=0.3)

    posicoes = np.arange(len(dados))
    altura = 0.38
    ax2.barh(posicoes + altura / 2, dados["abandono_com"], altura,
             label="Escolas que têm o atributo", color=COR_COM)
    ax2.barh(posicoes - altura / 2, dados["abandono_sem"], altura,
             label="Escolas que não têm", color=COR_SEM)
    maiores = dados[["abandono_com", "abandono_sem"]].max(axis=1)
    for posicao, maior, marca in zip(posicoes, maiores, dados["significancia"]):
        if marca:
            ax2.text(maior + 0.15, posicao, marca, fontsize=10, va="center")
    ax2.set_yticks(posicoes, rotulos)
    ax2.set_xlim(0, maiores.max() * 1.25)
    ax2.set_xlabel("Taxa média de abandono do ano seguinte (%)\n"
                   "— duas médias do mesmo indicador, uma por grupo")
    ax2.set_title("Abandono médio conforme a escola tem ou não o atributo")
    ax2.legend(loc="upper right", framealpha=1.0)
    ax2.grid(axis="x", alpha=0.3)

    fig.suptitle("Atributos de sim/não: quão comuns são e o abandono associado\n"
                 "(à esquerda, a repartição das escolas; à direita, o abandono "
                 "médio de cada grupo · * diferença significativa)",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "E6_binarias.png")


def figura_relacao_geral(resumo: pd.DataFrame) -> None:
    """E7 — todas as informações ordenadas pela relação com o abandono."""
    dados = resumo.sort_values("relacao")
    cores = [COR_AUMENTA if v > 0 else COR_REDUZ for v in dados["relacao"]]
    cores = [c if s else COR_NEUTRA for c, s in zip(cores, dados["significancia"])]

    fig, eixo = plt.subplots(figsize=(12, 13))
    barras = eixo.barh(dados["informacao"], dados["relacao"], color=cores)
    eixo.bar_label(barras, labels=[f"{v:+.2f}{s}" for v, s in
                                   zip(dados["relacao"], dados["significancia"])],
                   padding=3, fontsize=8)
    eixo.axvline(0, color="black", linewidth=0.8)
    eixo.set_xlim(dados["relacao"].min() * 1.4, dados["relacao"].max() * 1.35)
    eixo.set_xlabel("Relação com o abandono do ano seguinte\n"
                    "(vermelho: aumenta o risco · azul: reduz · cinza: sem relação "
                    "estatística)")
    eixo.set_title(f"As {len(dados)} informações numéricas ordenadas pela relação "
                   "com o abandono", fontsize=13, fontweight="bold")
    eixo.tick_params(labelsize=8)
    eixo.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    salvar_figura(fig, "E7_relacao_todas.png")


def figura_categorica(resumo: pd.DataFrame) -> None:
    """E8 — a única informação categórica: a região do estado."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    dados = resumo.sort_values("abandono_medio")
    barras = ax1.barh(dados["categoria"], dados["abandono_medio"], color=COR_AUMENTA)
    ax1.bar_label(barras, fmt="%.2f%%", padding=3, fontsize=10)
    ax1.set_xlim(0, dados["abandono_medio"].max() * 1.3)
    ax1.set_xlabel("Taxa média de abandono do ano seguinte (%)")
    ax1.set_title("Abandono médio por região do estado")
    ax1.grid(axis="x", alpha=0.3)

    barras = ax2.barh(dados["categoria"], dados["participacao"], color=COR_BARRA)
    ax2.bar_label(barras, labels=[f"{p:.0f}% ({n})" for p, n in
                                  zip(dados["participacao"], dados["escolas"])],
                  padding=3, fontsize=10)
    ax2.set_xlim(0, dados["participacao"].max() * 1.35)
    ax2.set_xlabel("% das observações (nº entre parênteses)")
    ax2.set_title("Peso de cada região no conjunto de dados")
    ax2.grid(axis="x", alpha=0.3)

    fig.suptitle("Região do estado: a única informação categórica",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "E8_mesorregiao.png")


# =============================================================================
# EXECUÇÃO
# =============================================================================

def main() -> None:
    df = carregar_dataset()
    features = colunas_features(df)
    tipos = {c: classificar(df[c], c) for c in features}
    continuas = [c for c in features if tipos[c] == "contínua"]
    binarias = [c for c in features if tipos[c] == "binária"]

    sep("Composição do conjunto de informações")
    print(f"Observações: {len(df)} | informações usadas na predição: {len(features)}")
    print(f"  contínuas: {len(continuas)} | binárias: {len(binarias)} "
          f"| categóricas: {len(CATEGORICAS)}")

    sep("E5 — Estatísticas descritivas das informações contínuas")
    resumo_continuas = descrever_continuas(df, continuas)
    print(resumo_continuas.drop(columns=["coluna", "tipo"]).round(3).to_string(index=False))
    figura_distribuicoes(df, resumo_continuas)

    sep("E6 — Informações de sim/não")
    resumo_binarias = descrever_binarias(df, binarias)
    print(resumo_binarias.drop(columns=["coluna", "tipo"]).round(3).to_string(index=False))
    figura_binarias(resumo_binarias)

    sep("E7 — Relação de todas as informações numéricas com o abandono")
    geral = pd.concat([resumo_continuas, resumo_binarias], ignore_index=True)
    significativas = geral[geral["significancia"] != ""]
    print(f"{len(significativas)} de {len(geral)} informações têm relação "
          f"estatisticamente significativa (p < {ALFA}) com o abandono do ano seguinte.")
    print("Sem relação detectada: "
          + ", ".join(geral.loc[geral["significancia"] == "", "informacao"]))
    figura_relacao_geral(geral)

    sep("E8 — Informação categórica (região do estado)")
    resumo_categorica = descrever_categorica(df, "CO_MESORREGIAO")
    print(resumo_categorica[["categoria", "escolas", "participacao",
                             "abandono_medio", "mediana", "p_valor",
                             "significancia"]].round(3).to_string(index=False))
    figura_categorica(resumo_categorica)

    destino = ROOT / "reports" / "estatisticas_features.csv"
    geral.to_csv(destino, index=False)
    destino_categorica = ROOT / "reports" / "estatisticas_mesorregiao.csv"
    resumo_categorica.to_csv(destino_categorica, index=False)
    print(f"\nEstatísticas salvas em: {destino} e {destino_categorica}")


if __name__ == "__main__":
    main()
