# Estado do projeto e próximos passos

Levantamento de 21 de julho de 2026.

---

## 1. Onde o projeto está

### O que está pronto

| Frente | Situação |
|---|---|
| Sistema (código) | Completo, da leitura dos dados públicos ao painel. **98 testes passando** |
| Modelo | Treinado, ajustado e avaliado nos dois protocolos. Resultados verificados e reproduzíveis |
| Análise das 38 informações | Concluída, com saída em CSV e quatro figuras |
| Painel | Funcionando (`streamlit run app/dashboard.py`) |
| Monografia | Sete capítulos escritos, 18 figuras, 10 quadros |
| Guia de defesa | Roteiro completo, com demonstração e arguição |
| README | Atualizado com o pipeline e o dashboard |

---

### Bloco A — Fechar a monografia 

**A1. Capítulo 2 — citações.** É a maior lacuna. A fundamentação teórica e os
trabalhos relacionados estão escritos, mas sem nenhuma fonte citada. Há uma nota
explícita no corpo do texto marcando isso. Em uma monografia, é o primeiro lugar
onde a banca aperta.

O que fazer: levantar de 6 a 10 trabalhos sobre predição de evasão e inserir as
citações nos pontos onde o texto afirma o que "a literatura mostra". Priorize os
que trabalham em nível de escola ou com dados públicos — são os que sustentam a
comparação da seção 2.2.

**A2. Referências.** A lista atual tem só as fontes usadas no desenvolvimento —
INEP, Chen & Guestrin, Freire, Lundberg & Lee. Falta a bibliografia da revisão,
que sai naturalmente do B1. Uma nota no documento já registra isso.

**A3. Elementos pré-textuais.** Nome do orientador na folha de rosto,
agradecimentos, ficha catalográfica (gerador da PUC, link no próprio documento) e
composição da banca.

**A4. Atualizar os campos no Word.** Abra o documento; ele pergunta se deve
atualizar os campos — aceite. É isso que preenche a paginação do Sumário. Se não
perguntar, `Ctrl+A` e depois `F9`. Confira em seguida se a Lista de Ilustrações
(18 entradas) e a Lista de Quadros (9 entradas) estão coerentes com o corpo.

**A5. Leitura final em voz alta.** Especificamente para caçar jargão remanescente
de análise de dados — foi o ponto do orientador. As métricas já aparecem nomeadas
pelo que medem, com o termo técnico entre parênteses uma única vez, na seção
6.3.1.

---

### Bloco B — Técnico, opcional antes da defesa

**B1. Empacotar em contêiner (Fase 12).** É a única lacuna técnica declarada, e
está prevista no capítulo de implantação como trabalho futuro. Fazer antes da
defesa transforma "prevê-se empacotar" em "está empacotado" — bom, mas não
essencial. Meio dia de trabalho.

**B2. Remoção da dependência `shap`.** Avaliada em sessão anterior: só faz
sentido se houver um motivo concreto (falha de instalação, lentidão). O XGBoost
calcula as mesmas contribuições nativamente, então dá para tirar o pacote sem
perder funcionalidade — o custo é redesenhar dois gráficos. **Não faça isso antes
da defesa**: mexe em `explain.py`, no serviço do painel e em três figuras da
monografia.

**B3. Correção do viés de equidade.** É o primeiro item dos trabalhos futuros da
monografia e deve continuar assim. Resolver agora significaria refazer a
avaliação e reescrever a seção 6.5.4 — muito risco, pouco tempo. Na defesa, o
valor está em *reconhecer* a limitação, não em tê-la resolvido.

---

## 3. Pontos de atenção

**3.1. O modelo treinado não está versionado.** `models/xgboost_v1.joblib` e
`data/` estão fora do Git. É a decisão certa (arquivo binário grande), mas
significa que, se a máquina falhar, o modelo se perde. Ele é reproduzível — basta
rodar os notebooks 05 e 08 —, o que leva alguns minutos. Ainda assim, vale uma
cópia em outro lugar até a defesa.

**3.2. Ordem de execução do pipeline.** O notebook 07 passou a avaliar também o
XGBoost, que ele carrega do disco. **Rode o 08 antes do 07**, ou o 07 falha. Está
registrado no README.

---


## 4. Comandos de referência

```bash
# Painel
cd evasao-escolar && streamlit run app/dashboard.py     # http://localhost:8501

# Testes
cd evasao-escolar && pytest tests/ -q                   # 98 passando

# Regenerar modelo e figuras do zero (ordem importa)
python notebooks/05_feature_engineering.py
python notebooks/08_tuning_xgboost.py
python notebooks/07_avaliacao_complementar.py
python notebooks/09_shap_diagnostico.py
python notebooks/12_figuras_monografia.py
python notebooks/13_estatisticas_features.py
```
