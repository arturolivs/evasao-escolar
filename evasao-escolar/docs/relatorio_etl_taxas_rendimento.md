# Relatório de ETL — Taxas de Rendimento Escolar
## Predição de Evasão Escolar em Pernambuco

**Versão:** 1.0  
**Data:** 2026-05-28  
**Escopo:** ETL das Taxas de Rendimento Escolar (INEP) — filtro PE/Estadual/EM, limpeza, normalização e geração do painel interim  
**Base de dados bruta:** `data/raw/taxas_rendimento/tx_rend_escolas_{2022,2023,2024}.xlsx`  
**Saída gerada:** `data/interim/taxas_rendimento_pe_estadual_em.parquet`

---

## 1. Contexto e motivação

As **Taxas de Rendimento Escolar** publicadas anualmente pelo INEP são a principal fonte para a construção do **target do projeto**: a taxa de abandono do Ensino Médio (`TAXA_ABND_MED`). A lógica temporal do modelo exige que, para cada escola no ano *t*, o alvo seja a taxa de abandono observada no ano *t+1* — o que torna esses dados insubstituíveis, não apenas como target mas também como fonte de features históricas (taxa de abandono no ano anterior é, intuitivamente, um dos preditores mais fortes).

Além do abandono, os arquivos contêm as taxas de **aprovação** e **reprovação** por série, que serão aproveitadas como features no Notebook 03 (feature engineering). O ETL descrito neste documento trata, filtra e normaliza essas informações, preparando-as para o join com o painel do Censo Escolar.

---

## 2. O que foi implementado

### 2.1 Módulos criados ou alterados

| Módulo | Ação | Responsabilidade |
|--------|------|-----------------|
| `src/data/build_taxas_rendimento.py` | **Criado** | ETL completo das taxas de rendimento: carga, filtro, normalização, validação e persistência |
| `src/data/build_target.py` | **Reescrito** | Simplificado para usar `build_taxas_rendimento` como dependência; lógica de join Censo ↔ taxas para construção do target *t+1* |

### 2.2 Pipeline de ETL implementado

O módulo `build_taxas_rendimento.py` executa as seguintes etapas em sequência, por ano, antes de concatenar o painel:

```
xlsx bruto (INEP)
   │
   ├── [1] Leitura com header=8 (pula 8 linhas de cabeçalho institucional)
   ├── [2] Filtro: SG_UF == 'PE' AND NO_DEPENDENCIA == 'Estadual'
   ├── [3] Seleção das colunas relevantes (ID + 18 colunas de taxa EM)
   ├── [4] Substituição de '--' por NaN e conversão para float
   ├── [5] Remoção de escolas sem oferta/dados de EM (TAXA_ABND_MED nulo)
   ├── [6] Cast de CO_ENTIDADE e CO_MUNICIPIO para Int64
   ├── [7] Validação de consistência (Aprovação + Reprovação + Abandono ≈ 100%)
   └── [8] Adição da coluna NU_ANO_CENSO
        │
        ↓ (concatenação dos 3 anos)
   [9] Ordenação por CO_ENTIDADE, NU_ANO_CENSO
  [10] Reordenação de colunas: identificadores primeiro, depois taxas
  [11] Salvamento em data/interim/taxas_rendimento_pe_estadual_em.parquet
```

### 2.3 Convenção de nomes adotada

O INEP publica as colunas de taxa com uma nomenclatura técnica pouco legível (ex.: `3_CAT_MED_01`). Todas foram renomeadas para nomes autoexplicativos seguindo o padrão `TAXA_{TIPO}_MED_{SERIE}`:

