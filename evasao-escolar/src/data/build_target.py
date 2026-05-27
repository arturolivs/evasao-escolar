"""
Construção do target longitudinal: taxa_abandono_t1.

Lógica central do projeto:
  Para cada escola no ano t, o target é a taxa de abandono observada no ano t+1.
  Isso transforma o problema em: "dado o perfil institucional da escola no ano t,
  quão alta será sua taxa de abandono no próximo ano letivo?"

Fonte dos dados de abandono:
  Taxas de Rendimento Escolar — publicadas pelo INEP.
  Arquivo esperado: data/raw/taxas_rendimento/TX_REND_<ano>.xlsx (ou .csv)
  Download: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/
             indicadores-educacionais/taxas-de-rendimento-escolar

Pares de treino que este módulo constrói:
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

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES
# =============================================================================

# Coluna de código de escola nas Taxas de Rendimento (confirmar com o arquivo)
COL_ESCOLA_RENDIMENTO = "Código da Escola"

# Nome da coluna de taxa de abandono do EM nas Taxas de Rendimento
# O nome varia com o ano do arquivo — ajustar conforme o arquivo real
COL_ABANDONO_EM = "Taxa de Abandono no Ensino Médio"

# Caminho esperado dos arquivos de taxas de rendimento
RENDIMENTO_DIR = config.RAW_DIR / "taxas_rendimento"


# =============================================================================
# CARGA DAS TAXAS DE RENDIMENTO
# =============================================================================

def carregar_taxas_rendimento(ano: int) -> pd.DataFrame:
    """
    Carrega as Taxas de Rendimento Escolar do INEP para um dado ano.

    O INEP publica esses dados em Excel (formato .xlsx), separados por
    dependência administrativa e etapa. O arquivo contém várias abas;
    buscamos a aba correspondente ao Ensino Médio.

    Args:
        ano: ano de referência das taxas (ex: 2023 → abandono ocorrido em 2023).

    Returns:
        DataFrame com pelo menos (CO_ENTIDADE, taxa_abandono_em).

    Raises:
        FileNotFoundError: se o arquivo não existir.
    """
    RENDIMENTO_DIR.mkdir(parents=True, exist_ok=True)

    # Busca por arquivos com padrões comuns do INEP
    candidatos = list(RENDIMENTO_DIR.glob(f"*{ano}*.xlsx")) + \
                 list(RENDIMENTO_DIR.glob(f"*{ano}*.csv")) + \
                 list(RENDIMENTO_DIR.glob(f"*{ano}*.xls"))

    if not candidatos:
        raise FileNotFoundError(
            f"Arquivo de taxas de rendimento para {ano} não encontrado em {RENDIMENTO_DIR}.\n"
            f"Baixe o arquivo em:\n"
            f"  https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/"
            f"indicadores-educacionais/taxas-de-rendimento-escolar\n"
            f"E coloque em: {RENDIMENTO_DIR}"
        )

    caminho = candidatos[0]
    logger.info("Carregando taxas de rendimento %d de: %s", ano, caminho)

    if caminho.suffix in (".xlsx", ".xls"):
        # O INEP geralmente publica com múltiplas abas; tenta a aba de EM
        xl = pd.ExcelFile(caminho)
        aba_em = _detectar_aba_em(xl.sheet_names)
        df = pd.read_excel(caminho, sheet_name=aba_em, header=None)
        df = _normalizar_taxas_rendimento(df, ano)
    else:
        df = pd.read_csv(caminho, sep=";", encoding="latin-1")
        df = _normalizar_taxas_rendimento(df, ano)

    logger.info("Taxas de rendimento %d: %d escolas carregadas.", ano, len(df))
    return df


def _detectar_aba_em(nomes_abas: list[str]) -> str | int:
    """Detecta qual aba contém os dados de Ensino Médio."""
    termos_em = ["médio", "medio", "EM", "MÉDIO"]
    for aba in nomes_abas:
        if any(t.lower() in aba.lower() for t in termos_em):
            return aba
    logger.warning(
        "Nenhuma aba com 'médio' encontrada. Abas disponíveis: %s. Usando a primeira.",
        nomes_abas,
    )
    return 0


def _normalizar_taxas_rendimento(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    """
    Normaliza o DataFrame das taxas de rendimento para o formato padrão do projeto.

    O INEP costuma publicar com cabeçalhos em múltiplas linhas e nomes de colunas
    inconsistentes entre anos. Esta função padroniza para:
        CO_ENTIDADE (int64) | taxa_abandono_em (float) | ano_rendimento (int)

    ATENÇÃO: esta função precisará de ajuste manual na primeira carga real,
    pois o layout do arquivo do INEP varia com o ano.
    """
    # --- Tentativa heurística de encontrar a coluna de código de escola ---
    col_escola = None
    for c in df.columns:
        if any(k in str(c).lower() for k in ["código", "codigo", "co_entidade", "entidade"]):
            col_escola = c
            break

    if col_escola is None:
        raise ValueError(
            f"Coluna de código de escola não encontrada no arquivo de rendimento {ano}. "
            f"Colunas disponíveis: {list(df.columns[:20])}. "
            f"Ajuste _normalizar_taxas_rendimento() manualmente."
        )

    # --- Tentativa heurística de encontrar a coluna de abandono de EM ---
    col_abandono = None
    for c in df.columns:
        c_str = str(c).lower()
        if "abandon" in c_str and ("médio" in c_str or "medio" in c_str or "em" in c_str):
            col_abandono = c
            break
    if col_abandono is None:
        for c in df.columns:
            if "abandon" in str(c).lower():
                col_abandono = c
                logger.warning(
                    "Coluna de abandono EM não encontrada com certeza; usando '%s'. "
                    "Verifique manualmente.", c
                )
                break

    if col_abandono is None:
        raise ValueError(
            f"Coluna de taxa de abandono de EM não encontrada no arquivo de rendimento {ano}. "
            f"Colunas disponíveis: {list(df.columns[:30])}. "
            f"Ajuste _normalizar_taxas_rendimento() manualmente."
        )

    out = pd.DataFrame()
    out["CO_ENTIDADE"] = pd.to_numeric(df[col_escola], errors="coerce").astype("Int64")
    out["taxa_abandono_em"] = pd.to_numeric(df[col_abandono], errors="coerce")
    out["ano_rendimento"] = ano

    # Remove linhas sem código de escola (linhas de cabeçalho duplicado, totais, etc.)
    out = out.dropna(subset=["CO_ENTIDADE"]).copy()

    return out


# =============================================================================
# CONSTRUÇÃO DO TARGET t+1
# =============================================================================

def construir_target_abandono_t1(
    painel: pd.DataFrame,
    anos_target: Optional[list[int]] = None,
) -> pd.DataFrame:
    """
    Constrói a coluna target `taxa_abandono_t1` para cada linha do painel.

    Lógica:
        Para cada escola no ano t, busca a taxa de abandono do ano t+1.
        Escolas sem correspondência no ano t+1 recebem NaN (serão removidas).

    Args:
        painel: DataFrame do painel longitudinal escola × ano.
        anos_target: anos para os quais buscar o abandono. Default = [2023, 2024].
            Esses são os anos de ABANDONO (t+1); os anos de features serão t-1.

    Returns:
        DataFrame com as colunas originais mais `taxa_abandono_t1`.
        Linhas sem target correspondente são descartadas.
    """
    if anos_target is None:
        anos_target = [2023, 2024]

    frames_target = []
    for ano in anos_target:
        try:
            df_rend = carregar_taxas_rendimento(ano)
        except FileNotFoundError as e:
            logger.error(
                "Target para %d não disponível: %s. "
                "Baixe o arquivo e tente novamente.", ano, e
            )
            continue

        # Filtra apenas PE + estadual (pode ter dados de todo o Brasil)
        if "CO_UF" in df_rend.columns:
            df_rend = df_rend[df_rend["CO_UF"] == config.UF_ALVO_CODIGO]
        if "TP_DEPENDENCIA" in df_rend.columns:
            df_rend = df_rend[df_rend["TP_DEPENDENCIA"] == config.DEPENDENCIA_ESTADUAL]

        frames_target.append(df_rend[["CO_ENTIDADE", "taxa_abandono_em", "ano_rendimento"]])

    if not frames_target:
        raise RuntimeError(
            "Nenhum arquivo de taxas de rendimento disponível. "
            "Baixe os arquivos e execute novamente."
        )

    targets = pd.concat(frames_target, ignore_index=True)
    targets = targets.rename(columns={"taxa_abandono_em": "taxa_abandono_t1"})

    # O painel está em ano t; o target está no ano t+1
    # → para cruzar: painel.NU_ANO_CENSO == targets.ano_rendimento - 1
    targets["NU_ANO_CENSO_FEATURES"] = targets["ano_rendimento"] - 1

    painel_com_target = painel.merge(
        targets[["CO_ENTIDADE", "NU_ANO_CENSO_FEATURES", "taxa_abandono_t1"]],
        left_on=["CO_ENTIDADE", "NU_ANO_CENSO"],
        right_on=["CO_ENTIDADE", "NU_ANO_CENSO_FEATURES"],
        how="inner",
    ).drop(columns=["NU_ANO_CENSO_FEATURES"])

    n_original = len(painel[painel["NU_ANO_CENSO"].isin(
        [a - 1 for a in anos_target]
    )])
    n_final = len(painel_com_target)
    n_perdido = n_original - n_final

    logger.info(
        "Target construído: %d observações (perdidas %d por ausência de match).",
        n_final, n_perdido,
    )

    return painel_com_target


def salvar_dataset_com_target(
    df: pd.DataFrame,
    caminho: Optional[str] = None,
) -> str:
    """Salva o dataset com target em data/interim/ (antes do feature engineering)."""
    if caminho is None:
        config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
        caminho_final = config.INTERIM_DIR / "painel_com_target.parquet"
    else:
        caminho_final = Path(caminho)

    df.to_parquet(caminho_final, index=False)
    logger.info("Dataset com target salvo em %s", caminho_final)
    return str(caminho_final)
