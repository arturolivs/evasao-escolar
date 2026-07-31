---
name: validar-escrita
description: Valida a qualidade da escrita da monografia — sintaxe e norma PT-BR, conformidade ABNT (citações, referências, citação longa, formatação), clareza e linguagem direta, e marcadores de escrita automática com sugestões de humanização. Usar quando pedirem revisão de texto, revisão de português, checagem de ABNT ou de referências, avaliação de clareza/linguagem acadêmica, ou quando quiserem saber se o texto "parece escrito por IA" e como torná-lo mais autoral.
---

# Validar a Escrita da Monografia

Avalia **como o texto está escrito**. Divisão de trabalho com as skills irmãs:

| Skill | Cuida de |
|---|---|
| `/validar-escrita` | sintaxe, ABNT, clareza, autoria — **esta** |
| `/validar-documento` | estrutura: numeração de figuras/quadros, terminologia, placeholders |
| `/validar-numeros` | se cada número do texto bate com o artefato que o gera |

## Execução

A partir da **raiz do repositório** (`monografia/`):

```bash
python .claude/skills/validar-escrita/analisar_escrita.py
```

Opções:

```bash
--doc "documentos/outro.docx"     # outro arquivo (padrão: TCC_Evasao_Escolar.docx)
--bloco ritmo|sintaxe|clareza|abnt|ia    # roda um bloco só
```

O script separa automaticamente o que **não** é texto corrido — legendas, `Fonte:`,
sumário, lista de referências, apêndices e os parágrafos em inglês (Abstract/Keywords) —
e delimita os pré-textuais pelo primeiro `Heading 1`. Sem isso, o título de uma referência
em inglês viraria "jargão" e a epígrafe viraria "primeira pessoa indevida".

## Linha de base verificada

Rodado no documento atual. Use para detectar regressão.

| Bloco | Resultado |
|---|---|
| **1. Ritmo** | 150 parágrafos · 478 frases · 22,2 palavras/frase (dp 13,1) · variação **0,59** |
| **2. Sintaxe PT-BR** | **0 ocorrências** em 11 regras · voz passiva 11% (voz ativa predominante) |
| **3. Clareza** | nominalizações **4,4%** (bom) · **0 candidatos a troca de jargão** · 10 frases com «que» encadeado |
| **4. ABNT** | margens = modelo PUC-SP · 24 referências (todas com PDF) · **0 órfãs, 0 não citadas** · ordem alfabética ok |
| **5. Marcadores de IA** | **0 indícios** em 8 medidas |

Pontos abertos que a linha de base registra:

- **50 frases com ≥ 40 palavras (10,5%)**, sendo 8 acima de 55. As maiores: ¶179 (71),
  ¶352 (68), ¶285 (64), ¶452 (61), ¶461 (61). O ¶179 é o Resumo, gênero de frase densa;
  o ¶352 é a cadeia de ponto-e-vírgula que imita a sequência do pipeline — ambos
  deliberados, não defeitos.
- **Jargão: zerado.** «boosting» solto (¶285, ¶288) passou a "gradiente impulsionado" e
  «ranking» (¶332) a "lista devolvida". Seguem legítimos, e contados como tal, a glosa
  «gradiente impulsionado (gradient boosting)» em ¶283 e o identificador `src.features`.
- **10 frases com 3+ «que»**, hoje no máximo 4× (¶256, ¶498, ¶510).
- O parágrafo-glossário de 245 palavras (antigo ¶398) virou cinco parágrafos de 44, 37,
  61, 67 e 32 palavras — ¶398 a ¶402.

## Como os blocos funcionam

### 1. Ritmo e legibilidade
Palavras por frase, desvio-padrão, frases longas e parágrafos longos. O número que
importa é a **variação (dp/média)**: texto humano oscila entre frase curta e longa;
geração automática tende ao ritmo uniforme.

### 2. Sintaxe e norma PT-BR
Onze regras de erro objetivo ou vício de estilo: espaço duplo, espaço antes de pontuação,
gerundismo, «o mesmo» como pronome, «através de», «a nível de», «enquanto que», primeira
pessoa no corpo, coloquialismo, «onde» em oração relativa. Mais a taxa de voz passiva.

As regras foram **calibradas para não gritar à toa**. Ex.: «o mesmo» só acende quando
substitui substantivo (`o mesmo foi…`), não no uso adjetivo legítimo (`o mesmo critério`);
«onde» só na oração relativa `, onde …`, não em `mostra onde agir`.

> Isto **não substitui** um corretor gramatical. Concordância, regência e crase exigem
> análise sintática que regex não faz — passar o texto pelo revisor do Word continua
> sendo necessário.

### 3. Clareza, simplicidade e direção
- **Nominalizações** (`-ção`, `-mento`, `-dade`): acima de ~9% o texto vira abstrato.
- **Jargão em inglês**, com a distinção que o comentário SS7 do orientador pede — glosa
  entre parênteses e identificador de código são legítimos; o resto é candidato a troca.
