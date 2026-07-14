"""
Camada de serviço do dashboard — Fase 8 (priorização de escolas).

Concentra TODA a lógica de domínio que o painel Streamlit consome, mantendo
a UI fina e a regra de negócio testável. Cobre o Cenário A acordado no
projeto: **priorizar escolas por risco e explicar o porquê** — sem
recomendar ações prescritivas (o modelo é correlacional; a própria análise
SHAP adverte contra leitura causal).

Três entregas, atadas às perguntas de pesquisa:
  P2 (previsão)   → `ranking()`: ordena as escolas por risco de abandono
                    previsto em t+1, com filtros e marcação de prioridade.
  P2 (local)      → `explicar_escola()`: decompõe a predição de UMA escola
                    em contribuições por indicador (SHAP), em linguagem de
                    gestor — quais fatores puxam o risco para cima/baixo.
  P3 (diagnóstico)→ resíduo (real − previsto): sinaliza escolas que abandonam
                    MAIS (alerta) ou MENOS (resiliente) do que o perfil prevê.

NOTA DE ESCALA: o modelo final usa transformação `sqrt` no target. As
predições e resíduos vêm de `predict()` já em pontos percentuais (a inversa
é aplicada pelo `TransformedTargetRegressor`). Os valores SHAP vivem no
espaço sqrt — usados aqui apenas para RANKING e SINAL das contribuições, que
são preservados por a raiz ser monotônica (mesma ressalva do notebook 09).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.models.explain import calcular_shap_values
from src.models.train import (
    ANO_COL,
    TARGET_COL,
    carregar_dataset,
    carregar_modelo,
    colunas_features,
)
from src.recommend.labels import rotular_feature, rotular_mesorregiao

logger = logging.getLogger(__name__)

# Colunas de identificação preservadas no ranking.
ID_COLS = ["CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO"]

# Limiar (em desvios-padrão do resíduo) para rotular o diagnóstico.
Z_ALERTA = 1.0       # abandona bem mais do que o previsto
Z_RESILIENTE = -1.0  # abandona bem menos do que o previsto

# Prefixo das dummies da mesorregião na matriz pós-pré-processamento.
_PREFIXO_MESO = "CO_MESORREGIAO_"


def _grupo_meso(nome_transformado: str) -> str:
    """Mapeia uma coluna pós-transformação para o indicador de origem,
    reunindo as dummies da mesorregião sob um único fator."""
    if nome_transformado.startswith(_PREFIXO_MESO):
        return "CO_MESORREGIAO"
    return nome_transformado


def _rotulo_localizacao(row: pd.Series) -> str:
    """Rótulo de localização por escola (precedência diferenciada > rural)."""
    if row.get("is_loc_diferenciada", 0) == 1:
        return "Diferenciada (indígena/quilombola)"
    return "Rural" if row.get("is_rural", 0) == 1 else "Urbana"


def _diagnostico(z: float) -> str:
    """Classifica o resíduo padronizado em alerta / resiliente / esperado."""
    if z >= Z_ALERTA:
        return "Alerta (abandona mais que o previsto)"
    if z <= Z_RESILIENTE:
        return "Resiliente (abandona menos que o previsto)"
    return "Dentro do esperado"


@dataclass
class ContribuicaoEscola:
    """Uma linha da explicação local: o fator e quanto/como ele moveu o risco."""
    feature: str          # nome técnico (origem)
    rotulo: str           # rótulo legível ao gestor
    valor: float | None   # valor observado do indicador na escola
    shap: float           # contribuição SHAP (espaço sqrt; sinal é o que importa)
    direcao: str          # "↑ aumenta risco" | "↓ reduz risco"


class ServicoPriorizacao:
    """
    Serviço de priorização carregado uma única vez (modelo + features +
    SHAP) e consultado pelo painel. Imutável após a construção.

    Construa via `ServicoPriorizacao.criar()`, que cuida da carga padrão do
    modelo serializado e do dataset de features.
    """

    def __init__(self, modelo, df: pd.DataFrame):
        self._modelo = modelo
        self._fcols = colunas_features(df)
        self._base = self._montar_base(df)
        # SHAP de todas as observações (rápido: TreeExplainer exato).
        self._shap = calcular_shap_values(modelo, df[self._fcols])
        self._df_features = df[self._fcols].reset_index(drop=True)

    # ------------------------------------------------------------------ #
    # Construção
    # ------------------------------------------------------------------ #
    @classmethod
    def criar(cls, nome_modelo: str = "xgboost_v1") -> "ServicoPriorizacao":
        modelo = carregar_modelo(nome_modelo)
        df = carregar_dataset().reset_index(drop=True)
        logger.info("Serviço de priorização: %d escolas-ano carregadas.", len(df))
        return cls(modelo, df)

    def _montar_base(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tabela-base por escola-ano: risco previsto, resíduo, rótulos."""
        X = df[self._fcols]
        y_pred = np.asarray(self._modelo.predict(X), dtype=float)
        y_real = df[TARGET_COL].to_numpy(dtype=float)

        residuo = y_real - y_pred
        dp = residuo.std()
        residuo_z = residuo / dp if dp > 0 else np.zeros_like(residuo)

        base = df[ID_COLS + [ANO_COL]].copy()
        base["mesorregiao"] = df["CO_MESORREGIAO"].map(rotular_mesorregiao)
        base["localizacao"] = df.apply(_rotulo_localizacao, axis=1)
        base["risco_previsto"] = y_pred
        base["abandono_real"] = y_real
        base["residuo"] = residuo
        base["residuo_z"] = residuo_z
        base["diagnostico"] = [_diagnostico(z) for z in residuo_z]

        # Ranking de risco POR ANO (1 = maior risco) + percentil.
        base["risco_rank"] = (
            base.groupby(ANO_COL)["risco_previsto"]
            .rank(ascending=False, method="first")
            .astype(int)
        )
        base["risco_percentil"] = (
            base.groupby(ANO_COL)["risco_previsto"].rank(pct=True) * 100
        )
        return base

    # ------------------------------------------------------------------ #
    # Consultas
    # ------------------------------------------------------------------ #
    def anos_disponiveis(self) -> list[int]:
        return sorted(self._base[ANO_COL].unique().tolist())

    def ano_mais_recente(self) -> int:
        """Ano de features mais recente (ranking operacional padrão)."""
        return max(self.anos_disponiveis())

    def mesorregioes(self) -> list[str]:
        return sorted(self._base["mesorregiao"].dropna().unique().tolist())

    def municipios(self, mesorregiao: str | None = None) -> list[str]:
        b = self._base
        if mesorregiao:
            b = b[b["mesorregiao"] == mesorregiao]
        return sorted(b["NO_MUNICIPIO"].dropna().unique().tolist())

    def ranking(
        self,
        ano: int | None = None,
        mesorregiao: str | None = None,
        municipio: str | None = None,
        busca: str | None = None,
        top_k: int | None = None,
    ) -> pd.DataFrame:
        """
        Escolas ordenadas por risco previsto (maior → menor) para um ano.

        `top_k` marca as `k` de maior risco do ano como prioritárias (coluna
        `prioritaria`) — a leitura de priorização que o gestor usa em campo.
        Os demais filtros são aplicados DEPOIS da marcação, para que a
        prioridade reflita o ano inteiro, não só o recorte exibido.
        """
        if ano is None:
            ano = self.ano_mais_recente()

        b = self._base[self._base[ANO_COL] == ano].copy()
        b["prioritaria"] = False
        if top_k:
            b.loc[b["risco_rank"] <= top_k, "prioritaria"] = True

        if mesorregiao:
            b = b[b["mesorregiao"] == mesorregiao]
        if municipio:
            b = b[b["NO_MUNICIPIO"] == municipio]
        if busca:
            b = b[b["NO_ENTIDADE"].str.contains(busca, case=False, na=False)]

        return b.sort_values("risco_previsto", ascending=False).reset_index(drop=True)

    def explicar_escola(
        self, co_entidade: int, ano: int, top_n: int = 8
    ) -> tuple[pd.Series, list[ContribuicaoEscola]]:
        """
        Decompõe a predição de UMA escola-ano em contribuições por indicador.

        Reúne as dummies da mesorregião num único fator e devolve os `top_n`
        de maior |contribuição|, já com rótulo legível, valor observado e
        direção (sobe/desce o risco). Base do "porquê" exibido no painel.
        """
        mask = (
            (self._base["CO_ENTIDADE"] == co_entidade)
            & (self._base[ANO_COL] == ano)
        )
        if not mask.any():
            raise KeyError(f"Escola {co_entidade} não encontrada no ano {ano}.")

        pos = int(np.flatnonzero(mask.to_numpy())[0])
        info = self._base.loc[mask].iloc[0]

        valores = self._shap.values[pos]
        nomes = list(self._shap.feature_names)
        linha_feat = self._df_features.iloc[pos]

        # Agrega contribuições por indicador de origem (mesorregião unificada).
        agreg: dict[str, float] = {}
        for nome, v in zip(nomes, valores):
            agreg[_grupo_meso(nome)] = agreg.get(_grupo_meso(nome), 0.0) + float(v)

        contribs: list[ContribuicaoEscola] = []
        for feat, shap_v in agreg.items():
            valor = (
                float(linha_feat[feat])
                if feat in linha_feat.index
                else None
            )
            contribs.append(
                ContribuicaoEscola(
                    feature=feat,
                    rotulo=rotular_feature(feat),
                    valor=valor,
                    shap=shap_v,
                    direcao="↑ aumenta risco" if shap_v > 0 else "↓ reduz risco",
                )
            )

        contribs.sort(key=lambda c: abs(c.shap), reverse=True)
        return info, contribs[:top_n]

    def resumo_por_grupo(self, ano: int | None = None) -> pd.DataFrame:
        """Risco médio e contagem por localização — panorama de equidade."""
        if ano is None:
            ano = self.ano_mais_recente()
        b = self._base[self._base[ANO_COL] == ano]
        return (
            b.groupby("localizacao")
            .agg(
                escolas=("CO_ENTIDADE", "count"),
                risco_medio=("risco_previsto", "mean"),
                alertas=("diagnostico",
                         lambda s: int(s.str.startswith("Alerta").sum())),
            )
            .reset_index()
            .sort_values("risco_medio", ascending=False)
            .reset_index(drop=True)
        )
