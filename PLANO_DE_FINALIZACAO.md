# Plano de Finalização do TCC

Levantamento de **24 de julho de 2026**, feito a partir da inspeção do
`TCC_Evasao_Escolar.docx` atual e do repositório. Supera o `PROXIMOS_PASSOS.md`
(21/07), que é anterior a toda a rodada de comentários do orientador.

**Estado geral:** o trabalho está essencialmente pronto. Os 13 comentários do
orientador foram atendidos, o Capítulo 2 (Revisão Bibliográfica) foi escrito com
referências reais em ABNT, o experimento SS13 e o gráfico de resíduos em número de
alunos foram inseridos. O documento tem 7 capítulos, 20 figuras, 11 quadros e 18
referências. O que resta são **correções de consistência, elementos pré-textuais do
autor e preparação para a defesa** — nenhuma tarefa de pesquisa em aberto.

> Observação: a remoção da marcação azul/amarela de revisão foi deixada de fora
> deste plano a pedido do autor.

---

## Tier 1 — Correções de consistência ✅ EXECUTADO (24/07/2026)

*Backup do estado anterior: `TCC_ANTES_TIER1.docx`. Restou apenas o item 1.4, que
depende do autor.*

- [x] **1.1 Regenerar e reinserir as figuras de desempenho desatualizadas. ✅**
  Regeradas com `notebooks/07` e `notebooks/12` (ambiente fixado, scikit-learn 1.8.0) e
  **reembutidas** no `.docx`: **Figura 12** (M6_cv_repetida), **Figura 15**
  (E4_desempenho) e **Figura 16** (M5_precision_por_k). Agora batem com os Quadros 9 e
  10. Conferido visualmente (F12: XGBoost Spearman ~0,42, RF ~0,44).

- [x] **1.2 Corrigir os títulos internos das figuras (“informação”). ✅**
  Corrigidos nos notebooks e reembutidos: **Figura 7** (E2) “A informação…” → “**O
  indicador** que o sistema aprende a prever”; **Figura 8** (E5), **Figura 10** (E8) e
  **Figura 11** (E7) “informação(ões)” → “**característica(s)**”. Também ajustado o
  título de E3 no notebook (figura não usada no `.docx`). Total: 7 figuras reembutidas,
  altura reajustada ao novo aspecto para não distorcer.

- [x] **1.3 Contagem de testes 98 → 114. ✅** `pytest` confirma **114 passando**; as 4
  ocorrências de “98 testes” no `.docx` foram atualizadas para “114 testes”.

- [ ] **1.4 Ficha catalográfica. ⏳ DEPENDE DO AUTOR.** Não foi tocada de propósito: o
  bloco ainda traz “Gerenciador de ficha catalográfica: http://biblio2.pucsp.br/ficha/…
  Obs. Após inserir a ficha deletar este texto”. Só o autor pode **gerar a ficha real**
  no link (com seus dados) e então apagar essa observação. Deixar como está até lá.

- [x] **1.5 Preparado o auto-update de campos. ✅** Inserido
  `<w:updateFields w:val="true"/>` no `settings.xml` → **ao abrir no Word, ele já
  pergunta se quer atualizar os campos** (Sumário, Lista de Ilustrações com 20 figuras,
  Lista de Quadros com 11). O autor só precisa **aceitar** (ou Ctrl+A, F9). Esta parte
  é intrínseca ao Word e não há como preencher a paginação fora dele.

- [x] **1.6 Larguras dos Quadros 5 e 7 conferidas. ✅** Quadro 5 (4 colunas, cabeçalhos
  curtos “Etapa/Critério/Linhas/Escolas”): sem problema. Quadro 7 (6 colunas, 9.070 dxa):
  os cabeçalhos são multipalavra e **quebram em espaços, não no meio de palavra** — o
  defeito que o orientador apontara não se repete. Vale só uma conferida visual no Word.

---

## Tier 2 — Elementos pré-textuais (dependem do autor)

- [ ] **2.1 Nome do orientador na folha de rosto.** Hoje ausente (não há “Prof.” no
  documento). É o campo pré-textual mais visível.
- [ ] **2.2 Composição da banca examinadora.** Há cinco linhas em branco “___” à
  espera dos nomes (pode ficar para a data da defesa).
- [ ] **2.3 Agradecimentos.** Existe um texto genérico; personalizar se desejar.

---

## Tier 3 — Preparação para a defesa

- [ ] **3.1 Justificar a escolha do XGBoost como modelo adotado.**
  Depois da fixação do ambiente, o XGBoost **deixou de liderar com folga**: na
  validação repetida o Random Forest empata ou supera (Spearman 0,431 vs 0,416) e os
  três modelos são estatisticamente indistinguíveis. A escolha segue defensável —
  lidera o teste temporal (que simula o uso real), é a base do SHAP, e o empate está
  dentro do ruído —, mas convém **ter o argumento pronto**, pois a banca pode
  perguntar. (Já corrigido no texto: não há mais a frase de que o modelo adotado é “o
  melhor de todos”.)
