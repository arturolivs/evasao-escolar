# Guia de demonstração — notebooks e painel

28/10/2026 · Artur Oliveira Santiago

## Visão geral

A demonstração entra logo depois do último slide e dura cerca de 15 minutos: testes, dois notebooks ao vivo, a predição de 2025 e o painel. O objetivo é provar ao orientador que o sistema descrito na monografia existe, roda e devolve os números dos Quadros 9 e 10.

Regra de ouro: **nada pesado roda ao vivo**. Tudo é gerado na véspera; ao vivo só rodam os passos de segundos, e o resto é mostrado pelas saídas já salvas em `reports/`.

## Preparação (véspera)

Hoje a máquina **não roda o projeto**: `data/raw/` só tem os README, e não existem `data/processed/` nem `models/`. Os passos abaixo resolvem isso e devem terminar ao menos um dia antes.

1. **Ambiente.** Ativar a venv da raiz (`F:\repos\evasao-escolar\.venv\Scripts\activate`) e rodar `pip install -r evasao-escolar\requirements.txt`. Falta só o `python-docx`; os outros 15 pacotes já batem.
2. **Dados brutos.** Baixar os 22 arquivos do INEP pelos links de cada `data/raw/*/README.md`, com os nomes exatos. Renomear `AFD_ESCOLAS_2023_v1.1.xlsx` para `AFD_ESCOLAS_2023.xlsx`. Conferir os SHA-256.
3. **Pipeline completo**, de dentro de `evasao-escolar/`, na ordem do `CLAUDE.md` (o 08 antes do 07). Cronometrar cada passo: os tempos decidem o que pode rodar ao vivo.
4. **Conferir os números.** `pytest` deve passar os 138 testes. Os Quadros 9 e 10 devem bater com `reports/metricas_cv_repetida.csv` e `reports/metricas_xgboost.csv`.
5. **Ensaio cronometrado** de todo o roteiro abaixo, com o projetor ou na resolução da sala.

Checklist do dia:

- [ ] Notebook na tomada, modo de energia em alto desempenho, notificações desligadas
- [ ] Terminal com fonte grande (18 pt ou mais), venv já ativa, pasta `evasao-escolar/` aberta
- [ ] Painel já iniciado uma vez para aquecer o cache (a primeira carga calcula o SHAP de todas as escolas)
- [ ] Pasta `reports/figuras/` aberta no explorador, com as figuras G1–G5 e S3 à mão
- [ ] Cópia de `data/`, `models/` e `reports/` em pendrive

## Roteiro da demonstração

Seis blocos em cerca de 15 minutos, do código para o gestor. Os tempos são uma meta; ajuste-os pelo ensaio.

| Min. | Bloco | O que fazer | Frase-chave |
| --- | --- | --- | --- |
| 0–2 | Estrutura | Mostrar `src/` (data → features → models → recommend) e `notebooks/` | "O fluxo é de mão única e cada etapa troca dados por parquet." |
| 2–4 | Testes | `pytest` (cerca de 25 s, 138 testes) | "O casamento t→t+1, o veto a município repetido entre treino e teste e a aditividade do SHAP são travados por teste." |
| 4–7 | Notebook ao vivo | `python notebooks/01_exploracao_inicial.py` ou o 13 (ver a próxima seção) | "Este script monta o painel escola × ano direto do microdado do INEP." |
| 7–9 | Resultados | Abrir `reports/metricas_*.csv` e as figuras G1–G5 | "Estes são os arquivos de onde saem os Quadros 9 e 10." |
| 9–10 | Predição | `python -m src.models.predict 2024` | "Com os dados de 2024, o sistema ordena as escolas pelo risco de 2025." |
| 10–15 | Painel | `streamlit run app/dashboard.py`, nas três abas | "Aqui o gestor vê a lista, o porquê e a ressalva." |

## Os notebooks

Os notebooks são scripts `.py`, não `.ipynb`: rodam no terminal, imprimem no console e salvam figuras em `reports/figuras/`. Para a banca, abra o arquivo no editor (a docstring do topo lista as perguntas que ele responde), rode-o e mostre a figura que ele gerou.

Ao vivo, rode só os notebooks que o ensaio cronometrar em menos de 1 minuto. Os de modelagem (06, 07, 08, com GridSearch e 20 repetições de validação) não rodam ao vivo: mostre o código e as saídas já salvas.

