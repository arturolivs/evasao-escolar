"""
Construção do painel longitudinal escola × ano.

Saída: tabela onde cada linha é (CO_ENTIDADE, NU_ANO_CENSO) com as features
brutas da escola naquele ano. Pronto para ser enriquecido com indicadores
externos (INSE, IDEB, Taxa de Abandono, etc.) na próxima fase.

Esta é a "tabela mãe" do projeto. Tudo a partir daqui se ramifica.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

import pandas as pd

from src.data import config, filter_pe_estadual_em as flt, load

logger = logging.getLogger(__name__)


# Colunas que carregamos por padrão para o painel inicial.
# Pode (e deve) ser expandida conforme a engenharia de features amadurecer.
# Lista derivada do inventário curado de variáveis (relevância ALTA).
COLUNAS_PAINEL_INICIAL = list(set([
    # Identificação
    "NU_ANO_CENSO",
    "CO_ENTIDADE",
    "NO_ENTIDADE",

    # Geografia (filtros + features regionais)
    "SG_UF",
    "CO_UF",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "CO_MESORREGIAO",
    "CO_MICRORREGIAO",

    # Características da escola
    "TP_DEPENDENCIA",
    "TP_LOCALIZACAO",
    "TP_LOCALIZACAO_DIFERENCIADA",
    "TP_SITUACAO_FUNCIONAMENTO",

    # Infraestrutura — serviços básicos
    "IN_AGUA_POTAVEL",
    "IN_ENERGIA_REDE_PUBLICA",
    "IN_ESGOTO_REDE_PUBLICA",

    # Infraestrutura — dependências físicas
    "IN_BIBLIOTECA",
    "IN_LABORATORIO_INFORMATICA",
    "IN_LABORATORIO_CIENCIAS",
    "IN_QUADRA_ESPORTES",
    "IN_REFEITORIO",
    "IN_SALA_LEITURA",
    "IN_AUDITORIO",
    "QT_SALAS_UTILIZADAS",

    # Tecnologia
    "IN_INTERNET",
    "IN_INTERNET_ALUNOS",
    "IN_BANDA_LARGA",
    "QT_DESKTOP_ALUNO",
    "QT_COMPUTADOR_ALUNO",
    "QT_TABLET_ALUNO",

    # Quantitativos — matrículas EM (alvo do projeto)
    "QT_MAT_MED",
    "QT_MAT_MED_INT",  # tempo integral
    "QT_MAT_MED_NM",   # normal/magistério (cuidado: pode estar deprecado)

    # Quantitativos — turmas EM
    "QT_TUR_MED",

    # Quantitativos — docentes
    "QT_DOC_MED",

    # Programas pedagógicos
    "IN_EXAME_SELECAO_INGRESSO",
]))


def montar_painel(
    anos: Optional[Iterable[int]] = None,
    colunas: Optional[Iterable[str]] = None,
    incluir_filtro_em: bool = True,
    nrows_por_ano: Optional[int] = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Monta o painel longitudinal escola × ano para PE / rede estadual / EM.

    Args:
        anos: anos do Censo a incluir. Default = todos de config.ANOS_DISPONIVEIS.
        colunas: colunas a carregar. Default = COLUNAS_PAINEL_INICIAL.
        incluir_filtro_em: se True, mantém apenas escolas com QT_MAT_MED > 0.
        nrows_por_ano: limite de linhas por ano (debug).

    Returns:
        (df_painel, metadata)
        - df_painel: DataFrame longitudinal indexado por (CO_ENTIDADE, NU_ANO_CENSO).
        - metadata: dict com relatórios por ano e contagens finais.
    """
    anos = list(anos) if anos is not None else config.ANOS_DISPONIVEIS
    colunas = list(colunas) if colunas is not None else COLUNAS_PAINEL_INICIAL

    relatorios_por_ano: dict[int, flt.RelatorioRecorte] = {}
    dfs_filtrados = []

    for ano in anos:
        logger.info("=" * 70)
        logger.info("Processando ano %d", ano)
        logger.info("=" * 70)

        try:
            df_ano = load.carregar_escolas_ano(
                ano,
                colunas=colunas,
                nrows=nrows_por_ano,
            )
        except ValueError as e:
            # Coluna pode não existir em algum ano específico — relatamos e
            # tentamos novamente carregando só as colunas presentes
            logger.warning(
                "Falha ao carregar com colunas exatas no ano %d: %s. "
                "Tentando carregar apenas o que existir...",
                ano, e,
            )
            df_ano = _carregar_com_colunas_tolerantes(ano, colunas, nrows_por_ano)

        df_filtrado, rel = flt.aplicar_recorte_universo(
            df_ano, incluir_filtro_em=incluir_filtro_em
        )
        relatorios_por_ano[ano] = rel
        dfs_filtrados.append(df_filtrado)

    painel = pd.concat(dfs_filtrados, ignore_index=True)

    # Validações finais
    _validar_painel(painel)

    metadata = {
        "anos": anos,
        "n_linhas_total": len(painel),
        "n_escolas_unicas": painel["CO_ENTIDADE"].nunique(),
        "linhas_por_ano": painel.groupby("NU_ANO_CENSO").size().to_dict(),
        "relatorios_por_ano": relatorios_por_ano,
        "colunas_carregadas": list(painel.columns),
    }

    logger.info("\nPainel final: %d linhas, %d escolas únicas em %d anos.",
                metadata["n_linhas_total"], metadata["n_escolas_unicas"], len(anos))
    logger.info("Linhas por ano: %s", metadata["linhas_por_ano"])

    return painel, metadata


