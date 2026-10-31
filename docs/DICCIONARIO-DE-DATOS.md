# Diccionario de datos

## `entregables/indice_riesgo_abstencion_distrital.csv` (300 filas)

| Columna | Descripción | Unidad |
|---|---|---|
| id_distrito | Clave `EE-DD` (entidad-distrito, cartografía 2023) | texto |
| entidad, EDOCVE, DEF | Nombre y claves INE de entidad y distrito | — |
| municipio_principal, n_municipios, municipios | Municipio con mayor lista nominal dentro del distrito, cuántos municipios lo integran y su composición (% de la lista nominal 2024; los menores a 3 % se agrupan). Derivado del CCPC 2024 a nivel sección; no es la cabecera oficial | — |
| LN_2024 | Lista nominal de los cuadernillos, 2024 | personas |
| banda | rojo · naranja · amarillo · verde | categoría |
| R | Índice de riesgo | 0–100 |
| A_habito, B_desafeccion, C_vulnerabilidad | Componentes del índice | 0–100 |
| mecanismo | Componente dominante (≥ 40 % de R) o `mixto` | categoría |
| prioridad, rango_prioridad | R × LN/LN_máx y su orden nacional (1 = mayor prioridad) | — |
| A1_desgaste_juvenil | −pendiente anual de la participación 18–29 (2009–2024) | puntos/año |
| A2_brecha_generacional | (p30+ − p18–29)₂₀₂₄ − (p30+ − p18–29)₂₀₁₂ | puntos |
| A3_retencion_cohorte | mediana(r) − r, r = p30–39,2024 − p18–29,2012 | puntos |
| B1_rebote_perdido | (p2012 − p2009) − (p2024 − p2021) | puntos |
| B2_caida_adulta | p30+,2018 − p30+,2024 | puntos |
| B3_volatilidad | Desv. est. de residuos de la trayectoria | puntos |
| C1_rural_mixto | % de LN 2024 en secciones rurales y mixtas | % |
| C2_brecha_genero | \|p mujeres − p hombres\|, 2024 | puntos |
| C3_peso_juvenil | % de LN 2024 con 18–29 años | % |
| p_total_AAAA, p_J_AAAA, p_A_AAAA, p_M_AAAA, p_H_AAAA | Participación total, 18–29, 30+, mujeres, hombres en el año AAAA | % |
| p_total_2025, sorpresa_2025 | Participación judicial 2025 y caída no anticipada (centrada) | % / puntos |
| p_2027_sin_intervencion, p_2027_con_intervencion | Escenarios | % |

Participación = 100 · SV / (SV + NV) (registros con marca de voto sobre registros con y sin marca; excluye no especificados), como en la plataforma CCPC.

## `entregables/semaforo_riesgo_abstencion_distrital.geojson`

FeatureCollection de 300 polígonos (EPSG:4326, simplificados a 0.003°) con `id_def`, `EDOCVE`, `DEF` y los atributos principales del CSV.

## `data/agregados/ccpc_AAAA_def24.csv`

Agregado de los archivos originales a `AELEC, EDOCVE, DEF2024, SEXO (0 H, 1 M, 2 no binario en 2024+), GEDAD (18-19, 20-24, 25-29, 30-39, 40-49, 50-59, 60-69, 70+), TIPOSEC (U, M, R)` con sumas de `LN, SV, NV, NS`. `DEF2024` es el distrito en cartografía 2023 para todos los años. Los archivos `_mun` y `_sec` son agregados a municipio y sección (con el DEF original del archivo) para análisis complementarios.

## `data/crosswalk/seccion_a_def2024.csv`

`EDOCVE, SECCION, DEF2024, fuente` donde `fuente` ∈ {directo, hijas, mayoria_dis2018}. Ver `docs/METODOLOGIA.md` §11.

## `outputs/`

`indice_distrital.csv` (todas las columnas intermedias, incluidos percentiles `pct_*`), `series_distrital.csv` (participación por distrito, año y grupo), `backtest_2018_2021.csv`, `sensibilidad.csv`, `escenarios.csv`, `escenarios_nacional.json`, `validacion.json`.
