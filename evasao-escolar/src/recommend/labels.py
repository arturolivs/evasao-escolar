"""
Rótulos legíveis para o público gestor — Fase 8 (dashboard).

O modelo e os datasets usam nomes técnicos (`abnd_t`, `tdi_med_t`,
`afd_g5_t`, dummies `CO_MESORREGIAO_2601`...). O dashboard é voltado aos
gestores da Secretaria Estadual de Educação, então toda exibição passa por
este mapa para virar linguagem comum.

Mantido isolado da lógica de scoring para que `service.py` permaneça
agnóstico de apresentação e os rótulos possam evoluir sem tocar no modelo.
"""

from __future__ import annotations

# Mesorregiões de Pernambuco (códigos IBGE usados em CO_MESORREGIAO).
MESORREGIAO_NOMES: dict[int, str] = {
    2601: "Sertão Pernambucano",
    2602: "São Francisco Pernambucano",
    2603: "Agreste Pernambucano",
    2604: "Mata Pernambucana",
    2605: "Metropolitana de Recife",
}

# Nome técnico da feature → rótulo em português para o gestor.
FEATURE_LABELS: dict[str, str] = {
    # Localização / contexto
    "is_rural": "Localização rural",
    "is_loc_diferenciada": "Localização diferenciada (indígena/quilombola)",
    "CO_MESORREGIAO": "Mesorregião",
    "oferta_em_nao_seriado": "Oferta de EM fora das séries regulares (EJA/modular)",
    # Porte e proporções
    "log_mat_med": "Porte (nº de matrículas)",
    "alunos_por_turma": "Alunos por turma",
    "alunos_por_docente": "Alunos por docente",
    "computadores_por_aluno": "Computadores por aluno",
    "pct_integral": "% de matrículas em tempo integral",
    # Infraestrutura
    "IN_AGUA_POTAVEL": "Água potável",
    "IN_ESGOTO_REDE_PUBLICA": "Esgoto em rede pública",
    "IN_BIBLIOTECA": "Biblioteca",
    "IN_LABORATORIO_CIENCIAS": "Laboratório de ciências",
    "IN_LABORATORIO_INFORMATICA": "Laboratório de informática",
    "IN_QUADRA_ESPORTES": "Quadra de esportes",
    "IN_REFEITORIO": "Refeitório",
    "IN_SALA_LEITURA": "Sala de leitura",
    "IN_AUDITORIO": "Auditório",
    "IN_INTERNET": "Internet",
    "IN_INTERNET_ALUNOS": "Internet para alunos",
    "IN_BANDA_LARGA": "Banda larga",
    "indice_infra": "Índice de infraestrutura",
    # Indicadores complementares
    "ird_med_t": "Regularidade do corpo docente (IRD)",
    "inse_media": "Nível socioeconômico (INSE)",
    "tdi_med_t": "Distorção idade-série (Ensino Médio)",
    "tdi_s1_t": "Distorção idade-série — 1ª série",
    "tdi_s2_t": "Distorção idade-série — 2ª série",
    "tdi_s3_t": "Distorção idade-série — 3ª série",
    "afd_g1_t": "Adequação da formação docente — Grupo 1",
    "afd_g3_t": "Adequação da formação docente — Grupo 3",
    "afd_g5_t": "Adequação da formação docente — Grupo 5",
    # Histórico de fluxo (ano anterior)
    "abnd_t": "Abandono no ano anterior (Ensino Médio)",
    "abnd_s1_t": "Abandono no ano anterior — 1ª série",
    "abnd_s2_t": "Abandono no ano anterior — 2ª série",
    "abnd_s3_t": "Abandono no ano anterior — 3ª série",
    "reprov_t": "Reprovação no ano anterior (Ensino Médio)",
    "reprov_s1_t": "Reprovação no ano anterior — 1ª série",
    "reprov_s2_t": "Reprovação no ano anterior — 2ª série",
    "reprov_s3_t": "Reprovação no ano anterior — 3ª série",
}


def rotular_feature(nome: str) -> str:
    """
    Devolve o rótulo legível de uma feature. Trata as dummies da
    mesorregião (`CO_MESORREGIAO_2605`) resolvendo o código para o nome
    da região. Cai no próprio nome se não houver mapeamento.
    """
    if nome.startswith("CO_MESORREGIAO_"):
        try:
            codigo = int(nome.rsplit("_", 1)[-1])
        except ValueError:
            return FEATURE_LABELS["CO_MESORREGIAO"]
        regiao = MESORREGIAO_NOMES.get(codigo, str(codigo))
        return f"Mesorregião: {regiao}"
    return FEATURE_LABELS.get(nome, nome)


def rotular_mesorregiao(codigo: int) -> str:
    """Nome da mesorregião a partir do código IBGE."""
    return MESORREGIAO_NOMES.get(int(codigo), str(codigo))
