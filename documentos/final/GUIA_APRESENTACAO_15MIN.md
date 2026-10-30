# Guia de Apresentação — 15 minutos

**Arquivo:** `Apresentacao_TCC_Evasao.pptx` (23 slides, versão enxuta)
**Apoio:** `monografia-artur-oliveira-engenharia-de-software-2026-entregue.pdf`

Tempo planejado: **cerca de 13 min 50 s**, com 1 min de folga. O "Relógio" é o horário acumulado ao fim de cada slide.

## A regra desta versão

O orientador pediu menos texto e mais objetividade. Por isso o slide traz **só o número ou a frase-chave**, e a explicação fica na sua fala.

- **Não leia o slide.** Aponte o número e explique com as suas palavras.
- **Uma ideia por slide.** Se a frase não sustenta a ideia do slide, corte.
- **Os números em negrito** abaixo são os que a banca vai cobrar.

## Mapa do tempo

| Parte | Slides | Tempo | Relógio |
|---|---|---|---|
| Abertura | 1 | 0:30 | 0:30 |
| 1 · O problema | 2–6 | 2:50 | 3:20 |
| 2 · A solução | 7–12 | 3:30 | 6:50 |
| 3 · Os resultados | 13–18 | 4:00 | 10:50 |
| Limites e fechamento | 19–23 | 3:00 | 13:50 |

Se até o slide 12 você passar de **7:15**, use "Onde cortar", no fim.

---

## ABERTURA

### 1 · Capa — 0:30 · Relógio 0:30

> Boa tarde. Sou Artur Oliveira Santiago e vou apresentar um **sistema que prioriza as escolas em risco de evasão** na rede estadual de Pernambuco. A ideia central é uma só: **o valor não está em prever a taxa exata, está em acertar a ordem das escolas.**

---

## PARTE 1 · O PROBLEMA

### 2 · Divisor — 0:05 · Relógio 0:35

"Começo pelo problema." Avance.

### 3 · Contexto — 0:40 · Relógio 1:15

**Slide:** três números (~800 escolas · 185 municípios · 2.043 alunos) e a frase final.

> São cerca de **800 escolas** de Ensino Médio em **185 municípios**, e **2.043 alunos** abandonaram a escola em 2024. Hoje a Secretaria age depois que o abandono aparece nos números. O sistema serve para **antecipar onde agir**.

### 4 · A média esconde o problema — 1:00 · Relógio 2:15

**Gráfico:**
- **Esquerda:** a taxa média da rede cai de **2,05%** para **0,96%** entre 2022 e 2024.
- **Direita:** em 2024, as **79 escolas mais críticas (10%)** concentram **76%** dos alunos que abandonaram.

> Olhando só a média, o problema parece resolvido: menos de 1%. Mas **dois terços das escolas não tiveram nenhum abandono**, e **76% dos evadidos estão em 79 escolas**. O abandono é **concentrado**. Quando é assim, o certo é priorizar, e para isso é preciso saber *quais* escolas estarão nesse grupo no ano seguinte.

*Aponte primeiro a linha caindo e depois a barra vermelha.*

### 5 · A decisão que define o sistema — 0:35 · Relógio 2:50

> Prever por aluno exige dados sigilosos e não é o nível em que o gestor decide. Prever por **escola** usa dados públicos, são umas 800 unidades por ano e é ali que o gestor aloca equipe e programa. **A unidade de análise é a escola.**

### 6 · Perguntas de pesquisa — 0:30 · Relógio 3:20

> Duas perguntas. **P1:** dá para prever quais escolas terão abandono alto no ano seguinte? **P2:** quais escolas fogem do que o próprio perfil faria esperar? O objetivo é **prever o risco e explicar cada indicação** ao gestor.

---

## PARTE 2 · A SOLUÇÃO

### 7 · Divisor — 0:05 · Relógio 3:25

"Agora, a solução." Avance.

### 8 · Os dados — 0:45 · Relógio 4:10

**Slide:** funil 2.392 → −791 → −15 → 1.586.

> Tudo vem do INEP e é público: Censo Escolar, taxas de rendimento e quatro indicadores, de 2022 a 2024.
> Leiam o funil: são **2.392 registros** no painel. Saem os **791** de 2024, que ainda não têm o ano seguinte para comparar, e **15** de escolas que saíram da rede. Ficam **1.586 observações, 801 escolas e 39 características**.
> A regra que evita vazamento é: **características do ano t preveem o abandono do ano t+1.**

### 9 · O que o sistema prevê — 0:40 · Relógio 4:50

**Gráfico:**
- **Esquerda:** **68%** das observações têm abandono zero; só **2%** passam de 10%.
- **Direita, 2024:** urbanas **0,6%** (679 escolas), rurais **0,9%** (70) e indígenas ou quilombolas **6,3%** (42).

> O alvo é a taxa de abandono do ano seguinte. **68% dos valores são zero**, e por isso prever o valor exato é tão difícil. E o risco é desigual: nas escolas indígenas e quilombolas a taxa é **cerca de 10 vezes maior** que nas urbanas. Esse grupo volta no slide de equidade.

> Se perguntarem por que aqui são 42 escolas e no slide 19 são 41: aqui é a taxa de 2024 em todas as escolas com dado; no slide 19 entram só as escolas do teste temporal, que precisam estar presentes nos dois anos.

### 10 · As características usadas — 0:40 · Relógio 5:30

**Gráfico:** as 38 características numéricas ordenadas pela relação com o abandono do ano seguinte. **Vermelho** aumenta o risco, **azul** reduz e **cinza** não tem relação estatística.

> Partimos de mais de 400 colunas e chegamos a **39 características em 6 grupos**. Cortamos repetição, colunas que derivam do próprio alvo e colunas quase vazias.
> No topo vermelho está o **abandono do ano anterior** (+0,48); na base azul, o **tempo integral** (−0,21). **30 das 38** têm relação comprovada.

