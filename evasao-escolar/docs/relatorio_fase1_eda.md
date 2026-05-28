# Relatório de Análise Exploratória — Fase 1
## Predição de Evasão Escolar em Pernambuco

**Versão:** 1.0  
**Data:** 2026-05-27  
**Escopo:** ETL inicial + Análises descritivas do painel escola × ano (Censo 2022–2024)  
**Base de dados:** `data/interim/painel_escola_ano_pe_estadual_em.parquet`

---

## 1. O que foi feito até aqui

### 1.1 Pipeline ETL implementado

O ETL cobre exclusivamente os **Microdados do Censo Escolar** (INEP), nos anos 2022, 2023 e 2024. A cadeia de processamento é composta por quatro módulos:

| Módulo | Arquivo | Responsabilidade |
|--------|---------|-----------------|
| Configuração | `src/data/config.py` | Centraliza caminhos, constantes e filtros |
| Carga | `src/data/load.py` | Lê os CSVs do INEP com encoding latin-1, separador `;`, tipagem explícita |
| Filtragem | `src/data/filter_pe_estadual_em.py` | Aplica os 4 filtros do universo de análise |
| Painel | `src/data/build_school_panel.py` | Concatena os 3 anos e valida a chave primária |
| Target | `src/data/build_target.py` | Pronto para integrar as Taxas de Rendimento quando disponíveis |

**Filtros aplicados em sequência:**

1. `SG_UF == "PE"` — restringe a Pernambuco  
2. `TP_DEPENDENCIA == 2` — apenas rede estadual  
3. `TP_SITUACAO_FUNCIONAMENTO == 1` — apenas escolas em atividade  
4. `QT_MAT_MED > 0` — apenas escolas que ofertam Ensino Médio  

A aplicação sequencial dos filtros é registrada em um relatório de contagem (`RelatorioRecorte`) que documenta quantas escolas foram removidas em cada etapa — rastreabilidade essencial para a monografia.

### 1.2 Análises descritivas realizadas

Implementadas em `notebooks/02_analises_descritivas.py`, cobrindo 10 dimensões:

| Análise | Descrição |
|---------|-----------|
| A1 — Perfil do universo | N de escolas por ano, municípios, estabilidade longitudinal |
| A2 — Distribuição geográfica | Localização urbana/rural, mesorregiões, top municípios |
| A3 — Matrículas e porte | Distribuição, categorias de porte, razões operacionais |
| A4 — Infraestrutura | Prevalência de 13 itens, índice composto, comparação urbana/rural |
| A5 — Tecnologia e conectividade | Internet, banda larga, desktops e tablets por aluno |
| A6 — Tendências temporais | Evolução das variáveis operacionais entre 2022 e 2024 |
| A7 — Correlações | Matriz de Spearman entre features quantitativas |
| A8 — Tempo integral | Distribuição e expansão do ensino em tempo integral |
| A9 — Qualidade dos dados | Missing values, inconsistências, colunas problemáticas |
| A10 — Ranking de municípios | Municípios por matrículas, infraestrutura e perfil rural |

**Saídas geradas:** 10 figuras PNG em `reports/figuras/`.

---

## 2. Campos do painel: inventário e tratamentos

### 2.1 Campos de identificação — sem tratamento necessário

| Campo | Tipo | Missing | Observação |
|-------|------|---------|------------|
| `CO_ENTIDADE` | Int64 | 0 | Chave primária da escola — convertido de float para Int64 explicitamente |
| `NU_ANO_CENSO` | Int64 | 0 | Injetado manualmente quando ausente no CSV; usado para identificar o ano |
| `NO_ENTIDADE` | str | 0 | Nome da escola; usado apenas para exibição |

### 2.2 Campos geográficos — sem tratamento necessário

| Campo | Tipo | Missing | Observação |
|-------|------|---------|------------|
| `SG_UF` | str | 0 | Normalizado para maiúsculas no filtro (aceita "pe" e "PE") |
| `CO_UF` | Int64 | 0 | Fallback quando `SG_UF` ausente; código IBGE 26 = PE |
| `CO_MUNICIPIO` | Int64 | 0 | Convertido para Int64 para evitar casas decimais em joins futuros |
| `NO_MUNICIPIO` | str | 0 | Usado para rankear municípios |
| `CO_MESORREGIAO` | int64 | 0 | Codificado como int nativo; labels adicionados na análise |
| `CO_MICRORREGIAO` | int64 | 0 | Presente mas não usado nas análises atuais |

