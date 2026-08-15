# Guia das Figuras da Monografia

**Cada uma das 22 figuras explicada para quem não trabalha com dados**

Sistema de priorização de escolas em risco de evasão · Rede estadual de Pernambuco
Artur Oliveira Santiago · PUC-SP · 2026

---

## Como usar este guia

Cada figura recebe a mesma estrutura, e ela é deliberada:

- **Identificação** — arquivo, script que a gera e onde ela aparece no texto. Serve para
  refazer a figura sem procurar.
- **O que ela é, mecanicamente** — o que está em cada eixo, o que cada barra ou ponto
  representa, quantas observações entram. Sem isso, qualquer leitura é chute.
- **O que ela revela** — a leitura que interessa, com os números que estão na imagem.
- **Por que ela está no texto** — a decisão do trabalho que a figura sustenta. Uma figura
  que não sustenta nada deveria sair.
- **Como dizer em 20 segundos** — a fala pronta, sem jargão, para a apresentação.

Um alerta que vale para o documento inteiro: quase todas as figuras contam **observações
de escola × ano**, não escolas. O conjunto tem 1.586 observações de 801 escolas — a mesma
escola aparece em dois anos. Onde a contagem é de escolas, está dito.

Companheiro deste guia: `Guia_Apresentacao_Capitulo6.docx`, com o roteiro de fala.
A seção final aqui, **Três pontos a verificar**, registra divergências entre figura e texto
que encontrei ao conferir cada imagem contra o script que a gera. Vale ler antes da defesa.

---

## Índice

| Fig. | Assunto | Arquivo | Script |
|---|---|---|---|
| 1 | O problema: queda da média e concentração | `E1_problema_critico.png` | `12_figuras_monografia.py` |
| 2 | Casos de uso | `arq1_casos_uso.png` | `10_diagramas_arquitetura.py` |
| 3 | Pacotes | `arq2_pacotes.png` | `10_diagramas_arquitetura.py` |
| 4 | Componentes e fluxo de dados | `arq3_componentes.png` | `10_diagramas_arquitetura.py` |
| 5 | Atividades do pipeline | `arq4_atividades.png` | `10_diagramas_arquitetura.py` |
| 6 | Implantação | `arq5_implantacao.png` | `10_diagramas_arquitetura.py` |
| 7 | Funil 2.392 → 1.586 | `G1_funil_amostra.png` | `16_figuras_simplificadas.py` |
| 8 | O indicador previsto e a desigualdade entre grupos | `E2_alvo.png` | `12_figuras_monografia.py` |
| 9 | Distribuição das 23 características contínuas | `E5_distribuicoes.png` | `13_estatisticas_features.py` |
| 10 | Atributos de sim ou não | `E6_binarias.png` | `13_estatisticas_features.py` |
| 11 | Região do estado | `E8_mesorregiao.png` | `13_estatisticas_features.py` |
| 12 | As 38 características ordenadas pela relação | `E7_relacao_todas.png` | `13_estatisticas_features.py` |
| 13 | Desempenho nas 20 repetições | `G3_cv_repetida.png` | `16_figuras_simplificadas.py` |
| 14 | Erro do valor × acerto da ordem | `G2_teste_ano_nunca_visto.png` | `16_figuras_simplificadas.py` |
| 15 | Desempenho em cada transição anual | `E9_ss13_cenarios.png` | `14_ss13_cenarios_temporais.py` |
| 16 | Resíduo por escola, em alunos | `E10_residuos_transicoes_alunos.png` | `14_ss13_cenarios_temporais.py` |
| 17 | Ganho prático sobre a escolha ao acaso | `E4_desempenho.png` | `12_figuras_monografia.py` |
| 18 | Acerto e alcance por tamanho de lista | `G4_tamanho_da_lista.png` | `16_figuras_simplificadas.py` |
| 19 | As características que mais pesam | `G5_peso_caracteristicas.png` | `16_figuras_simplificadas.py` |
| 20 | Peso e direção de cada característica | `S2_shap_direcao.png` | `09_shap_diagnostico.py` |
| 21 | Explicação individual de uma escola | `S3_waterfall_alto_risco.png` | `09_shap_diagnostico.py` |
| 22 | Erro por grupo de localização | `S5_equidade_grupos.png` | `09_shap_diagnostico.py` |

---

# Parte 1 — O problema e a arquitetura (Figuras 1 a 6)

---

## Figura 1 — "Queda da taxa média da rede e concentração do abandono em 10% das escolas"

**Arquivo:** `E1_problema_critico.png` · **gerada por:** `notebooks/12_figuras_monografia.py` · **onde aparece:** Capítulo 1, na apresentação do problema.

### O que ela é, mecanicamente

Dois painéis que respondem a duas perguntas diferentes sobre o mesmo problema.

- **Esquerda:** uma linha com três pontos, um por ano. O eixo vertical é a taxa média de
  abandono da rede estadual: 2,05% em 2022, 1,37% em 2023, 0,96% em 2024.
- **Direita:** duas barras que repartem **os alunos que abandonaram em 2024** — não as
  escolas. A barra vermelha são os alunos que saíram das 79 escolas mais críticas (10% da
  rede); a cinza, os que saíram das outras 712.

### O que ela revela

A tensão que justifica o trabalho inteiro. A média da rede vem caindo — de longe, parece
um problema em vias de se resolver sozinho. Mas as 79 escolas mais críticas, 10% da rede,
concentram **76% de todos os alunos que abandonaram**. As outras 712 escolas juntas
respondem por 24%.

O problema não é difuso: é concentrado. E um problema concentrado não se enfrenta com
política de média — se enfrenta com priorização.

### Por que ela está no texto

É a figura que autoriza o restante da monografia. Se o abandono estivesse espalhado
uniformemente pela rede, um sistema de ordenação teria pouco a oferecer: atender qualquer
escola seria quase tão bom quanto atender outra. A concentração é o que torna a ordem
valiosa. Ela também antecipa a escolha do recorte de 10% para o tamanho da lista de
prioridade, usado em todo o Capítulo 6.

### Como dizer em 20 segundos

> "A taxa média da rede caiu de 2,05% para 0,96% em três anos, e olhando só para isso o
> problema parece estar se resolvendo. Mas o abandono não está espalhado: em 2024, 10% das
> escolas concentraram 76% dos alunos que saíram. É um problema concentrado, e problema
> concentrado se enfrenta escolhendo onde agir primeiro."

---

## Figura 2 — "Diagrama de casos de uso do sistema"

**Arquivo:** `arq1_casos_uso.png` · **gerada por:** `notebooks/10_diagramas_arquitetura.py` · **onde aparece:** Capítulo 4, na arquitetura.

### O que ela é, mecanicamente

Notação UML. Os bonecos são **atores** — quem interage com o sistema. As elipses dentro da
caixa são **casos de uso** — o que cada ator consegue fazer. A linha liga o ator à ação que
ele executa.

Três atores: o **Gestor** da Secretaria, o **Analista/Pesquisador** e o **INEP**, que não
opera nada, apenas fornece os dados (linha tracejada, «fornece»).

Cinco casos de uso: consultar o ranking de risco do ano seguinte, ver a explicação de uma
escola, inspecionar o diagnóstico de resíduos (equidade), executar o pipeline de dados e
treinar ou atualizar o modelo.

### O que ela revela

A divisão de responsabilidades. O gestor **consome** — ranking, explicação, diagnóstico. Ele
não treina nada, não roda pipeline, não escolhe modelo. O analista **opera** — executa o
pipeline, retreina, e também consulta.

Isso não é detalhe de desenho: é a decisão de que o gestor não precisa entender o modelo
para usar o sistema, e não tem como quebrá-lo por engano.

### Por que ela está no texto

Fixa o escopo antes de qualquer detalhe técnico. As três funções do painel descritas no
final do Capítulo 6 — lista, detalhe da escola, diagnóstico — são exatamente os três casos
de uso do gestor nesta figura. É a promessa que o Capítulo 6 mostra cumprida.

### Como dizer em 20 segundos