*Aponte só o topo e a base do gráfico; não percorra as barras.*

#### Para entender o slide 10: os 6 grupos (estudo, não é fala)

Fonte: Quadro 3 da monografia e `_colunas_features()` em `src/features/build_features.py`. Todas as características são do ano **t**.

**1. Contexto e localização (4)**
| Característica | Nome no código |
|---|---|
| Zona rural (sim/não) | `is_rural` |
| Localização diferenciada: indígena ou quilombola (sim/não) | `is_loc_diferenciada` |
| Mesorregião do estado | `CO_MESORREGIAO` (categórica) |
| Oferta de EM fora das séries regulares (EJA ou organização modular) | `oferta_em_nao_seriado` |

**2. Porte e proporções (5)**
| Característica | Nome no código |
|---|---|
| Matrículas no Ensino Médio (em logaritmo) | `log_mat_med` |
| Alunos por turma | `alunos_por_turma` |
| Alunos por professor | `alunos_por_docente` |
| Computadores por aluno | `computadores_por_aluno` |
| % de alunos em tempo integral | `pct_integral` |

**3. Infraestrutura (13)**: 12 itens sim/não do Censo e um índice-resumo.
| Característica | Nome no código |
|---|---|
| Água potável | `IN_AGUA_POTAVEL` |
| Esgoto na rede pública | `IN_ESGOTO_REDE_PUBLICA` |
| Biblioteca | `IN_BIBLIOTECA` |
| Laboratório de ciências | `IN_LABORATORIO_CIENCIAS` |
| Laboratório de informática | `IN_LABORATORIO_INFORMATICA` |
| Quadra de esportes | `IN_QUADRA_ESPORTES` |
| Refeitório | `IN_REFEITORIO` |
| Sala de leitura | `IN_SALA_LEITURA` |
| Auditório | `IN_AUDITORIO` |
| Internet | `IN_INTERNET` |
| Internet para os alunos | `IN_INTERNET_ALUNOS` |
| Banda larga | `IN_BANDA_LARGA` |
| Índice de infraestrutura (resumo dos 12) | `indice_infra` |

**4. Corpo docente (4)**
| Característica | Nome no código |
|---|---|
| Regularidade do corpo docente (IRD): estabilidade dos professores na escola | `ird_med_t` |
| Adequação da formação (AFD), grupo 1: licenciatura na mesma disciplina que leciona | `afd_g1_t` |
| AFD grupo 3: licenciatura em outra área | `afd_g3_t` |
| AFD grupo 5: sem curso superior | `afd_g5_t` |

**5. Perfil dos alunos (5)**
| Característica | Nome no código |
|---|---|
| Nível socioeconômico médio (INSE) | `inse_media` |
| Distorção idade-série (TDI) no EM | `tdi_med_t` |
| TDI na 1ª, 2ª e 3ª série | `tdi_s1_t`, `tdi_s2_t`, `tdi_s3_t` |

**6. Histórico de rendimento (8)**
| Característica | Nome no código |
|---|---|
| Abandono no EM | `abnd_t` |
| Abandono na 1ª, 2ª e 3ª série | `abnd_s1_t`, `abnd_s2_t`, `abnd_s3_t` |
| Reprovação no EM | `reprov_t` |
| Reprovação na 1ª, 2ª e 3ª série | `reprov_s1_t`, `reprov_s2_t`, `reprov_s3_t` |

**Detalhes que a banca pode cobrar.**
- **Por que 38 no gráfico e 39 no total?** A mesorregião é uma categoria, não um número, e não tem correlação para mostrar no gráfico.
- **O que ficou de fora e por quê:**
  - **Aprovação:** aprovação + reprovação + abandono = 100%, então ela seria redundante.
  - **Matrícula bruta:** r = 1,0 com o logaritmo.
  - **Nível INSE em faixas:** r = 0,898 com o INSE médio.
  - **IED e ICG:** avaliados no notebook 11, sem ganho preditivo.
- **O INSE é de 2021**, a última edição disponível, e o mesmo valor é usado em todos os anos.
- **O peso dos grupos não é proporcional ao tamanho.** A infraestrutura tem 13 características e peso modesto. O histórico de rendimento tem 8 e é o mais forte (ver slide 17).

**Onde os grupos aparecem no trabalho.** Só como **organização**, nunca como unidade de análise:
- Quadro 3 (Capítulo 3) e Apêndice A da monografia;
- comentários de `src/recommend/labels.py`;
- `GRUPOS_FEATURES`, que o notebook 05 usa só para imprimir estatísticas.

Nenhum modelo, teste ou figura compara os grupos entre si. O mais próximo é o ¶432, que descreve o SHAP em "três blocos" (histórico, perfil dos alunos e contexto) por leitura das características, sem somar o peso.

*Se perguntarem qual grupo pesa mais.* Num cálculo avulso feito em 29/10, fora da monografia, a partir de `reports/shap_importancia.csv`, somando o peso SHAP médio de cada característica do grupo:

| Grupo | Fatia do peso |
|---|---|
| Histórico de rendimento | ~50% |
| Perfil dos alunos | ~22% |
| Contexto e localização | ~9% |
| Corpo docente | ~9% |
| Porte e proporções | ~8% |
| Infraestrutura | ~2% |

Somar o SHAP médio de cada característica dá uma **aproximação** do peso do grupo, não o valor exato. Use só como ordem de grandeza.

### 11 · Arquitetura — 0:35 · Relógio 6:05

**Diagrama:** em cima ficam os componentes (ETL → características → modelagem → explicação e painel); embaixo, os arquivos que cada um grava. O gestor só acessa o painel.

> Cada etapa grava o resultado em disco e a seguinte lê esse arquivo, **sem chamada direta**. Por isso dá para retomar de qualquer ponto. A dependência tem **sentido único**: dados, características, modelo, painel.

