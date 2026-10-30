"""Escribe en db/seed/ los CSV para poblar el esquema de db/migrations/0001_esquema_base.sql con los datos de la fase 0."""
import json, os, glob, hashlib
import pandas as pd, geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "db/seed"); os.makedirs(SEED, exist_ok=True)
cfg = json.load(open(os.path.join(ROOT, "config.json")))
EST = {1:("Aguascalientes","AGS"),2:("Baja California","BC"),3:("Baja California Sur","BCS"),4:("Campeche","CAMP"),5:("Coahuila","COAH"),6:("Colima","COL"),7:("Chiapas","CHIS"),8:("Chihuahua","CHIH"),9:("Ciudad de México","CDMX"),10:("Durango","DGO"),11:("Guanajuato","GTO"),12:("Guerrero","GRO"),13:("Hidalgo","HGO"),14:("Jalisco","JAL"),15:("México","MEX"),16:("Michoacán","MICH"),17:("Morelos","MOR"),18:("Nayarit","NAY"),19:("Nuevo León","NL"),20:("Oaxaca","OAX"),21:("Puebla","PUE"),22:("Querétaro","QRO"),23:("Quintana Roo","QROO"),24:("San Luis Potosí","SLP"),25:("Sinaloa","SIN"),26:("Sonora","SON"),27:("Tabasco","TAB"),28:("Tamaulipas","TAMPS"),29:("Tlaxcala","TLAX"),30:("Veracruz","VER"),31:("Yucatán","YUC"),32:("Zacatecas","ZAC")}
def w(name, df): df.to_csv(os.path.join(SEED, name + ".csv"), index=False); print(f"{name:32s} {len(df):>7} filas")

# cat
w("cat_entidad", pd.DataFrame([{"entidad_id": k, "nombre": v[0], "abreviatura": v[1]} for k, v in EST.items()]))
w("cat_cartografia", pd.DataFrame([
    {"cartografia_id": 1, "clave": "DERFE-2021", "descripcion": "Marco geográfico 2021 (distritación 2017); campo DEF de los CCPC 2009–2021", "fecha_corte": "2021-01-01", "acuerdo": "INE/CG59/2017", "vigente_desde": "2017-03-15", "vigente_hasta": "2023-01-31"},
    {"cartografia_id": 2, "clave": "DERFE-2023", "descripcion": "Marco geográfico 2023 (distritación 2023); campo DEF de los CCPC 2024 y PJ 2025", "fecha_corte": "2023-05-31", "acuerdo": "INE/CG875/2022", "vigente_desde": "2023-02-01", "vigente_hasta": ""}]))
g = gpd.read_file(os.path.join(ROOT, "data/geo/distritos_federales_2024.geojson"))
g["distrito_id"] = range(1, len(g) + 1); g["cartografia_id"] = 2
w("cat_distrito", pd.DataFrame({"distrito_id": g.distrito_id, "cartografia_id": 2, "entidad_id": g.EDOCVE, "numero": g.DEF, "cabecera": "", "geom": g.geometry.to_wkt()}))
idmap = dict(zip(g.id_def, g.distrito_id))
elec = [(1, 2009, "2009-07-05", "intermedia", 1), (2, 2012, "2012-07-01", "presidencial", 1), (3, 2015, "2015-06-07", "intermedia", 1), (4, 2018, "2018-07-01", "presidencial", 1), (5, 2021, "2021-06-06", "intermedia", 1), (6, 2024, "2024-06-02", "presidencial", 2), (7, 2025, "2025-06-01", "judicial", 2)]
w("cat_eleccion", pd.DataFrame([{"eleccion_id": i, "anio": a, "fecha": f, "tipo": t, "descripcion": f"Elección federal {a}" if t != "judicial" else "Proceso Electoral Extraordinario del Poder Judicial 2024–2025", "cartografia_id": c, "es_federal_ordinaria": t != "judicial"} for i, a, f, t, c in elec]))
w("cat_sexo", pd.DataFrame([{"sexo_id": 0, "nombre": "Hombres"}, {"sexo_id": 1, "nombre": "Mujeres"}, {"sexo_id": 2, "nombre": "No binario"}]))
ge = ["18-19", "20-24", "25-29", "30-39", "40-49", "50-59", "60-69", "70+"]; lim = [(18, 19), (20, 24), (25, 29), (30, 39), (40, 49), (50, 59), (60, 69), (70, 120)]
w("cat_grupo_edad", pd.DataFrame([{"grupo_edad_id": i + 1, "clave": c, "edad_min": a, "edad_max": b, "es_joven": b <= 29} for i, (c, (a, b)) in enumerate(zip(ge, lim))]))
cw = pd.read_csv(os.path.join(ROOT, "data/crosswalk/seccion_a_def2024.csv"))
cw["distrito_destino_id"] = (cw.EDOCVE.map("{:02d}".format) + "-" + cw.DEF2024.map("{:02d}".format)).map(idmap)
w("cat_equivalencia_seccion", pd.DataFrame({"entidad_id": cw.EDOCVE, "seccion_numero": cw.SECCION, "cartografia_origen": 1, "cartografia_destino": 2, "distrito_destino_id": cw.distrito_destino_id, "fuente_asignacion": cw.fuente.replace({"mayoria_dis2018": "mayoria"})}))

# hecho (agregado a distrito; el nivel sección se carga desde los archivos originales)
eid = {a: i for i, a, *_ in elec}; gid = {c: i + 1 for i, c in enumerate(ge)}
rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "data/agregados/ccpc_*_def24.csv"))):
    d = pd.read_csv(f); d["distrito_id"] = (d.EDOCVE.map("{:02d}".format) + "-" + d.DEF2024.map("{:02d}".format)).map(idmap)
    rows.append(pd.DataFrame({"eleccion_id": d.AELEC.map(eid), "distrito_id": d.distrito_id, "sexo_id": d.SEXO, "grupo_edad_id": d.GEDAD.map(gid), "tipo_seccion": d.TIPOSEC, "ln": d.LN, "sv": d.SV, "nv": d.NV, "ns": d.NS}))
