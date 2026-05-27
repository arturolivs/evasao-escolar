"""
Filtragem do universo de escolas: Pernambuco, rede estadual, com Ensino Médio.

Princípio: cada filtro é uma função pura que recebe e retorna DataFrame.
A função orquestradora `aplicar_recorte_universo` aplica todos em ordem
e devolve um relatório de quantas linhas foram cortadas em cada etapa.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from src.data import config

logger = logging.getLogger(__name__)


@dataclass
class RelatorioRecorte:
    """Registra quantas linhas restaram após cada filtro aplicado."""
    inicial: int = 0
    etapas: list[tuple[str, int]] = field(default_factory=list)

    def registrar(self, nome_etapa: str, n_linhas: int) -> None:
        self.etapas.append((nome_etapa, n_linhas))

    def __str__(self) -> str:
        linhas = [f"Relatório de recorte do universo:"]
        linhas.append(f"  Inicial: {self.inicial:,} linhas")
        anterior = self.inicial
        for nome, n in self.etapas:
            delta = n - anterior
            sinal = "-" if delta < 0 else "+"
            linhas.append(f"  {nome:50s} {n:>10,} ({sinal}{abs(delta):,})")
            anterior = n
        return "\n".join(linhas)


def filtrar_uf_pe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mantém apenas escolas em Pernambuco.

    Aceita filtrar por SG_UF (texto) ou CO_UF (numérico), o que estiver
    disponível. Se nenhuma das duas colunas existir, levanta erro.
    """
    if "SG_UF" in df.columns:
        mask = df["SG_UF"].astype(str).str.upper().str.strip() == config.UF_ALVO_SIGLA
        return df.loc[mask].copy()
    if "CO_UF" in df.columns:
        mask = df["CO_UF"] == config.UF_ALVO_CODIGO
        return df.loc[mask].copy()
    raise ValueError(
        "Nenhuma das colunas SG_UF / CO_UF está disponível. "
        "Verifique a lista de colunas carregadas em load.py."
    )


def filtrar_rede_estadual(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém apenas escolas da rede estadual (TP_DEPENDENCIA == 2)."""
    if "TP_DEPENDENCIA" not in df.columns:
        raise ValueError(
            "Coluna TP_DEPENDENCIA ausente. Adicione em COLUNAS_CHAVE_ESCOLA."
        )
    mask = df["TP_DEPENDENCIA"] == config.DEPENDENCIA_ESTADUAL
    return df.loc[mask].copy()


def filtrar_em_atividade(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mantém apenas escolas em atividade no ano do Censo.

    Escolas paralisadas ou extintas têm dados pouco confiáveis e devem
    ser excluídas para evitar viés.
    """
    if "TP_SITUACAO_FUNCIONAMENTO" not in df.columns:
        logger.warning(
            "TP_SITUACAO_FUNCIONAMENTO ausente; assumindo que todas as escolas "
            "carregadas estão em atividade. Recomenda-se incluir essa coluna."
        )
        return df.copy()
    mask = df["TP_SITUACAO_FUNCIONAMENTO"] == config.SITUACAO_EM_ATIVIDADE
    return df.loc[mask].copy()


def filtrar_oferta_ensino_medio(
    df: pd.DataFrame,
    col_qtd_em: Optional[str] = None,
) -> pd.DataFrame:
    """
    Mantém apenas escolas que oferecem Ensino Médio (QT_MAT_MED > 0).

    Args:
        df: DataFrame de escolas.
        col_qtd_em: nome da coluna de quantidade de matrículas de EM.
            Se None, usa o default de config.COL_QTD_MATRICULA_EM.

    Raises:
        ValueError: se a coluna não estiver presente.
    """
    col = col_qtd_em or config.COL_QTD_MATRICULA_EM
    if col not in df.columns:
        raise ValueError(
            f"Coluna '{col}' ausente — necessária para identificar escolas com EM. "
            f"Inclua-a na lista de colunas em load.py."
        )
    # NaN é tratado como zero (escola não oferta EM)
    serie = pd.to_numeric(df[col], errors="coerce").fillna(0)
    mask = serie > 0
    return df.loc[mask].copy()


def aplicar_recorte_universo(
    df: pd.DataFrame,
    incluir_filtro_em: bool = True,
) -> tuple[pd.DataFrame, RelatorioRecorte]:
    """
    Aplica todos os filtros em sequência e devolve o DataFrame recortado
    junto com um relatório das contagens em cada etapa.

    Ordem dos filtros (importa para o relatório, não para o resultado):
    1. UF Pernambuco
    2. Rede estadual
    3. Em atividade
    4. Oferece Ensino Médio (opcional — algumas análises podem manter todas)

    Args:
        df: DataFrame bruto carregado de load.py.
        incluir_filtro_em: se True, filtra escolas com EM. Default True.

    Returns:
        (df_filtrado, relatorio)
    """
    rel = RelatorioRecorte(inicial=len(df))

    df = filtrar_uf_pe(df)
    rel.registrar("UF == PE", len(df))

    df = filtrar_rede_estadual(df)
    rel.registrar("TP_DEPENDENCIA == Estadual", len(df))

    df = filtrar_em_atividade(df)
    rel.registrar("TP_SITUACAO_FUNCIONAMENTO == Em atividade", len(df))

    if incluir_filtro_em:
        df = filtrar_oferta_ensino_medio(df)
        rel.registrar(f"{config.COL_QTD_MATRICULA_EM} > 0 (oferta EM)", len(df))

    logger.info("\n%s", rel)
    return df, rel