### 12 · Testes — 0:45 · Relógio 6:50

> Este é o ponto central para a Engenharia de Software. Em um sistema que aprende com dados, **o erro não quebra a execução: ele gera, em silêncio, um modelo inválido.** Se eu deslocasse em um ano o casamento entre características e abandono, tudo rodaria e o modelo não valeria nada.
> Por isso os **138 testes** cobrem riscos de validade, como casamento temporal, vazamento entre treino e teste e consistência das explicações, e não só de execução. **Nenhuma etapa depende da máquina local**, e os dados originais nunca são sobrescritos.

---

## PARTE 3 · OS RESULTADOS

### 13 · Divisor — 0:05 · Relógio 6:55

"Agora, os resultados." Avance.

### 14 · Como foi medido — 0:35 · Relógio 7:30

> Usei dois testes. Na **validação repetida**, são 20 rodadas, cada uma deixando 20% dos **municípios** fora do treino, e nenhum município aparece dos dois lados. No **teste do ano nunca visto**, o sistema treina com 2022→2023 e prevê 2023→2024, como no uso real; é a **estimativa honesta**.
> O que importa é **acertar a ordem** e a lista das 10% mais críticas.

### 15 · O sistema acerta a ordem, não a magnitude — 1:10 · Relógio 8:40

**Gráfico (teste do ano nunca visto):**
- **Esquerda, erro do valor (menor é melhor):** sem sistema **2,54** e modelo adotado **2,87**. Nenhum modelo fica abaixo da linha tracejada, que é a média da rede.
- **Direita, acerto da lista:** sem sistema **9 em cada 100**; modelo adotado **42 em cada 100**.
- Cores: cinza = sem sistema, azul = linear, verde = árvores, vermelho = modelo adotado (XGBoost).

> Este é o resultado central. No **erro do valor**, o sistema é **pior que chutar a média**. No **acerto da lista**, passa de **9 para 42 em cada 100**.
> Os cartões resumem: ordenação **0,348**, lista **0,418**, separação entre críticas e não críticas **0,798**.
> É um **termômetro descalibrado**: erra os graus, mas aponta quem tem mais febre, e é isso que o gestor precisa.
> Os três modelos são **estatisticamente indistinguíveis**. Escolhi o XGBoost pelo teste temporal e pelas explicações construídas sobre ele, **não por superioridade geral**.

*Não suavize o erro do valor. Dizer isso antes da banca perguntar mostra rigor.*

#### Para entender o slide 15 (estudo, não é fala)

**O cenário.** Todos os números são do teste do ano nunca visto. O modelo treina com as características de 2022 e o abandono de 2023, e então recebe as características de 2023 das **789 escolas** para prever o abandono de 2024, que ele nunca viu. É o mesmo uso que terá na Secretaria.

**As quatro barras.** São quatro jeitos de prever o abandono de 2024:

| Barra | O que é | Como prevê |
|---|---|---|
| Cinza, "sem sistema" | Dummy | Dá a **mesma taxa** a todas as escolas: a média do treino |
| Azul, "linear" | Ridge | Soma ponderada das 39 características |
| Verde, "árvores" | Random Forest | Média de muitas árvores de decisão |
| Vermelho, "adotado" | XGBoost | Árvores em sequência, cada uma corrigindo a anterior |

**Gráfico da esquerda: erro do valor (RMSE, em pontos percentuais).** Mede quanto a taxa prevista fica longe da real, em média. Erros grandes pesam mais, porque o erro é elevado ao quadrado.
- O dummy erra **2,54 p.p.** e serve de piso (linha tracejada). O XGBoost erra **2,87**, o RF 2,75 e o Ridge 2,89.
- **Nenhum modelo fica abaixo do piso.** Para estimar a taxa, chutar a média é melhor. O R² do XGBoost é **−0,33**, e o negativo quer dizer exatamente isso.
- O motivo: **68% dos valores são zero** e poucas escolas têm taxas muito altas. A média fica perto da maioria e nunca erra muito. O modelo tenta separar as escolas, se arrisca com valores altos e, quando erra num caso extremo, o erro ao quadrado pesa muito. Além disso, o abandono caiu de 1,36% para 0,88% entre as duas transições, e um modelo treinado no ano de abandono mais alto tende a prever acima do que aconteceu.

**Gráfico da direita: acerto da lista (Precision@K).** A Secretaria não usa a taxa, usa a **lista das 10% mais críticas**. Com 789 escolas, K = **79**.
- O sistema monta a lista com as 79 de maior risco previsto. Depois se confere quantas delas estão entre as 79 de maior abandono real em 2024.
- XGBoost: **0,418**, ou seja, 33 das 79 (42 em cada 100). RF: 41. Ridge: 38.
- Dummy: **0,089**, 7 das 79. Como dá o mesmo valor a todas, a lista dele é arbitrária e equivale a sortear. Ao acaso se espera cerca de 10 em cada 100.
- Ganho: 0,418 / 0,089 = **4,7×**.

**Os cartões.**
- **0,348, acerto da ordenação (Spearman).** Compara a ordem prevista com a ordem real das 789 escolas. Vai de −1 a 1: 0 é ordem aleatória e 1 é ordem perfeita. 0,348 é uma concordância moderada. Não é uma porcentagem.
- **0,418, acerto da lista prioritária.** É o Precision@K explicado acima.
- **0,798, separação entre críticas e não críticas (ROC AUC).** Pegue ao acaso uma escola crítica (dos 10% de maior abandono real) e uma não crítica. Em **80% dos pares** o sistema dá risco maior à crítica. A escala vai de 0,5 (acaso) a 1 (separação perfeita). A monografia trata disso no ¶461.
- **"Não supera o piso", erro do valor.** É o gráfico da esquerda em uma frase.

