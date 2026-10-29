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

### 16 · Quanto isso vale — 0:50 · Relógio 9:30

**Gráfico (teste do ano nunca visto):**
- **Esquerda:** das escolas indicadas, **42 em cada 100** eram críticas, contra **9** ao acaso.
- **Direita:** fração das escolas críticas alcançadas pela lista: com **50 escolas, 28% × 6%**; com **100, 46% × 13%**; com **150, 57% × 19%**.

> Na prática: com uma lista de **150 escolas**, a Secretaria alcança **57% das escolas críticas**, três vezes mais que escolhendo ao acaso. E o tamanho da lista se ajusta ao orçamento.

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
| O SHAP mostra causa? | Não. Mostra o peso de cada característica na previsão. Por isso o painel não recomenda ações. |
| O desempenho é estável entre anos? | Não totalmente: 2022→2023 teve 0,469 / 0,627 e 2023→2024 teve 0,367 / 0,381, acompanhando a queda do abandono médio (1,36% → 0,88%). |
| A monografia fala em "cerca de metade" acertada; o slide diz 42 em cada 100. | "Cerca de metade" (0,504) é da validação repetida. O slide usa o teste do ano nunca visto, que é mais conservador. |
| Quanto o sistema erra, em alunos? | Cerca de **3 alunos por escola** (3,3 e 3,0 nas duas transições), sem tendência; os maiores desvios estão nas escolas grandes. *(O slide desse dado saiu da versão enxuta.)* |

## Onde cortar se estiver atrasado

1. **Slide 14:** diga só "validação por município e teste no ano nunca visto, que é a estimativa honesta" (ganha ~20 s).
2. **Slide 10:** só "39 características; no topo, o histórico da escola" (ganha ~15 s).
3. **Slide 22:** só o item 1 (ganha ~10 s).

**Nunca corte:** os slides 4 (concentração), 15 (ordem × magnitude) e 19 (equidade).

## Antes da defesa

- [ ] Ensaiar com cronômetro pelo menos duas vezes; a meta é terminar entre **13:30 e 14:30**.
- [ ] O gráfico do slide 19 ainda tem título técnico ("S5 — resíduo do XGBoost"). Se perguntarem, diga que é a figura técnica do diagnóstico.
