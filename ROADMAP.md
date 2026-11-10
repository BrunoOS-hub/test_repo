# ROADMAP: G4 AI Master · Challenge 003 Lead Scorer

> **Fonte única de verdade do projeto.** Qualquer pessoa ou LLM que retomar o trabalho lê este arquivo primeiro, depois o `CLAUDE.md`.
> Atualize o status, a seção "Estado atual" e o log de decisões ao fim de cada etapa.

**Candidato:** Bruno Antoniassi · **Desafio:** [ai-master-challenge / 003](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/tree/main/challenges/build-003-lead-scorer) · **Início:** 10/11/2026

---

## Estado atual

- **Fase:** F3 (pauta via WhatsApp)
- **Último marco:** app web estático pronto (Vendedor, Gestor, Como funciona) e brief de WhatsApp determinístico no motor (15/15 testes). Falta ativar o GitHub Pages (Settings → Pages → Source: GitHub Actions).
- **Próxima ação:** F3, a partir do T3.2 (redação opcional com Claude Haiku, validada por `validate_numbers`) e do T3.3 (workflow n8n + Whapi).
- **Bloqueios:** nenhum.

---

## Tese

Os 109 concorrentes do 003 chegaram aos mesmos insights (ver `docs/benchmark-003.md`):
- atributos do CRM não preveem ganho (AUC ~0,5);
- nenhum deal fechou depois de 138 dias;
- 81% dos deals em Engaging já passaram desse limite.

Repetir isso é obrigatório e não diferencia. **O diferencial é a entrega:**

1. **Pauta de segunda no WhatsApp,** em vez de um app que o vendedor precisa lembrar de abrir. Zero de 109 concorrentes fazem isso.
2. **A resposta do vendedor vira dado** ("1 avancei / 2 perdi / 3 adiar"). Isso resolve a limitação que todos citam: a base não tem histórico de atividades.
3. **Padrão G4OS:** número sai do código determinístico, o LLM só redige, e o custo é medido.
4. **Documentação curta:** README de uma página e roteiro "avaliar em 2 minutos". A mediana dos concorrentes é de ~24 mil palavras.

---

## Fases

Legenda: ✅ feito · 🔄 em andamento · ⬜ a fazer

### F0: Pesquisa e decisão ✅ (~1h)
- [x] Ler o repositório do desafio e as regras de submissão
- [x] Pesquisar o G4 (modelo, cultura, uso de IA, G4OS)
- [x] Escolher o 003 (problema interno do G4: área comercial com mais de 130 pessoas, meta mensal de R$ 80 milhões)
- [x] Benchmark das 109 submissões → `docs/benchmark-003.md`, `docs/benchmark_003_109.csv`

### F1: Motor de score + backtest ✅ (~1h)
- [x] T1.1 Carga e limpeza (`GTXPro` → `GTX Pro`, auditoria de dados)
- [x] T1.2 Curva P(ganhar em 90 dias | idade), estimada por snapshots semanais e sem vazamento
- [x] T1.3 Score = preço × chance; filas Agir / Qualificar / Decidir; razão e ação em PT-BR
- [x] T1.4 Backtest em 18 segundas contra valor, "óbvia", mais novo e sorteio: **+7,2% vs valor (IC 90%: +1,6% a +13,1%)**, após corrigir o desempate (D10)
- [x] T1.5 8 testes (pytest)
- [x] T1.6 Validar localmente no Mac (venv, pytest, run.py) + backtest determinístico (9 testes)

### F2: App web ✅ (~1,5h)
Stack: **HTML + JS puro, sem build.** Abre com duplo clique e publica no GitHub Pages.
- [x] T2.1 `run.py export` gera também `app/data.js` (`window.SCORES = {...}`), porque `fetch` não funciona em `file://`
- [x] T2.2 **Visão do vendedor ("Minha semana"):**
  - seletor de vendedor, resumo em 3 frases;
  - as 3 filas, com cards de produto, conta, valor esperado, recibo e ação;
  - barra de idade até 138 dias.
- [x] T2.3 **Visão do gestor:**
  - filtros por manager e região;
  - por vendedor: vivos, valor esperado, zumbis e valor parado;
  - botão "exportar CSV".
- [x] T2.4 Aba "Como funciona": curva, backtest e o que não usamos e por quê. No máximo uma tela.
- [x] T2.5 Prévia da mensagem de WhatsApp de cada vendedor, gerada pelo mesmo motor
- [x] T2.6 Testado em 390px (sem rolagem horizontal). Workflow `.github/workflows/pages.yml` pronto; **falta ativar:** Settings → Pages → Source: GitHub Actions

### F3: Pauta via WhatsApp 🔄 (~1,5h)
- [x] T3.1 `engine/brief.py`: monta a mensagem determinística (top 5 Agir + resumo de Decidir) e `validate_numbers` para checar texto de LLM (D11)
- [ ] T3.2 Redação opcional com Claude Haiku:
  - **regra:** todo número no texto do LLM precisa existir no JSON; se não existir, usa o texto determinístico;
  - registrar custo em tokens por vendedor.
