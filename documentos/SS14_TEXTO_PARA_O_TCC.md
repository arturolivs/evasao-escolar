# SS14 — Texto e Quadro para a seção 6.3: o modelo em escolas concretas

> **APLICADO AO `.docx` EM 11/08/2026.** As três propostas entraram no documento com
> marcação de revisão (azul `1F4E9B` + realce amarelo), backup em `TCC_ANTES_SS14.docx`.
> Ponteiros no documento: ¶413 (proposta 1), ¶437 (proposta 3), ¶445–¶450 + Quadro 12
> (proposta 2); entrada acrescentada à Lista de Quadros (¶202). Das duas decisões que
> dependiam do autor, valeram as recomendações: escolas **nomeadas** e quadro ao **fim
> de 6.3**, sem renumerar nada. Governança cumprida: bloco 10 novo no notebook 15 com 26
> checagens (varredura **162 OK / 0 divergências**, `pytest` 138/138). Este arquivo fica
> como registro da proposta e da justificativa de cada escolha.

Atende ao comentário do orientador (11/08/2026, `comentários-orientador.md`):

> *"Ainda tô achando confusa a seção 6. Não consigo entender o que o modelo faz
> exatamente. O Quadro 11, por exemplo, traz um grande levantamento de taxa de
> acertos, mas quando olho eu não sei se o modelo tá bom ou tá ruim. Eu gostaria
> de ver algo do tipo: a evasão da escola X foi 10 e o modelo disse 9; mas teve
> escola com evasão 0 e modelo disse 1 ou zero. Talvez tenha escolas que o modelo
> acerta muito e outras que acerta pouco. Queria saber quais são os casos. Acho
> que tá faltando isso."*

O comentário contém quatro pedidos, e cada proposta abaixo ataca um deles:

| Pedido | Proposta |
|---|---|
| "não entendo o que o modelo faz exatamente" | **1** — três frases operacionais na abertura de 6.3.1 |
| "não sei se tá bom ou tá ruim" (Quadro 11) | **3** — frase-guia de leitura junto ao Quadro 11 |
| "evasão foi 10 e o modelo disse 9; evasão 0 e disse 1 ou 0" | **2** — Quadro novo com seis escolas reais |
| "quais são os casos em que acerta muito e acerta pouco" | **2** — parágrafo de leitura com a tipologia nomeada |

Todos os números vêm de artefatos existentes do pipeline — **nenhum retreino é
necessário**:

- **Fonte principal:** `reports/residuos_grupo_temporal.csv` (as 789 escolas do
  teste do ano nunca visto, cada uma com abandono observado, previsto e resíduo)
- **Em nº de alunos:** `reports/residuos_transicoes_alunos.csv` (transição 2023–2024)
- Posição na lista = ordem decrescente da taxa prevista nesse mesmo CSV

