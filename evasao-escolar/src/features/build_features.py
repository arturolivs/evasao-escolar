"""
Feature engineering — dataset final para modelagem.

Constrói um dataset escola × ano com features do Censo, indicadores
complementares (IRD, INSE, TDI, AFD), lags de taxas de rendimento
e o target taxa_abandono_t1.

Lógica temporal:
  Para cada escola e cada ano t ∈ {2022, 2023}:
    - features = atributos da escola no ano t
    - target   = taxa de abandono EM observada no ano t+1

  O ano 2024 não entra como ano-feature porque não há dados de 2025.

Saída: data/processed/features.parquet
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.data import config

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES
# =============================================================================

# Anos que servem como ano-feature (t); target vem de t+1
ANOS_FEATURE = [2022, 2023]

# Flags de infraestrutura (excluindo IN_ENERGIA_REDE_PUBLICA — constante)
INFRA_FLAGS = [
    "IN_AGUA_POTAVEL",
    "IN_ESGOTO_REDE_PUBLICA",
    "IN_BIBLIOTECA",
    "IN_LABORATORIO_CIENCIAS",
    "IN_LABORATORIO_INFORMATICA",
    "IN_QUADRA_ESPORTES",
    "IN_REFEITORIO",
    "IN_SALA_LEITURA",
    "IN_AUDITORIO",
    "IN_INTERNET",
    "IN_INTERNET_ALUNOS",
    "IN_BANDA_LARGA",
]

# Taxas usadas como features lag (excluindo Aprovação — colinear: aprov+reprov+abnd=100)
# e excluindo S4/NS por alto percentual de missing
TAXAS_LAG_COLS = [
    "TAXA_ABND_MED",
    "TAXA_ABND_MED_S1", "TAXA_ABND_MED_S2", "TAXA_ABND_MED_S3",
    "TAXA_REPROV_MED",
    "TAXA_REPROV_MED_S1", "TAXA_REPROV_MED_S2", "TAXA_REPROV_MED_S3",
]

# Mapeamento nível INSE → ordinal
_INSE_NIVEL_MAP = {
    "Nível I": 1, "Nível II": 2, "Nível III": 3, "Nível IV": 4,
    "Nível V": 5, "Nível VI": 6, "Nível VII": 7,
}

# Colunas de identificação — não entram no modelo
ID_COLS = ["CO_ENTIDADE", "NU_ANO_CENSO", "NO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO"]

# =============================================================================
# CARGA DOS PARQUETS
# =============================================================================

def _carregar_fontes() -> dict[str, pd.DataFrame]:
    def _load(name: str) -> pd.DataFrame:
        path = config.INTERIM_DIR / f"{name}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Parquet não encontrado: {path}")
        return pd.read_parquet(path)

    fontes = {
        "painel": _load("painel_escola_ano_pe_estadual_em"),
        "taxas":  _load("taxas_rendimento_pe_estadual_em"),
        "ird":    _load("ird_pe_estadual"),
        "inse":   _load("inse_pe_estadual"),
        "tdi":    _load("tdi_pe_estadual"),
        "afd":    _load("afd_pe_estadual"),
    }
    for nome, df in fontes.items():
        if "NU_ANO_CENSO" in df.columns:
            df["NU_ANO_CENSO"] = df["NU_ANO_CENSO"].astype(int)
        logger.info("Carregado %s: %d linhas", nome, len(df))
    return fontes


# =============================================================================
# FEATURES DO CENSO
# =============================================================================

def _features_censo(painel: pd.DataFrame) -> pd.DataFrame:
    """Seleciona e deriva features brutas do Censo Escolar."""
    df = painel.copy()

    # CO_MESORREGIAO: CSV 2022 usa 1-5 enquanto 2023 usa IBGE 2601-2605 — normaliza
    meso_map = {1: 2601, 2: 2602, 3: 2603, 4: 2604, 5: 2605}
    df["CO_MESORREGIAO"] = df["CO_MESORREGIAO"].replace(meso_map)

    # Binárias de localização
    df["is_rural"] = (df["TP_LOCALIZACAO"] == 2).astype(int)
    df["is_loc_diferenciada"] = (
        df["TP_LOCALIZACAO_DIFERENCIADA"].fillna(0) > 0
    ).astype(int)

    # Indicadores operacionais derivados
    df["alunos_por_turma"] = (df["QT_MAT_MED"] / df["QT_TUR_MED"]).clip(5, 50)
    df["alunos_por_docente"] = (df["QT_MAT_MED"] / df["QT_DOC_MED"]).replace(
        [np.inf, -np.inf], np.nan
    )
    df["pct_integral"] = (
        df["QT_MAT_MED_INT"] / df["QT_MAT_MED"] * 100
    ).clip(0, 100)
    df["log_mat_med"] = np.log1p(df["QT_MAT_MED"])
    df["computadores_por_aluno"] = (
        (df["QT_DESKTOP_ALUNO"].fillna(0) + df["QT_TABLET_ALUNO"].fillna(0))
        / df["QT_MAT_MED"]
    ).replace([np.inf, -np.inf], np.nan)

    # Índice composto de infraestrutura (média das flags presentes)
    infra_presentes = [c for c in INFRA_FLAGS if c in df.columns]
    df["indice_infra"] = df[infra_presentes].mean(axis=1)

    return df


# =============================================================================
# IMPUTAÇÃO DE MISSINGS
# =============================================================================

def _imputar_banda_larga(df: pd.DataFrame) -> pd.DataFrame:
    """IN_BANDA_LARGA: 0,8% missing → modal por mesorregião×ano."""
    if "IN_BANDA_LARGA" not in df.columns:
        return df
    mask = df["IN_BANDA_LARGA"].isna()
    if not mask.any():
        return df
    modal = (
        df.groupby(["CO_MESORREGIAO", "NU_ANO_CENSO"])["IN_BANDA_LARGA"]
        .agg(lambda x: x.mode()[0] if not x.mode().empty else 1)
    )
    df = df.copy()
    for idx in df[mask].index:
        key = (df.at[idx, "CO_MESORREGIAO"], df.at[idx, "NU_ANO_CENSO"])
        df.at[idx, "IN_BANDA_LARGA"] = modal.get(key, 1)
    logger.info("IN_BANDA_LARGA: %d missing imputados por modal de mesorregião.", mask.sum())
    return df


def _imputar_por_meso(df: pd.DataFrame, cols: list[str], group_cols: list[str]) -> pd.DataFrame:
    """Imputa colunas numéricas com a média do grupo (mesorregião × ano)."""
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            continue
        n_miss = df[col].isna().sum()
        if n_miss == 0:
            continue
        medias = df.groupby(group_cols)[col].transform("mean")
        df[col] = df[col].fillna(medias)
        # Fallback: média global
        df[col] = df[col].fillna(df[col].mean())
        logger.info("%s: %d missing imputados por média de mesorregião.", col, n_miss)
    return df


# =============================================================================
# JOIN DOS INDICADORES COMPLEMENTARES
# =============================================================================

def _adicionar_ird(df: pd.DataFrame, ird: pd.DataFrame) -> pd.DataFrame:
    ird_sel = ird[["CO_ENTIDADE", "NU_ANO_CENSO", "IRD_MED"]].rename(
        columns={"IRD_MED": "ird_med_t"}
    )
    return df.merge(ird_sel, on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")


def _adicionar_inse(df: pd.DataFrame, inse: pd.DataFrame) -> pd.DataFrame:
    inse_sel = inse[["CO_ENTIDADE", "INSE_MEDIA", "INSE_NIVEL"]].rename(
        columns={"INSE_MEDIA": "inse_media"}
    ).copy()
    inse_sel["inse_nivel_num"] = inse_sel["INSE_NIVEL"].map(_INSE_NIVEL_MAP)
    inse_sel = inse_sel.drop(columns=["INSE_NIVEL"])
    return df.merge(inse_sel, on="CO_ENTIDADE", how="left")


def _adicionar_tdi(df: pd.DataFrame, tdi: pd.DataFrame) -> pd.DataFrame:
    tdi_cols = ["CO_ENTIDADE", "NU_ANO_CENSO", "TDI_MED"]
    for c in ["TDI_MED_S1", "TDI_MED_S2", "TDI_MED_S3"]:
        if c in tdi.columns:
            tdi_cols.append(c)
    rename = {
        "TDI_MED":    "tdi_med_t",
        "TDI_MED_S1": "tdi_s1_t",
        "TDI_MED_S2": "tdi_s2_t",
        "TDI_MED_S3": "tdi_s3_t",
    }
    tdi_sel = tdi[tdi_cols].rename(columns=rename)
    return df.merge(tdi_sel, on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")


def _adicionar_afd(df: pd.DataFrame, afd: pd.DataFrame) -> pd.DataFrame:
    afd_cols = ["CO_ENTIDADE", "NU_ANO_CENSO"]
    for c in ["AFD_MED_G1", "AFD_MED_G3", "AFD_MED_G5"]:
        if c in afd.columns:
            afd_cols.append(c)
    rename = {
        "AFD_MED_G1": "afd_g1_t",
        "AFD_MED_G3": "afd_g3_t",
        "AFD_MED_G5": "afd_g5_t",
    }
    afd_sel = afd[afd_cols].rename(columns=rename)
    return df.merge(afd_sel, on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")


def _adicionar_taxas_lag(df: pd.DataFrame, taxas: pd.DataFrame) -> pd.DataFrame:
    """Adiciona taxas do ano t como features lag e abandono t+1 como target."""
    # Features lag (mesmo ano t)
    lag_cols = [c for c in TAXAS_LAG_COLS if c in taxas.columns]
    rename_lag = {c: c.lower().replace("taxa_", "") + "_t" for c in lag_cols}
    # Simplifica nomes: TAXA_ABND_MED → abnd_t, TAXA_REPROV_MED_S1 → reprov_s1_t
    rename_lag = {
        "TAXA_ABND_MED":      "abnd_t",
        "TAXA_ABND_MED_S1":   "abnd_s1_t",
        "TAXA_ABND_MED_S2":   "abnd_s2_t",
        "TAXA_ABND_MED_S3":   "abnd_s3_t",
        "TAXA_REPROV_MED":    "reprov_t",
        "TAXA_REPROV_MED_S1": "reprov_s1_t",
        "TAXA_REPROV_MED_S2": "reprov_s2_t",
        "TAXA_REPROV_MED_S3": "reprov_s3_t",
    }
    rename_lag = {k: v for k, v in rename_lag.items() if k in taxas.columns}
    taxas_lag = taxas[["CO_ENTIDADE", "NU_ANO_CENSO"] + list(rename_lag.keys())].rename(
        columns=rename_lag
    )
    df = df.merge(taxas_lag, on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")

    # Target: abandono no ano t+1
    target = taxas[["CO_ENTIDADE", "NU_ANO_CENSO", "TAXA_ABND_MED"]].copy()
    target["NU_ANO_CENSO"] = target["NU_ANO_CENSO"] - 1  # shift: target 2023 → feature 2022
    target = target.rename(columns={"TAXA_ABND_MED": "taxa_abandono_t1"})
    df = df.merge(target, on=["CO_ENTIDADE", "NU_ANO_CENSO"], how="left")
    return df


# =============================================================================
# SELEÇÃO FINAL DE COLUNAS
# =============================================================================

def _colunas_features() -> list[str]:
    """Lista ordenada de features que entram no modelo."""
    # Censo — geográfico/estrutural
    geo = ["is_rural", "is_loc_diferenciada", "CO_MESORREGIAO"]
    # Censo — porte (QT_MAT_MED excluída: r=1.0 com log_mat_med)
    porte = ["log_mat_med", "alunos_por_turma",
             "alunos_por_docente", "computadores_por_aluno"]
    # Censo — programas
    programas = ["pct_integral"]
    # Censo — infraestrutura (flags individuais + índice)
    infra = INFRA_FLAGS + ["indice_infra"]
    # Indicadores complementares (ano t)
    # inse_nivel_num excluído: r=0.898 com inse_media (redundante)
    indicadores = [
        "ird_med_t",
        "inse_media",
        "tdi_med_t", "tdi_s1_t", "tdi_s2_t", "tdi_s3_t",
        "afd_g1_t", "afd_g3_t", "afd_g5_t",
    ]
    # Taxas lag (ano t)
    taxas_lag = [
        "abnd_t", "abnd_s1_t", "abnd_s2_t", "abnd_s3_t",
        "reprov_t", "reprov_s1_t", "reprov_s2_t", "reprov_s3_t",
    ]
    return geo + porte + programas + infra + indicadores + taxas_lag


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def construir_dataset(anos_feature: list[int] | None = None) -> pd.DataFrame:
    """
    Constrói o dataset completo de features + target.

    Retorna um DataFrame com:
      - Colunas de ID (CO_ENTIDADE, NU_ANO_CENSO, ...)
      - Features do Censo, derivadas e de indicadores complementares
      - Target: taxa_abandono_t1
    """
    if anos_feature is None:
        anos_feature = ANOS_FEATURE

    fontes = _carregar_fontes()
    painel = fontes["painel"]
    taxas  = fontes["taxas"]

    # Filtra apenas os anos que serão usados como feature
    df = painel[painel["NU_ANO_CENSO"].isin(anos_feature)].copy()
    logger.info("Painel filtrado para anos %s: %d linhas", anos_feature, len(df))

    # ── Features do Censo ────────────────────────────────────────────────────
    df = _features_censo(df)

    # ── Imputação de missings do Censo ───────────────────────────────────────
    df = _imputar_banda_larga(df)
    df = _imputar_por_meso(
        df,
        cols=["alunos_por_docente", "computadores_por_aluno"],
        group_cols=["CO_MESORREGIAO", "NU_ANO_CENSO"],
    )

    # ── Indicadores complementares ───────────────────────────────────────────
    df = _adicionar_ird(df, fontes["ird"])
    df = _adicionar_inse(df, fontes["inse"])
    df = _adicionar_tdi(df, fontes["tdi"])
    df = _adicionar_afd(df, fontes["afd"])

    # Imputa missings dos indicadores por média de mesorregião×ano
    indicadores_num = [
        "ird_med_t", "inse_media", "inse_nivel_num",
        "tdi_med_t", "tdi_s1_t", "tdi_s2_t", "tdi_s3_t",
        "afd_g1_t", "afd_g3_t", "afd_g5_t",
    ]
    df = _imputar_por_meso(df, cols=indicadores_num,
                           group_cols=["CO_MESORREGIAO", "NU_ANO_CENSO"])

    # ── Taxas lag + target ───────────────────────────────────────────────────
    df = _adicionar_taxas_lag(df, taxas)

    # Imputa missings das taxas lag por mesorregião×ano
    taxas_lag_cols = [
        "abnd_t", "abnd_s1_t", "abnd_s2_t", "abnd_s3_t",
        "reprov_t", "reprov_s1_t", "reprov_s2_t", "reprov_s3_t",
    ]
    df = _imputar_por_meso(df, cols=taxas_lag_cols,
                           group_cols=["CO_MESORREGIAO", "NU_ANO_CENSO"])

    # ── Remove linhas sem target ─────────────────────────────────────────────
    n_antes = len(df)
    df = df[df["taxa_abandono_t1"].notna()].copy()
    logger.info(
        "Linhas com target: %d (removidas %d sem target).",
        len(df), n_antes - len(df),
    )

    # ── Seleciona e reordena colunas ─────────────────────────────────────────
    feature_cols = _colunas_features()
    feature_cols_presentes = [c for c in feature_cols if c in df.columns]
    cols_finais = ID_COLS + feature_cols_presentes + ["taxa_abandono_t1"]
    cols_finais = [c for c in cols_finais if c in df.columns]
    df = df[cols_finais].reset_index(drop=True)

    logger.info(
        "Dataset final: %d linhas × %d colunas (%d features + 1 target).",
        len(df), len(df.columns),
        len(feature_cols_presentes),
    )
    return df


def salvar_dataset(df: pd.DataFrame) -> Path:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = config.PROCESSED_DIR / "features.parquet"
    df.to_parquet(out, index=False)
    logger.info("Salvo em: %s", out)
    return out


def relatorio_colunas(df: pd.DataFrame) -> None:
    """Imprime inventário de features com tipo, missing e estatística básica."""
    feature_cols = [c for c in df.columns if c not in ID_COLS + ["taxa_abandono_t1"]]
    print(f"\n{'Coluna':<28} {'Tipo':<10} {'Missing%':>8}  {'Média/Moda':>12}  {'Min':>8}  {'Máx':>8}")
    print("-" * 85)
    for col in feature_cols:
        miss = df[col].isna().mean() * 100
        dtype = str(df[col].dtype)
        if df[col].dtype in [np.float64, np.float32, float]:
            stat = f"{df[col].mean():.2f}"
            mn   = f"{df[col].min():.2f}"
            mx   = f"{df[col].max():.2f}"
        else:
            top = df[col].mode()
            stat = str(top.iloc[0]) if len(top) > 0 else "—"
            mn = str(df[col].min())
            mx = str(df[col].max())
        print(f"  {col:<26} {dtype:<10} {miss:>7.1f}%  {stat:>12}  {mn:>8}  {mx:>8}")


# =============================================================================
# Entry-point
# =============================================================================

if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        level=logging.INFO,
    )

    df = construir_dataset()
    salvar_dataset(df)

    print(f"\nShape final: {df.shape}")
    print(f"Anos feature: {sorted(df['NU_ANO_CENSO'].unique())}")
    print(f"Escolas únicas: {df['CO_ENTIDADE'].nunique()}")
    print(f"\nTarget — taxa_abandono_t1:")
    print(df["taxa_abandono_t1"].describe().round(2).to_string())
    print("\n=== Inventário de features ===")
    relatorio_colunas(df)
    print("\n=== % Nulos por feature ===")
    miss = df.isnull().mean() * 100
    miss = miss[miss > 0]
    if miss.empty:
        print("  Nenhum missing no dataset final.")
    else:
        print(miss.round(2).to_string())
