---
name: validar-ambiente
description: Confere se o ambiente Python instalado é idêntico ao ambiente de referência fixado no requirements.txt do projeto de evasão escolar. Usar SEMPRE antes de treinar modelos, regerar métricas, refazer figuras ou atualizar qualquer número do Capítulo 6 da monografia — a partição do GroupKFold muda entre versões do scikit-learn e altera resultados sem que dados ou código mudem. Também usar quando números não reproduzem, quando métricas mudam sem explicação, ou ao configurar a máquina.
---

# Validar Ambiente de Referência

**Rodar isto primeiro, antes das outras validações.** Número gerado em ambiente errado é
número inválido — e isso já custou uma rodada inteira de retrabalho neste projeto.

## Por que existe

O `requirements.txt` fixa todas as versões com `==`, não `>=`. O motivo está documentado em
`documentos/SS8_TEXTO_PARA_O_TCC.md` (seção 6): ao reexecutar os notebooks sob outra versão do
scikit-learn, **as métricas dos Quadros 9 e 10 mudaram sem que dados ou código mudassem** — o
`GroupKFold` foi reimplementado e passou a produzir partições diferentes. A prova é que o
modelo "sem sistema" (média da rede), que não usa nenhuma característica e depende *só* da
partição, também mudou:

- folds antes: `[2,408 · 3,653 · 1,828 · 4,633 · 4,059]`
- folds depois: `[2,524 · 3,305 · 3,967 · 3,053 · 4,228]`

Consequência narrativa que já foi absorvida no texto: o Spearman do modelo adotado caiu de
0,458 → 0,416 e o XGBoost deixou de liderar isoladamente.

`GroupShuffleSplit` (notebook 14, experimento SS13) é estável entre versões — só o
`GroupKFold` quebra.

## Ambiente de referência

**Python 3.14, Windows.** Versões em `evasao-escolar/requirements.txt`.

## Verificação

A partir de `evasao-escolar/`:

```bash
python - <<'PY'
import subprocess, sys
req = {}
for l in open("requirements.txt", encoding="utf-8"):
    l = l.strip()
    if not l or l.startswith("#") or "==" not in l: continue
    p, v = l.split("=="); req[p.strip().lower()] = v.strip()
out = subprocess.run([sys.executable, "-m", "pip", "list", "--format=freeze"],
                     capture_output=True, text=True).stdout
inst = {}
for l in out.splitlines():
    if "==" in l:
        p, v = l.split("=="); inst[p.strip().lower()] = v.strip()
ok, div, falta = [], [], []
for p, v in sorted(req.items()):
    if p not in inst: falta.append(p)
    elif inst[p] != v: div.append((p, v, inst[p]))
    else: ok.append(p)
print(f"python {sys.version.split()[0]}  (referencia: 3.14)")
print(f"{len(ok)}/{len(req)} pacotes na versao fixada")
for p, esperado, achado in div: print(f"  XX {p}: requirements={esperado}  instalado={achado}")
for p in falta: print(f"  ?? {p}: nao instalado")
if not div and not falta: print("  ambiente identico ao de referencia")
PY
```

Última execução verificada: **15/15 pacotes na versão fixada, Python 3.14.5** — ambiente
alinhado. (Os alertas históricos de deriva do `shap` 0.52.0 e do scikit-learn 1.9.0 nos
documentos `SS13_TEXTO_PARA_O_TCC.md` e `PLANO_DE_FINALIZACAO.md` já estão resolvidos.)

## Se houver divergência

1. **Não regerar nada** enquanto não alinhar. Reportar a divergência ao autor primeiro.
2. Corrigir com `pip install -r requirements.txt` (o `==` força o downgrade).
3. Divergência que **importa** para números de métrica: `scikit-learn`, `xgboost`, `numpy`,
   `scipy`. Divergência que importa só para **figuras** do SHAP: `shap`, `matplotlib`.
4. Depois de alinhar, rodar `/validar-numeros` para confirmar que os números do `.docx`
   continuam batendo.

## Pegadinha conhecida

Alinhar o ambiente **não é suficiente** se os artefatos ficaram para trás. Conferir também se
`data/processed/features.parquet` é mais novo que `models/*.joblib` — modelo treinado em
features velhas é erro silencioso. Verificação forte disponível em `/revisar-projeto`
(pilar 7), que regera o dataset em memória e compara com o parquet em disco.
