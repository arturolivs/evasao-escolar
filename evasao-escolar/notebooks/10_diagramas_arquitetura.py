"""
Diagramas de arquitetura (Capítulo 4 da monografia).
Gera, de forma determinística, as visões arquiteturais do sistema no estilo do
modelo 4+1 de Kruchten, usando matplotlib (o ambiente não tem Graphviz):

  arq1_casos_uso.png       — casos de uso (aspectos funcionais)
  arq2_pacotes.png         — visão estrutural: dependências entre pacotes
  arq3_componentes.png     — visão estrutural: componentes e fluxo de dados
  arq4_atividades.png      — visão comportamental: execução do pipeline
  arq5_implantacao.png     — visão de implementação e implantação

Saída: reports/figuras/arq*.png
"""

from __future__ import annotations

from comum import FIGURAS_DIR, salvar_figura

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch

AZUL, VERDE, VERM, CINZA, AMAR = "#1565C0", "#2E7D32", "#C62828", "#9E9E9E", "#F9A825"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})


# ---------------------------------------------------------------------------
# Primitivas de desenho
# ---------------------------------------------------------------------------

def box(ax, x, y, w, h, text, fc="#FFFFFF", ec="#333333", fs=9.5,
        style="round,pad=0.02,rounding_size=0.06", lw=1.4, bold=False, tc="#111111"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style,
                                fc=fc, ec=ec, lw=lw, mutation_scale=10))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal", color=tc, wrap=True)


def datastore(ax, x, y, w, h, text, fc="#ECEFF1"):
    box(ax, x, y, w, h, text, fc=fc, ec="#546E7A",
        style="round,pad=0.02,rounding_size=0.05", lw=1.3)


def ellipse(ax, cx, cy, w, h, text, fc="#E3F2FD", ec=AZUL):
    ax.add_patch(Ellipse((cx, cy), w, h, fc=fc, ec=ec, lw=1.3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=8.6)


def arrow(ax, p, q, style="-|>", dashed=False, color="#333333", lw=1.4,
          label=None, lc="#444444", rad=0.0, fs=8.2):
    ls = (0, (5, 3)) if dashed else "solid"
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=14,
                                 lw=lw, color=color, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=2, shrinkB=2))
    if label:
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        ax.text(mx, my, label, ha="center", va="center", fontsize=fs,
                color=lc, bbox=dict(fc="white", ec="none", pad=0.6))


def actor(ax, x, y, label, color="#222222"):
    ax.add_patch(Circle((x, y + 0.34), 0.10, fc="white", ec=color, lw=1.6))
    ax.plot([x, x], [y + 0.24, y - 0.12], color=color, lw=1.6)
    ax.plot([x - 0.18, x + 0.18], [y + 0.12, y + 0.12], color=color, lw=1.6)
    ax.plot([x, x - 0.16], [y - 0.12, y - 0.40], color=color, lw=1.6)
    ax.plot([x, x + 0.16], [y - 0.12, y - 0.40], color=color, lw=1.6)
    ax.text(x, y - 0.58, label, ha="center", va="center", fontsize=8.8, fontweight="bold")


def package(ax, x, y, w, h, titulo, itens, fc="#FFFFFF", ec="#37474F"):
    ax.add_patch(FancyBboxPatch((x, y + h), w * 0.42, 0.22, boxstyle="square,pad=0",
                                fc=fc, ec=ec, lw=1.3))
    ax.text(x + w * 0.21, y + h + 0.11, titulo, ha="center", va="center",
            fontsize=8.8, fontweight="bold")
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                                fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h - 0.18, "\n".join(itens), ha="center", va="top",
            fontsize=7.8, color="#37474F")


def finaliza(ax, xlim, ylim, titulo, aspect="equal"):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect(aspect)
    ax.axis("off")
    ax.set_title(titulo, fontsize=12, fontweight="bold", pad=8)


# ---------------------------------------------------------------------------
# ARQ1 — Casos de uso
# ---------------------------------------------------------------------------

