# Instruções para agentes (cópia de CLAUDE.md, mantenha os dois iguais)

Projeto: submissão de Bruno Antoniassi ao **G4 AI Master Challenge 003 (Lead Scorer)**. Leia `ROADMAP.md` antes de qualquer ação: lá estão o estado atual, a próxima tarefa e as decisões já tomadas.

## Regras

1. **Números só saem do motor** (`solution/engine/`). O LLM nunca calcula nem inventa valores para o usuário final. Todo texto gerado por LLM que cite número precisa de validação contra `outputs/scores.json`.
2. **Não reabra decisões do log** (`ROADMAP.md` → Log de decisões) sem dado novo. Para propor uma mudança, adicione uma linha nova com o motivo.
3. **Nunca copie código das submissões concorrentes.** Ideias e padrões citados em `docs/benchmark-003.md` podem ser usados.
4. **Teste antes de commitar:** `cd solution && pytest -q`. Nada de commit com teste quebrado.
5. **Documentação curta.** O G4 penaliza documento longo. README de submissão em no máximo uma página; detalhes vão para `docs/`.
6. **Idioma:** PT-BR em tudo que o usuário final ou o avaliador lê; código e identificadores em inglês.
7. **Integrações:** WhatsApp só via **Whapi** (nunca Z-API); orquestração em **n8n**; LLM em runtime: Claude Haiku (barato) com fallback determinístico. Antes de propor qualquer serviço, verifique e declare os limites do plano gratuito. Recurso pago só com aviso explícito.
8. **O app precisa rodar sem chave de API e sem servidor.** Requisito do desafio: "precisa rodar".
9. **Registro do processo:** ao fim de cada tarefa, registre em `process-log/` o que foi feito, onde a IA errou e o que o Bruno decidiu.

## Ao terminar uma tarefa

1. Marque a tarefa como feita em `ROADMAP.md` e atualize "Estado atual".
2. Rode `pytest -q`.
3. Faça commit com uma mensagem descritiva (`feat(F2): ...`, `docs: ...`) e dê push.

## Estrutura

```
ROADMAP.md            fonte de verdade: fases, estado, decisões
CLAUDE.md / AGENTS.md estas regras
solution/             motor Python (engine/), CLI (run.py), testes, dados, outputs
  app/                (F2) app web estático
automation/           (F3) workflows n8n exportados
docs/                 benchmark e material de apoio
process-log/          evidências do uso de IA (obrigatório no desafio)
```

Na entrega (F5), o conteúdo deste repo vai para `submissions/bruno-antoniassi/` no fork do repositório do G4.
