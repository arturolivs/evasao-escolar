"""
Exploração inicial — Painel de escolas PE / rede estadual / EM.

Valida visualmente o painel construído por src.data.build_school_panel:
  1. Tamanho do universo (~1.000 escolas estaduais com EM em PE).
  2. Distribuição geográfica (município e localização).
  3. Distribuição de matrículas de EM.
  4. Valores ausentes nas features iniciais.
  5. Continuidade do CO_ENTIDADE entre anos.
Ao final salva o painel em parquet (data/interim).
"""

from comum import sep

import pandas as pd

from src.data import build_school_panel


def construir_painel() -> pd.DataFrame:
    sep("FASE 1: Construção do painel")
    painel, meta = build_school_panel.montar_painel()

    print(f"\nLinhas totais: {meta['n_linhas_total']:,}")
    print(f"Escolas únicas: {meta['n_escolas_unicas']:,}")
    print(f"\nLinhas por ano:")
    for ano, n in sorted(meta["linhas_por_ano"].items()):
        print(f"  {ano}: {n:,}")

    print("\nColunas no painel:")
    print(painel.dtypes.to_string())
    return painel


def validar_tamanho_universo(painel: pd.DataFrame) -> None:
    sep("FASE 2: Sanity check do tamanho")
    for ano in sorted(painel["NU_ANO_CENSO"].dropna().unique()):
        n = (painel["NU_ANO_CENSO"] == ano).sum()
        print(f"Ano {int(ano)}: {n} escolas no painel.")
        if not (500 < n < 1500):
            print(
                f"  ATENÇÃO: número fora do intervalo esperado (500-1500). "
                f"Reveja os filtros."
            )


def relatorio_geografico(df_recente: pd.DataFrame, ano: int) -> None:
    sep(f"FASE 3: Distribuição geográfica (ano mais recente)")

    if "NO_MUNICIPIO" in df_recente.columns:
        top_municipios = df_recente["NO_MUNICIPIO"].value_counts().head(15)
        print(f"\nTop 15 municípios por nº de escolas (ano {ano}):")
        print(top_municipios.to_string())

    if "TP_LOCALIZACAO" in df_recente.columns:
        print(f"\nDistribuição por localização (1=Urbana, 2=Rural):")
        print(df_recente["TP_LOCALIZACAO"].value_counts(dropna=False).to_string())


def relatorio_matriculas(df_recente: pd.DataFrame) -> None:
    sep("FASE 4: Distribuição de QT_MAT_MED")

    if "QT_MAT_MED" not in df_recente.columns:
        return
    print(df_recente["QT_MAT_MED"].describe().to_string())
    print(f"\nQuantidade de escolas com QT_MAT_MED == 0: "
          f"{(df_recente['QT_MAT_MED'] == 0).sum()}")
    print(f"Quantidade de escolas com QT_MAT_MED nulo: "
          f"{df_recente['QT_MAT_MED'].isna().sum()}")


def relatorio_valores_ausentes(df_recente: pd.DataFrame) -> None:
    sep("FASE 5: Missing values por coluna (ano mais recente)")

    missing = df_recente.isna().sum().sort_values(ascending=False)
    missing = missing[missing > 0]
    if len(missing) == 0:
        print("Nenhuma coluna com valores ausentes.")
        return
    pct = (missing / len(df_recente) * 100).round(1)
    relatorio = pd.DataFrame({"n_missing": missing, "pct_missing": pct})
    print(relatorio.to_string())


def relatorio_continuidade_entre_anos(painel: pd.DataFrame) -> None:
    sep("FASE 6: Continuidade de escolas entre anos")

    escolas_por_n_anos = (
        painel.groupby("CO_ENTIDADE")["NU_ANO_CENSO"]
        .nunique()
        .value_counts()
        .sort_index()
    )
    print("\nQuantas escolas aparecem em N anos do painel:")
    for n_anos, n_escolas in escolas_por_n_anos.items():
        print(f"  Em {int(n_anos)} ano(s): {n_escolas} escolas")


def salvar_painel(painel: pd.DataFrame) -> None:
    sep("FASE 7: Salvando painel em parquet")

    caminho = build_school_panel.salvar_painel(painel)
    print(f"\nPainel salvo em: {caminho}")
    print(f"Próximos passos:")
    print(f"  1. Baixar Taxas de Rendimento (target)")
    print(f"  2. Baixar indicadores: INSE, Distorção, Adequação, Regularidade")
    print(f"  3. Construir o target abandono_t1 com lag 1 ano")
    print(f"  4. Enriquecer o painel com os indicadores")
    print(f"  5. Engenharia de features finais")


def main() -> None:
    painel = construir_painel()
    validar_tamanho_universo(painel)

    ano_mais_recente = int(painel["NU_ANO_CENSO"].max())
    df_recente = painel[painel["NU_ANO_CENSO"] == ano_mais_recente]

    relatorio_geografico(df_recente, ano_mais_recente)
    relatorio_matriculas(df_recente)
    relatorio_valores_ausentes(df_recente)
    relatorio_continuidade_entre_anos(painel)
    salvar_painel(painel)


if __name__ == "__main__":
    main()
