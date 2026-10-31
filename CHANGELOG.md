# Bitácora de versiones

## 0.3.1 — 2026-10-31
Ajuste de redacción del escenario 2027 con intervención (determinación de cumplimiento del 30-oct): la banda sólo decide dónde se concentra la campaña; los puntos +3/+2/+1 se presentan como supuesto declarado, no medido ni documentado por la literatura; la prioridad por riesgo se apoya en el índice y su backtest, no en el escenario. Parámetro `elasticidad_puntos` renombrado a `puntos_campana_por_banda`. Ninguna cifra cambia (49.19 / 50.31; por banda idénticas).

## 0.3.0 — 2026-10-30
Tablero v2.1: leyenda contextual dentro del mapa (título, frase de lectura y escala cambian con «pintar por»). Diseño de plataforma: `docs/ARQUITECTURA-PLATAFORMA.md`, `db/migrations/0001_esquema_base.sql` (7 esquemas, 37 objetos, probado en Postgres 16), `db/seed/` y `scripts/exporta_seed.py` (las vistas reproducen 45/60/89/106 y 49.19/50.31 desde la base).

## 1.0.0 — 2026-10-31
Versión entregada al INE: índice, tablero, CSV, GeoJSON, reporte, láminas y documentación metodológica.

## 0.2.0 — 2026-10-30
Tablero v2: Leaflet embebido, ficha explicativa por distrito (por qué es ese color, qué tan cerca está de cambiar, cálculo 2027 paso a paso), secciones «Cómo se decide el color», «De dónde sale el 50.3 %», glosario de señales, fundamentos matemáticos y sensibilidad. Documento `docs/METODOLOGIA.md`.

## 0.1.0 — 2026-10-30
Primera corrida completa con datos reales del CCPC 2009–2025: crosswalk de redistritación, índice, backtest 2018→2021, prueba de estrés 2025, sensibilidad, escenarios, tablero v1, reporte y láminas.
