-- =====================================================================================================
-- Alerta temprana de abstención — esquema base (fase 1)
-- Postgres 15 + PostGIS (Supabase). Migración 0001. Nunca editar una migración aplicada: crear la 0002.
-- Principios: la base es la fuente de verdad; todo versionado; sin datos personales (el grano mínimo es
-- sección × sexo × grupo de edad); trazabilidad de cada número a su archivo de origen.
-- =====================================================================================================
create extension if not exists postgis;
create extension if not exists pgcrypto;

create schema if not exists cat;      -- catálogos y cartografía
create schema if not exists hecho;    -- observaciones
create schema if not exists modelo;   -- configuraciones, corridas y resultados del índice
create schema if not exists decision; -- planes, ejecución y evaluación de intervenciones
create schema if not exists senal;    -- series continuas y alertas
create schema if not exists audit;    -- bitácora
create schema if not exists vista;    -- vistas para la presentación (sólo lectura)

-- -----------------------------------------------------------------------------------------------------
-- cat
-- -----------------------------------------------------------------------------------------------------
create table cat.entidad (
  entidad_id   smallint primary key check (entidad_id between 1 and 32),
  nombre       text not null,
  abreviatura  text not null
);
comment on table cat.entidad is 'Entidades federativas con clave INE.';

create table cat.cartografia (
  cartografia_id   smallserial primary key,
  clave            text not null unique,              -- 'DERFE-2021', 'DERFE-2023'
  descripcion      text not null,
  fecha_corte      date not null,
  acuerdo          text,                              -- acuerdo del Consejo General que la aprueba
  vigente_desde    date,
  vigente_hasta    date
);
comment on table cat.cartografia is 'Versiones del marco geográfico electoral. Todo dato territorial referencia una.';

create table cat.distrito (
  distrito_id      serial primary key,
  cartografia_id   smallint not null references cat.cartografia,
  entidad_id       smallint not null references cat.entidad,
  numero           smallint not null,
  cabecera         text,
  geom             geometry(MultiPolygon, 4326),
  unique (cartografia_id, entidad_id, numero)
);
create index on cat.distrito using gist (geom);
comment on table cat.distrito is 'Distrito electoral federal por versión de cartografía, con geometría.';

create table cat.municipio (
  municipio_id   serial primary key,
  entidad_id     smallint not null references cat.entidad,
  clave_ine      smallint not null,
  nombre         text not null,
  unique (entidad_id, clave_ine)
);

create table cat.seccion (
  seccion_id        serial primary key,
  cartografia_id    smallint not null references cat.cartografia,
  entidad_id        smallint not null references cat.entidad,
  numero            integer  not null,
  municipio_id      integer  references cat.municipio,
  distrito_id       integer  references cat.distrito,          -- distrito federal en esa cartografía
  distrito_local    smallint,
  tipo              char(1)  check (tipo in ('U','M','R')),    -- urbana, mixta, rural
  geom              geometry(MultiPolygon, 4326),
  unique (cartografia_id, entidad_id, numero)
);
create index on cat.seccion (entidad_id, numero);
comment on table cat.seccion is 'Sección electoral por cartografía. Es la llave mínima entre marcos y la unidad mínima de todo dato.';

create table cat.equivalencia_seccion (
  equivalencia_id      serial primary key,
  entidad_id           smallint not null references cat.entidad,
  seccion_numero       integer  not null,
  cartografia_origen   smallint not null references cat.cartografia,
  cartografia_destino  smallint not null references cat.cartografia,
  distrito_destino_id  integer  not null references cat.distrito,
  fuente_asignacion    text not null check (fuente_asignacion in ('directo','hijas','mayoria','manual')),
  observacion          text,
  unique (entidad_id, seccion_numero, cartografia_origen, cartografia_destino)
);
comment on table cat.equivalencia_seccion is 'Crosswalk sección (marco origen) → distrito (marco destino). Reproduce data/crosswalk/seccion_a_def2024.csv con su fuente.';

create table cat.eleccion (
  eleccion_id      smallserial primary key,
  anio             smallint not null,
  fecha            date not null,
  tipo             text not null check (tipo in ('presidencial','intermedia','judicial','local','extraordinaria')),
  descripcion      text not null,
  cartografia_id   smallint not null references cat.cartografia,   -- marco en que vienen sus datos
  es_federal_ordinaria boolean not null default true,
  unique (anio, tipo)
);

