"""
Configurações centrais do projeto TCC — Predição de Evasão Escolar.

Princípio: nenhuma constante (caminho, código, filtro) deve ficar hardcoded
no código de ETL ou modelagem. Tudo passa por aqui.

Edite este arquivo para apontar para a sua estrutura local de dados.
"""

from pathlib import Path

# =============================================================================
# CAMINHOS
# =============================================================================

# Raiz do projeto = pasta pai de src/
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT_DIR / "models"

# Todos os anos do Censo ficam na mesma pasta data/raw/censo/
# Arquivos nomeados como "microdados_ed_basica_<ano>.csv"
CENSO_DIR = RAW_DIR / "censo"
CENSO_DIRS = {ano: CENSO_DIR for ano in [2022, 2023, 2024]}

# Nome do arquivo da tabela ESCOLA dentro de cada pasta de ano.
# Conforme o INEP, costuma ser "microdados_ed_basica_<ano>.csv".
# Se na sua pasta estiver com outro nome, ajuste aqui ou em load.py.
CENSO_ESCOLA_FILENAME_TEMPLATE = "microdados_ed_basica_{ano}.csv"

# =============================================================================
# PARÂMETROS DE LEITURA DOS CSVs DO INEP
# =============================================================================

# Padrão histórico dos microdados do INEP
CSV_ENCODING = "latin-1"
CSV_SEPARATOR = ";"

# Anos cobertos pelo projeto
ANOS_DISPONIVEIS = [2022, 2023, 2024]

# =============================================================================
# FILTROS PARA RECORTE DO UNIVERSO
# =============================================================================

# UF alvo: Pernambuco. Pode ser tanto via SG_UF ou CO_UF.
UF_ALVO_SIGLA = "PE"
UF_ALVO_CODIGO = 26  # Código IBGE de Pernambuco

# Dependência administrativa (TP_DEPENDENCIA do Censo):
#   1 = Federal
#   2 = Estadual
#   3 = Municipal
#   4 = Privada
DEPENDENCIA_ESTADUAL = 2

# Situação de funcionamento (TP_SITUACAO_FUNCIONAMENTO):
#   1 = Em atividade
#   2 = Paralisada
#   3 = Extinta no ano em curso
#   4 = Extinta em anos anteriores
SITUACAO_EM_ATIVIDADE = 1

# =============================================================================
# COLUNAS-CHAVE PARA ETL DE ESCOLA EM PE / REDE ESTADUAL / EM
# =============================================================================

# Colunas mínimas obrigatórias para o filtro inicial.
# As demais virão na fase de feature engineering.
COLUNAS_CHAVE_ESCOLA = [
    "NU_ANO_CENSO",
    "CO_ENTIDADE",
    "NO_ENTIDADE",
    "SG_UF",
    "CO_UF",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "TP_DEPENDENCIA",
    "TP_LOCALIZACAO",
    "TP_SITUACAO_FUNCIONAMENTO",
]

# Colunas que indicam que a escola OFERECE Ensino Médio Regular.
# IMPORTANTE: o Censo tem múltiplas variáveis que indicam etapas ofertadas.
# Pra EM regular, as principais (a confirmar com dicionário do ano específico):
#   IN_REGULAR — flag se oferece ensino regular
#   QT_MAT_MED — qtd. de matrículas de EM
#   QT_MAT_MED_NM — qtd. de matrículas de EM "normal/magistério"
# Estratégia adotada: escola oferece EM se QT_MAT_MED > 0
COL_QTD_MATRICULA_EM = "QT_MAT_MED"

# =============================================================================
# CAMINHOS DOS INDICADORES COMPLEMENTARES
# =============================================================================

IRD_DIR  = RAW_DIR / "indicador_regularidade_docente"
INSE_DIR = RAW_DIR / "inse"
TDI_DIR  = RAW_DIR / "taxa_distorcao_idade"
AFD_DIR  = RAW_DIR / "adequacao_formacao_docente"

# =============================================================================
# LOGGING
# =============================================================================

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
