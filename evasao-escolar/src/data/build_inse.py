"""
ETL do Nível Socioeconômico (INSE) para escolas estaduais de EM em PE.

Fonte: INEP/SAEB — Indicador de Nível Socioeconômico por escola
Arquivo: data/raw/inse/INSE_2021_escolas.xlsx

ATENÇÃO: O INSE é calculado nos anos do SAEB (ciclos bienais). Apenas a edição
2021 está disponível em nível escolar no conjunto de dados do projeto. O arquivo
2023 disponível (INSE_2023_estados.xlsx) é agregado por estado, sem granularidade
escolar, e portanto não é utilizado. O INSE de 2021 é tratado como atributo
estático da escola — válido para todos os anos do painel (2022–2024).

Saída: data/interim/inse_pe_estadual.parquet
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.data import config

logger = logging.getLogger(__name__)

# TP_TIPO_REDE no SAEB: 1=Federal, 2=Estadual, 3=Municipal, 4=Privada
_REDE_ESTADUAL = 2

_RENAME: dict[str, str] = {
    "ID_ESCOLA":          "CO_ENTIDADE",
    "CO_MUNICIPIO":       "CO_MUNICIPIO",
    "NO_MUNICIPIO":       "NO_MUNICIPIO",
    "NO_ESCOLA":          "NO_ENTIDADE",
    "TP_LOCALIZACAO":     "TP_LOCALIZACAO",
    "QTD_ALUNOS_INSE":    "INSE_QTD_ALUNOS",
    "MEDIA_INSE":         "INSE_MEDIA",
    "INSE_CLASSIFICACAO": "INSE_NIVEL",
    "PC_NIVEL_1":         "INSE_PC_N1",
    "PC_NIVEL_2":         "INSE_PC_N2",
    "PC_NIVEL_3":         "INSE_PC_N3",
    "PC_NIVEL_4":         "INSE_PC_N4",
    "PC_NIVEL_5":         "INSE_PC_N5",
    "PC_NIVEL_6":         "INSE_PC_N6",
    "PC_NIVEL_7":         "INSE_PC_N7",
    "PC_NIVEL_8":         "INSE_PC_N8",
}

INSE_COLS = [
    "INSE_MEDIA", "INSE_NIVEL", "INSE_QTD_ALUNOS",
    "INSE_PC_N1", "INSE_PC_N2", "INSE_PC_N3", "INSE_PC_N4",
    "INSE_PC_N5", "INSE_PC_N6", "INSE_PC_N7", "INSE_PC_N8",
]

# Único arquivo escola-level disponível
_ANO_INSE = 2021
_FILENAME  = f"INSE_{_ANO_INSE}_escolas.xlsx"


def carregar_inse() -> pd.DataFrame:
    """Carrega e filtra o INSE escola-level (edição 2021)."""
    path = config.INSE_DIR / _FILENAME
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    logger.info("Carregando %s …", path.name)
    df = pd.read_excel(path, header=0)

    mask = (df["SG_UF"] == config.UF_ALVO_SIGLA) & (df["TP_TIPO_REDE"] == _REDE_ESTADUAL)
    df = df.loc[mask].copy()
    logger.info("  Após filtro PE/Estadual: %d escolas", len(df))

    df = df[list(_RENAME.keys())].rename(columns=_RENAME)

    df["CO_ENTIDADE"]  = pd.to_numeric(df["CO_ENTIDADE"],  errors="coerce").astype("Int64")
    df["CO_MUNICIPIO"] = pd.to_numeric(df["CO_MUNICIPIO"], errors="coerce").astype("Int64")
    df["NU_ANO_SAEB"]  = _ANO_INSE

    numeric_cols = [c for c in INSE_COLS if c != "INSE_NIVEL"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info("  INSE %d: %d escolas carregadas.", _ANO_INSE, len(df))
    return df


def salvar_painel(df: pd.DataFrame) -> Path:
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out = config.INTERIM_DIR / "inse_pe_estadual.parquet"
    df.to_parquet(out, index=False)
    logger.info("Salvo em: %s", out)
    return out


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT, level=logging.INFO)

    df = carregar_inse()
    salvar_painel(df)

    print("\n=== Tipos ===")
    print(df.dtypes)
    print("\n=== Estatísticas ===")
    print(df[["INSE_MEDIA"] + [c for c in INSE_COLS if c.startswith("INSE_PC")]].describe().round(2))
    print("\n=== Distribuição por nível ===")
    print(df["INSE_NIVEL"].value_counts().sort_index())
    print("\n=== % Nulos ===")
    print((df.isnull().mean() * 100).round(1).to_string())
    print(f"\nTotal: {len(df)} escolas")