create table cat.sexo (
  sexo_id  smallint primary key,  -- 0 hombres, 1 mujeres, 2 no binario (2024+)
  nombre   text not null
);
create table cat.grupo_edad (
  grupo_edad_id  smallserial primary key,
  clave          text not null unique,   -- '18-19','20-24','25-29','30-39','40-49','50-59','60-69','70+'
  edad_min       smallint not null,
  edad_max       smallint not null,
  es_joven       boolean not null default false  -- 18–29
);

-- -----------------------------------------------------------------------------------------------------
-- hecho
-- -----------------------------------------------------------------------------------------------------
create table hecho.carga (
  carga_id       bigserial primary key,
  fuente         text not null,                 -- 'INE-DECEyEC CCPC'
  archivo        text not null,
  sha256         text not null,
  filas          bigint,
  eleccion_id    smallint references cat.eleccion,
  cargado_por    uuid,                          -- auth.users.id en Supabase
  cargado_en     timestamptz not null default now(),
  notas          text
);
comment on table hecho.carga is 'Bitácora de archivos cargados: cada número es rastreable a su archivo.';

create table hecho.participacion_seccion (
  eleccion_id     smallint not null references cat.eleccion,
  entidad_id      smallint not null references cat.entidad,
  seccion_numero  integer  not null,
  sexo_id         smallint not null references cat.sexo,
  grupo_edad_id   smallint not null references cat.grupo_edad,
  tipo_seccion    char(1),
  ln   integer not null check (ln >= 0),
  sv   integer not null check (sv >= 0),
  nv   integer not null check (nv >= 0),
  ns   integer not null check (ns >= 0),
  carga_id        bigint references hecho.carga,
  primary key (eleccion_id, entidad_id, seccion_numero, sexo_id, grupo_edad_id)
) partition by list (eleccion_id);
comment on table hecho.participacion_seccion is 'Tabla de hechos del CCPC. Grano: elección × sección × sexo × grupo de edad. Sin personas.';
-- Particiones: una por elección, p. ej.
-- create table hecho.participacion_seccion_2024 partition of hecho.participacion_seccion for values in (6);

-- Participación agregada a distrito (cartografía destino). Se llena por job desde participacion_seccion + equivalencias,
-- o desde los agregados de data/agregados/ (semilla de la fase 0). Es la tabla que lee el modelo.
create table hecho.participacion_distrito (
  eleccion_id    smallint not null references cat.eleccion,
  distrito_id    integer  not null references cat.distrito,
  sexo_id        smallint not null references cat.sexo,
  grupo_edad_id  smallint not null references cat.grupo_edad,
  tipo_seccion   char(1)  not null check (tipo_seccion in ('U','M','R')),
  ln integer not null, sv integer not null, nv integer not null, ns integer not null,
  carga_id       bigint references hecho.carga,
  primary key (eleccion_id, distrito_id, sexo_id, grupo_edad_id, tipo_seccion)
);
create index on hecho.participacion_distrito (eleccion_id, distrito_id);

-- Misma agregación calculada desde el nivel sección vía equivalencias (para verificar la tabla anterior o regenerarla)
create materialized view hecho.participacion_distrito_desde_seccion as
select
  p.eleccion_id,
  coalesce(eq.distrito_destino_id, s.distrito_id)       as distrito_id,
  p.sexo_id, p.grupo_edad_id, p.tipo_seccion,
  sum(p.ln) ln, sum(p.sv) sv, sum(p.nv) nv, sum(p.ns) ns
from hecho.participacion_seccion p
join cat.eleccion e on e.eleccion_id = p.eleccion_id
left join cat.seccion s
  on s.cartografia_id = e.cartografia_id and s.entidad_id = p.entidad_id and s.numero = p.seccion_numero
left join cat.equivalencia_seccion eq
  on eq.entidad_id = p.entidad_id and eq.seccion_numero = p.seccion_numero
 and eq.cartografia_origen = e.cartografia_id
 and eq.cartografia_destino = (select cartografia_id from cat.cartografia where vigente_hasta is null order by fecha_corte desc limit 1)
group by 1,2,3,4,5;

