# Plataforma «Alerta temprana de abstención» — arquitectura propuesta (fase 2)

**Estado:** propuesta de diseño, 30-oct-2026. Lo entregado al Hackathon (v1.0.0) es un pipeline reproducible y un tablero estático. Este documento describe cómo convertirlo en un sistema que el INE pueda **seguir alimentando**, usar para **decidir** y, con el tiempo, leer **señales cercanas al tiempo real** del comportamiento electoral, con la misma disciplina con que Yoltik construye sus productos: base de datos como fuente de verdad, todo versionado, migraciones nuevas y nunca editadas, evidencia de cada cambio.

---

## 1. Principios

1. **La base de datos es la fuente de verdad; el índice es una vista calculada.** Ningún número vive sólo en un HTML o en un CSV: todo lo que se muestra sale de una tabla con fecha, versión y origen.
2. **Todo se versiona:** cartografías (2021, 2023, la que venga), configuraciones del índice (pesos, cortes), corridas del modelo y fuentes. Dos corridas con distinta configuración conviven y se comparan; nunca se sobrescriben.
3. **Sin datos personales, por diseño.** La unidad mínima almacenada es sección × sexo × grupo de edad. Ninguna tabla admite identificadores de personas; la restricción se impone en el esquema, no en la buena voluntad.
4. **Del dato a la decisión y de vuelta.** El sistema registra qué intervención se decidió en cada distrito, cuándo se ejecutó y qué pasó después, para que la siguiente elección evalúe la intervención y no sólo el riesgo.
5. **Capas separadas:** ingesta (Python), almacenamiento y cálculo (Postgres/Supabase), API (PostgREST + funciones), presentación (web). Cada capa se puede reemplazar sin tocar las otras.

## 2. Capas