def _carregar_com_colunas_tolerantes(
    ano: int,
    colunas_desejadas: list[str],
    nrows: Optional[int],
) -> pd.DataFrame:
    """
    Carrega o CSV do ano com apenas as colunas que existirem.

    Útil para lidar com a realidade de que o INEP muda nomes de variáveis
    entre anos. As que não existirem geram aviso, mas não falham.
    """
    from src.data.load import _resolver_caminho_csv_escola

    caminho = _resolver_caminho_csv_escola(ano)
    cabecalho = pd.read_csv(
        caminho,
        sep=config.CSV_SEPARATOR,
        encoding=config.CSV_ENCODING,
        nrows=0,
    )
    cols_existentes = [c for c in colunas_desejadas if c in cabecalho.columns]
    cols_faltando = set(colunas_desejadas) - set(cols_existentes)

    if cols_faltando:
        logger.warning(
            "Ano %d — colunas pedidas que não existem (serão ignoradas): %s",
            ano, sorted(cols_faltando),
        )

    return load.carregar_escolas_ano(ano, colunas=cols_existentes, nrows=nrows)


def _validar_painel(painel: pd.DataFrame) -> None:
    """
    Sanity-checks no painel final. Falha alto se algo estiver muito errado.
    """
    # Checagem 1: chave primária (CO_ENTIDADE, NU_ANO_CENSO) é única
    duplicatas = painel.duplicated(subset=["CO_ENTIDADE", "NU_ANO_CENSO"], keep=False)
    if duplicatas.any():
        n_dup = duplicatas.sum()
        amostra = painel.loc[duplicatas, ["CO_ENTIDADE", "NU_ANO_CENSO"]].head(5)
        raise ValueError(
            f"Painel tem {n_dup} linhas duplicadas em (CO_ENTIDADE, NU_ANO_CENSO). "
            f"Amostra:\n{amostra}"
        )

    # Checagem 2: CO_ENTIDADE não pode ser nulo
    n_nulos = painel["CO_ENTIDADE"].isna().sum()
    if n_nulos > 0:
        raise ValueError(f"Painel tem {n_nulos} linhas com CO_ENTIDADE nulo.")

    # Checagem 3: NU_ANO_CENSO não pode ser nulo
    n_nulos_ano = painel["NU_ANO_CENSO"].isna().sum()
    if n_nulos_ano > 0:
        raise ValueError(f"Painel tem {n_nulos_ano} linhas com NU_ANO_CENSO nulo.")

    logger.info("Validações do painel: OK.")


def salvar_painel(painel: pd.DataFrame, caminho: Optional[str] = None) -> str:
    """Salva o painel em parquet (compacto e tipado)."""
    if caminho is None:
        config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
        caminho_final = config.INTERIM_DIR / "painel_escola_ano_pe_estadual_em.parquet"
    else:
        caminho_final = caminho

    painel.to_parquet(caminho_final, index=False)
    logger.info("Painel salvo em %s", caminho_final)
    return str(caminho_final)