- [ ] T3.3 Workflow n8n: Cron (seg 8h) → brief → Whapi `POST /messages/text` → log. Exportar o JSON para `automation/`.
- [ ] T3.4 Digest do gestor (1 mensagem por manager)
- [ ] T3.5 Gravar a demonstração (vídeo curto) com 1 a 2 números reais

**Restrição:** o sandbox gratuito do Whapi tem 5 conversas/mês, 150 mensagens/dia e 1.000 requisições/mês. Basta para o desenvolvimento e o vídeo. O plano pago (US$ 35/mês por canal, US$ 29 no anual) só se justifica se decidirmos deixar um número aberto para o avaliador.

### F4: Loop de respostas ⬜ (~1h)
- [ ] T4.1 Webhook do Whapi → n8n: interpretar "1/2/3 + código do deal"
- [ ] T4.2 Persistir as respostas. **Verificar os limites do plano gratuito antes de escolher** entre Upstash Redis, Google Sheets e Data Tables do n8n.
- [ ] T4.3 O motor lê as respostas:
  - "perdi" sai da fila;
  - "adiar" some por 7 dias;
  - "avancei" ganha um selo e o registro da data.
- [ ] T4.4 Teste: uma resposta muda a pauta da semana seguinte

### F5: Entrega ⬜ (~1h)
- [ ] T5.1 README da submissão em uma página (template do G4), com roteiro "avaliar em 2 minutos"
- [ ] T5.2 Registro do processo: consolidar `process-log/` (ferramentas, fluxo, onde a IA errou, o que eu adicionei)
- [ ] T5.3 Vídeo de 90 segundos (vendedor → gestor → WhatsApp → resposta)
- [ ] T5.4 Checagem final do zero: clone limpo → setup → app abre → testes passam
- [ ] T5.5 Fork de `Gestao-Quatro-Ponto-Zero/ai-master-challenge` → branch `submission/bruno-antoniassi` → copiar este repo para `submissions/bruno-antoniassi/` → PR com título `[Submission] Bruno Antoniassi — Challenge 003`

**Orçamento total:** ~7h. O G4 recomenda 4 a 6h. Cortar F4 primeiro se o tempo apertar, mantendo-a como "próximo passo" no README.

---

## Log de decisões

| # | Decisão | Por quê | Origem |
|---|---|---|---|
| D1 | Challenge 003 | Problema diário do G4; destaque entre 107 vale mais | Bruno |
| D2 | Não usar produto/setor/vendedor/porte no score | AUC 0,506 em holdout temporal; vendedor × produto cabe no ruído binomial | Dados |
| D3 | Score = preço × P(ganhar em 90 dias \| idade) | Única variável com sinal; recibo em US$ sem pesos arbitrários | Dados + Claude |
| D4 | Parede de 138 dias → fila Decidir com chance 0 | Nenhum deal concluído passou de 138 dias | Dados |
| D5 | Fila Decidir ordenada por "passou da parede há menos tempo" | É o que tem mais chance de ser recuperado | Claude, revisado por Bruno |
| D6 | Números só do motor; LLM só redige | Padrão do G4OS (templates SQL); evita número inventado | Bruno |
| D7 | App em HTML + JS puro | Avaliador abre sem instalar nada; menos risco | Claude |
| D8 | Whapi (nunca Z-API) + n8n | Stack do Bruno; canal real do vendedor brasileiro | Bruno |
| D9 | Reaproveitar ideias de concorrentes, nunca código; citar o benchmark no registro do processo | Transparência; os avaliadores têm os 109 PRs | Bruno + Claude |
| D10 | Desempate determinístico por opportunity_id no backtest | +10,6% era artefato de ordenação instável; o número reproduzível é +7,2% | Claude Code (detectou) + Bruno |
| D11 | Brief gerado no motor e reutilizado no app e no WhatsApp | Um só texto, um só lugar de validação; o app não calcula nada | Bruno + Claude |

---

## Números de referência (validados)

- 8.800 deals: Won 4.238 · Lost 2.473 · Engaging 1.589 · Prospecting 500. Win rate 63,15%.
- Parede: 138 dias. Engaging além dela: 1.291 (81%), cerca de US$ 3,2 mi a preço de lista.
- Abertos sem conta: 1.425 de 2.089 (68%). Prospecting sem `engage_date`: 500 de 500.
- Curva de chance em 90 dias por idade: 0-14 38% · 15-30 41% · 31-60 45% · 61-90 45% · 91-120 30% · 121-138 6% · 139+ 0%.
- Backtest (top 5 por vendedor, 18 segundas): score 25,2% · valor 23,5% · óbvia 23,5% · mais novo 9,8% · sorteio 8,2%. Ganho do score: +7,2% vs valor (IC 90%: +1,6% a +13,1%).

---

## Como retomar numa conversa nova

1. Cole na LLM: *"Leia ROADMAP.md e CLAUDE.md do repo BrunoOS-hub/test_repo e continue da próxima ação."*
2. Fluxo de trabalho: **o chat orquestra** (planeja, revisa, escreve prompts) e **o Claude Code no VS Code executa** (código e testes). Ao fim de cada tarefa, o Claude Code atualiza este arquivo e faz commit.
