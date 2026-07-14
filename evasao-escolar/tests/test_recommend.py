"""
Testes da camada de serviço do dashboard (Fase 8 — priorização).

Riscos centrais:
  1. Ranking fora de ordem → gestor prioriza a escola errada.
  2. `risco_rank` incoerente com o risco previsto.
  3. `top_k` marcando quantidade errada de prioritárias.
  4. Filtros (mesorregião/município/busca) que não restringem.
  5. Explicação local vazando as dummies da mesorregião em vez de
     agregá-las num único fator, ou sinal de direção trocado.
  6. Diagnóstico (alerta/resiliente) com o sinal do resíduo invertido.

Os testes constroem o serviço sobre um XGBoost ajustado a um dataset
sintético — sem depender do modelo serializado nem do features.parquet.

Rodar com:
    pytest tests/test_recommend.py -v
"""

import numpy as np
import pandas as pd
import pytest

from src.models.train import aplicar_transformacao_target, criar_xgboost, preparar_xy
from src.recommend.labels import rotular_feature, rotular_mesorregiao
from src.recommend.service import ServicoPriorizacao


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def df_modelagem():
    """Dataset sintético no formato do features.parquet (50 escolas × 2 anos).
    abnd_t tem relação forte e crescente com o target → risco previsto sobe
    com ele, dando ordenação previsível para os testes de ranking."""
    rng = np.random.RandomState(11)
    linhas = []
    for ano in (2022, 2023):
        for i in range(50):
            abnd = rng.uniform(0, 12)
            linhas.append({
                "CO_ENTIDADE": 1000 + i,
                "NU_ANO_CENSO": ano,
                "NO_ENTIDADE": f"ESCOLA {i:02d}",
                "CO_MUNICIPIO": 2600000 + (i % 8),
                "NO_MUNICIPIO": f"MUN {i % 8}",
                "CO_MESORREGIAO": 2601 + (i % 5),
                "is_rural": int(i % 3 == 0),
                "is_loc_diferenciada": int(i % 10 == 0),
                "abnd_t": abnd,
                "inse_media": rng.normal(),
                "taxa_abandono_t1": max(0.0, 1.5 * abnd + rng.normal(0, 0.5)),
            })
    return pd.DataFrame(linhas)


@pytest.fixture
def servico(df_modelagem):
    X, y, _ = preparar_xy(df_modelagem)
    modelo = aplicar_transformacao_target(criar_xgboost(X), "sqrt")
    modelo.fit(X, y)
    return ServicoPriorizacao(modelo, df_modelagem)


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def test_ranking_ordenado_por_risco_desc(servico):
    r = servico.ranking(ano=2023)
    riscos = r["risco_previsto"].to_numpy()
    assert np.all(np.diff(riscos) <= 1e-9), "ranking não está decrescente"


def test_risco_rank_coerente_com_risco(servico):
    r = servico.ranking(ano=2023)
    # rank 1 deve ser a de maior risco previsto
    assert r.iloc[0]["risco_rank"] == 1
    assert r["risco_rank"].min() == 1
    assert r["risco_rank"].is_monotonic_increasing


def test_top_k_marca_quantidade_certa(servico):
    r = servico.ranking(ano=2023, top_k=15)
    assert int(r["prioritaria"].sum()) == 15
    # as prioritárias são exatamente as de menor rank (maior risco)
    assert set(r[r["prioritaria"]]["risco_rank"]) == set(range(1, 16))


def test_ano_mais_recente(servico):
    assert servico.ano_mais_recente() == 2023
    assert servico.anos_disponiveis() == [2022, 2023]


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------

def test_filtro_municipio_restringe(servico):
    todos = servico.ranking(ano=2023)
    um = servico.ranking(ano=2023, municipio="MUN 1")
    assert len(um) < len(todos)
    assert set(um["NO_MUNICIPIO"]) == {"MUN 1"}


def test_filtro_busca_por_nome(servico):
    r = servico.ranking(ano=2023, busca="ESCOLA 01")
    assert len(r) == 1
    assert r.iloc[0]["NO_ENTIDADE"] == "ESCOLA 01"


def test_prioridade_independe_do_filtro(servico):
    """top_k marca as N de maior risco do ANO inteiro, mesmo filtrando depois."""
    geral = servico.ranking(ano=2023, top_k=10)
    prioritarias_ano = set(geral[geral["prioritaria"]]["CO_ENTIDADE"])
    filtrado = servico.ranking(ano=2023, municipio="MUN 0", top_k=10)
    for row in filtrado.itertuples():
        esperado = row.CO_ENTIDADE in prioritarias_ano
        assert row.prioritaria == esperado


# ---------------------------------------------------------------------------
# Explicação local (SHAP)
# ---------------------------------------------------------------------------

def test_explicar_escola_agrega_mesorregiao(servico):
    co = servico.ranking(ano=2023).iloc[0]["CO_ENTIDADE"]
    _, contribs = servico.explicar_escola(int(co), 2023, top_n=50)
    features = [c.feature for c in contribs]
    # As dummies CO_MESORREGIAO_* não devem vazar...
    assert not any(f.startswith("CO_MESORREGIAO_") for f in features)
    # ...e a mesorregião aparece, se aparecer, como fator único.
    assert features.count("CO_MESORREGIAO") <= 1


def test_explicar_escola_ordenado_por_impacto(servico):
    co = servico.ranking(ano=2023).iloc[0]["CO_ENTIDADE"]
    _, contribs = servico.explicar_escola(int(co), 2023)
    impactos = [abs(c.shap) for c in contribs]
    assert impactos == sorted(impactos, reverse=True)


def test_explicar_escola_direcao_segue_sinal(servico):
    co = servico.ranking(ano=2023).iloc[0]["CO_ENTIDADE"]
    _, contribs = servico.explicar_escola(int(co), 2023)
    for c in contribs:
        if c.shap > 0:
            assert c.direcao == "↑ aumenta risco"
        else:
            assert c.direcao == "↓ reduz risco"


def test_explicar_escola_inexistente_levanta(servico):
    with pytest.raises(KeyError):
        servico.explicar_escola(999999, 2023)


# ---------------------------------------------------------------------------
# Diagnóstico de resíduo
# ---------------------------------------------------------------------------

def test_diagnostico_segue_sinal_do_residuo(servico):
    r = servico.ranking(ano=2023)
    for row in r.itertuples():
        if row.residuo_z >= 1.0:
            assert row.diagnostico.startswith("Alerta")
        elif row.residuo_z <= -1.0:
            assert row.diagnostico.startswith("Resiliente")
        else:
            assert row.diagnostico.startswith("Dentro")


def test_resumo_por_grupo_cobre_todas_escolas(servico):
    resumo = servico.resumo_por_grupo(2023)
    total = servico.ranking(ano=2023)
    assert resumo["escolas"].sum() == len(total)
    assert {"localizacao", "risco_medio", "alertas"}.issubset(resumo.columns)


# ---------------------------------------------------------------------------
# Rótulos
# ---------------------------------------------------------------------------

def test_rotular_feature_mesorregiao_dummy():
    assert rotular_feature("CO_MESORREGIAO_2605") == "Mesorregião: Metropolitana de Recife"


def test_rotular_feature_conhecida():
    assert rotular_feature("abnd_t") == "Abandono no ano anterior (Ensino Médio)"


def test_rotular_feature_desconhecida_cai_no_nome():
    assert rotular_feature("xpto_inexistente") == "xpto_inexistente"


def test_rotular_mesorregiao():
    assert rotular_mesorregiao(2601) == "Sertão Pernambucano"