### 2.3 Campos de caracterização da escola — sem tratamento necessário

| Campo | Tipo | Missing | Observação |
|-------|------|---------|------------|
| `TP_DEPENDENCIA` | int64 | 0 | Filtro: apenas valor 2 (estadual) |
| `TP_LOCALIZACAO` | int64 | 0 | 1=Urbana, 2=Rural; usado extensivamente nas análises |
| `TP_LOCALIZACAO_DIFERENCIADA` | float64 | 0 | Indica localização em área indígena, quilombola, etc. |
| `TP_SITUACAO_FUNCIONAMENTO` | int64 | 0 | Filtro: apenas valor 1 (em atividade) |

### 2.4 Campos de infraestrutura (flags binárias 0/1)

Todos representam a **presença (1) ou ausência (0)** de determinado item. O INEP os publica como indicadores binários. Abaixo a tabela com a prevalência em 2024 e o comportamento por ano:

| Campo | Label | 2022 | 2023 | 2024 | Δ pp | Tratamento |
|-------|-------|------|------|------|------|------------|
| `IN_ENERGIA_REDE_PUBLICA` | Energia elétrica | 100% | 100% | 100% | 0,0 | **Constante** — ver seção 3.1 |
| `IN_AGUA_POTAVEL` | Água potável | 95,0% | 95,4% | 95,7% | +0,7 | Nenhum |
| `IN_ESGOTO_REDE_PUBLICA` | Esgoto rede pública | 60,0% | 60,2% | 60,4% | +0,4 | Nenhum |
| `IN_BIBLIOTECA` | Biblioteca | 89,9% | 91,5% | 92,7% | +2,8 | Nenhum |
| `IN_LABORATORIO_INFORMATICA` | Lab. Informática | 76,4% | 78,3% | 77,5% | +1,1 | Nenhum |
| `IN_LABORATORIO_CIENCIAS` | Lab. Ciências | 42,2% | 46,2% | 42,6% | +0,4 | Nenhum |
| `IN_QUADRA_ESPORTES` | Quadra de esportes | 68,4% | 73,3% | 78,4% | +10,0 | Nenhum |
| `IN_REFEITORIO` | Refeitório | 29,1% | 35,2% | 31,6% | +2,5 | Nenhum |
| `IN_SALA_LEITURA` | Sala de leitura | 14,6% | 16,0% | 13,1% | **−1,5** | Nenhum — ver seção 3.4 |
| `IN_AUDITORIO` | Auditório | 26,1% | 28,8% | 27,3% | +1,2 | Nenhum |
| `IN_INTERNET` | Internet | 99,1% | 99,4% | 99,1% | 0,0 | Nenhum |
| `IN_INTERNET_ALUNOS` | Internet p/ alunos | 70,8% | 76,5% | 77,6% | +6,8 | Nenhum |
| `IN_BANDA_LARGA` | Banda larga | 87,5% | 88,1% | 88,9% | +1,4 | **Missing 0,8%** — ver seção 3.2 |

**Enriquecimento derivado:** foi criado o `indice_infra` como média simples das 13 flags acima, gerando um índice contínuo [0, 1] que resume a dotação de infraestrutura de cada escola.

### 2.5 Campos quantitativos de matrículas e estrutura

| Campo | Label | Missing | Situação |
|-------|-------|---------|----------|
| `QT_MAT_MED` | Matrículas totais de EM | 0 | Base do filtro e da análise de porte |
| `QT_MAT_MED_INT` | Matrículas em tempo integral | 0 | Base do indicador derivado `pct_integral` |
| `QT_MAT_MED_NM` | Matrículas em normal/magistério | **33,4%** | **Depreciada** — ver seção 3.3 |
| `QT_TUR_MED` | Turmas de EM | 0 | Base do indicador `alunos_por_turma` |
| `QT_DOC_MED` | Docentes de EM | 0 | Base do indicador `alunos_por_docente` |
| `QT_SALAS_UTILIZADAS` | Salas em uso | 0 | Não usado nas análises atuais |
| `QT_DESKTOP_ALUNO` | Desktops disponíveis | 0 | Analisado como proxy de tecnologia |
| `QT_TABLET_ALUNO` | Tablets disponíveis | 0 | Analisado como proxy de tecnologia |

