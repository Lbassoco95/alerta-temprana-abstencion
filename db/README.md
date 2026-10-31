# Base de datos (fase 1)

`migrations/0001_esquema_base.sql` crea los siete esquemas de la plataforma en Postgres 15 + PostGIS (Supabase): `cat`, `hecho`, `modelo`, `decision`, `senal`, `analitica`, `audit` y las vistas de `vista`. La migración se probó sintácticamente en Postgres 16 (37 objetos). El porqué de cada tabla está en `docs/ARQUITECTURA-PLATAFORMA.md`.

Reglas, las mismas que en los productos de Yoltik:

1. **Nunca editar una migración aplicada.** Un cambio es una migración nueva (`0002_…`).
2. **Sin datos personales.** No existe tabla con grano individual; una revisión de código que proponga una se rechaza.
3. **Todo versionado:** cartografías, configuraciones del índice, corridas, modelos. Se inserta; no se sobrescribe.
4. **Vistas para el público, tablas para los roles.** El tablero sólo lee `vista.*`.

## Semillas

`python3 scripts/exporta_seed.py` escribe en `db/seed/` los CSV listos para `\copy` con los datos de la fase 0: catálogos, cartografía 2023 (WKT), configuración v1.0.0, corrida de producción, resultados por distrito e indicador, validación y sensibilidad, y la participación agregada por distrito 2009–2025. La tabla de hechos a nivel sección (`hecho.participacion_seccion`) se carga desde los CSV originales del INE con el mismo criterio de `scripts/agrega_def24.py` (ver `data/raw/README.md`).

Orden de carga: `cat.*` → `hecho.carga` → `hecho.participacion_*` → `modelo.configuracion` → `modelo.indicador` → `modelo.corrida` → `modelo.resultado_*` → `modelo.validacion` → `modelo.sensibilidad`.

## Instancia

La migración `0001` y las semillas están aplicadas en el proyecto Supabase del equipo `alerta-temprana-abstencion` (31-oct-2026, RLS habilitado en todas las tablas; trigger de auditoría de `cat.equivalencia_seccion` desactivado sólo durante la carga inicial). Comprobación de cierre: `select * from vista.tablero_nacional;` debe devolver 45 | 60 | 89 | 106 | 49.19 | 50.31.

## Pendiente para la 0002

Esquema `seguridad` (perfil de usuario, distritos asignados), políticas RLS completas, particiones de `hecho.participacion_seccion` y `senal.observacion`, funciones SQL `modelo.fn_percentil` / `fn_bandas` / `fn_escenario`, y `vista.ficha_distrito` con la serie histórica.
