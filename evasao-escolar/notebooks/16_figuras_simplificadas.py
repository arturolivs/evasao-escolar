"""
Figuras do Capítulo 6 em linguagem de gestor.

As figuras técnicas (M5, M6, S1) usam vocabulário de aprendizado de máquina —
RMSE, Spearman, Precision@K, mean(|SHAP value|) — e nomes de biblioteca para os
modelos. Este script regera as que entram no corpo do texto com os mesmos
números e os rótulos usados nos quadros do capítulo, e acrescenta duas figuras
que hoje só existem como texto denso: o funil da amostra e a comparação dos
modelos no teste do ano nunca visto.

Depende de: notebooks 06, 07 e 08 (métricas e modelos) e 09 (SHAP).
Execução: python notebooks/16_figuras_simplificadas.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from comum import REPORTS_DIR, salvar_figura, sep
from matplotlib import pyplot as plt

from src.models.evaluate import precision_at_k
from src.recommend.labels import rotular_feature

COR_NEUTRA = "#9E9E9E"
COR_DESTAQUE = "#C62828"
COR_PERDA = "#B0BEC5"
COR_REFERENCIA = "#1565C0"

# Rótulos usados nos Quadros 9 e 10 do capítulo, para que figura e quadro
# falem a mesma língua.
NOMES_GESTOR = {
    "dummy": "Sem sistema\n(média da rede)",
    "dummy_media": "Sem sistema\n(média da rede)",
    "ridge": "Modelo de\nreferência linear",
    "random_forest": "Modelo de\nreferência\nem árvores",
    "xgboost": "Modelo adotado",
}
CORES_GESTOR = {
    "dummy": COR_NEUTRA,
    "dummy_media": COR_NEUTRA,
    "ridge": COR_REFERENCIA,
    "random_forest": "#2E7D32",
    "xgboost": COR_DESTAQUE,
}
ORDEM_MODELOS = ["dummy", "ridge", "random_forest", "xgboost"]


def virgula(valor: float, casas: int = 2) -> str:
    """Formata com vírgula decimal, como nos quadros do capítulo."""
    return f"{valor:.{casas}f}".replace(".", ",")


def eixo_com_virgula(ax, eixo: str = "y", casas: int = 2) -> None:
    from matplotlib.ticker import FuncFormatter

    formatador = FuncFormatter(lambda v, _: virgula(v, casas))
    (ax.yaxis if eixo == "y" else ax.xaxis).set_major_formatter(formatador)


# =============================================================================
# G1 — Funil da amostra: de 2.392 observações a 1.586 pares
# =============================================================================

def figura_funil_amostra() -> None:
    """Transforma o Quadro 5 em uma figura: onde as linhas ficam pelo caminho."""
    dados = pd.read_csv(REPORTS_DIR / "rastreabilidade_amostra.csv")
    restantes = dados["linhas_restantes"].tolist()
    removidas = dados["linhas_removidas"].tolist()

    etapas = [
        "Todas as observações de escola e ano\n(2022, 2023 e 2024)",
        "Anos que podem prever o ano seguinte\n(2022 e 2023)",
        "Pares completos, usados na previsão\n(características de um ano → abandono do seguinte)",
    ]
    motivos = [
        "",
        f"−{removidas[1]} observações de 2024:\nnão há 2025 para observar",
        f"−{removidas[2]} escolas que saíram da rede\nou deixaram de ofertar Ensino Médio",
    ]

    fig, ax = plt.subplots(figsize=(12, 5))
    posicoes = list(range(len(etapas)))[::-1]
    cores = [COR_NEUTRA, COR_NEUTRA, COR_DESTAQUE]

    for pos, valor, cor in zip(posicoes, restantes, cores):
        ax.barh(pos, valor, height=0.55, color=cor)
        ax.text(valor + 40, pos, f"{valor:,}".replace(",", "."),
                va="center", fontsize=14, fontweight="bold")

    for pos, motivo in zip(posicoes, motivos):
        if motivo:
            ax.text(60, pos + 0.42, motivo, va="bottom", ha="left",
                    fontsize=9.5, color="#455A64", style="italic")

    ax.set_yticks(posicoes)
    ax.set_yticklabels(etapas, fontsize=10.5)
    ax.set_xlim(0, max(restantes) * 1.18)
    ax.set_xlabel("Nº de observações de escola e ano")
    ax.set_title("Por que o conjunto encolhe de 2.392 para 1.586 observações",
                 fontsize=13, fontweight="bold", pad=14)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    salvar_figura(fig, "G1_funil_amostra.png")


# =============================================================================
# G2 — Teste do ano nunca visto: erra o valor, acerta a ordem
# =============================================================================

def figura_teste_ano_nunca_visto() -> None:
    """Transforma o Quadro 10 em duas barras lado a lado."""
    metricas = pd.read_csv(REPORTS_DIR / "metricas_xgboost.csv")
    temporal = metricas[metricas["avaliacao"] == "temporal_2023_2024"].copy()
    temporal["modelo"] = temporal["modelo"].replace({"dummy_media": "dummy"})
    temporal = temporal.set_index("modelo").loc[ORDEM_MODELOS]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    rotulos = [NOMES_GESTOR[m] for m in ORDEM_MODELOS]
    cores = [CORES_GESTOR[m] for m in ORDEM_MODELOS]

    piso = temporal.loc["dummy", "rmse"]
    barras = ax1.bar(rotulos, temporal["rmse"], color=cores)
    ax1.bar_label(barras, labels=[virgula(v) for v in temporal["rmse"]],
                  padding=3, fontsize=12)
    ax1.axhline(piso, color="#455A64", ls="--", lw=1.4)
    ax1.set_ylim(0, temporal["rmse"].max() * 1.42)
    ax1.text(1.5, temporal["rmse"].max() * 1.30,
             "nenhum modelo fica abaixo da linha tracejada:\n"
             "no valor da taxa, ninguém supera o piso",
             ha="center", fontsize=9.5, color="#455A64", style="italic")
    ax1.set_ylabel("Erro médio da taxa (pontos percentuais)")
    ax1.set_title("Errar o valor: quanto o sistema erra a taxa\n(menor é melhor)",
                  fontsize=12)
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_axisbelow(True)
    eixo_com_virgula(ax1, "y", 1)

    acerto = temporal["precision_at_k"] * 100
    barras = ax2.bar(rotulos, acerto, color=cores)
    ax2.bar_label(barras, fmt="%.0f em cada 100", padding=3, fontsize=11)
    ax2.set_ylim(0, acerto.max() * 1.45)
    ax2.set_ylabel("Escolas da lista que eram mesmo críticas (%)")
    ax2.set_title("Acertar a ordem: quantas escolas da lista\neram mesmo críticas (maior é melhor)",
                  fontsize=12)
    ax2.grid(axis="y", alpha=0.3)
    ax2.set_axisbelow(True)

    fig.suptitle("No ano nunca visto, o sistema erra o valor da taxa, mas acerta quem priorizar",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "G2_teste_ano_nunca_visto.png")


# =============================================================================
# G3 — Validação repetida, com os rótulos do Quadro 9
# =============================================================================

def figura_cv_repetida() -> None:
    """Regera a M6 com nomes de gestor e sem sigla de métrica no eixo."""
    dados = pd.read_csv(REPORTS_DIR / "metricas_cv_repetida.csv")

    paineis = [
        ("rmse", "Erro médio da taxa\n(pontos percentuais — menor é melhor)",
         ORDEM_MODELOS),
        ("spearman", "Acerto da ordenação\n(0 a 1 — maior é melhor)",
         ["ridge", "random_forest", "xgboost"]),
        ("precision_at_k", "Acerto na lista prioritária\n(0 a 1 — maior é melhor)",
         ORDEM_MODELOS),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))
    for ax, (coluna, titulo, modelos) in zip(axes, paineis):
        amostras = [dados.loc[dados.modelo == m, coluna].dropna() for m in modelos]
        caixas = ax.boxplot(amostras, patch_artist=True,
                            medianprops={"color": "black", "linewidth": 2})
        for caixa, modelo in zip(caixas["boxes"], modelos):
            caixa.set_facecolor(CORES_GESTOR[modelo])
            caixa.set_alpha(0.85)
        ax.set_xticklabels([NOMES_GESTOR[m] for m in modelos], fontsize=9)
        ax.set_title(titulo, fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        ax.set_axisbelow(True)
        eixo_com_virgula(ax, "y", 0 if coluna == "rmse" else 2)

    fig.suptitle("Cada medida ao longo das 20 repetições: a caixa mostra onde ficam "
                 "as repetições típicas",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "G3_cv_repetida.png")


# =============================================================================
# G4 — Acerto e alcance conforme o tamanho da lista
# =============================================================================

def figura_tamanho_da_lista() -> None:
    """Regera a M5 apenas com o modelo adotado, contra a escolha ao acaso."""
    from sklearn.base import clone

    from src.models.train import (
        carregar_dataset,
        carregar_modelo,
        preparar_xy,
        split_temporal,
    )

    df = carregar_dataset()
    treino, teste = split_temporal(df)
    X_tr, y_tr, _ = preparar_xy(treino)
    X_te, y_te, _ = preparar_xy(teste)

    modelo = clone(carregar_modelo("xgboost_v1"))
    modelo.fit(X_tr, y_tr)
    y_pred = modelo.predict(X_te)

    y_te = y_te.reset_index(drop=True)
    n = len(y_te)
    limiar = np.percentile(y_te, 90)
    criticas = set(np.flatnonzero(y_te.values >= limiar))
    ks = [10, 20, 30, 50, 75, 100, 125, 150, 200]

    acerto, alcance, acaso = [], [], []
    for k in ks:
        topo = set(np.argsort(y_pred)[::-1][:k])
        acerto.append(precision_at_k(y_te.values, y_pred, k) * 100)
        alcance.append(len(topo & criticas) / len(criticas) * 100)
        acaso.append(k / n * 100)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    for ax, serie, titulo, eixo in (
        (ax1, acerto,
         "Acerto: das escolas da lista,\nquantas eram mesmo críticas",
         "% da lista que era mesmo crítica"),
        (ax2, alcance,
         "Alcance: das escolas críticas da rede,\nquantas a lista encontra",
         "% das escolas críticas encontradas"),
    ):
        ax.plot(ks, serie, "o-", color=COR_DESTAQUE, lw=2.5, ms=7,
                label="Lista do sistema")
        ax.plot(ks, acaso, "--", color=COR_NEUTRA, lw=1.8,
                label="Escolha ao acaso")
        ax.set_xlabel("Tamanho da lista (nº de escolas atendidas)")
        ax.set_ylabel(eixo)
        ax.set_title(titulo, fontsize=12)
        ax.set_ylim(0, 100)
        ax.legend(fontsize=10)
        ax.grid(alpha=0.3)
        ax.set_axisbelow(True)

    fig.suptitle("O gestor escolhe o tamanho da lista conforme o orçamento "
                 "(teste do ano nunca visto)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "G4_tamanho_da_lista.png")


# =============================================================================
# G5 — Peso de cada característica, sem jargão no eixo
# =============================================================================

def figura_peso_caracteristicas(n_topo: int = 15) -> None:
    """Regera a importância SHAP como barras simples, na ordem do texto."""
    dados = pd.read_csv(REPORTS_DIR / "shap_importancia.csv")
    # A escala bruta do SHAP não tem leitura direta; o que interessa ao leitor é
    # a fatia que cada característica ocupa no peso total das previsões.
    dados["fatia"] = dados["shap_mean_abs"] / dados["shap_mean_abs"].sum() * 100
    dados = dados.sort_values("fatia", ascending=False).head(n_topo).iloc[::-1]
    rotulos = [rotular_feature(f) for f in dados["feature"]]

    fig, ax = plt.subplots(figsize=(11, 6.5))
    barras = ax.barh(rotulos, dados["fatia"], color=COR_DESTAQUE, height=0.7)
    ax.bar_label(barras, labels=[f"{virgula(v, 1)}%" for v in dados["fatia"]],
                 padding=4, fontsize=10)
    ax.set_xlim(0, dados["fatia"].max() * 1.15)
    ax.set_xlabel("Fatia do peso total das previsões (%)")
    ax.set_title(f"As {n_topo} características que mais pesam nas previsões do sistema\n"
                 f"(juntas, respondem por {dados['fatia'].sum():.0f}% do peso)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    salvar_figura(fig, "G5_peso_caracteristicas.png")


def main() -> None:
    sep("G1 — FUNIL DA AMOSTRA")
    figura_funil_amostra()

    sep("G2 — TESTE DO ANO NUNCA VISTO")
    figura_teste_ano_nunca_visto()

    sep("G3 — VALIDAÇÃO REPETIDA")
    figura_cv_repetida()

    sep("G4 — TAMANHO DA LISTA")
    figura_tamanho_da_lista()

    sep("G5 — PESO DAS CARACTERÍSTICAS")
    figura_peso_caracteristicas()


if __name__ == "__main__":
    main()
