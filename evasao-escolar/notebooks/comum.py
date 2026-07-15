"""
Infraestrutura compartilhada pelos notebooks de análise.

Importar este módulo (antes de matplotlib.pyplot e de src.*) tem efeitos
colaterais intencionais: força o backend Agg, reconfigura o stdout para UTF-8,
configura o logging e adiciona a raiz do projeto ao sys.path.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPORTS_DIR = ROOT / "reports"
FIGURAS_DIR = REPORTS_DIR / "figuras"
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
_logger = logging.getLogger(__name__)

ANOS_CENSO = [2022, 2023, 2024]

CORES_ANOS = {2022: "#2196F3", 2023: "#FF9800", 2024: "#4CAF50"}
COR_URBANA = "#1565C0"
COR_RURAL = "#2E7D32"
COR_ABANDONO = "#C62828"
COR_REPROVACAO = "#E65100"
COR_APROVACAO = "#1B5E20"

LABELS_LOCALIZACAO = {1: "Urbana", 2: "Rural"}

NOMES_MESORREGIOES = {
    2601: "Sertão Pernambucano",
    2602: "São Francisco Pernambucano",
    2603: "Agreste Pernambucano",
    2604: "Mata Pernambucana",
    2605: "Metropolitana de Recife",
}

NOMES_CURTOS_MESORREGIOES = {
    2601: "Sertão",
    2602: "São Francisco",
    2603: "Agreste",
    2604: "Mata",
    2605: "Metropolitana",
}

CORES_MODELOS = {
    "dummy_media": "#9E9E9E",
    "dummy": "#9E9E9E",
    "ridge": "#1565C0",
    "random_forest": "#2E7D32",
    "xgboost": "#C62828",
}

LABELS_MODELOS = {
    "dummy_media": "Dummy (média)",
    "dummy": "Dummy (média)",
    "ridge": "Ridge",
    "random_forest": "Random Forest",
    "xgboost": "XGBoost",
}

METRICAS_AVALIACAO = ["rmse", "mae", "r2", "spearman", "precision_at_k"]


def sep(titulo: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {titulo}")
    print("=" * 70)


def salvar_figura(fig: plt.Figure, nome: str) -> None:
    caminho = FIGURAS_DIR / nome
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    _logger.info("Figura salva: %s", caminho)


def carregar_parquet(caminho: Path, comando_geracao: str) -> pd.DataFrame:
    """Lê um parquet interim/processed, exigindo que já tenha sido gerado."""
    if not caminho.exists():
        raise FileNotFoundError(
            f"Parquet não encontrado: {caminho}\nExecute: {comando_geracao}"
        )
    df = pd.read_parquet(caminho)
    if "NU_ANO_CENSO" in df.columns:
        df["NU_ANO_CENSO"] = df["NU_ANO_CENSO"].astype(int)
    _logger.info("Carregado %s: %d linhas × %d colunas.", caminho.name, *df.shape)
    return df


def imprimir_tabela_metricas(resumos: dict[str, dict[str, str]]) -> None:
    print(f"\n{'Modelo':<22}" + "".join(f"{m:>18}" for m in METRICAS_AVALIACAO))
    print("-" * (22 + 18 * len(METRICAS_AVALIACAO)))
    for nome, resumo in resumos.items():
        label = LABELS_MODELOS.get(nome, nome)
        print(f"  {label:<20}" + "".join(f"{resumo[m]:>18}" for m in METRICAS_AVALIACAO))


def salvar_metricas_cv_e_temporal(
    folds_por_modelo: dict[str, pd.DataFrame],
    resultados_temporais: dict[str, dict],
    caminho: Path,
) -> None:
    """Consolida num CSV as métricas por fold da CV e as da validação temporal."""
    linhas = []
    for nome, df_folds in folds_por_modelo.items():
        for _, fold in df_folds.iterrows():
            linhas.append({
                "modelo": nome,
                "avaliacao": "cv_groupkfold",
                "fold": int(fold["fold"]),
                **{m: fold[m] for m in METRICAS_AVALIACAO},
            })
    for nome, metricas in resultados_temporais.items():
        linhas.append({
            "modelo": nome,
            "avaliacao": "temporal_2023_2024",
            "fold": None,
            **{m: metricas[m] for m in METRICAS_AVALIACAO},
        })
    pd.DataFrame(linhas).to_csv(caminho, index=False)
    print(f"\nMétricas salvas em: {caminho}")
