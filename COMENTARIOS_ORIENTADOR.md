# Comentários do Orientador — TCC Evasão Escolar

Fonte: `TCC_Evasao_Escolar_comentários.pdf` (autor dos comentários: SS)
Extraídos em 22/07/2026. Todos os 13 comentários estão no **Capítulo 6 — Testes e Análise dos Resultados** (páginas 31–39).

**Status (24/07/2026): 13 de 13 concluídos.** O SS13 foi implementado e verificado
no ambiente de referência (código, números e texto prontos). Restam apenas os
ajustes manuais de acabamento no Word e a passagem de regeneração de figuras,
consolidados na seção [Pendências em aberto](#pendências-em-aberto).

---

## Lista de comentários

| # | Pág. | Seção / âncora | Comentário |
|---|------|----------------|------------|
| SS1 | 31 | 6.2.1 Base Construída | *"não fica claro porque reduziu de 2392 para 1586"* |
| SS2 | 32 | 6.2.2 O Que o Sistema Prevê | *"faltou citar a figura 7"* |
| SS3 | 32 | 6.2.2 (resposta a SS2) | *"precisa de um parágrafo para explicar esse gráfico"* |
| SS4 | 32 | 6.2.2 (resposta a SS2) | *"incluir na média valor do desvio padrão"* |
| SS5 | 32 | 6.2.2 — parágrafo "Daí decorre o critério…" | *"tá com cara de discussão, deveria ser falado depois de mostrar toda a análise estatística"* |
| SS6 | 32 | 6.2.2 (resposta a SS5) | *"reserve para conclusão do TCC"* |
| SS7 | 32 | 6.2.3 | *"troca informações por feature ou característica"* |
| SS8 | 33 | Quadro 5 | *"revisar essa coluna — Reprovação no ano anterior (Ensino Médio)"* |
| SS9 | 33 | Quadro 5 | *"o que é Adequação da formação docente — Grupo 1?"* |
| SS10 | 33 | Quadro 5 (resposta a SS9) | *"explicar as colunas dessa tabela, antes da tabela aparecer, imediatamente antes"* |
| SS11 | 33 | Quadro 5 (resposta a SS9) | *"ex: nível socioeconômico (INSE) é um valor que varia de 0 a 10, e indica o desenv. econômico da comunidade onde a escola está inserida"* |
| SS12 | 36 | Quadro 6 | *"a coluna abandono tem e abandono não tem — devem somar 100% para fazer sentido essa tabela"* |
| SS13 | 39 | 6.3.2 — Quadro 8 | *"mostre a comparação usando 1 modelo e dois cenários: 2022 prevendo 2023 e 2023 prevendo 2024"* |

### Agrupamento por natureza

- **Terminologia:** SS7
- **Rastreabilidade metodológica:** SS1, SS8, SS12
- **Didática de tabelas e figuras:** SS2, SS3, SS4, SS9, SS10, SS11
- **Reestruturação / novo experimento:** SS5, SS6, SS13

---

## Ordem de execução

### Fase 1 — Verificação factual ✅ **CONCLUÍDA**
*Primeiro de tudo: pode invalidar texto já escrito.*

> Resultado: **nenhum número do TCC estava errado**. Os três comentários apontavam
> falhas de apresentação e rastreabilidade, todas corrigidas no pipeline com testes.
> **`TCC_Evasao_Escolar.docx` já foi atualizado** com os três (backup em
> `TCC_Evasao_Escolar_ANTES_SS1_SS8_SS12.docx`).
> Pendência aberta: o Quadro 8 — agora **Quadro 9** — não é reprodutível no ambiente
> atual (ver SS8).
>
> ⚠️ **Os quadros foram renumerados**: o Quadro 5 novo (rastreabilidade da amostra)
> empurrou os demais. Antigo 5→6, 6→7, 7→8, 8→9, 9→10. Os comentários pendentes do
> orientador referem-se à numeração **antiga**.

- [x] **SS8** — ~~Auditar a coluna "Reprovação no ano anterior (EM)" no Quadro 5.~~ **Concluído.** Os números estavam corretos; o defeito era a incoerência entre a linha do EM e as das séries (o total do INEP inclui 4ª série e não seriado). Implementado o atributo `oferta_em_nao_seriado` no pipeline + testes. Texto e números para o documento em `SS8_TEXTO_PARA_O_TCC.md`.
  - ⚠️ Achado colateral: o Quadro 8 **não é reprodutível** no ambiente atual — a partição da CV mudou por versão de biblioteca, não pela correção. Resolver junto com o SS13 (Fase 3). Detalhes no mesmo arquivo.
- [x] **SS12** — ~~Reinterpretar o Quadro 6.~~ **Concluído.** Nenhum número estava errado; o defeito era a tabela misturar duas grandezas (repartição das escolas × médias de grupo) sem sinalizar. Adicionadas contagens e a coluna complementar, Figura 9 regenerada como barra empilhada 100%, + 4 testes. Texto em `SS12_TEXTO_PARA_O_TCC.md`.
- [x] **SS1** — ~~Documentar a queda de 2.392 → 1.586 registros.~~ **Concluído.** A redução não é descarte: 2.392 → −791 (2024 é alvo, não origem) → 1.601 → −15 (escolas sem par no ano seguinte) → 1.586. Implementado `rastrear_reducao_amostra()` + CSV + 6 testes. Texto e Quadro novo em `SS1_TEXTO_PARA_O_TCC.md`.

### Fase 2 — Terminologia ✅ **CONCLUÍDA**
*Varre o documento inteiro; fazer antes de reescrever parágrafos.*

- [x] **SS7** — ~~Substituir "informações" por "características" em todo o TCC.~~ **Concluído.** Termo escolhido: **característica** (feminino como "informação", preserva concordâncias; evita anglicismo na linguagem de gestor). 51 parágrafos + 8 células, incluindo 6 títulos de seção. Três exceções deliberadas: o alvo da previsão virou "indicador" (P368/P369 e Quadro 1), e P288/P296/P405 mantêm "informação" no sentido comum. Backup em `TCC_ANTES_SS7.docx`.
  - ⚠️ **Atualizar o sumário no Word** (Ctrl+A, F9): os títulos de seção mudaram e o sumário é campo automático.

### Fase 3 — Novo experimento ✅ **CONCLUÍDA**
*Maior esforço técnico; roda em paralelo com a Fase 4.*

- [x] **SS13** — ~~Rodar e tabular a comparação de um único modelo em dois cenários temporais (2022→2023 e 2023→2024).~~ **Concluído (24/07/2026).** As duas transições são as duas coortes anuais do dataset (2022→2023 = 797 escolas; 2023→2024 = 789). O modelo adotado (XGBoost) é avaliado **fora da amostra em cada coorte** por validação cruzada agrupada repetida (20 repetições, 20% dos municípios em teste) — mesma régua do Quadro 9, aqui separada por ano. Resultado: o modelo rende mais na transição 2022→2023 (ordenação 0,469, lista 0,627, ROC-AUC 0,901) do que na 2023→2024 (0,367 / 0,381 / 0,813), acompanhando a queda do abandono médio (1,36% → 0,88%). Os dois cenários cercam os números agregados do Quadro 9 (coerência confirmada). Código em `notebooks/14_ss13_cenarios_temporais.py`; números por repetição em `reports/metricas_ss13_cenarios.csv`; figura `reports/figuras/E9_ss13_cenarios.png`; Quadro e texto prontos em `SS13_TEXTO_PARA_O_TCC.md`.
  - ⚠️ **Ainda não inserido no `.docx`** — o material está pronto para colar em 6.3.2 (novo Quadro + 3 parágrafos + figura a numerar).
  - ✅ **Sem fragilidade de ambiente:** rodado sob scikit-learn 1.9.0 e 1.8.0 com números idênticos (o `GroupShuffleSplit` é estável entre versões, ao contrário do `GroupKFold` que quebrou os Quadros 9/10).

### Fase 4 — Redação e didática

- [x] **SS10 + SS9 + SS11** — ~~Parágrafo introdutório antes do Quadro 5.~~ **Concluído.** Dois parágrafos novos antes do Quadro 6: glossário dos indicadores (TDI, INSE, AFD Grupos 1/3/5, IRD) e guia das colunas colado na tabela. Aplicado ao `.docx`; backup em `TCC_ANTES_SS9_SS11.docx`.
  - ⚠️ **Divergência com o orientador:** ele exemplificou o INSE como "0 a 10". O dado real do INEP 2021 vai de **2,45 a 6,85** nas 69.820 escolas do país e de **2,97 a 6,10** nesta rede. Usei os números verificados.
  - Achado colateral: o rótulo "Porte (nº de matrículas)" exibia 5,73 — é o **logaritmo**. Rótulo corrigido no quadro e em `labels.py`, com a conversão explicada no texto.
- [x] **SS4** — ~~Incluir desvio-padrão junto das médias na seção 6.2.2.~~ **Concluído.** Urbanas 0,6% (dp 1,8), rurais 0,9% (dp 1,8), indígenas/quilombolas 6,6% (dp 9,0), com frase sobre o que o desvio alto revela. Números conferidos contra a definição exata da Figura 7 no notebook 12.
- [x] **SS2 + SS3** — ~~Citar a Figura 7 e escrever o parágrafo que a interpreta.~~ **Concluído.** Parágrafo de leitura dos dois painéis inserido **antes** da figura. Backup em `TCC_ANTES_SS2_SS4.docx`.
  - ⚠️ Pendência menor: o **título interno da Figura 7** ("A informação que o sistema aprende a prever") ainda usa "informação" — resquício do SS7, dentro do PNG. Corrigir na passagem de regeneração de figuras (junto com SS13/ambiente).

### Fase 5 — Reestruturação ✅ **CONCLUÍDA**
*Por último; depende de todo o texto acima estar estável.*

- [x] **SS5 + SS6** — ~~Mover o parágrafo "Daí decorre o critério…"~~ **Concluído.** Removido do ponto prematuro (entre 6.2.2 e 6.2.3). Ponte metodológica enxuta (só "ordem, não valor") inserida no fim de 6.2, antes de "Desempenho do Sistema". Parte argumentativa ("responder zero seria inútil ao gestor") dobrada ao parágrafo "Sobre o problema" da conclusão. Backup em `TCC_ANTES_SS5_SS6.docx`.

---

## Pendências em aberto

### 1. SS13 — ✅ **RESOLVIDO (24/07/2026)**

- **Feito:** um único modelo (XGBoost adotado) avaliado nas duas transições anuais em
  separado, fora da amostra, com Quadro e texto prontos (`SS13_TEXTO_PARA_O_TCC.md`).
  Ver detalhe na Fase 3 acima.
- **Falta só inserir no `.docx`** (novo Quadro em 6.3.2 + 3 parágrafos + figura a
  numerar). Não há mais nenhum experimento pendente.
- **Deriva de ambiente corrigida nesta sessão:** o venv estava com scikit-learn 1.9.0;
  reinstalei a 1.8.0 (versão fixada no `requirements.txt`) antes de gerar os números.
  Alerta remanescente: `shap` está em 0.52.0 vs 0.51.0 fixado — não afeta números de
  métrica (só as figuras do notebook 09), mas alinhar antes de regerar figuras do SHAP.

### 2. Ambiente reprodutível — Quadros 9 e 10 regenerados ✅ **RESOLVIDO (23/07/2026)**

- **Ação tomada:** `requirements.txt` agora fixa todas as versões com `==` (ambiente de
  referência: Python 3.14, Windows). Reexecução dupla do notebook 07 confirma
  reprodutibilidade: Spearman e Precision@K idênticos entre execuções (só ruído de
  ponto flutuante em 1e-16 no RMSE, sem afetar dígito exibido).
- **Achado ao regenerar:** apenas a linha do **modelo adotado (XGBoost)** mudou — a
  causa não era a partição da CV, e sim a versão do **xgboost (3.2.0)**. Ridge, Random
  Forest e "sem sistema" ficaram idênticos ao commit.
- **Quadros 9 e 10 atualizados no `.docx`** com os números reprodutíveis. Backup em
  `TCC_ANTES_QUADRO9.docx`.

⚠️ **Consequência de narrativa que o autor precisa avaliar antes da defesa:**
  - O Spearman do modelo adotado caiu de 0,458 → **0,416** (validação repetida) e de
    0,390 → **0,348** (teste temporal); a captura da lista de 150 caiu de 64% → **57%**;
    o ROC-AUC de 0,830 → **0,798**.
  - Com isso, **o XGBoost deixou de liderar** claramente. Na validação repetida o
    Random Forest tem Spearman ligeiramente maior (0,431 vs 0,416) e RMSE menor; no
    teste temporal o XGBoost ainda lidera de raspão (Spearman 0,348 vs 0,343). Os três
    modelos são **estatisticamente indistinguíveis** (ICs sobrepostos).
  - A frase falsa *"o modelo adotado alcança o melhor acerto de ordenação de todos"* foi
    **reescrita** para o empate honesto (P416). Todas as citações numéricas na conclusão
    e no resumo foram atualizadas.
  - **Decisão em aberto:** a escolha do XGBoost como modelo adotado continua defensável
    (lidera o teste temporal, que simula o uso real; SHAP construído sobre ele; empate
    dentro do ruído), mas o autor deve estar preparado para justificá-la, já que o RF
    empata ou supera em vários pontos. **Não** alterei o modelo adotado — seria decisão
    de mérito, não de correção.
- Análise técnica completa em `SS8_TEXTO_PARA_O_TCC.md`, seção 6.

### 3. Divergência factual com o orientador — escala do INSE (resolvida no texto)

- O orientador exemplificou o INSE como *"varia de 0 a 10"* (SS11). O dado real do INEP
  2021 vai de **2,45 a 6,85** nas 69.820 escolas do país e de **2,97 a 6,10** nesta
  rede. O texto usa os números verificados.
- **Ação sugerida:** ter os números à mão na defesa, caso o orientador questione.

### 4. Ajustes a fazer no Word (manuais)

- **Atualizar o sumário:** os títulos de seção mudaram (SS7) e o sumário é campo
  automático — abrir o `.docx`, Ctrl+A, F9.
- **Conferir a largura das colunas** dos Quadros 5 (novo) e 7 (reestruturado): foram
  montados somando os mesmos 9.070 dxa das demais tabelas, mas o Quadro 7 tem seis
  colunas e o cabeçalho pode quebrar no meio de palavra — que foi justamente uma queixa
  do orientador sobre o quadro antigo.

### 5. Passagem de regeneração de figuras ⚠️

- **Figuras 12, 13 e 14** (desempenho, ganho da lista, acerto por tamanho de lista):
  os PNGs embutidos no `.docx` ainda mostram as curvas **antigas** do XGBoost. Os
  Quadros 9 e 10 já foram atualizados, mas essas figuras não — precisam ser
  regeradas (notebook 07/12) e re-inseridas para bater com as tabelas. Visualmente a
  diferença é pequena (só o XGBoost mudou), mas há inconsistência.
- **Títulos internos das Figuras 7 e E2** ainda dizem *"informação"* — resquício do
  SS7, que só tocou texto (notebook 12, `suptitle`).
- Fazer tudo numa passagem única de figuras.

### 6. Numeração dos quadros mudou ⚠️

- O Quadro 5 novo (rastreabilidade da amostra) empurrou os demais: antigo **5→6, 6→7,
  7→8, 8→9, 9→10**. Os comentários originais do orientador citam a numeração **antiga**.

### 7. Limpeza de backups

- Acumulados durante as edições: `TCC_Evasao_Escolar_ANTES_SS1_SS8_SS12.docx`,
  `TCC_ANTES_SS7.docx`, `TCC_ANTES_SS9_SS11.docx`, `TCC_ANTES_SS2_SS4.docx`,
  `TCC_ANTES_SS5_SS6.docx`. Apagar após conferência final no Word.

---

## Observações sobre o caminho crítico

- **SS8 → Fase 4:** se o recálculo da coluna de reprovação mudar valores, os parágrafos interpretativos precisam ser escritos sobre os números corretos. *(Resolvido: os números não mudaram.)*
- **SS13** é o item de maior risco de prazo, por depender de execução de código e da reprodutibilidade do ambiente (Pendência 2).