**A metáfora.** Um termômetro que marca 39 °C para quem tem 38 °C e 37 °C para quem tem 36 °C erra os graus, mas acerta quem está com mais febre. Para decidir quem atender primeiro, isso basta.

**Por que isso não invalida o sistema.** A decisão do gestor é uma **ordem**: por quais escolas começar. O erro do valor seria grave se o sistema fosse usado para dizer "esta escola vai perder 12 alunos". Por isso o painel mostra a posição e o laudo, e não promete a taxa.

**Cuidado: as métricas não apontam todas para o XGBoost.**
- Ele ganha na ordenação (0,348) e na lista (0,418).
- O RF ganha no erro do valor (2,751 contra 2,874) **e na separação** (0,829 contra 0,798, ¶463).
- Na validação repetida, o RF ganha na ordenação (0,431) e o Ridge na lista (0,513); o XGBoost fica com 0,416 e 0,504. Os intervalos se sobrepõem, então **os três empatam**. Não diga "o melhor modelo"; diga "o modelo adotado".

**Posição no tempo.** Este slide responde à P1. Se estiver atrasado, **não corte este slide**: corte o 14.

### 16 · Quanto isso vale — 0:50 · Relógio 9:30

**Gráfico (teste do ano nunca visto):**
- **Esquerda:** das escolas indicadas, **42 em cada 100** eram críticas, contra **9** ao acaso.
- **Direita:** fração das escolas críticas alcançadas pela lista: com **50 escolas, 28% × 6%**; com **100, 46% × 13%**; com **150, 57% × 19%**.

> Na prática: com uma lista de **150 escolas**, a Secretaria alcança **57% das escolas críticas**, três vezes mais que escolhendo ao acaso. E o tamanho da lista se ajusta ao orçamento.

#### Para entender o slide 16 (estudo, não é fala)

**A pergunta do slide.** O slide 15 mostra que o sistema ordena melhor que o acaso. O 16 traduz isso para o gestor: *se eu visitar N escolas da lista, quantas críticas eu encontro?*

**O cenário.** É o mesmo teste do ano nunca visto: o modelo treina com 2022→2023 e prevê 2024 para **789 escolas**.

**Quem é "crítica".** Uma escola é crítica se ficou entre os 10% de maior abandono **real** em 2024: taxa de **2,7% ou mais**. São **80 escolas**. São 80, e não 79, porque há empates no limiar. Essa definição é feita depois do fato, só para conferir o acerto: o sistema não sabe quem é crítica.

**Gráfico da esquerda: precisão, "das indicadas, quantas eram críticas".** É o mesmo número do slide 15: em uma lista de 79 escolas, **33** eram críticas (42 em cada 100). Ao acaso, 9 em cada 100. A pergunta é: *quando o sistema aponta, ele acerta?*

**Gráfico da direita: alcance, "das críticas, quantas a lista encontra".** Aqui a pergunta se inverte: *das 80 críticas que existem, quantas a lista pega?*

| Lista (escolas visitadas) | Críticas encontradas | Alcance | Ao acaso | Precisão da lista |
|---|---|---|---|---|
| 50 | 22 | **28%** | 6% | 44% |
| 100 | 37 | **46%** | 13% | 37% |
| 150 | 46 | **57%** | 19% | 31% |

- **"Ao acaso"** é simplesmente o tamanho da lista dividido pelo total: visitar 150 de 789 escolas sorteadas pega 19% de qualquer grupo, inclusive das críticas.
- O ganho fica em torno de **3 a 4,4×** sobre o acaso, em qualquer tamanho de lista.

**A troca que o gestor faz (a última coluna não está no slide).** Quanto maior a lista, **mais críticas ela alcança**, mas **menor a fração de acertos**: com 50 escolas, 44% são críticas; com 150, 31%. Uma lista curta é mais certeira e deixa muitas críticas de fora. Uma lista longa cobre mais e gasta mais visitas com escolas sem problema. Por isso "o tamanho se ajusta ao orçamento": o gestor escolhe o ponto da troca, e o sistema só fornece a ordem.

**A leitura honesta.**
- Mesmo com 150 escolas (19% da rede), **43% das críticas ficam de fora** (34 de 80).
- Com 150 visitas, cerca de **7 em cada 10 escolas visitadas não eram críticas**.
- O acaso é a mesma régua fraca do slide 15. O slide não compara o sistema com a lista do ano anterior.

**Perguntas que este slide puxa.**
- *Por que o 57%, se o slide 15 diz 42?* São medidas diferentes. 42 é a fração **da lista** que acertou (lista de 79). 57 é a fração **das críticas** que a lista encontrou (lista de 150).
- *Quem decide o tamanho da lista?* O gestor, conforme a equipe e o orçamento. O painel deixa filtrar o top-N.

### 17 · Por que esta escola? — 0:45 · Relógio 10:15

**Gráfico:** o peso médio de cada característica na previsão (SHAP). Vermelho = valor alto aumenta o risco; azul = reduz.

> Cada previsão é decomposta em quanto cada característica contribuiu. Pesam mais o **histórico de abandono da escola**, a **defasagem idade-série** e a **reprovação**, e as direções batem com o esperado. O sistema **acerta pelas razões certas**. A leitura é diagnóstica, **não causal**.

### 18 · Uma escola específica — 0:35 · Relógio 10:50

**Gráfico:** a explicação de uma escola só. Todas as barras empurram o risco para cima, e a maior é a defasagem idade-série.

> A maior previsão da base histórica é uma **escola indígena de Jatobá: 28,7%**, com características de 2022 (o observado em 2023 foi 39,1%). O motivo principal é a **defasagem idade-série**. É esse **laudo** que o gestor vê no painel, para concordar ou discordar com argumento.

> Se perguntarem: no ranking de 2025, essa escola está em 16º, com 7,7%.

**Transição:** "E o fato de essa escola ser indígena me leva ao limite do trabalho."

---

