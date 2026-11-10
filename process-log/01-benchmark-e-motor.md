# 01: Benchmark e motor de score

**Data:** 10/11/2026 · **Ferramenta:** Claude (Opus) com shell e git

## Passos

1. **Li o repositório e escolhi o desafio.** O 003 tem 107 PRs, a maior concorrência. Escolhi mesmo assim, porque é o problema interno do G4: um time comercial de mais de 130 pessoas e meta mensal de R$ 80 milhões.
2. **Benchmark de 109 submissões públicas.** Baixei os PRs via git, extraí métricas por script e li os 28 melhores.
   - Conclusão: os insights estão saturados (AUC ~0,5, parede de 138 dias, 81% de deals zumbis).
   - Lacunas encontradas: ninguém entrega no canal do vendedor, ninguém gera dado de atividade, e a documentação tem mediana de ~24 mil palavras.
3. **Verifiquei os achados nos CSVs originais antes de usar.** AUC 0,506 em holdout temporal; parede de 138 dias; 1.291 de 1.589 deals além dela.
4. **Motor determinístico** (decisão minha, inspirada no artigo do time do G4OS): números saem do código, nunca do LLM.

## Onde a IA errou e como corrigi

- **Classificação dos PRs.** A primeira regex contava "roc" dentro de "process" como evidência de AUC. Apertei os padrões.
- **Ordenação da fila "Decidir".** Na primeira versão, deals com o mesmo preço ficavam em ordem arbitrária. Mudei para "passou da parede há menos tempo primeiro", porque esses são os mais recuperáveis.
- **Backtest não reproduzível.** O número original (+10,6% na nuvem) não bateu na execução local (+7,3%). Detectado comparando execuções. Causa: muitos deals empatados em preço por vendedor e `sort_values` instável, então o top-k mudava entre versões de pandas/numpy. Correção: desempate determinístico por `opportunity_id` (mergesort) e teste de determinismo (inclusive com a base embaralhada). Número reproduzível: +7,3% (D10).
- **"Faltam 0 dias".** A ação sugerida saía com esse texto sem sentido. Criei um caso próprio para o deal que está exatamente no limite.

## Decisões minhas (não da IA)

- **Não usar vendedor × produto no score.** O spread de 47% a 81% cabe no ruído binomial.
- **Baseline "mais novo primeiro" no backtest.** Um concorrente mostrou que essa ordenação empatava com o score dele. Na nossa métrica de receita ela perde feio (−58%).
- **Mostrar valor esperado em US$ em vez de nota 0–100.** O recibo fecha a conta sem pesos arbitrários.
