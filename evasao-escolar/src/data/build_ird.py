"""
ETL do Indicador de Regularidade do Docente (IRD) para escolas estaduais de EM em PE.

Fonte: INEP — Indicador de Regularidade do Docente por escola
Arquivo: data/raw/indicador_regularidade_docente/IRD_ESCOLAS_<ano>.xlsx

Os arquivos XLSX têm 10 linhas de cabeçalho institucional antes dos dados reais.
Colunas com '--' indicam ausência de docentes naquela etapa (substituídas por NaN).

Saída: data/interim/ird_pe_estadual.parquet
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.data import config

logger = logging.getLogger(__name__)

_HEADER_ROW = 10
_SENTINEL = "--"

_RENAME: dict[str, str] = {
    "CO_ENTIDADE":  "CO_ENTIDADE",
    "CO_MUNICIPIO": "CO_MUNICIPIO",
    "NO_MUNICIPIO": "NO_MUNICIPIO",
    "NO_ENTIDADE":  "NO_ENTIDADE",
    "NO_CATEGORIA": "NO_CATEGORIA",
    "EDU_BAS_CAT_0": "IRD_MED",
}

IRD_COLS = ["IRD_MED"]


def carregar_ano(ano: int) -> pd.DataFrame:
    """Carrega, filtra e normaliza o IRD de um único ano."""
    path = config.IRD_DIR / f"IRD_ESCOLAS_{ano}.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    logger.info("Carregando %s …", path.name)
    df = pd.read_excel(path, header=_HEADER_ROW)

    mask = (df["SG_UF"] == config.UF_ALVO_SIGLA) & (df["NO_DEPENDENCIA"] == "Estadual")
    df = df.loc[mask].copy()
    logger.info("  Após filtro PE/Estadual: %d linhas", len(df))

    df = df[list(_RENAME.keys())].rename(columns=_RENAME)

    df["IRD_MED"] = pd.to_numeric(df["IRD_MED"].replace(_SENTINEL, pd.NA), errors="coerce")

    df["CO_ENTIDADE"]  = pd.to_numeric(df["CO_ENTIDADE"],  errors="coerce").astype("Int64")
    df["CO_MUNICIPIO"] = pd.to_numeric(df["CO_MUNICIPIO"], errors="coerce").astype("Int64")
    df["NU_ANO_CENSO"] = ano

    logger.info("  Ano %d: %d escolas carregadas.", ano, len(df))
    return df


def construir_painel_ird(anos: list[int] | None = None) -> pd.DataFrame:
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
        raise RuntimeError("Nenhum arquivo IRD encontrado.")

    painel = pd.concat(frames, ignore_index=True)
    painel = painel.sort_values(["CO_ENTIDADE", "NU_ANO_CENSO"]).reset_index(drop=True)

    id_cols = ["NU_ANO_CENSO", "CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO", "NO_CATEGORIA"]
    painel = painel[id_cols + IRD_COLS]

    logger.info(
        "Painel IRD: %d linhas, %d escolas únicas, anos %s.",
        len(painel),
        painel["CO_ENTIDADE"].nunique(),
        sorted(painel["NU_ANO_CENSO"].unique()),
    )
    return painel


def salvar_painel(df: pd.DataFrame) -> Path:
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out = config.INTERIM_DIR / "ird_pe_estadual.parquet"
    df.to_parquet(out, index=False)
    logger.info("Salvo em: %s", out)
    return out


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT, level=logging.INFO)

    painel = construir_painel_ird()
    salvar_painel(painel)

    print("\n=== Tipos ===")
    print(painel.dtypes)
    print("\n=== Estatísticas ===")
    print(painel[IRD_COLS].describe().round(3))
    print("\n=== % Nulos ===")
    print((painel.isnull().mean() * 100).round(1).to_string())
    print(f"\nTotal: {len(painel)} linhas | {painel['CO_ENTIDADE'].nunique()} escolas únicas")
