---
name: validar-documento
description: Valida a consistência estrutural e editorial da monografia em .docx — numeração de figuras e quadros sem lacunas, terminologia padronizada ("característica" e não "informação"/"feature"), citações com entrada nas referências, placeholders pré-textuais pendentes e status dos 13 comentários do orientador. Usar antes de entregar ao orientador, antes da defesa, depois de inserir ou renumerar figuras/quadros/seções, ou quando pedirem revisão do documento (não dos números — para números use validar-numeros).
---

# Validar o Documento da Monografia

Confere a **estrutura e a edição** do `.docx`. Para os valores numéricos, use
`/validar-numeros` — são validações complementares e nenhuma substitui a outra.

## Documento alvo

`documentos/monografia-artur-oliveira-engenharia-de-software-2026.docx` — 637 parágrafos,
13 tabelas. É o único documento canônico e o mesmo alvo do notebook 15 (varredura de
números). Renomeado em 31/07/2026; antes chamava-se `TCC_Evasao_Escolar.docx`.

Os `TCC_ANTES_*.docx` em `documentos/` são backups por rodada de edição: servem para
comparar ou restaurar, **nunca** para validar nem editar.

## Verificação automática

A partir da **raiz do repositório** (`monografia/`):

```bash
python - <<'PY'
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from docx import Document

DOC = "documentos/monografia-artur-oliveira-engenharia-de-software-2026.docx"
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

# --- campos automaticos: sem esta tag o Word nao oferece atualizar Sumario/Listas ---
import zipfile
cfg = zipfile.ZipFile(DOC).read("word/settings.xml").decode("utf-8")
print("\n--- campos automaticos ---")
print("  updateFields:", "OK" if "updateFields" in cfg else "XX AUSENTE - Sumario e Listas nao serao atualizados")

# --- marcacao temporaria (azul 1F4E9B + realce) ---
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
marcados = []
def varre(ps, ctx=""):
    for i, par in enumerate(ps):
        for r in par.runs:
            rPr = r._element.rPr
            if rPr is None: continue
            c, h = rPr.find(W+"color"), rPr.find(W+"highlight")
            cv = c.get(W+"val") if c is not None else None
            hv = h.get(W+"val") if h is not None else None
            if (cv and cv.upper() == "1F4E9B") or (hv and hv != "none"):
                marcados.append(f"{ctx}\u00b6{i} cor={cv} realce={hv} :: {r.text[:60]!r}")
varre(d.paragraphs)
for ti, t in enumerate(d.tables):
    for ri, row in enumerate(t.rows):
        for ci, c in enumerate(row.cells): varre(c.paragraphs, f"tab{ti}[{ri},{ci}] ")
print("\n--- marcacao temporaria ---")
print(f"  runs marcados: {len(marcados)}")
for m in marcados: print("   ", m)

# --- SS2: figura/quadro citado no corpo ANTES da legenda (ignora listas pre-textuais) ---
INI = next(i for i, t in enumerate(pars) if t.strip().upper().startswith("LISTA DE ABREVIATURAS")) + 1
print("\n--- SS2: citacao antes da legenda ---")
def ss2(rot, n_max):
    prob = []
    for n in range(1, n_max+1):
        pat = re.compile(rf"\b{rot} {n}\b")
        leg = cit = None
        for i in range(INI, len(pars)):
            if not pat.search(pars[i]): continue
            if re.match(rf"^{rot} {n}\s*[\u2013\-:]", pars[i].strip()):
                if leg is None: leg = i
            elif cit is None: cit = i
        if leg is None: prob.append(f"{rot} {n}: legenda ausente no corpo")
        elif cit is None: prob.append(f"{rot} {n}: sem citacao no corpo (legenda \u00b6{leg})")
        elif cit > leg: prob.append(f"{rot} {n}: citada \u00b6{cit} DEPOIS da legenda \u00b6{leg}")
    print(f"  {rot}s: {len(prob)} problema(s)")
    for x in prob: print("   XX", x)
ss2("Figura", max(int(m) for m in re.findall(r"Figura (\d+)", txt)))
ss2("Quadro", max(int(m) for m in re.findall(r"Quadro (\d+)", txt)))

# --- referencias orfas ---
import unicodedata
def norm(x): return "".join(ch for ch in unicodedata.normalize("NFD", x) if unicodedata.category(ch) != "Mn").lower()
R0 = next(i for i, t in enumerate(pars) if t.strip().upper().startswith("REFER\u00caNCIAS") and i > 300) + 1
R1 = next((i for i in range(R0, len(pars)) if pars[i].strip().lower().startswith("ap\u00eandice")), len(pars))
refs = [(i, pars[i].strip()) for i in range(R0, R1) if len(pars[i].strip()) > 40]
corpo = norm("\n".join(pars[INI:R0]))
orfas = [f"\u00b6{i} {t[:50]}" for i, t in refs if norm(re.split(r"[,.;]", t)[0].split()[0]) not in corpo]
print(f"\n--- referencias ---\n  entradas: {len(refs)} | orfas: {len(orfas)}")
for o in orfas: print("   XX", o)
PY
```

