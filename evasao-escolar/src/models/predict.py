"""
Modo predição — usa o modelo já treinado para estimar o risco de abandono de
um ano ainda não observado.

O modelo aprende uma função geral (características da escola no ano t → taxa de
abandono em t+1); ela vale para qualquer ano. Este módulo monta as
características de um ano-feature via `construir_dataset_predicao` e aplica o
modelo serializado, devolvendo o ranking de risco das escolas para t+1.

Uso:
    python -m src.models.predict 2024      # prevê o abandono de 2025
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.data import config
from src.features.build_features import (
    construir_dataset_predicao,
    salvar_predicao_features,
)
from src.models.train import carregar_modelo, colunas_features

logger = logging.getLogger(__name__)

COLS_SAIDA = ["CO_ENTIDADE", "NO_ENTIDADE", "NO_MUNICIPIO"]


def prever_ano(
    ano_feature: int,
    modelo_nome: str = "xgboost_v1",
    salvar_features: bool = False,
) -> pd.DataFrame:
    """
    Prevê o abandono de `ano_feature + 1` para todas as escolas.

    Retorna um DataFrame ordenado por risco decrescente, com a posição no
    ranking. As predições são de fora da amostra: o modelo nunca viu o ano-alvo.
    """
    df = construir_dataset_predicao(ano_feature)
    if salvar_features:
        salvar_predicao_features(df, ano_feature)

    modelo = carregar_modelo(modelo_nome)
    X = df[colunas_features(df)]
    risco = modelo.predict(X)

    res = df[COLS_SAIDA].copy()
    res["ano_referencia"] = ano_feature
    res["ano_previsto"] = ano_feature + 1
    res["risco_abandono_previsto"] = risco.clip(min=0)
    res = res.sort_values("risco_abandono_previsto", ascending=False).reset_index(
        drop=True
    )
    res.insert(0, "posicao", res.index + 1)
    logger.info(
        "Previsão de %d gerada para %d escolas (modelo %s).",
        ano_feature + 1, len(res), modelo_nome,
    )
    return res


def salvar_predicao(res: pd.DataFrame, ano_previsto: int) -> Path:
    out = config.PROCESSED_DIR / f"predicao_abandono_{ano_previsto}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out, index=False)
    logger.info("Previsão salva em: %s", out)
    return out


def _main() -> None:
    import sys

    logging.basicConfig(
        format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT, level=logging.INFO
    )
    ano_feature = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    res = prever_ano(ano_feature, salvar_features=True)
    salvar_predicao(res, ano_feature + 1)

    print(f"\n=== Risco de abandono previsto para {ano_feature + 1} "
          f"(a partir das características de {ano_feature}) ===")
    print(f"Escolas: {len(res)}  |  risco médio previsto: "
          f"{res['risco_abandono_previsto'].mean():.2f}%")
    print("\nTop 10 escolas de maior risco:")
    for _, r in res.head(10).iterrows():
        print(f"  {r['posicao']:>3}. {r['risco_abandono_previsto']:>5.1f}%  "
              f"{r['NO_ENTIDADE'][:48]:<50} ({r['NO_MUNICIPIO']})")


if __name__ == "__main__":
    _main()