> "São duas pessoas diferentes usando o sistema. O gestor da Secretaria só consome: vê a
> lista, vê por que cada escola está nela, vê o diagnóstico. Quem roda o pipeline e
> retreina o modelo é o analista. O INEP não usa o sistema — ele fornece os dados. Essa
> separação é proposital: o gestor não precisa entender o modelo para usar a ferramenta."

---

## Figura 3 — "Diagrama de pacotes"

**Arquivo:** `arq2_pacotes.png` · **gerada por:** `notebooks/10_diagramas_arquitetura.py` · **onde aparece:** Capítulo 4.

### O que ela é, mecanicamente

Cada retângulo é um **pacote** — um conjunto de arquivos de código com uma
responsabilidade. A seta tracejada significa "usa", e aponta do pacote que depende para o
pacote do qual ele depende.

De baixo para cima: `src.data` (leitura e padronização dos dados do INEP) → `src.features`
(construção das 39 características e o cruzamento de um ano com o seguinte) → `src.models`
(treino, avaliação e explicação). À parte, `src.data.config` guarda caminhos e constantes;
`notebooks` e `tests` usam os pacotes, e `src.recommend` é o painel.

### O que ela revela

Todas as setas apontam para o mesmo lado. Não há ciclo: nenhum pacote de baixo depende de
um pacote de cima. Na prática, isso significa que dá para trocar o modelo sem tocar na
leitura dos dados, e trocar a leitura dos dados sem tocar no painel.

Repare também que `tests` aponta para dentro do sistema, e nada aponta para `tests`. Os
testes observam o código; o código não sabe que eles existem.

### Por que ela está no texto

Sustenta a afirmação de arquitetura em camadas com dependências em sentido único, retomada
nas conclusões do Capítulo 6 como uma das defesas contra erros que não se manifestam em
tempo de execução. Sem esta figura, seria só uma afirmação.

### Como dizer em 20 segundos

> "Cada caixa é uma parte do código com uma responsabilidade só, e as setas mostram quem
> depende de quem. Todas apontam para o mesmo lado — os dados não sabem que existe um
> modelo, e o modelo não sabe que existe um painel. É o que permite trocar uma peça sem
> quebrar as outras."

> ⚠️ Esta figura marca o painel como "planejado" e cita "notebooks 01..09". Ver **Três
> pontos a verificar**, ponto 3.

---

## Figura 4 — "Diagrama de componentes e fluxo de dados"

**Arquivo:** `arq3_componentes.png` · **gerada por:** `notebooks/10_diagramas_arquitetura.py` · **onde aparece:** Capítulo 4.

### O que ela é, mecanicamente

A Figura 3 mostra quem depende de quem; esta mostra **por onde o dado passa**. As caixas
coloridas com «component» são as etapas de processamento; as caixas cinza embaixo são os
arquivos gravados em disco entre uma etapa e outra.

O caminho: `data/raw` (os arquivos originais do INEP — Censo, Taxas, INSE, IRD, TDI, AFD) →
**ETL** → `data/interim/*.parquet` → **Engenharia de características** →
`data/processed/features.parquet` → **Modelagem** → `models/xgboost_v1.joblib` →
**Explicabilidade** e **Painel** → o gestor.

### O que ela revela

Cada etapa termina gravando um arquivo, e a etapa seguinte começa lendo esse arquivo. As
etapas não se chamam diretamente. Isso é o que permite reexecutar só um trecho do pipeline
sem refazer tudo, e é o que torna possível verificar o resultado intermediário de cada
etapa.

Repare que o modelo é gravado em disco (`xgboost_v1.joblib`) e depois **carregado** tanto
pela explicação quanto pelo painel. É o mesmo modelo nos dois lugares — a explicação
mostrada ao gestor descreve exatamente o modelo que produziu a lista, e não uma cópia
aproximada.

### Por que ela está no texto

É a figura que torna concreta a reprodutibilidade afirmada no Capítulo 6: todo número da
monografia sai de um desses arquivos, e cada arquivo é gerado por uma etapa identificada.

### Como dizer em 20 segundos

> "Este é o caminho do dado. Sai do INEP em planilha bruta, passa por limpeza, vira a tabela
> de características, vira modelo treinado, e chega ao painel do gestor. Entre cada etapa há
> um arquivo gravado em disco — é o que permite conferir o resultado de cada passo em vez de
> confiar na caixa inteira."

> ⚠️ Painel marcado como "planejado". Ver **Três pontos a verificar**, ponto 3.

---

## Figura 5 — "Diagrama de atividades do fluxo de execução"

**Arquivo:** `arq4_atividades.png` · **gerada por:** `notebooks/10_diagramas_arquitetura.py` · **onde aparece:** Capítulo 4.

### O que ela é, mecanicamente

Uma sequência de execução, de cima para baixo, do ponto preto (início) ao alvo (fim). Dez
atividades em três blocos de cor: azul, a preparação dos dados; verde, a modelagem;
vermelho, a entrega ao gestor.

Na ordem: carregar os microdados do Censo → filtrar o universo (Pernambuco, rede estadual,
escola em atividade com Ensino Médio) → montar o painel escola × ano → integrar os
indicadores (Taxas, INSE, IRD, TDI, AFD) → construir as características de um ano com o
alvo do ano seguinte → treinar os modelos de referência e ajustar o modelo adotado →
avaliar nos dois protocolos → gravar o modelo → explicar e diagnosticar → servir no painel.

### O que ela revela

Onde exatamente acontece a decisão mais delicada do projeto: na quinta caixa,
"Construir features t → alvo t+1". É ali que as características de um ano são casadas com o
abandono do ano seguinte. Um deslocamento nessa caixa não geraria erro visível em nenhuma
das outras nove — o programa rodaria até o fim e a lista sairia plausível. É por isso que
essa etapa tem teste dedicado (`test_build_target.py`, no Quadro 4).

Vale notar também que a avaliação vem **antes** de gravar o modelo, e não depois.

### Por que ela está no texto

Traduz a arquitetura em ordem de execução, e é a referência de quem for reexecutar o
pipeline. A ordem desta figura é a ordem conceitual; a ordem prática dos scripts está no
`CLAUDE.md` do repositório, e não é a ordem numérica dos arquivos.

### Como dizer em 20 segundos

> "É a receita, de cima para baixo. Carrega o dado bruto do Censo, filtra o que interessa,
> monta a história de cada escola ano a ano, cruza as informações de um ano com o abandono
> do ano seguinte, treina, avalia, guarda o modelo e entrega no painel. A quinta caixa é a
> mais delicada: é onde um erro de um ano estragaria tudo sem dar sinal."

---

## Figura 6 — "Diagrama de implantação"

**Arquivo:** `arq5_implantacao.png` · **gerada por:** `notebooks/10_diagramas_arquitetura.py` · **onde aparece:** Capítulo 4.

### O que ela é, mecanicamente

Onde cada parte do sistema **roda**, em três blocos.

À esquerda, a estação de desenvolvimento: o ambiente Python com o pipeline, os dados em
Parquet e os modelos gravados. No meio, um contêiner com a aplicação do painel e uma cópia
do modelo. À direita, o navegador do gestor, que acessa o painel por HTTPS.

A seta do primeiro para o segundo bloco carrega o rótulo "build / copia modelo".

### O que ela revela

A separação entre o ambiente onde o modelo é **construído** e o ambiente onde ele é
**servido**. O gestor nunca toca nos dados brutos nem no pipeline: o que chega até ele é o
modelo já treinado, mais a aplicação que o consulta.

Isso tem consequência prática: o painel não recalcula nada quando o gestor abre a tela. Ele
carrega um modelo pronto. Retreinar é uma operação deliberada, feita do outro lado da seta.

### Por que ela está no texto

Fecha a arquitetura mostrando o sistema em operação, e não apenas em desenvolvimento.

### Como dizer em 20 segundos

> "O modelo é construído de um lado e usado do outro. Na máquina de desenvolvimento ficam os
> dados brutos e o treino; o que vai para o gestor é só o modelo pronto mais a aplicação que
> o consulta, pelo navegador. O painel não recalcula nada quando abre — retreinar é decisão
> de quem opera, não efeito colateral de quem consulta."

