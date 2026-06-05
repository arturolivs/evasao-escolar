"""
ETL da Taxa de Distorção Idade-Série (TDI) para escolas estaduais de EM em PE.

Fonte: INEP — Taxa de Distorção Idade-Série por escola
Arquivo: data/raw/taxa_distorcao_idade/TDI_ESCOLAS_<ano>.xlsx

Os arquivos XLSX têm 8 linhas de cabeçalho institucional antes dos dados reais.
Colunas com '--' indicam que a escola não oferta aquela série (substituídas por NaN).

Colunas de EM selecionadas:
  MED_CAT_0  → TDI_MED    (total EM)
  MED_01_CAT_0 → TDI_MED_S1 (1ª série)
  MED_02_CAT_0 → TDI_MED_S2 (2ª série)
  MED_03_CAT_0 → TDI_MED_S3 (3ª série)
  MED_04_CAT_0 → TDI_MED_S4 (4ª série — educação profissional integrada)

Saída: data/interim/tdi_pe_estadual.parquet
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.data import config

logger = logging.getLogger(__name__)

_HEADER_ROW = 8
_SENTINEL = "--"

_RENAME: dict[str, str] = {
    "CO_ENTIDADE":   "CO_ENTIDADE",
    "CO_MUNICIPIO":  "CO_MUNICIPIO",
    "NO_MUNICIPIO":  "NO_MUNICIPIO",
    "NO_ENTIDADE":   "NO_ENTIDADE",
    "NO_CATEGORIA":  "NO_CATEGORIA",
    "MED_CAT_0":     "TDI_MED",
    "MED_01_CAT_0":  "TDI_MED_S1",
    "MED_02_CAT_0":  "TDI_MED_S2",
    "MED_03_CAT_0":  "TDI_MED_S3",
    "MED_04_CAT_0":  "TDI_MED_S4",
}

TDI_COLS = ["TDI_MED", "TDI_MED_S1", "TDI_MED_S2", "TDI_MED_S3", "TDI_MED_S4"]


def carregar_ano(ano: int) -> pd.DataFrame:
    """Carrega, filtra e normaliza a TDI de um único ano."""
    path = config.TDI_DIR / f"TDI_ESCOLAS_{ano}.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    logger.info("Carregando %s …", path.name)
    df = pd.read_excel(path, header=_HEADER_ROW)

    mask = (df["SG_UF"] == config.UF_ALVO_SIGLA) & (df["NO_DEPENDENCIA"] == "Estadual")
    df = df.loc[mask].copy()
    logger.info("  Após filtro PE/Estadual: %d linhas", len(df))

    # Seleciona apenas colunas que existem no arquivo (MED_S4 pode estar ausente em alguns anos)
    cols_disponiveis = {c: v for c, v in _RENAME.items() if c in df.columns}
    df = df[list(cols_disponiveis.keys())].rename(columns=cols_disponiveis)

    for col in TDI_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].replace(_SENTINEL, pd.NA), errors="coerce")

    # Remove escolas que não ofertam EM (TDI_MED nulo)
    n_antes = len(df)
    df = df[df["TDI_MED"].notna()].copy()
    if n_antes - len(df):
        logger.info("  %d escolas sem oferta de EM removidas.", n_antes - len(df))

    df["CO_ENTIDADE"]  = pd.to_numeric(df["CO_ENTIDADE"],  errors="coerce").astype("Int64")
    df["CO_MUNICIPIO"] = pd.to_numeric(df["CO_MUNICIPIO"], errors="coerce").astype("Int64")
    df["NU_ANO_CENSO"] = ano

    logger.info("  Ano %d: %d escolas com EM carregadas.", ano, len(df))
    return df


def construir_painel_tdi(anos: list[int] | None = None) -> pd.DataFrame:
    """Consolida todos os anos em painel longitudinal escola × ano."""
    if anos is None:
        anos = config.ANOS_DISPONIVEIS

    frames: list[pd.DataFrame] = []
    for ano in anos:
        try:
            frames.append(carregar_ano(ano))
        except FileNotFoundError as exc:
            logger.warning("Pulando ano %d: %s", ano, exc)

    if not frames:
        raise RuntimeError("Nenhum arquivo TDI encontrado.")

    painel = pd.concat(frames, ignore_index=True)
    painel = painel.sort_values(["CO_ENTIDADE", "NU_ANO_CENSO"]).reset_index(drop=True)

    id_cols = ["NU_ANO_CENSO", "CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO", "NO_CATEGORIA"]
    tdi_presentes = [c for c in TDI_COLS if c in painel.columns]
    painel = painel[id_cols + tdi_presentes]

    logger.info(
        "Painel TDI: %d linhas, %d escolas únicas, anos %s.",
        len(painel),
        painel["CO_ENTIDADE"].nunique(),
        sorted(painel["NU_ANO_CENSO"].unique()),
    )
    return painel


def salvar_painel(df: pd.DataFrame) -> Path:
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out = config.INTERIM_DIR / "tdi_pe_estadual.parquet"
    df.to_parquet(out, index=False)
    logger.info("Salvo em: %s", out)
    return out


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT, level=logging.INFO)

    painel = construir_painel_tdi()
    salvar_painel(painel)

    tdi_presentes = [c for c in TDI_COLS if c in painel.columns]
    print("\n=== Tipos ===")
    print(painel.dtypes)
    print("\n=== Estatísticas ===")
    print(painel[tdi_presentes].describe().round(2))
    print("\n=== % Nulos ===")
    print((painel.isnull().mean() * 100).round(1).to_string())
    print(f"\nTotal: {len(painel)} linhas | {painel['CO_ENTIDADE'].nunique()} escolas únicas")
