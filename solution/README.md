# Lead Scorer: motor

Motor determinístico que ordena os deals abertos do CRM. Todo número que o vendedor vê (no app ou no WhatsApp) sai daqui.

## Rodar

```bash
cd solution
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py audit              # qualidade dos dados
python run.py curve              # chance de ganhar em 90 dias por idade do deal
python run.py agent "Zane Levy"  # pauta de segunda de um vendedor
python run.py backtest           # score vs. alternativas em segundas passadas
python run.py export             # outputs/scores.json + app/data.js (app e WhatsApp)
open app/index.html              # app web: duplo clique, sem servidor e sem chave de API
pytest -q                        # 30 testes
```

## Lógica

1. **O que não usamos.** Produto, setor, região, vendedor e porte não separam ganho de perda: o AUC em holdout temporal é 0,51, ou seja, cara ou coroa. Usá-los seria vender ruído como ciência.
2. **O que usamos: a idade do deal.** A curva é medida em "fotos" semanais do pipeline passado, só com resultados já conhecidos na data (sem vazamento):

   | Idade | 0-14 | 15-30 | 31-60 | 61-90 | 91-120 | 121-138 | 139+ |
   |---|---|---|---|---|---|---|---|
   | Chance de ganhar em 90 dias | 38% | 41% | 45% | 45% | 30% | 6% | **0%** |

   Nenhum deal da base fechou depois de **138 dias**.
3. **Score = preço de lista × chance pela idade.** O resultado é o valor esperado em US$, explicado em uma frase que fecha a conta.
4. **Três filas:**
   - **Agir:** deals vivos, ordenados por valor esperado.
   - **Qualificar:** deals em Prospecting, sem data de início, ordenados por preço.
   - **Decidir:** deals além de 138 dias, para reativar com data de decisão ou dar como perdidos.

## Backtest

Avaliamos 18 segundas-feiras, de junho a outubro de 2017, com o top-5 de cada vendedor e a receita ganha nos 90 dias seguintes.

| Ordenação | Receita capturada | vs. "valor" |
|---|---|---|
| **Score** | **25,2%** | **+7,2%** (IC 90%: +1,6% a +13,1%) |
| Valor (preço) | 23,5% | — |
| "Óbvia" (preço × win rate do vendedor × do produto) | 23,5% | 0% (empata com valor) |
| Mais novo primeiro | 9,8% | −58% |
| Sorteio | 8,2% | −65% |

## Limitações

- O ganho vem principalmente de tirar da frente os deals além da parede dos 138 dias.
- As semanas do backtest se sobrepõem (horizonte de 90 dias), então o intervalo de confiança é otimista.
- A base é sintética e não tem histórico de atividades. O loop de respostas pelo WhatsApp existe para criar esse dado.