> ⚠️ O contêiner aparece como "planejado" e o ambiente como Python 3.10. Ver **Três pontos
> a verificar**, ponto 3.

---

# Parte 2 — As figuras do Capítulo 6 (Figuras 7 a 22)

---

## Figura 7 — "Por que o conjunto usado na previsão tem 1.586 observações"

**Arquivo:** `G1_funil_amostra.png` · **gerada por:** `notebooks/16_figuras_simplificadas.py` · **onde aparece:** Capítulo 6, logo após o Quadro 5.

### O que ela é, mecanicamente

Um funil de três barras horizontais. O comprimento de cada barra é o número de observações
de escola × ano que sobrevivem àquela etapa. Entre as barras, em itálico, está escrito
quantas saíram e por quê.

- **2.392** — todas as observações de escola e ano, de 2022, 2023 e 2024 (barra cinza).
- **−791** porque 2024 não tem 2025 para observar → **1.601**.
- **−15** escolas que saíram da rede ou deixaram de ofertar Ensino Médio → **1.586**
  (barra vermelha, o conjunto efetivamente usado).

### O que ela revela

Que a redução **não é descarte por qualidade**. Nenhuma escola foi removida por dado
ausente ou suspeito. É consequência aritmética da regra que define o problema: o sistema
aprende com pares — as características de um ano e o abandono do ano seguinte —, e com três
anos de painel cada escola forma apenas dois pares.

As 791 linhas de 2024 não se perdem: elas são o **alvo** das linhas de 2023. O que não
existe é o alvo delas.

### Por que ela está no texto

Porque a distância entre 2.392 e 1.586 é a primeira coisa que um leitor atento questiona, e
a explicação em prosa é mais difícil de acompanhar do que o funil. A figura também planta a
limitação central do trabalho: **apenas dois pares de anos**. Essa janela curta é a
explicação da principal falha do sistema, discutida na Figura 14 e retomada nas conclusões.

### Como dizer em 20 segundos

> "Começamos com 2.392 observações de escola e ano. O sistema aprende com pares — o ano
> atual prevendo o seguinte —, então as 791 linhas de 2024 não podem ser ponto de partida:
> não existe 2025 para observar. Elas não se perdem, são o alvo das linhas de 2023. Mais 15
> escolas saíram da rede. Restam 1.586. Nenhuma escola foi descartada por dado ruim — é
> aritmética da regra, não limpeza."

---

## Figura 8 — "Distribuição da taxa de abandono prevista e diferença de risco entre grupos de escolas"

**Arquivo:** `E2_alvo.png` · **gerada por:** `notebooks/12_figuras_monografia.py` · **onde aparece:** Capítulo 6, seção *O Que o Sistema Prevê*.

### O que ela é, mecanicamente

Dois painéis com unidades diferentes — vale dizer isso em voz alta antes de comentar.

- **Esquerda:** quantas observações de escola × ano caem em cada faixa de abandono.
  Nenhum abandono (0%): 1.079 casos, 68%. Baixo (0 a 2%): 303, 19%. Moderado (2 a 5%): 101,
  6%. Alto (5 a 10%): 64, 4%. Crítico (acima de 10%): 39, 2%.
- **Direita:** a taxa média de abandono em 2024 por grupo de localização — 0,6% nas 679
  escolas urbanas, 0,9% nas 70 rurais, 6,3% nas 42 indígenas ou quilombolas. Aqui a
  contagem é de **escolas**, e o eixo é percentual, não número de casos.

### O que ela revela

Os dois fatos que condicionam todo o resto do capítulo.

O primeiro: a maioria absoluta das escolas não registra abandono nenhum. As faixas encolhem
rápido — só 2% das observações passam de 10%.

O segundo: o risco é muito desigual. As barras urbana e rural quase encostam no zero; a das
escolas indígenas e quilombolas está mais de dez vezes acima. E a média alta não é uniforme
nesse grupo — o desvio-padrão é de 8,9 pontos, ou seja, há escolas sem abandono algum ao
lado de escolas acima de 30%.

### Por que ela está no texto

Ela justifica as duas decisões metodológicas mais importantes do capítulo. Como a maioria
está em zero, julgar o sistema pelo erro do valor previsto premiaria quem respondesse "zero"
para todas as escolas — daí a opção por avaliar a **ordem**. E como o risco é desigual entre
grupos, uma média única de erro esconderia falhas concentradas — daí a análise por grupo de
localização, que reaparece na Figura 22.

### Como dizer em 20 segundos

> "Duas coisas sobre o que o sistema tenta prever. À esquerda: em 68% dos casos a taxa é
> exatamente zero — a maioria das escolas não perde ninguém. À direita: o pouco que existe é
> muito desigual. Escola urbana, 0,6%. Rural, 0,9%. Indígena ou quilombola, 6,3% — mais de
> dez vezes. Por isso o sistema é julgado pela ordem que produz, e o erro é medido grupo a
> grupo, nunca numa média só."

---

## Figura 9 — "Distribuição das 23 características contínuas na rede estadual"

**Arquivo:** `E5_distribuicoes.png` · **gerada por:** `notebooks/13_estatisticas_features.py` (`figura_distribuicoes`) · **onde aparece:** Capítulo 6, logo após o Quadro 6.

### O que ela é, mecanicamente

São 23 mini-gráficos num painel só — um para cada característica contínua do sistema, **na
mesma ordem do Quadro 6** (da que mais se relaciona com o abandono para a que menos se
relaciona, lendo da esquerda para a direita, de cima para baixo).

Cada mini-gráfico é um histograma:

- **Eixo horizontal:** o valor da característica, na unidade dela (percentual, escala do
  INSE, alunos por turma).
- **Eixo vertical:** quantas observações caem em cada faixa. O total de cada painel é 1.586.
- **Linha tracejada vermelha:** a mediana, o valor que divide a rede ao meio.

Ela não mostra relação com o abandono. Mostra **o formato de cada característica** — se as
escolas estão espalhadas ou amontoadas num valor só.

### O que ela revela

Três padrões, todos visíveis de longe.

1. **As características de fluxo estão coladas no zero.** Nos quatro primeiros painéis
   (abandono do ano anterior, geral e por série) e nos de reprovação há uma torre gigante na
   primeira barra e uma cauda fina que se estende até 40–50%. A mediana está em zero — a
   linha tracejada quase encosta no eixo. É o que o Quadro 6 diz em números: mediana 0,00 e
   média 1,72%, puxada por poucas escolas extremas.
2. **Tempo integral não é uma escala, é quase um sim ou não.** Duas torres e um vazio entre
   elas: cerca de 505 observações em 0% e cerca de 700 em 100%.
3. **A defasagem idade-série se espalha em sino, em torno de 23%.** É o oposto das
   anteriores — as escolas ocupam toda a faixa. É isso que a torna útil para *diferenciar*
   escolas, e ajuda a explicar por que ela aparece entre as de maior peso na Figura 19.

De graça, a figura ainda entrega: formação docente Grupo 5 e computadores por aluno também
amontoados em zero; INSE, alunos por turma, alunos por docente, IRD e formação docente
Grupos 1 e 3 em formato de sino; o índice de infraestrutura em barras espaçadas, porque é
uma contagem de itens; e o porte ainda assimétrico **mesmo já em logaritmo**.

### Por que ela está no texto

É a justificativa visual de três decisões metodológicas: por que o Quadro 6 usa a correlação
de Spearman, que compara posições, e não uma medida baseada em valores, que seria dominada
por uma dezena de escolas extremas; por que o porte entra em logaritmo; e por que média e
mediana divergem tanto no Quadro 6.

### Como dizer em 20 segundos

> "Cada quadradinho é uma característica da escola, e mostra como as escolas se distribuem
> nela. Onde tem uma torre única, quase todas as escolas têm o mesmo valor — abandono zero,
> por exemplo — e a característica pouco ajuda a separar uma escola da outra. Onde a
> distribuição é espalhada, como na defasagem idade-série, ela separa bem, e é ali que o
> sistema encontra sinal. O tempo integral é o caso curioso: a rede está dividida entre
> escolas totalmente integrais e escolas sem nada, quase sem meio-termo."