| Coluna INEP | Nome padronizado | Significado |
|-------------|-----------------|-------------|
| `1_CAT_MED` | `TAXA_APROV_MED` | Taxa de Aprovação — EM Total |
| `1_CAT_MED_01` | `TAXA_APROV_MED_S1` | Taxa de Aprovação — 1ª Série |
| `1_CAT_MED_02` | `TAXA_APROV_MED_S2` | Taxa de Aprovação — 2ª Série |
| `1_CAT_MED_03` | `TAXA_APROV_MED_S3` | Taxa de Aprovação — 3ª Série |
| `1_CAT_MED_04` | `TAXA_APROV_MED_S4` | Taxa de Aprovação — 4ª Série |
| `1_CAT_MED_NS` | `TAXA_APROV_MED_NS` | Taxa de Aprovação — EM Não Seriado |
| `2_CAT_MED` | `TAXA_REPROV_MED` | Taxa de Reprovação — EM Total |
| `2_CAT_MED_01` | `TAXA_REPROV_MED_S1` | Taxa de Reprovação — 1ª Série |
| … | … | … (mesmo padrão) |
| `3_CAT_MED` | `TAXA_ABND_MED` | Taxa de Abandono — EM Total **(target)** |
| `3_CAT_MED_01` | `TAXA_ABND_MED_S1` | Taxa de Abandono — 1ª Série |
| `3_CAT_MED_02` | `TAXA_ABND_MED_S2` | Taxa de Abandono — 2ª Série |
| `3_CAT_MED_03` | `TAXA_ABND_MED_S3` | Taxa de Abandono — 3ª Série |
| `3_CAT_MED_04` | `TAXA_ABND_MED_S4` | Taxa de Abandono — 4ª Série |
| `3_CAT_MED_NS` | `TAXA_ABND_MED_NS` | Taxa de Abandono — EM Não Seriado |

Os prefixos numéricos `1_CAT`, `2_CAT` e `3_CAT` identificam, respectivamente, as categorias **Aprovação**, **Reprovação** e **Abandono** conforme a codificação interna do INEP.

---

## 3. Problemas encontrados

### 3.1 Formato xlsx do INEP: 8 linhas de cabeçalho institucional

**O que é:** Os arquivos publicados pelo INEP não começam diretamente com os dados. As primeiras 8 linhas contêm cabeçalhos institucionais (logomarca do Ministério da Educação, nome do INEP, título do relatório, descrição das colunas em formato multi-nível) antes que a linha de cabeçalho real apareça.

**Evidência observada:**

```
Linha 0: "Ministério da Educação"
Linha 1: "Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira"
Linha 2: (vazia)
Linha 3: "Taxas de Rendimento Escolar por escola - 2022"
Linha 4: (descrição longa das colunas)
Linha 5: (nomes das etapas: Fundamental, Médio)
Linha 6: (nomes das séries: 1º Ano, 2º Ano…)
Linha 7: (nomes das sub-colunas: Total, Anos Iniciais…)
Linha 8: NU_ANO_CENSO | NO_REGIAO | SG_UF | ...  ← header real
Linha 9: 2022 | Norte | RO | ...                  ← primeiro dado
```

**Problema:** Ao usar `pd.read_excel()` sem especificar o `header`, o pandas interpreta a linha 0 ("Ministério da Educação") como cabeçalho, gerando colunas `Unnamed: 0`, `Unnamed: 2`, etc., e descarta os nomes reais. Além disso, lê as 8 linhas de cabeçalho como dados, resultando em um DataFrame de 129.317 linhas com os 8 primeiros registros sendo lixo.

**Solução adotada:** `pd.read_excel(path, header=8)` — o argumento `header=8` instrui o pandas a tratar a linha 8 (0-indexed) como a linha de cabeçalho e ignorar tudo acima. O arquivo passa de 129.317 para 129.309 registros reais.

**Justificativa:** A verificação manual das primeiras linhas (leitura sem header) foi essencial para identificar a linha correta. O valor `header=8` foi fixado como constante nomeada `_HEADER_ROW = 8` no código, com comentário explicativo, dado que pode mudar em versões futuras dos arquivos INEP.

---

### 3.2 Sentinela '--' para "escola não oferta esta série"

**O que é:** O INEP usa o valor string `'--'` (dois hifens) para indicar que a escola não oferta determinada série ou etapa — por exemplo, uma escola que tem apenas 1ª, 2ª e 3ª séries do EM terá `'--'` em todas as colunas da 4ª série. Isso é distinto de um dado ausente por falha de coleta.

