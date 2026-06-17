"""
ETL do Indicador de Esforço Docente (IED) para escolas estaduais de EM em PE.

Fonte: INEP — Indicador de Esforço Docente por escola
Arquivo: data/raw/esforco_docente/IED_ESCOLAS_<ano>.xlsx

Os arquivos XLSX têm 10 linhas de cabeçalho institucional antes dos dados reais.
Colunas com '--' indicam ausência de docentes naquela etapa (substituídas por NaN).

O IED classifica os docentes em 6 níveis de esforço necessário ao exercício da
profissão (Nível 1 = menor esforço … Nível 6 = maior esforço). Para o Ensino Médio,
as colunas MED_CAT_1..MED_CAT_6 trazem o PERCENTUAL de docentes em cada nível.

Além dos 6 percentuais, deriva-se um índice escalar `IED_MED_MEDIO`: a média
ponderada do nível pelo percentual de docentes (escala 1–6), que resume o esforço
docente típico da escola numa única feature ordinal e interpretável.

Saída: data/interim/ied_pe_estadual.parquet
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
    "MED_CAT_1":    "IED_MED_N1",
    "MED_CAT_2":    "IED_MED_N2",
    "MED_CAT_3":    "IED_MED_N3",
    "MED_CAT_4":    "IED_MED_N4",
    "MED_CAT_5":    "IED_MED_N5",
    "MED_CAT_6":    "IED_MED_N6",
}

IED_NIVEL_COLS = [
    "IED_MED_N1", "IED_MED_N2", "IED_MED_N3",
    "IED_MED_N4", "IED_MED_N5", "IED_MED_N6",
]
IED_COLS = IED_NIVEL_COLS + ["IED_MED_MEDIO"]


def _indice_medio(df: pd.DataFrame) -> pd.Series:
    """Média ponderada do nível de esforço (1–6) pelo percentual de docentes.

    Como os percentuais somam ~100, divide-se pela soma observada (robusto a
    pequenos desvios de arredondamento do INEP). Escolas sem docentes em
    nenhum nível (soma 0/NaN) resultam em NaN.
    """
    pesos = range(1, len(IED_NIVEL_COLS) + 1)
    numerador = sum(peso * df[col] for peso, col in zip(pesos, IED_NIVEL_COLS))
    soma = df[IED_NIVEL_COLS].sum(axis=1, min_count=1)
    return (numerador / soma).where(soma > 0)


def carregar_ano(ano: int) -> pd.DataFrame:
    """Carrega, filtra e normaliza o IED de um único ano."""
    path = config.IED_DIR / f"IED_ESCOLAS_{ano}.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    logger.info("Carregando %s …", path.name)
    df = pd.read_excel(path, header=_HEADER_ROW)

    mask = (df["SG_UF"] == config.UF_ALVO_SIGLA) & (df["NO_DEPENDENCIA"] == "Estadual")
    df = df.loc[mask].copy()
    logger.info("  Após filtro PE/Estadual: %d linhas", len(df))

    df = df[list(_RENAME.keys())].rename(columns=_RENAME)

    for col in IED_NIVEL_COLS:
        df[col] = pd.to_numeric(df[col].replace(_SENTINEL, pd.NA), errors="coerce")

    # Remove escolas que não ofertam EM (todos os níveis nulos)
    n_antes = len(df)
    df = df[df[IED_NIVEL_COLS].notna().any(axis=1)].copy()
    if n_antes - len(df):
        logger.info("  %d escolas sem oferta de EM removidas.", n_antes - len(df))

    df["IED_MED_MEDIO"] = _indice_medio(df)

    df["CO_ENTIDADE"]  = pd.to_numeric(df["CO_ENTIDADE"],  errors="coerce").astype("Int64")
    df["CO_MUNICIPIO"] = pd.to_numeric(df["CO_MUNICIPIO"], errors="coerce").astype("Int64")
    df["NU_ANO_CENSO"] = ano

    logger.info("  Ano %d: %d escolas com EM carregadas.", ano, len(df))
    return df


def construir_painel_ied(anos: list[int] | None = None) -> pd.DataFrame:
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
        raise RuntimeError("Nenhum arquivo IED encontrado.")

    painel = pd.concat(frames, ignore_index=True)
    painel = painel.sort_values(["CO_ENTIDADE", "NU_ANO_CENSO"]).reset_index(drop=True)

    id_cols = ["NU_ANO_CENSO", "CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO", "NO_CATEGORIA"]
    painel = painel[id_cols + IED_COLS]

    logger.info(
        "Painel IED: %d linhas, %d escolas únicas, anos %s.",
        len(painel),
        painel["CO_ENTIDADE"].nunique(),
        sorted(painel["NU_ANO_CENSO"].unique()),
    )
    return painel


def salvar_painel(df: pd.DataFrame) -> Path:
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out = config.INTERIM_DIR / "ied_pe_estadual.parquet"
    df.to_parquet(out, index=False)
    logger.info("Salvo em: %s", out)
    return out


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT, level=logging.INFO)

    painel = construir_painel_ied()
    salvar_painel(painel)

    print("\n=== Tipos ===")
    print(painel.dtypes)
    print("\n=== Estatísticas ===")
    print(painel[IED_COLS].describe().round(2))
    print("\n=== % Nulos ===")
    print((painel.isnull().mean() * 100).round(1).to_string())
    print(f"\nTotal: {len(painel)} linhas | {painel['CO_ENTIDADE'].nunique()} escolas únicas")