---

## Figura 10 — "Repartição das escolas por atributo de sim ou não e taxa média de abandono de cada grupo"

**Arquivo:** `E6_binarias.png` · **gerada por:** `notebooks/13_estatisticas_features.py` · **onde aparece:** Capítulo 6, após o Quadro 7.

### O que ela é, mecanicamente

Os dois painéis medem coisas diferentes, e confundi-los é o erro mais provável nesta figura.

- **Esquerda:** cada linha é uma barra empilhada que reparte as 1.586 observações entre as
  que têm o atributo (verde) e as que não têm (cinza). Os dois pedaços **somam 100%**, e o
  número dentro da barra traz o percentual e a contagem: internet 99% (n=1.574), biblioteca
  91% (n=1.438), localização rural 14% (n=218), localização diferenciada 5% (n=81).
- **Direita:** duas barras separadas por linha, cada uma com a **taxa média de abandono do
  ano seguinte** dentro de um dos dois grupos. São duas médias do mesmo indicador, medidas
  em conjuntos diferentes de escolas — **não somam 100% e não há razão para somarem**. O que
  interessa é a distância entre elas. Os asteriscos marcam as diferenças que não se explicam
  pelo acaso.

Os atributos aparecem ordenados do mais comum para o mais raro.

### O que ela revela

A maior diferença da rede está na **localização, não na infraestrutura**. Escolas indígenas
e quilombolas têm abandono médio de 8,95% contra 0,70% das demais; as rurais, 3,74% contra
0,70%. As duas barras dessas linhas são visivelmente desiguais.

Os itens de infraestrutura produzem diferenças reais, mas modestas — de meio ponto a dois
pontos —, todas na mesma direção: quem tem biblioteca, laboratório, quadra e internet para
alunos abandona menos.

E há um alerta embutido: atributos presentes em quase toda a rede não separam nada. Internet
está em 99,2% das escolas e água potável em 95,1% — sobram 12 e 77 escolas do outro lado, e
a comparação perde sustentação. É por isso que esses atributos aparecem sem asterisco.

### Por que ela está no texto

Trata as 15 características de sim ou não com o método correto: para elas não faz sentido
correlação, e sim a comparação de médias entre dois grupos. E antecipa o achado de equidade
da Figura 22 — a localização diferenciada já aparece aqui como a maior separadora da rede,
o que explica por que o modelo lhe dá tanto peso, e por que o viés se concentra nela.

### Como dizer em 20 segundos

> "À esquerda, quantas escolas têm cada item — os dois pedaços somam a rede inteira. À
> direita, o abandono médio de quem tem e de quem não tem. Essas duas não somam nada: o que
> importa é a distância entre elas. E a maior distância de toda a figura não está em nenhum
> item de infraestrutura: está na localização. Escola indígena ou quilombola, 8,95%; as
> demais, 0,70%."

---

## Figura 11 — "Abandono médio e peso de cada região do estado no conjunto de dados"

**Arquivo:** `E8_mesorregiao.png` · **gerada por:** `notebooks/13_estatisticas_features.py` · **onde aparece:** Capítulo 6, após o Quadro 8.

### O que ela é, mecanicamente

Duas barras horizontais por região, em painéis separados, ambos ordenados do maior abandono
para o menor.

- **Esquerda:** taxa média de abandono do ano seguinte em cada uma das cinco regiões — São
  Francisco Pernambucano 2,76%, Sertão 1,53%, Agreste 1,08%, Mata 0,57%, Metropolitana de
  Recife 0,50%.
- **Direita:** quanto cada região pesa no conjunto de dados — Metropolitana 33% (523
  observações), Agreste 23% (366), Sertão 15% (237), Mata 15% (233), São Francisco 14% (227).

### O que ela revela

Os dois painéis contam histórias opostas de propósito. A região com **maior** abandono é a
que tem **menos** observações; a região com **menor** abandono é a que tem **mais**.

A diferença entre extremos é grande: o São Francisco Pernambucano abandona mais de cinco
vezes o que abandona a Região Metropolitana. E o painel da direita é a advertência: a média
geral da rede é puxada para baixo pela Metropolitana, que sozinha responde por um terço do
conjunto.

### Por que ela está no texto

Justifica manter a região do estado entre as características do sistema — a diferença entre
regiões é real e estatisticamente comprovada. E serve de contraste para explicar por que o
**município** não entra como característica: ele cumpre outro papel, o de agrupar as escolas
na avaliação para que nenhuma cidade apareça ao mesmo tempo no treino e no teste. Usá-lo
também como característica levaria o sistema a decorar o histórico de cada cidade em vez de
aprender o padrão que vale para as demais.

### Como dizer em 20 segundos

> "As cinco regiões do estado são muito diferentes entre si: o São Francisco Pernambucano
> abandona 2,76%, mais de cinco vezes a Região Metropolitana, que fica em 0,50%. E repare no
> painel da direita: a região que menos abandona é justamente a que mais pesa no conjunto de
> dados, um terço do total. É por isso que a média da rede engana, e é por isso que a região
> continua sendo uma característica do sistema."

---

## Figura 12 — "As 38 características numéricas ordenadas pela relação com o abandono do ano seguinte"

**Arquivo:** `E7_relacao_todas.png` · **gerada por:** `notebooks/13_estatisticas_features.py` · **onde aparece:** Capítulo 6, seção *Quais Características Têm Valor para a Previsão*.

### O que ela é, mecanicamente

Um ranking de 38 barras horizontais, uma por característica numérica, ordenadas da que mais
aumenta o risco (topo) para a que mais o reduz (base).

- O eixo horizontal é a **relação com o abandono do ano seguinte**, medida pela correlação
  de posição, que vai de −1 a +1. Zero é a linha vertical do meio.
- **Vermelho:** valor alto acompanha **mais** abandono. **Azul:** valor alto acompanha
  **menos** abandono. **Cinza:** a relação não se distingue do acaso.
- Os asteriscos indicam a confiança do resultado (* 95%, ** 99%, *** 99,9%).

### O que ela revela

Uma hierarquia limpa, em três blocos, e ela faz sentido antes mesmo de qualquer modelo.

No topo, em vermelho forte, o **histórico recente da própria escola**: abandono do ano
anterior no Ensino Médio (+0,48), na 1ª série (+0,46), na 2ª (+0,45), na 3ª (+0,37). Nenhuma
outra característica chega perto.

Logo abaixo, o **contexto e o perfil dos alunos**: localização diferenciada (+0,29),
defasagem idade-série nas três séries (+0,27, +0,27, +0,25), formação docente Grupo 5 —
professores sem ensino superior (+0,21).

Na ponta azul, o que protege: tempo integral (−0,21), formação docente Grupo 1 — professores
com licenciatura na própria disciplina (−0,17), nível socioeconômico (−0,17), alunos por
turma (−0,16), infraestrutura (−0,12).

E as oito barras cinza, sem relação detectável: formação docente Grupo 3, água potável, sala
de leitura, esgoto, **porte da escola**, internet, banda larga e auditório. Que o tamanho da
escola não diga nada sobre abandono costuma surpreender.

### Por que ela está no texto

Serve de **régua de verificação** para o modelo. Se as características que o sistema mais
usar, na Figura 19, forem outras, é sinal de que há erro no caminho entre os dados e o
modelo. É a comparação entre esta figura e a Figura 19 que sustenta a frase "o sistema não
está apenas acertando, está acertando pelas razões certas".

Ela também justifica manter as oito características cinza: isoladamente não dizem nada, mas
podem ajudar em combinação, e com 39 colunas para 1.586 observações o custo de mantê-las é
menor que o risco de descartar sinal por engano.

### Como dizer em 20 segundos

