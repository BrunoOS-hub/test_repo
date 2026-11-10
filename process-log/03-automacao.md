# 03: Automação (F3-A, sem credenciais)

**Data:** 10/11/2026 · **Ferramenta:** Claude Code (VS Code)

## Passos

1. **`outputs/briefs.json`** (49 KB), gerado por `run.py export`: texto pronto de cada vendedor e gestor, com `as_of`, `generated_at`, `engine_commit` e `allowed_numbers` (os números que o motor produziu para aquele texto). O n8n usará esse conjunto para validar o texto do LLM na T3.2.
2. **Digest do gestor** (`build_manager_digest`): recomendação do time (`team_headline`), top 3 vendedores por valor esperado e o link do app (`APP_URL` em `config.py`). Passa pela mesma validação de números do brief.
3. **Workflow n8n** (`automation/n8n-pauta-segunda.json`): Manual Trigger e Schedule (segunda 08:00, America/Sao_Paulo) → GitHub raw → "Destinatários" → loop de 1 → Whapi → espera de 5 s → "Resumo". Sem token, telefone real nem ID de credencial no arquivo.
4. **Testes:** 37 passando. Novos: todo brief e digest passa em `validate_numbers` com o próprio `allowed_numbers`; `briefs.json` tem menos de 200 KB; toda connection do workflow aponta para um nó existente; e o código do nó "Destinatários" roda de verdade (via Node) com o `briefs.json` real, incluindo os erros de telefone placeholder e de nome inexistente.

## Onde a IA errou e como corrigi

- **Teste de export sujava arquivos versionados.** O teste que chama `cmd_export` reescrevia `outputs/` e `app/data.js` no repositório. Com `generated_at` no `briefs.json`, cada `pytest` passaria a gerar diff. Passei os testes a escrever num diretório temporário.
- **Número de telefone de exemplo na mensagem de erro.** A primeira versão do nó citava um número no formato de telefone real como exemplo. Troquei por "55 + DDD + número", para o arquivo não ter nada parecido com telefone, e o teste procura por isso.
- **Não validei o workflow no n8n.** Não há instância aqui. Conferi o JSON, as connections e o código dos nós por teste, mas **a importação e a execução com credenciais ainda não foram feitas**; o ROADMAP marca o T3.3 como "falta importar e testar".

## Decisões minhas (não da IA)

- **D12:** o n8n lê `briefs.json` do GitHub raw. O motor continua a única fonte de números, e os telefones ficam só dentro do n8n.
- **Demo em modo manual** (Manual Trigger) para o vídeo, com o agendamento já configurado para segunda 08:00.

## Teste real (10/11/2026)

- O workflow foi criado direto na instância n8n pelo MCP do n8n, sem import manual, e validado pelo SDK antes de salvar.
- **Teste seco (exec. #1):** sem telefone, buscou o `briefs.json` e parou no erro esperado ("Telefone inválido… preencha o nó Config"). Nada foi enviado.
- **Onde travou:**
  - exec. #2: rodou só o gatilho ("Execute step" no nó, não o workflow inteiro);
  - exec. #3 e #4: o Whapi respondeu **404 "Channel not found"**. A causa era o token de um canal que não estava ativo. O Bruno corrigiu no painel do Whapi e criou uma credencial nova, que não estava ligada ao nó; liguei pelo MCP.
- **Exec. #5:** 2 enviadas, 0 falhas. A pauta do Zane Levy chegou como texto e o digest da Summer Sewald como link preview do app.
- **Lição:** o erro do Whapi vinha do canal, não do workflow. Ler a execução pelo MCP (request e resposta) separou isso em um passo.
- **Segurança:** o token apareceu uma vez no chat. Fica a ação de gerar um token novo depois da gravação do vídeo. O JSON versionado não tem telefone nem ID de credencial (teste automatizado).

## Revisão no celular (10/11/2026)

O Bruno testou a pauta no WhatsApp e achou 3 problemas:

1. **Lista automática:** o WhatsApp transforma "1. " em lista e os 3 espaços de indentação desalinham. Correção: "*1) Produto · Conta*", sem espaço no início de nenhuma linha e com linha em branco entre os blocos.
2. **Código do deal ilegível:** `FZWU2I30` e `4R4QF0ZU` confundem I/1 e O/0 na digitação. Correção: o código saiu do texto. O vendedor responde com a posição ("avancei 1", "perdi 1", "adiar 1") e o `briefs.json` guarda `deals: [{pos, opportunity_id}]` por vendedor, para a F4 mapear posição → deal.
3. **Digest do gestor no mesmo padrão:** cabeçalho, recomendação e top 3 em blocos separados, cada vendedor como "*1) Nome*" + linha de valores.

Testes novos: nenhuma linha começa com espaço ou "<dígito>. "; nenhum ID aparece no texto; `deals` tem pos 1..N com IDs que existem em `scores.json`; a última linha é "*avancei 1* · *perdi 1* · *adiar 1*". `validate_numbers` segue passando (posições 1 a 5 entram no `allowed`).

**Onde a IA errou:** o brief antigo tinha um teste com comentário "todo vendedor tem Agir", falso: 6 de 27 não têm. Sem Agir, "avancei 1" não apontaria para deal nenhum. Correção: nesses casos o "Comece por" da fila Decidir vira o deal 1 (e, se não houver Agir nem Decidir, a linha de resposta some).
