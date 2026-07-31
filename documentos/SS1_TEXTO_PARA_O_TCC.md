# SS1 — Texto e números para inserir no Capítulo 6

**Comentário:** *"nao fica claro porque reduziu de 2392 para 1586"* (seção 6.2.1, p. 31).

Resultado da auditoria e da correção implementada. A inserção no `.docx` fica para a
**Fase 4** (redação), que reescreve essa seção por inteiro.

---

## 1. Diagnóstico

O orientador está certo: o texto atual apresenta os dois números em frases seguidas, sem
nada entre eles que explique a passagem. Lê-se como se 806 observações tivessem sido
descartadas por algum problema de qualidade — e não foi isso que aconteceu.

**A redução não é perda de amostra. É a estrutura de pares.**

O sistema aprende com pares: os atributos da escola no ano *t* e o abandono observado em
*t+1*. Com três anos de painel (2022, 2023, 2024) só se formam **dois** pares por escola
— 2022→2023 e 2023→2024. O ano de 2024 não desaparece: ele entra como **alvo** das
linhas de 2023, e não como origem. Chamar isso de "redução" é o que confunde; o dado de
2024 é usado, apenas do outro lado da equação.

## 2. Quadro novo, a inserir na seção 6.2.1

**Quadro X — Do painel histórico ao conjunto usado na previsão**

| Etapa | Critério | Linhas | Escolas |
|---|---|---|---|
| Painel histórico escola × ano | Escolas estaduais de EM em atividade, 2022 a 2024 | 2.392 | 806 |
| Anos que podem servir de origem (*t* = 2022, 2023) | O ano de 2024 não tem 2025 para observar: entra como alvo, não como origem | −791 → **1.601** | 804 |
| Pares completos (*t* → *t+1*) | Escola sem abandono observado no ano seguinte — saiu da rede ou deixou de ofertar Ensino Médio | −15 → **1.586** | 801 |

*Fonte: elaborado pelo autor.*

Gerado por `src/features/build_features.py::rastrear_reducao_amostra()` e persistido em
`reports/rastreabilidade_amostra.csv` — os números do quadro não são transcritos à mão.

## 3. Parágrafo a inserir logo após o Quadro X

> A diferença entre os dois totais não decorre de descarte por qualidade. O sistema
> aprende com pares: os atributos da escola em um ano e o abandono observado no ano
> seguinte. Com três anos de painel formam-se apenas dois pares por escola — 2022 para
> 2023 e 2023 para 2024 —, de modo que as 791 linhas de 2024 não servem de origem, por
> não haver 2025 a observar. Elas não são perdidas: são justamente o alvo das linhas de
> 2023. Descontadas essas, restam 1.601 pares potenciais, dos quais 15 não se completam
> porque a escola não aparece no ano seguinte, tendo saído da rede ou deixado de ofertar
> Ensino Médio. Chega-se assim às 1.586 observações de escola e ano usadas na previsão.

## 4. Detalhamento das 15 exclusões

Se a banca pedir o detalhe, a composição é esta:

| Ano de origem | Linhas sem par | Motivo |
|---|---|---|
| 2022 | 3 | Escolas presentes apenas em 2022 — ausentes já em 2023 |
| 2023 | 12 | Escolas presentes em 2022 e 2023 — ausentes em 2024 |

Efeito sobre a contagem de escolas: das 806 do painel, **5 não geram nenhum par** — as 3
que só aparecem em 2022 e as 2 que só aparecem em 2024 (estas últimas removidas na etapa
anterior, por 2024 nunca ser ano de origem). Restam **801 escolas**.

## 5. Conexão com os 97,4% já citados no texto

A frase atual — *"806 escolas, 97,4% delas presentes nos três anos"* — está correta e se
encaixa bem aqui, porque é a mesma informação vista pelo outro lado. A composição
completa do painel:

| Presença no painel | Escolas | % |
|---|---|---|
| Nos três anos (2022, 2023, 2024) | 785 | 97,4% |
| Só em 2022 e 2023 | 12 | 1,5% |
| Só em 2023 e 2024 | 4 | 0,5% |
| Só em 2022 | 3 | 0,4% |
| Só em 2024 | 2 | 0,2% |
| **Total** | **806** | **100%** |

Sugestão de redação: mover a menção aos 97,4% para **depois** do Quadro X, ligando as
duas informações — a alta permanência no painel é exatamente o que garante que quase
toda escola contribua com os dois pares.

## 6. Conferência aritmética por ano

| Ano de origem | Linhas no painel | Sem par | Linhas no conjunto final |
|---|---|---|---|
| 2022 | 800 | 3 | 797 |
| 2023 | 801 | 12 | 789 |
| 2024 | 791 | — (não é ano de origem) | 0 |
| **Total** | **2.392** | **15** | **1.586** |

## 7. O que mudou no código

| Arquivo | Mudança |
|---|---|
| `src/features/build_features.py` | Nova função `rastrear_reducao_amostra()`, que reconstrói a cadeia etapa a etapa, e `salvar_rastreabilidade()`, que a persiste |
| `src/features/build_features.py` | O entry-point passa a imprimir o rastro ao final da execução |
| `tests/test_rastreabilidade_amostra.py` | 6 testes novos: travam a aritmética entre etapas, a coincidência da última etapa com o parquet gravado, e a garantia de que o ano mais recente nunca sobra como origem (seria vazamento temporal) |
| `reports/rastreabilidade_amostra.csv` | Arquivo novo — fonte dos números do Quadro X |

Suíte: **114 testes passam** (eram 108 após o SS12).

## 8. Nenhum número anterior estava errado

Os dois totais citados no texto — 2.392 e 1.586 — foram conferidos contra o pipeline e
estão corretos. Faltava o caminho entre eles.