> "É o ranking do que anda junto com o abandono. Vermelho aumenta o risco, azul reduz, cinza
> não diz nada. O topo é o histórico recente da própria escola — quanto ela abandonou no ano
> passado. Depois vem o contexto e o perfil dos alunos. Na ponta azul, o que protege: tempo
> integral, professor formado na disciplina, nível socioeconômico. E oito características
> não mostram relação nenhuma, incluindo o tamanho da escola."

---

## Figura 13 — "Distribuição das medidas de desempenho nas 20 repetições"

**Arquivo:** `G3_cv_repetida.png` · **gerada por:** `notebooks/16_figuras_simplificadas.py` · **onde aparece:** Capítulo 6, após o Quadro 9.

### O que ela é, mecanicamente

Três painéis, um por medida, cada um comparando os quatro modelos. Antes de qualquer
leitura, é preciso explicar o desenho — é um diagrama de caixa, e ele não é óbvio:

- A **caixa** contém a metade central das 20 repetições.
- A **linha grossa** dentro dela é a repetição típica (a mediana).
- As **hastes** vão até os extremos usuais; as **bolinhas soltas** são repetições atípicas.
- Caixa alta = resultado instável, que depende muito de quais municípios caíram no teste.

Os painéis: erro médio da taxa (menor é melhor), acerto da ordenação e acerto na lista
prioritária (maior é melhor). O modelo "sem sistema" não aparece no painel do meio — quem
responde a média para todas as escolas não ordena escola nenhuma, e a medida não existe.

### O que ela revela

Duas leituras, e a segunda é a que interessa.

Primeira: no acerto da lista prioritária, os três modelos ficam em torno de 0,50 e o "sem
sistema" fica em 0,07, com a caixa dele inteiramente abaixo das outras. A distância é
enorme e não deixa dúvida.

Segunda: **entre os três modelos não há vencedor**. As caixas se sobrepõem quase
inteiramente nos três painéis. O modelo adotado fica ligeiramente atrás na ordenação (0,416
contra 0,428 e 0,431) e no meio no acerto da lista (0,504 contra 0,513 e 0,501).

E há um terceiro fato que a figura deixa evidente e a tabela não: as caixas são **altas**. O
acerto da lista do modelo adotado vai de cerca de 0,30 a quase 0,69 conforme a repetição.
Um número solitário esconderia essa variação.

### Por que ela está no texto

É o que sustenta a afirmação de que os três modelos são estatisticamente indistinguíveis —
afirmação que a escolha do modelo adotado tem de enfrentar, e não contornar. O empate é um
resultado, não uma imprecisão. A figura também é a defesa contra a pergunta "e se der outro
resultado com outra amostra?": foram 20 amostras, e a variação está desenhada.

### Como dizer em 20 segundos

> "Repetimos a avaliação 20 vezes, escondendo municípios diferentes a cada vez. Cada caixa
> mostra onde ficam as repetições típicas de cada modelo. Duas leituras: qualquer modelo é
> muito melhor que não ter sistema — 0,50 contra 0,07 no acerto da lista. E entre os três
> modelos as caixas se sobrepõem: é empate, e eu digo isso no texto em vez de escolher o
> número que me favorece."

---

## Figura 14 — "Erro do valor e acerto da ordem no teste do ano nunca visto"

**Arquivo:** `G2_teste_ano_nunca_visto.png` · **gerada por:** `notebooks/16_figuras_simplificadas.py` · **onde aparece:** Capítulo 6, após o Quadro 10.

### O que ela é, mecanicamente

A figura central do capítulo. Dois painéis com os mesmos quatro modelos, no protocolo mais
exigente: treino com os pares de 2022 e 2023, avaliação em 2024, um ano que o modelo nunca
viu.

- **Esquerda — errar o valor.** Erro médio da taxa em pontos percentuais, menor é melhor.
  Sem sistema 2,54; referência linear 2,89; referência em árvores 2,75; modelo adotado 2,87.
  A **linha tracejada** marca o nível do "sem sistema", e o rótulo diz o que ela significa:
  nenhum modelo fica abaixo dela.
- **Direita — acertar a ordem.** Das escolas que cada modelo colocou na lista prioritária,
  quantas eram mesmo críticas: 9 em cada 100 sem sistema, 38 na referência linear, 41 na
  referência em árvores, **42 no modelo adotado**.

### O que ela revela

O achado central, e ele tem duas faces opostas na mesma imagem.

À esquerda, o resultado é **desfavorável ao sistema**: nenhum modelo supera o chute. Para
acertar o valor da taxa, responder a média da rede para todas as escolas é melhor. O
coeficiente de determinação do modelo adotado é negativo (−0,33), que é a mesma coisa dita
em outra escala.

À direita, o resultado se inverte: 42 em cada 100 contra 9 em cada 100, quase cinco vezes
mais. Em números absolutos, das 79 escolas do topo da lista, 33 estavam de fato entre as de
maior abandono; o acaso acertaria 7.

A causa da descalibração é conhecida e cabe numa frase: entre um ciclo e outro o abandono
médio da coorte caiu de 1,36% para 0,88%, e o modelo, treinado no patamar anterior, prevê um
nível que a rede deixou de ter. Ele acerta quem está acima da média e erra onde a média
está. Com apenas dois pares de anos — a Figura 7 —, não há como aprender que o patamar se
move.

### Por que ela está no texto

Porque a honestidade do trabalho depende dela. O erro de magnitude está no Quadro 10 e será
visto de qualquer forma; a figura o põe lado a lado com o ganho de ordenação, que é onde o
sistema é útil. Ela também delimita o que o sistema **não** autoriza: ler a taxa prevista
como estimativa do número de alunos que sairão de uma escola.

### Como dizer em 20 segundos

> "Este é o resultado principal, e começo pela parte ruim. À esquerda, para acertar o valor
> da taxa, nenhum modelo supera o chute de responder a média da rede — a linha tracejada. À
> direita, a outra metade: das escolas que o sistema mandou atender primeiro, 42 em cada 100
> eram mesmo críticas, contra 9 do acaso. O sistema é um termômetro descalibrado: erra
> alguns graus, mas aponta corretamente quem está com mais febre."

---

## Figura 15 — "Desempenho do modelo adotado em cada transição anual"

**Arquivo:** `E9_ss13_cenarios.png` · **gerada por:** `notebooks/14_ss13_cenarios_temporais.py` · **onde aparece:** Capítulo 6, após o Quadro 11.

### O que ela é, mecanicamente

Mesmo tipo de diagrama de caixa da Figura 13, mas agora o que se compara não são modelos, e
sim **anos**. É sempre o mesmo modelo adotado; muda apenas a transição avaliada: azul para
2022 → 2023, vermelho para 2023 → 2024. Cada caixa resume 20 repetições em que 20% dos
municípios daquele ano ficaram fora do treino.

Três painéis: erro médio da taxa (menor é melhor), acerto da ordenação e acerto na lista
prioritária (maior é melhor).

### O que ela revela

O desempenho **não é constante entre os anos**, e a diferença é grande.

Na transição de 2022 para 2023, a lista prioritária acerta 0,627 — 63 escolas certas em cada
100. Na de 2023 para 2024, cai para 0,381. A ordenação segue o mesmo caminho: 0,469 contra
0,367. As caixas mal se tocam nesses dois painéis, o que significa que a diferença não é
sorte de amostra.

O painel do erro caminha na direção oposta: 2,82 na primeira transição contra 2,16 na
segunda. Errar menos e ordenar pior ao mesmo tempo parece contraditório, e não é — é o mesmo
fenômeno. O abandono médio caiu de 1,36% para 0,88% e as escolas se aproximaram de zero.
Isso reduz o erro absoluto e comprime o sinal que permite ordená-las.

Mesmo no ano pior, a capacidade de separar escolas críticas das demais fica em 0,81, numa
escala em que 0,5 é cara ou coroa.

### Por que ela está no texto

Responde a uma objeção legítima: os dois protocolos anteriores agregam as duas transições
num número só, e um sistema que funcionasse bem em um par de anos e mal no seguinte não
serviria como ferramenta anual. A figura mostra que ele serve nos dois — mas com desempenho
diferente. A consequência prática é explícita: **o desempenho da lista precisa ser
reavaliado a cada edição dos dados, não presumido constante.**