w("hecho_participacion_distrito", pd.concat(rows))
w("hecho_carga", pd.DataFrame([{"carga_id": i, "fuente": "INE-DECEyEC CCPC", "archivo": os.path.basename(f), "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest(), "filas": sum(1 for _ in open(f)) - 1, "eleccion_id": eid[int(os.path.basename(f).split("_")[1])], "notas": "agregado a distrito 2023 (ver scripts/agrega_def24.py)"} for i, f in enumerate(sorted(glob.glob(os.path.join(ROOT, "data/agregados/ccpc_*_def24.csv"))), 1)]))

# modelo
w("modelo_configuracion", pd.DataFrame([{"configuracion_id": 1, "version": "1.0.0", "descripcion": "Configuración entregada al Hackathon INE 2026", "normalizacion": cfg["normalizacion"], "agregacion": cfg["agregacion"], "pesos_indicadores": json.dumps(cfg["pesos_indicadores"]), "pesos_componentes": json.dumps(cfg["pesos_componentes"]), "bandas_cuantiles": json.dumps(cfg["bandas_cuantiles"]), "umbral_mecanismo": cfg["umbral_mecanismo"], "escenarios": json.dumps(cfg["escenarios"], ensure_ascii=False)}]))
IND = [("A1", "A", "Desgaste juvenil", "−pendiente de p_J en p_J = a + β·t + γ·P", "Plutzer 2002; Franklin 2004"), ("A2", "A", "Brecha generacional", "(p_A − p_J)_T − (p_A − p_J)_{T−12}", "Cohorte vs adultos"), ("A3", "A", "Retención de cohorte", "mediana(r) − r; r = p_{30–39,T} − p_{J,T−12}", "Ryder 1965"),
       ("B1", "B", "Rebote perdido", "(p_{T−12} − p_{T−15}) − (p_T − p_{T−3})", "Reif y Schmitt 1980"), ("B2", "B", "Caída adulta", "p_{A,T−6} − p_{A,T}", "Easton 1975; Norris 1999"), ("B3", "B", "Volatilidad", "sd(residuos) de p = a + b·t + c·P", "Rosenstone y Hansen 1993"),
       ("C1", "C", "Peso rural y mixto", "LN rural+mixto / LN", "Verba, Schlozman y Brady 1995"), ("C2", "C", "Brecha de género", "|p_M − p_H|", "Desigualdad de participación"), ("C3", "C", "Peso juvenil", "LN 18–29 / LN", "Exposición")]
w("modelo_indicador", pd.DataFrame([{"indicador_id": a, "componente": b, "nombre": c, "formula": d, "orientacion": "mas_es_mas_riesgo", "fundamento": e} for a, b, c, d, e in IND]))
w("modelo_corrida", pd.DataFrame([{"corrida_id": 1, "configuracion_id": 1, "cartografia_id": 2, "eleccion_referencia": 6, "elecciones_incluidas": "{1,2,3,4,5,6}", "proposito": "produccion", "commit_codigo": "v1.0.0", "estado": "completa", "notas": "Corrida entregada al INE"},
                                   {"corrida_id": 2, "configuracion_id": 1, "cartografia_id": 2, "eleccion_referencia": 4, "elecciones_incluidas": "{1,2,3,4}", "proposito": "backtest", "commit_codigo": "v1.0.0", "estado": "completa", "notas": "Backtest con información hasta 2018"}]))
r = pd.read_csv(os.path.join(ROOT, "outputs/indice_distrital.csv"), index_col=0); esc = pd.read_csv(os.path.join(ROOT, "outputs/escenarios.csv"), index_col=0)
r["distrito_id"] = r.index.map(idmap)
w("modelo_resultado_distrito", pd.DataFrame({"corrida_id": 1, "distrito_id": r.distrito_id, "a_habito": r.A_habito.round(2), "b_desafeccion": r.B_desafeccion.round(2), "c_vulnerabilidad": r.C_vulnerabilidad.round(2), "r": r.R.round(2), "banda": r.banda, "mecanismo": r.mecanismo, "prioridad": r.prioridad.round(4), "rango_prioridad": r.rango_prioridad, "ln_referencia": r.LN_2024, "esc_sin_intervencion": esc.p_2027_sin_intervencion.reindex(r.index).values, "esc_con_intervencion": esc.p_2027_con_intervencion.reindex(r.index).values}))
ri = []
for k, *_ in IND:
    col = [c for c in r.columns if c.startswith(k + "_") and not c.startswith("pct_")][0]
    ri.append(pd.DataFrame({"corrida_id": 1, "distrito_id": r.distrito_id, "indicador_id": k, "valor_crudo": r[col].round(4), "percentil": r["pct_" + col].round(2)}))
w("modelo_resultado_indicador", pd.concat(ri))
val = json.load(open(os.path.join(ROOT, "outputs/validacion.json")))
w("modelo_validacion", pd.DataFrame([{"corrida_id": 1, "prueba": "holdout_2025", "eleccion_objetivo": 7, "metricas": json.dumps(val["holdout_2025"], ensure_ascii=False)}, {"corrida_id": 2, "prueba": "backtest_2018_2021", "eleccion_objetivo": 5, "metricas": json.dumps(val["backtest_2018_a_2021"], ensure_ascii=False)}]))
s = pd.read_csv(os.path.join(ROOT, "outputs/sensibilidad.csv")); s.insert(0, "corrida_id", 1); w("modelo_sensibilidad", s)
