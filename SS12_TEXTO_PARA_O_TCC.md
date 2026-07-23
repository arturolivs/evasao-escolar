# SS12 — Texto e números para inserir no Capítulo 6

**Comentário:** *"a coluna abandono tem e abandono nao tem — devem somar 100% para
fazer sentido essa tabela"* (Quadro 6, p. 36).

Resultado da auditoria e da correção implementada. A inserção no `.docx` fica para a
**Fase 4** (redação), que reescreve essa seção por inteiro.

---

## 1. Diagnóstico

O orientador está certo sobre o efeito, e a causa é de apresentação, não de cálculo.

O Quadro 6 tem hoje quatro colunas de números, e elas misturam **duas grandezas
diferentes** sem sinalizar isso:

| Coluna | O que é | Soma 100%? |
|---|---|---|
| % das escolas que têm | reparte a rede em dois grupos | **sim** — falta a metade complementar |
| Abandono médio — têm | média do abandono dentro de um grupo | não |
| Abandono médio — não têm | média do abandono dentro do outro grupo | não |
| Diferença (p.p.) | subtração das duas médias | não se aplica |

As duas colunas de abandono são **médias de uma variável contínua** em subgrupos
distintos — duas leituras do mesmo termômetro, não fatias de um bolo. Somadas, dão
entre 2,01 e 9,65 conforme a linha, e não há razão para que dessem outra coisa.

A coluna que de fato reparte a rede é a primeira, mas ela aparece sozinha: mostra-se
"90,7% têm biblioteca" e nunca "9,3% não têm". Lendo os três números em sequência —
`90,7% | 0,93% | 3,01%` — a interpretação natural é que os três se referem a
proporções de escolas. Daí a leitura de que deveriam fechar em 100.

Dois agravantes:

- **Ausência das contagens.** Sem o `n`, não dá para ver que a média de 1,84% da coluna
  "não têm" na linha *Internet* repousa sobre **12 escolas**. O texto que antecede a
  tabela já alerta para isso ("praticamente não existe grupo de comparação"), mas a
  tabela não dá ao leitor como confirmar.
- **Quebra de linha nos cabeçalhos.** No PDF os títulos saem partidos — "Abandon o
  médio — têm", "Difer ença (p.p.)" —, o que dificulta ainda mais associar cada número
  à sua grandeza. É largura de coluna no Word, e precisa ser ajustada.

## 2. Correção proposta na tabela

Repartir os cabeçalhos em dois blocos, explicitar o grupo complementar e trazer as
contagens. Assim a soma 100% fica visível onde ela existe, e a ausência dela nas médias
deixa de surpreender.

**Quadro 6 — Repartição das escolas por atributo de sim ou não e abandono médio de cada grupo**

| Atributo | Escolas que têm | Escolas que não têm | Abandono médio se tem (%) | Abandono médio se não tem (%) | Diferença (p.p.) |
|---|---|---|---|---|---|
| Localização diferenciada (indígena/quilombola) | 81 (5,1%) | 1.505 (94,9%) | 8,95 | 0,70 | 8,25\*\*\* |
| Localização rural | 218 (13,7%) | 1.368 (86,3%) | 3,74 | 0,70 | 3,04\*\*\* |
| Biblioteca | 1.438 (90,7%) | 148 (9,3%) | 0,93 | 3,01 | −2,08\*\* |
| Laboratório de informática | 1.228 (77,4%) | 358 (22,6%) | 0,74 | 2,44 | −1,71\*\*\* |
| Banda larga | 1.393 (87,8%) | 193 (12,2%) | 0,95 | 2,34 | −1,39 |
| Quadra de esportes | 1.120 (70,6%) | 466 (29,4%) | 0,79 | 1,93 | −1,14\* |
| Laboratório de ciências | 705 (44,5%) | 881 (55,5%) | 0,53 | 1,59 | −1,06\*\*\* |
| Esgoto em rede pública | 952 (60,0%) | 634 (40,0%) | 0,74 | 1,70 | −0,96 |
| Água potável | 1.509 (95,1%) | 77 (4,9%) | 1,08 | 1,91 | −0,83 |
| Internet para alunos | 1.170 (73,8%) | 416 (26,2%) | 0,92 | 1,69 | −0,77\*\*\* |
| Internet | 1.574 (99,2%) | 12 (0,8%) | 1,12 | 1,84 | −0,73 |
| Refeitório | 511 (32,2%) | 1.075 (67,8%) | 0,73 | 1,31 | −0,58\* |
| Auditório | 438 (27,6%) | 1.148 (72,4%) | 0,75 | 1,26 | −0,52 |
| Oferta de EM fora das séries regulares (EJA/modular) | 283 (17,8%) | 1.303 (82,2%) | 1,49 | 1,04 | 0,45\*\*\* |
| Sala de leitura | 244 (15,4%) | 1.342 (84,6%) | 1,38 | 1,07 | 0,30 |