-- -----------------------------------------------------------------------------------------------------
-- modelo
-- -----------------------------------------------------------------------------------------------------
create table modelo.configuracion (
  configuracion_id   serial primary key,
  version            text not null unique,        -- '1.0.0'
  descripcion        text not null,
  normalizacion      text not null check (normalizacion in ('percentil','minmax','zscore')),
  agregacion         text not null check (agregacion in ('lineal','geometrica')),
  pesos_indicadores  jsonb not null,              -- {"A1":0.30,...}
  pesos_componentes  jsonb not null,              -- {"A":0.40,"B":0.40,"C":0.20}
  bandas_cuantiles   jsonb not null,              -- {"rojo":0.15,...}
  umbral_mecanismo   numeric(4,2) not null,
  escenarios         jsonb not null,              -- {"puntos_campana_por_banda":{...}}
  creada_por         uuid,
  creada_en          timestamptz not null default now()
);
comment on table modelo.configuracion is 'Cada versión de config.json. Nunca se edita: se inserta una nueva.';

create table modelo.indicador (
  indicador_id   text primary key,                -- 'A1','A2',...,'C3'
  componente     char(1) not null check (componente in ('A','B','C')),
  nombre         text not null,
  formula        text not null,
  orientacion    text not null default 'mas_es_mas_riesgo',
  fundamento     text
);

create table modelo.corrida (
  corrida_id            serial primary key,
  configuracion_id      integer not null references modelo.configuracion,
  cartografia_id        smallint not null references cat.cartografia,
  eleccion_referencia   smallint not null references cat.eleccion,      -- T (última presidencial usada)
  elecciones_incluidas  smallint[] not null,
  proposito             text not null check (proposito in ('produccion','backtest','sensibilidad','exploracion')),
  commit_codigo         text,
  ejecutada_por         uuid,
  ejecutada_en          timestamptz not null default now(),
  estado                text not null default 'completa' check (estado in ('en_proceso','completa','descartada')),
  notas                 text
);

create table modelo.resultado_indicador (
  corrida_id     integer not null references modelo.corrida on delete cascade,
  distrito_id    integer not null references cat.distrito,
  indicador_id   text    not null references modelo.indicador,
  valor_crudo    numeric(12,4),
  percentil      numeric(6,2),
  primary key (corrida_id, distrito_id, indicador_id)
);

create table modelo.resultado_distrito (
  corrida_id        integer not null references modelo.corrida on delete cascade,
  distrito_id       integer not null references cat.distrito,
  a_habito          numeric(6,2), b_desafeccion numeric(6,2), c_vulnerabilidad numeric(6,2),
  r                 numeric(6,2) not null,
  banda             text not null check (banda in ('rojo','naranja','amarillo','verde')),
  mecanismo         text not null check (mecanismo in ('habito','desafeccion','vulnerabilidad','mixto')),
  prioridad         numeric(8,4),
  rango_prioridad   smallint,
  ln_referencia     integer,
  esc_sin_intervencion numeric(5,2),
  esc_con_intervencion numeric(5,2),
  primary key (corrida_id, distrito_id)
);
create index on modelo.resultado_distrito (corrida_id, banda);

create table modelo.validacion (
  validacion_id   serial primary key,
  corrida_id      integer not null references modelo.corrida on delete cascade,
  prueba          text not null,                 -- 'backtest_2018_2021', 'holdout_2025'
  eleccion_objetivo smallint references cat.eleccion,
  metricas        jsonb not null                 -- spearman, medias por banda, % sobre mediana, n
);

create table modelo.sensibilidad (
  corrida_id              integer not null references modelo.corrida on delete cascade,
  variante                text not null,
  pct_cambia_banda        numeric(5,1),
  pct_rojos_se_mantienen  numeric(5,1),
  spearman_con_base       numeric(5,3),
  primary key (corrida_id, variante)
);

-- -----------------------------------------------------------------------------------------------------
-- decision
-- -----------------------------------------------------------------------------------------------------
create table decision.catalogo_accion (
  accion_id      serial primary key,
  clave          text not null unique,
  nombre         text not null,
  descripcion    text,
  eje_enccivica  text check (eje_enccivica in ('verdad','dialogo','exigencia')),
  mecanismo      text check (mecanismo in ('habito','desafeccion','vulnerabilidad','mixto')),
  indicador_meta text references modelo.indicador,
  unidad_alcance text                             -- 'personas','planteles','secciones','eventos'
);

