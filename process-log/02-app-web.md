# 02: App web e brief de WhatsApp

**Data:** 10/11/2026 · **Ferramenta:** Claude Code (VS Code), com Chrome para a verificação visual

## Passos

1. **Estimativa pontual como número principal.** README e ROADMAP passam a citar +7,2% (IC 90%: +1,6% a +13,1%). O +7,3% era a mediana do bootstrap. `run.py backtest` imprime as duas.
2. **`engine/brief.py`.** Resumos por vendedor, manager e região, e `build_brief` (texto de WhatsApp em PT-BR, determinístico). `validate_numbers` recusa qualquer número que o motor não tenha produzido; vai validar o texto do LLM na F3 (D11).
3. **`run.py export`** gera `outputs/scores.json` e `app/data.js` (`window.SCORES`), porque `fetch` não funciona em `file://`. Inclui backtest, resumos e o brief de cada vendedor.
4. **App em HTML + CSS + JS puros** (Vendedor, Gestor, Como funciona). O JS só filtra, ordena por campos exportados e exibe. As linhas de totais vêm do Python: vendedor, manager, região ou base inteira, conforme o filtro.
5. **Testes:** 15 passando. Novos: todo número de todo brief passa em `validate_numbers`; número inventado é acusado; `data.js` é parseável; soma de vivos == fila Agir.
6. **Deploy:** `.github/workflows/pages.yml` (upload de `solution/app`). Falta o passo manual: Settings → Pages → Source: GitHub Actions.
7. **Verificação visual:** `process-log/screenshots/` (vendedor, gestor, como funciona, vendedor em 390px). Em 390px não há rolagem horizontal da página; só a tabela do gestor rola dentro do próprio quadro.

## Onde a IA errou e como corrigi

- **A validação do brief barrou o primeiro export.** A lista de números permitidos não incluía o horizonte de 90 dias ("em 90 dias"). Exatamente o tipo de falha que `validate_numbers` existe para pegar; adicionei `HORIZON_DAYS` à lista.
- **`sed -i` do Linux no macOS.** A troca +7,3% → +7,2% quebrou na primeira tentativa (o macOS exige `-i ''`) e a edição de `run.py` encadeada depois dele nem rodou. Refiz e conferi com `grep`.
- **Título do card com gambiarra.** A primeira versão montava o título e corrigia o texto depois, quando não havia conta. Reescrevi para montar certo de uma vez.
- **Estado das abas.** Ao ir do Vendedor para o Gestor, o vendedor escolhido ficava como filtro e a tabela mostrava uma linha só. Passei a limpar o filtro no Gestor e a restaurá-lo ao voltar.
- **Verificação em `file://` e em 390px.** A extensão do Chrome não abre `file://`, e a janela não encolhia abaixo de 704px. Servi a pasta em `localhost` só para a captura e emulei 390px e 1200px com uma página temporária de `iframe` (apagada depois). O app em si não usa servidor.

## Decisões minhas (não da IA)

- **O app não calcula nada.** Todo número e todo texto vêm do Python.
- **+7,2% (estimativa pontual) como número principal,** com o IC ao lado.
- **Brief gerado no motor** e reaproveitado no app e no WhatsApp (D11).