## Linha de base verificada

Rodado com o documento atual — use como referência para detectar regressão:

| Checagem | Esperado | Status |
|---|---|---|
| Figuras | 1–22, sem lacunas | ✅ |
| Quadros | 1–12, sem lacunas | ✅ |
| Tabelas no arquivo | 13 (12 quadros + 1 pré-textual, a de abreviaturas) | ✅ |
| Listas pré-textuais | Lista de Ilustrações com 22 entradas (¶166–¶187), Lista de Quadros com 12 (¶193–¶204) | ✅ |
| "informações" (plural) | 0 | ✅ |
| "informação" | 4 — todas legítimas, sentido comum (¶283, ¶291, ¶319, ¶433) | ✅ |
| "feature(s)" | 2 — caminho `src.features` (¶347), título da referência Guyon & Elisseeff (¶577) | ✅ |
| "N testes" | `{"138 testes"}`, 4 ocorrências (¶310, ¶358, ¶538, ¶551), confere com o `pytest` | ✅ |
| Orientador na folha de rosto | "sob a orientação do prof. Silvio Luiz Stanzani" | ✅ presente |
| Agradecimentos | preenchidos em 31/07/2026 a pedido do autor | ✅ |
| SS2 — figura/quadro citado antes da legenda | 22 figuras e 12 quadros, 0 problemas | ✅ |
| Referências | 24 entradas (¶566–¶589), 0 órfãs, INEP com 2024a/b/c | ✅ |
| Campos automáticos | `<w:updateFields w:val="true"/>` presente no `settings.xml` | ✅ **reinserido em 20/08/2026** |
| Títulos pré-textuais | todos em versal — RESUMO, ABSTRACT, AGRADECIMENTOS, LISTA DE… | ✅ |
| Marcação temporária azul+amarelo | 0 runs | ✅ limpa em 20/08/2026 |
| Ficha catalográfica | **ausente, sem placeholder** — verso da folha de rosto (¶53–¶72) inteiramente em branco: 0 caixas de texto, 0 parágrafos com borda, 0 ocorrências de "ficha" no XML | ⏳ **depende do autor** |
| Banca | **5** linhas de assinatura (¶75, 77, 79, 81, 83), 33 `_` cada | ⏳ **depende do autor** |

> **O script imprime `linhas em branco '___' (banca): 55`, e são 5 linhas.** O `re.findall('___')`
> conta trincas de underscore sem sobreposição: 33 ÷ 3 = 11 por linha × 5 linhas = 55. Número
> da linha de base anterior era esse artefato, não a contagem real.

> **Convenção dos ponteiros `¶`**: índice 0-based de `Document(...).paragraphs`, o mesmo que
> o notebook 15 usa. Recalculados em 20/08/2026 — os de 31/07 estavam defasados em 1 a 47
> posições (a reescrita do Capítulo 6 empurrou tudo a partir de ¶410).

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
- [ ] Lista de Ilustrações com 22 entradas e Lista de Quadros com 12 — o script confere a contagem; a paginação só no Word, após atualizar campos.
- [ ] Sumário atualizado: títulos de seção mudaram no SS7 e o sumário é campo automático. O `settings.xml` precisa de `<w:updateFields w:val="true"/>` para o Word oferecer a atualização ao abrir — sem ele, Sumário e Listas saem defasados no PDF em silêncio. **A tag já sumiu uma vez** (detectada ausente em 20/08/2026, quando as listas já tinham crescido para 22 figuras e 12 quadros); por isso o script passou a verificá-la. Alternativa manual: Ctrl+A / F9 no Word.

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