### 2.6 Campos derivados (enriquecimentos criados)

Quatro indicadores foram construídos durante as análises. Eles não estão no parquet interim mas são recriados no notebook e serão incorporados ao feature engineering:

| Indicador | Fórmula | Propósito |
|-----------|---------|-----------|
| `alunos_por_turma` | `QT_MAT_MED / QT_TUR_MED` | Proxy de superlotação; candidato a feature do modelo |
| `alunos_por_docente` | `QT_MAT_MED / QT_DOC_MED` | Proxy de carga do professor |
| `pct_integral` | `QT_MAT_MED_INT / QT_MAT_MED × 100` | Intensidade do programa integral |
| `indice_infra` | Média das 13 flags `IN_*` | Score agregado de infraestrutura |

---

## 3. Problemas encontrados

### 3.1 `IN_ENERGIA_REDE_PUBLICA` — coluna constante, sem variância

**O que é:** flag binária indicando se a escola possui energia elétrica fornecida pela rede pública.  
**Problema:** o valor é `1.0` para **100%** das escolas nos três anos (800 em 2022, 801 em 2023, 791 em 2024). Sem nenhuma variação, a variável é **informativamente inútil** para o modelo — uma variável constante não contribui para diferenciar escolas de risco alto versus baixo.  
**Decisão:** mantida no painel interim para integridade da carga, mas **será excluída do feature engineering**. O fato de toda escola estadual de EM em PE ter energia elétrica é, em si, um achado contextual relevante para a monografia (indica universalização deste insumo básico).

### 3.2 `IN_BANDA_LARGA` — missing em 0,8% do painel

**O que é:** flag indicando acesso à banda larga.  
**Problema:** 19 observações (0,8% do painel) com valor ausente. A distribuição por ano sugere que é um problema de não-resposta pontual na coleta, não uma mudança estrutural no Censo.  
**Decisão:** missing ignorado nas análises atuais. Para o modelo, será imputado pela **mediana da escola no ano com dado disponível** ou pelo valor modal da mesorregião no mesmo ano. Não representa risco significativo dado o volume.

### 3.3 `QT_MAT_MED_NM` — coluna quebrada no Censo 2022

**O que é:** quantidade de matrículas em cursos de magistério (Normal/Magistério) no Ensino Médio — modalidade residual que pouquíssimas escolas ainda ofertam.  
**Problema grave:** a coluna está com **100% de missing no ano 2022** (todos os 800 registros são NaN). Nos anos 2023 e 2024 os valores estão presentes, mas são quase todos zero (magistério está em extinção).

| Ano | Missing | Valor > 0 |
|-----|---------|-----------|
| 2022 | 800/800 (100%) | — |
| 2023 | 0/801 (0%) | ~5 escolas |
| 2024 | 0/791 (0%) | ~4 escolas |

**Causa provável:** o INEP parece ter mudado o nome ou a estrutura desta coluna entre 2022 e 2023. A leitura tolerante de colunas (`_carregar_com_colunas_tolerantes`) não encontrou correspondente no CSV de 2022 e preencheu com NaN.  
**Decisão:** **campo descartado** do projeto. Mesmo que o missing de 2022 fosse corrigido, o conteúdo é irrelevante para o modelo (quase nenhuma escola tem magistério e o campo não tem relação direta com evasão do EM regular).

### 3.4 `IN_SALA_LEITURA` — queda entre 2022 e 2024

