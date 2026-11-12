#!/usr/bin/env bash
# Gera requisições variadas (200, 404, 500, 503) para popular o dashboard do Kibana.
# Uso: bash observability/gerar_trafego.sh [url_base] [quantidade]
BASE=${1:-http://localhost:8000}
N=${2:-200}
ROTAS=(
  "/health" "/health" "/health"
  "/clima/diario" "/clima/diario?localidade=moju" "/clima/mensal"
  "/clima/diario?localidade=belem"   # 404
  "/simular-erro"                    # 500
)
for ((i = 1; i <= N; i++)); do
  rota=${ROTAS[RANDOM % ${#ROTAS[@]}]}
  curl -s -o /dev/null -w "%{http_code} $rota\n" "$BASE$rota"
  sleep 0.2
done
