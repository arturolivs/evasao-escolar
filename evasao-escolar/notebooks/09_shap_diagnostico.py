"""
Fase 7 — Explicabilidade (SHAP) e diagnóstico por resíduos.
Escolas estaduais de EM em PE — modelo final XGBoost (models/xgboost_v1.joblib).

Responde às perguntas:
  S1. Globalmente, quais indicadores institucionais mais movem o risco de
      abandono previsto, e em que direção? (SHAP global — beeswarm + barras)
  S2. A direção de cada feature (valor alto → mais/menos risco) é coerente
      com a teoria? (correlação valor × SHAP)
  S3. Por que UMA escola específica recebeu sua pontuação de risco?
      (SHAP local — waterfall de uma escola de alto risco e uma resiliente)
  S4. (P3) Quais escolas abandonam significativamente ACIMA ou ABAIXO do
      que o seu perfil institucional prevê? (análise de resíduos)
  S5. O modelo tem viés sistemático por grupo de localização? (equidade)

Escala: os valores SHAP estão em unidades de sqrt(taxa de abandono) — o
modelo final usa transformação sqrt no target. O ranking e o sinal das
contribuições permanecem válidos (sqrt é monotônica). Predições e resíduos
são devolvidos na escala original (%). Ver src/models/explain.py.

Saídas:
  - Texto no console
  - Figuras salvas em: reports/figuras/  (prefixo S*)
  - Tabelas em: reports/shap_importancia.csv, reports/residuos_diagnostico.csv
"""

from __future__ import annotations

from comum import (
    COR_ABANDONO,
    COR_RURAL,
    COR_URBANA,
    FIGURAS_DIR,
    REPORTS_DIR,
    salvar_figura,
    sep,
)

import matplotlib.pyplot as plt
import numpy as np
import shap

from src.models.explain import (
    analise_residuos,
    calcular_shap_values,
    direcao_features,
    importancia_shap,
    preparar_matriz_shap,
    residuos_validacao_temporal,
    resumo_residuos_por_grupo,
)
from src.models.train import carregar_dataset, carregar_modelo, colunas_features

COR_CONTRIBUICAO_POSITIVA = COR_ABANDONO
COR_CONTRIBUICAO_NEGATIVA = COR_URBANA


# =============================================================================
# S1 — SHAP GLOBAL (beeswarm + barras)
# =============================================================================

def shap_global(shap_values) -> None:
    sep("S1 — SHAP GLOBAL (importância e dispersão das contribuições)")

    imp = importancia_shap(shap_values)
    print("\nTop 15 features por |SHAP| médio (unidades de sqrt(%)):")
    for _, r in imp.head(15).iterrows():
        print(f"  {r['feature']:<28} {r['shap_mean_abs']:.4f}")

    imp.to_csv(REPORTS_DIR / "shap_importancia.csv", index=False)
    print(f"\nTabela salva em: {REPORTS_DIR / 'shap_importancia.csv'}")

    plt.figure(figsize=(9, 7))
    shap.plots.beeswarm(shap_values, max_display=15, show=False)
    fig = plt.gcf()
    fig.suptitle("S1 — SHAP global (beeswarm): contribuição por escola e feature",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "S1_shap_beeswarm.png")

    plt.figure(figsize=(8, 6))
    shap.plots.bar(shap_values, max_display=15, show=False)
    fig = plt.gcf()
    fig.suptitle("S1 — SHAP global (barras): importância média |SHAP|",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "S1_shap_barras.png")


# =============================================================================
# S2 — DIREÇÃO DAS FEATURES
# =============================================================================

def shap_direcao(shap_values) -> None:
    sep("S2 — DIREÇÃO DAS FEATURES (valor alto → mais ou menos risco?)")

    dirs = direcao_features(shap_values).head(15)
    print(f"\n{'Feature':<28}{'|SHAP|':>10}{'corr':>9}  direção")
    print("-" * 64)
    for _, r in dirs.iterrows():
        corr = "  nan" if np.isnan(r["corr_valor_shap"]) else f"{r['corr_valor_shap']:+.2f}"
        print(f"  {r['feature']:<26}{r['shap_mean_abs']:>10.4f}{corr:>9}  {r['direcao']}")

    top = dirs.iloc[::-1]
    cores = [COR_CONTRIBUICAO_POSITIVA if c > 0 else COR_CONTRIBUICAO_NEGATIVA
             for c in top["corr_valor_shap"].fillna(0)]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top["feature"], top["shap_mean_abs"], color=cores, alpha=0.85)
    ax.set_xlabel("|SHAP| médio (unidades de sqrt(%))")
    ax.set_title("S2 — Importância e direção das features\n"
                 "vermelho = valor alto aumenta risco · azul = reduz",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "S2_shap_direcao.png")


