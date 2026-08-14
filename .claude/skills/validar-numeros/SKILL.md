---
name: validar-numeros
description: Confere cada número escrito na monografia contra o artefato do pipeline que o gera (parquets, CSVs de métricas, resíduos, SHAP), recalculando em vez de conferir de memória. Usar depois de qualquer edição numérica no .docx, depois de retreinar ou regerar métricas, antes de entregar ao orientador ou defender, e sempre que houver dúvida se um valor do texto ainda corresponde ao pipeline.
---

# Validar os Números da Monografia

Regra do projeto: **nenhum número entra no `.docx` sem sair de um artefato do pipeline.**
Esta skill é o mecanismo que trava essa regra.

Pré-requisito: rodar `/validar-ambiente` primeiro. Número recalculado em ambiente diferente
do de referência não serve para comparação.

## Execução

A partir de `evasao-escolar/`:

```bash
python notebooks/15_varredura_numeros.py
```

O script recalcula tudo a partir de `data/`, `reports/` e do modelo serializado, lê o
`.docx` com `python-docx` e compara valor a valor. Saída em 10 blocos (base histórica,
características, quadros descritivos, métricas, SS13, resíduos, equidade, SHAP, testes) e um
resumo final no formato:

```
RESUMO: 178 conferidos OK · 0 divergencia(s) · 0 sem fonte automatica
```

**Última execução verificada: 178 OK, 0 divergências, 0 sem fonte (14/08/2026).**
Subiu de 136 para 178 na reescrita do Capítulo 6: a leitura dos quadros passou a citar no
texto valores que antes só apareciam nas tabelas, e as justificativas das escolhas trouxeram
números novos, todos com checagem acrescentada ao notebook 15 — R² do teste temporal (−0,33),
as sete linhas do experimento de ablação IED/ICG, o par acerto×alcance por tamanho de lista
(50, 100, 150) e a contagem de escolas de localização diferenciada (41).

Complementar com a suíte, que trava as invariantes que a varredura não cobre:

```bash
pytest -q          # 138 testes
```

## Como ler a saída

| Marca | Significado | O que fazer |
|---|---|---|
| `ok` | texto e recálculo batem dentro da tolerância (1,1% relativa) | nada |
| `XX` | **divergência** — o texto diz um valor, o pipeline diz outro | investigar antes de corrigir (ver abaixo) |
| `??` | número do texto sem fonte reproduzível automática | conferir à mão e, se possível, dar-lhe uma fonte |

## Diante de uma divergência

Não "corrigir o texto para bater". A ordem é:

1. **Qual lado está errado?** O pipeline mudou (retreino, novo dado, versão de biblioteca) ou
   o texto foi digitado errado? Conferir a data de modificação dos artefatos em `reports/`.
2. Se o **pipeline** mudou: o número novo é o correto — mas verificar se a mudança era
   intencional. Deriva de ambiente já falsificou números neste projeto (ver `/validar-ambiente`).
3. Se o **texto** está errado: corrigir no `.docx`, com backup `TCC_ANTES_<ASSUNTO>.docx`.
4. Um número quase nunca aparece uma vez só. Verificar também **Resumo, Conclusão, legendas
   de figura e notas de rodapé** — a varredura cobre o corpo e os quadros, não garante o resto.

## Limites conhecidos desta varredura

Pontos que o script **imprime mas não trava** — conferir a olho:

