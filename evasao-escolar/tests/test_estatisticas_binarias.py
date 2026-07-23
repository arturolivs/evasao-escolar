"""
Testes para a descrição dos atributos de sim/não (notebooks/13_estatisticas_features.py).

O Quadro 6 da monografia cruza duas grandezas que se parecem e não são a mesma
coisa: a **repartição das escolas** entre quem tem e quem não tem o atributo
(que soma o total da rede) e a **média do abandono dentro de cada grupo** (duas
médias do mesmo indicador, que não somam nada). Confundi-las inverte a leitura
da tabela — foi o que a revisão da banca apontou.

Estes testes travam a invariante: as contagens repartem a rede, as médias não.

Rodar com:
    pytest tests/test_estatisticas_binarias.py -v
"""

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

_NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"


@pytest.fixture(scope="module")
def modulo():
    """Carrega o notebook-script, cujo nome começa com dígito (não importável)."""
    sys.path.insert(0, str(_NOTEBOOKS))
    spec = importlib.util.spec_from_file_location(
        "estatisticas_features", _NOTEBOOKS / "13_estatisticas_features.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def df_binario(modulo):
    """Seis escolas, dois atributos: um comum e um raro."""
    return pd.DataFrame({
        "tem_biblioteca": [1, 1, 1, 1, 0, 0],
        "is_rural":       [1, 0, 0, 0, 0, 0],
        modulo.TARGET_COL: [4.0, 0.0, 2.0, 0.0, 6.0, 8.0],
    })


def test_contagens_repartem_a_rede(modulo, df_binario):
    """n_tem + n_nao devolve o total — é a coluna que soma 100%."""
    resumo = modulo.descrever_binarias(df_binario, ["tem_biblioteca", "is_rural"])
    for _, linha in resumo.iterrows():
        assert linha["n_tem"] + linha["n_nao"] == len(df_binario)
        assert linha["prevalencia"] + linha["pct_nao"] == pytest.approx(100.0)


def test_medias_de_abandono_nao_somam_cem(modulo, df_binario):
    """
    As duas colunas de abandono são médias de grupo, não uma partição.
    Se alguém as reescrever como percentuais complementares, isto quebra.
    """
    resumo = modulo.descrever_binarias(df_binario, ["tem_biblioteca"])
    linha = resumo.iloc[0]
    # Escolas com biblioteca: 4, 0, 2, 0 → média 1,5 | sem: 6, 8 → média 7,0
    assert linha["abandono_com"] == pytest.approx(1.5)
    assert linha["abandono_sem"] == pytest.approx(7.0)
    assert linha["diferenca"] == pytest.approx(-5.5)


def test_contagens_batem_com_os_percentuais(modulo, df_binario):
    resumo = modulo.descrever_binarias(df_binario, ["is_rural"])
    linha = resumo.iloc[0]
    assert linha["n_tem"] == 1
    assert linha["n_nao"] == 5
    assert linha["prevalencia"] == pytest.approx(100 / 6)


def test_quadro6_publicado_mantem_a_invariante():
    """O CSV que alimenta o Quadro 6 precisa carregar as contagens corretas."""
    from src.data import config

    caminho = config.ROOT_DIR / "reports" / "estatisticas_features.csv"
    if not caminho.exists():
        pytest.skip("estatisticas_features.csv ausente — rode o notebook 13")

    dados = pd.read_csv(caminho)
    binarias = dados[dados["tipo"] == "binária"]
    if "n_tem" not in binarias.columns:
        pytest.skip("CSV gerado antes da inclusão das contagens")

    assert not binarias.empty
    total = binarias["n"].iloc[0]
    assert (binarias["n_tem"] + binarias["n_nao"] == total).all()
    assert (binarias["prevalencia"] + binarias["pct_nao"]).round(6).eq(100.0).all()
