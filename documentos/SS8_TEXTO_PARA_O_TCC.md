# SS8 — Texto e números para inserir no Capítulo 6

Resultado da auditoria da coluna "Reprovação no ano anterior (Ensino Médio)" e da
correção implementada no pipeline. Este arquivo reúne o que precisa ser levado ao
`.docx`; a inserção em si fica para a **Fase 4** (redação), que reescreve essa
seção por inteiro.

---

## 1. Nota de rodapé do Quadro 5 (obrigatória)

> As taxas de Ensino Médio publicadas pelo INEP agregam a 1ª, 2ª e 3ª séries, a 4ª série
> e a matrícula não seriada (EJA e organização modular). Por isso o valor da rede pode
> superar o máximo observado em qualquer série isolada: o máximo de 55,3% corresponde a
> uma escola cuja matrícula de Ensino Médio é integralmente não seriada. As 283
> observações nessa situação (17,8% do conjunto) estão identificadas pelo atributo
> "Oferta de EM fora das séries regulares", no Quadro 6.

## 2. Frase de contexto, no parágrafo que antecede o Quadro 5

> Nas escolas cuja matrícula de Ensino Médio não se organiza em séries regulares, os
> valores por série são estimados pela média da mesorregião no mesmo ano; o atributo do
> Quadro 6 sinaliza esse subgrupo, de modo que a estimativa não seja lida como
> observação.

## 3. Linha nova no Quadro 6

Inserir entre "Auditório" e "Sala de leitura" (a tabela é ordenada por diferença
decrescente em valor absoluto):

| Atributo | % das escolas que têm | Abandono médio — têm | Abandono médio — não têm | Diferença (p.p.) |
|---|---|---|---|---|
| Oferta de EM fora das séries regulares (EJA/modular) | 17,8% | 1,49% | 1,04% | 0,45\*\*\* |

## 4. Contagens a atualizar no texto corrido

O conjunto passou de 38 para **39** características. Ocorrências a corrigir:

| Onde | Antes | Depois |
|---|---|---|
| 6.2.1, fim do parágrafo | "38 informações e nenhuma lacuna" | "39 características e nenhuma lacuna" |
| 6.2.3, 1º parágrafo | "Cada uma das 38 informações" | "Cada uma das 39 características" |
| 6.2.3, 1º parágrafo | "14 são de sim ou não" | "15 são de sim ou não" |
| Título do Quadro 6 | "as 14 informações de sim ou não" | "as 15 características de sim ou não" |
| Legenda da Figura 9 | idem | idem |
| Seção 6.2.4 (relação geral) | "de 38" | "30 de 38 → 30 de 38" *(conferir: 30 significativas de 38 numéricas — a contagem de numéricas passou de 37 para 38)* |

> A troca "informações" → "características" é o comentário **SS7** (Fase 2) e vale para
> o documento inteiro; aqui só ficam registradas as contagens que mudaram por causa do SS8.

## 5. Números do Quadro 5 — sem alteração

Os valores auditados batem exatamente com o pipeline e **permanecem como estão**:

| | Média | Desvio-padrão | Mínimo | Mediana | Máximo | Relação |
|---|---|---|---|---|---|---|
| Reprovação no ano anterior (Ensino Médio) | 4,55 | 4,68 | 0,00 | 3,50 | 55,30 | 0,18\*\*\* |

O que mudou foi a explicação, não o número.

---

## 6. Achado colateral — Quadro 8 não é reprodutível no ambiente atual

Ao reexecutar os notebooks, as métricas do Quadro 8 mudaram. **A causa não é a
correção do SS8.** Verificação controlada (mesmos hiperparâmetros, dataset com e sem o
novo atributo, 20 repetições pareadas):

| Modelo | Métrica | Sem o atributo | Com o atributo | Δ | p pareado |
|---|---|---|---|---|---|
| Ridge | Spearman | 0,402 | 0,402 | +0,000 | 0,452 |
| Random Forest | Spearman | 0,431 | 0,431 | +0,000 | 0,076 |
| XGBoost | Spearman | 0,415 | 0,416 | +0,001 | 0,083 |

Nenhuma diferença significativa. Além disso, o modelo sem sistema (média da rede) —
que depende **apenas** da partição, não de features — também mudou:

- Folds do commit anterior: `[2,408 · 3,653 · 1,828 · 4,633 · 4,059]`
- Folds reproduzidos agora: `[2,524 · 3,305 · 3,967 · 3,053 · 4,228]`
- Reproduzidos com e sem o atributo: **idênticos entre si**

Ou seja, a partição da validação cruzada mudou de ambiente, não de dados. A causa
provável é a versão do scikit-learn (1.8.0 instalada; `requirements.txt` pede apenas
`>=1.3`, e o `GroupKFold` foi reimplementado nesse intervalo).

**Consequência para o TCC:** os números do Quadro 8 atualmente no documento foram
gerados por um ambiente que não é mais o instalado. O modelo adotado deixou de ser o
melhor em ordenação (Spearman caiu de 0,458 para 0,416; o Random Forest agora lidera
com 0,431), o que contraria a frase "O modelo adotado alcança o melhor acerto de
ordenação de todos", na seção 6.3.2.

Isso precisa ser resolvido junto com o **SS13** (Fase 3), que já vai reescrever essa
seção. Duas saídas:

1. **Fixar o ambiente** (`requirements.txt` com versões exatas) e regerar o Quadro 8 —
   e então reavaliar se o XGBoost segue sendo a escolha defensável.
2. **Adotar os números novos** e reescrever a conclusão da seção 6.3.2 reconhecendo que
   os três modelos empatam dentro do intervalo de confiança — leitura que, aliás, os
   intervalos sempre sustentaram.

Recomendo a **1**, com a **2** como redação de fecho: fixar o ambiente é requisito de
reprodutibilidade de qualquer forma.

### Quadro 8 recalculado no ambiente atual

| Modelo | Erro médio da taxa (p.p.) | Acerto da ordenação (0 a 1) | Acerto na lista prioritária |
|---|---|---|---|
| Sem sistema (média da rede) | 3,154 | — | 0,068 |
| Modelo de referência linear | 2,628 | 0,428 | 0,513 |
| Modelo de referência em árvores | 2,546 | 0,431 | 0,501 |
| Modelo adotado | 2,597 | 0,416 | 0,504 |

---

## 7. Observação sobre o poder preditivo do novo atributo

O atributo é **estatisticamente significativo** na análise descritiva (diferença de
+0,45 p.p. no abandono médio, p < 0,001), mas sua importância SHAP no modelo final é
**zero** — o XGBoost não o utiliza. Isso é esperado e vale registrar no texto: a
informação que ele carrega já está contida nas taxas por série. Ele entra por
**transparência metodológica**, não por ganho preditivo — exatamente como o IED e o ICG,
que a seção 6.2.4 já trata dessa forma.