**Problema:** Como o INEP mistura strings (`'--'`) e números (`100`, `0`, `85.5`) na mesma coluna, o pandas lê todas essas colunas como `object` (string). Qualquer operação aritmética direta retornaria erro.

**Solução adotada:**
```python
df[col] = pd.to_numeric(df[col].replace("--", pd.NA), errors="coerce")
```
O `replace("--", pd.NA)` converte o sentinela para `pandas.NA` antes da conversão numérica. O `errors="coerce"` garante que qualquer valor inesperado (eventual lixo textual) também vire NaN em vez de gerar exceção.

**Justificativa:** Manter `--` como NaN é semanticamente correto: a escola não tem 4ª série, portanto não há taxa a reportar — não é um dado faltante, é ausência da unidade de observação. O modelo de machine learning deve tratar esses NaNs adequadamente (ignorar na agregação ou imputar zero, dependendo do contexto).

---

### 3.3 CO_ENTIDADE lido como float pelo Excel

**O que é:** A coluna `CO_ENTIDADE` (código da escola — chave primária do INEP) é um inteiro de 8 dígitos (ex.: `26036731`). No Excel, é armazenada como número.

**Problema:** Por causa das linhas de cabeçalho mistas no início do arquivo, o motor do Excel (openpyxl) infere o tipo da coluna como `float64`, resultando em valores como `26036731.0`. Se exportado diretamente para parquet ou usado em um join, o `.0` seria preservado, causando falhas silenciosas ao cruzar com o `CO_ENTIDADE` do Censo (que é inteiro).

**Solução adotada:**
```python
df["CO_ENTIDADE"] = pd.to_numeric(df["CO_ENTIDADE"], errors="coerce").astype("Int64")
```
O cast explícito para `Int64` (inteiro nullable do pandas) remove as casas decimais e preserva compatibilidade com valores ausentes sem truncar para `int32`.

**Justificativa:** O mesmo tratamento já foi aplicado ao `CO_ENTIDADE` no módulo do Censo (`build_school_panel.py`). Manter consistência de tipo nas chaves de join é crítico para evitar bugs silenciosos onde `26036731 != 26036731.0` dependendo do motor de comparação.

---

### 3.4 `TAXA_*_MED_S4` — 98,3% nulos (4ª série do EM)

**O que é:** As colunas `_S4` referem-se à 4ª série do Ensino Médio, que existe apenas em cursos **técnicos integrados** de 4 anos — uma modalidade rara na rede estadual.

**Evidência:**

| Coluna | % Nulos |
|--------|---------|
| `TAXA_ABND_MED_S4` | 98,3% |
| `TAXA_REPROV_MED_S4` | 98,3% |
| `TAXA_APROV_MED_S4` | 98,3% |

Dos 2.392 registros do painel, apenas ~41 têm valor preenchido nessas colunas — aproximadamente 14 escolas em cada ano.

**Problema:** Colunas com 98% de missing têm altíssimo risco de introduzir ruído no modelo. Se usadas como features, a maioria dos registros seria imputada, inflando artificialmente a correlação com o target.

**Decisão:** As colunas `_S4` foram **mantidas no parquet interim** para rastreabilidade e eventual uso futuro (ex.: análise separada de cursos técnicos), mas **serão excluídas do pipeline de features** no Notebook 03. A justificativa para não descartar agora é preservar a capacidade de análise futura sem necessidade de re-rodar o ETL.

---

### 3.5 `TAXA_*_MED_NS` — 87,4% nulos (EM Não Seriado)

**O que é:** O sufixo `_NS` refere-se ao **Ensino Médio Não Seriado** — uma modalidade alternativa voltada principalmente à Educação de Jovens e Adultos (EJA) integrada ao EM regular ou cursos supletivos.

**Evidência:**

| Coluna | % Nulos |
|--------|---------|
| `TAXA_ABND_MED_NS` | 87,4% |