- **Perífrases** que alongam sem informar («no âmbito de», «faz-se necessário»…).
- **Encadeamento de «que»** e repetição de palavra significativa na mesma frase.

### 4. Conformidade ABNT
- **Margens**: comparadas ao `Modelo TCC Engenharia de Software 2022.docx`, **não** aos
  3/3/2/2 genéricos da NBR 14724. O modelo da PUC-SP usa 3,0/2,5/3,0/2,5 e é ele que a
  banca cobra — validar contra a norma genérica produziria 3 alarmes falsos.
- **Citações ↔ referências** nos dois sentidos: citação sem entrada e entrada não citada.
  A busca trata as armadilhas reais do padrão ABNT: `(CHAPMAN et al., 2000)` com «et al.»
  em minúscula, `(McKINNEY, 2010)` com grafia mista, e co-autores em `Ribeiro, Singh e
  Guestrin (2016)` — que não abrem entrada própria mas constam no corpo da referência.
- **Ordem alfabética** e ponto final das entradas.
- **Citação direta longa** (NBR 10520): busca recuo de 3,5–5,5 cm com texto substancial
  e confere fonte reduzida e entrelinha simples. A faixa exclui os blocos de 8 cm da folha
  de rosto, que não são citação. Também detecta citação longa ainda embutida no corpo.
- **Legenda acima / `Fonte:` abaixo**.

### 5. Marcadores de escrita automática

**Leia esta parte antes de usar o resultado.** Não existe detector confiável de texto
gerado — nem este, nem os comerciais. O que o bloco mede são padrões que modelos de
linguagem produzem acima da média humana, e que **também aparecem em texto acadêmico
formal escrito à mão**. O resultado é uma lista de revisão, nunca um veredito, e não deve
ser usado para afirmar ou negar autoria de ninguém.

Oito medidas: uniformidade do tamanho de frases e de parágrafos, densidade de conectores
formulaicos, adjetivos de reforço sem medida ao lado, listas de três termos, «não
apenas… mas também», travessões e aberturas de frase repetidas.

**Os limiares foram calibrados contra um controle.** Um parágrafo-teste escrito
deliberadamente no registro de LLM acende 5 dos 8 indícios com margens grandes —
conectores a 56,8 por mil contra 0,8 do documento real, variação de ritmo 0,11 contra
0,61. Ou seja: o bloco discrimina, não dá "ok" para tudo.

## Humanizar: o que de fato funciona

Se o bloco 5 acender vários indícios, estas são as intervenções em ordem de retorno.
Todas valem também para texto escrito à mão que ficou burocrático.

1. **Trocar abstração por episódio.** A marca mais forte de autoria não é estilo, é
   conteúdo que só quem fez o trabalho tem. Este projeto tem episódios de sobra:
   a partição do `GroupKFold` que mudou de versão e obrigou a regerar os Quadros 9 e 10;
   o IED e o ICG integrados e depois removidos por não ajudarem; o XGBoost que empata com
   o Ridge. Contar o que deu errado e o que se decidiu a respeito não é fraqueza — é o
   que nenhum gerador teria como inventar.
2. **Cortar o andaime.** «Além disso», «dessa forma», «nesse sentido», «vale ressaltar»:
   na maioria dos casos a frase seguinte se sustenta sozinha. Remova e leia de novo.
3. **Variar o comprimento.** Depois de duas frases longas, escreva uma de seis palavras.
   É o que mais move a métrica de ritmo, e o efeito na leitura é imediato.
4. **Substituir adjetivo por número.** «Desempenho robusto» → «acerto de 42% na lista das
   150 escolas, contra 19% ao acaso». O adjetivo é opinião; o número é resultado.
5. **Desfazer o tricolon automático.** Listas de três adjetivos («complexo, multifacetado
   e desafiador») quase sempre têm um termo que não acrescenta nada. Fique com um.
6. **Nomear o agente.** «Foram realizados testes» → «a suíte roda 132 testes». Voz ativa
   diz quem fez o quê e encurta a frase.
7. **Ler em voz alta.** O item 5.3 do `PLANO_DE_FINALIZACAO.md` já pede isso, e continua
   sendo o filtro que pega o que nenhuma métrica pega: onde você tropeça, o leitor também.

## Ao corrigir o `.docx`

1. **Backup antes**, na convenção do projeto: `TCC_ANTES_<ASSUNTO>.docx` em `documentos/`.
2. Marcar o texto novo em azul `1F4E9B` + realce amarelo, como nas rodadas anteriores —
   é assim que o autor revisa o que mudou.
3. Não tocar nas pendências que dependem do autor: ficha catalográfica, banca,
   agradecimentos.
4. Se a edição mexer em qualquer número, rodar `/validar-numeros` depois.
5. Reescrever para "sair bem no detector" **não é** objetivo válido. O objetivo é texto
   mais claro e mais seu; a métrica é consequência, não meta.
