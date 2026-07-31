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
RESUMO: 121 conferidos OK · 0 divergencia(s) · 0 sem fonte automatica
```

**Última execução verificada: 121 OK, 0 divergências, 0 sem fonte.**

Complementar com a suíte, que trava as invariantes que a varredura não cobre:

```bash
pytest -q          # 132 testes
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

- **Bloco 9 (ordem dos fatores SHAP).** O script imprime o top-6 de
  `reports/shap_importancia.csv` e o parágrafo do texto, **sem assertar** — conferir a olho a
  cada retreino. Ordem real hoje: `abnd_s2_t` (0,333), `tdi_med_t` (0,201), `abnd_t` (0,152),
  `abnd_s1_t` (0,127), `is_loc_diferenciada` (0,113), `reprov_t` (0,098). O `inse_media` é o
  **13º** (0,042).
  > Divergência encontrada e **corrigida** neste ponto: o ¶476 citava o "nível socioeconômico"
  > entre os principais fatores e omitia `is_loc_diferenciada`. Provável resíduo de uma rodada
  > de SHAP anterior, em que o INSE era de fato 4º. Backup `TCC_ANTES_TESTES_E_SHAP.docx`.
  > Lição: como o bloco não trava, um retreino pode reintroduzir a divergência em silêncio.
- **Bloco 10 (contagem de testes).** Delegado ao `pytest` rodado em separado — este bloco
  **não** compara nada. O `.docx` diz "132 testes" em 4 pontos (¶332, ¶380, ¶501, ¶514) e o
  `pytest` confirma 132. Todo teste novo obriga a atualizar esses 4 pontos. Atenção:
  `PLANO_DE_FINALIZACAO.md`, `SS1_TEXTO_PARA_O_TCC.md` e `SS12_TEXTO_PARA_O_TCC.md` falam de
  114, 108 e 104 — são registros históricos de cada rodada, não erros.
- **Alvo fixo por caminho absoluto.** As constantes `RAIZ` e `DOC` no topo do script trazem
  caminhos absolutos da máquina do autor, e `DOC` aponta para
  `documentos/TCC_Evasao_Escolar.docx` — o documento canônico. Se o arquivo for renomeado ou
  movido, o script quebra com erro claro (não passa em falso). Se um dia surgir uma variante
  do documento, ela **não** é validada até que `DOC` seja atualizado.

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