- [ ] **3.2 Escala do INSE.** O orientador exemplificou “0 a 10” (SS11); o dado real do
  INEP 2021 vai de **2,45 a 6,85** no país e de **2,97 a 6,10** nesta rede. Ter os
  números à mão caso seja questionado.
- [ ] **3.3 Números novos no roteiro de defesa.** Incorporar o Quadro 11 (SS13, dois
  cenários) e a Figura 14 (resíduo em nº de alunos, MAE ≈ 3 alunos por escola) ao
  discurso da defesa.
- [ ] **3.4 Atualizar o `Guia_Apresentacao_v2.docx`** com o SS13, a Figura 14 e o
  Capítulo 2, se for usá-lo como roteiro.

---

## Tier 4 — Higiene técnica e reprodutibilidade

- [ ] **4.1 Commit do trabalho da sessão.** Nada foi commitado: notebooks 14 e
  alterações no 07, `requirements.txt` (versões fixadas), `metricas_*` e `residuos_*`
  novos, o `.docx`, o Capítulo 2, a Figura 14, e os arquivos `SS13_TEXTO_PARA_O_TCC.md`,
  `COMENTARIOS_ORIENTADOR.md`. Sugerido separar em commits temáticos (SS13; Cap. 2;
  figura de resíduos; ambiente).
- [ ] **4.2 Alinhar a versão do `shap` (0.52.0 → 0.51.0 do `requirements.txt`).**
  Só é necessário **se** for regerar as figuras do SHAP (beeswarm/força/waterfall);
  não afeta nenhum número de métrica nem as figuras dos itens 1.1/1.2.
- [ ] **4.3 Backup do modelo treinado.** `models/xgboost_v1.joblib` está fora do Git
  (decisão correta, arquivo binário). É reproduzível (rodar notebooks 05 e 08), mas
  vale uma cópia externa até a defesa.
- [ ] **4.4 Limpar os backups acumulados** (`TCC_ANTES_*.docx`, `TCC_ANTES_QUADRO9.docx`,
  etc.) após a conferência final no Word.
- [ ] **4.5 (Opcional) Empacotar em contêiner — Docker (Fase 9).** É a única lacuna
  técnica declarada e está prevista como trabalho futuro no capítulo de implantação.
  Transforma “prevê-se empacotar” em “está empacotado”; ~meio dia. Não é essencial.

---

## Tier 5 — Melhorias opcionais (qualidade)

- [x] **5.1 Verificação cruzada de números após a fixação do ambiente. ✅ CONFERIDO
  (24/07).** Varredura do `.docx`: nenhum valor antigo sobrou (0,458; 0,390; 0,830;
  64%) e os novos reprodutíveis estão presentes (Spearman 0,416; temporal 0,348;
  ROC-AUC 0,798; captura de 150 = 57%). Resumo, Conclusão e corpo estão coerentes com
  os Quadros 9 e 10 atuais. Nada a corrigir aqui.
- [ ] **5.2 Conferir o total de evasões de 2024.** A memória registra “2.043 alunos”
  (notebook 12), enquanto a base do painel usada na Figura 14 dá **2.020**. Alinhar a
  base de matrícula das duas contas para o número ficar único no texto.
- [ ] **5.3 Leitura final em voz alta** caçando jargão de análise de dados remanescente
  — foi o pedido central do orientador. As métricas já aparecem nomeadas pelo que
  medem, com o termo técnico entre parênteses uma única vez, em 6.3.1.
- [ ] **5.4 Revisão de fluxo do Capítulo 2** recém-criado, conferindo que as transições
  entre 2.1 (Fundamentação) e 2.2 (Trabalhos Relacionados) estão suaves e que toda
  citação no texto tem entrada nas Referências (verificado automaticamente: 16 citações,
  todas com referência).

---

## Caminho crítico sugerido

1. **Passagem única de figuras** (itens 1.1 + 1.2 + 4.2 se preciso) — resolve a maior
   inconsistência visível de uma vez.
2. **Correções de texto** (1.3) e **pré-textuais** (1.4, 2.1–2.3).
3. **Atualização de campos no Word** (1.5) e conferência das tabelas (1.6) — por último,
   depois de todo o conteúdo estável.
4. **Commit** (4.1) e **preparação da defesa** (Tier 3) em paralelo.

Nada aqui bloqueia a entrega imediata do ponto de vista de conteúdo; os itens do Tier 1
são de acabamento e consistência, não de mérito.