Aproximadamente 301 linhas do painel (12,6%) têm valor preenchido — cerca de 100 escolas por ano ofertam alguma modalidade não seriada.

**Decisão:** Mesmo critério das colunas `_S4`: mantidas no parquet, excluídas do pipeline de features. O índice de 87% de missing torna qualquer análise com essas colunas estatisticamente limitada e suscetível a viés de seleção (as escolas que ofertam EM não seriado tendem a ter perfil muito diferente do universo).

---

### 3.6 `build_target.py` com lógica placeholder incompatível

**O que era:** O `build_target.py` original foi escrito antes dos arquivos de taxas de rendimento estarem disponíveis. Ele continha lógica heurística para tentar detectar automaticamente os nomes das colunas via string matching (ex.: procurava por `"abandon"` no nome da coluna), e esperava o caminho `TX_REND_<ano>.xlsx` com uma aba específica de Ensino Médio.

**Problemas identificados:**
1. Os arquivos reais se chamam `tx_rend_escolas_{ano}.xlsx` (formato diferente do esperado)
2. Não existe separação por aba — um único arquivo contém todas as etapas (Fundamental e Médio) em colunas separadas
3. O header real está na linha 8, não na linha 0 que o código tentava parsear
4. Os nomes reais das colunas (`3_CAT_MED`, `1_CAT_MED`, etc.) não contêm as palavras-chave buscadas pelo heurístico ("abandono", "médio")
5. O filtro por UF e dependência usava `CO_UF` (código numérico) e `TP_DEPENDENCIA` (código numérico) — colunas do Censo que não existem no arquivo de taxas, que usa `SG_UF` (string) e `NO_DEPENDENCIA` (string)

**Solução adotada:** O `build_target.py` foi completamente reescrito. Toda a lógica de carga e normalização foi movida para `build_taxas_rendimento.py`, e o `build_target.py` passou a ser apenas a camada de join: importa o painel de taxas já limpo e realiza o merge com o painel do Censo usando `CO_ENTIDADE` e `NU_ANO_CENSO`.

**Justificativa:** A separação de responsabilidades torna o código mais testável e reutilizável. O módulo `build_taxas_rendimento.py` pode ser executado independentemente para inspecionar os dados brutos; o `build_target.py` depende do painel já normalizado e não precisa conhecer os detalhes do formato INEP.

---

### 3.7 Dependência `openpyxl` ausente no ambiente virtual

**O que é:** A leitura de arquivos `.xlsx` pelo pandas requer a biblioteca `openpyxl` como engine. O ambiente virtual do projeto (`.venv/`) não a tinha instalada.

**Erro observado:**
```
ImportError: `Import openpyxl` failed. Use pip or conda to install the openpyxl package.
```

**Solução:** Instalação via `pip install openpyxl`. A dependência deve ser adicionada ao `requirements.txt` (ou `pyproject.toml`) do projeto para evitar que outros executores encontrem o mesmo erro.

---

## 4. Validações realizadas

### 4.1 Consistência matemática das taxas

A soma das três taxas totais (Aprovação + Reprovação + Abandono) deve ser exatamente 100% para cada escola, uma vez que o INEP garante que todos os alunos matriculados são contabilizados em exatamente uma das três categorias ao final do ano letivo.

**Resultado da validação:**

| Métrica | Valor |
|---------|-------|
| Registros testados | 2.392 |
| Soma mínima | 100,0% |
| Soma máxima | 100,0% |
| Registros fora de [99, 101] | **0 (0,0%)** |

O painel não apresenta nenhuma inconsistência — o INEP já arredonda as três taxas de forma que a soma seja exatamente 100. Esta validação confirma que a substituição de `'--'` por NaN e a conversão numérica foram aplicadas corretamente.

### 4.2 Estabilidade longitudinal do painel

A mesma análise de estabilidade do painel do Censo foi aplicada às taxas de rendimento para verificar consistência entre as fontes:

| Escolas que aparecem em | N | % |
|------------------------|---|---|
| 3 anos (2022, 2023, 2024) | 785 | 97,4% |
| 2 anos | 16 | 2,0% |
| 1 ano | 5 | 0,6% |