## LIMITES E FECHAMENTO

### 19 · Equidade — 0:55 · Relógio 11:45

**Gráfico (teste do ano nunca visto):**
- **Esquerda:** urbanas e rurais ficam em torno de zero; nas escolas de localização diferenciada (indígenas e quilombolas), a caixa inteira fica abaixo.
- **Direita:** erro médio por grupo: urbanas **+0,07**, rurais **+0,38** e indígenas e quilombolas **−6,12 p.p.** Negativo quer dizer que o sistema **previu mais** do que aconteceu.

> Este é o limite mais importante. Nas **41 escolas indígenas e quilombolas**, o sistema prevê cerca de **11%** e o observado é cerca de **5%**: erra **6 pontos para mais**. A causa provável é a **proteção comunitária**, que os dados não captam. Sem correção, o sistema levaria recursos para escolas sem risco real. Por isso o limite está **declarado no painel** e é o primeiro trabalho futuro.

*Fale devagar aqui.*

#### Para entender o slide 19 (estudo, não é fala)

**O que é o resíduo.** Resíduo = abandono **real − previsto**, em pontos percentuais.
- **Positivo:** o sistema previu **menos** do que aconteceu (subestimou).
- **Negativo:** previu **mais** do que aconteceu (superestimou).
- Perto de zero: o sistema está calibrado para aquele grupo.

Os dados são do teste do ano nunca visto: características de 2023 e abandono de 2024, 789 escolas (`reports/residuos_grupo_temporal.csv`).

**Gráfico da esquerda: distribuição do resíduo por grupo (boxplot).** A caixa reúne a metade central das escolas, a linha preta é a mediana, as hastes mostram a dispersão e as bolinhas são casos isolados.
- **Urbanas (679) e rurais (69):** a caixa é tão estreita que vira um traço em cima do zero. A maioria das escolas tem erro pequeno. As bolinhas acima de zero são escolas onde o abandono "estourou" sem que o sistema previsse; a maior delas chega a +24 p.p.
- **Diferenciadas (41):** a caixa inteira fica abaixo de zero, com mediana de **−4,6 p.p.** e erros de até −23. O erro não é ocasional: é **sistemático**, e **80%** dessas escolas foram superestimadas.

**Gráfico da direita: erro médio por grupo.**

| Grupo | Escolas | Previsto (média) | Real (média) | Erro médio |
|---|---|---|---|---|
| Urbanas | 679 | 0,56% | 0,63% | **+0,07** |
| Rurais | 69 | 0,50% | 0,88% | **+0,38** |
| Indígenas e quilombolas | 41 | **11,08%** | **4,96%** | **−6,12** |

Urbanas e rurais estão calibradas, porque o erro médio é quase nulo. Nas diferenciadas, o sistema prevê o **dobro** do que acontece.

**Por que é o limite mais importante.**
1. **Distorce a lista.** Das 41 escolas diferenciadas, **39 entram na lista das 79 de maior risco**: metade da lista prioritária vem de um grupo que é 5% da rede. Dessas 39, só **17** eram de fato críticas. Ou seja, **22 vagas da lista** foram para escolas diferenciadas sem risco real, tirando lugar de escolas urbanas e rurais críticas.
2. **A característica é a nº 1 do modelo.** `is_loc_diferenciada` é a característica de maior ganho no XGBoost (0,239). O sistema aprendeu "diferenciada = risco alto" e aplica isso ao grupo inteiro.
3. **É o grupo mais sensível.** Um erro aqui pode estigmatizar comunidades indígenas e quilombolas e direcionar recursos de forma equivocada.

**⚠ Cuidado com a "causa provável" do slide.** O slide atribui o erro à "proteção comunitária que os dados não captam". Os dados mostram uma explicação mais simples:

| Escolas diferenciadas | Abandono médio |
|---|---|
| 2023 (o que o modelo aprendeu e recebeu como característica) | **13,0%** |
| 2024 (o que aconteceu) | **4,96%** |

O abandono do grupo **caiu de 13% para 5% em um ano**. O modelo aprendeu com o ano de 13%, recebeu a taxa de 2023 como característica mais forte, e previu 11%. Se houvesse uma proteção comunitária estável, o abandono de 2023 não teria sido de 13%. A leitura mais defensável é:
- **o grupo mudou muito de um ano para o outro e o modelo não tinha como antecipar isso**;
- o grupo é **pequeno** (41 escolas), então poucas escolas mudam a média;
- o que fez o abandono cair não está nos dados, e a proteção comunitária é **uma das hipóteses**, não a causa.

Também é preciso dizer que o viés foi medido em **um único ano de teste**. Não se sabe se ele se repete.

**Fala alternativa sugerida para a "causa":**
> O abandono nessas escolas caiu de 13% para 5% em um ano, e o modelo, que aprendeu com o ano anterior, não acompanhou. O que explica essa queda, seja proteção comunitária, seja alguma política local, os dados públicos não mostram.

**"Declarado no painel".** É a função `ressalva_equidade()` em `src/recommend/service.py`. Toda escola diferenciada aparece no painel e na planilha exportada com o aviso de que o risco está superestimado em cerca de 6 p.p.

**Por que não simplesmente retirar a característica?** O grupo continuaria identificável por características correlacionadas (alta defasagem idade-série, abandono passado alto, localização), e o viés migraria para elas. O caminho é **calibrar por grupo** e, até lá, declarar o limite.

### 20 · O painel — 0:40 · Relógio 12:25

> O gestor recebe três telas: o **ranking** do ano seguinte, com filtros e exportação; o **detalhe da escola**, com o laudo; e o **panorama**, que mostra quem abandona mais ou menos que o previsto e responde à P2. É **apoio à decisão**: mostra associações, não causas. Responde **onde intervir primeiro, e por quê**.

### 21 · Conclusões — 0:45 · Relógio 13:10