create table decision.plan_distrital (
  plan_id        serial primary key,
  corrida_id     integer not null references modelo.corrida,
  distrito_id    integer not null references cat.distrito,
  accion_id      integer not null references decision.catalogo_accion,
  decidido_por   uuid,
  decidido_en    timestamptz not null default now(),
  fecha_inicio   date, fecha_fin date,
  meta_alcance   numeric(12,2),
  meta_indicador numeric(8,2),                    -- p. ej. llevar p_J de 41 a 45
  presupuesto    numeric(14,2),
  estado         text not null default 'planeado' check (estado in ('planeado','en_curso','concluido','cancelado')),
  notas          text
);
create index on decision.plan_distrital (distrito_id, estado);

create table decision.ejecucion (
  ejecucion_id   serial primary key,
  plan_id        integer not null references decision.plan_distrital on delete cascade,
  fecha          date not null,
  alcance        numeric(12,2),
  secciones      integer[],                       -- números de sección cubiertos (no personas)
  evidencia_url  text,
  registrado_por uuid,
  registrado_en  timestamptz not null default now(),
  notas          text
);

create table decision.evaluacion (
  evaluacion_id       serial primary key,
  plan_id             integer not null references decision.plan_distrital on delete cascade,
  eleccion_id         smallint not null references cat.eleccion,
  indicador_id        text references modelo.indicador,
  valor_antes         numeric(8,2), valor_despues numeric(8,2),
  valor_comparacion   numeric(8,2),              -- media de distritos de la misma banda sin la acción
  efecto_estimado     numeric(8,2),
  metodo              text,
  evaluado_en         timestamptz not null default now()
);

-- -----------------------------------------------------------------------------------------------------
-- senal
-- -----------------------------------------------------------------------------------------------------
create table senal.serie (
  serie_id       serial primary key,
  clave          text not null unique,            -- 'tramites_credencial_18_19'
  nombre         text not null,
  fuente         text not null,
  periodicidad   text not null check (periodicidad in ('horaria','diaria','semanal','mensual','trimestral','por_eleccion')),
  nivel          text not null check (nivel in ('seccion','municipio','distrito','entidad','nacional')),
  unidad         text not null,
  descripcion    text
);

create table senal.observacion (
  serie_id       integer not null references senal.serie,
  nivel_id       integer not null,                -- seccion_id / municipio_id / distrito_id / entidad_id según serie.nivel
  ts             timestamptz not null,
  sexo_id        smallint references cat.sexo,
  grupo_edad_id  smallint references cat.grupo_edad,
  valor          numeric(16,4) not null,
  carga_id       bigint references hecho.carga,
  primary key (serie_id, nivel_id, ts, sexo_id, grupo_edad_id)
) partition by range (ts);
comment on table senal.observacion is 'Serie larga de señales agregadas. Particionar por mes. Nunca contiene personas.';

create table senal.regla_alerta (
  regla_id       serial primary key,
  serie_id       integer not null references senal.serie,
  nombre         text not null,
  tipo           text not null check (tipo in ('umbral','variacion_interanual','desviacion_tendencia','comparacion_esperado')),
  parametros     jsonb not null,
  severidad      text not null check (severidad in ('baja','media','alta')),
  activa         boolean not null default true
);

create table senal.alerta (
  alerta_id      bigserial primary key,
  regla_id       integer not null references senal.regla_alerta,
  distrito_id    integer references cat.distrito,
  nivel_id       integer,
  ts             timestamptz not null,
  valor          numeric(16,4),
  esperado       numeric(16,4),
  severidad      text not null,
  estado         text not null default 'abierta' check (estado in ('abierta','atendida','descartada')),
  atendida_por   uuid, atendida_en timestamptz, notas text
);
create index on senal.alerta (estado, severidad, ts desc);


-- -----------------------------------------------------------------------------------------------------
-- analitica: panel seccional, covariables externas, motivos de no voto y registro de modelos (ML)
-- Diseñado para crecer en variables sin cambiar el esquema: las variables se registran en un catálogo y
-- los valores viven en una tabla larga. El grano sigue siendo territorial (sección o distrito): no personas.
-- -----------------------------------------------------------------------------------------------------
create schema if not exists analitica;