Um achado da seleção que vale registrar: o exemplo hipotético dele ("evasão 10,
modelo disse 9") **existe quase literalmente nos dados** — a Escola Sagrada
Família teve 16,7% de abandono e o modelo previu 16,4%.

---

## Proposta 1 — o que o modelo faz, em três frases (abertura de 6.3.1)

Inserir no início de "Como o Desempenho Foi Medido" (¶412), antes dos protocolos:

> Em termos operacionais, o modelo faz uma única coisa. Para cada escola, ele
> recebe as 39 características observadas em um ano — histórico de abandono e
> reprovação, perfil dos alunos, corpo docente, infraestrutura, localização — e
> devolve um número: a taxa de abandono prevista para o ano seguinte. Aplicado a
> toda a rede, esse número ordena as escolas da maior para a menor taxa prevista,
> e é dessa ordem que sai a lista de prioridade. Como saber se essas previsões
> prestam é a pergunta desta seção; a subseção final a responde no caso a caso,
> com escolas reais.

## Proposta 2 — subseção nova ao fim de 6.3, com o Quadro 12

**Posição:** nova subseção (Heading 3) depois de "Resultados em Cada Transição
Anual", fechando 6.3. Assim o quadro novo vira **Quadro 12** e **nada é
renumerado** — figuras e quadros existentes ficam como estão.

**Título sugerido da subseção:** *O Que Esses Números Significam em Seis Escolas*

### Parágrafo-guia (antes do quadro, no padrão do SS10)

> Os quadros anteriores resumem centenas de escolas em poucos números; este
> mostra o que eles significam caso a caso. O Quadro 12 traz seis escolas reais
> do teste do ano nunca visto — o modelo treinado com os pares de 2022 e 2023,
> prevendo 2024 sem conhecê-lo. Para cada uma: o abandono que de fato ocorreu, o
> que o modelo havia previsto e a posição da escola na lista de prioridade que o
> gestor receberia (1ª = risco mais alto, entre 789). As seis não são as vitrines
> do sistema: foram escolhidas para cobrir o espectro completo, do acerto quase
> exato ao pior erro.

### Quadro 12 — o modelo diante de seis escolas reais (teste 2023→2024)

| Escola (município) | Abandono observado em 2024 | Previsto pelo modelo | Posição na lista |
|---|---|---|---|
| Sagrada Família (Carnaubeira da Penha) | 16,7% | 16,4% | 9ª |
| Estadual Ororuba (Pesqueira) | 28,1% | 19,9% | 3ª |
| EREM Santos Dumont (Recife) | 0,0% | 0,2% | 579ª |
| Antônio Vieira de Barros (Salgueiro) | 0,0% | 1,3% | 101ª |
| Estadual Indígena José Luciano (Jatobá) | 0,0% | 19,0% | 6ª |
| EREF Coronel Othon (Recife) | 23,7% | 0,0% | 789ª (última) |

> Nota de rodapé sugerida: *Posição na lista = ordem decrescente da taxa
> prevista entre as 789 escolas do ano de teste; a lista de prioridade do
> capítulo corresponde às 79 primeiras posições. Fonte: elaborado pelo autor.*

### Parágrafo de leitura (depois do quadro — a tipologia que ele pediu)

> O quadro exibe os três comportamentos que os números agregados resumem. O
> primeiro é o caso típico, que o modelo acerta com folga: dois terços da rede
> (531 escolas) não registraram abandono em 2024, e para 92% delas a previsão
> ficou abaixo de 1% — a Santos Dumont e a Antônio Vieira de Barros são exemplos
> dos dois lados dessa margem. O segundo é a escola criticamente afetada com
> histórico de abandono, onde estão os maiores acertos: na Sagrada Família o
> modelo previu 16,4% para um abandono que foi de 16,7%; na Ororuba errou o
> valor (previu 19,9% para 28,1%), mas a colocou na 3ª posição da lista — e,
> para priorizar, é a posição que importa. O terceiro comportamento são os dois
> padrões de erro, e ambos têm cara conhecida. Nas escolas indígenas e
> quilombolas sem abandono o modelo superprevê o risco — a José Luciano recebeu
> previsão de 19,0% e não perdeu aluno algum; é o viés de −6,12 pontos
> percentuais tratado em Erros do Modelo e Equidade. E a escola que rompe com o
> próprio histórico fica invisível: a Coronel Othon não tinha registro de
> abandono, saltou para 23,7% em 2024, e o modelo a deixou na última posição da
> lista; na Maria Lúcia Alves (Santa Cruz do Capibaribe), a maior perda da rede
> em alunos, cerca de 154 estudantes saíram onde a previsão era de 0,7%. O
> modelo lê o passado registrado de cada escola; a ruptura que não deixou sinal
> prévio nos dados ele não tem como antecipar. É por isso que a lista é
> apresentada como apoio à decisão, e não como substituto da visita à escola.

## Proposta 3 — régua de julgamento no Quadro 11

Duas opções, em ordem de preferência:

**Opção A (recomendada — só texto):** acrescentar uma frase-guia no início do
parágrafo de leitura do Quadro 11 (¶435):

> Para julgar esses números, a régua é dupla: uma escolha ao acaso acertaria
> cerca de 10% da lista, e repetir a média da rede não ordenaria escola alguma.
> Lido assim, 0,627 significa que, de cada cem escolas apontadas na transição
> 2022→2023, 63 estavam de fato entre as mais críticas — contra dez do acaso.

**Opção B (mexe na tabela):** adicionar ao Quadro 11 uma linha "Escolha ao
acaso" com o Precision@K esperado (~0,10 em cada cenário). Custo: o Quadro 11 é
validado linha a linha pelo notebook 15, que precisaria de atualização, e a
tabela ganharia uma linha de natureza diferente das demais. A Opção A entrega o
mesmo efeito sem esse custo.

---

## Decisões que dependem do autor (antes de aplicar)

1. **Nomear ou anonimizar as escolas.** Os nomes são dados públicos do INEP e a
   monografia já nomeia uma escola (Figura 19 — a mesma José Luciano deste
   quadro, aliás, o que cria uma ligação útil entre as duas seções). Mas expor
   nominalmente os piores erros é escolha editorial: a alternativa "Escola A
   (Recife)" preserva o efeito didático. **Recomendação: nomear** — o quadro
   ganha concretude e a banca pode conferir os dados no INEP.
2. **Posição da subseção.** A proposta evita renumeração colocando o Quadro 12
   ao fim de 6.3. Se preferir o quadro *antes* dos Quadros 9–11 (didaticamente
   defensável), toda a numeração de quadros a partir do 9 muda — não recomendo a
   esta altura.
3. **Registrar o comentário como SS14** no `COMENTARIOS_ORIENTADOR.md` ao aplicar.

## Governança de números (obrigatório ao aplicar)

Todo valor citado acima precisa de checagem no notebook 15 antes de entrar no
`.docx`. Adicionar um bloco "Quadro 12 / SS14" que confira, contra
`residuos_grupo_temporal.csv` e `residuos_transicoes_alunos.csv`:

- as 6 linhas do quadro (observado, previsto, posição) — recalculando a posição
  pela ordenação do próprio CSV;
- 531 escolas com abandono zero (67% de 789) e 92% delas previstas abaixo de 1%;
- os casos citados só no texto: Maria Lúcia Alves (14,0% observado, 0,7%
  previsto, ≈154 alunos) e a ligação José Luciano ↔ Figura 19;
- a coerência com números já validados: −6,12 p.p. (equidade) e lista de 79.

Observação de exibição: a previsão bruta da Coronel Othon é −0,1% (o modelo
pode produzir valores levemente negativos); exibir como 0,0% no quadro, a mesma
regra do modo de predição em produção (`src/models/predict.py:55`,
`risco.clip(min=0)`).

Depois de aplicar: `/validar-numeros` e `/validar-documento` (numeração 1–12 e
lista de quadros no Word via F9).