> **P1: sim.** O sistema acerta *quais* escolas, não *quanto*, e a decisão do gestor depende da ordem.
> **P2: sim.** Comparar observado e esperado revela as escolas que fogem do padrão.
> A evasão é concentrada, então priorizar faz sentido; e em um sistema que aprende com dados, **a engenharia, com camadas e testes, é a defesa** contra erros silenciosos.

### 22 · Trabalhos futuros — 0:20 · Relógio 13:30

> Primeiro, **corrigir o viés de equidade**. Depois, ampliar a base histórica, evoluir o sistema e avaliar o uso com gestores.

### 23 · Encerramento — 0:20 · Relógio 13:50

> **O sistema não diz quanto cada escola vai perder. Diz onde olhar primeiro, e por quê.** Obrigado.

*Pausa antes do "obrigado".*

---

## Perguntas prováveis da banca

| Pergunta | Resposta curta |
|---|---|
| Por que XGBoost, se o RF empata? | Os três são indistinguíveis. O XGBoost foi o melhor no teste temporal (0,348 / 0,418) e as explicações foram feitas sobre ele. Não afirmo superioridade geral. |
| Errar mais que a média não invalida o modelo? | Só se o objetivo fosse estimar a taxa. Com 68% de zeros, a média é difícil de bater nesse erro. O objetivo é ordenar, e aí o ganho é de 4,7× (0,418 × 0,089). |
| Como evitou vazamento? | Casamento t→t+1, divisão por município e preenchimento de dados faltantes por mesorregião no mesmo ano. Tudo travado por teste. |
| Por que só três anos? | É o que existe com todos os indicadores harmonizados. A série curta explica parte do erro de magnitude. |
| Por que não tirar a característica indígena/quilombola? | O viés migraria para características correlacionadas. A saída é calibrar por grupo e, enquanto isso, declarar o limite. |
| Como sabe que a causa é a proteção comunitária? | Não sei; é hipótese. O que os dados mostram é que o abandono do grupo caiu de 13,0% (2023) para 4,96% (2024), e o modelo aprendeu com o ano alto. Com 41 escolas e um só ano de teste, não dá para separar a causa. |
| O viés afeta a lista ou só o valor? | Afeta a lista: 39 das 41 diferenciadas entram no top 79, e só 17 delas eram críticas. São 22 vagas para escolas sem risco real. |
| O SHAP mostra causa? | Não. Mostra o peso de cada característica na previsão. Por isso o painel não recomenda ações. |
| O desempenho é estável entre anos? | Não totalmente: 2022→2023 teve 0,469 / 0,627 e 2023→2024 teve 0,367 / 0,381, acompanhando a queda do abandono médio (1,36% → 0,88%). |
| A monografia fala em "cerca de metade" acertada; o slide diz 42 em cada 100. | "Cerca de metade" (0,504) é da validação repetida. O slide usa o teste do ano nunca visto, que é mais conservador. |
| O RF não separa melhor as críticas (0,829 × 0,798)? | Sim, e também erra menos o valor. O XGBoost ganha nas duas medidas ligadas à decisão (ordem e lista) no teste do ano nunca visto. As diferenças estão dentro da variação: os três empatam. |
| O que é o 0,348? Uma porcentagem? | Não. É a correlação de Spearman entre a ordem prevista e a real: 0 é ordem aleatória e 1 é ordem perfeita. 0,348 indica concordância moderada. |
| Por que não usar só a taxa de abandono do ano anterior? | **Ponto fraco, preparar bem.** Num cálculo avulso (29/10, fora do pipeline e da monografia), repetir a taxa de 2023 deu Spearman 0,466 e P@K 0,456, acima do XGBoost na ordenação. Ela já é uma das 39 características e a mais forte. As outras servem para: (1) **538 das 789 escolas** tinham abandono zero em 2023 e a regra não as ordena; **105** delas tiveram abandono em 2024, e **20** estavam entre as 79 mais críticas; (2) a P2 depende de um perfil "esperado"; (3) o laudo explica o porquê. *Só cite esses números depois de colocá-los no pipeline.* |
| Quanto o sistema erra, em alunos? | Cerca de **3 alunos por escola** (3,3 e 3,0 nas duas transições), sem tendência; os maiores desvios estão nas escolas grandes. *(O slide desse dado saiu da versão enxuta.)* |

---

## Apoio para perguntas técnicas da área de dados (estudo, não é fala)

Esta seção serve para quando alguém da banca falar como cientista de dados: hiperparâmetros, desenho da validação, métricas, SHAP. Os números foram conferidos em 30/10 contra `models/xgboost_v1.joblib`, `src/models/train.py`, `src/models/evaluate.py`, `notebooks/07` e `08` e os CSVs de `reports/`. A regra continua a mesma: responda curto, com o número, e **admita o limite antes que a banca o aponte**.

### Ficha técnica do modelo adotado

| Item | Valor | Onde está |
|---|---|---|
| Tarefa | **Regressão** da taxa de abandono t+1 (em %), usada como escore de risco para ordenar | `TARGET_COL` em `train.py` |
| Algoritmo | `XGBRegressor`, `objective="reg:squarederror"`, `tree_method="hist"` | `criar_xgboost()` |
| Hiperparâmetros finais | `n_estimators=300`, `max_depth=2`, `learning_rate=0.02`, `min_child_weight=5`, `reg_lambda=5.0` | lidos do `.joblib` |
| Fixos (fora da busca) | `subsample=0.8`, `colsample_bytree=0.8`, `random_state=42` | `criar_xgboost()` |
| Busca | `GridSearchCV`, **48 combinações** × 5 folds, `GroupKFold` por município, critério **RMSE** | `GRID_XGB`, `buscar_hiperparametros()` |
| Transformação do alvo | Testadas identidade, `log1p` e `sqrt`; venceu a **identidade** (o modelo salvo é um `Pipeline` simples, sem `TransformedTargetRegressor`) | notebook 08, X2 |
| Pré-processamento | Numéricas: mediana + `StandardScaler`; mesorregião: *one-hot* | `criar_preprocessador()` |
| Modelo em produção | Retreinado com **todas as 1.586 observações** (2022 e 2023) | `registrar_e_salvar()` |
| Explicação | `shap.TreeExplainer`, `feature_perturbation="tree_path_dependent"` (exato, sem amostra de fundo) | `calcular_shap_values()` |
| Baselines | Dummy (média); Ridge (`alpha` em 0,1–100); RF (300 árvores, `max_depth` e `min_samples_leaf` na grade) | `GRID_RIDGE`, `GRID_RF` |

