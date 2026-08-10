"""
Figuras de apoio à monografia, com rótulos em linguagem de gestor.

As figuras das análises técnicas (A*, B*, C*, F*, M*, S*) usam os nomes das
colunas do dataset. Este script gera as quatro figuras que entram no corpo do
texto voltadas a um leitor não especialista em dados: o recorte do problema,
a variável prevista, as informações usadas e o desempenho do sistema.

Execução: python notebooks/12_figuras_monografia.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from comum import (
    COR_ABANDONO,
    CORES_ANOS,
    ROOT,
    carregar_parquet,
    salvar_figura,
    sep,
)
from matplotlib import pyplot as plt

from src.recommend.labels import rotular_feature

INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"

COR_NEUTRA = "#9E9E9E"
COR_DESTAQUE = "#C62828"


def carregar_taxas_com_matriculas() -> pd.DataFrame:
    taxas = carregar_parquet(
        INTERIM / "taxas_rendimento_pe_estadual_em.parquet",
        "python -m src.data.build_taxas_rendimento",
    )
    painel = carregar_parquet(
        INTERIM / "painel_escola_ano_pe_estadual_em.parquet",
        "python -m src.data.build_school_panel",
    )
    colunas = ["CO_ENTIDADE", "NU_ANO_CENSO", "QT_MAT_MED", "TP_LOCALIZACAO",
               "TP_LOCALIZACAO_DIFERENCIADA"]
    df = taxas.merge(painel[colunas], on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")
    df["alunos_que_abandonaram"] = df["QT_MAT_MED"] * df["TAXA_ABND_MED"] / 100
    return df


def figura_problema_critico(df: pd.DataFrame) -> None:
    """E1 — a taxa média cai, mas o abandono se concentra em poucas escolas."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    anos = sorted(df["NU_ANO_CENSO"].unique())
    medias = [df.loc[df.NU_ANO_CENSO == a, "TAXA_ABND_MED"].mean() for a in anos]
    ax1.plot(anos, medias, marker="o", color=COR_ABANDONO, linewidth=2.5, markersize=9)
    for ano, valor in zip(anos, medias):
        ax1.annotate(f"{valor:.2f}%", (ano, valor), textcoords="offset points",
                     xytext=(0, 12), ha="center", fontsize=11)
    ax1.set_xticks(anos)
    ax1.set_ylim(0, max(medias) * 1.35)
    ax1.set_ylabel("Taxa média de abandono (%)")
    ax1.set_title("A taxa média da rede vem caindo")
    ax1.grid(axis="y", alpha=0.3)

    ano_ref = max(anos)
    dados = (df[df.NU_ANO_CENSO == ano_ref]
             .dropna(subset=["alunos_que_abandonaram"])
             .sort_values("alunos_que_abandonaram", ascending=False))
    total = dados["alunos_que_abandonaram"].sum()
    n_escolas = len(dados)
    k = int(n_escolas * 0.10)
    concentrado = dados.head(k)["alunos_que_abandonaram"].sum() / total * 100
    rotulos = [f"As {k} escolas mais\ncríticas (10% da rede)",
               f"As outras {n_escolas - k}\nescolas (90% da rede)"]
    acumulado = [concentrado, 100 - concentrado]
    barras = ax2.bar(rotulos, acumulado, color=[COR_DESTAQUE, COR_NEUTRA])
    ax2.bar_label(barras, fmt="%.0f%%", padding=3, fontsize=12)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("% dos alunos que abandonaram")
    ax2.set_title(f"Mas o abandono se concentra em poucas escolas ({ano_ref})")
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle("O problema não é a média da rede: é a concentração",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "E1_problema_critico.png")

    print(f"{ano_ref}: {int(total)} alunos abandonaram, em {n_escolas} escolas.")
    for rotulo, valor in zip(rotulos, acumulado):
        print(f"  {rotulo.replace(chr(10), ' ')}: {valor:.1f}% do total")


