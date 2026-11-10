# Benchmark — Challenge 003 Lead Scorer (109 submissões)

*Levantado em 10/11/2026. Fonte: os 239 PRs do repositório `Gestao-Quatro-Ponto-Zero/ai-master-challenge`. Classifiquei 109 como 003 (última versão por autor). Os achados de dados foram reproduzidos por mim nos CSVs originais.*

---

## 1. Conclusão em 5 linhas

1. **O espaço de insights está saturado.** Os top 15 chegaram aos mesmos achados (seção 3). Repetir esses achados é obrigatório, mas não diferencia.
2. **A fórmula vencedora já é consenso:** preço de lista × P(ganhar | idade do deal), com os deals "zumbis" separados numa fila de decisão e um backtest contra "ordenar por valor".
3. **Quase todo mundo errou no tamanho.** A mediana dos top 15 é de **~24 mil palavras** de markdown, e alguns passam de 100 mil. O próprio G4 penaliza o "documento de 40 páginas onde 5 resolveriam".
4. **Ninguém entrega onde o vendedor está.** 0 de 109 envia de fato a pauta pelo WhatsApp. 17 citam o WhatsApp, mas só como "trabalho futuro" ou como texto para copiar.
5. **A limitação que todos citam, e ninguém resolve, é a falta de histórico de atividades.** A resposta do vendedor no WhatsApp (avancei / perdi / adiar) cria esse dado.

---

## 2. Verdades dos dados (verificadas por mim)

| Fato | Número |
|---|---|
| Deals por estágio | Won 4.238 · Lost 2.473 · Engaging 1.589 · Prospecting 500 |
| Win rate geral | 63,2% |
| Poder preditivo de produto/setor/região/vendedor/porte | **AUC 0,506** (holdout temporal); a faixa de win rate fica entre 60% e 65% em todas as dimensões |
| Maior ciclo já fechado | **138 dias**. Nenhum deal fechou depois disso |
| Engaging com mais de 138 dias na data de referência (31/12/2017) | **1.291 de 1.589 (81%)**, cerca de US$ 3,2 mi a preço de lista |
| Perda rápida | Mediana do ciclo perdido = 14 dias. Deal que passa de 14 dias aberto tem win rate de **69%** (sobe, não cai) |
| Deals abertos sem conta | 1.425 de 2.089 (68%) |
| Prospecting sem `engage_date` | 500 de 500 |
| Qualidade | `GTXPro` ≠ `GTX Pro` no catálogo; 5 vendedores sem nenhum deal |
| Valor | `close_value` ≈ preço de lista (razão mediana 1,0), então o valor é determinado pelo produto |
| Vendedor × produto | Spread de 47% a 81% em 89 células, dentro do ruído binomial (dp ≈ 7,6pp com n≈40). **Não usar sem shrinkage** |
| Armadilha de vazamento | Duração do ciclo e mês de fechamento usam `close_date` (futuro). Quem reporta AUC de 0,82 ou 0,94 provavelmente vazou |

---

## 3. O que o top já faz (consenso para copiar o padrão, não o código)

Frequência nas 109 submissões:
- Achados: "sem sinal / AUC ~0,5" em 83; parede dos 138 dias em 56; deals zumbis em 97; 68% sem conta em 66; GTXPro em 75.
- Rigor: backtest em 60; vazamento discutido em 63.
- Produto: visão de segunda-feira em 98; próxima ação em 78; visão do gestor em 43; testes automatizados em 64; app publicado em 35.
- LLM em runtime: só ~15. Agente de chat sobre o pipeline: 8.

**Stacks:** HTML estático ou React+Vite são maioria; Streamlit aparece em 33 e Next.js em 20.

---

## 4. Top 15: o melhor de cada um