**O resultado é idêntico ao painel do Censo** — 97,4% de estabilidade em ambas as fontes. Isso confirma que as duas fontes de dados descrevem o mesmo universo de escolas e que o join entre elas (via `CO_ENTIDADE`) terá altíssima cobertura.

### 4.3 Rastreabilidade do filtro por etapa

O filtro principal que define "escola com Ensino Médio" nas taxas de rendimento foi aplicado via `TAXA_ABND_MED.notna()`. A quantidade de escolas removidas em cada ano foi registrada em log:

| Ano | PE + Estadual | Sem dados EM (removidas) | Com EM |
|-----|:-------------:|:------------------------:|:------:|
| 2022 | 1.025 | 225 | **800** |
| 2023 | 1.026 | 225 | **801** |
| 2024 | 1.028 | 237 | **791** |

As 225–237 escolas removidas por ano são escolas estaduais de PE que têm dados no arquivo do INEP (ofertam Fundamental ou outra etapa) mas não têm Ensino Médio — o que é esperado, pois o filtro do Censo (`QT_MAT_MED > 0`) seleciona apenas as que têm EM, e o arquivo de taxas cobre todas as etapas.

---

## 5. Resultados e análise descritiva das taxas

### 5.1 Taxa de Abandono do Ensino Médio (`TAXA_ABND_MED`)

Esta é a variável mais importante do projeto — será o **target** do modelo preditivo. Sua distribuição revela características que impactam diretamente as decisões de modelagem:

**Estatísticas descritivas por ano:**

| Estatística | 2022 | 2023 | 2024 |
|-------------|------|------|------|
| N | 800 | 801 | 791 |
| Média | 2,05% | 1,37% | 0,96% |
| Desvio-padrão | 5,27 | 4,20 | 2,97 |
| Mínimo | 0,0% | 0,0% | 0,0% |
| Mediana (p50) | 0,0% | 0,0% | 0,0% |
| p75 | 1,12% | 0,50% | 0,45% |
| p90 | 7,0%* | 4,3%* | 3,7%* |
| p95 | — | — | 8,39% |
| Máximo | 43,6% | 39,5% | 38,9% |

*estimado a partir das estatísticas disponíveis

**Achados críticos:**

1. **Distribuição fortemente assimétrica à direita:** A mediana é 0,0% nos três anos — mais da metade das escolas estaduais de PE reporta zero abandono no EM. A média (1,37–2,05%) é puxada por uma minoria de escolas com abandono alto. O p95 já está em 8,39%, e o máximo chega a 43,6%.

2. **Escola com abandono zero é a norma, não a exceção:**

| Ano | Escolas com TAXA_ABND_MED = 0 | % do total |
|-----|:-----------------------------:|:----------:|
| 2022 | 501 | 62,6% |
| 2023 | 550 | 68,7% |
| 2024 | 531 | 67,1% |

3. **Tendência de queda expressiva:** A taxa média de abandono caiu de 2,05% em 2022 para 0,96% em 2024 — uma redução de 53% em dois anos. O número de escolas com abandono acima de 10% caiu de 51 (2022) para apenas 14 (2024). Este é um dos achados mais relevantes para a contextualização na monografia.

   **Possíveis explicações para a queda:**
   - Expansão do programa de Ensino em Tempo Integral em PE (de 56,7% para 64,9% das escolas entre 2022 e 2024 — ver Relatório Fase 1), que mantém os alunos por mais tempo na escola e reduz a oportunidade de abandono;
   - Recuperação pós-pandemia: escolas e alunos estabilizando a rotina após os anos de 2020–2021;
   - Mudanças nos critérios de classificação do INEP para "abandono" versus "transferência".