```
┌──────────────────────────── PRESENTACIÓN (web, React + Vite + Tailwind + MapLibre) ────────────────────────────┐
│  Público: tablero guiado ("¿qué quieres saber?")  ·  Junta distrital: mi distrito, mi plan, mi seguimiento   │
│  Dirección (DECEyEC): priorización nacional, comparación de corridas, escenarios  ·  Analista: explorador    │
└──────────────────────────────────────────────┬────────────────────────────────────────────────────────────────┘
                                               │ PostgREST / RPC (sólo lectura para público; escritura por rol)
┌──────────────────────────────────────────────┴────────────────────────────────────────────────────────────────┐
│  SUPABASE (Postgres 15 + PostGIS + RLS + Realtime)                                                              │
│  Esquemas: cat (catálogos y cartografía) · hecho (observaciones) · modelo (config, corridas, resultados)       │
│            decision (intervenciones y seguimiento) · senal (series continuas) · audit (bitácora)               │
│  Vistas materializadas para el tablero · Funciones SQL para percentiles, bandas y escenarios                  │
└──────────────────────────────────────────────┬────────────────────────────────────────────────────────────────┘
                                               │ jobs (Python, programados) y cargas manuales auditadas
┌──────────────────────────────────────────────┴────────────────────────────────────────────────────────────────┐
│  INGESTA: CCPC por elección (batch) · cartografía DERFE · señales periódicas (módulos de credencialización,    │
│  actividades ENCCÍVICA, capacitación, casillas) · jornada electoral (SIJE/PREP agregados por sección)          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 3. Modelo de datos

Siete esquemas. Las tablas están en `db/migrations/0001_esquema_base.sql`; aquí el porqué de cada una.

### 3.1 `cat` — catálogos y cartografía (lo que cambia poco)

| Tabla | Qué guarda | Por qué así |
|---|---|---|
| `cat.entidad` | 32 entidades con clave INE | Ancla de todo |
| `cat.cartografia` | Versiones del marco geográfico (2021, 2023, …) con fecha de corte y acuerdo | La distritación cambia; el sistema debe saber en qué marco vive cada dato |
| `cat.distrito` | Distrito × cartografía, con geometría (PostGIS) | Permite mapas para cualquier versión y comparar 2021 vs 2023 |
| `cat.seccion` | Sección × cartografía, tipo (U/M/R), municipio, distrito federal y local | Nivel mínimo de agregación; la llave entre marcos |
| `cat.equivalencia_seccion` | Sección (marco A) → sección/distrito (marco B), con la fuente de la asignación | El crosswalk que hoy está en `data/crosswalk/`, ya como tabla auditable |
| `cat.eleccion` | Elección: fecha, tipo (presidencial, intermedia, judicial, local), cartografía aplicable | Sustituye los `[2009…2024]` escritos en código |
| `cat.grupo_edad`, `cat.sexo` | Catálogos cerrados | Evita códigos mágicos |

### 3.2 `hecho` — observaciones (lo que se mide)

| Tabla | Grano | Nota |
|---|---|---|
| `hecho.participacion_seccion` | elección × sección × sexo × grupo de edad: LN, SV, NV, NS | **La tabla de hechos.** Carga directa desde los CSV del CCPC. ~1.1 M filas por elección. Sin personas. |
| `hecho.participacion_distrito` | vista materializada: elección × distrito (de cualquier cartografía, vía equivalencias) × sexo × grupo | Lo que hoy es `ccpc_AAAA_def24.csv` |
| `hecho.carga` | bitácora de cada archivo cargado: fuente, hash, filas, fecha, quién | Trazabilidad: de qué archivo salió cada número |

### 3.3 `modelo` — el índice, versionado

| Tabla | Qué guarda |
|---|---|
| `modelo.configuracion` | Una fila por versión de `config.json`: pesos, normalización, agregación, cuantiles, umbral de mecanismo, supuestos de escenarios, descripción del cambio |
| `modelo.indicador` | Catálogo de los nueve indicadores: clave, componente, fórmula en texto, orientación, fundamento bibliográfico |
| `modelo.corrida` | Una ejecución: configuración usada, cartografía, elecciones incluidas, elección de referencia (T), fecha, versión de código (commit), estado |
| `modelo.resultado_indicador` | corrida × distrito × indicador: valor crudo y percentil |
| `modelo.resultado_distrito` | corrida × distrito: A, B, C, R, banda, mecanismo, prioridad, rango, escenarios |
| `modelo.validacion` | corrida × prueba (backtest, estrés): métricas (ρ, medias por banda, % sobre mediana) |
| `modelo.sensibilidad` | corrida × variante: % cambia banda, % rojos se mantienen, ρ con base |

Con esto, "¿qué pasaría con pesos iguales?" es insertar una configuración y correr; el tablero compara dos corridas lado a lado.

### 3.4 `decision` — de la alerta a la acción

| Tabla | Qué guarda |
|---|---|
| `decision.catalogo_accion` | Acciones tipificadas por eje ENCCÍVICA y por mecanismo (brigadas de credencialización, diálogos distritales, módulos itinerantes, materiales en lenguas…) |
| `decision.plan_distrital` | corrida × distrito × acción: decisión de la Junta, fecha, responsable, meta (indicador que debe moverse), presupuesto estimado |
| `decision.ejecucion` | plan × evento: qué se hizo, cuándo, alcance (personas, planteles, secciones), evidencia |
| `decision.evaluacion` | plan × elección posterior: cambio observado en el indicador meta vs grupo de comparación (distritos de la misma banda sin esa acción) |

Esta es la parte que convierte un hackathon en política pública: cierra el ciclo identificar → decidir → ejecutar → evaluar, y permite estimar el efecto real de la promoción (hoy el rendimiento de la campaña por banda es un supuesto declarado de +3/+2/+1 puntos; con dos elecciones de registros, deja de serlo).

### 3.5 `senal` — series continuas y tiempo real

Las elecciones federales ocurren cada tres años; entre una y otra hay señales que el INE ya produce y que anticipan el comportamiento. Se modelan como una sola tabla larga:

| Tabla | Grano | Ejemplos de señal |
|---|---|---|
| `senal.serie` | catálogo: clave, descripción, fuente, periodicidad, nivel (sección/municipio/distrito), unidad | `tramites_credencial_18_19`, `asistentes_actividad_enccivica`, `casillas_aprobadas`, `ciudadania_capacitada`, `participacion_horaria_jornada` |
| `senal.observacion` | serie × unidad territorial × fecha/hora × sexo? × grupo? → valor | Una fila por dato; particionada por mes |
| `senal.alerta` | regla sobre una serie (umbral, caída vs mismo periodo anterior, desviación de la tendencia) → evento con severidad, distrito, fecha, estado (abierta, atendida, descartada) | "Trámites de credencial de 18–19 en el distrito 30-18 caen 20 % contra el mismo trimestre de 2023" |

**Qué significa "tiempo real" aquí.** No se observa a personas. Se observan agregados que el INE ya produce con distinta frecuencia: trimestral (credencialización por módulo → sección), mensual (actividades de educación cívica), semanal en proceso electoral (capacitación, casillas, observadores) y **por hora el día de la jornada** (SIJE: instalación de casillas e incidentes; conteo rápido y PREP: participación por casilla conforme llegan actas). Con Supabase Realtime, una tabla `senal.observacion` que recibe actas agregadas por sección permite un mapa de participación que se actualiza durante la jornada y se compara, sección por sección, con la participación esperada a esa hora según 2021 y 2024: la primera alerta operativa de abstención el mismo día. Ese es el horizonte; la fase 2 deja las tablas y el mecanismo listos y carga las series que ya existen como datos abiertos.


### 3.7 `analitica` — crecer en variables y pasar del índice al aprendizaje automático

El índice de la fase 0 usa nueve variables del CCPC. Para que el análisis crezca sin rehacer el sistema, las variables **no son columnas**: son filas de un catálogo (`analitica.variable`) y sus valores viven en un **panel largo** sección × periodo × variable (`analitica.panel_seccion`, con su agregado `panel_distrito`). Agregar marginación (CONAPO), estructura de edad y escolaridad (Censo INEGI por AGEB → sección), conectividad, incidencia delictiva, distancia a módulos o a casillas, es insertar una variable y cargar sus valores; el esquema no cambia y cada variable trae fuente, licencia, unidad y una marca `es_sensible` que impide usarla como insumo si el INE no lo autoriza.

Sobre ese panel se construye la ruta de modelos, registrada en `analitica.modelo_ml` → `entrenamiento` → `prediccion`:

| Etapa | Modelo | Qué aporta | Requisito para pasar a producción |
|---|---|---|---|
| 0 (hoy) | Índice compuesto (nueve variables, pesos declarados) | Transparencia total; validado con backtest | — |
| 1 | Regresión regularizada y árboles (gradient boosting) sobre el panel distrital, objetivo = caída no anticipada en la siguiente intermedia | Aprende los pesos en lugar de declararlos; incorpora covariables externas; importancia de variables comparable con los pesos del índice | Mejorar el Spearman del backtest (0.37) con validación temporal estricta; explicabilidad (SHAP) por distrito |
| 2 | Modelos de panel a nivel **sección** (≈ 68 000 unidades × 6 elecciones × sexo × edad): efectos fijos, luego redes recurrentes o transformers temporales sobre la secuencia de cada sección | Detecta trayectorias de erosión del hábito con mucha más resolución; permite bajar el semáforo a sección | Datos de al menos tres ciclos; prueba fuera de muestra por elección; auditoría de sesgo por tipo de sección y región |
| 3 | Modelos causales sobre `decision.*` (diferencias en diferencias, controles sintéticos) | Estima el efecto real de cada intervención y sustituye el supuesto +3/+2/+1 | Registro completo de planes y ejecución durante al menos un ciclo |

Dos límites que el diseño impone y que conviene decir con todas sus letras. Primero, **"aprendizaje profundo sobre los votantes" significa sobre agregados territoriales de votantes**, nunca sobre personas: el grano mínimo es sección × sexo × grupo de edad, y no existe en el esquema una tabla donde quepa un individuo. Segundo, un modelo que no explique por qué marca un distrito no se aprueba (`entrenamiento.aprobado` exige `importancia` no nula): el objetivo no es predecir la abstención con precisión decimal, es entender **qué motivo pesa en cada territorio** (confianza, comprensión, interés, costo de acceso, que es lo que recoge `analitica.motivo_no_voto` desde la ENCUCI y los estudios del INE) para elegir la acción que convierta a esa población en una más participativa. La precisión se mide, al final, en si la participación subió donde se intervino.

### 3.6 `audit` — quién cambió qué

`audit.bitacora` con disparadores en todas las tablas de `modelo.configuracion`, `decision.*` y `cat.equivalencia_seccion`: usuario, tabla, operación, antes/después, fecha. Es el equivalente a "evidencia de todo" en los PR.

## 4. Flujos

1. **Nueva elección (cada 3 años, batch).** Descargar CCPC → `hecho.carga` → `hecho.participacion_seccion` → refrescar `hecho.participacion_distrito` → nueva `modelo.corrida` con la configuración vigente → validación automática contra la elección recién observada (el backtest deja de ser un ejercicio: cada corrida se califica sola) → publicar.
2. **Nueva cartografía.** Insertar `cat.cartografia`, cargar `cat.seccion`/`cat.distrito`, generar `cat.equivalencia_seccion`; las vistas por distrito se recalculan para el marco nuevo sin tocar los hechos.
3. **Cambio de método.** Nueva fila en `modelo.configuracion` (nunca editar la anterior) → corrida → comparación de bandas entre corridas en el tablero → decisión documentada.
4. **Operación distrital (continuo).** La Junta abre su distrito, ve banda, causa y señales recientes, registra su plan en `decision.plan_distrital`, va registrando ejecución; la dirección ve el avance nacional.
5. **Jornada electoral (horas).** Ingesta de agregados por sección → `senal.observacion` → comparación con esperado → `senal.alerta` → mapa en vivo.

## 5. API y seguridad

* PostgREST expone vistas de sólo lectura (`vista.tablero_distrito`, `vista.tablero_nacional`, `vista.corrida_actual`) para el tablero público; sin llaves con privilegios en el navegador.
* Escritura (planes, ejecuciones, cargas) sólo con sesión y rol: `direccion`, `junta_distrital` (RLS por `distrito_id` asignado), `analista`, `admin`. Misma lógica multi-tenant que en MATI: nada sin filtro de alcance.
* Funciones SQL (`modelo.fn_percentil`, `modelo.fn_bandas`, `modelo.fn_escenario`) replican lo que hoy hace `indice.py`, para que la corrida pueda ejecutarse dentro de la base y quedar auditada; el script de Python se conserva como referencia y prueba cruzada.

## 6. Presentación: una interfaz que guía

El tablero estático ya explica; la plataforma además **conduce**. Patrón propuesto:

* **Entrada por pregunta, no por menú.** Pantalla inicial con cuatro preguntas: "¿Cómo está mi distrito?" (busca y abre la ficha), "¿Dónde concentrar esfuerzos?" (lista de prioridad con filtros), "¿Por qué está cayendo la participación?" (mapa por causa con recorrido explicado), "¿Qué pasaría en 2027?" (escenarios con deslizadores de supuestos).
* **Recorrido guiado** de cinco pasos la primera vez (qué es R, qué es el color, qué es la causa, cómo leer la ficha, qué puedo hacer), con posibilidad de volver a verlo.
* **Leyenda siempre visible y contextual:** cada cambio de "pintar por" trae su título, su frase de lectura y su escala dentro del mapa (ya implementado en v2.1).
* **Ficha con tres niveles:** resumen en lenguaje llano → detalle con números → fórmula y fuente. Nunca una cifra sin su "de dónde sale".
* **Comparar:** dos distritos, o el mismo distrito en dos corridas (antes y después de una intervención).
* **Accesibilidad:** texturas por banda para daltonismo e impresión, contraste AA, navegación por teclado, tabla equivalente a cada gráfico.
* **Stack:** React + Vite + TypeScript + Tailwind (como `mati-app`), MapLibre GL con teselas vectoriales de los distritos (PMTiles servidos como archivo estático), Supabase JS para datos, i18n preparado (es por defecto).

## 7. Hoja de ruta

| Fase | Alcance | Resultado |
|---|---|---|
| **0 (entregado)** | Pipeline reproducible, tablero estático, reporte | v1.0.0 |
| **1 — Base** (iniciada 31-oct-2026) | Supabase con los siete esquemas; carga de catálogos, cartografía 2023, crosswalk, CCPC agregado a distrito 2009–2025, configuración v1.0.0 y corrida de producción; vistas para el tablero. Pendiente: hechos a nivel sección, funciones SQL del índice | `vista.tablero_nacional` devuelve las mismas cifras que v1.0.0 (45/60/89/106; 49.19/50.31) |
| **2 — Web guiada** (3–4 semanas) | Frontend React con entrada por preguntas, recorrido guiado, ficha de tres niveles, comparación de distritos y de corridas | Tablero público en producción |
| **3 — Decisión** (3 semanas) | Esquema `decision`, roles, pantalla de Junta Distrital, catálogo de acciones ENCCÍVICA, bitácora | Las juntas registran planes y ejecución |
| **4 — Señales** (4 semanas) | Esquema `senal`, ingesta de series abiertas (credencialización, actividades), reglas de alerta | Alertas entre elecciones |
| **5 — Jornada** (previo a 2027) | Ingesta de agregados por sección durante la jornada, comparación con esperado por hora, mapa en vivo | Alerta operativa el día de la elección |

### Instancia desplegada

La fase 1 corre en un proyecto Supabase propio del equipo (nombre `alerta-temprana-abstencion`, región East US, PostGIS en el esquema `extensions`), creado el 31 de octubre de 2026 y separado de cualquier otro proyecto de los autores. Se aplicó `db/migrations/0001_esquema_base.sql` sin modificaciones, con RLS habilitado en todas las tablas, y se cargaron las semillas de `db/seed/` en el orden del `db/README.md`. El acceso al panel es por invitación; las credenciales no se versionan. Para reproducirla en otro proyecto: `psql "$SUPABASE_DB_URL" -f db/migrations/0001_esquema_base.sql` y, por cada CSV de `db/seed/`, `\copy esquema.tabla(columnas) from 'archivo.csv' csv header` (la geometría de `cat.distrito` entra como WKT: cargar a una columna temporal y convertir con `ST_Multi(ST_GeomFromText(wkt, 4326))`).

## 8. Lo que no se hace

No se almacenan datos de personas, ni siquiera seudonimizados. No se cruzan con padrones, encuestas con identificador ni redes sociales individuales. No se usa el sistema para inferir preferencias ni para decidir ubicación de casillas fuera de los criterios legales. La plataforma orienta promoción del voto y educación cívica; su métrica de éxito es que suba la participación en los distritos que marcó, no que acierte un pronóstico.
