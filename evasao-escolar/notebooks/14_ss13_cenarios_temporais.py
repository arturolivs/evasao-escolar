"""
SS13 — Comparação de um único modelo em dois cenários temporais separados.

Comentário do orientador (SS13, Quadro 8 antigo / Quadro 9 atual, seção 6.3.2):
  "mostre a comparação usando 1 modelo e dois cenários:
   2022 prevendo 2023 e 2023 prevendo 2024."

O Quadro atual do teste temporal treina no par 2022→2023 e prevê o par
2023→2024 de uma vez só. Este notebook decompõe as DUAS transições anuais
para o modelo adotado (XGBoost), de forma que o desempenho de cada cenário
apareça isolado:

  Cenário A — 2022 → 2023 : características do Censo 2022  →  abandono 2023
  Cenário B — 2023 → 2024 : características do Censo 2023  →  abandono 2024

Cada cenário é uma coorte anual do dataset de modelagem (NU_ANO_CENSO). Para
que as métricas sejam de fora da amostra (e não um ajuste otimista sobre os
mesmos dados), cada cenário é avaliado por validação cruzada agrupada repetida
DENTRO da coorte: a cada repetição, 20% dos municípios daquele ano ficam de
fora do treino e servem de teste. É a mesma mecânica do Quadro 9 (notebook 07),
aqui separada por ano em vez de agregada.

Um único modelo — o adotado — em dois cenários, como o comentário pede.

Saídas:
  - Texto no console (quadro pronto para 6.3.2)
  - reports/metricas_ss13_cenarios.csv
  - reports/figuras/E9_ss13_cenarios.png
"""

from __future__ import annotations

from comum import salvar_figura, sep

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

from src.models.evaluate import calcular_metricas
from src.models.train import (
    ANO_COL,
    RANDOM_STATE,
    carregar_dataset,
    carregar_modelo,
    preparar_xy,
)

MODELO_ADOTADO = "xgboost_v1"

# Mesma configuração de repetições e proporção de teste do Quadro 9 (nb 07),
# para que os números dos dois quadros sejam lidos na mesma régua.
N_REPETICOES = 20
FRACAO_TESTE = 0.20
FRACAO_CRITICAS = 0.10  # top 10% de maior abandono = escolas "críticas"

CENARIOS = {
    2022: "2022 → 2023",  # características 2022 → abandono 2023
    2023: "2023 → 2024",  # características 2023 → abandono 2024
}

COR_CENARIO = {2022: "#1565C0", 2023: "#C62828"}


def roc_auc_binarizado(y_true: np.ndarray, y_pred: np.ndarray,
                       fracao: float = FRACAO_CRITICAS) -> float:
    """
    ROC-AUC tratando como positivas as escolas de maior abandono real
    (top `fracao`). Score = predição contínua da regressão (sem retreinar).
    Retorna NaN se a binarização degenerar (uma única classe no fold).
    """
    limiar = np.quantile(y_true, 1 - fracao)
    y_bin = (y_true >= limiar).astype(int)
    if y_bin.min() == y_bin.max():
        return float("nan")
    return float(roc_auc_score(y_bin, y_pred))


def avaliar_cenario(df_ano: pd.DataFrame) -> pd.DataFrame:
    """
    Validação cruzada agrupada repetida dentro de uma coorte anual.

    A cada repetição, 20% dos municípios daquele ano vão para teste; o modelo
    adotado é clonado e treinado nos 80% restantes. Uma linha por repetição.
    """
    X, y, grupos = preparar_xy(df_ano)
    gss = GroupShuffleSplit(n_splits=N_REPETICOES, test_size=FRACAO_TESTE,
                            random_state=RANDOM_STATE)
    linhas = []
    for rep, (idx_tr, idx_te) in enumerate(gss.split(X, y, groups=grupos), start=1):
        modelo = clone(carregar_modelo(MODELO_ADOTADO))
        modelo.fit(X.iloc[idx_tr], y.iloc[idx_tr])
        y_pred = modelo.predict(X.iloc[idx_te])
        y_te = y.iloc[idx_te].to_numpy()
        met = calcular_metricas(y_te, y_pred)
        met["roc_auc"] = roc_auc_binarizado(y_te, y_pred)
        met["repeticao"] = rep
        met["n_teste"] = len(idx_te)
        linhas.append(met)
    return pd.DataFrame(linhas)


def resumir(df_reps: pd.DataFrame, metrica: str) -> dict[str, float]:
    vals = df_reps[metrica].dropna()
    media, dp = vals.mean(), vals.std()
    ep = dp / np.sqrt(len(vals))
    return {
        "media": media, "dp": dp, "ep": ep,
        "ic_baixo": media - 1.96 * ep, "ic_alto": media + 1.96 * ep,
    }


