"""
Notebook de exploração inicial — Painel de escolas PE / rede estadual / EM.

USO:
    Pode ser executado como script ou aberto como notebook (após conversão
    via jupytext ou nbformat). Pretende-se que sirva como ponto de partida
    para validar visualmente o painel construído.

OBJETIVOS DA EDA INICIAL:
    1. Confirmar que o filtro de universo está correto (N esperado ~1.000 escolas
       estaduais com EM em PE).
    2. Visualizar a distribuição geográfica (por município e mesorregião).
    3. Visualizar a distribuição de matrículas, turmas e docentes de EM.
    4. Identificar valores ausentes nas features iniciais.
    5. Verificar estabilidade do CO_ENTIDADE entre anos (escolas que aparecem
       em todos os anos, escolas que entram/saem do painel).
"""

import logging
import sys
from pathlib import Path

import pandas as pd

# Permite rodar como script: adiciona raiz do projeto ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import build_school_panel  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# =============================================================================
# 1. CONSTRUÇÃO DO PAINEL
# =============================================================================
print("\n" + "=" * 70)
print("FASE 1: Construção do painel")
print("=" * 70)

painel, meta = build_school_panel.montar_painel()

print(f"\nLinhas totais: {meta['n_linhas_total']:,}")
print(f"Escolas únicas: {meta['n_escolas_unicas']:,}")
print(f"\nLinhas por ano:")
for ano, n in sorted(meta["linhas_por_ano"].items()):
    print(f"  {ano}: {n:,}")

print("\nColunas no painel:")
print(painel.dtypes.to_string())

# =============================================================================
# 2. SANITY CHECK — N de escolas estaduais com EM em PE deve estar em torno de 1000
# =============================================================================
print("\n" + "=" * 70)
print("FASE 2: Sanity check do tamanho")
print("=" * 70)

for ano in sorted(painel["NU_ANO_CENSO"].dropna().unique()):
    n = (painel["NU_ANO_CENSO"] == ano).sum()
    print(f"Ano {int(ano)}: {n} escolas no painel.")
    if not (500 < n < 1500):
        print(
            f"  ATENÇÃO: número fora do intervalo esperado (500-1500). "
            f"Reveja os filtros."
        )

# =============================================================================
# 3. DISTRIBUIÇÃO GEOGRÁFICA
# =============================================================================
print("\n" + "=" * 70)
print("FASE 3: Distribuição geográfica (ano mais recente)")
print("=" * 70)

ano_mais_recente = int(painel["NU_ANO_CENSO"].max())
df_recente = painel[painel["NU_ANO_CENSO"] == ano_mais_recente]

if "NO_MUNICIPIO" in df_recente.columns:
    top_municipios = df_recente["NO_MUNICIPIO"].value_counts().head(15)
    print(f"\nTop 15 municípios por nº de escolas (ano {ano_mais_recente}):")
    print(top_municipios.to_string())

if "TP_LOCALIZACAO" in df_recente.columns:
    print(f"\nDistribuição por localização (1=Urbana, 2=Rural):")
    print(df_recente["TP_LOCALIZACAO"].value_counts(dropna=False).to_string())

# =============================================================================
# 4. DISTRIBUIÇÃO DE MATRÍCULAS DE EM
# =============================================================================
print("\n" + "=" * 70)
print("FASE 4: Distribuição de QT_MAT_MED")
print("=" * 70)

if "QT_MAT_MED" in df_recente.columns:
    print(df_recente["QT_MAT_MED"].describe().to_string())
    print(f"\nQuantidade de escolas com QT_MAT_MED == 0: "
          f"{(df_recente['QT_MAT_MED'] == 0).sum()}")
    print(f"Quantidade de escolas com QT_MAT_MED nulo: "
          f"{df_recente['QT_MAT_MED'].isna().sum()}")

# =============================================================================
# 5. VALORES AUSENTES
# =============================================================================
print("\n" + "=" * 70)
print("FASE 5: Missing values por coluna (ano mais recente)")
print("=" * 70)

missing = df_recente.isna().sum().sort_values(ascending=False)
missing = missing[missing > 0]
if len(missing) == 0:
    print("Nenhuma coluna com valores ausentes.")
else:
    pct = (missing / len(df_recente) * 100).round(1)
    relat = pd.DataFrame({"n_missing": missing, "pct_missing": pct})
    print(relat.to_string())

# =============================================================================
# 6. ESTABILIDADE DAS ESCOLAS ENTRE ANOS
# =============================================================================
print("\n" + "=" * 70)
print("FASE 6: Continuidade de escolas entre anos")
print("=" * 70)

escolas_por_ano = (
    painel.groupby("CO_ENTIDADE")["NU_ANO_CENSO"]
    .nunique()
    .value_counts()
    .sort_index()
)
print("\nQuantas escolas aparecem em N anos do painel:")
for n_anos, n_escolas in escolas_por_ano.items():
    print(f"  Em {int(n_anos)} ano(s): {n_escolas} escolas")

# =============================================================================
# 7. SALVAR PAINEL
# =============================================================================
print("\n" + "=" * 70)
print("FASE 7: Salvando painel em parquet")
print("=" * 70)

caminho = build_school_panel.salvar_painel(painel)
print(f"\nPainel salvo em: {caminho}")
print(f"Próximos passos:")
print(f"  1. Baixar Taxas de Rendimento (target)")
print(f"  2. Baixar indicadores: INSE, Distorção, Adequação, Regularidade")
print(f"  3. Construir o target abandono_t1 com lag 1 ano")
print(f"  4. Enriquecer o painel com os indicadores")
print(f"  5. Engenharia de features finais")