**O que é:** flag indicando existência de sala de leitura.  
**Problema:** o índice caiu de 14,6% (2022) para 13,1% (2024) — movimento contrário à tendência de melhoria observada em todos os outros itens de infraestrutura. Isso pode indicar:  
- Mudança na definição ou critério de declaração do item no Censo;  
- Conversão de salas de leitura em outros espaços (refeitório, lab) em algumas escolas;  
- Variação aleatória dado o baixo valor base (~116 escolas).  
**Decisão:** campo mantido, mas sua interpretação exige cautela na monografia. Não foi descartado porque a variância entre escolas ainda pode ter poder explicativo.

### 3.5 `QT_COMPUTADOR_ALUNO` e `IN_EXAME_SELECAO_INGRESSO` — ausentes nos CSVs

**O que são:** `QT_COMPUTADOR_ALUNO` era a contagem geral de computadores; `IN_EXAME_SELECAO_INGRESSO` indica se a escola faz seleção de ingresso.  
**Problema:** ambas estavam na lista de colunas desejadas em `build_school_panel.py` (herdada do inventário de variáveis), mas **não existem nos CSVs do Censo 2022–2024**. A função `_carregar_com_colunas_tolerantes` descartou silenciosamente essas colunas com aviso de log.  
**Causa provável:** o INEP renomeou ou removeu essas variáveis entre edições do Censo. `QT_COMPUTADOR_ALUNO` provavelmente foi fragmentado em `QT_DESKTOP_ALUNO` e `QT_TABLET_ALUNO` (presentes). `IN_EXAME_SELECAO_INGRESSO` pode ter sido descontinuado.  
**Decisão:** `QT_COMPUTADOR_ALUNO` substituído pela soma de `QT_DESKTOP_ALUNO + QT_TABLET_ALUNO` no feature engineering futuro. `IN_EXAME_SELECAO_INGRESSO` descartado.

### 3.6 Outliers em `QT_MAT_MED`

**Problema:** 20 escolas (2,5% do painel de 2024) com matrículas acima do fence superior do IQR (872 alunos). A escola maior tem 1.435 matrículas — quase 4× a mediana. No extremo oposto, 70 escolas (8,8%) têm menos de 100 matrículas, sendo algumas com valores muito baixos (mínimo: 7 alunos em 2023).  
**Decisão:** **não serão removidos** — esses valores são reais (grandes centros urbanos têm escolas maiores; municípios pequenos têm escolas menores). O modelo deve aprender com esta variabilidade. Para o feature engineering, será avaliada a transformação logarítmica de `QT_MAT_MED` para reduzir a assimetria da distribuição.

### 3.7 Valores extremos em `alunos_por_turma`

**Problema:** 3 escolas com mais de 45 alunos por turma e 2 com menos de 5. Os valores extremamente baixos (< 5) sugerem turmas em fase de encerramento ou dados de declaração incorretos.  
**Decisão:** monitorar durante o feature engineering. O cap em [5, 50] será avaliado antes de entrar no modelo.

---

## 4. Análises descartadas ou limitadas

### 4.1 Análise por modalidade magistério (`QT_MAT_MED_NM`)

**Planejada:** comparar escolas com e sem oferta de magistério.  
**Por que foi descartada:** 100% de missing em 2022 inviabiliza qualquer análise longitudinal. Nos anos disponíveis, o N de escolas com magistério é irrisório (< 5).

### 4.2 Análise de variação intra-escola de infraestrutura

**Planejada:** verificar se a mesma escola melhora ou piora sua infraestrutura ao longo dos anos.  
**Limitação:** como o painel só cobre 3 anos e a maioria dos itens de infra são estáveis (escola raramente perde biblioteca de um ano para o outro), a variação intra-escola é mínima e estatisticamente pouco expressiva. Esta análise será relevante apenas quando o target (taxa de abandono) estiver disponível, para verificar se melhorias de infraestrutura precedem quedas na evasão.

### 4.3 Análise de `QT_SALAS_UTILIZADAS`

**Planejada:** relacionar número de salas com porte e índice de infraestrutura.  
**Decisão de adiamento:** a variável está presente e sem missing, mas sua interpretação requer cruzamento com o número de turmas para fazer sentido (salas/turma). Foi deixada para o feature engineering (Notebook 03) quando será criado o indicador de ocupação.

### 4.4 Análise de `CO_MICRORREGIAO`