METRICAS_QUADRO = [
    ("rmse", "Erro médio da taxa (p.p.)", "RMSE"),
    ("spearman", "Acerto da ordenação (0 a 1)", "Spearman"),
    ("precision_at_k", "Acerto na lista prioritária", "Precision@K"),
    ("roc_auc", "Separação alto/baixo risco", "ROC-AUC"),
]


def imprimir_quadro(resultados: dict[int, pd.DataFrame]) -> None:
    print(f"\nModelo adotado (XGBoost) — mesmo modelo nos dois cenários.")
    print(f"Cada célula: média ± IC 95% sobre {N_REPETICOES} repetições "
          f"(20% dos municípios em teste).\n")
    cab = f"{'Métrica':<32}" + "".join(f"{CENARIOS[a]:>22}" for a in CENARIOS)
    print(cab)
    print("-" * len(cab))
    for chave, rotulo, termo in METRICAS_QUADRO:
        linha = f"{rotulo + ' (' + termo + ')':<32}"
        for ano in CENARIOS:
            r = resumir(resultados[ano], chave)
            celula = f"{r['media']:.3f} ± {1.96 * r['ep']:.3f}"
            linha += f"{celula:>22}"
        print(linha)


def figura_cenarios(resultados: dict[int, pd.DataFrame]) -> None:
    metricas_fig = [
        ("rmse", "Erro médio da taxa (p.p.)\n— menor é melhor"),
        ("spearman", "Acerto da ordenação (Spearman)\n— maior é melhor"),
        ("precision_at_k", "Acerto na lista prioritária\n(Precision@K, top 10%) — maior é melhor"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for ax, (chave, titulo) in zip(axes, metricas_fig):
        dados = [resultados[ano][chave].dropna() for ano in CENARIOS]
        bp = ax.boxplot(dados, tick_labels=[CENARIOS[a] for a in CENARIOS],
                        patch_artist=True, medianprops=dict(color="black", lw=2),
                        widths=0.55)
        for patch, ano in zip(bp["boxes"], CENARIOS):
            patch.set_facecolor(COR_CENARIO[ano])
            patch.set_alpha(0.75)
        ax.set_title(titulo, fontsize=10)
        ax.set_xlabel("Cenário (ano das características → ano do abandono)")
        ax.grid(axis="y", alpha=0.3)
    fig.suptitle("SS13 — Modelo adotado em dois cenários temporais separados "
                 f"({N_REPETICOES} repetições, 20% dos municípios em teste)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "E9_ss13_cenarios.png")


def persistir(resultados: dict[int, pd.DataFrame]) -> None:
    linhas = []
    for ano, df_reps in resultados.items():
        for _, r in df_reps.iterrows():
            linhas.append({
                "cenario": CENARIOS[ano],
                "ano_features": ano,
                "ano_abandono": ano + 1,
                "modelo": "xgboost",
                "repeticao": int(r["repeticao"]),
                "n_teste": int(r["n_teste"]),
                "rmse": r["rmse"],
                "mae": r["mae"],
                "spearman": r["spearman"],
                "precision_at_k": r["precision_at_k"],
                "roc_auc": r["roc_auc"],
            })
    from comum import REPORTS_DIR
    caminho = REPORTS_DIR / "metricas_ss13_cenarios.csv"
    pd.DataFrame(linhas).to_csv(caminho, index=False)
    print(f"\nMétricas por repetição salvas em: {caminho}")


def main() -> None:
    sep("SS13 — UM MODELO, DOIS CENÁRIOS TEMPORAIS (2022→2023 e 2023→2024)")

    df = carregar_dataset()
    resultados: dict[int, pd.DataFrame] = {}
    for ano in CENARIOS:
        df_ano = df[df[ANO_COL] == ano].copy()
        n_munis = df_ano["CO_MUNICIPIO"].nunique()
        print(f"\nCenário {CENARIOS[ano]}: {len(df_ano)} escolas em {n_munis} "
              f"municípios (abandono médio {df_ano['taxa_abandono_t1'].mean():.2f}%).")
        resultados[ano] = avaliar_cenario(df_ano)

    imprimir_quadro(resultados)
    figura_cenarios(resultados)
    persistir(resultados)

    sep("LEITURA")
    print("""
Um único modelo — o adotado — avaliado nas duas transições anuais em separado.
A comparação mostra se o desempenho se sustenta de um ano para o outro; a
diferença de nível do abandono entre as coortes (1,36% em 2022 contra 0,88%
em 2023) ajuda a interpretar a variação das métricas de erro.
""")


if __name__ == "__main__":
    main()
