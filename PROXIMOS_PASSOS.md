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

### Arquivos que valem hoje

| Arquivo | Papel |
|---|---|
| `TCC_Evasao_Escolar_2026.docx` | **Monografia de referência.** É a versão consolidada, com os números conferidos |
| `Guia_Apresentacao_TCC_Consolidado.docx` | Roteiro de defesa |
| `evasao-escolar/` | O sistema |
| `Modelo TCC Engenharia de Software 2022.docx` | Versão de trabalho anterior, com marcações coloridas. Ver item 3.3 |

---

## 2. O que falta — em ordem de prioridade

Se a defesa estiver a menos de duas semanas, faça os blocos A e B e ignore o D.

### Bloco A — Higiene do repositório (30 minutos, faça hoje)

**A1. Commitar o trabalho.** É o risco mais concreto agora: o último commit é de
6 dias atrás e nada das últimas sessões está versionado. São 9 arquivos alterados
e 15 não rastreados, incluindo a monografia, o guia, dois notebooks novos e todas
as figuras E1–E8.

```bash
cd /c/Users/Suporte/Documents/monografia
git add -A
git commit -m "Monografia consolidada, análise estatística das 38 informações e correção da captura"
```

Se preferir separar, três commits fazem sentido: (i) correção do vazamento e
notebooks 12/13, (ii) figuras e métricas regeneradas, (iii) documentos do TCC.

**A2. Limpar os arquivos soltos da raiz.** `gerar_tcc.py` e `a.txt` são duas
cópias quase idênticas do script que gerou o *esqueleto* antigo da monografia —
aquele com números que não batem com o projeto (mediana de 4,2%, São Francisco a
5,2%, correlação de 0,78, captura de 28%). Se alguém rodar isso por engano,
sobrescreve a monografia boa com dados inventados.

```bash
mkdir -p ignore && mv a.txt gerar_tcc.py ignore/    # ignore/ já está no .gitignore
```

**A3. Restaurar ou aposentar o `decisoes_projeto.md`.** Ele foi apagado e o
README já não o cita mais. Se as justificativas metodológicas dele ainda
interessam, recupere com `git checkout HEAD -- decisoes_projeto.md`; senão,
confirme a remoção no commit.

---

### Bloco B — Fechar a monografia (caminho crítico)

Estes quatro itens são o que separa o documento de estar pronto para a banca.

**B1. Capítulo 2 — citações.** É a maior lacuna. A fundamentação teórica e os
trabalhos relacionados estão escritos, mas sem nenhuma fonte citada. Há uma nota
explícita no corpo do texto marcando isso. Em uma monografia, é o primeiro lugar
onde a banca aperta.

O que fazer: levantar de 6 a 10 trabalhos sobre predição de evasão e inserir as
citações nos pontos onde o texto afirma o que "a literatura mostra". Priorize os
que trabalham em nível de escola ou com dados públicos — são os que sustentam a
comparação da seção 2.2.

**B2. Referências.** A lista atual tem só as fontes usadas no desenvolvimento —
INEP, Chen & Guestrin, Freire, Lundberg & Lee. Falta a bibliografia da revisão,
que sai naturalmente do B1. Uma nota no documento já registra isso.

> Atenção: o esqueleto original trazia referências que não localizei em lugar
> nenhum (OLIVEIRA & SILVA, SANTOS et al., SILVA & SANTOS). Não foram copiadas
> para a versão consolidada, e não devem ser — citar fonte inexistente é falta
> grave em banca.

**B3. Elementos pré-textuais.** Nome do orientador na folha de rosto,
agradecimentos, ficha catalográfica (gerador da PUC, link no próprio documento) e
composição da banca.

**B4. Atualizar os campos no Word.** Abra o documento; ele pergunta se deve
atualizar os campos — aceite. É isso que preenche a paginação do Sumário. Se não
perguntar, `Ctrl+A` e depois `F9`. Confira em seguida se a Lista de Ilustrações
(18 entradas) e a Lista de Quadros (9 entradas) estão coerentes com o corpo.

**B5. Leitura final em voz alta.** Especificamente para caçar jargão remanescente
de análise de dados — foi o ponto do orientador. As métricas já aparecem nomeadas
pelo que medem, com o termo técnico entre parênteses uma única vez, na seção
6.3.1.

---

### Bloco C — Preparar a defesa

**C1. Montar os slides** a partir do `Guia_Apresentacao_TCC_Consolidado.docx`. O
guia já traz, por bloco, o que colocar no slide e o que dizer. São 10 blocos em
20 minutos.

**C2. Ensaiar três vezes com cronômetro.** O que mais estoura o tempo é a
demonstração. O bloco de arquitetura merece o tempo que está reservado (4 min) —
o curso é Engenharia de Software, e é ali que isso aparece.

**C3. Plano B da demonstração.** Capture as telas do painel em imagem e deixe em
um slide oculto. Se o notebook falhar na hora, você segue sem improvisar.

**C4. Decorar quatro números:** 2.043 alunos em 2024; 10% das escolas concentram
76% dos casos; 38 informações de mais de 400; metade da lista prioritária contra
7 em cada 100 do acaso.

---

### Bloco D — Técnico, opcional antes da defesa

**D1. Empacotar em contêiner (Fase 12).** É a única lacuna técnica declarada, e
está prevista no capítulo de implantação como trabalho futuro. Fazer antes da
defesa transforma "prevê-se empacotar" em "está empacotado" — bom, mas não
essencial. Meio dia de trabalho.

**D2. Remoção da dependência `shap`.** Avaliada em sessão anterior: só faz
sentido se houver um motivo concreto (falha de instalação, lentidão). O XGBoost
calcula as mesmas contribuições nativamente, então dá para tirar o pacote sem
perder funcionalidade — o custo é redesenhar dois gráficos. **Não faça isso antes
da defesa**: mexe em `explain.py`, no serviço do painel e em três figuras da
monografia.

**D3. Correção do viés de equidade.** É o primeiro item dos trabalhos futuros da
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

**3.3. O documento antigo tem uma contradição interna.** No
`Modelo TCC Engenharia de Software 2022.docx`, o texto foi corrigido para os
números honestos de captura (30%, 54%, 64%), mas a figura embutida ainda é a
versão anterior, que mostra 34%, 60% e 69% — a imagem foi copiada para dentro do
arquivo antes da correção. Como esse documento foi substituído pelo
`TCC_Evasao_Escolar_2026.docx`, o caminho mais simples é **aposentá-lo**: mova
para `ignore/` e mantenha só a versão consolidada como referência. Se quiser
continuar usando as marcações coloridas, avise que eu troco a figura.

**3.4. Por que os números de captura mudaram.** A versão anterior calculava o
alcance da lista usando o modelo treinado com *todos* os anos, inclusive o de
teste. Isso inflava o resultado. Agora o modelo é treinado só no par anterior, e
os números batem com a avaliação independente do notebook 07. Se a banca
perguntar por que o trabalho reporta 30% e não um número maior, a resposta é
essa — e ela conta a favor.

---

## 4. Sequência sugerida

| Quando | O quê |
|---|---|
| Hoje | A1, A2, A3 — commitar e limpar |
| Esta semana | B1 e B2 — citações e referências (é o maior bloco de trabalho) |
| Em seguida | B3, B4, B5 — pré-textuais e revisão final |
| Última semana | C1 a C4 — slides e ensaios |
| Se sobrar tempo | D1 — contêiner |

---

## 5. Comandos de referência

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