**Planejada:** desagregação em nível de microrregião (granularidade maior que mesorregião).  
**Decisão de adiamento:** PE tem 19 microrregiões. Com ~800 escolas, a média é ~42 escolas por microrregião — granularidade viável. Porém, os dados de localidade do Censo não incluem os nomes das microrregiões diretamente, exigindo join com tabela auxiliar do IBGE. Adiado para o Notebook 03.

### 4.5 Análise de `TP_LOCALIZACAO_DIFERENCIADA`

**Planejada:** identificar escolas em territórios diferenciados (indígenas, quilombolas, assentamentos).  
**Decisão de adiamento:** a coluna está presente e sem missing. Porém, o N de escolas nesses territórios em PE é pequeno. A análise será integrada ao Notebook 03 em conjunto com os indicadores socioeconômicos (INSE), que ainda não foram baixados.

---

## 5. Resultados das análises descritivas

### 5.1 Perfil do universo (A1)

O painel contém **806 escolas únicas** distribuídas em 3 anos, totalizando **2.392 observações** (escola × ano). A estabilidade longitudinal é alta:

| Escolas que aparecem em | N | % |
|------------------------|---|---|
| 3 anos (2022, 2023 e 2024) | 785 | 97,4% |
| 2 anos | 16 | 2,0% |
| 1 ano | 5 | 0,6% |

As 15 escolas que saíram do painel entre 2022 e 2024 provavelmente foram extintas ou paralisadas ao longo do período. As 6 que entraram podem ter iniciado a oferta de EM ou terem sido estadualizadas. A alta estabilidade (97,4%) confirma que o painel é adequado para modelagem longitudinal.

**Movimento anual:**

| Transição | Saíram | Entraram |
|-----------|--------|----------|
| 2022 → 2023 | 3 | 4 |
| 2023 → 2024 | 12 | 2 |

A queda de 801 para 791 escolas em 2024 merece atenção — 12 escolas saíram em um único ano, valor maior que o histórico. Isso pode refletir extinções, reorganizações ou mudanças de dependência administrativa. Nenhuma hipótese foi confirmada ainda; será investigado ao integrar o target.

---

### 5.2 Distribuição geográfica (A2)

**Localização urbana/rural (2024):**

| Localização | N | % |
|-------------|---|---|
| Urbana | 680 | 86,0% |
| Rural | 111 | 14,0% |

O perfil é predominantemente urbano, consistente com a concentração da rede estadual nas sedes municipais.

**Escolas por mesorregião (2024):**

| Mesorregião | Código | N | Total Matrículas | Média |
|-------------|--------|---|-----------------|-------|
| Metropolitana de Recife | 2605 | 258 | 103.932 | 403 |
| Agreste Pernambucano | 2603 | 183 | 76.605 | 419 |
| Sertão Pernambucano | 2601 | 118 | 39.390 | 334 |
| Mata Pernambucana | 2604 | 116 | 43.364 | 374 |
| São Francisco Pernambucano | 2602 | 116 | 27.209 | 235 |

A mesorregião Metropolitana de Recife concentra **33% das escolas e 35% das matrículas**. A mesorregião do São Francisco se destaca pelo menor porte médio (235 matrículas/escola vs. 419 no Agreste), o que pode indicar maior vulnerabilidade a variações bruscas na evasão.

**Concentração municipal:** Recife sozinha tem 100 escolas e 40.407 matrículas — 13% de todo o universo. As 5 maiores cidades (Recife, Jaboatão, Petrolina, Caruaru, Olinda) respondem por 31% das escolas.

---

### 5.3 Matrículas e porte das escolas (A3)

**Estatísticas descritivas de `QT_MAT_MED` por ano:**

| Estatística | 2022 | 2023 | 2024 |
|-------------|------|------|------|
| Média | 373,3 | 365,5 | 367,3 |
| Mediana | 351,5 | 347,0 | 355,0 |
| Desvio-padrão | 211,8 | 209,6 | 210,2 |
| Mínimo | 10 | 7 | 7 |
| Máximo | 1.346 | 1.375 | 1.435 |