def diagrama_casos_uso():
    fig, ax = plt.subplots(figsize=(10, 6.2))
    # fronteira do sistema
    ax.add_patch(FancyBboxPatch((3.0, 0.3), 4.0, 5.4, boxstyle="round,pad=0.02",
                                fc="#FAFAFA", ec="#90A4AE", lw=1.6))
    ax.text(5.0, 5.5, "Sistema de Predição de Evasão Escolar",
            ha="center", va="center", fontsize=9.5, fontweight="bold", color="#455A64")

    ucs = {
        "u1": (5.0, 4.8, "Consultar ranking\nde risco (t+1)"),
        "u2": (5.0, 3.9, "Visualizar explicação\nSHAP por escola"),
        "u3": (5.0, 3.0, "Inspecionar diagnóstico\nde resíduos (equidade)"),
        "u4": (5.0, 2.1, "Executar pipeline\nde dados (ETL→features)"),
        "u5": (5.0, 1.2, "Treinar / atualizar\nmodelo (tuning)"),
    }
    for cx, cy, t in ucs.values():
        ellipse(ax, cx, cy, 2.5, 0.74, t)

    actor(ax, 1.2, 3.6, "Gestor\n(Secretaria de Educação)", color=AZUL)
    actor(ax, 8.8, 3.6, "Analista /\nPesquisador", color=VERDE)
    actor(ax, 8.8, 1.0, "INEP\n(fonte de dados)", color=CINZA)

    casos_do_gestor = ("u1", "u2", "u3")
    for u in casos_do_gestor:
        arrow(ax, (1.55, 3.7), (ucs[u][0] - 1.25, ucs[u][1]), style="-", color=AZUL, lw=1.2)

    casos_do_analista = ("u4", "u5", "u1")
    for u in casos_do_analista:
        arrow(ax, (8.45, 3.7), (ucs[u][0] + 1.25, ucs[u][1]), style="-", color=VERDE, lw=1.2)

    arrow(ax, (8.45, 1.0), (ucs["u4"][0] + 1.25, ucs["u4"][1] - 0.1),
          style="-", color=CINZA, lw=1.2, dashed=True, label="«fornece»")

    finaliza(ax, (0.2, 9.8), (0.2, 5.9), "Figura – Diagrama de casos de uso")
    salvar_figura(fig, "arq1_casos_uso.png")


# ---------------------------------------------------------------------------
# ARQ2 — Pacotes
# ---------------------------------------------------------------------------

def diagrama_pacotes():
    fig, ax = plt.subplots(figsize=(9.5, 6.6))
    package(ax, 0.6, 5.2, 2.6, 0.9, "notebooks", ["01..09 análises", "10 diagramas"], fc="#FFF8E1")
    package(ax, 6.3, 5.2, 2.6, 0.9, "tests", ["test_etl/panel/taxas", "test_models/explain"], fc="#FFF8E1")

    package(ax, 3.4, 5.2, 2.6, 0.9, "src.recommend", ["dashboard (Streamlit)", "— planejado —"], fc="#FCE4EC")
    package(ax, 3.4, 3.6, 2.6, 1.0, "src.models", ["train  ·  evaluate", "explain (SHAP)"], fc="#E8F5E9")
    package(ax, 3.4, 2.0, 2.6, 0.9, "src.features", ["build_features", "(join t → t+1)"], fc="#E3F2FD")
    package(ax, 3.4, 0.4, 2.6, 1.0, "src.data", ["load · filtros · painel", "build_* (indicadores)"], fc="#E3F2FD")
    package(ax, 7.0, 0.7, 2.0, 0.7, "src.data.config", ["caminhos, anos"], fc="#ECEFF1")

    def dependencia(origem, destino, **kwargs):
        arrow(ax, origem, destino, style="-|>", dashed=True, color="#546E7A", **kwargs)

    dependencia((1.9, 5.2), (4.3, 4.6), label="usa")   # notebooks → models
    dependencia((7.6, 5.2), (5.1, 4.6), label="usa")   # tests → models
    dependencia((4.7, 5.2), (4.7, 4.6))                # recommend → models
    dependencia((4.7, 3.6), (4.7, 3.0))                # models → features
    dependencia((4.7, 2.0), (4.7, 1.4))                # features → data
    dependencia((6.0, 0.9), (7.0, 1.0))                # data → config
    dependencia((6.0, 4.1), (7.6, 1.4), rad=-0.2)      # models → config

    ax.text(4.7, 6.45, "dependência  ┄┄▷  (seta tracejada = «usa»)",
            ha="center", fontsize=8, color="#546E7A")
    finaliza(ax, (0.2, 9.4), (0.2, 6.7), "Figura – Diagrama de pacotes (visão estrutural)")
    salvar_figura(fig, "arq2_pacotes.png")


