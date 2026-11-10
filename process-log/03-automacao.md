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