A distribuição é estável entre os anos — o teste Kruskal-Wallis não detectou diferença significativa entre os três anos (H=0,76, p=0,68). A assimetria positiva é marcante (média > mediana), puxada pelas escolas grandes de Recife e Jaboatão.

**Categorias de porte (2024):**

| Porte | Critério | N | % |
|-------|----------|---|---|
| Micro | < 100 alunos | 70 | 8,8% |
| Pequena | 100–249 | 173 | 21,9% |
| Média | 250–499 | 379 | 47,9% |
| Grande | 500–749 | 134 | 16,9% |
| Muito grande | 750+ | 35 | 4,4% |

Quase metade das escolas é de porte médio. As micros (8,8%) merecem monitoramento especial, pois a taxa de abandono em escolas muito pequenas pode ser extremamente volátil — a saída de poucos alunos muda drasticamente o indicador percentual.

**Razões operacionais (2024):**

| Indicador | Média | Mediana | Mín | Máx |
|-----------|-------|---------|-----|-----|
| Alunos por turma | 32,9 | 34,2 | 2,3 | 51,1 |
| Alunos por docente | 17,7 | 18,4 | 1,0 | 36,5 |

**Escolas rurais têm significativamente menos matrículas que urbanas** (teste Mann-Whitney: p < 0,0001). A diferença de porte entre os perfis é estrutural e consistente nos 3 anos.

---

### 5.4 Infraestrutura física e tecnológica (A4)

**Índice de infraestrutura (média das 13 flags IN_*):**

| Estatística | 2024 |
|-------------|------|
| Média | 0,680 |
| Mediana | 0,692 |
| Desvio-padrão | 0,154 |
| Mínimo | 0,167 |
| Máximo | 1,000 |

**Diferença urbana vs. rural é estatisticamente expressiva:**

| Grupo | N | Média | DP |
|-------|---|-------|-----|
| Urbana | 680 | 0,707 | 0,138 |
| Rural | 111 | 0,517 | 0,143 |
| Diferença | — | **−0,190** | — |

Teste t de Welch: t=13,09, p < 0,000001. A diferença de 19 pontos percentuais no índice entre escolas urbanas e rurais é uma das maiores disparidades observadas no painel. Isso sugere que a localização geográfica deve ser uma feature relevante no modelo preditivo.

**Por mesorregião (2024 — ranqueado do menor para o maior índice):**

| Mesorregião | Índice médio | DP |
|-------------|-------------|-----|
| São Francisco PE | 0,589 | 0,179 |
| Mata PE | 0,661 | 0,143 |
| Sertão PE | 0,689 | 0,133 |
| Agreste PE | 0,704 | 0,137 |
| Metropolitana de Recife | 0,709 | 0,150 |

A mesorregião do São Francisco apresenta o menor índice (0,589) e o maior desvio-padrão (0,179), indicando heterogeneidade interna elevada — convivem escolas com dotação muito baixa e algumas bem equipadas. Esta mesorregião também tem o menor porte médio das escolas, sugerindo acumulação de fatores de risco.

**Itens que mais cresceram entre 2022 e 2024:**
- Quadra de esportes: +10,0 pp (68,4% → 78,4%)
- Internet para alunos: +6,8 pp (70,8% → 77,6%)
- Biblioteca: +2,8 pp (89,9% → 92,7%)

**Item que regrediu:**
- Sala de leitura: −1,5 pp (14,6% → 13,1%) — provável mudança de critério de declaração, não desaparecimento físico (ver seção 3.4).

---

### 5.5 Tecnologia e conectividade (A5)

| Indicador | 2022 | 2023 | 2024 |
|-----------|------|------|------|
| Internet (qualquer) | 99,1% | 99,4% | 99,1% |
| Internet para alunos | 70,8% | 76,5% | 77,6% |
| Banda larga | 87,5% | 88,1% | 88,9% |

A cobertura de internet é praticamente universal. No entanto, há uma diferença importante: enquanto 99% das escolas têm internet, apenas 78% a disponibilizam para os alunos. Esta diferença é ainda mais acentuada no rural (65,8%) vs. urbano (79,6%).