| Notebook | Responde | Mostrar | Ao vivo? |
| --- | --- | --- | --- |
| 01 exploração inicial | Monta o painel escola × ano a partir do Censo | Console: escolas por ano | Sim, se for rápido no ensaio |
| 02 descritivas | Porte, infraestrutura, urbano × rural (A1–A7) | `A6_tendencias_temporais.png` | Opcional |
| 03 taxas de rendimento | Distribuição e tendência do abandono (B1–B10) | `B2_distribuicao_abandono.png`, `B3_tendencia_temporal.png` | Opcional |
| 04 indicadores | IRD, INSE, TDI, AFD contra o abandono (C1–C8) | `C5_correlacoes.png` | Não |
| 05 engenharia de características | Alvo, qualidade e correlações (F1–F6) | `F2_target.png` | Não |
| 06 baselines | Ridge e Random Forest, GroupKFold por município | `reports/metricas_baselines.csv` | Não |
| 08 tuning do XGBoost | Hiperparâmetros e teste temporal | `reports/metricas_xgboost.csv`, `X4_validacao_temporal.png` | Não |
| 07 avaliação complementar | Precision@K por K, CV repetida 20× | `G3_cv_repetida.png`, `G4_tamanho_da_lista.png` | Não |
| 09 SHAP e diagnóstico | Peso das características, explicação por escola, equidade | `G5_peso_caracteristicas.png`, `S3_waterfall_alto_risco.png`, `S5_equidade_grupos.png` | Não |
| 11 IED e ICG | Ablação: por que esses indicadores ficaram de fora | `D1_ablacao_ied_icg.png` | Não |
| 13 estatísticas das características | Descritiva e teste de cada característica | `E7_relacao_todas.png` | Sim, se for rápido no ensaio |
| 14 cenários temporais (SS13) | 2022→2023 × 2023→2024 | `E9_ss13_cenarios.png` | Não |
| 16 figuras simplificadas | Figuras do Cap. 6 em linguagem de gestor | `G1_funil_amostra.png`, `G2_teste_ano_nunca_visto.png` | Sim, se for rápido no ensaio |

Os notebooks 10 e 12 só geram diagramas e figuras da monografia, e não precisam aparecer. O 15 (varredura de números) tem caminhos fixos de outra máquina (`C:\Users\Suporte\...`) e falha aqui sem ajuste; não o rode ao vivo.

Para a banca, a ordem de execução vale um comentário: o 08 roda antes do 07, porque o 07 carrega o modelo que o 08 salva.

## O painel

O painel é a parte que o orientador mais vai querer ver: é onde o modelo vira decisão de gestor. Abra com `streamlit run app/dashboard.py`, de dentro de `evasao-escolar/`. Ele carrega `models/xgboost_v1.joblib` e o conjunto de características, e calcula o SHAP de todas as escolas na primeira carga; por isso, inicie-o antes de começar a falar.

Toda a regra de negócio fica em `src/recommend/service.py`, e o painel só apresenta. Vale dizer isso: é o que permite testar a regra com `pytest` sem abrir a interface.

**Barra lateral (30 s).** O ano dos indicadores (t), mesorregião, município, busca por nome e o controle "Marcar como prioritárias as N de maior risco", de 10 a 200. Diga que o risco se refere ao abandono do ano seguinte (t+1).

**Aba Ranking de risco (1–2 min).**

1. Mostre os três indicadores do topo: escolas no recorte, prioritárias e risco médio.
2. Mova o controle de N de 50 para 150 (cerca de 10% da rede). "O gestor escolhe o tamanho da lista conforme a capacidade de atendimento, sem retreinar nada."
3. Filtre por uma mesorregião e um município.
4. Aponte o botão de download: o CSV leva a ressalva de equidade numa coluna própria, porque a planilha circula fora do painel.

**Aba Detalhe da escola (2 min), o ponto alto.**

1. Escolha uma escola do topo do ranking.
2. Leia o diagnóstico: "Alerta" (abandona mais que o previsto), "Resiliente" (menos) ou "Dentro do esperado".
3. Mostre "Por que esta escola foi pontuada assim": cada característica, o valor dela na escola e se ela aumenta ou reduz o risco.
4. Diga que a explicação é **diagnóstica, não causal**: o painel aponta onde olhar, não o que fazer.
5. Escolha depois uma escola indígena ou quilombola e mostre o aviso "Ressalva de equidade".

**Aba Panorama (1 min).** A distribuição do risco previsto e o risco médio por localização. Use este gráfico para falar do viés: o modelo prevê 11,08% para as escolas de localização diferenciada, contra 4,96% observados.

O seletor de ano mostra os anos que têm abandono observado, porque o diagnóstico compara previsto e real. O ranking de 2025 vem da linha de comando (`python -m src.models.predict 2024`), que lista as 10 escolas de maior risco. Confirme isso no ensaio.

## O que dizer depois do PPT

A mensagem central: o sistema **acerta a ordem**, não o valor. Entre as escolas que ele põe no topo, 41,8% estão de fato entre as de maior abandono, contra 8,9% de uma lista sem modelo (4,7 vezes mais).

Escala do problema: 39 características, 1.586 observações escola × ano, 801 escolas, 185 municípios. O treino usa os anos 2022 e 2023; 2024 serve só para prever 2025.

Os números, todos nos CSVs de `reports/`:

| | Dummy (média) | Ridge | Random Forest | XGBoost |
| --- | --- | --- | --- | --- |
| CV repetida — Spearman | — | 0,428 | **0,431** | 0,416 |
| CV repetida — Precision@K | 0,068 | **0,513** | 0,501 | 0,504 |
| Teste temporal — Spearman | — | 0,330 | 0,343 | **0,348** |
| Teste temporal — Precision@K | 0,089 | 0,380 | 0,405 | **0,418** |
| Teste temporal — RMSE | **2,540** | 2,891 | 2,751 | 2,874 |

Três ressalvas que devem ser ditas por você, antes que a banca pergunte:

- **RMSE pior que o dummy.** No teste temporal o XGBoost erra mais o valor que a simples média (R² de −0,33). Por isso o critério é ordenação (Precision@K e Spearman), e não RMSE.
- **Os modelos empatam.** Os três têm intervalos de confiança sobrepostos, e o Random Forest empata ou supera em vários pontos. O XGBoost foi escolhido pelo teste temporal e pelo SHAP construído sobre ele, não por ser superior em tudo.
- **Há viés medido.** Nas 41 escolas indígenas e quilombolas o modelo prevê 11,08% contra 4,96% observados (resíduo médio de −6,12 p.p.). Urbanas (+0,07) e rurais (+0,38) ficam calibradas. Agrava que `is_loc_diferenciada` é a característica nº 1 por ganho (0,239). Por isso o painel e o CSV carregam a ressalva.

O resultado por transição anual (SS13) mostra que 2022→2023 rende mais (Spearman 0,469 / P@K 0,627) que 2023→2024 (0,367 / 0,381). Isso acompanha a queda do abandono médio, de 1,36% para 0,88%: com menos abandono, há menos sinal para ordenar.

Para fechar, uma frase de engenharia: o ambiente é fixado com `==` porque uma troca de versão do scikit-learn mudou a partição do GroupKFold e as métricas, sem mudar dado nem código. E o `features.parquet` regerado do zero saiu idêntico bit a bit.

## Perguntas prováveis

| Pergunta | Resposta curta | Onde mostrar |
| --- | --- | --- |
| Como você garante que não há vazamento? | Características de t preveem o abandono de t+1; o mesmo município nunca fica em treino e teste (GroupKFold por município); a imputação usa só a mesorregião no mesmo ano. | `tests/test_build_target.py`, `tests/test_models.py` |
| Por que não o Random Forest, se ele empata? | Empata na CV, mas o XGBoost lidera o teste temporal, que simula o uso real, e o SHAP foi construído sobre ele. Não é superioridade geral. | Quadros 9 e 10 |
| De onde saem 1.586 observações, se o painel tem 2.392? | Cada etapa da redução está rastreada no Quadro 5 e travada por teste. | `G1_funil_amostra.png`, `tests/test_rastreabilidade_amostra.py` |
| O SHAP diz o que a escola deve fazer? | Não. É uma leitura diagnóstica, correlacional; o painel não recomenda ações. | Aba Detalhe da escola |
| O que muda para escolas indígenas e quilombolas? | O modelo superestima o risco em 6,12 p.p.; a ressalva aparece no painel e no CSV. Corrigir isso é trabalho futuro. | Aba Panorama, `S5_equidade_grupos.png` |
| Os números se reproduzem em outra máquina? | Sim, com o ambiente fixado no `requirements.txt`; o GroupKFold muda entre versões do scikit-learn. | `requirements.txt` |
| Por que IED e ICG ficaram de fora? | A ablação mostrou que não agregam sinal. | `D1_ablacao_ied_icg.png` |
| Como se prevê um ano novo? | `python -m src.models.predict <ano>`, quando o INEP publicar os dados. | Terminal |

## Plano B

Se algo falhar ao vivo, não depure na frente da banca: diga o que aconteceu e passe ao material salvo. As 75 figuras e os CSVs de `reports/` estão no Git e abrem sem rodar nada.

| Falha | Causa provável | O que fazer |
| --- | --- | --- |
| `ModuleNotFoundError` | O terminal está no Python global, não na venv | Ativar `F:\repos\evasao-escolar\.venv` |
| `FileNotFoundError: Modelo não encontrado` | `models/` vazio ou 07 rodado antes do 08 | Mostrar as figuras G3–G5 e os CSVs |
| `FileNotFoundError` em `data/raw/` | Arquivo do INEP ausente ou com outro nome | Pular para os resultados salvos |
| Painel demora para abrir | Primeira carga calcula o SHAP de todas as escolas | Ter o painel já aberto antes de começar |
| Porta 8501 ocupada | Outra instância do Streamlit aberta | `streamlit run app/dashboard.py --server.port 8502` |
| Sem projetor ou sem a máquina | — | Gravação de tela do ensaio (2–3 min do painel) em pendrive |

A gravação de tela do ensaio é o seguro mais barato: grave o painel funcionando na véspera.
