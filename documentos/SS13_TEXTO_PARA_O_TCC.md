# SS13 — Texto e Quadro para a seção 6.3.2

Atende ao comentário do orientador:

> *"mostre a comparação usando 1 modelo e dois cenários: 2022 prevendo 2023 e
> 2023 prevendo 2024."*

O teste temporal que já constava do capítulo (Quadro 10) treina o modelo no par
2022→2023 e o aplica ao par 2023→2024 de uma vez só. O SS13 pede a **decomposição
das duas transições anuais**, para um **único modelo** — o adotado (XGBoost). Este
material entrega o experimento pronto, com os números verificados no ambiente de
referência (Python 3.14, scikit-learn 1.8.0), reproduzível.

- **Código:** `notebooks/14_ss13_cenarios_temporais.py`
- **Dados por repetição:** `reports/metricas_ss13_cenarios.csv`
- **Figura:** `reports/figuras/E9_ss13_cenarios.png` (numerar como figura no Word)

---

## 1. Como o experimento foi montado (parágrafo de método, antes do Quadro)

> Para examinar se o desempenho se sustenta de um ano para o outro, o modelo
> adotado foi avaliado nos dois cenários anuais em separado. No primeiro cenário
> ele usa as características de 2022 para prever o abandono de 2023; no segundo,
> usa as de 2023 para prever o de 2024. Em cada cenário, o desempenho é medido
> fora da amostra: a cada uma das vinte repetições, 20% dos municípios daquele
> ano são retirados do treino e reservados para teste, exatamente como no Quadro
> 9 — a diferença é que ali as duas transições foram avaliadas juntas e aqui elas
> aparecem isoladas. É sempre o mesmo modelo; muda apenas o ano de referência.

## 2. Quadro novo — um modelo, dois cenários

**Título:** Desempenho do modelo adotado em cada transição anual (média ± intervalo
de confiança de 95% sobre 20 repetições).

| Indicador de desempenho | Cenário 2022 → 2023 | Cenário 2023 → 2024 |
|---|---|---|
| Erro médio da taxa, em pontos percentuais (RMSE) — *menor é melhor* | 2,82 ± 0,34 | 2,16 ± 0,26 |
| Acerto da ordenação, de 0 a 1 (Spearman) — *maior é melhor* | 0,469 ± 0,039 | 0,367 ± 0,032 |
| Acerto na lista prioritária, top 10% (Precision@K) — *maior é melhor* | 0,627 ± 0,060 | 0,381 ± 0,041 |
| Separação entre alto e baixo risco (ROC-AUC) — *maior é melhor* | 0,901 ± 0,035 | 0,813 ± 0,019 |

> Nota de rodapé sugerida: *As características de cada ano preveem o abandono do ano
> seguinte; o abandono médio da rede foi 1,36% na transição 2022→2023 e 0,88% na
> transição 2023→2024. Cada célula resume vinte repetições em que 20% dos municípios
> ficaram fora do treino.*

## 3. Parágrafo de leitura (depois do Quadro)

> O modelo mantém utilidade nas duas transições, mas rende mais na primeira. Na
> transição 2022→2023, entre as escolas que ele coloca no topo da lista prioritária,
> 63% estão de fato entre as de maior abandono; na transição 2023→2024, esse acerto
> cai para 38% — ainda muito acima dos cerca de 10% que uma escolha ao acaso
> alcançaria. A queda acompanha a própria mudança da rede: o abandono médio caiu de
> 1,36% para 0,88% e as escolas se concentraram mais perto de zero, o que ao mesmo
> tempo reduz o erro absoluto (há menos a errar) e comprime o sinal que permite
> ordenar as escolas (mais empates perto de zero tornam a ordenação mais difícil).
> Mesmo no cenário mais difícil, a capacidade de separar as escolas de alto risco
> das demais permanece alta (0,81 numa escala em que 0,5 é o acaso). Os dois
> cenários, tomados em conjunto, cercam os valores do Quadro 9, que avalia as duas
> transições agregadas — sinal de que a decomposição é coerente com o desempenho
> global, e não um artefato de um ano específico.

## 4. Ligação com o restante da seção

- **Não substitui** o Quadro 10 (teste temporal prospectivo 2022–2023 → 2023–2024):
  aquele responde "treinado no passado, o modelo acerta o futuro?"; este responde
  "o desempenho é parecido em cada ano isolado?". São complementares.
- O achado reforça a ressalva de equidade e magnitude já registrada no capítulo: o
  desempenho de ordenação é sensível ao nível de abandono do ano, mais alto quando
  há mais evasão para distinguir.

---

## 5. Observações de reprodutibilidade (para o autor, não vai ao texto)

- O experimento foi rodado **duas vezes**, sob scikit-learn 1.9.0 e sob 1.8.0
  (o ambiente de referência do `requirements.txt`): os números foram **idênticos**.
  Ao contrário do `GroupKFold` — que mudou de partição entre versões e obrigou a
  regenerar os Quadros 9 e 10 —, o `GroupShuffleSplit` usado aqui é estável entre
  as duas versões. O SS13, portanto, não herda a fragilidade que travou a pendência
  do ambiente.
- **Deriva encontrada e corrigida nesta sessão:** o venv estava com
  scikit-learn 1.9.0, mas o `requirements.txt` fixa 1.8.0. Reinstalei a 1.8.0 para
  alinhar ao ambiente de referência antes de gerar os números finais. Fica um alerta:
  o `shap` no venv está em 0.52.0, e o `requirements.txt` pede 0.51.0 — isso não
  afeta nenhum número deste quadro nem dos Quadros 9/10 (o SHAP só entra no
  notebook 09), mas convém alinhar antes de regerar as figuras do SHAP.