**Desktops (2024):** média de 12 desktops por escola; 22,3% das escolas não possuem nenhum. **Tablets:** distribuição muito assimétrica — mediana = 0, indicando que a maioria das escolas não possui tablets, com alguns outliers que receberam doações ou programas governamentais.

---

### 5.6 Tendências temporais 2022–2024 (A6)

| Indicador | 2022 | 2023 | 2024 | Variação % |
|-----------|------|------|------|------------|
| Matrículas médias (QT_MAT_MED) | 373,3 | 365,5 | 367,3 | −1,6% |
| Turmas médias (QT_TUR_MED) | 10,78 | 10,67 | 10,72 | −0,6% |
| Docentes médios (QT_DOC_MED) | 19,34 | 19,40 | 19,67 | +1,7% |
| Alunos por turma | 33,28 | 32,79 | 32,85 | −1,3% |
| Alunos por docente | 18,49 | 17,89 | 17,70 | **−4,3%** |
| % Integral (média) | 56,7% | 61,6% | 64,9% | **+14,6%** |

**Achados principais:**
- As matrículas totais estabilizaram (queda não-significativa de −1,6%). Isso é esperado em um estado sem forte crescimento demográfico no segmento de EM.
- O número de docentes cresceu enquanto as matrículas caíram levemente — a relação alunos/docente melhorou 4,3%, o que pode indicar uma política de reforço do quadro.
- O crescimento do tempo integral é a tendência mais marcante: +14,6% em 3 anos, refletindo a expansão nacional do programa.

---

### 5.7 Correlações entre features (A7)

Matriz de correlação de Spearman (2024) — principais relações:

| Par | r de Spearman | Significância |
|-----|--------------|---------------|
| QT_MAT_MED × QT_TUR_MED | +0,957 | *** |
| QT_MAT_MED × QT_DOC_MED | +0,861 | *** |
| alunos_por_turma × QT_MAT_MED | +0,661 | *** |
| % Integral × índice_infra | **+0,441** | *** |
| Localização × índice_infra | **−0,407** | *** |
| QT_MAT_MED × índice_infra | +0,307 | *** |

**Interpretações:**

1. **Matrículas × Turmas × Docentes** — as três variáveis medem basicamente o mesmo conceito (tamanho da escola). No modelo, usar as três seria introduzir multicolinearidade. Apenas uma deve entrar como feature (recomendado: `QT_MAT_MED` como medida de porte).

2. **% Integral × Infraestrutura (r=+0,44)** — escolas de tempo integral tendem a ter melhor infraestrutura. Isso pode refletir uma seleção: o programa integral tende a ser implementado primeiro nas escolas com melhor dotação física. Importante considerar possível confundimento ao usar ambas as features no modelo.

3. **Localização × Infraestrutura (r=−0,41)** — confirmação estatística do que já foi observado: escolas rurais (código 2) têm menor índice de infraestrutura. A correlação negativa é esperada (código 2 = rural = menor infra).

4. **Ausência de multicolinearidade extrema** entre infraestrutura e variáveis de tamanho (r ≈ 0,31) indica que porte e qualidade de infraestrutura são dimensões distintas — ambas podem entrar no modelo sem redundância.

---

### 5.8 Tempo integral (A8)

O programa de educação em tempo integral é uma das mais marcantes transformações do ensino médio em PE nos últimos anos. Os dados revelam:

**Classificação das escolas em 2024:**

| Categoria | N | % |
|-----------|---|---|
| 100% integral (todas as matrículas) | 395 | 49,9% |
| Híbrida (parte integral, parte regular) | 265 | 33,5% |
| 0% integral (apenas turmas regulares) | 131 | 16,6% |

**Em 2024, metade das escolas estaduais de EM em PE são 100% integrais.** Este é um dado extraordinário que tem implicações diretas para o modelo preditivo: a modalidade integral pode ser um fator de proteção contra evasão (alunos com mais atividades na escola tendem a ter menor abandono). Ou, ao contrário, pode ser um fator de risco para determinados perfis de alunos que precisam trabalhar.

**Por localização (2024):**

| Localização | % Integral médio | Mediana |
|-------------|-----------------|---------|
| Urbana | 71,4% | 100% |
| Rural | 25,1% | 0% |