create table analitica.variable (
  variable_id    serial primary key,
  clave          text not null unique,          -- 'p_total','p_j','ln_rural_share','marginacion_conapo','pob_18_29_inegi'
  nombre         text not null,
  dominio        text not null check (dominio in ('participacion','demografia','socioeconomico','territorio','institucional','seguridad','conectividad','opinion','derivada')),
  nivel_origen   text not null check (nivel_origen in ('seccion','ageb','municipio','distrito','entidad','nacional')),
  fuente         text not null,                  -- 'INE CCPC','INEGI Censo 2020','CONAPO IM 2020','ENCUCI 2020'
  unidad         text not null,
  periodicidad   text,
  descripcion    text,
  licencia       text,
  es_sensible    boolean not null default false  -- bloquea su uso como insumo de modelos si true (p. ej. etnicidad sin consentimiento del INE)
);
comment on table analitica.variable is 'Catálogo abierto de variables. Agregar una variable = una fila aquí + sus valores en panel; el esquema no cambia.';

create table analitica.panel_seccion (
  variable_id    integer not null references analitica.variable,
  entidad_id     smallint not null references cat.entidad,
  seccion_numero integer  not null,
  cartografia_id smallint not null references cat.cartografia,
  periodo        date not null,                  -- fecha de referencia (jornada electoral, censo, corte)
  sexo_id        smallint references cat.sexo,
  grupo_edad_id  smallint references cat.grupo_edad,
  valor          numeric(18,6) not null,
  carga_id       bigint references hecho.carga,
  primary key (variable_id, entidad_id, seccion_numero, cartografia_id, periodo, sexo_id, grupo_edad_id)
) partition by list (variable_id);
comment on table analitica.panel_seccion is 'Panel largo sección × periodo × variable. Base para cualquier modelo. Grano territorial, nunca individual.';

create table analitica.panel_distrito (
  variable_id    integer not null references analitica.variable,
  distrito_id    integer not null references cat.distrito,
  periodo        date not null,
  sexo_id        smallint references cat.sexo,
  grupo_edad_id  smallint references cat.grupo_edad,
  valor          numeric(18,6) not null,
  derivada_de    text,                            -- 'suma','media_ponderada_ln','ratio' desde panel_seccion
  primary key (variable_id, distrito_id, periodo, sexo_id, grupo_edad_id)
);

-- Motivos declarados de no participación (encuestas del INE/INEGI): agregados por estrato, nunca microdatos identificables
create table analitica.motivo_no_voto (
  motivo_id      serial primary key,
  fuente         text not null,                   -- 'ENCUCI 2020','Informe País 2020','Estudio muestral 2021'
  periodo        date not null,
  nivel          text not null check (nivel in ('nacional','entidad','region','estrato')),
  nivel_id       integer,
  estrato        jsonb,                            -- {"sexo":1,"grupo_edad":"18-29","tipo_seccion":"R"}
  motivo         text not null,                    -- 'desconfianza en partidos','no sabía qué se elegía','no le interesa','no pudo (trabajo/distancia)'
  categoria      text not null check (categoria in ('confianza','comprension','interes','costo_acceso','otro')),
  porcentaje     numeric(5,2) not null,
  n_muestra      integer,
  carga_id       bigint references hecho.carga
);
comment on table analitica.motivo_no_voto is 'Vincula el índice con los dos déficits (confianza y comprensión) medidos por encuesta, por estrato. Permite ponderar causas por territorio.';

-- Registro de modelos: desde el índice compuesto hasta modelos de aprendizaje automático sobre el panel
create table analitica.modelo_ml (
  modelo_id        serial primary key,
  clave            text not null unique,          -- 'indice_v1','gbm_caida_2021','panel_dl_v0'
  familia          text not null check (familia in ('indice_compuesto','regresion','arboles','red_neuronal','series_tiempo','bayesiano','otro')),
  objetivo         text not null,                 -- 'sorpresa_2021','p_total_2027','p_j_2027'
  nivel            text not null check (nivel in ('seccion','distrito')),
  variables        text[] not null,               -- claves de analitica.variable usadas
  descripcion      text,
  codigo_ref       text,                          -- ruta/commit del código de entrenamiento
  creado_en        timestamptz not null default now()
);

create table analitica.entrenamiento (
  entrenamiento_id  serial primary key,
  modelo_id         integer not null references analitica.modelo_ml,
  elecciones_entrenamiento smallint[] not null,
  eleccion_prueba   smallint references cat.eleccion,
  hiperparametros   jsonb,
  metricas          jsonb not null,               -- {"spearman":0.37,"mae":2.1,"auc_rojo":0.71}
  importancia       jsonb,                        -- importancia de variables / SHAP agregada: la explicabilidad es obligatoria
  artefacto_url     text,
  ejecutado_en      timestamptz not null default now(),
  aprobado          boolean not null default false,
  aprobado_por      uuid
);
comment on table analitica.entrenamiento is 'Cada entrenamiento guarda métricas e importancia de variables. Sin explicabilidad no se aprueba para producción.';

