"""Une el índice con la cartografía y produce los entregables de datos: CSV agregado, GeoJSON con semáforo
y el archivo JSON que alimenta el tablero."""
import json, os
import pandas as pd, geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs"); ENT = os.path.join(ROOT, "entregables"); os.makedirs(ENT, exist_ok=True)
EST = {1:"Aguascalientes",2:"Baja California",3:"Baja California Sur",4:"Campeche",5:"Coahuila",6:"Colima",7:"Chiapas",
       8:"Chihuahua",9:"Ciudad de México",10:"Durango",11:"Guanajuato",12:"Guerrero",13:"Hidalgo",14:"Jalisco",15:"México",
       16:"Michoacán",17:"Morelos",18:"Nayarit",19:"Nuevo León",20:"Oaxaca",21:"Puebla",22:"Querétaro",23:"Quintana Roo",
       24:"San Luis Potosí",25:"Sinaloa",26:"Sonora",27:"Tabasco",28:"Tamaulipas",29:"Tlaxcala",30:"Veracruz",31:"Yucatán",32:"Zacatecas"}

r = pd.read_csv(os.path.join(OUT, "indice_distrital.csv"), index_col=0)
esc = pd.read_csv(os.path.join(OUT, "escenarios.csv"), index_col=0)
r["entidad"] = r.EDOCVE.map(EST)
MUN = json.load(open(os.path.join(ROOT, "data/geo/municipios_por_distrito.json")))
r["municipio_principal"] = r.index.map(lambda k: MUN.get(k, {}).get("mun_principal", ""))
r["n_municipios"] = r.index.map(lambda k: MUN.get(k, {}).get("n_municipios", 0))
r["municipios"] = r.index.map(lambda k: MUN.get(k, {}).get("municipios", ""))
r["p_2027_sin_intervencion"] = esc.p_2027_sin_intervencion; r["p_2027_con_intervencion"] = esc.p_2027_con_intervencion

# ---- CSV agregado (entregable) ----
cols = ["entidad", "EDOCVE", "DEF", "municipio_principal", "n_municipios", "municipios", "LN_2024", "banda", "R", "A_habito", "B_desafeccion", "C_vulnerabilidad", "mecanismo",
        "prioridad", "rango_prioridad",
        "A1_desgaste_juvenil", "A2_brecha_generacional", "A3_retencion_cohorte", "B1_rebote_perdido", "B2_caida_adulta",
        "B3_volatilidad", "C1_rural_mixto", "C2_brecha_genero", "C3_peso_juvenil",
        "p_total_2012", "p_total_2018", "p_total_2021", "p_total_2024", "p_J_2012", "p_J_2018", "p_J_2024",
        "p_A_2024", "p_M_2024", "p_H_2024", "p_total_2025", "sorpresa_2025",
        "p_2027_sin_intervencion", "p_2027_con_intervencion"]
csv = r[cols].copy(); csv.index.name = "id_distrito"
csv.round(2).to_csv(os.path.join(ENT, "indice_riesgo_abstencion_distrital.csv"), encoding="utf-8-sig")

# ---- GeoJSON ----
g = gpd.read_file(os.path.join(ROOT, "data/geo/distritos_federales_2024.geojson"))
keep = ["entidad", "municipio_principal", "n_municipios", "LN_2024", "banda", "R", "A_habito", "B_desafeccion", "C_vulnerabilidad", "mecanismo", "prioridad",
        "rango_prioridad", "p_total_2021", "p_total_2024", "p_J_2024", "p_A_2024", "p_M_2024", "p_H_2024",
        "p_2027_sin_intervencion", "p_2027_con_intervencion"]
gj = g.merge(r[keep].round(2), left_on="id_def", right_index=True, how="left")
gj.to_file(os.path.join(ENT, "semaforo_riesgo_abstencion_distrital.geojson"), driver="GeoJSON")

# ---- Datos para el tablero (geometría proyectada + atributos) ----
feats = json.load(open(os.path.join(ENT, "semaforo_riesgo_abstencion_distrital.geojson")))["features"]
json.dump({"features": feats,
           "validacion": json.load(open(os.path.join(OUT, "validacion.json"))),
           "sensibilidad": pd.read_csv(os.path.join(OUT, "sensibilidad.csv")).to_dict(orient="records"),
           "nacional": json.load(open(os.path.join(OUT, "escenarios_nacional.json"))),
           "config": json.load(open(os.path.join(ROOT, "config.json")))},
          open(os.path.join(OUT, "tablero_data.json"), "w"), ensure_ascii=False)
print("CSV:", csv.shape, "| GeoJSON:", len(gj), "distritos,", round(os.path.getsize(os.path.join(ENT, "semaforo_riesgo_abstencion_distrital.geojson"))/1e6, 2), "MB")
print(r.groupby("entidad").banda.value_counts().unstack().fillna(0).astype(int).sort_values("rojo", ascending=False).head(12))