Os dois cenários também cercam os valores do Quadro 9, sinal de que o resultado agregado não
esconde um ano ruim.

### Como dizer em 20 segundos

> "É sempre o mesmo modelo, avaliado em dois anos separados. Ele funciona nos dois, mas rende
> mais no primeiro: 63 acertos em cada 100 na lista de 2022 para 2023, contra 38 de 2023 para
> 2024. A queda acompanha a própria rede — o abandono médio caiu pela metade e as escolas se
> aproximaram de zero, o que reduz o erro e ao mesmo tempo dificulta ordená-las. Por isso o
> desempenho precisa ser remedido a cada ano, não presumido."

---

## Figura 16 — "Resíduo do modelo por escola, em número de alunos"

**Arquivo:** `E10_residuos_transicoes_alunos.png` · **gerada por:** `notebooks/14_ss13_cenarios_temporais.py` · **onde aparece:** Capítulo 6, após a Figura 15.

### O que ela é, mecanicamente

Dois painéis de pontos, um por transição (2022–2023 à esquerda, 2023–2024 à direita). **Cada
ponto é uma escola.**

- O eixo vertical é o resíduo convertido para **número de alunos**: o real menos o previsto,
  obtido multiplicando a taxa de abandono pela matrícula de Ensino Médio da escola. Acima de
  zero, o sistema subestimou — saíram mais alunos do que ele previu. Abaixo, superestimou.
- O eixo horizontal é apenas a enumeração das escolas (1, 2, 3, …, 797 e 789); não tem
  significado, serve para espalhar os pontos.
- As **linhas tracejadas** marcam o erro médio: 3,3 alunos na primeira transição, 3,0 na
  segunda.
- Os **triângulos** no topo são escolas cujo erro passou de ±45 alunos e foram trazidas para
  a borda para não esticar a escala: uma na primeira transição, duas na segunda.

### O que ela revela

O erro do sistema traduzido para a unidade em que o gestor pensa. Em ambos os painéis a
massa de pontos se concentra em torno de zero, sem inclinação para cima ou para baixo — o
sistema **não erra sistematicamente** para mais nem para menos na rede como um todo.

O erro típico é de cerca de **três alunos por escola**. Para uma escola de 350 matrículas,
é um erro pequeno o suficiente para não atrapalhar a decisão de priorizar.

Os desvios grandes estão nas poucas escolas de maior porte, onde uma taxa errada por alguns
pontos vira dezenas de estudantes.

### Por que ela está no texto

Traduz o erro de magnitude — que a Figura 14 mostrou ser ruim em pontos percentuais — para
uma unidade concreta, e mostra que ele é menos dramático do que a taxa sugere. É também a
figura que sustenta a frase mais forte sobre limites do sistema: a maior perda da rede em
número de alunos veio de uma escola sem histórico de abandono (a Maria Lúcia Alves, em Santa
Cruz do Capibaribe, com cerca de 154 estudantes contra uma previsão de 0,7%).

### Como dizer em 20 segundos

> "Aqui o erro está em alunos, não em porcentagem. Cada ponto é uma escola: acima da linha, o
> sistema previu de menos; abaixo, de mais. A massa está em torno de zero, sem viés para
> nenhum lado, e o erro típico é de cerca de três alunos por escola. Os desvios grandes estão
> nas escolas de maior porte, onde poucos pontos percentuais viram dezenas de estudantes."

---

## Figura 17 — "Ganho prático da lista de prioridade em relação à escolha ao acaso"

**Arquivo:** `E4_desempenho.png` · **gerada por:** `notebooks/12_figuras_monografia.py` · **onde aparece:** Capítulo 6, seção *Capacidade de Priorização*.

### O que ela é, mecanicamente

Dois painéis que respondem às duas perguntas do gestor.

- **Esquerda — o acerto.** Das escolas indicadas, quantas eram mesmo críticas: 7 em cada 100
  sem o sistema, 52 em cada 100 com a lista de prioridade.
- **Direita — o alcance.** Das escolas críticas da rede, quantas a lista encontra, para três
  orçamentos: 50 escolas visitadas alcançam 28% (contra 6% ao acaso), 100 alcançam 46%
  (contra 13%), 150 alcançam 57% (contra 19%).

"Críticas" aqui são as escolas do décimo mais alto de abandono observado.

### O que ela revela

O ganho traduzido em decisão orçamentária. A barra cinza do painel direito é o que se
alcançaria visitando escolas ao acaso — se você visita 150 de 789, encontra por definição
19% das críticas. A barra vermelha é o que a lista entrega: 57%, três vezes mais, com a
mesma equipe e o mesmo orçamento.

É o princípio da triagem de um pronto-socorro: com vagas limitadas, a fila ordenada por
gravidade encontra muito mais casos graves do que o atendimento por ordem de chegada.

### Por que ela está no texto

Porque converte medidas abstratas em algo sobre o qual um gestor decide. A pergunta "meu
sistema tem Spearman de 0,35" não significa nada para a Secretaria; "com equipe para 150
escolas, você alcança 57% do problema em vez de 19%" significa.

### Como dizer em 20 segundos

> "É o desempenho traduzido em decisão. À direita: com equipe para visitar 150 escolas, a
> lista alcança 57% das escolas realmente críticas. Visitando ao acaso, você alcançaria 19% —
> três vezes menos, com o mesmo orçamento. É a triagem do pronto-socorro: com vagas
> limitadas, a fila ordenada por gravidade encontra muito mais casos graves do que a ordem de
> chegada."

> ⚠️ O painel esquerdo mistura dois protocolos de avaliação e exibe um número que não aparece
> no texto. Ver **Três pontos a verificar**, ponto 1.

---

## Figura 18 — "Acerto e alcance da lista para diferentes tamanhos de lista"

**Arquivo:** `G4_tamanho_da_lista.png` · **gerada por:** `notebooks/16_figuras_simplificadas.py` · **onde aparece:** Capítulo 6, após a Figura 17.

### O que ela é, mecanicamente

Duas curvas, ambas no teste do ano nunca visto. O eixo horizontal, nos dois painéis, é o
**tamanho da lista** — quantas escolas o gestor consegue atender, de 10 a 200. A linha
vermelha é o sistema; a tracejada cinza é o que a escolha ao acaso entregaria.

- **Esquerda — acerto:** das escolas da lista, que percentual era mesmo crítico.
- **Direita — alcance:** das escolas críticas da rede, que percentual a lista encontra.

### O que ela revela

O painel da direita é inequívoco: o alcance sobe de forma contínua com o tamanho da lista,
de menos de 5% com 10 escolas até cerca de 70% com 200, sempre bem acima da linha do acaso.
Quanto mais escolas o gestor consegue atender, mais do problema a lista cobre.

No painel da esquerda, a curva vermelha também sobe, e fica sempre acima da linha do acaso —
com qualquer tamanho de lista, o sistema seleciona melhor do que sortear.

**Atenção:** o painel esquerdo desta figura e os percentuais de acerto citados no texto
("entre as 50 primeiras, 44%; entre as 150 primeiras, 31%") usam **definições diferentes de
acerto**, e por isso não coincidem — nem em valor, nem em direção. Ver **Três pontos a
verificar**, ponto 2, antes de comentar esta figura em público.

### Por que ela está no texto

Sustenta a afirmação de que não existe tamanho ótimo de lista, e que quem arbitra é o gestor.
Como a saída do sistema é um número contínuo, e não um carimbo de "em risco", o ponto de
corte pode ser escolhido depois, conforme o orçamento, e revisto a cada ano sem tocar no
modelo. Essa flexibilidade é uma decisão de projeto, tomada lá atrás na seção *O Que o
Sistema Prevê*, e esta figura é onde ela dá retorno.

### Como dizer em 20 segundos