| PR | Autor | O que pegar |
|---|---|---|
| [#183](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/183) | Bruno Mosconi | Roteiro "avaliar em 2 minutos" no README; núcleo da regra isolado e testado; backtest top-10 por vendedor (41% vs 33% por preço vs 14% sorteio) |
| [#197](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/197) | Eduardo Celestino | Kanban em 3 colunas de ação (Negociar / Qualificar / Confirmar ou encerrar); vídeo de 2 min; intervalo de confiança no ganho (+19%, de +12% a +25%) |
| [#233](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/233) | Vinicius Eduardo | "Máquina do tempo" (escolher uma data passada e revelar o que aconteceu); passos 1-2-3 da semana; atalhos de teclado; comparação contra o "rival mais forte" |
| [#175](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/175) | Matheus Garmatz | Melhor explicabilidade: "96 = +85 valor +11 momento"; relógio do deal (saudável → esfriando → última chance → zumbi); resumo da semana em 4 frases; README curto (~4,8 mil palavras) |
| [#137](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/137) | Marcus Barbosa | P(ganhar em 90 dias) calibrada por 7 snapshots; honestidade: "dentro da faixa de idade o score ordena como o preço" |
| [#220](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/220) | Rafael Pereira | Listas Foque / Reative / Limpe; admite que o ganho vem de tirar zumbis |
| [#208](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/208) | Fabrizio Justino | "Modo emergência" de fim de trimestre: lista que fecha o gap da meta (casa com a cultura de meta do G4) |
| [#223](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/223) | Renan | "Recibo" que fecha a conta do score; Agente Gestor (Claude) restrito aos dados; Radar proativo; 34 testes |
| [#129](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/129) | Guilherme Fraga | Baseline "mais novo primeiro", que empata com o score. É o baseline mais honesto e precisamos incluí-lo |
| [#124](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/124) | Julyan Matheus | 4 grupos (Focar / Requalificar / Iniciar / Limpar); registro de decisões com origem (minha / IA / consenso) |
| [#155](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/155) | Bernardo Couto | Sprint de limpeza com recorte concreto (561 deals de 139 a 180 dias); forecast só com deals vivos |
| [#224](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/224) | Felipe Holanda | Forecast ingênuo vs ajustado pela idade (US$ 2,5 mi vs US$ 168 mil, 15x); GIF de demonstração |
| [#232](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/232) | Erick Cormack | Score em SQL auditável (Supabase) |
| [#230](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/230) | Liberato Gouveia | Curva de chance por idade (47% → 26% aos 90 dias → 0% aos 138) explicada em uma frase |
| [#240](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/240) | Guilherme Breq | Pico de decisão aos ~75 dias; "98 deals cuja janela fecha em 20 dias" |

**Ganhos de backtest reportados contra ordenar só por valor:** de +6pp a +21pp de receita capturada no topo da lista. Os próprios autores admitem que a maior parte vem de remover zumbis.

---

## 5. Onde os 109 falharam (nosso espaço)

1. **Entrega passiva.** Todos exigem que o vendedor abra um app. O README do desafio lista "Bot que envia prioridades por Slack/email" como solução válida, e ninguém entregou isso funcionando. No Brasil, vendas acontecem no WhatsApp.
2. **Sem loop de dados.** Todos citam "a base não tem atividades" como limitação. Nenhum gera esse dado.
3. **Documentação inchada.** O avaliador precisa de 2 minutos, e recebe 24 mil palavras.
4. **LLM mal posicionado.** A maioria não usa LLM no produto. Quem usa, usa em chat genérico. O padrão do próprio G4 (artigo do time do G4OS) é **número determinístico (templates SQL) + LLM só para linguagem + custo de tokens controlado**.

---

## 6. Plano de otimização (eficiência máxima, nada exótico)

**Núcleo, igual ao consenso:**
- Motor determinístico em Python ou SQL: preço × P(ganhar em 90 dias | idade), com a curva medida por snapshots passados.
- Quatro filas: Agir / Decidir (zumbi) / Qualificar (Prospecting) / Completar cadastro.
- Backtest contra quatro baselines: valor, mais novo primeiro, sorteio e "lógica óbvia" (produto/setor/vendedor).
- App web estático com visões do vendedor e do gestor, filtros por vendedor/manager/região, e score com recibo ("+85 valor +11 momento").

**Diferenciais, em ordem de custo-benefício:**
1. **Pauta de segunda via WhatsApp** (n8n + Whapi): às 8h, cada vendedor recebe os 5 deals, o porquê e a ação; o gestor recebe o digest do time. O texto é escrito pelo Claude Haiku a partir do JSON do motor, com validação de que todo número citado existe no JSON.
2. **Respostas viram dado:** o vendedor responde 1, 2 ou 3 (avancei / perdi / adiar), o n8n grava, e a fila da semana seguinte já considera a resposta. Isso resolve a limitação que todos os 109 deixaram aberta.
3. **Custo explícito:** custo em tokens por vendedor por semana no README, no espírito do G4OS.
4. **README de no máximo 1 página** com roteiro "avaliar em 2 minutos", vídeo de 90 segundos e o resto em `docs/`.
5. **Registro do processo curto e com julgamento,** incluindo este benchmark ("analisei as 109 submissões públicas antes de construir").

**Restrições de custo:**
- O sandbox gratuito do Whapi tem 5 conversas/mês, 150 mensagens/dia e 1.000 requisições/mês. Basta para o desenvolvimento e o vídeo, mas não para um número público de demonstração. O plano pago custa US$ 35/mês por canal (US$ 29 no anual), e só vale contratar se decidirmos deixar um número aberto para o avaliador.
- O web app precisa rodar sozinho, sem chave de API, porque o requisito é "precisa rodar".

**Riscos:**
- O avaliador não testa o WhatsApp sem número; isso se mitiga com prévia da mensagem dentro do app e vídeo.
- Mostrar que analisamos os PRs dos concorrentes pode ser lido como "copiou". A mitigação é reutilizar padrões e ideias, nunca código, e citar as fontes no registro do processo.
