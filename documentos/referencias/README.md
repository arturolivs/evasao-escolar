# Referências bibliográficas do TCC

**24 referências** na lista do `monografia-artur-oliveira-engenharia-de-software-2026.docx`,
todas citadas em algum ponto do texto
(nenhuma órfã) e todas com fonte verificada — autores, ano, veículo e páginas conferidos antes de
entrar no documento.

**Regra vigente desde 30/07/2026: só entra no texto obra com cópia local nesta pasta.** Os 21 PDFs
cobrem todas as referências bibliográficas; as três entradas do INEP são fontes de dados, cujos
arquivos brutos estão em `evasao-escolar/data/raw/`.

Foram **removidas** por não ter cópia disponível — três pagas, um livro comercial e um livro sem PDF
oficial: TINTO (1975), RUMBERGER (2011), ROMERO & VENTURA (2010), MOLNAR (2022) e HUNTER (2007).
As passagens que dependiam delas foram reancoradas em obras com PDF (backup do estado anterior em
`documentos/TCC_ANTES_REMOCAO_REFS.docx`).

Cada linha liga o **arquivo em disco** à **forma como a obra é citada** no `.docx`. A coluna
"Onde aparece" traz o número do parágrafo (índice de `python-docx`), para localizar rápido.

---

## A. Fundamentação sobre evasão e mineração de dados educacionais

| Arquivo | Referência | Citação no texto | Onde aparece |
|---|---|---|---|
| `BAKER_YACEF_2009_JEDM.pdf` (14 p.) | BAKER, R. S. J. D.; YACEF, K. The state of educational data mining in 2009. *JEDM*, v. 1, n. 1, p. 3–16, 2009. | `(ROMERO; VENTURA, 2010; BAKER; YACEF, 2009)` · `Baker e Yacef (2009)…` | ¶245 · ¶281 |
| `CORTEZ_SILVA_2008_StudentPerformance.pdf` (8 p.) | CORTEZ, P.; SILVA, A. Using data mining to predict secondary school student performance. In: *FUBUTEC*, 5., 2008. p. 5–12. | `(CORTEZ; SILVA, 2008)` · `Cortez e Silva (2008)…` | ¶245 · ¶281 |
| `JESUS_GUSMAO_2024_RBIE.pdf` (35 p.) | JESUS, J. A. de; GUSMÃO, R. P. de. Investigação da evasão estudantil… *RBIE*, v. 32, p. 807–841, 2024. | `(JESUS; GUSMÃO, 2024; …)` · `Jesus e Gusmão (2024)…` | ¶245 · ¶287 |
| `NASCIMENTO_et_al_2024_RBIE.pdf` (25 p.) | NASCIMENTO, F. F. do et al. Técnicas de mineração de dados e aprendizado de máquina aplicados à evasão estudantil. *RBIE*, v. 32, p. 270–294, 2024. | `(…; NASCIMENTO et al., 2024)` · `Nascimento et al. (2024)…` | ¶245 · ¶287 |
| `TEODORO_KAPPEL_2020_RBIE.pdf` (26 p.) | TEODORO, L. de A.; KAPPEL, M. A. A. Aplicação de técnicas de aprendizado de máquina… *RBIE*, v. 28, p. 838–863, 2020. | `(TEODORO; KAPPEL, 2020)` · `Teodoro e Kappel (2020)…` | ¶245 · ¶287 |

## B. Modelos, interpretabilidade e método

