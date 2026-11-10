"""Parâmetros do motor. Tudo que é escolha (não medição) fica aqui, com o porquê."""
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Data de referência: último close_date da base. O "hoje" do CRM.
AS_OF = "2017-12-31"

# Horizonte da chance: "ganhar nos próximos 90 dias". Cobre o ciclo mediano
# de deals ganhos (57 dias) e cabe num trimestre.
HORIZON_DAYS = 90

# Faixas de idade (dias desde engage_date). Cortes nos pontos onde a curva muda:
# perdas se concentram nas 2 primeiras semanas; nenhum deal fechou após 138 dias.
AGE_BINS = [-1, 14, 30, 60, 90, 120, 138, 10_000]
AGE_LABELS = ["0-14", "15-30", "31-60", "61-90", "91-120", "121-138", "139+"]

# Maior ciclo já concluído na base (Won ou Lost). Medido em load.max_cycle(),
# fixado aqui só como fallback de documentação.
WALL_DAYS_FALLBACK = 138

# Suavização (Laplace/Beta): evita chance 0% ou 100% em faixas com pouca amostra.
PRIOR_STRENGTH = 10

# Snapshots usados para estimar a curva: segundas-feiras, espaçamento semanal.
SNAPSHOT_FREQ = "W-MON"

# Página pública do app (GitHub Pages). Vai no rodapé do digest do gestor.
APP_URL = "https://brunoos-hub.github.io/test_repo/"