A diferença é drástica: na zona rural, a mediana é 0% — a maioria das escolas rurais não tem nenhuma matrícula integral. O programa integral é, até agora, predominantemente urbano.

---

### 5.9 Qualidade dos dados (A9)

De 34 colunas no painel, apenas 2 apresentam missing:

| Coluna | Missing | Impacto |
|--------|---------|---------|
| `QT_MAT_MED_NM` | 33,4% (todo o ano 2022) | Descartada do projeto |
| `IN_BANDA_LARGA` | 0,8% (19 obs.) | Imputação simples resolve |

**O painel é de alta qualidade para as variáveis do Censo.** A ausência de missing nas features principais (infraestrutura, matrículas, localização) é um ponto favorável para o modelo.

---

### 5.10 Ranking de municípios (A10)

**Municípios com menor infraestrutura média (mín. 3 escolas, 2024):**

| Município | N escolas | Índice infra | % Rural |
|-----------|----------|-------------|---------|
| Carnaubeira da Penha | 11 | 0,442 | 90,9% |
| Floresta | 10 | 0,471 | 60,0% |
| Jatobá | 5 | 0,508 | 60,0% |
| Tacaratu | 8 | 0,510 | 75,0% |

Esses municípios concentram características de vulnerabilidade: alta taxa de escolas rurais, baixo índice de infraestrutura, e localização no interior (São Francisco e Sertão). São candidatos a aparecer no topo do ranking de risco de evasão quando o target for integrado.

**Municípios com maior infraestrutura média (mín. 3 escolas, 2024):**

| Município | N escolas | Índice infra | % Rural |
|-----------|----------|-------------|---------|
| Surubim | 4 | 0,827 | 0% |
| São Bento do Una | 4 | 0,827 | 0% |
| Recife | 100 | 0,791 | 0% |
| Caruaru | 21 | 0,773 | 0% |

---

## 6. Limitações das análises atuais

1. **Ausência do target** — todas as análises são descritivas das features. Não é possível ainda afirmar qual feature se correlaciona com evasão, apenas caracterizar o perfil das escolas.

2. **Sem indicadores externos** — INSE, Distorção Idade-Série, Adequação Docente e Regularidade do Corpo Docente (fontes marcadas como "A baixar" no `decisoes_projeto.md`) não foram incorporados. Estes indicadores têm potencial preditivo alto e sua ausência limita a análise exploratória.

3. **Painel curto** — 3 anos é suficiente para o modelo, mas insuficiente para análises de tendência de longo prazo (ex.: impacto da pandemia de 2020 na composição atual das escolas).

4. **Infraestrutura como proxy** — sem o target, o índice de infraestrutura é usado como proxy de qualidade. Com o target disponível, será possível verificar se escolas com menor infraestrutura têm de fato mais evasão — hipótese plausível mas não confirmada.

---

## 7. Próximos passos

| Prioridade | Ação | Arquivo |
|-----------|------|---------|
| **CRÍTICA** | Baixar Taxas de Rendimento Escolar (target) | `data/raw/taxas_rendimento/` |
| ALTA | Baixar INSE, Distorção, Adequação e Regularidade | `data/raw/outros_indicadores/` |
| ALTA | Executar `build_target.py` para construir `taxa_abandono_t1` | Notebook 02b |
| MÉDIA | Feature engineering: criar `indice_infra`, `alunos_por_turma`, lags | Notebook 03 |
| MÉDIA | Excluir `IN_ENERGIA_REDE_PUBLICA` (constante) do pipeline | `feature_engineer.py` |
| MÉDIA | Planejar imputação de `IN_BANDA_LARGA` (0,8% missing) | `feature_engineer.py` |
| BAIXA | Join com tabela de microrregiões IBGE para labels | Notebook 03 |
| BAIXA | Avaliar transformação log de `QT_MAT_MED` | Notebook 03 |

---

*Documento gerado com base nas análises do painel `painel_escola_ano_pe_estadual_em.parquet` (2.392 linhas, 34 colunas), usando os notebooks `01_exploracao_inicial.py` e `02_analises_descritivas.py`.*