| Arquivo | Referência | Citação no texto | Onde aparece |
|---|---|---|---|
| `BREIMAN_2001_RandomForests.pdf` (33 p.) | BREIMAN, L. Random forests. *Machine Learning*, v. 45, n. 1, p. 5–32, 2001. | `Breiman (2001) propôs as florestas aleatórias…` | ¶283 |
| `CHEN_GUESTRIN_2016_XGBoost.pdf` (13 p.) | CHEN, T.; GUESTRIN, C. XGBoost: a scalable tree boosting system. In: *KDD*, 2016. p. 785–794. | `Chen e Guestrin (2016)…` · `o XGBoost (CHEN; GUESTRIN, 2016)` | ¶283 · ¶359 |
| `LUNDBERG_LEE_2017_SHAP.pdf` (10 p.) | LUNDBERG, S. M.; LEE, S. I. A unified approach to interpreting model predictions. In: *NeurIPS*, 30., 2017. p. 4765–4774. | `Lundberg e Lee (2017)…` · `a biblioteca SHAP (LUNDBERG; LEE, 2017)` · `o SHAP (LUNDBERG; LEE, 2017)` | ¶285 · ¶360 · ¶471 |
| `RIBEIRO_SINGH_GUESTRIN_2016_LIME.pdf` (10 p.) | RIBEIRO, M. T.; SINGH, S.; GUESTRIN, C. "Why should I trust you?" In: *KDD*, 2016. p. 1135–1144. | `…o LIME, de Ribeiro, Singh e Guestrin (2016)…` | ¶285 |
| `CHAPMAN_et_al_2000_CRISP-DM.pdf` (76 p.) | CHAPMAN, P. et al. *CRISP-DM 1.0*: step-by-step data mining guide. Copenhagen: SPSS, 2000. | `o processo CRISP-DM (CHAPMAN et al., 2000)` | ¶291 |
| `GUYON_ELISSEEFF_2003_FeatureSelection.pdf` (26 p.) | GUYON, I.; ELISSEEFF, A. An introduction to variable and feature selection. *JMLR*, v. 3, p. 1157–1182, 2003. | `…critérios guiaram os cortes, alinhados às diretrizes … (GUYON; ELISSEEFF, 2003)` | ¶313 |
| `SCULLEY_et_al_2015_TechnicalDebtML.pdf` (9 p.) | SCULLEY, D. et al. Hidden technical debt in machine learning systems. In: *NeurIPS*, 28., 2015. p. 2503–2511. | `…risco já documentado como característico de sistemas de aprendizado de máquina em produção (SCULLEY et al., 2015)` | ¶375 |
| `BAROCAS_HARDT_NARAYANAN_2023_FairnessML.pdf` (294 p.) | BAROCAS, S.; HARDT, M.; NARAYANAN, A. *Fairness and machine learning*. Cambridge: MIT Press, 2023. | `…na linha do que a literatura recomenda para sistemas preditivos aplicados a políticas públicas (BAROCAS; HARDT; NARAYANAN, 2023)` | ¶491 |

## C. Bibliotecas e ferramentas

| Arquivo | Referência | Citação no texto | Onde aparece |
|---|---|---|---|
| `PEDREGOSA_et_al_2011_scikit-learn.pdf` (6 p.) | PEDREGOSA, F. et al. Scikit-learn: machine learning in Python. *JMLR*, v. 12, p. 2825–2830, 2011. | `o scikit-learn (PEDREGOSA et al., 2011)` | ¶359 |
| `McKINNEY_2010_pandas.pdf` (6 p.) | McKINNEY, W. Data structures for statistical computing in Python. In: *Python in Science Conference*, 9., 2010. p. 56–61. | `as bibliotecas pandas (McKINNEY, 2010)…` | ¶358 |
| `HARRIS_et_al_2020_NumPy.pdf` (6 p.) | HARRIS, C. R. et al. Array programming with NumPy. *Nature*, v. 585, n. 7825, p. 357–362, 2020. | `…e NumPy (HARRIS et al., 2020)` | ¶358 |

## D. Fontes de dados do INEP

Distinguidas por letra conforme a NBR 6023 (mesmo autor, mesmo ano; letras na ordem alfabética dos
títulos). Não são texto e sim dados — os arquivos brutos já estão em `evasao-escolar/data/raw/`.

| Letra | Referência | Onde é citada |
|---|---|---|
| **2024a** | BRASIL. INEP. *Censo Escolar da Educação Básica*: microdados 2022–2024. Brasília: INEP, 2024a. | ¶243 (oferta de tempo integral) · ¶244 (universo da rede) · ¶300 (leitura dos microdados) |
| **2024b** | BRASIL. INEP. *Indicadores educacionais*: INSE, IRD, TDI e AFD. Brasília: INEP, 2024b. | ¶303 (integração dos indicadores) · ¶393 (definição do INSE) |
| **2024c** | BRASIL. INEP. *Taxas de rendimento escolar*: 2022–2024. Brasília: INEP, 2024c. | ¶246 (série 2,05/1,37/0,96%) · ¶279 (definição de abandono e evasão) · ¶303 (integração das taxas) |

---