def figura_alvo(df: pd.DataFrame, features: pd.DataFrame) -> None:
    """E2 — o que o sistema prevê: a taxa de abandono do ano seguinte."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    alvo = features["taxa_abandono_t1"]
    faixas = [
        ("Nenhum abandono\n(0%)", (alvo == 0).sum()),
        ("Baixo\n(0 a 2%)", ((alvo > 0) & (alvo <= 2)).sum()),
        ("Moderado\n(2 a 5%)", ((alvo > 2) & (alvo <= 5)).sum()),
        ("Alto\n(5 a 10%)", ((alvo > 5) & (alvo <= 10)).sum()),
        ("Crítico\n(acima de 10%)", (alvo > 10).sum()),
    ]
    rotulos = [f[0] for f in faixas]
    valores = [f[1] for f in faixas]
    cores = ["#BDBDBD", "#90CAF9", "#FFB74D", "#EF6C00", COR_DESTAQUE]
    barras = ax1.bar(rotulos, valores, color=cores)
    ax1.bar_label(barras, labels=[f"{v}\n({v / len(alvo) * 100:.0f}%)" for v in valores],
                  padding=3, fontsize=10)
    ax1.set_ylim(0, max(valores) * 1.25)
    ax1.set_ylabel("Nº de observações escola-ano")
    ax1.set_title("A maioria das escolas não registra abandono")
    ax1.grid(axis="y", alpha=0.3)

    ano_ref = df["NU_ANO_CENSO"].max()
    recorte = df[df.NU_ANO_CENSO == ano_ref].copy()
    # mesma definição de `is_loc_diferenciada` do pipeline (build_features.py):
    # qualquer código > 0 é localização diferenciada
    dif = recorte.TP_LOCALIZACAO_DIFERENCIADA.fillna(0) > 0
    grupos = {
        "Urbana": recorte[(recorte.TP_LOCALIZACAO == 1) & ~dif],
        "Rural": recorte[(recorte.TP_LOCALIZACAO == 2) & ~dif],
        "Indígena ou\nquilombola": recorte[dif],
    }
    nomes = list(grupos)
    medias = [g["TAXA_ABND_MED"].mean() for g in grupos.values()]
    contagens = [g["TAXA_ABND_MED"].notna().sum() for g in grupos.values()]
    barras = ax2.bar(nomes, medias, color=["#1565C0", "#2E7D32", COR_DESTAQUE])
    ax2.bar_label(barras, labels=[f"{m:.1f}%\n({n} escolas)" for m, n in zip(medias, contagens)],
                  padding=3, fontsize=10)
    ax2.set_ylim(0, max(medias) * 1.3)
    ax2.set_ylabel("Taxa média de abandono (%)")
    ax2.set_title(f"O risco não é igual em toda a rede ({ano_ref})")
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle("O indicador que o sistema aprende a prever",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "E2_alvo.png")

    for nome, media, n in zip(nomes, medias, contagens):
        print(f"  {nome.replace(chr(10), ' ')}: {media:.2f}% ({n} escolas)")


def figura_variaveis(features: pd.DataFrame) -> None:
    """E3 — quais informações mais acompanham o abandono do ano seguinte."""
    alvo = features["taxa_abandono_t1"]
    ignorar = {"CO_ENTIDADE", "NU_ANO_CENSO", "NO_ENTIDADE", "CO_MUNICIPIO",
               "NO_MUNICIPIO", "CO_MESORREGIAO", "taxa_abandono_t1"}
    candidatas = features.drop(columns=list(ignorar)).select_dtypes(include=[np.number])
    correlacoes = (candidatas.apply(lambda coluna: coluna.corr(alvo, method="spearman"))
                   .sort_values(key=abs, ascending=False)
                   .head(15)
                   .sort_values())

    fig, ax = plt.subplots(figsize=(11, 7))
    cores = [COR_DESTAQUE if v > 0 else "#1565C0" for v in correlacoes]
    barras = ax.barh([rotular_feature(n) for n in correlacoes.index], correlacoes.values,
                     color=cores)
    ax.bar_label(barras, fmt="%+.2f", padding=3, fontsize=10)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlim(correlacoes.min() * 1.35, correlacoes.max() * 1.25)
    ax.set_xlabel("Relação com o abandono do ano seguinte\n"
                  "(vermelho: aumenta o risco · azul: reduz o risco)")
    ax.set_title("As 15 características mais associadas ao abandono do ano seguinte",
                 fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    salvar_figura(fig, "E3_variaveis.png")

    print(correlacoes.sort_values(key=abs, ascending=False).round(3).to_string())


def capturas_do_modelo_adotado(tamanhos: list[int]) -> tuple[list[int], list[float], list[float]]:
    """
    Quanto das escolas realmente críticas uma lista de K escolas alcança, no
    teste temporal (features de 2023, abandono observado em 2024). Críticas são
    as do decil superior de abandono. Comparação: a mesma lista sorteada ao acaso.
    """
    from sklearn.base import clone

    from src.models.train import (
        carregar_dataset,
        carregar_modelo,
        preparar_xy,
        split_temporal,
    )

    treino, teste = split_temporal(carregar_dataset())
    X_treino, y_treino, _ = preparar_xy(treino)
    X_teste, y_teste, _ = preparar_xy(teste)

    # O modelo serializado foi treinado em todos os anos, inclusive o de teste.
    # Aqui a captura precisa ser honesta: mesma configuração, treinada só no
    # par anterior (2022→2023) e aplicada ao par que ela nunca viu.
    modelo = clone(carregar_modelo("xgboost_v1"))
    modelo.fit(X_treino, y_treino)
    previsto = modelo.predict(X_teste)

    limiar = np.percentile(y_teste, 90)
    criticas = set(np.flatnonzero(y_teste.values >= limiar))
    n = len(y_teste)
    print(f"Teste temporal: {n} escolas | limiar crítico (P90): {limiar:.1f}% | "
          f"{len(criticas)} escolas críticas")

    capturado, aleatorio = [], []
    for k in tamanhos:
        topo = set(np.argsort(-previsto)[:k])
        capturado.append(len(topo & criticas) / len(criticas) * 100)
        aleatorio.append(k / n * 100)
        print(f"  top-{k}: alcança {capturado[-1]:.1f}% das críticas "
              f"(ao acaso: {aleatorio[-1]:.1f}%)")
    return tamanhos, capturado, aleatorio


def figura_desempenho() -> None:
    """E4 — o que o desempenho do modelo significa para o gestor."""
    cv = pd.read_csv(ROOT / "reports" / "metricas_cv_repetida.csv")
    xgb = pd.read_csv(ROOT / "reports" / "metricas_xgboost.csv")
    cv_xgb = xgb[(xgb.modelo == "xgboost") & (xgb.avaliacao == "cv_groupkfold")]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    rotulos = ["Sem o sistema\n(escolha ao acaso)", "Com o sistema\n(lista de prioridade)"]
    acertos = [cv[cv.modelo == "dummy"]["precision_at_k"].mean() * 100,
               cv_xgb["precision_at_k"].mean() * 100]
    barras = ax1.bar(rotulos, acertos, color=[COR_NEUTRA, COR_DESTAQUE], width=0.55)
    ax1.bar_label(barras, labels=[f"{v:.0f} em cada 100" for v in acertos],
                  padding=3, fontsize=12)
    ax1.set_ylim(0, max(acertos) * 1.35)
    ax1.set_ylabel("% de acerto na lista prioritária")
    ax1.set_title("Das escolas indicadas, quantas eram mesmo críticas")
    ax1.grid(axis="y", alpha=0.3)

    tamanhos, capturado, aleatorio = capturas_do_modelo_adotado([50, 100, 150])
    largura = 0.35
    posicoes = np.arange(len(tamanhos))
    b1 = ax2.bar(posicoes - largura / 2, capturado, largura, label="Lista do sistema",
                 color=COR_DESTAQUE)
    b2 = ax2.bar(posicoes + largura / 2, aleatorio, largura, label="Escolha ao acaso",
                 color=COR_NEUTRA)
    ax2.bar_label(b1, fmt="%.0f%%", padding=3, fontsize=10)
    ax2.bar_label(b2, fmt="%.0f%%", padding=3, fontsize=10)
    ax2.set_xticks(posicoes, [f"{t} escolas\nvisitadas" for t in tamanhos])
    ax2.set_ylim(0, 85)
    ax2.set_ylabel("% das escolas críticas alcançadas")
    ax2.set_title("Quanto do problema a lista alcança")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle("O que o desempenho do sistema significa na prática",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "E4_desempenho.png")

    for rotulo, valor in zip(rotulos, acertos):
        print(f"  {rotulo.replace(chr(10), ' ')}: {valor:.1f}%")


def main() -> None:
    df = carregar_taxas_com_matriculas()
    features = carregar_parquet(
        PROCESSED / "features.parquet", "python -m src.features.build_features"
    )

    sep("E1 — Recorte do problema")
    figura_problema_critico(df)

    sep("E2 — Variável prevista")
    figura_alvo(df, features)

    sep("E3 — Informações usadas")
    figura_variaveis(features)

    sep("E4 — Desempenho")
    figura_desempenho()


if __name__ == "__main__":
    main()
