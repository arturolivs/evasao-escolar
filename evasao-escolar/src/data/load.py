"""
Carga dos microdados do Censo Escolar (INEP) — tabela ESCOLA.

Princípios:
- Não silenciar erros: se algo der errado, falha alto e claro.
- Permitir carga seletiva de colunas (microdados são gigantes; carregar tudo é caro).
- Tipagem explícita para colunas críticas (CO_ENTIDADE como int64, não float).
- Logging informativo para rastrear o que está sendo lido.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from src.data import config

logger = logging.getLogger(__name__)


def _resolver_caminho_csv_escola(ano: int) -> Path:
    """
    Resolve o caminho do CSV de escolas para um dado ano.

    Tenta primeiro o nome padrão do template do INEP. Se não encontrar,
    busca qualquer CSV na pasta cujo nome contenha 'escola' ou 'ed_basica'.

    Raises:
        FileNotFoundError: se a pasta do ano não existir ou nenhum CSV de
            escola for encontrado.
    """
    pasta = config.CENSO_DIRS[ano]
    if not pasta.exists():
        raise FileNotFoundError(
            f"Pasta do Censo {ano} não encontrada em {pasta}. "
            f"Confira config.CENSO_DIRS e a estrutura de data/raw/."
        )

    # Tentativa 1: nome padrão do template
    nome_padrao = config.CENSO_ESCOLA_FILENAME_TEMPLATE.format(ano=ano)
    caminho_padrao = pasta / nome_padrao
    if caminho_padrao.exists():
        return caminho_padrao

    # Tentativa 2: busca heurística por arquivos de escola
    # (em alguns anos o INEP usa "microdados_ed_basica_2023.csv", em outros
    # pode estar em pasta dados/ ou com sufixo diferente)
    candidatos = []
    for csv_path in pasta.rglob("*.csv"):
        nome_lower = csv_path.name.lower()
        if "ed_basica" in nome_lower or "escola" in nome_lower:
            candidatos.append(csv_path)

    if not candidatos:
        raise FileNotFoundError(
            f"Nenhum CSV de escola encontrado em {pasta}. "
            f"Esperado algo como '{nome_padrao}'. "
            f"Arquivos presentes: {[p.name for p in pasta.rglob('*.csv')]}"
        )

    if len(candidatos) > 1:
        logger.warning(
            "Múltiplos CSVs de escola encontrados em %s: %s. Usando o primeiro: %s",
            pasta, [c.name for c in candidatos], candidatos[0].name,
        )

    return candidatos[0]


def carregar_escolas_ano(
    ano: int,
    colunas: Optional[Iterable[str]] = None,
    nrows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Carrega o CSV de escolas do Censo de um ano específico.

    Args:
        ano: ano do Censo (2022, 2023 ou 2024).
        colunas: subconjunto de colunas a carregar. Se None, carrega tudo
            (caro; só para exploração). Recomenda-se passar uma lista.
        nrows: limite de linhas (para teste rápido). None = todas.

    Returns:
        DataFrame com as colunas pedidas. Coluna CO_ENTIDADE é convertida
        para int64 quando presente.

    Raises:
        FileNotFoundError: se o CSV não existir.
        ValueError: se alguma coluna pedida não existir no arquivo.
    """
    if ano not in config.ANOS_DISPONIVEIS:
        raise ValueError(
            f"Ano {ano} fora dos disponíveis ({config.ANOS_DISPONIVEIS}). "
            f"Atualize config.ANOS_DISPONIVEIS se necessário."
        )

    caminho = _resolver_caminho_csv_escola(ano)
    logger.info("Lendo CSV de escolas do ano %d: %s", ano, caminho)

    # Primeiro, lê só o cabeçalho para validar colunas pedidas
    if colunas is not None:
        colunas = list(colunas)
        cabecalho = pd.read_csv(
            caminho,
            sep=config.CSV_SEPARATOR,
            encoding=config.CSV_ENCODING,
            nrows=0,
        )
        cols_disponiveis = set(cabecalho.columns)
        cols_faltando = [c for c in colunas if c not in cols_disponiveis]
        if cols_faltando:
            raise ValueError(
                f"Colunas pedidas não existem no CSV do ano {ano}: {cols_faltando}. "
                f"Colunas disponíveis (amostra): {sorted(cols_disponiveis)[:30]}..."
            )

    df = pd.read_csv(
        caminho,
        sep=config.CSV_SEPARATOR,
        encoding=config.CSV_ENCODING,
        usecols=colunas,
        nrows=nrows,
        low_memory=False,
    )

    # Tipagem explícita para colunas críticas, quando presentes
    if "CO_ENTIDADE" in df.columns:
        df["CO_ENTIDADE"] = pd.to_numeric(df["CO_ENTIDADE"], errors="coerce").astype("Int64")
    if "CO_MUNICIPIO" in df.columns:
        df["CO_MUNICIPIO"] = pd.to_numeric(df["CO_MUNICIPIO"], errors="coerce").astype("Int64")
    if "CO_UF" in df.columns:
        df["CO_UF"] = pd.to_numeric(df["CO_UF"], errors="coerce").astype("Int64")
    if "NU_ANO_CENSO" in df.columns:
        df["NU_ANO_CENSO"] = pd.to_numeric(df["NU_ANO_CENSO"], errors="coerce").astype("Int64")

    logger.info(
        "Carregadas %d linhas e %d colunas do Censo %d.",
        len(df), df.shape[1], ano,
    )
    return df


def carregar_escolas_multiplos_anos(
    anos: Iterable[int],
    colunas: Optional[Iterable[str]] = None,
    nrows_por_ano: Optional[int] = None,
) -> pd.DataFrame:
    """
    Carrega e concatena vários anos do Censo em um único DataFrame.

    Args:
        anos: iterável com os anos a carregar.
        colunas: ver carregar_escolas_ano.
        nrows_por_ano: limite de linhas por ano (teste rápido).

    Returns:
        DataFrame concatenado, com coluna NU_ANO_CENSO identificando o ano.
    """
    dfs = []
    for ano in anos:
        df = carregar_escolas_ano(ano, colunas=colunas, nrows=nrows_por_ano)
        # Garante que NU_ANO_CENSO está presente — alguns CSVs antigos podem
        # ter omitido essa coluna; injeta manualmente se faltar
        if "NU_ANO_CENSO" not in df.columns:
            df["NU_ANO_CENSO"] = ano
            logger.warning("NU_ANO_CENSO ausente no CSV do ano %d; injetado manualmente.", ano)
        dfs.append(df)

    out = pd.concat(dfs, ignore_index=True)
    logger.info("Concatenados %d anos. Total: %d linhas.", len(dfs), len(out))
    return out
