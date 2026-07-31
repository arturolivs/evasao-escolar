# Skill: Gerador de README Completo para Projetos de Software

## Descrição
Esta skill gera um `README.md` abrangente e profissional para qualquer projeto de software, com base na análise da estrutura do código, dependências, arquitetura e documentação existente (como `CLAUDE.md` ou arquivos de monografia).

Ela produz uma documentação completa, incluindo:
- **Visão geral e objetivos** do projeto.
- **Funcionalidades principais**.
- **Tecnologias e dependências** utilizadas.
- **Estrutura de diretórios** detalhada e comentada.
- **Arquitetura do software** (com diagramas em **Mermaid** representando camadas, componentes e fluxos de dados).
- **Instruções de instalação e configuração**.
- **Guia de uso** (execução do pipeline, inicialização de interfaces/painéis).
- **Como executar os testes**.
- **Estratégia de implantação** (deploy).
- **Diretrizes para contribuição**.
- **Licenciamento e créditos**.

---

## Instruções de Uso
1. **Ative a skill** digitando `/gerar-readme` no Claude Code (ou cole este arquivo como instrução).
2. A skill **analisará automaticamente** a estrutura do diretório atual, os arquivos de configuração (`pyproject.toml`, `requirements.txt`, `package.json`, `Dockerfile`, etc.), os pacotes-fonte (`src/`) e os testes (`tests/`).
3. Caso exista um `CLAUDE.md` ou um TCC/documento de especificação no repositório, a skill o lerá para extrair o contexto arquitetural e de negócio.
4. Ao final, ela **retornará o conteúdo completo** do `README.md`, pronto para ser copiado e colado na raiz do projeto.

---

## Etapas de Execução

### 1. Descoberta e Levantamento de Informações
- Liste a estrutura de diretórios (ex.: `src/`, `app/`, `tests/`, `notebooks/`, `docs/`).
- Identifique a linguagem principal (Python, JavaScript, etc.) e o framework (Streamlit, Django, React, etc.).
- Leia os arquivos de dependências:
  - `requirements.txt`, `pyproject.toml` (Python)
  - `package.json` (Node.js)
  - `Cargo.toml` (Rust), etc.
- Verifique se há um `Dockerfile` ou `docker-compose.yml`.
- Procure por `CLAUDE.md` ou arquivos de especificação para entender o domínio (ex.: evasão escolar, predição, etc.).

### 2. Análise da Arquitetura e Camadas
- Identifique as **camadas** do projeto. Exemplos comuns:
  - **Camada de Dados (Data Layer)**: Leitura, filtragem e armazenamento de dados brutos/intermediários.
  - **Camada de Características (Features Layer)**: Engenharia de atributos, preparação do conjunto final.
  - **Camada de Modelagem (Model Layer)**: Treino, ajuste, avaliação e serialização do modelo.
  - **Camada de Serviço/Recomendação (Service Layer)**: Lógica de negócio para gerar listas e explicações.
  - **Camada de Apresentação (Presentation Layer)**: Interface com o usuário (painel, API).
- Mapeie os fluxos de dados entre as camadas.
- **Gere diagramas Mermaid** automaticamente com base nessa análise:
  - **Diagrama de Camadas** (Stacked boxes).
  - **Diagrama de Componentes** (mostrando dependências e fluxo de arquivos).
  - **Diagrama de Atividades/Fluxo** (sequência de execução do pipeline).

### 3. Geração do Conteúdo do README
A skill montará o documento com as seguintes seções obrigatórias:

#### a. Cabeçalho e Badges
- Nome do projeto.
- Badges indicando versão, status dos testes, licença, cobertura (se aplicável).

#### b. Visão Geral / Introdução
- Descrição do problema resolvido.
- Público-alvo.
- Diferencial da solução.

#### c. Funcionalidades
- Lista objetiva do que o sistema faz (ex.: "Ordena escolas por risco", "Explica previsões via SHAP", "Painel interativo").

#### d. Tecnologias Utilizadas
- Tabela com tecnologia, versão e propósito.

#### e. Estrutura do Projeto (Árvore)
- Exibição da árvore de diretórios com breve descrição de cada pasta/arquivo principal.

#### f. Arquitetura (COM DIAGRAMAS!)
- Subseção **Visão Estrutural**: Diagrama de camadas (Mermaid `block-beta` ou `flowchart`).
- Subseção **Visão de Fluxo**: Diagrama mostrando como os dados se movem (entrada → processamento → saída).
- Subseção **Visão de Implantação**: Como o sistema é empacotado e executado (ex.: contêiner Docker).

#### g. Instalação e Configuração
- Pré-requisitos (Python 3.10+, etc.).
- Passos para clonar, criar ambiente virtual e instalar dependências.
- Configuração de variáveis de ambiente (se houver).

#### h. Como Usar / Execução
- Comando para rodar o pipeline completo (ex.: `python run_pipeline.py`).
- Comando para iniciar a interface/painel (ex.: `streamlit run app/app.py`).
- Exemplos de saída (resultados, listas geradas).

#### i. Testes
- Comando para executar a suíte de testes (ex.: `pytest tests/`).
- Breve explicação sobre a cobertura de testes.

#### j. Implantação / Deploy
- Instruções para containerização (Docker).
- Como rodar em produção (se aplicável).

#### k. Como Contribuir
- Diretrizes para submissão de PRs, padrões de código, convenções de commit.

#### l. Licença
- Tipo de licença (MIT, Apache, etc.) e copyright.

#### m. Agradecimentos / Referências
- Créditos a instituições, bases de dados (ex.: INEP), bibliotecas.

### 4. Revisão e Ajustes Finais
- A skill verificará se os diagramas gerados estão sintaticamente corretos (Mermaid).
- Garantirá que não haja placeholders genéricos sem explicação.
- Se o projeto for o "Sistema de Priorização de Escolas" (baseado no TCC anterior), ela preencherá automaticamente os detalhes específicos (ex.: 39 features, XGBoost, SHAP, etc.) a partir do contexto disponível.

---

## Exemplo de Saída (Estrutura do README)

```markdown
# Sistema de Priorização de Escolas em Risco de Evasão

![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![Tests](https://img.shields.io/badge/tests-120%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## Visão Geral
Este sistema identifica antecipadamente as escolas estaduais de Ensino Médio de Pernambuco com maior risco de abandono, utilizando dados públicos do INEP. Diferente de abordagens focadas na média, ele gera uma **lista priorizada** das escolas críticas, com explicações individuais baseadas em SHAP.

## Funcionalidades
- ✅ Leitura e padronização automática dos microdados do Censo Escolar.
- ✅ Engenharia de 39 características estatisticamente validadas.
- ✅ Modelo XGBoost com validação temporal e por município.
- ✅ Explicações globais e individuais via SHAP.
- ✅ Painel Streamlit para gestores (filtros, ranking, diagnóstico).

## Tecnologias
| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| Python     | 3.10   | Linguagem base |
| pandas     | 2.0+   | Manipulação de dados |
| scikit-learn | 1.3+ | Preparação e modelos baseline |
| XGBoost    | 1.7+   | Modelo principal |
| SHAP       | 0.42+  | Explicabilidade |
| Streamlit  | 1.28+  | Painel interativo |
| pytest     | 7.0+   | Testes automatizados |

## Estrutura do Projeto