- **Bloco 9 (ordem dos fatores SHAP).** ✅ **Deixou de ser só informativo em 31/07.** Agora
  trava três coisas: que os **dois primeiros** do `shap_importancia.csv` estejam nomeados no
  parágrafo pelos rótulos de gestor, que o **nível socioeconômico não** apareça entre os
  principais (ele é o 13º, 0,042), e que a âncora do parágrafo ainda exista. Ordem real hoje:
  `abnd_s2_t` (0,333), `tdi_med_t` (0,201), `abnd_t` (0,152), `abnd_s1_t` (0,127),
  `is_loc_diferenciada` (0,113), `reprov_t` (0,098).
  > **Duas falhas reais deste bloco, ambas corrigidas.** (1) O texto citava o "nível
  > socioeconômico" entre os principais fatores — resíduo de uma rodada de SHAP anterior em que
  > o INSE era 4º. (2) O localizador usava `find("ela mostra")`, e quando o parágrafo foi
  > reescrito para "ela ordena" o `-1` passou a fatiar em silêncio: o bloco imprimia texto
  > vazio e ninguém notava. As asserções novas pegam as duas — verificado simulando a redação
  > antiga, que acende `top «abnd_s2_t» ausente` e `INSE citado, sendo o 13º`.
- **Bloco 10 (contagem de testes).** Delegado ao `pytest` rodado em separado — este bloco
  **não** compara nada. O `.docx` diz "138 testes" em 4 pontos (¶310, ¶358, ¶527, ¶540) e o
  `pytest` confirma 138. Todo teste novo obriga a atualizar esses 4 pontos. Atenção:
  `PLANO_DE_FINALIZACAO.md`, `SS1_TEXTO_PARA_O_TCC.md` e `SS12_TEXTO_PARA_O_TCC.md` falam de
  114, 108 e 104 — são registros históricos de cada rodada, não erros.
- **Alvo fixo por caminho absoluto.** As constantes `RAIZ` e `DOC` no topo do script trazem
  caminhos absolutos da máquina do autor, e `DOC` aponta para
  `documentos/monografia-artur-oliveira-engenharia-de-software-2026.docx` — o documento
  canônico. Se o arquivo for renomeado ou movido, o script quebra com erro claro (não passa
  em falso). Se um dia surgir uma variante do documento, ela **não** é validada até que `DOC`
  seja atualizado. Já aconteceu uma vez: o arquivo foi renomeado em 31/07/2026 e `DOC`,
  as skills e o `CLAUDE.md` tiveram de acompanhar.
- **Ponteiros `¶` na saída.** São rótulos fixos em string, índice 0-based de
  `Document(...).paragraphs`; o script localiza por busca de texto, nunca por índice, então um
  rótulo defasado atrapalha quem procura à mão mas não falseia nenhuma checagem. Recalculados
  em 31/07/2026.

## Fontes que alimentam a varredura

`data/interim/painel_escola_ano_pe_estadual_em.parquet` · `data/interim/taxas_rendimento_pe_estadual_em.parquet` ·
`data/processed/features.parquet` · `reports/estatisticas_features.csv` ·
`reports/estatisticas_mesorregiao.csv` · `reports/metricas_cv_repetida.csv` ·
`reports/metricas_xgboost.csv` · `reports/metricas_ss13_cenarios.csv` ·
`reports/residuos_transicoes_alunos.csv` · `reports/residuos_grupo_temporal.csv` ·
`reports/residuos_top20_temporal.csv` · `reports/shap_importancia.csv`

Se um número novo entrar no texto e não tiver fonte nessa lista, **adicionar a checagem ao
notebook 15** em vez de conferir manualmente uma vez só.

## Números-âncora (para reconhecer deriva de relance)

| Valor | Significado |
|---|---|
| 2.392 → 1.586 | painel histórico → conjunto de modelagem (806 → 801 escolas) |
| 39 / 1.586 / 801 / 185 | características / observações / escolas / municípios |
| 0,416 · 0,504 | Spearman e Precision@K do modelo adotado (CV repetida) |
| 0,348 · 0,418 | idem no teste temporal |
| 0,469 / 0,627 vs 0,367 / 0,381 | SS13: transição 2022→2023 vs 2023→2024 |
| −6,12 p.p. | resíduo médio nas escolas de localização diferenciada |
| 1,36% → 0,88% | abandono médio das duas coortes |