# ---------------------------------------------------------------------------
# ARQ3 — Componentes e fluxo de dados
# ---------------------------------------------------------------------------

def diagrama_componentes():
    fig, ax = plt.subplots(figsize=(11, 6.2))
    datastore(ax, 0.3, 4.6, 2.1, 1.0, "data/raw\nCenso, Taxas, INSE,\nIRD, TDI, AFD", fc="#ECEFF1")
    box(ax, 0.3, 2.7, 2.1, 1.1, "«component»\nETL\n(src.data)", fc="#E3F2FD", ec=AZUL, bold=True)
    datastore(ax, 0.3, 1.0, 2.1, 0.9, "data/interim\n*.parquet", fc="#ECEFF1")

    box(ax, 3.1, 2.7, 2.1, 1.1, "«component»\nFeature Eng.\n(src.features)", fc="#E3F2FD", ec=AZUL, bold=True)
    datastore(ax, 3.1, 1.0, 2.1, 0.9, "data/processed\nfeatures.parquet", fc="#ECEFF1")

    box(ax, 5.9, 2.7, 2.1, 1.1, "«component»\nModelagem\n(train·evaluate)", fc="#E8F5E9", ec=VERDE, bold=True)
    datastore(ax, 5.9, 1.0, 2.1, 0.9, "models/\nxgboost_v1.joblib", fc="#FFF3E0")

    box(ax, 8.7, 4.0, 2.1, 1.1, "«component»\nExplicabilidade\n(explain · SHAP)", fc="#E8F5E9", ec=VERDE, bold=True)
    box(ax, 8.7, 2.0, 2.1, 1.1, "«component»\nDashboard\n(src.recommend)\n— planejado —", fc="#FCE4EC", ec=VERM, bold=True)
    actor(ax, 9.75, 0.7, "Gestor", color=AZUL)

    arrow(ax, (1.35, 4.6), (1.35, 3.8))                       # raw → ETL
    arrow(ax, (1.35, 2.7), (1.35, 1.9))                       # ETL → interim
    arrow(ax, (2.4, 1.45), (3.1, 2.9), label="lê")            # interim → feateng
    arrow(ax, (4.15, 2.7), (4.15, 1.9))                       # feateng → processed
    arrow(ax, (5.2, 1.45), (5.9, 2.9), label="lê")            # processed → modelagem
    arrow(ax, (6.95, 2.7), (6.95, 1.9))                       # modelagem → models
    arrow(ax, (8.0, 1.45), (8.7, 2.3), label="carrega")       # models → dashboard
    arrow(ax, (8.0, 3.4), (8.7, 4.3), label="carrega")        # models → explain
    arrow(ax, (8.7, 4.2), (8.7, 3.1), style="-|>", color=VERM, label="usa", rad=0.0)  # explain → dashboard
    arrow(ax, (9.75, 2.0), (9.75, 1.1), color=VERM)           # dashboard → gestor

    finaliza(ax, (0.0, 11.2), (0.2, 5.9),
             "Figura – Diagrama de componentes e fluxo de dados", aspect="auto")
    salvar_figura(fig, "arq3_componentes.png")


# ---------------------------------------------------------------------------
# ARQ4 — Atividades (execução do pipeline)
# ---------------------------------------------------------------------------

