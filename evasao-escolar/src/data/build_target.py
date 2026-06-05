"""
Construção do target longitudinal: taxa_abandono_t1.

Lógica central do projeto:
  Para cada escola no ano t, o target é a taxa de abandono observada no ano t+1.
  Isso transforma o problema em: "dado o perfil institucional da escola no ano t,
  quão alta será sua taxa de abandono no próximo ano letivo?"

Pares de treino gerados:
  (features ano 2022) → (abandono EM 2023)
  (features ano 2023) → (abandono EM 2024)

ATENÇÃO: Não incluir o abandono do próprio ano t como feature — data leakage.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.data import config
from src.data.build_taxas_rendimento import construir_painel_taxas, COL_TARGET

logger = logging.getLogger(__name__)


def construir_target_abandono_t1(
    painel: pd.DataFrame,
    anos_target: Optional[list[int]] = None,
) -> pd.DataFrame:
    """
    Constrói a coluna target `taxa_abandono_t1` para cada linha do painel.

    Para cada escola no ano t, busca a taxa de abandono do ano t+1.
    Escolas sem correspondência no ano t+1 recebem NaN e são descartadas.

    Args:
        painel: DataFrame do painel longitudinal escola × ano (Censo).
        anos_target: anos de ABANDONO (t+1). Default = [2023, 2024].

    Returns:
        DataFrame com colunas originais + `taxa_abandono_t1`.
    """
    if anos_target is None:
        anos_target = [2023, 2024]

    anos_features = [a - 1 for a in anos_target]

    # Carrega painel de taxas (todos os anos disponíveis)
    taxas = construir_painel_taxas(anos=anos_target)

    # Mantém apenas o target total do EM (sem ruído de colunas por série)
    taxas_target = (
        taxas[["NU_ANO_CENSO", "CO_ENTIDADE", COL_TARGET]]
        .rename(columns={COL_TARGET: "taxa_abandono_t1", "NU_ANO_CENSO": "ano_rendimento"})
        .copy()
    )

    # Chave de join: painel está no ano t → target está no ano t+1
    taxas_target["NU_ANO_CENSO"] = taxas_target["ano_rendimento"] - 1

    painel_filtrado = painel[painel["NU_ANO_CENSO"].isin(anos_features)]

    painel_com_target = painel_filtrado.merge(
        taxas_target[["CO_ENTIDADE", "NU_ANO_CENSO", "taxa_abandono_t1"]],
        on=["CO_ENTIDADE", "NU_ANO_CENSO"],
        how="inner",
    )

    n_original = len(painel_filtrado)
    n_final = len(painel_com_target)
    logger.info(
        "Target construído: %d observações (perdidas %d por ausência de match).",
        n_final,
        n_original - n_final,
    )

    return painel_com_target


def salvar_dataset_com_target(
    df: pd.DataFrame,
    caminho: Optional[str] = None,
) -> str:
    """Salva o dataset com target em data/interim/."""
    if caminho is None:
        config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
        caminho_final = config.INTERIM_DIR / "painel_com_target.parquet"
    else:
        caminho_final = Path(caminho)

    df.to_parquet(caminho_final, index=False)
    logger.info("Dataset com target salvo em %s", caminho_final)
    return str(caminho_final)