# =============================================================================
# S3 — SHAP LOCAL (waterfall de casos)
# =============================================================================

def shap_local(shap_values, df, modelo) -> None:
    sep("S3 — SHAP LOCAL (por que esta escola recebeu sua pontuação?)")

    y_pred = np.asarray(modelo.predict(df[colunas_features(df)]), dtype=float)
    casos = [
        ("ALTO RISCO", int(np.argmax(y_pred)), "S3_waterfall_alto_risco.png"),
        ("BAIXO RISCO", int(np.argmin(y_pred)), "S3_waterfall_baixo_risco.png"),
    ]

    for rotulo, idx, arquivo in casos:
        escola = df.iloc[idx]
        print(f"\n[{rotulo}] {escola.get('NO_ENTIDADE', '?')} "
              f"({escola.get('NO_MUNICIPIO', '?')}, {int(escola['NU_ANO_CENSO'])}) "
              f"— previsto={y_pred[idx]:.1f}%  real={escola['taxa_abandono_t1']:.1f}%")

        plt.figure(figsize=(9, 6))
        shap.plots.waterfall(shap_values[idx], max_display=12, show=False)
        fig = plt.gcf()
        fig.suptitle(f"S3 — SHAP local ({rotulo.lower()}): "
                     f"{escola.get('NO_ENTIDADE', '?')}",
                     fontsize=11, fontweight="bold")
        fig.tight_layout()
        salvar_figura(fig, arquivo)


# =============================================================================
# S4 — DIAGNÓSTICO POR RESÍDUOS (P3)
# =============================================================================

def relatorio_residuos_extremos(res) -> None:
    print("\n10 escolas que abandonam MAIS do que o perfil prevê (alerta):")
    for _, r in res.acima.head(10).iterrows():
        print(f"  {r.get('NO_ENTIDADE', '?'):<34} {int(r['NU_ANO_CENSO'])}  "
              f"real={r['y_real']:5.1f}%  prev={r['y_pred']:5.1f}%  "
              f"resíduo={r['residuo']:+5.1f} (z={r['residuo_z']:+.1f})")

    print("\n10 escolas que abandonam MENOS do que o perfil prevê (resilientes):")
    for _, r in res.abaixo.head(10).iterrows():
        print(f"  {r.get('NO_ENTIDADE', '?'):<34} {int(r['NU_ANO_CENSO'])}  "
              f"real={r['y_real']:5.1f}%  prev={r['y_pred']:5.1f}%  "
              f"resíduo={r['residuo']:+5.1f} (z={r['residuo_z']:+.1f})")


def figura_residuos(res) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    ax.scatter(res.df["y_pred"], res.df["y_real"], alpha=0.3, s=14,
               color=COR_CONTRIBUICAO_POSITIVA)
    lim = max(res.df["y_real"].max(), res.df["y_pred"].max()) * 1.05
    ax.plot([0, lim], [0, lim], "k--", lw=1.2, label="previsto = real")
    ax.set_xlabel("Abandono previsto pelo perfil (%)")
    ax.set_ylabel("Abandono real (%)")
    ax.set_title("Real × previsto (acima da linha = abandona mais que o esperado)")
    ax.legend(fontsize=9)

    ax = axes[1]
    ax.hist(res.df["residuo"], bins=40, color=COR_CONTRIBUICAO_POSITIVA, alpha=0.8)
    ax.axvline(0, color="black", lw=1.2)
    ax.set_xlabel("Resíduo (real − previsto, p.p.)")
    ax.set_ylabel("Nº de escolas-ano")
    ax.set_title("Distribuição dos resíduos")

    fig.suptitle("S4 — Diagnóstico por resíduos (P3): escolas fora do esperado",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "S4_residuos_diagnostico.png")


def diagnostico_residuos(modelo, df) -> None:
    sep("S4 — DIAGNÓSTICO POR RESÍDUOS (escolas fora do esperado — P3)")

    res = analise_residuos(modelo, df, top_n=20)

    print(f"\nResíduo (real − previsto): média={res.df['residuo'].mean():.2f}  "
          f"DP={res.df['residuo'].std():.2f} p.p.")

    relatorio_residuos_extremos(res)

    res.df.to_csv(REPORTS_DIR / "residuos_diagnostico.csv", index=False)
    print(f"\nTabela completa salva em: {REPORTS_DIR / 'residuos_diagnostico.csv'}")

    figura_residuos(res)