create table analitica.prediccion (
  entrenamiento_id  integer not null references analitica.entrenamiento on delete cascade,
  nivel_id          integer not null,             -- distrito_id o seccion_id según el modelo
  periodo           date not null,
  valor             numeric(10,4) not null,
  intervalo_inf     numeric(10,4), intervalo_sup numeric(10,4),
  contribuciones    jsonb,                        -- aporte de cada variable a esta predicción (explicación local)
  primary key (entrenamiento_id, nivel_id, periodo)
);

-- -----------------------------------------------------------------------------------------------------
-- audit
-- -----------------------------------------------------------------------------------------------------
create table audit.bitacora (
  bitacora_id   bigserial primary key,
  esquema       text not null, tabla text not null, operacion text not null,
  llave         jsonb, antes jsonb, despues jsonb,
  usuario       uuid, ts timestamptz not null default now()
);
create or replace function audit.fn_bitacora() returns trigger language plpgsql as $$
begin
  insert into audit.bitacora(esquema, tabla, operacion, antes, despues, usuario)
  values (tg_table_schema, tg_table_name, tg_op,
          case when tg_op in ('UPDATE','DELETE') then to_jsonb(old) end,
          case when tg_op in ('INSERT','UPDATE') then to_jsonb(new) end,
          nullif(current_setting('request.jwt.claim.sub', true), '')::uuid);
  return coalesce(new, old);
end $$;
create trigger trg_audit_config   after insert or update or delete on modelo.configuracion       for each row execute function audit.fn_bitacora();
create trigger trg_audit_plan     after insert or update or delete on decision.plan_distrital     for each row execute function audit.fn_bitacora();
create trigger trg_audit_ejec     after insert or update or delete on decision.ejecucion          for each row execute function audit.fn_bitacora();
create trigger trg_audit_equiv    after insert or update or delete on cat.equivalencia_seccion    for each row execute function audit.fn_bitacora();

-- -----------------------------------------------------------------------------------------------------
-- vistas para el tablero (sólo lectura, lo único expuesto al público)
-- -----------------------------------------------------------------------------------------------------
create view vista.corrida_actual as
select * from modelo.corrida where proposito = 'produccion' and estado = 'completa' order by ejecutada_en desc limit 1;

create view vista.tablero_distrito as
select d.distrito_id, en.nombre entidad, en.entidad_id, d.numero distrito,
       r.a_habito, r.b_desafeccion, r.c_vulnerabilidad, r.r, r.banda, r.mecanismo, r.prioridad, r.rango_prioridad,
       r.ln_referencia, r.esc_sin_intervencion, r.esc_con_intervencion, d.geom
from modelo.resultado_distrito r
join vista.corrida_actual c on c.corrida_id = r.corrida_id
join cat.distrito d on d.distrito_id = r.distrito_id
join cat.entidad en on en.entidad_id = d.entidad_id;

create view vista.tablero_nacional as
select count(*) filter (where banda='rojo') rojos, count(*) filter (where banda='naranja') naranjas,
       count(*) filter (where banda='amarillo') amarillos, count(*) filter (where banda='verde') verdes,
       round(sum(esc_sin_intervencion*ln_referencia)/sum(ln_referencia),2) p2027_sin,
       round(sum(esc_con_intervencion*ln_referencia)/sum(ln_referencia),2) p2027_con
from vista.tablero_distrito;

-- -----------------------------------------------------------------------------------------------------
-- RLS (Supabase): público lee vistas; escritura por rol. Las políticas detalladas van en 0002.
-- -----------------------------------------------------------------------------------------------------
alter table decision.plan_distrital enable row level security;
alter table decision.ejecucion      enable row level security;
alter table modelo.configuracion    enable row level security;
-- Ejemplo de política por alcance distrital (perfil de usuario con distritos asignados en 0002):
-- create policy junta_lee_su_distrito on decision.plan_distrital for select
--   using (distrito_id = any (select distrito_id from seguridad.usuario_distrito where usuario_id = auth.uid()));