4. **Implicação para modelagem:** A distribuição com mediana zero é típica de variáveis de contagem/proporção com excesso de zeros (*zero-inflated*). Estratégias a avaliar no Notebook 04:
   - Transformação Box-Cox ou log(x + ε) para compressão da cauda;
   - Modelagem em dois estágios: primeiro classificar escolas como "zero abandono" vs. "com algum abandono", depois regredir apenas nas que têm abandono;
   - Usar diretamente a taxa sem transformação, pois o XGBoost é robusto a distribuições assimétricas.

### 5.2 Taxa de Reprovação (`TAXA_REPROV_MED`)

| Estatística | 2022 | 2023 | 2024 |
|-------------|------|------|------|
| Média | 5,01% | 4,09% | 3,09% |
| Mediana | 3,90% | 3,10% | 2,20% |
| Máximo | 55,3% | 38,5% | 41,1% |

A reprovação também caiu significativamente — 38% de redução na média entre 2022 e 2024. A taxa de reprovação do ano anterior é uma feature candidata de alta relevância no modelo: escolas com reprovação alta em *t* tendem a ter abandono alto em *t+1* (alunos que ficam reprovados frequentemente desistem no ano seguinte).

### 5.3 Taxa de Aprovação (`TAXA_APROV_MED`)

| Estatística | Valor (2022–2024) |
|-------------|-------------------|
| Média | ~94,5% |
| Mediana | ~96,4% |
| Mínimo | 28,2% |
| Máximo | 100,0% |

A taxa de aprovação é a dominante: a média de 94,5% reflete que, para a maioria das escolas, a quase totalidade dos alunos é aprovada. O mínimo de 28,2% indica que existem escolas em situação muito crítica — provavelmente as mesmas que aparecem com abandono e reprovação altos.

### 5.4 Distribuição por localização

| Localização | 2022 | 2023 | 2024 |
|-------------|------|------|------|
| Urbana | 690 | 692 | 680 |
| Rural | 110 | 109 | 111 |

O perfil urbano/rural é estável entre os anos (≈86%/14%), idêntico ao observado no painel do Censo — confirmando consistência entre as fontes.

### 5.5 Missing por coluna (painel completo)

| Coluna | % Nulos | Interpretação |
|--------|---------|---------------|
| `TAXA_APROV_MED` | 0,0% | Completo — incluir no modelo |
| `TAXA_REPROV_MED` | 0,0% | Completo — incluir no modelo |
| `TAXA_ABND_MED` | 0,0% | Completo — **target principal** |
| `TAXA_*_MED_S1` | 3,2% | Usável — escolas sem 1ª série (raro) |
| `TAXA_*_MED_S2` | 2,5% | Usável — escolas sem 2ª série (raro) |
| `TAXA_*_MED_S3` | 2,6% | Usável — escolas sem 3ª série (raro) |
| `TAXA_*_MED_S4` | 98,3% | **Excluir do modelo** — só técnico integrado |
| `TAXA_*_MED_NS` | 87,4% | **Excluir do modelo** — não seriado raro |

---

## 6. Enriquecimentos e decisões de design

### 6.1 Manter taxas por série (_S1, _S2, _S3) apesar de 3% de nulos

**Decisão:** Manter as colunas de taxa por série (1ª, 2ª e 3ª) no parquet interim, mesmo que não estejam 100% preenchidas.

**Justificativa:** Informações por série são potencialmente muito úteis para o modelo. Escolas onde o abandono se concentra na 1ª série têm um perfil diferente daquelas onde o problema ocorre na 3ª série. Os 3% de missing são aceitáveis e serão tratados por imputação no feature engineering (zero para as colunas de abandono/reprovação, valor da série mais próxima para aprovação, ou simplesmente remoção do feature se o modelo não se beneficiar).

### 6.2 Ordenação por escola × ano para viabilizar lags

O painel foi ordenado por `["CO_ENTIDADE", "NU_ANO_CENSO"]` antes de ser salvo. Isso não é necessário para o parquet em si, mas facilita o cálculo de features de lag no Notebook 03:

```python
# Exemplo de feature que será criada no Notebook 03:
df["TAXA_ABND_MED_lag1"] = df.groupby("CO_ENTIDADE")["TAXA_ABND_MED"].shift(1)
```

