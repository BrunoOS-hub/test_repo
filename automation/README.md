# Automação: pauta de segunda no WhatsApp

Workflow n8n que lê `briefs.json` (gerado pelo motor) e envia a pauta de cada vendedor e o digest de cada gestor pelo Whapi.
O n8n **não calcula nem escreve número**: ele só entrega o texto pronto. Os telefones ficam só dentro do n8n.

**Fluxo:** "Rodar agora (demo)" ou "Toda segunda 8h" (America/Sao_Paulo) → nó "Config" (nomes e telefones da demo) → busca `briefs.json` no GitHub raw →
"Montar mensagens" cruza nome e texto → loop de 1 em 1 → `POST gate.whapi.cloud/messages/text` → pausa de 5 s → "Resumo do envio" (enviadas e falhas).

**Validado em 10/11/2026:** execução #5 no n8n Cloud, 2 mensagens entregues (pauta do Zane Levy e digest da Summer Sewald), 0 falhas.

## Como usar

1. No n8n: **Import from file** → `automation/n8n-pauta-segunda.json`.
2. Crie a credencial **Bearer Auth** chamada `Whapi` e cole só o token do canal (sem a palavra "Bearer").
   Se o nó "Enviar via Whapi" não pegar a credencial sozinho, selecione `Whapi` nele.
3. No nó **Config (telefones da demo)**, troque os `55XXXXXXXXXXX` por telefones reais (só dígitos: 55 + DDD + número).
   Com o placeholder, o workflow para com um erro claro.
4. Clique em **Execute workflow** a partir de "Rodar agora (demo)". Para ativar a segunda 08:00, ative o workflow.

Para atualizar a pauta: `python run.py export`, commit e push. O n8n lê sempre a versão da `main`.

## Limites (planos gratuitos)

- **Whapi (sandbox):** 5 conversas por mês, 150 mensagens por dia, 1.000 requisições por mês.
- **n8n Cloud (teste):** 14 dias e 1.000 execuções. Depois disso o workspace é apagado, por isso o workflow fica versionado aqui.
- Para rodar de graça depois do teste: n8n self-hosted (Docker) com o mesmo arquivo.