# =============================================================================
# S5 — EQUIDADE: RESÍDUOS POR GRUPO DE LOCALIZAÇÃO (validação temporal)
# =============================================================================

def figura_equidade(res) -> None:
    grupos = ["urbana", "rural", "diferenciada"]
    cores_grupo = {"urbana": COR_URBANA, "rural": COR_RURAL, "diferenciada": COR_ABANDONO}
    dados = [res.loc[res["grupo"] == g, "residuo"] for g in grupos]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    bp = ax.boxplot(dados, tick_labels=grupos, patch_artist=True,
                    medianprops=dict(color="black", lw=2))
    for patch, g in zip(bp["boxes"], grupos):
        patch.set_facecolor(cores_grupo[g])
        patch.set_alpha(0.6)
    ax.axhline(0, color="black", lw=1, ls="--")
    ax.set_ylabel("Resíduo (real − previsto, p.p.)")
    ax.set_title("Distribuição do resíduo por grupo")

    ax = axes[1]
    medias = [res.loc[res["grupo"] == g, "residuo"].mean() for g in grupos]
    ax.bar(grupos, medias, color=[cores_grupo[g] for g in grupos], alpha=0.8)
    ax.axhline(0, color="black", lw=1)
    for i, m in enumerate(medias):
        ax.text(i, m + (0.1 if m >= 0 else -0.3), f"{m:+.2f}",
                ha="center", fontweight="bold")
    ax.set_ylabel("Resíduo médio (p.p.)")
    ax.set_title("Viés médio por grupo (negativo = superpredição)")

    fig.suptitle("S5 — Equidade: resíduo do XGBoost por localização (teste temporal 2023→2024)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    salvar_figura(fig, "S5_equidade_grupos.png")


def equidade_grupos(modelo, df) -> None:
    sep("S5 — EQUIDADE: RESÍDUO POR GRUPO DE LOCALIZAÇÃO (XGBoost, teste temporal)")

    res = residuos_validacao_temporal(modelo, df)
    resumo = resumo_residuos_por_grupo(res)

    print(f"\n{'Grupo':<16}{'resíduo médio':>15}{'DP':>9}{'n':>7}")
    print("-" * 47)
    for _, r in resumo.iterrows():
        print(f"  {r['grupo']:<14}{r['media']:>15.2f}{r['desvio']:>9.2f}{int(r['n']):>7}")
    print("\nResíduo = real − previsto (p.p.). Negativo ⇒ o modelo SUPERPREDIZ "
          "o abandono (prevê mais do que ocorre).")

    res.to_csv(REPORTS_DIR / "residuos_grupo_temporal.csv", index=False)
    figura_equidade(res)


# =============================================================================
# SUMÁRIO
# =============================================================================

def sumario(shap_values) -> None:
    sep("SUMÁRIO EXECUTIVO — FASE 7 (SHAP + RESÍDUOS)")

    imp = importancia_shap(shap_values)
    top5 = ", ".join(imp.head(5)["feature"])
    print(f"""
MODELO EXPLICADO: XGBoost final (models/xgboost_v1.joblib, target sqrt)

SHAP GLOBAL
  • Top 5 drivers do risco previsto: {top5}
  • Beeswarm e barras em reports/figuras/S1_*

DIREÇÃO E CASOS
  • Direção (valor × SHAP) em reports/figuras/S2_shap_direcao.png
  • Waterfalls (alto/baixo risco) em reports/figuras/S3_*

DIAGNÓSTICO P3
  • Escolas acima/abaixo do esperado em reports/residuos_diagnostico.csv
  • Figura reports/figuras/S4_residuos_diagnostico.png

ARTEFATOS
  • reports/shap_importancia.csv
  • reports/residuos_diagnostico.csv
  • reports/figuras/S1–S4

PRÓXIMA FASE (8)
  → Dashboard (src/recommend/) — depende da decisão de escopo com orientador
""")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    df = carregar_dataset()
    modelo = carregar_modelo("xgboost_v1")

    print(f"\nDataset: {len(df):,} obs  |  modelo: xgboost_v1 (TransformedTargetRegressor)")
    matriz = preparar_matriz_shap(modelo, df[colunas_features(df)])
    print(f"Matriz SHAP: {matriz.shape[0]:,} obs × {matriz.shape[1]} features transformadas")

    shap_values = calcular_shap_values(modelo, df[colunas_features(df)])

    shap_global(shap_values)
    shap_direcao(shap_values)
    shap_local(shap_values, df, modelo)
    diagnostico_residuos(modelo, df)
    equidade_grupos(modelo, df)
    sumario(shap_values)

    print("\nFiguras salvas em:", FIGURAS_DIR)


if __name__ == "__main__":
    main()