> "O gestor escolhe o tamanho da lista conforme o orçamento, e a figura mostra o que ele
> ganha em cada tamanho. Quanto maior a lista, maior a fatia do problema alcançada — chega a
> 70% com 200 escolas. E em qualquer tamanho a lista do sistema está bem acima da linha
> tracejada, que é o que a escolha ao acaso entregaria. Não existe tamanho ótimo: existe o
> tamanho que a capacidade de atendimento do ano permite."

---

## Figura 19 — "As características que mais pesam nas previsões do sistema"

**Arquivo:** `G5_peso_caracteristicas.png` · **gerada por:** `notebooks/16_figuras_simplificadas.py` · **onde aparece:** Capítulo 6, seção *Explicação das Indicações*.

### O que ela é, mecanicamente

Um ranking de 15 barras. O eixo horizontal é a **fatia do peso total das previsões** que
cabe a cada característica, em percentual — juntas, essas 15 respondem por 90% do peso.

A diferença em relação à Figura 12 é essencial e vale enunciar: a Figura 12 mede o que a
característica tem a ver com o abandono **na realidade observada**; esta mede o quanto o
**modelo efetivamente a usa** para decidir. Uma é sobre o mundo, a outra é sobre o sistema.

Do topo: abandono no ano anterior na 2ª série 20,7%, defasagem idade-série no Ensino Médio
12,5%, abandono no Ensino Médio 9,5%, abandono na 1ª série 7,9%, localização diferenciada
7,0%, reprovação no ano anterior 6,1%.

### O que ela revela

Duas coisas.

Primeira, a confirmação: somados, abandono e reprovação do ano anterior respondem por cerca
de **metade de todo o peso** (20,7 + 9,5 + 7,9 + 6,1 + 2,6 ≈ 47%). O melhor previsor do
tempo de amanhã é o tempo de hoje. E a hierarquia bate com a da Figura 12 — histórico,
depois perfil dos alunos, depois contexto. O sistema aprendeu o que a análise dos dados já
apontava, o que é um argumento de confiança.

Segunda, o alerta: **localização diferenciada é a quinta característica mais usada**, com 7%
do peso. Não é uma característica marginal. Esse peso é exatamente o que torna o viés da
Figura 22 tão consequente — o modelo não erra nesse grupo por acaso, ele erra porque usa
muito a informação que define o grupo.

### Por que ela está no texto

É a verificação de que o modelo aprendeu pelas razões certas, e não por artefato dos dados.
Uma inversão em relação à Figura 12, numa reexecução futura, deve ser tratada como sintoma
de erro no caminho dos dados. E é aqui que a discussão de equidade começa a se armar, antes
de a Figura 22 fechá-la.

### Como dizer em 20 segundos

> "A Figura anterior mostrava o que tem a ver com o abandono na realidade; esta mostra o que
> o sistema realmente usa para decidir. As duas concordam, e isso é bom sinal: o histórico de
> abandono e reprovação da própria escola responde por cerca de metade do peso. Mas repare na
> quinta linha: localização indígena ou quilombola pesa 7%. Guarde esse número — ele volta
> quando eu falar do viés."

---

## Figura 20 — "Peso e direção de cada característica nas previsões do sistema"

**Arquivo:** `S2_shap_direcao.png` · **gerada por:** `notebooks/09_shap_diagnostico.py` · **onde aparece:** Capítulo 6, seção *Direção dos Efeitos*.

### O que ela é, mecanicamente

As mesmas 15 características da Figura 19, com o mesmo comprimento relativo de barra, mas
com uma informação a mais: a **cor**.

- **Vermelho:** valor alto dessa característica **aumenta** o risco previsto.
- **Azul:** valor alto **reduz** o risco previsto.

O eixo horizontal é o peso médio na previsão. A unidade é a escala interna do modelo, não
pontos percentuais — o que importa aqui é a comparação entre barras, não o valor absoluto.

### O que ela revela

Que as direções são todas coerentes com o que se esperaria, e nenhuma está invertida.

Em vermelho, empurrando o risco para cima: abandono e reprovação do ano anterior, defasagem
idade-série, localização diferenciada, formação docente Grupo 5 (professores sem ensino
superior).

Em azul, empurrando para baixo: formação docente Grupo 1 (licenciatura na própria
disciplina), nível socioeconômico, alunos por turma, computadores por aluno.

Essa coerência é o argumento mais forte de confiança do capítulo: o sistema não está apenas
acertando, está acertando pelas razões certas.

### Por que ela está no texto

É uma verificação executável. Uma inversão de direção — nível socioeconômico alto passando a
aumentar o risco, por exemplo — em uma reexecução futura deve ser tratada como sintoma de
erro no caminho dos dados, não como descoberta. A figura estabelece a referência contra a
qual essa verificação é feita.

### Como dizer em 20 segundos

> "As mesmas características da figura anterior, agora com a direção. Vermelho empurra o
> risco para cima: abandono passado, reprovação, atraso escolar, professor sem formação
> superior. Azul empurra para baixo: professor formado na disciplina, nível socioeconômico,
> turmas menores. Nenhuma direção está invertida — o sistema não está só acertando, está
> acertando pelas razões certas."

---

## Figura 21 — "Explicação individual da escola de maior risco previsto"

**Arquivo:** `S3_waterfall_alto_risco.png` · **gerada por:** `notebooks/09_shap_diagnostico.py` · **onde aparece:** Capítulo 6, seção *Explicação de Uma Escola*.

### O que ela é, mecanicamente

O gráfico mais difícil de ler do capítulo, e o mais importante de explicar devagar. É uma
"cascata": ela parte da previsão média da rede, embaixo, e vai somando as contribuições de
cada característica até chegar à previsão daquela escola específica, no topo.

- **Embaixo, `E[f(X)]`:** o ponto de partida — o que o sistema preveria para uma escola
  qualquer, sem saber nada sobre ela.
- **Cada barra:** o quanto uma característica **afastou** a previsão desse ponto de partida.
  À esquerda de cada barra aparece o valor daquela característica na escola (em escala
  padronizada, não na unidade original).
- **No topo, `f(x)`:** a previsão final para esta escola.
- **"Outras 32 características":** o resto, agrupado, para a figura caber.

A soma de todas as contribuições reproduz **exatamente** a previsão exibida. Isso não é
aproximação: é propriedade matemática do método, e está travada por teste automatizado
(`test_explain.py`, no Quadro 4).

### O que ela revela

Por que esta escola — uma estadual indígena no município de Jatobá — foi para o topo da
lista. As maiores contribuições vêm da defasagem idade-série (a maior de todas), da
defasagem na 3ª série, do histórico de abandono do Ensino Médio e do abandono na 2ª série.
A localização diferenciada também contribui, mas não é a principal.

Nenhuma contribuição relevante puxa para baixo: é uma escola em que quase tudo aponta para
risco alto.

### Por que ela está no texto

É a materialização do requisito de explicabilidade fixado no Capítulo 4. Sem esta figura, o
gestor recebe uma lista e tem de aceitá-la ou rejeitá-la em bloco. Com ela, pode **discordar
com argumento** — olhar a justificativa, saber que aquela escola está no topo por causa da
defasagem idade-série, e decidir se isso faz sentido para a escola que ele conhece.

E é a mesma mecânica que expõe o problema: esta escola, apontada como a de maior risco, não
perdeu aluno nenhum em 2024 (Quadro 12). O mecanismo que justifica as indicações é o mesmo
que revela onde elas não devem ser seguidas — que é o assunto da Figura 22.

### Como dizer em 20 segundos

> "É a nota fiscal da previsão de uma escola. Começa embaixo, no que o sistema preveria para
> uma escola qualquer, e cada barra mostra o quanto uma característica afastou a previsão
> desse ponto de partida, para cima ou para baixo, até o número final lá em cima. A soma bate
> exatamente com a previsão exibida — não é aproximação, e tem teste automatizado garantindo
> isso. É o que permite ao gestor discordar com argumento, em vez de aceitar ou rejeitar a
> lista inteira."

> ⚠️ O valor de `f(x)` nesta figura não é o mesmo previsto para a escola no Quadro 12, e a
> unidade do eixo merece conferência. Ver **Três pontos a verificar**, ponto 2.

