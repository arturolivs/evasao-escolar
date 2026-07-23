# Comentários do Orientador — TCC Evasão Escolar

Fonte: `TCC_Evasao_Escolar_comentários.pdf` (autor dos comentários: SS)
Extraídos em 22/07/2026. Todos os 13 comentários estão no **Capítulo 6 — Testes e Análise dos Resultados** (páginas 31–39).

---

## Lista de comentários

| # | Pág. | Seção / âncora | Comentário |
|---|------|----------------|------------|
| SS1 | 31 | 6.2.1 Base Construída | *"não fica claro porque reduziu de 2392 para 1586"* |
| SS2 | 32 | 6.2.2 O Que o Sistema Prevê | *"faltou citar a figura 7"* |
| SS3 | 32 | 6.2.2 (resposta a SS2) | *"precisa de um parágrafo para explicar esse gráfico"* |
| SS4 | 32 | 6.2.2 (resposta a SS2) | *"incluir na média valor do desvio padrão"* |
| SS5 | 32 | 6.2.2 — parágrafo "Daí decorre o critério…" | *"tá com cara de discussão, deveria ser falado depois de mostrar toda a análise estatística"* |
| SS6 | 32 | 6.2.2 (resposta a SS5) | *"reserve para conclusão do TCC"* |
| SS7 | 32 | 6.2.3 | *"troca informações por feature ou característica"* |
| SS8 | 33 | Quadro 5 | *"revisar essa coluna — Reprovação no ano anterior (Ensino Médio)"* |
| SS9 | 33 | Quadro 5 | *"o que é Adequação da formação docente — Grupo 1?"* |
| SS10 | 33 | Quadro 5 (resposta a SS9) | *"explicar as colunas dessa tabela, antes da tabela aparecer, imediatamente antes"* |
| SS11 | 33 | Quadro 5 (resposta a SS9) | *"ex: nível socioeconômico (INSE) é um valor que varia de 0 a 10, e indica o desenv. econômico da comunidade onde a escola está inserida"* |
| SS12 | 36 | Quadro 6 | *"a coluna abandono tem e abandono não tem — devem somar 100% para fazer sentido essa tabela"* |
| SS13 | 39 | 6.3.2 — Quadro 8 | *"mostre a comparação usando 1 modelo e dois cenários: 2022 prevendo 2023 e 2023 prevendo 2024"* |

### Agrupamento por natureza

- **Terminologia:** SS7
- **Rastreabilidade metodológica:** SS1, SS8, SS12
- **Didática de tabelas e figuras:** SS2, SS3, SS4, SS9, SS10, SS11
- **Reestruturação / novo experimento:** SS5, SS6, SS13

---

## Ordem de execução

### Fase 1 — Verificação factual
*Primeiro de tudo: pode invalidar texto já escrito.*

- [x] **SS8** — ~~Auditar a coluna "Reprovação no ano anterior (EM)" no Quadro 5.~~ **Concluído.** Os números estavam corretos; o defeito era a incoerência entre a linha do EM e as das séries (o total do INEP inclui 4ª série e não seriado). Implementado o atributo `oferta_em_nao_seriado` no pipeline + testes. Texto e números para o documento em `SS8_TEXTO_PARA_O_TCC.md`.
  - ⚠️ Achado colateral: o Quadro 8 **não é reprodutível** no ambiente atual — a partição da CV mudou por versão de biblioteca, não pela correção. Resolver junto com o SS13 (Fase 3). Detalhes no mesmo arquivo.
- [x] **SS12** — ~~Reinterpretar o Quadro 6.~~ **Concluído.** Nenhum número estava errado; o defeito era a tabela misturar duas grandezas (repartição das escolas × médias de grupo) sem sinalizar. Adicionadas contagens e a coluna complementar, Figura 9 regenerada como barra empilhada 100%, + 4 testes. Texto em `SS12_TEXTO_PARA_O_TCC.md`.
- [ ] **SS1** — Documentar a queda de 2.392 → 1.586 registros (perda do último ano pelo casamento temporal + escolas sem par ano/ano+1), com o número exato de cada exclusão.

### Fase 2 — Terminologia
*Varre o documento inteiro; fazer antes de reescrever parágrafos.*

- [ ] **SS7** — Substituir "informações" por "características" (ou "features") em todo o TCC, não só no Cap. 6. Fazer agora evita reescrever duas vezes os parágrafos das fases seguintes.

### Fase 3 — Novo experimento
*Maior esforço técnico; roda em paralelo com a Fase 4.*

- [ ] **SS13** — Rodar e tabular a comparação de um único modelo em dois cenários temporais (2022→2023 e 2023→2024). Único comentário que exige código e execução novos; começar cedo para o resultado estar pronto quando a redação chegar em 6.3.2.

### Fase 4 — Redação e didática

- [ ] **SS10 + SS9 + SS11** — Parágrafo introdutório imediatamente antes do Quadro 5, definindo cada coluna e cada indicador (INSE: escala e significado; Grupos 1–5 da adequação da formação docente conforme classificação do INEP; distorção idade-série). Tratar os três juntos — é um único bloco de texto.
- [ ] **SS4** — Incluir desvio-padrão junto das médias na seção 6.2.2 (taxas por grupo urbano/rural/indígena). O Quadro 5 já tem a coluna; o texto corrido não.
- [ ] **SS2 + SS3** — Citar a Figura 7 no texto e escrever o parágrafo que a interpreta. Depois dos itens acima, porque o vocabulário de leitura das estatísticas já estará estabelecido.

### Fase 5 — Reestruturação
*Por último; depende de todo o texto acima estar estável.*

- [ ] **SS5 + SS6** — Mover o parágrafo "Daí decorre o critério de avaliação…" para depois de toda a análise estatística (provavelmente o fecho da seção 6.2) e transferir a parte argumentativa ("seria inútil ao gestor") para a conclusão do TCC. Deixar por último porque é um recorte-e-cola que quebra se os parágrafos vizinhos ainda estiverem em mudança.

---

## Observações sobre o caminho crítico

- **SS8 → Fase 4:** se o recálculo da coluna de reprovação mudar valores, os parágrafos interpretativos precisam ser escritos sobre os números corretos.
- **SS13** é o item de maior risco de prazo, por depender de execução de código — vale destravá-lo já na Fase 1, em paralelo.
