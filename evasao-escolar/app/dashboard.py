"""
Painel de priorização de escolas — Fase 8 (Cenário A).

Ferramenta de apoio ao gestor da Secretaria Estadual de Educação para
*priorizar* escolas estaduais de Ensino Médio de Pernambuco por risco de
abandono em t+1 e *entender o porquê* de cada predição. Não recomenda ações
prescritivas: o modelo é correlacional e a leitura SHAP é diagnóstica, não
causal.

Execução (a partir da raiz do projeto, com o venv ativo):
    streamlit run app/dashboard.py

Toda a regra de negócio vive em `src.recommend.service`; aqui só há
apresentação.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Garante que a raiz do projeto está no path quando executado via Streamlit.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.recommend.service import ServicoPriorizacao  # noqa: E402

st.set_page_config(
    page_title="Priorização de Risco de Evasão — PE",
    page_icon="🎓",
    layout="wide",
)

COR_ALTO = "#c0392b"
COR_BAIXO = "#2980b9"


@st.cache_resource(show_spinner="Carregando modelo e indicadores…")
def carregar_servico() -> ServicoPriorizacao:
    """Carrega o serviço uma única vez por sessão do servidor."""
    return ServicoPriorizacao.criar()


def formatar_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """Seleciona e renomeia colunas do ranking para exibição."""
    cols = {
        "risco_rank": "Posição",
        "NO_ENTIDADE": "Escola",
        "NO_MUNICIPIO": "Município",
        "mesorregiao": "Mesorregião",
        "localizacao": "Localização",
        "risco_previsto": "Risco previsto (%)",
        "diagnostico": "Diagnóstico",
        "prioritaria": "Prioritária",
    }
    return df[list(cols)].rename(columns=cols)


# ===========================================================================
# CARGA
# ===========================================================================
try:
    servico = carregar_servico()
except FileNotFoundError as e:
    st.error(
        "Não foi possível carregar o modelo ou o dataset de features.\n\n"
        f"Detalhe: {e}\n\n"
        "Gere os artefatos antes de abrir o painel:\n"
        "`python -m src.features.build_features` e o notebook de tuning "
        "(`notebooks/08_tuning_xgboost.py`)."
    )
    st.stop()

st.title("🎓 Priorização de Risco de Evasão Escolar")
st.caption(
    "Escolas estaduais de Ensino Médio de Pernambuco · ranking por risco de "
    "abandono previsto para o ano seguinte (t+1), com explicação por escola."
)

# ===========================================================================
# FILTROS (barra lateral)
# ===========================================================================
with st.sidebar:
    st.header("Filtros")
    anos = servico.anos_disponiveis()
    ano = st.selectbox(
        "Ano dos indicadores (t)",
        anos,
        index=len(anos) - 1,
        help="O risco previsto refere-se ao abandono no ano seguinte (t+1).",
    )

    meso_opcoes = ["Todas"] + servico.mesorregioes()
    meso = st.selectbox("Mesorregião", meso_opcoes)
    meso_filtro = None if meso == "Todas" else meso

    mun_opcoes = ["Todos"] + servico.municipios(meso_filtro)
    municipio = st.selectbox("Município", mun_opcoes)
    mun_filtro = None if municipio == "Todos" else municipio

    busca = st.text_input("Buscar escola pelo nome", "").strip() or None

    top_k = st.slider(
        "Marcar como prioritárias as N de maior risco do ano",
        min_value=10, max_value=200, value=50, step=10,
    )

ranking = servico.ranking(
    ano=ano,
    mesorregiao=meso_filtro,
    municipio=mun_filtro,
    busca=busca,
    top_k=top_k,
)

# ===========================================================================
# ABAS
# ===========================================================================
aba_ranking, aba_detalhe, aba_panorama = st.tabs(
    ["🎯 Ranking de risco", "🔍 Detalhe da escola", "📊 Panorama"]
)

# --------------------------------------------------------------------------
# ABA 1 — RANKING
# --------------------------------------------------------------------------
with aba_ranking:
    c1, c2, c3 = st.columns(3)
    c1.metric("Escolas no recorte", len(ranking))
    c2.metric("Prioritárias (top-N do ano)", int(ranking["prioritaria"].sum()))
    c3.metric(
        "Risco médio do recorte",
        f"{ranking['risco_previsto'].mean():.1f}%" if len(ranking) else "—",
    )

    if ranking.empty:
        st.info("Nenhuma escola atende aos filtros selecionados.")
    else:
        topo = ranking.head(20).iloc[::-1]
        fig = px.bar(
            topo,
            x="risco_previsto",
            y="NO_ENTIDADE",
            orientation="h",
            color="prioritaria",
            color_discrete_map={True: COR_ALTO, False: COR_BAIXO},
            labels={
                "risco_previsto": "Risco previsto (% de abandono em t+1)",
                "NO_ENTIDADE": "",
                "prioritaria": "Prioritária",
            },
            title="20 escolas de maior risco no recorte",
        )
        fig.update_layout(height=600, yaxis={"automargin": True})
        st.plotly_chart(fig, use_container_width=True)

        tabela = formatar_ranking(ranking)
        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Risco previsto (%)": st.column_config.NumberColumn(format="%.1f"),
            },
        )
        st.download_button(
            "⬇️ Baixar ranking (CSV)",
            data=tabela.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"ranking_risco_evasao_{ano}.csv",
            mime="text/csv",
        )

# --------------------------------------------------------------------------
# ABA 2 — DETALHE DA ESCOLA
# --------------------------------------------------------------------------
with aba_detalhe:
    if ranking.empty:
        st.info("Ajuste os filtros para selecionar uma escola.")
    else:
        rotulos = {
            f"{r.NO_ENTIDADE} — {r.NO_MUNICIPIO}": int(r.CO_ENTIDADE)
            for r in ranking.itertuples()
        }
        escolhido = st.selectbox("Escola", list(rotulos))
        co = rotulos[escolhido]

        info, contribs = servico.explicar_escola(co, ano)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Risco previsto (t+1)", f"{info['risco_previsto']:.1f}%")
        m2.metric("Posição no ano", f"{int(info['risco_rank'])}º")
        m3.metric("Percentil de risco", f"{info['risco_percentil']:.0f}")
        m4.metric("Abandono observado (t)", f"{info['abandono_real']:.1f}%")

        diag = info["diagnostico"]
        if diag.startswith("Alerta"):
            st.warning(f"**Diagnóstico:** {diag} "
                       f"(resíduo z = {info['residuo_z']:+.1f})")
        elif diag.startswith("Resiliente"):
            st.success(f"**Diagnóstico:** {diag} "
                       f"(resíduo z = {info['residuo_z']:+.1f})")
        else:
            st.info(f"**Diagnóstico:** {diag} "
                    f"(resíduo z = {info['residuo_z']:+.1f})")

        st.subheader("Por que esta escola foi pontuada assim")
        st.caption(
            "Contribuição de cada indicador para afastar a predição da média. "
            "Vermelho aumenta o risco; azul reduz. (Importância relativa — "
            "valores em escala interna do modelo.)"
        )
        df_c = pd.DataFrame(
            [{"Indicador": c.rotulo, "Contribuição": c.shap,
              "Valor observado": c.valor, "Direção": c.direcao}
             for c in contribs]
        ).iloc[::-1]

        fig = px.bar(
            df_c,
            x="Contribuição",
            y="Indicador",
            orientation="h",
            color="Contribuição",
            color_continuous_scale=[COR_BAIXO, "#ecf0f1", COR_ALTO],
            color_continuous_midpoint=0,
        )
        fig.update_layout(height=420, yaxis={"automargin": True},
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df_c[["Indicador", "Valor observado", "Direção"]].iloc[::-1],
            use_container_width=True,
            hide_index=True,
        )

# --------------------------------------------------------------------------
# ABA 3 — PANORAMA
# --------------------------------------------------------------------------
with aba_panorama:
    st.subheader(f"Distribuição do risco previsto — {ano}")
    todo_ano = servico.ranking(ano=ano)
    fig = px.histogram(
        todo_ano, x="risco_previsto", nbins=40,
        labels={"risco_previsto": "Risco previsto (% de abandono em t+1)"},
    )
    fig.update_layout(height=320, yaxis_title="Nº de escolas")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Risco médio por localização (equidade)")
    resumo = servico.resumo_por_grupo(ano)
    cg1, cg2 = st.columns([3, 2])
    with cg1:
        fig = px.bar(
            resumo, x="localizacao", y="risco_medio",
            labels={"localizacao": "", "risco_medio": "Risco médio (%)"},
            color="localizacao",
        )
        fig.update_layout(height=320, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cg2:
        st.dataframe(
            resumo.rename(columns={
                "localizacao": "Localização", "escolas": "Escolas",
                "risco_medio": "Risco médio (%)", "alertas": "Alertas",
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "Risco médio (%)": st.column_config.NumberColumn(format="%.1f"),
            },
        )

    st.caption(
        "Modelo: XGBoost (target √-transformado), validado por GroupKFold por "
        "município e validação temporal 2022→2023 / 2023→2024. As predições "
        "são in-sample neste painel demonstrativo; a estimativa honesta de "
        "desempenho prospectivo consta da validação temporal (Capítulo 6). "
        "Use o ranking como apoio à priorização, não como decisão automática."
    )
