# Por que o XGBoost é o modelo adotado — justificativa para a defesa

Preparado em 10/08/2026. Todos os números saem de artefatos do pipeline
(`reports/metricas_cv_repetida.csv`, `reports/metricas_xgboost.csv`,
`reports/metricas_ss13_cenarios.csv`, `reports/residuos_grupo_temporal.csv`) e
conferem com a varredura do notebook 15 (136 OK, 0 divergências, 10/08/2026).
Onde o texto da monografia trata do tema: ¶291 (apresentação dos concorrentes),
¶416 (Quadro 9), ¶427–¶430 (Quadro 10 e justificativa), ¶498 (conclusão).

---

## 1. O contexto que torna a pergunta legítima

A escolha do XGBoost **não é imposta pelos números** — o próprio texto da
monografia diz isso (¶430). Os três modelos avaliados são estatisticamente
indistinguíveis: os intervalos de confiança das 20 repetições se sobrepõem em
todas as métricas. A floresta aleatória empata ou supera o XGBoost em vários
pontos. Quem defende a escolha precisa saber exatamente onde cada um ganha.

## 2. Os números lado a lado

**Validação repetida** (20 repetições, 20% dos municípios fora do treino — Quadro 9):

| | RMSE (p.p.) | Spearman | Precision@K |
|---|---|---|---|
| Sem sistema (média da rede) | 3,154 | — | 0,068 |
| Regressão Ridge | 2,628 | **0,428** | **0,513** |
| Floresta aleatória | **2,546** | **0,431** | 0,501 |
| XGBoost (adotado) | 2,597 | 0,416 | 0,504 |

**Teste do ano nunca visto** (treino 2022–2023, teste 2023–2024 — Quadro 10):

| | RMSE (p.p.) | Spearman | Precision@K | ROC-AUC |
|---|---|---|---|---|
| Sem sistema (média da rede) | **2,540** | — | 0,089 | — |
| Regressão Ridge | 2,891 | 0,330 | 0,380 | 0,812 |
| Floresta aleatória | 2,751 | 0,343 | 0,405 | **0,829** |
| XGBoost (adotado) | 2,874 | **0,348** | **0,418** | 0,798 |

Leitura honesta: na validação repetida o XGBoost fica **atrás** dos dois
concorrentes em Spearman; no teste temporal ele lidera as duas métricas de
ordenação **por margem pequena** e perde em RMSE e ROC-AUC para a floresta
aleatória. Nenhum modelo supera o piso trivial no RMSE do teste temporal.

## 3. Os três motivos da escolha

### Motivo 1 — lidera onde o propósito exige, no cenário que simula o uso real

O sistema existe para **priorizar**: ordenar escolas por risco e montar a lista
de atendimento. As métricas que respondem a isso são Spearman (ordem) e
Precision@K (acerto da lista) — não RMSE nem ROC-AUC. E o protocolo que
reproduz o uso real é o teste do ano nunca visto: treinar no passado, prever um
ano que o modelo nunca viu. **Nesse cenário e nessas métricas, o XGBoost é o
primeiro colocado** (0,348 e 0,418): das 79 escolas que coloca no topo da
lista, 33 estavam de fato entre as de maior abandono, contra 7 da escolha ao
acaso — ganho de 4,7×. A vantagem da floresta aleatória está em RMSE e ROC-AUC,
dimensões menos centrais para a decisão de onde intervir primeiro.

### Motivo 2 — a camada de explicação foi construída e validada sobre ele

Toda a camada de transparência do sistema — importância global, direção dos
efeitos, explicação individual por escola (Figuras 17–19), a ressalva de
equidade exibida no painel — é SHAP calculado sobre o XGBoost, com a
aditividade das explicações travada por teste automatizado
(`tests/test_explain.py`). Trocar o modelo adotado exigiria reconstruir e
revalidar essa camada inteira em troca de um ganho que os intervalos de
confiança não confirmam.

### Motivo 3 — o empate torna a escolha sem custo

Como as diferenças entre os três ficam dentro da margem de incerteza, adotar o
XGBoost **não representa perda de desempenho relevante** em nenhuma métrica.
O argumento é assimétrico: não há razão estatística para trocar, e há razões
operacionais (motivos 1 e 2) para manter.

## 4. O que NÃO se pode alegar

A banca pode cobrar qualquer uma destas afirmações — nenhuma delas é verdadeira
e nenhuma está no texto:

- ~~"O XGBoost é o melhor modelo em geral."~~ Falso: empate estatístico; a
  floresta aleatória vence em RMSE (nos dois protocolos), em ROC-AUC e no
  Spearman da validação repetida.
- ~~"O sistema prevê bem o valor da taxa."~~ Falso: no teste temporal o RMSE do
  XGBoost (2,874) é **pior que o do piso trivial** (2,540) e o R² é negativo
  (−0,33). O abandono médio da rede caiu entre os ciclos (1,36% → 0,88%) e
  nenhum modelo acompanhou o nível. O valor do sistema está na **ordem**, não
  na magnitude — a analogia do texto: termômetro descalibrado que ainda aponta
  quem tem mais febre.
- ~~"O desempenho é estável entre anos."~~ Parcial: o acerto da lista caiu de
  0,627 (2022→2023) para 0,381 (2023→2024), acompanhando a queda do abandono
  médio (Quadro 11). Segue muito acima do acaso (~0,10) nas duas transições.
- ~~"O modelo é neutro entre grupos de escolas."~~ Falso: superprediz o risco
  das escolas de localização diferenciada em **−6,12 p.p.** em média, enquanto
  urbanas (+0,07) e rurais (+0,38) ficam calibradas. A ressalva acompanha toda
  saída ao gestor (`service.ressalva_equidade()`).

## 5. Perguntas prováveis e respostas curtas

**"Por que não a floresta aleatória, se ela ganha em vários pontos?"**
Porque os pontos em que ela ganha (RMSE, ROC-AUC) não são o propósito do
sistema, e os pontos em que o XGBoost ganha (ordenação e lista no teste
temporal) são exatamente o que a Secretaria usaria. Somado a isso, a camada
SHAP está construída e testada sobre o XGBoost. E como o empate é estatístico,
a troca não traria ganho mensurável.

**"Com intervalos sobrepostos, a escolha não é arbitrária?"**
É uma escolha entre equivalentes, decidida por critérios operacionais
explícitos — e o texto declara isso em vez de esconder (¶430: "a escolha não é
imposta pelos números"). Arbitrário seria alegar superioridade que os dados não
mostram.

**"O RMSE pior que o piso trivial não invalida o sistema?"**
Invalidaria se o objetivo fosse prever o valor da taxa. O objetivo é montar a
lista de prioridade: no mesmo teste, a lista do sistema acerta 4,7× mais que o
acaso. Responder "zero para todas as escolas" teria RMSE ótimo e utilidade
nula — é o argumento da conclusão (¶500). A limitação de magnitude vem da
janela curta (dois pares de anos) e está registrada nas limitações.

**"Por que o gradiente impulsionado, do ponto de vista da literatura?"**
Métodos de árvores dominam dados tabulares como os deste trabalho; o gradiente
impulsionado costuma superar florestas aleatórias nesse regime (Chen &
Guestrin, 2016 — referência do texto, ¶258). A configuração adotada foi
escolhida por busca sistemática entre 48 combinações, deliberadamente contida
(passos pequenos, complexidade penalizada) para uma base de treino com menos de
800 observações.

**"Esses números são estáveis? Já mudaram alguma vez?"**
Já — e essa história fortalece a resposta. Ao regenerar os quadros no ambiente
fixado, a linha do XGBoost mudou (Spearman de CV de 0,458 para 0,416) por
efeito da versão da biblioteca xgboost (3.2.0), e o modelo deixou de liderar
com folga. O texto foi **reescrito para o empate honesto** naquele momento, a
escolha foi reavaliada e mantida pelos motivos acima, e o `requirements.txt`
passou a fixar todas as versões com `==`. A varredura automática (notebook 15)
confere hoje 136 números do documento contra os artefatos, com zero
divergências.

## 6. Fontes

| Número | Artefato |
|---|---|
| Quadro 9 (CV repetida, ICs) | `reports/metricas_cv_repetida.csv` |
| Quadro 10 (teste temporal) | `reports/metricas_xgboost.csv` |
| Quadro 11 (transições anuais) | `reports/metricas_ss13_cenarios.csv` |
| Equidade (−6,12 / +0,07 / +0,38) | `reports/residuos_grupo_temporal.csv` |
| 33 de 79 na lista; 4,7× | recalculado no notebook 15, seção 6 |
| Aditividade SHAP | `tests/test_explain.py` (suíte com 138 testes) |