A taxa de abandono do ano anterior (`lag1`) é provavelmente o preditor mais forte do modelo — escolas com histórico de abandono alto tendem a manter o problema se nada mudar. A ordenação prévia garante que o `shift(1)` produza o valor correto sem necessidade de sort adicional.

### 6.3 Separação entre ETL e construção do target

O target final do modelo (`taxa_abandono_t1`) não é gerado no `build_taxas_rendimento.py` — é produzido pelo `build_target.py`, que realiza o join com o painel do Censo. Esta separação foi uma decisão deliberada:

- `build_taxas_rendimento.py` → transforma os dados brutos em um painel limpo e autocontido das taxas;
- `build_target.py` → cruza esse painel com o Censo para criar os pares (*features t*, *target t+1*).

A separação facilita a depuração (é possível inspecionar cada parquet individualmente) e torna o código mais modular para o caso de os arquivos do INEP sofrerem atualizações futuras.

### 6.4 Validação de consistência como diagnóstico, não como filtro

A validação matemática (soma = 100%) foi implementada como **warning de log**, não como filtro que remove linhas. A razão: se uma inconsistência existisse, ela deveria ser investigada e documentada — não silenciosamente removida. Neste caso, o resultado confirmou que todas as 2.392 linhas somam exatamente 100%, o que indica alta qualidade dos dados do INEP.

---

## 7. Limitações e ressalvas

### 7.1 Tendência de queda do abandono pode dificultar a predição

A forte queda na taxa de abandono entre 2022 e 2024 (de 2,05% para 0,96%) cria um desafio metodológico: o modelo treinado com dados de 2022 pode superestimar o abandono para 2024. Isso reforça a importância de usar **GroupKFold por ano** (além de por município) na validação cruzada — o modelo não deve "ver" anos futuros durante o treinamento.

### 7.2 Excesso de zeros no target

Com 67% das escolas reportando abandono zero, o modelo de regressão terá dificuldade em calibrar previsões para escolas de risco médio (ex.: 3–5% de abandono). Estratégias de tratamento serão avaliadas no Notebook 04.

### 7.3 `_S4` e `_NS` não descartados do parquet

Por decisão de projeto (rastreabilidade), as colunas com 98% e 87% de nulos foram mantidas no parquet. É obrigação do pipeline de feature engineering descartá-las explicitamente antes do treinamento — o que deve ser documentado e automatizado, não deixado a cargo de quem executar o notebook.

### 7.4 Sem validação de cobertura de municípios

Não foi verificado se os 185 municípios com escolas no painel do Censo têm correspondentes no painel de taxas. Isso será verificado ao executar `build_target.py` e inspecionar os registros perdidos no join.

---

## 8. Próximos passos

| Prioridade | Ação | Arquivo |
|-----------|------|---------|
| **CRÍTICA** | Executar `build_target.py` para gerar `painel_com_target.parquet` | `src/data/build_target.py` |
| **CRÍTICA** | Inspecionar registros perdidos no join Censo ↔ Taxas | Notebook 02b (a criar) |
| ALTA | Adicionar `openpyxl` ao `requirements.txt` | `requirements.txt` |
| ALTA | Notebook 03: criar `TAXA_ABND_MED_lag1`, `TAXA_REPROV_MED_lag1` | `notebooks/03_feature_engineering.py` |
| ALTA | Notebook 03: descartar `_S4` e `_NS` do pipeline de features | `notebooks/03_feature_engineering.py` |
| MÉDIA | Baixar INSE, Distorção Idade-Série e Adequação Docente | `data/raw/outros_indicadores/` |
| MÉDIA | Avaliar transformação do target (log, Box-Cox, ou manter bruto) | Notebook 04 |
| BAIXA | Investigar os 12 escolas que saíram do painel em 2024 | Análise ad-hoc |

---

*Documento gerado com base na execução de `src/data/build_taxas_rendimento.py` e análise do parquet `taxas_rendimento_pe_estadual_em.parquet` (2.392 linhas, 806 escolas únicas, 24 colunas).*
