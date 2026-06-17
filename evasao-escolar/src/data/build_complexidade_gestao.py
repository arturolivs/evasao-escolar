"""
ETL do Indicador de Complexidade de Gestão da Escola (ICG) para escolas
estaduais de EM em PE.

Fonte: INEP — Indicador de Complexidade de Gestão da Escola
Arquivo: data/raw/complexidade_gestao_escola/ICG_ESCOLAS_<ano>.xlsx

Os arquivos XLSX têm 10 linhas de cabeçalho institucional antes dos dados reais.
A coluna COMPLEX traz o nível de complexidade textual ("Nível  1" … "Nível  6"),
combinando porte, número de turnos, etapas e modalidades ofertadas.

O ICG é convertido em uma variável ordinal `ICG_NIVEL` (1 = menor … 6 = maior
complexidade de gestão). Diferentemente dos demais indicadores, é definido para
toda escola em atividade (não depende de oferta de EM por etapa), então o filtro
de "escola com EM" é resolvido na junção com o painel em build_features.

Saída: data/interim/icg_pe_estadual.parquet
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
    "COMPLEX":      "ICG_TEXTO",
}

ICG_COLS = ["ICG_NIVEL"]


def _parse_nivel(serie: pd.Series) -> pd.Series:
    """Extrai o inteiro do rótulo "Nível  N" → N (1–6); demais valores → NaN."""
    texto = serie.replace(_SENTINEL, pd.NA).astype("string")
    nivel = texto.str.extract(r"(\d+)", expand=False)
    return pd.to_numeric(nivel, errors="coerce").astype("Int64")


def carregar_ano(ano: int) -> pd.DataFrame:
    """Carrega, filtra e normaliza o ICG de um único ano."""
    path = config.ICG_DIR / f"ICG_ESCOLAS_{ano}.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    logger.info("Carregando %s …", path.name)
    df = pd.read_excel(path, header=_HEADER_ROW)

    mask = (df["SG_UF"] == config.UF_ALVO_SIGLA) & (df["NO_DEPENDENCIA"] == "Estadual")
    df = df.loc[mask].copy()
    logger.info("  Após filtro PE/Estadual: %d linhas", len(df))

    df = df[list(_RENAME.keys())].rename(columns=_RENAME)

    df["ICG_NIVEL"] = _parse_nivel(df["ICG_TEXTO"])

    # Remove escolas sem nível de complexidade atribuído
    n_antes = len(df)
    df = df[df["ICG_NIVEL"].notna()].copy()
    if n_antes - len(df):
        logger.info("  %d escolas sem nível de complexidade removidas.", n_antes - len(df))

    df["CO_ENTIDADE"]  = pd.to_numeric(df["CO_ENTIDADE"],  errors="coerce").astype("Int64")
    df["CO_MUNICIPIO"] = pd.to_numeric(df["CO_MUNICIPIO"], errors="coerce").astype("Int64")
    df["NU_ANO_CENSO"] = ano

    logger.info("  Ano %d: %d escolas carregadas.", ano, len(df))
    return df


def construir_painel_icg(anos: list[int] | None = None) -> pd.DataFrame:
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
        raise RuntimeError("Nenhum arquivo ICG encontrado.")

    painel = pd.concat(frames, ignore_index=True)
    painel = painel.sort_values(["CO_ENTIDADE", "NU_ANO_CENSO"]).reset_index(drop=True)

    id_cols = ["NU_ANO_CENSO", "CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO", "NO_CATEGORIA"]
    painel = painel[id_cols + ICG_COLS]

    logger.info(
        "Painel ICG: %d linhas, %d escolas únicas, anos %s.",
        len(painel),
        painel["CO_ENTIDADE"].nunique(),
        sorted(painel["NU_ANO_CENSO"].unique()),
    )
    return painel


def salvar_painel(df: pd.DataFrame) -> Path:
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out = config.INTERIM_DIR / "icg_pe_estadual.parquet"
    df.to_parquet(out, index=False)
    logger.info("Salvo em: %s", out)
    return out


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT, level=logging.INFO)

    painel = construir_painel_icg()
    salvar_painel(painel)

    print("\n=== Tipos ===")
    print(painel.dtypes)
    print("\n=== Distribuição de níveis ===")
    print(painel["ICG_NIVEL"].value_counts().sort_index().to_string())
    print("\n=== % Nulos ===")
    print((painel.isnull().mean() * 100).round(1).to_string())
    print(f"\nTotal: {len(painel)} linhas | {painel['CO_ENTIDADE'].nunique()} escolas únicas")
