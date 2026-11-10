# Automação: pauta de segunda no WhatsApp

Workflow n8n que lê `briefs.json` (gerado pelo motor) e envia a pauta de cada vendedor e o digest de cada gestor pelo Whapi.
O n8n **não calcula nem escreve número**: ele só entrega o texto pronto. Os telefones ficam só dentro do n8n.

**Fluxo:** Manual Trigger (demo) ou Schedule (segunda 08:00, America/Sao_Paulo) → busca `briefs.json` no GitHub raw → nó
"Destinatários" cruza nome e telefone → loop de 1 em 1 → `POST gate.whapi.cloud/messages/text` → espera 5 s → "Resumo" (enviadas e falhas).

## Como usar

1. No n8n: **Import from file** → `automation/n8n-pauta-segunda.json`.
2. Crie a credencial **Header Auth** chamada `Whapi`: *Name* `Authorization`, *Value* `Bearer <seu token>`.
   Se o nó "Enviar via Whapi" não pegar a credencial sozinho, selecione `Whapi` nele.
3. No nó **Destinatários**, troque os `55XXXXXXXXXXX` por telefones reais (só dígitos: 55 + DDD + número) e os nomes, se quiser.
   Com o placeholder, o nó para com um erro claro.
4. Clique em **Test workflow** (Manual Trigger). Para ativar a segunda 08:00, ative o workflow.

Para atualizar a pauta: `python run.py export`, commit e push. O n8n lê sempre a versão da `main`.

## Limites (planos gratuitos)

- **Whapi (sandbox):** 5 conversas por mês, 150 mensagens por dia, 1.000 requisições por mês.
- **n8n Cloud (teste):** 14 dias e 1.000 execuções. Depois disso o workspace é apagado, por isso o workflow fica versionado aqui.
- Para rodar de graça depois do teste: n8n self-hosted (Docker) com o mesmo arquivo.
