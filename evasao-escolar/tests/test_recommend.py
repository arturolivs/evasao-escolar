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
  7. Predição de escola indígena/quilombola exibida sem a ressalva de viés —
     o grupo em que o modelo superestima o risco em ~6 p.p.

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
from src.recommend.service import (
    LOC_DIFERENCIADA,
    VIES_DIFERENCIADA,
    ServicoPriorizacao,
    num_pt,
    ressalva_equidade,
    ressalva_equidade_curta,
)


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
# Ressalva de equidade
#
# Risco: o gestor vê o rótulo do grupo e a posição no ranking sem saber que a
# predição para escolas indígenas/quilombolas é inflada em ~6 p.p. — o viés
# está medido em reports/residuos_grupo_temporal.csv.
# ---------------------------------------------------------------------------

def test_ressalva_equidade_para_localizacao_diferenciada():
    texto = ressalva_equidade(LOC_DIFERENCIADA)
    assert texto is not None
    assert "superestima" in texto


@pytest.mark.parametrize("grupo", ["Urbana", "Rural", None, "", "Outra coisa"])
def test_ressalva_equidade_ausente_nos_demais_grupos(grupo):
    """Só o grupo com viés medido recebe ressalva — nada de aviso genérico."""
    assert ressalva_equidade(grupo) is None


def test_ressalva_cita_os_numeros_do_diagnostico():
    """Os valores do texto vêm da constante, não digitados à mão na UI."""
    texto = ressalva_equidade(LOC_DIFERENCIADA)
    assert f"{num_pt(VIES_DIFERENCIADA['observado'])}%" in texto
    assert f"{num_pt(VIES_DIFERENCIADA['previsto'])}%" in texto
    assert VIES_DIFERENCIADA["residuo_pp"] < 0, "o viés é de superestimação"


@pytest.mark.parametrize("valor,casas,sinal,esperado", [
    (4.96, 1, False, "5,0"),
    (11.08, 1, False, "11,1"),
    (-6.12, 2, True, "-6,12"),
    (0.38, 2, True, "+0,38"),
])
def test_num_pt_usa_virgula_decimal(valor, casas, sinal, esperado):
    """Painel é PT-BR: número de gestor não sai com ponto decimal."""
    assert num_pt(valor, casas=casas, sinal=sinal) == esperado


def test_ressalva_curta_cabe_em_celula_de_planilha():
    """O CSV circula fora do painel: a ressalva tem de viajar junto e ser curta."""
    curta = ressalva_equidade_curta(LOC_DIFERENCIADA)
    assert curta is not None
    assert len(curta) < 160, "não cabe em coluna de planilha"
    assert "superestimado" in curta
    assert "\n" not in curta, "quebra de linha corrompe o CSV"


@pytest.mark.parametrize("grupo", ["Urbana", "Rural", None, "Outra coisa"])
def test_ressalva_curta_ausente_nos_grupos_calibrados(grupo):
    assert ressalva_equidade_curta(grupo) is None


def test_ressalva_curta_e_longa_concordam_no_grupo():
    """As duas versões têm de acender exatamente para o mesmo grupo."""
    for g in (LOC_DIFERENCIADA, "Urbana", "Rural", None):
        assert (ressalva_equidade(g) is None) == (ressalva_equidade_curta(g) is None)


def test_escolas_diferenciadas_do_resumo_tem_ressalva(servico):
    """Se o grupo aparece no panorama, a ressalva se aplica a ele."""
    resumo = servico.resumo_por_grupo(2023)
    grupos = set(resumo["localizacao"])
    assert LOC_DIFERENCIADA in grupos, "fixture deve conter escolas diferenciadas"
    com_ressalva = {g for g in grupos if ressalva_equidade(g)}
    assert com_ressalva == {LOC_DIFERENCIADA}


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