*Para decorar:* **árvores de profundidade 2, passo 0,02, 300 árvores, regularização L2 = 5.** A configuração é contida de propósito, porque a base é pequena (¶296).

### Formulação do problema

| Pergunta | Resposta curta |
|---|---|
| Por que regressão e não classificação? | O alvo é contínuo, e qualquer corte de "escola crítica" seria arbitrário e mudaria a cada ano. A regressão gera um escore que ordena todas as escolas e deixa o gestor escolher o tamanho da lista. A classificação aparece só **depois**, para comparar com a literatura: críticas = decil superior do abandono real, ROC AUC **0,798** (¶461). |
| Se o objetivo é ordenar, por que não um modelo de ranking (*learning to rank*)? | Não foi testado. Com ~800 escolas por ano e dois pares de anos, a regressão com métrica de ordenação foi a opção mais simples de auditar. Fica como trabalho futuro. |
| Como lidou com os 68% de zeros? | Testei transformar o alvo (`log1p` e `sqrt`). No Ridge e no RF elas melhoram um pouco a ordenação e pioram o erro do valor (`reports/metricas_transformacoes.csv`); no XGBoost a identidade venceu por RMSE. Modelos próprios para excesso de zeros (Tweedie, *hurdle*) **não foram testados**. É uma boa sugestão. |
| Isso é série temporal? | Não no sentido de modelar a dinâmica: cada linha é escola×ano e o passado entra como característica do ano t (`abnd_t`, `reprov_t`). Só há dois pares t→t+1, então não dá para estimar tendência. |

### Validação e vazamento

| Pergunta | Resposta curta |
|---|---|
| Por que agrupar por município? | Escolas do mesmo município compartilham contexto (rede, economia, gestão regional). Misturar o município entre treino e teste infla a métrica. `CO_MUNICIPIO` fica fora das características e serve só como grupo. |
| A mesma escola aparece duas vezes (2022 e 2023). Isso vaza? | Não entre folds: a escola está sempre no mesmo município, logo sempre do mesmo lado. No teste temporal, a escola de 2023 tem par em 2022 no treino, e isso é o uso real: o sistema conhece a história da escola. |
| Qual a diferença entre as duas validações? | **Validação repetida:** `GroupShuffleSplit`, 20 rodadas com 20% dos municípios no teste; mistura os dois anos e mede a variabilidade. **Teste do ano nunca visto:** treina em 2022→2023 e testa em 2023→2024 (789 escolas); é a estimativa que reproduz o uso. |
| Por que dois métodos de divisão diferentes (`GroupKFold` e `GroupShuffleSplit`)? | `GroupKFold` (5 folds) foi usado na busca de hiperparâmetros; `GroupShuffleSplit` permite repetir 20 vezes com sementes diferentes e obter a distribuição das métricas. Detalhe extra: o `GroupKFold` mudou a partição entre versões do scikit-learn, por isso o `requirements.txt` fixa as versões. |
| E a imputação, não vaza? | Dois níveis. No `build_features`, a média por **mesorregião × mesmo ano**, sem nenhum ano futuro e sem usar o alvo. No pipeline, `SimpleImputer` com mediana ajustada só no fold de treino. Ressalva honesta: a média por mesorregião é calculada com todas as escolas daquele ano, inclusive as que caem no teste. É informação das características, não do alvo, e o efeito é pequeno. |
| Por que o K da validação repetida varia? | K = 10% do fold de teste, e o fold sorteia **municípios**, não escolas. Por isso K vai de **18 a 44** entre as rodadas (`metricas_cv_repetida.csv`). |

### Hiperparâmetros e sobreajuste

| Pergunta | Resposta curta |
|---|---|
| Como evitou sobreajuste? | Árvores rasas (`max_depth=2`), passo pequeno (0,02), `min_child_weight=5`, L2 = 5 e subamostragem de 80% de linhas e colunas. A grade inteira foi montada só com configurações conservadoras. |
| Por que grade e não busca bayesiana (Optuna)? | 48 combinações cabem em validação agrupada, e a grade é reprodutível e fácil de auditar. Com resultados tão próximos entre modelos, uma busca mais fina dificilmente mudaria a conclusão, mas isso não foi testado. |
| Por que não redes neurais? | Dados tabulares, ~1.600 linhas e 39 características: árvores com *boosting* são o padrão para esse cenário, e o SHAP é exato para elas. Uma rede exigiria mais dados e perderia a explicação exata. |

### Métricas

