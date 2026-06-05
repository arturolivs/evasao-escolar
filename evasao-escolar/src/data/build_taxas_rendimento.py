"""
ETL das Taxas de Rendimento Escolar (INEP) para escolas estaduais de EM em PE.

Fonte: INEP — Taxas de Rendimento Escolar por escola
Arquivo: data/raw/taxas_rendimento/tx_rend_escolas_<ano>.xlsx

Os arquivos XLSX do INEP têm 8 linhas de cabeçalho institucional antes
dos dados reais. Colunas com '--' indicam que a escola não oferta aquela
série/etapa (substituídas por NaN).

Saída: data/interim/taxas_rendimento_pe_estadual_em.parquet
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.data import config

logger = logging.getLogger(__name__)

# Linha 0-indexed que contém os nomes reais das colunas nos xlsx do INEP
_HEADER_ROW = 8

# Valor sentinela do INEP para "escola não oferta esta etapa/série"
_SENTINEL = "--"

# Mapeamento bruto → nome padronizado do projeto
# CAT 1 = Aprovação | CAT 2 = Reprovação | CAT 3 = Abandono
_RENAME: dict[str, str] = {
    "CO_ENTIDADE": "CO_ENTIDADE",
    "CO_MUNICIPIO": "CO_MUNICIPIO",
    "NO_MUNICIPIO": "NO_MUNICIPIO",
    "NO_ENTIDADE": "NO_ENTIDADE",
    "NO_CATEGORIA": "NO_CATEGORIA",
    # Aprovação — Ensino Médio
    "1_CAT_MED":    "TAXA_APROV_MED",
    "1_CAT_MED_01": "TAXA_APROV_MED_S1",
    "1_CAT_MED_02": "TAXA_APROV_MED_S2",
    "1_CAT_MED_03": "TAXA_APROV_MED_S3",
    "1_CAT_MED_04": "TAXA_APROV_MED_S4",
    "1_CAT_MED_NS": "TAXA_APROV_MED_NS",
    # Reprovação — Ensino Médio
    "2_CAT_MED":    "TAXA_REPROV_MED",
    "2_CAT_MED_01": "TAXA_REPROV_MED_S1",
    "2_CAT_MED_02": "TAXA_REPROV_MED_S2",
    "2_CAT_MED_03": "TAXA_REPROV_MED_S3",
    "2_CAT_MED_04": "TAXA_REPROV_MED_S4",
    "2_CAT_MED_NS": "TAXA_REPROV_MED_NS",
    # Abandono — Ensino Médio  (target principal do projeto)
    "3_CAT_MED":    "TAXA_ABND_MED",
    "3_CAT_MED_01": "TAXA_ABND_MED_S1",
    "3_CAT_MED_02": "TAXA_ABND_MED_S2",
    "3_CAT_MED_03": "TAXA_ABND_MED_S3",
    "3_CAT_MED_04": "TAXA_ABND_MED_S4",
    "3_CAT_MED_NS": "TAXA_ABND_MED_NS",
}

TAXA_COLS = [v for v in _RENAME.values() if v.startswith("TAXA_")]
COL_TARGET = "TAXA_ABND_MED"


# ---------------------------------------------------------------------------
# Carga de um único ano
# ---------------------------------------------------------------------------

def carregar_ano(ano: int) -> pd.DataFrame:
    """Carrega, filtra e normaliza as taxas de rendimento de um único ano.

    Retorna apenas escolas estaduais de PE que ofertam Ensino Médio.
    """
    path = config.RAW_DIR / "taxas_rendimento" / f"tx_rend_escolas_{ano}.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    logger.info("Carregando %s …", path.name)
    df = pd.read_excel(path, header=_HEADER_ROW)

    # --- Filtro geográfico e administrativo ---
    mask = (df["SG_UF"] == config.UF_ALVO_SIGLA) & (df["NO_DEPENDENCIA"] == "Estadual")
    df = df.loc[mask].copy()
    logger.info("  Após filtro PE/Estadual: %d linhas", len(df))

    # --- Seleciona e renomeia colunas ---
    df = df[list(_RENAME.keys())].rename(columns=_RENAME)

    # --- Converte taxas: '--' → NaN, string → float ---
    for col in TAXA_COLS:
        df[col] = pd.to_numeric(df[col].replace(_SENTINEL, pd.NA), errors="coerce")

    # --- Remove escolas que não ofertam EM ---
    # TAXA_ABND_MED nulo indica que a escola não tem dados de EM (não oferta ou não informou)
    n_antes = len(df)
    df = df[df[COL_TARGET].notna()].copy()
    n_sem_em = n_antes - len(df)
    if n_sem_em:
        logger.info("  %d escolas sem oferta/dados de EM removidas.", n_sem_em)

    # --- Tipos das chaves ---
    df["CO_ENTIDADE"] = pd.to_numeric(df["CO_ENTIDADE"], errors="coerce").astype("Int64")
    df["CO_MUNICIPIO"] = pd.to_numeric(df["CO_MUNICIPIO"], errors="coerce").astype("Int64")
    df["NU_ANO_CENSO"] = ano

    _validar_consistencia(df, ano)

    logger.info("  Ano %d: %d escolas com EM carregadas.", ano, len(df))
    return df


def _validar_consistencia(df: pd.DataFrame, ano: int) -> None:
    """Verifica se Aprovação + Reprovação + Abandono ≈ 100 nas linhas completas."""
    completas = df[["TAXA_APROV_MED", "TAXA_REPROV_MED", "TAXA_ABND_MED"]].dropna()
    if completas.empty:
        return
    soma = completas.sum(axis=1)
    # Tolerância de 1 ponto percentual (arredondamento INEP)
    fora = (soma - 100).abs() > 1.0
    n_fora = fora.sum()
    if n_fora:
        logger.warning(
            "Ano %d: %d escola(s) com soma Aprov+Reprov+Abnd ≠ 100 (verificar raw).",
            ano, n_fora,
        )


# ---------------------------------------------------------------------------
# Painel consolidado
# ---------------------------------------------------------------------------

def construir_painel_taxas(anos: list[int] | None = None) -> pd.DataFrame:
    """Consolida todos os anos em um painel longitudinal escola × ano."""
    if anos is None:
        anos = config.ANOS_DISPONIVEIS

    frames: list[pd.DataFrame] = []
    for ano in anos:
        try:
            frames.append(carregar_ano(ano))
        except FileNotFoundError as exc:
            logger.warning("Pulando ano %d: %s", ano, exc)

    if not frames:
        raise RuntimeError("Nenhum arquivo de taxas de rendimento encontrado.")

    painel = pd.concat(frames, ignore_index=True)
    painel = painel.sort_values(["CO_ENTIDADE", "NU_ANO_CENSO"]).reset_index(drop=True)

    # Reordena colunas: identificadores primeiro, depois taxas
    id_cols = ["NU_ANO_CENSO", "CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO", "NO_CATEGORIA"]
    painel = painel[id_cols + TAXA_COLS]

    logger.info(
        "Painel consolidado: %d linhas, %d escolas únicas, anos %s.",
        len(painel),
        painel["CO_ENTIDADE"].nunique(),
        sorted(painel["NU_ANO_CENSO"].unique()),
    )
    return painel


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def salvar_painel(df: pd.DataFrame) -> Path:
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out = config.INTERIM_DIR / "taxas_rendimento_pe_estadual_em.parquet"
    df.to_parquet(out, index=False)
    logger.info("Salvo em: %s", out)
    return out


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        level=logging.INFO,
    )

    painel = construir_painel_taxas()
    salvar_painel(painel)

    print("\n=== Tipos ===")
    print(painel.dtypes)
    print("\n=== Estatísticas ===")
    print(painel[TAXA_COLS].describe().round(2))
    print("\n=== % Nulos por coluna ===")
    print((painel.isnull().mean() * 100).round(1).to_string())
    print(f"\nTotal: {len(painel)} linhas | {painel['CO_ENTIDADE'].nunique()} escolas únicas")