def diagrama_atividades():
    fig, ax = plt.subplots(figsize=(7.6, 9.6))
    ax.add_patch(Circle((1.5, 9.4), 0.12, fc="#111111"))   # nó inicial
    passos = [
        "Carregar microdados do Censo (load)",
        "Filtrar PE · estadual · EM ativo (filter)",
        "Construir painel escola×ano (build_school_panel)",
        "Integrar indicadores: Taxas, INSE, IRD, TDI, AFD",
        "Construir features t → alvo t+1 (build_features)",
        "Treinar baselines e tunar XGBoost (train, GridSearchCV)",
        "Avaliar: CV agrupada + validação temporal (evaluate)",
        "Serializar modelo (models/xgboost_v1.joblib)",
        "Explicar (SHAP) e diagnosticar resíduos (explain)",
        "Servir ranking e explicações no dashboard [planejado]",
    ]
    y = 8.5
    anterior = (1.5, 9.28)
    for i, txt in enumerate(passos):
        fc = "#FCE4EC" if "planejado" in txt else ("#E8F5E9" if i >= 5 else "#E3F2FD")
        ec = VERM if "planejado" in txt else (VERDE if i >= 5 else AZUL)
        box(ax, 0.2, y, 5.4, 0.62, txt, fc=fc, ec=ec, fs=8.6)
        arrow(ax, anterior, (2.9, y + 0.62))
        anterior = (2.9, y)
        y -= 0.86

    # nó final
    ax.add_patch(Circle((2.9, y + 0.30), 0.16, fc="white", ec="#111111", lw=1.6))
    ax.add_patch(Circle((2.9, y + 0.30), 0.09, fc="#111111"))
    arrow(ax, anterior, (2.9, y + 0.46))
    finaliza(ax, (0.0, 6.0), (y - 0.1, 9.8), "Figura – Diagrama de atividades do pipeline")
    salvar_figura(fig, "arq4_atividades.png")


# ---------------------------------------------------------------------------
# ARQ5 — Implantação
# ---------------------------------------------------------------------------

def diagrama_implantacao():
    fig, ax = plt.subplots(figsize=(10.5, 6.0))

    # nó: estação de desenvolvimento
    box(ax, 0.3, 0.6, 4.0, 4.6, "", fc="#F5F5F5", ec="#455A64", lw=1.8, style="square,pad=0")
    ax.text(2.3, 5.0, "«device» Estação de desenvolvimento", ha="center", fontweight="bold", fontsize=9)
    box(ax, 0.6, 3.3, 3.4, 1.3, "«execution environment»\nPython 3.10 (venv)\npipeline ETL · modelagem · SHAP",
        fc="#E3F2FD", ec=AZUL)
    datastore(ax, 0.6, 2.1, 3.4, 0.9, "data/  raw · interim · processed (Parquet)")
    datastore(ax, 0.6, 0.9, 3.4, 0.9, "models/  *.joblib", fc="#FFF3E0")

    # nó: contêiner docker
    box(ax, 5.7, 1.6, 3.4, 3.0, "", fc="#F5F5F5", ec=VERM, lw=1.8, style="square,pad=0")
    ax.text(7.4, 4.4, "«container» Docker  [planejado]", ha="center", fontweight="bold", fontsize=9, color=VERM)
    box(ax, 6.0, 2.9, 2.8, 1.1, "«component»\nApp Streamlit\n(src.recommend)", fc="#FCE4EC", ec=VERM)
    datastore(ax, 6.0, 1.8, 2.8, 0.8, "modelo serializado\n(xgboost_v1.joblib)", fc="#FFF3E0")

    # nó: navegador
    box(ax, 9.6, 2.6, 1.6, 1.2, "«device»\nNavegador\ndo gestor", fc="#E8F5E9", ec=VERDE)

    arrow(ax, (4.3, 2.6), (5.7, 3.2), label="build /\ncopia modelo")
    arrow(ax, (9.1, 3.2), (9.6, 3.2), label="HTTPS")

    finaliza(ax, (0.0, 11.4), (0.4, 5.2),
             "Figura – Diagrama de implantação", aspect="auto")
    salvar_figura(fig, "arq5_implantacao.png")


def main():
    diagrama_casos_uso()
    diagrama_pacotes()
    diagrama_componentes()
    diagrama_atividades()
    diagrama_implantacao()
    print("Diagramas de arquitetura salvos em:", FIGURAS_DIR)


if __name__ == "__main__":
    main()