---

## Figura 22 — "Erro do sistema por grupo de localização no teste do ano nunca visto"

**Arquivo:** `S5_equidade_grupos.png` · **gerada por:** `notebooks/09_shap_diagnostico.py` · **onde aparece:** Capítulo 6, seção *Erros do Modelo e Equidade*.

### O que ela é, mecanicamente

O achado de equidade, em duas leituras do mesmo dado.

- **Esquerda:** um diagrama de caixa do resíduo (real menos previsto, em pontos percentuais)
  para cada grupo de localização. A linha tracejada no zero é a calibração perfeita. Urbanas
  e rurais têm caixas achatadas coladas no zero, com pontos soltos para os dois lados. A
  caixa das indígenas e quilombolas é **larga e inteiramente abaixo do zero**.
- **Direita:** o mesmo em uma barra por grupo — o resíduo médio. Urbanas +0,07, rurais +0,38,
  indígenas e quilombolas **−6,12**.

Negativo significa **superpredição**: o sistema previu mais abandono do que aconteceu.

### O que ela revela

Um erro que cai sempre do mesmo lado para o mesmo grupo — que é diferente de errar às vezes
para mais e às vezes para menos.

Nas 41 escolas de localização diferenciada, o sistema prevê risco alto para escolas cujo
abandono observado é próximo de zero. Urbanas e rurais estão calibradas; esse grupo não
está, e por uma margem de mais de 6 pontos percentuais.

O painel da esquerda acrescenta algo que a média esconde: a caixa desse grupo é **larga**. O
erro não é uniforme — há escolas em que o sistema acerta e escolas em que erra por mais de
20 pontos.

A explicação provável é a existência de fatores de proteção ligados ao vínculo comunitário
que os dados públicos não captam. O perfil dessas escolas — rural, baixo nível
socioeconômico, alta defasagem — está associado a abandono alto, mas o abandono não
acontece. É o que faz um seguro de automóvel cobrar caro de um motorista pelo perfil de
risco, sem saber que ele dirige pouco e com cuidado.

### Por que ela está no texto

Porque uma média única de erro esconderia exatamente o tipo de falha que mais importa numa
ferramenta que aloca recurso público. Sem correção, o sistema daria atenção excessiva a
escolas que não estão em risco, deslocando recursos de onde eles fazem falta.

Duas saídas foram consideradas e nenhuma adotada nesta versão. Retirar a característica de
localização diferenciada não resolveria, porque o erro não vem dela: o modelo reencontraria
o mesmo perfil por zona rural, nível socioeconômico e defasagem. Calibrar o grupo
separadamente exigiria entender antes quais fatores de proteção explicam o baixo abandono, e
ajustar sem esse entendimento apenas esconderia o problema. Optou-se por **medir, declarar e
registrar**: a ressalva acompanha cada indicação exibida no painel, e a correção é o primeiro
item dos trabalhos futuros.

### Como dizer em 20 segundos

> "Esta é a limitação mais séria do trabalho, e ela é minha, não da plateia me perguntando.
> Nas 41 escolas indígenas e quilombolas o sistema erra sempre para o mesmo lado: prevê 6,12
> pontos percentuais a mais de abandono do que acontece. Urbanas e rurais estão calibradas.
> A explicação provável é que existem fatores de proteção comunitários que os dados públicos
> não captam. Não corrigi nesta versão porque corrigir sem entender esconderia o problema —
> então medi, declarei, e a ressalva aparece na tela junto com cada indicação."

---

# Três pontos a verificar antes da defesa

Encontrados ao conferir cada figura contra o script que a gera. Nenhum invalida o trabalho;
todos são perguntáveis por uma banca atenta, e é melhor chegar com a resposta pronta.

## 1. Figura 17 — o painel esquerdo mistura dois protocolos

**O que acontece.** As duas barras do painel esquerdo vêm de fontes diferentes. A barra "com
o sistema" (52 em cada 100) sai de `reports/metricas_xgboost.csv`, do GroupKFold de 5
partições — a média das cinco é 0,525. A barra "sem o sistema" (7 em cada 100) sai de
`reports/metricas_cv_repetida.csv`, das 20 repetições — média 0,067. Está no código, em
`notebooks/12_figuras_monografia.py`, na função `figura_desempenho`.

**Por que importa.** O número 52 não aparece em lugar nenhum do texto. O Quadro 9 e a síntese
do capítulo reportam 0,504 e falam em "cerca de metade", ambos vindos das 20 repetições. Uma
banca que comparar figura e quadro vai encontrar dois números para a mesma coisa.

**O que fazer.** Trocar a fonte da barra do modelo para `metricas_cv_repetida.csv`, o que faz
a figura exibir 50 em cada 100 e alinha tudo. Se preferir não regerar, a resposta pronta é
que a figura usa o GroupKFold simples e o quadro usa a validação repetida; mas alinhar é mais
limpo. **Regerar a figura exige o ambiente fixado — rodar `/validar-ambiente` antes.**

## 2. Figura 18 — figura e texto usam definições diferentes de "acerto"

**O que acontece.** Há duas definições de acerto em circulação no capítulo.

- No painel esquerdo da Figura 18, "acerto" é o cruzamento entre as K escolas de **maior
  previsão** e as K de **maior abandono observado** — os dois conjuntos crescem juntos com K.
  É a definição de `precision_at_k` em `src/models/evaluate.py`, e é a mesma do Quadro 10
  (0,418 em K = 79). Por essa definição, o acerto **sobe** com o tamanho da lista: cerca de
  34% em 50 escolas e 47% em 150.
- No texto da seção *Capacidade de Priorização*, "críticas" é um conjunto **fixo** — as 79
  escolas do décimo mais alto de 2024. Por essa definição o acerto **cai** com o tamanho da
  lista: 44% em 50 escolas e 31% em 150. Esses valores são coerentes com o alcance citado no
  mesmo parágrafo — 28% das 79 críticas encontradas numa lista de 50 dá 44% de acerto, e 57%
  delas numa lista de 150 dá cerca de 30%.

**Por que importa.** O texto afirma que "ampliá-la aumenta o alcance e reduz o acerto, como
mostra a Figura 18", e o painel esquerdo da Figura 18 mostra o acerto **subindo**. A frase
está correta sob a definição do texto e contradita pela figura que ela cita.

**O que fazer.** Duas saídas. Ou remeter a frase apenas ao painel da direita (o alcance, que
não tem ambiguidade) e explicar o trade-off só com os números do texto. Ou regerar o painel
esquerdo com o conjunto fixo de 79 escolas críticas, o que faria a curva cair e casar com o
texto. A segunda é mais correta conceitualmente, porque é a definição que corresponde à
decisão real do gestor. **Se optar por regerar, `/validar-ambiente` primeiro.**

## 3. Detalhes desatualizados nas figuras de arquitetura

**O que acontece.** As Figuras 3, 4, 5 e 6 marcam o painel Streamlit como "planejado"; a
Figura 6 registra o ambiente como "Python 3.10 (venv)"; a Figura 3 descreve os notebooks como
"01..09 análises, 10 diagramas".

**Por que importa.** O Capítulo 6 apresenta o painel como entregue e em funcionamento, com
suas três funções descritas em detalhe. O ambiente de referência do projeto é Python 3.14, e
os notebooks vão até o 16. Uma banca que ler a arquitetura antes do Capítulo 6 encontra um
painel "planejado" que depois aparece pronto.

**O que fazer.** Regerar os diagramas com `notebooks/10_diagramas_arquitetura.py`, removendo
as marcas de "planejado" do painel e corrigindo a versão do Python. O contêiner Docker
continua legitimamente planejado — está nos trabalhos futuros. Esses diagramas não dependem
do modelo nem dos dados, então regerá-los não altera número algum do Capítulo 6.

---

*Todos os números deste guia foram lidos diretamente das imagens em
`evasao-escolar/reports/figuras/`, dos CSVs em `evasao-escolar/reports/` e do Capítulo 6 da
monografia. Depois de qualquer regeração de figura, rodar `/validar-numeros`.*
