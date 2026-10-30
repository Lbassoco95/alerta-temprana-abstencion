#!/usr/bin/env bash
# Reproduce todos los resultados a partir de los agregados incluidos en data/agregados (menos de 2 minutos).
set -e
cd "$(dirname "$0")"
python3 scripts/indice.py      # índice, bandas, mecanismo, validación, sensibilidad, escenarios  -> outputs/
python3 scripts/exporta.py     # CSV y GeoJSON entregables                                         -> entregables/
python3 scripts/tablero.py     # tablero autocontenido; también escribe docs/index.html (GitHub Pages)
