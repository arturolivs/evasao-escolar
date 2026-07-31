---
name: validar-documento
description: Valida a consistência estrutural e editorial da monografia em .docx — numeração de figuras e quadros sem lacunas, terminologia padronizada ("característica" e não "informação"/"feature"), citações com entrada nas referências, placeholders pré-textuais pendentes e status dos 13 comentários do orientador. Usar antes de entregar ao orientador, antes da defesa, depois de inserir ou renumerar figuras/quadros/seções, ou quando pedirem revisão do documento (não dos números — para números use validar-numeros).
---

# Validar o Documento da Monografia

Confere a **estrutura e a edição** do `.docx`. Para os valores numéricos, use
`/validar-numeros` — são validações complementares e nenhuma substitui a outra.

## Documento alvo

`documentos/TCC_Evasao_Escolar.docx` — 591 parágrafos, 12 tabelas. É o único documento
canônico e o mesmo alvo do notebook 15 (varredura de números).

Os `TCC_ANTES_*.docx` em `documentos/` são backups por rodada de edição: servem para
comparar ou restaurar, **nunca** para validar nem editar.

## Verificação automática

A partir da **raiz do repositório** (`monografia/`):

```bash
python - <<'PY'
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from docx import Document

DOC = "documentos/TCC_Evasao_Escolar.docx"   # confirmar o canônico
d = Document(DOC)
pars = [p.text for p in d.paragraphs]
txt = "\n".join(pars)
print(f"{DOC} | {len(pars)} paragrafos | {len(d.tables)} tabelas\n")

def seq(rot, padrao):
    nums = sorted({int(m) for m in re.findall(padrao, txt)})
    falta = [n for n in range(1, (max(nums) if nums else 0)+1) if n not in nums]
    print(f"{rot}: 1..{max(nums) if nums else 0} | {len(nums)} distintos | lacunas: {falta or 'nenhuma'}")

seq("Figuras", r"Figura (\d+)")
seq("Quadros", r"Quadro (\d+)")

print("\n--- terminologia (comentario SS7) ---")
for t in ["informações", "informação", "features", "feature"]:
    print(f"  {t}: {len(re.findall(rf'\b{t}\b', txt, re.I))}")

print("\n--- placeholders pre-textuais ---")
for p in ["ficha catalográfica", "biblio2.pucsp", "deletar este texto", "orientação do prof"]:
    print(f"  {p!r}: {len(re.findall(re.escape(p), txt, re.I))}")
print(f"  linhas em branco '___' (banca): {len(re.findall('___', txt))}")

print("\n--- testes citados no texto ---")
print("  ", set(re.findall(r"\d+ testes", txt)) or "nenhuma mencao")
PY
```

## Linha de base verificada

Rodado com o documento atual — use como referência para detectar regressão:

| Checagem | Esperado | Status |
|---|---|---|
| Figuras | 1–20, sem lacunas | ✅ |
| Quadros | 1–11, sem lacunas | ✅ |
| Tabelas no arquivo | 12 (11 quadros + 1 pré-textual) | ✅ |
| "informações" (plural) | 0 | ✅ |
| "informação" | 4 — todas legítimas, sentido comum (¶305, ¶313, ¶341, ¶433) | ✅ |
| "feature(s)" | 3 — *abstract* em inglês, título da referência Guyon & Elisseeff, caminho `src/features` | ✅ |
| "N testes" | `{"138 testes"}`, 4 ocorrências (¶332, ¶380, ¶501, ¶514), confere com o `pytest` | ✅ |
| Orientador na folha de rosto | "sob a orientação do prof. Silvio Luiz Stanzani" | ✅ presente |
| Ficha catalográfica | placeholder ainda presente | ⏳ **depende do autor** |
| Banca | 55 linhas `___` | ⏳ **depende do autor** |

> `PLANO_DE_FINALIZACAO.md` (24/07) lista o item 2.1 "nome do orientador ausente" como
> pendente. **Está desatualizado**: o nome está no documento em minúscula (`prof.`), e a
> verificação original buscava `Prof.` com maiúscula.

## Checklist manual (o que script não pega)

### 1. Terminologia e linguagem de gestor
- [ ] Cada ocorrência de "informação"/"feature" sinalizada é uma das exceções auditadas acima? Nova ocorrência = regressão do SS7.
- [ ] Métrica técnica nomeada pelo que mede, com o termo técnico entre parênteses **uma única vez** (padrão adotado em 6.3.1).
- [ ] Nenhum jargão de análise de dados sobrando — foi o pedido central do orientador.

### 2. Numeração e listas
- [ ] Toda figura e todo quadro é **citado no corpo** antes de aparecer (foi o comentário SS2).
- [ ] Lista de Ilustrações com 20 entradas e Lista de Quadros com 11 — só conferível no Word, após atualizar campos.
- [ ] Sumário atualizado: títulos de seção mudaram no SS7 e o sumário é campo automático. O `settings.xml` já tem `<w:updateFields w:val="true"/>` — o autor aceita o prompt ao abrir, ou Ctrl+A / F9.

### 3. Citações e referências
- [ ] 24 referências, nenhuma órfã, todas citadas — **todas com PDF em `documentos/referencias/`**. Mapa completo `PDF → citação → parágrafo` em `documentos/referencias/README.md`.
- [ ] Fontes do INEP distinguidas por letra (2024a/b/c) conforme a NBR 6023.
- [ ] Regra vigente: **só entra no texto obra com cópia local**. Tinto, Rumberger, Romero & Ventura, Molnar e Hunter foram removidos em 30/07/2026 por não terem PDF (backup `TCC_ANTES_REMOCAO_REFS.docx`).

### 4. Comentários do orientador
- [ ] Os 13 (SS1–SS13) seguem atendidos — status em `documentos/COMENTARIOS_ORIENTADOR.md`.
- [ ] Atenção à renumeração: o Quadro 5 novo empurrou os demais (antigo 5→6, 6→7, 7→8, 8→9, 9→10). **Os comentários originais citam a numeração antiga.**
- [ ] Divergência factual deliberada com o orientador: ele exemplificou o INSE como "0 a 10"; o texto usa o dado real do INEP 2021 (2,45–6,85 no país; 2,97–6,10 nesta rede). Ter os números à mão na defesa.

### 5. Coerência de conteúdo com o pipeline
- [ ] A ressalva de equidade (superestimação em escolas indígenas/quilombolas, −6,12 p.p.) aparece onde há afirmação sobre risco.
- [ ] A justificativa da escolha do XGBoost reconhece o empate estatístico com Ridge e Random Forest — não afirmar liderança geral.
- [ ] Larguras dos Quadros 5 e 7 conferidas no Word (cabeçalhos multipalavra não devem quebrar no meio de palavra — queixa original do orientador).

## Regras ao editar o `.docx`

1. **Backup obrigatório antes de tocar**, seguindo a convenção: `TCC_ANTES_<ASSUNTO>.docx`.
2. Marcar o texto novo em azul `1F4E9B` + realce amarelo; a marcação é **temporária** e sai quando a pendência é dada por concluída (limpeza de 30/07/2026 zerou as 23 então existentes).
3. Não "resolver" pendências que dependem do autor: ficha catalográfica, banca, agradecimentos.
4. Depois de qualquer edição numérica, rodar `/validar-numeros`.