| Pergunta | Resposta curta |
|---|---|
| Como o Precision@K trata empates? | Ordena por `np.argsort` e pega os K maiores; empates no limiar são desfeitos pela posição na tabela. Por isso o Dummy, que dá o mesmo valor a todas, tem uma lista **arbitrária**, e o Spearman dele nem existe (vazio no CSV), porque a previsão é constante. |
| Como foram calculados os intervalos de confiança? | Média ± 1,96 × erro-padrão nas 20 rodadas (aproximação normal). Spearman: Ridge **[0,392; 0,463]**, RF **[0,400; 0,463]**, XGBoost **[0,387; 0,445]**. P@K: Ridge [0,472; 0,553], RF [0,457; 0,545], XGBoost [0,457; 0,550]. Todos se sobrepõem. *(Calculado de `metricas_cv_repetida.csv` pela fórmula do notebook 07, M6.)* |
| As 20 rodadas são independentes? | Não: os conjuntos de treino se sobrepõem, e o erro-padrão simples **subestima** a variância. Isso reforça a conclusão de empate: com uma correção, os intervalos ficariam ainda mais largos. |
| R² negativo não é um modelo inútil? | R² negativo diz que, **para estimar o valor**, a média é melhor. Não diz nada sobre ordenar. O ganho está no Spearman e no P@K (slide 15). |
| Por que a separação (AUC 0,798) é alta e o Spearman (0,348) é moderado? | Medem coisas diferentes. O AUC só pergunta se as críticas ficam acima das não críticas. O Spearman exige acertar a ordem entre as ~68% de escolas com abandono zero, que é ruído. |

### Explicabilidade (SHAP)

| Pergunta | Resposta curta |
|---|---|
| Por que `is_loc_diferenciada` é a 1ª por ganho e só a 5ª no SHAP? | O **ganho** mede quanto a característica reduziu o erro nas divisões das árvores: ela separa 41 escolas com abandono muito diferente, e cada divisão rende muito (0,239). O **SHAP médio** tira a média do efeito absoluto em todas as escolas: para a grande maioria, que não é diferenciada, o efeito é pequeno, e a média cai (0,113). As duas leituras estão certas; respondem a perguntas diferentes. |
| Em que unidade está o SHAP? | Em **pontos percentuais** de abandono previsto, porque o alvo não foi transformado. Ex.: o abandono da 2ª série (`abnd_s2_t`) desloca a previsão em **0,33 p.p.** em média (`shap_importancia.csv`). A soma das contribuições mais o valor-base reproduz a previsão, e há teste para isso (`tests/test_explain.py`). |
| Características correlacionadas (abandono total e por série) não confundem o SHAP? | Confundem a **divisão do crédito** entre elas: o peso do "histórico de abandono" pode se espalhar por `abnd_t`, `abnd_s1_t`, `abnd_s2_t` e `abnd_s3_t`. Por isso a leitura é por bloco (¶432) e diagnóstica, não causal. |
| Por que `tree_path_dependent`? | É exato para árvores, determinístico e dispensa escolher uma amostra de fundo. |

### Produção e deriva

| Pergunta | Resposta curta |
|---|---|
| Como o modelo lida com a queda do abandono entre os anos? | Não lida: com dois pares de anos não há como aprender que o patamar se move (1,36% → 0,88%). É a causa principal do erro do valor (¶460). A ordem se mantém melhor que o nível. |
| Com que frequência retreinar? | A cada novo Censo e taxas de rendimento do INEP, ou seja, uma vez por ano. Cada ano novo acrescenta um par t→t+1 e permite medir a deriva. |
| O modelo em produção é o mesmo que foi avaliado? | Mesma configuração, retreinado com os dois anos (1.586 linhas). As métricas do teste temporal vêm de um ajuste separado, só com 2022→2023. |

### Pontos fracos que um cientista de dados pode encontrar

Saiba estes de cor. Admitir antes é melhor que ser pego.

1. **A busca de hiperparâmetros viu o ano de teste.** O `GridSearchCV` roda sobre as 1.586 linhas, que incluem os pares 2023→2024; depois o teste temporal reaproveita essa configuração. A validação não é aninhada. *Resposta:* "A configuração foi escolhida com os dois anos e reaproveitada no teste temporal, então essa estimativa é levemente otimista. O mesmo procedimento valeu para os três modelos, e a comparação entre eles continua justa. A grade é pequena e conservadora, o que limita o efeito, mas o certo seria escolher só com 2022→2023."
2. **A busca otimizou RMSE, e o critério do trabalho é ordenação.** *Resposta:* "É uma incoerência real. Otimizar diretamente Spearman ou P@K é um ajuste natural e não muda o desenho do sistema."
3. **A regra ingênua (repetir a taxa do ano anterior) ordena melhor.** Ver a última linha da tabela anterior. Não esconda.
4. **O erro-padrão da validação repetida é otimista** (rodadas não independentes). A conclusão de empate só se fortalece.
5. **Comentário desatualizado no código.** O topo de `src/models/explain.py` diz que o modelo final usa `sqrt` no alvo e que o SHAP está em "unidades de raiz". O modelo salvo **não tem transformação** (venceu a identidade), então o SHAP está em p.p. Se alguém abrir o código, explique que é um comentário antigo, e corrija depois da defesa.

## Onde cortar se estiver atrasado

1. **Slide 14:** diga só "validação por município e teste no ano nunca visto, que é a estimativa honesta" (ganha ~20 s).
2. **Slide 10:** só "39 características; no topo, o histórico da escola" (ganha ~15 s).
3. **Slide 22:** só o item 1 (ganha ~10 s).

**Nunca corte:** os slides 4 (concentração), 15 (ordem × magnitude) e 19 (equidade).

## Antes da defesa

- [ ] Ensaiar com cronômetro pelo menos duas vezes; a meta é terminar entre **13:30 e 14:30**.
- [ ] Rastreabilidade do slide 16: o gráfico da esquerda (9 e 42 em cada 100, teste do ano nunca visto) **não é** o que `notebooks/12_figuras_monografia.py` gera hoje. A função `figura_desempenho` calcula o painel esquerdo pela média da validação repetida (≈7 e ≈50) e não põe "(teste do ano nunca visto)" no título. O painel direito confere com o notebook 12 (28/46/57%). Antes de responder sobre a origem da figura, saber qual versão está no slide.
- [ ] O gráfico do slide 19 ainda tem título técnico ("S5 — resíduo do XGBoost"). Se perguntarem, diga que é a figura técnica do diagnóstico.
