"""
Testes do modo predição (src/features/build_features.py::construir_dataset_predicao
e src/models/predict.py::prever_ano).

O modo predição monta as características de um ano cujo abandono ainda não foi
observado, para que o modelo já treinado estime o ano seguinte. O que precisa
ser garantido:
  - o vetor de predição tem EXATAMENTE as mesmas features do treino (senão o
    modelo recebe colunas erradas e prevê lixo com cara de certo);
  - a imputação fecha em 0 missing também fora do treino;
  - o alvo não é exigido (é o que estava travando prever anos futuros);
  - o ranking sai ordenado, íntegro e sem risco negativo.

Rodar com:
    pytest tests/test_predicao.py -v
"""

import pandas as pd
import pytest

from src.data import config
from src.features.build_features import construir_dataset_predicao
from src.models.train import colunas_features

ANO_PRED = 2024  # características de 2024 → prevê 2025 (dados já carregados)


def _tem_dados() -> bool:
    return (config.INTERIM_DIR / "painel_escola_ano_pe_estadual_em.parquet").exists()


pytestmark = pytest.mark.skipif(
    not _tem_dados(), reason="parquets interim ausentes — rode os ETLs"
)


@pytest.fixture(scope="module")
def df_pred() -> pd.DataFrame:
    return construir_dataset_predicao(ANO_PRED)


def test_mesmas_features_do_treino(df_pred):
    """As colunas de feature têm de coincidir com as do features.parquet."""
    caminho = config.PROCESSED_DIR / "features.parquet"
    if not caminho.exists():
        pytest.skip("features.parquet ausente — rode src.features.build_features")
    treino = pd.read_parquet(caminho)
    assert colunas_features(df_pred) == colunas_features(treino)


def test_apenas_o_ano_solicitado(df_pred):
    assert set(df_pred["NU_ANO_CENSO"].unique()) == {ANO_PRED}


def test_sem_missing_nas_features(df_pred):
    """A imputação por mesorregião tem de fechar também fora do treino."""
    cols = colunas_features(df_pred)
    assert int(df_pred[cols].isna().sum().sum()) == 0


def test_alvo_ausente_nao_e_exigido(df_pred):
    """Prever não pode depender do alvo de t+1, que ainda não existe."""
    assert df_pred["taxa_abandono_t1"].isna().all()
    assert len(df_pred) > 0


def test_ano_sem_dados_falha_com_mensagem_clara():
    with pytest.raises(ValueError, match="Sem dados de Censo"):
        construir_dataset_predicao(2099)


def test_ranking_previsto_integro():
    """prever_ano devolve ranking ordenado, posições 1..N e risco não negativo."""
    if not (config.MODELS_DIR / "xgboost_v1.joblib").exists():
        pytest.skip("modelo xgboost_v1 ausente — rode notebooks/08")
    from src.models.predict import prever_ano

    res = prever_ano(ANO_PRED)
    assert len(res) == len(construir_dataset_predicao(ANO_PRED))
    assert res["ano_previsto"].eq(ANO_PRED + 1).all()
    assert (res["risco_abandono_previsto"] >= 0).all()
    # ordenado por risco decrescente e posição 1..N
    assert res["risco_abandono_previsto"].is_monotonic_decreasing
    assert list(res["posicao"]) == list(range(1, len(res) + 1))