*Fonte: elaborado pelo autor.*

> A linha "Oferta de EM fora das séries regulares" vem do **SS8** — ver
> `SS8_TEXTO_PARA_O_TCC.md`. Todas as linhas somam 1.586 observações.

**Formatação no Word:** aumentar a largura das colunas 2 a 6 e reduzir o corpo da fonte
do cabeçalho, de modo que nenhum título quebre no meio de uma palavra.

## 3. Parágrafo explicativo, imediatamente antes do Quadro 6

Cobre o SS12 e serve também ao **SS10**, que pede explicação das colunas antes da
tabela aparecer.

> O Quadro 6 reúne duas leituras distintas de cada atributo, e vale distingui-las. As
> duas primeiras colunas repartem as 1.586 observações em dois grupos — as escolas que
> têm o atributo e as que não têm — e por isso se completam: somadas, dão o total da
> rede. As duas colunas seguintes são de outra natureza: cada uma traz a taxa média de
> abandono no ano seguinte **dentro** de um desses grupos. São duas médias do mesmo
> indicador, medidas em conjuntos diferentes de escolas, e não há razão para que se
> somem a 100% — o que interessa nelas é a distância entre uma e outra, registrada na
> última coluna. As contagens aparecem ao lado dos percentuais porque a comparação só
> se sustenta quando os dois grupos têm tamanho suficiente: em *Internet*, por exemplo,
> a média de quem não tem o atributo apoia-se em apenas 12 escolas.

## 4. Frase de ressalva, logo após o Quadro 6

Substitui e amplia o trecho atual sobre atributos quase universais:

> Atributos presentes em quase toda a rede não separam grupos porque não sobra
> comparação: internet está em 99,2% das escolas e água potável em 95,1%, restando 12 e
> 77 escolas do outro lado. As diferenças que essas linhas exibem não são
> estatisticamente distinguíveis do acaso, e não devem ser lidas como efeito do
> atributo.

## 5. Figura 9 — mesma correção

A figura tinha a mesma ambiguidade: o painel esquerdo mostrava só a fatia "têm". Foi
regenerada com **barra empilhada**, em que os dois grupos preenchem 100% da largura e
as contagens aparecem sobre as barras. O eixo passa a dizer, explicitamente,
"os dois grupos somam 100%"; o painel direito passa a dizer que traz "duas médias do
mesmo indicador, uma por grupo".

Arquivo regenerado: `reports/figuras/E6_binarias.png`.

Legenda sugerida:

> Figura 9 – Repartição das escolas por atributo de sim ou não (à esquerda) e taxa média
> de abandono de cada grupo (à direita)

## 6. O que mudou no código

| Arquivo | Mudança |
|---|---|
| `notebooks/13_estatisticas_features.py` | `descrever_binarias()` passa a devolver `n_tem`, `n_nao` e `pct_nao`, com docstring explicando por que as duas grandezas não se misturam |
| `notebooks/13_estatisticas_features.py` | `figura_binarias()` — painel esquerdo vira barra empilhada 100% com contagens; rótulos de eixo e título revisados |
| `tests/test_estatisticas_binarias.py` | 4 testes novos: travam `n_tem + n_nao = n` e `prevalencia + pct_nao = 100`, e verificam que as médias de abandono **não** são complementares |
| `reports/estatisticas_features.csv` | regenerado com as colunas novas |

Suíte: **108 testes passam** (eram 104 após o SS8).

## 7. Nenhum número anterior estava errado

Todos os valores já publicados no Quadro 6 foram conferidos contra o pipeline e
**permanecem idênticos**. O que muda é o que a tabela deixa o leitor ver: a repartição
completa, as contagens por trás de cada média, e a separação explícita entre o que soma
100% e o que não soma.
