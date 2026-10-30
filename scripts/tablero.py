"""Genera el tablero web (HTML autocontenido: Leaflet embebido, datos inline, sin dependencias de red;
si hay internet carga un mapa base de CARTO, si no, dibuja sobre fondo neutro con límites estatales)."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "outputs/tablero_data.json")))
LEAF_DIR = os.path.join(ROOT, "vendor/leaflet")
leaf_js = open(os.path.join(LEAF_DIR, "leaflet.js")).read().replace("</script>", "<\\/script>")
leaf_css = open(os.path.join(LEAF_DIR, "leaflet.css")).read()
ent = json.load(open(os.path.join(ROOT, "data/geo/entidades.geojson")))
import subprocess
met_html = subprocess.run(["pandoc", os.path.join(ROOT, "docs/METODOLOGIA.md"), "-f", "markdown", "-t", "html5"], capture_output=True, text=True).stdout
import re
met_html = re.sub(r"<h2([^>]*)>", r"<h3\1>", met_html).replace("</h2>", "</h3>")
met_html = re.sub(r"<h1([^>]*)>", r"<h2\1>", met_html).replace("</h1>", "</h2>")

KEEP = ["id_def", "entidad", "LN_2024", "banda", "R", "A_habito", "B_desafeccion", "C_vulnerabilidad", "mecanismo", "prioridad",
        "rango_prioridad", "p_total_2021", "p_total_2024", "p_J_2024", "p_A_2024", "p_M_2024", "p_H_2024",
        "p_2027_sin_intervencion", "p_2027_con_intervencion"]
feats = [{"type": "Feature", "geometry": f["geometry"], "properties": {k: f["properties"].get(k) for k in KEEP}} for f in D["features"]]
# series extra por distrito para el explicador de escenarios
import pandas as pd
idx = pd.read_csv(os.path.join(ROOT, "outputs/indice_distrital.csv"), index_col=0)
extra = idx[["p_total_2012", "p_total_2018", "p_J_2012", "pct_A1_desgaste_juvenil", "pct_A2_brecha_generacional", "pct_A3_retencion_cohorte",
             "pct_B1_rebote_perdido", "pct_B2_caida_adulta", "pct_B3_volatilidad", "pct_C1_rural_mixto", "pct_C2_brecha_genero", "pct_C3_peso_juvenil"]].round(1)
for f in feats: f["properties"].update(extra.loc[f["properties"]["id_def"]].to_dict())
rows = [f["properties"] for f in feats]
val = D["validacion"]; sens = D["sensibilidad"]; nac = D["nacional"]; cfg = D["config"]
bt = val["backtest_2018_a_2021"]; ho = val["holdout_2025"]
cnt = {b: sum(1 for r in rows if r["banda"] == b) for b in ["rojo", "naranja", "amarillo", "verde"]}
ln = {b: sum(r["LN_2024"] for r in rows if r["banda"] == b) for b in cnt}
cut = {b: round(min(r["R"] for r in rows if r["banda"] == b), 1) for b in ["rojo", "naranja", "amarillo"]}
E = cfg["escenarios"]["elasticidad_puntos"]
LNtot = sum(r["LN_2024"] for r in rows)
sens_rows = "".join(f"<tr><td>{s['variante'].replace('_', ' ')}</td><td>{s['pct_cambia_banda']} %</td><td>{s['pct_rojos_se_mantienen']} %</td><td>{s['spearman_con_base']}</td></tr>" for s in sens)
bb = bt["sorpresa_media_por_banda"]

html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Alerta temprana de abstención · ¿Dónde puede caer la participación en 2027?</title>
<style>{leaf_css}</style>
<style>
:root{{color-scheme:light;--surface:#fcfcfb;--page:#f4f4f1;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--border:rgba(11,11,11,.10);
--verde:#0ca30c;--amarillo:#fab219;--naranja:#ec835a;--rojo:#d03b3b;--accent:#2a78d6;--hab:#6250d6;--des:#2a78d6;--vul:#1baf7a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}
header{{padding:22px 24px 14px;background:var(--surface);border-bottom:1px solid var(--grid)}}h1{{font-size:24px;margin:0 0 4px;letter-spacing:-.2px}}h2{{font-size:17px;margin:0 0 8px}}h3{{font-size:15px;margin:12px 0 4px}}
.sub{{color:var(--ink2);font-size:14px;max-width:900px}}.wrap{{max-width:1340px;margin:0 auto;padding:16px 24px 48px}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 18px}}
.start{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:0 0 14px}}.start .card{{border-top:4px solid var(--accent)}}.start .n{{display:inline-block;width:24px;height:24px;border-radius:50%;background:var(--accent);color:#fff;text-align:center;font-weight:700;line-height:24px;margin-right:6px;font-size:13px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:0 0 14px}}.tile{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 14px;position:relative}}.tile .v{{font-size:30px;font-weight:650;line-height:1.1}}.tile .l{{color:var(--ink2);font-size:13px;margin-top:3px}}.tile a{{font-size:12px;color:var(--accent);text-decoration:none;display:inline-block;margin-top:4px}}
.filters{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 12px}}select,button,input{{font:inherit;padding:7px 10px;border:1px solid var(--grid);border-radius:8px;background:var(--surface);color:var(--ink)}}button{{cursor:pointer}}button.primary{{background:var(--accent);color:#fff;border-color:var(--accent)}}
.chip{{cursor:pointer;display:inline-flex;align-items:center;gap:6px;padding:5px 9px;border:1px solid var(--grid);border-radius:999px;background:var(--surface);font-size:13px}}.chip.off{{opacity:.4}}.sw{{width:12px;height:12px;border-radius:3px;display:inline-block}}
.grid{{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(320px,1fr);gap:14px}}@media(max-width:960px){{.grid{{grid-template-columns:1fr}}}}
#map{{height:600px;border-radius:10px;background:#eef0ee}}.leaflet-container{{font:inherit}}
.lg{{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:13px;margin-top:10px;align-items:center}}.b{{display:inline-flex;align-items:center;gap:6px;font-weight:600}}.b::before{{content:"";width:11px;height:11px;border-radius:50%;background:var(--c);flex:none}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}th,td{{text-align:left;padding:6px 7px;border-bottom:1px solid var(--grid);font-variant-numeric:tabular-nums;vertical-align:top}}th{{color:var(--ink2);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}
.bar{{height:9px;border-radius:5px;background:var(--grid);overflow:hidden;margin:3px 0 8px}}.bar i{{display:block;height:100%}}
.kv{{display:grid;grid-template-columns:1fr auto;gap:3px 12px;font-size:14px}}.kv b{{font-weight:600}}.note{{font-size:13.5px;color:var(--ink2)}}.muted{{color:var(--muted);font-size:13px}}
.scale{{position:relative;height:46px;margin:14px 4px 6px}}.scale .seg{{position:absolute;top:14px;height:14px;border-radius:3px}}.scale .cutl{{position:absolute;top:30px;font-size:11px;color:var(--ink2);transform:translateX(-50%);white-space:nowrap}}.scale .dot{{position:absolute;top:6px;width:30px;height:30px;border-radius:50%;background:#fff;border:3px solid var(--ink);transform:translateX(-50%);box-shadow:0 1px 4px rgba(0,0,0,.25)}}
.steps{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}}.step{{background:#f6f6f3;border-radius:10px;padding:12px 14px;font-size:14px}}.step .big{{font-size:16px;font-weight:650;margin:6px 0}}.step code{{background:#fff;padding:1px 5px;border-radius:4px;font-size:12.5px}}
details{{margin-top:10px}}summary{{cursor:pointer;font-weight:600}}.gl{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;margin-top:8px}}.gl div{{background:#f6f6f3;border-radius:8px;padding:10px 12px;font-size:13.5px}}.gl b{{display:block;margin-bottom:2px}}
.foot{{margin-top:22px;color:var(--ink2);font-size:13px}}.tag{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600;color:#fff}}
.leaflet-tooltip.tt{{font:13px system-ui;padding:6px 9px;border-radius:6px;border:none;box-shadow:0 1px 6px rgba(0,0,0,.2)}}
.section{{margin-top:14px}}.met{{font-size:14px;color:var(--ink)}}.met h2{{display:none}}.met h3{{font-size:15px;margin:16px 0 6px;color:var(--ink)}}.met table{{font-size:13px;margin:8px 0}}.met blockquote{{margin:8px 0;padding:8px 12px;background:#f6f6f3;border-left:3px solid var(--accent);border-radius:4px}}.met ul,.met ol{{padding-left:20px}}.met li{{margin:3px 0}}.met p{{margin:6px 0}}.q{{font-weight:600;color:var(--ink)}}
</style></head><body>
<header><div class="wrap" style="padding:0 0 0">
<h1>¿Dónde puede caer la participación electoral en 2027?</h1>
<div class="sub">Un semáforo para los 300 distritos electorales federales de México. Mide el <b>riesgo de que la gente deje de votar</b> comparando a cada distrito con su propia historia (2009–2024), a partir de los conteos censales de participación del INE. No mide quién gana ni por quién se vota.</div>
</div></header>
<div class="wrap">

<div class="start">
 <div class="card"><h2><span class="n">1</span>Qué es cada color</h2><div class="note">Cada distrito recibe una calificación de riesgo <b>R de 0 a 100</b>. Los 300 se ordenan de mayor a menor riesgo y se pintan: los <b style="color:var(--rojo)">45 más altos en rojo</b>, los <b style="color:#b85a2f">60 siguientes en naranja</b>, los <b style="color:#9a6a00">89 siguientes en amarillo</b> y los <b style="color:var(--verde)">106 restantes en verde</b>. Rojo no quiere decir “aquí vota poca gente”: quiere decir “aquí la participación está cayendo más rápido respecto a lo que este distrito acostumbraba”.</div></div>
 <div class="card"><h2><span class="n">2</span>Por qué está en riesgo</h2><div class="note">Además del color, cada distrito tiene un <b>mecanismo</b>, la causa principal: <span class="tag" style="background:var(--hab)">Hábito</span> los jóvenes no están aprendiendo a votar · <span class="tag" style="background:var(--des)">Desafección</span> gente que antes votaba dejó de hacerlo · <span class="tag" style="background:var(--vul)">Vulnerabilidad</span> el territorio hace más difícil votar (rural, brechas). El color dice qué tan urgente; el mecanismo dice qué hacer.</div></div>
 <div class="card"><h2><span class="n">3</span>Cómo usar el tablero</h2><div class="note">Pasa el cursor sobre el mapa para ver cada distrito y <b>haz clic</b> para abrir su ficha: ahí verás por qué tiene ese color, qué tan cerca está de cambiar y qué pasaría en 2027 con y sin intervención. Usa los filtros para ver una entidad o una sola causa. Más abajo está la lista de prioridad y la explicación de cada número.</div></div>
</div>

<div class="tiles">
 <div class="tile"><div class="v" style="color:var(--rojo)">{cnt['rojo']}</div><div class="l">distritos en rojo · {ln['rojo']/1e6:.1f} millones de personas en lista nominal</div><a href="#colores">¿Cómo se define el rojo?</a></div>
 <div class="tile"><div class="v" style="color:#b85a2f">{cnt['naranja']}</div><div class="l">en naranja · {ln['naranja']/1e6:.1f} millones</div><a href="#colores">¿Cuándo cambia de color?</a></div>
 <div class="tile"><div class="v">{nac['p_2024']} %</div><div class="l">votó en 2024 (de cada 100 personas en la lista nominal)</div><a href="#datos">¿De dónde salen los datos?</a></div>
 <div class="tile"><div class="v">{nac['p_2027_sin_intervencion']:.1f} %</div><div class="l">votaría en 2027 si cada distrito sigue como va</div><a href="#escenarios">¿Cómo se calcula?</a></div>
 <div class="tile"><div class="v" style="color:var(--accent)">{nac['p_2027_con_intervencion']:.1f} %</div><div class="l">votaría en 2027 si el INE concentra la promoción en rojos, naranjas y amarillos</div><a href="#escenarios">¿Por qué sube {round(nac['p_2027_con_intervencion']-nac['p_2027_sin_intervencion'],1)} puntos?</a></div>
</div>

<div class="filters">
 <select id="fEdo"><option value="">Todas las entidades</option></select>
 <select id="fMec"><option value="">Todas las causas</option><option value="habito">Hábito (jóvenes)</option><option value="desafeccion">Desafección (adultos que dejaron de votar)</option><option value="vulnerabilidad">Vulnerabilidad del territorio</option><option value="mixto">Mixto</option></select>
 <select id="fVar"><option value="banda">Pintar por: color de riesgo</option><option value="mecanismo">Pintar por: causa principal</option><option value="p_total_2024">Pintar por: % que votó en 2024</option><option value="p_J_2024">Pintar por: % de jóvenes que votó en 2024</option><option value="dif">Pintar por: puntos que se recuperarían en 2027</option></select>
 <input id="buscar" placeholder="Buscar: entidad o número de distrito" style="min-width:230px">
 <span class="chip" data-b="rojo"><i class="sw" style="background:var(--rojo)"></i>Rojo {cnt['rojo']}</span><span class="chip" data-b="naranja"><i class="sw" style="background:var(--naranja)"></i>Naranja {cnt['naranja']}</span><span class="chip" data-b="amarillo"><i class="sw" style="background:var(--amarillo)"></i>Amarillo {cnt['amarillo']}</span><span class="chip" data-b="verde"><i class="sw" style="background:var(--verde)"></i>Verde {cnt['verde']}</span>
 <button id="reset">Limpiar</button>
</div>

<div class="grid">
 <div class="card"><div id="map" role="img" aria-label="Mapa de los 300 distritos electorales federales coloreados por riesgo"></div>
  <div class="lg" id="legend"></div>
  <p class="note" id="mapnote">Los límites gruesos son estados; los delgados, distritos. Si tienes internet se muestra el mapa base con nombres de ciudades; si no, sólo los polígonos.</p></div>
 <div class="card" id="detail"><h2>Ficha del distrito</h2><p class="muted">Haz clic en un distrito del mapa o en una fila de la tabla para ver su ficha completa: por qué tiene ese color, qué tan cerca está de cambiar y qué pasaría en 2027.</p>
  <p class="note">Mientras tanto, un ejemplo: el distrito con mayor riesgo del país es <a href="#" id="ej" style="color:var(--accent)">Veracruz 18</a>.</p></div>
</div>

<div class="card section" id="colores"><h2>Cómo se decide el color, y cuándo cambia</h2>
 <div class="scale" id="scaleAll"></div>
 <div class="steps" style="margin-top:10px">
  <div class="step"><div class="q">1. Se califica el riesgo</div>Cada distrito recibe <b>R</b>, un número de 0 a 100 que resume nueve señales de alerta en tres causas: hábito (40 %), desafección (40 %) y vulnerabilidad (20 %). Un R de 80 significa que el distrito está peor que la gran mayoría.</div>
  <div class="step"><div class="q">2. Se forma la fila</div>Los 300 distritos se ordenan de mayor a menor R. El color depende del <b>lugar en la fila</b>, no de un umbral fijo: los primeros 45 son rojos, luego 60 naranjas, 89 amarillos y 106 verdes. Con los datos actuales los cortes quedan en <b>R ≥ {cut['rojo']}</b> para rojo, <b>R ≥ {cut['naranja']}</b> para naranja y <b>R ≥ {cut['amarillo']}</b> para amarillo.</div>
  <div class="step"><div class="q">3. Cuándo cambia de color</div>Un distrito cambia de color cuando su R cruza un corte. Eso pasa por dos vías: <b>porque sus propios indicadores cambian</b> (por ejemplo, los jóvenes vuelven a votar y baja su R) o <b>porque los demás distritos se mueven</b> y la fila se reordena. El semáforo se recalcula después de cada elección federal con los nuevos conteos.</div>
  <div class="step"><div class="q">4. Por qué 45 y no otro número</div>Los cortes (15 %, 20 %, 30 %, 35 %) son una decisión operativa: las juntas distritales pueden atender con intensidad a unas decenas de distritos, no a cientos. Son ajustables en el archivo de configuración y el análisis de sensibilidad muestra que la lista roja casi no cambia al moverlos.</div>
 </div>
</div>

<div class="card section" id="escenarios"><h2>¿De dónde sale el {nac['p_2027_con_intervencion']:.1f} %? El cálculo paso a paso</h2>
 <div class="steps">
  <div class="step"><div class="q">Paso 1 · Punto de partida</div>Para cada distrito tomamos lo que votó en la última elección intermedia, <b>2021</b> (la de 2027 también es intermedia: se eligen diputaciones, no presidencia, y siempre vota menos gente).</div>
  <div class="step"><div class="q">Paso 2 · Su impulso reciente</div>Le sumamos cómo cambió el distrito entre las dos últimas presidenciales: <code>2024 − 2018</code>. Si cayó 7 puntos entre presidenciales, suponemos que trae esa misma inercia hacia 2027.<div class="big">sin intervención = p<sub>2021</sub> + (p<sub>2024</sub> − p<sub>2018</sub>)</div></div>
  <div class="step"><div class="q">Paso 3 · Qué pasa si el INE interviene</div>A ese número le sumamos el efecto de una promoción focalizada: <b>+{E['rojo']:.0f} puntos en rojos, +{E['naranja']:.0f} en naranjas, +{E['amarillo']:.0f} en amarillos, 0 en verdes</b>. Es un supuesto declarado, tomado del rango bajo de los experimentos de movilización electoral (Gerber y Green), y se puede cambiar en la configuración.</div>
  <div class="step"><div class="q">Paso 4 · Se suma el país</div>El promedio nacional pondera cada distrito por su lista nominal (un distrito con 380 mil personas pesa más que uno con 290 mil). Así salen <b>{nac['p_2027_sin_intervencion']:.1f} %</b> sin intervención y <b>{nac['p_2027_con_intervencion']:.1f} %</b> con intervención: {round(nac['p_2027_con_intervencion']-nac['p_2027_sin_intervencion'],1)} puntos, unas {round((nac['p_2027_con_intervencion']-nac['p_2027_sin_intervencion'])/100*LNtot/1e6,1)} millones de personas.</div>
 </div>
 <p class="note" style="margin-top:10px">No es un pronóstico de cuánta gente votará: es una forma de comparar “seguir igual” contra “concentrar esfuerzos donde el riesgo es mayor”, con los mismos supuestos para todos los distritos. En la ficha de cada distrito aparece este mismo cálculo con sus números.</p>
</div>

<div class="card section" id="datos"><h2>Las nueve señales, en palabras llanas</h2>
 <p class="note">Cada señal se convierte en un <b>percentil</b>: “92” significa “peor que el 92 % de los distritos” en esa señal. Después se promedian con los pesos indicados.</p>
 <div class="gl">
  <div><b style="color:var(--hab)">Hábito · ¿Los jóvenes están aprendiendo a votar?</b>A1 Desgaste juvenil: ¿la participación de 18 a 29 años viene bajando elección tras elección? (30 %) · A2 Brecha generacional: ¿los jóvenes se están alejando de los adultos más que en 2012? (30 %) · A3 Retención: quienes votaron por primera vez en 2012, ¿siguen votando doce años después? (40 %)</div>
  <div><b style="color:var(--des)">Desafección · ¿La gente que votaba sigue votando?</b>B1 Rebote perdido: en 2024 el distrito “rebotó” menos después de una intermedia que en 2012 (45 %) · B2 Caída adulta: los mayores de 30 votaron menos en 2024 que en 2018 (35 %) · B3 Volatilidad: la participación sube y baja de forma errática, señal de que depende de la movilización del momento (20 %)</div>
  <div><b style="color:var(--vul)">Vulnerabilidad · ¿El territorio hace difícil votar?</b>C1 Qué parte de la lista nominal vive en secciones rurales o mixtas (40 %) · C2 Qué tan distinta es la participación de mujeres y hombres (35 %) · C3 Qué parte de la lista nominal tiene entre 18 y 29 años, la edad en que el hábito se decide (25 %)</div>
 </div>
 <p class="note" style="margin-top:10px"><b>Datos:</b> Conteos Censales de Participación Ciudadana del INE (DECEyEC): para cada sección electoral, sexo y edad, cuántas personas estaban en la lista nominal y cuántas tienen marca de voto en los cuadernillos. Elecciones federales de 2009, 2012, 2015, 2018, 2021 y 2024, y la judicial de 2025 como prueba. Toda la serie se llevó a los 300 distritos de la cartografía 2023. No hay un solo dato personal: la unidad mínima es un grupo de personas por sección, sexo y edad.</p>
</div>

<div class="card section"><h2>Lista de prioridad: a quién atender primero</h2>
 <p class="note">Orden por <b>riesgo × tamaño</b> (R multiplicado por la lista nominal del distrito): entre dos distritos igual de rojos, primero el que tiene más personas. Haz clic en una fila para abrir la ficha. La tabla responde a los filtros de arriba.</p>
 <div style="max-height:440px;overflow:auto"><table id="tabla"><thead><tr><th>#</th><th>Distrito</th><th>Entidad</th><th>Color</th><th>R</th><th>Hábito</th><th>Desafección</th><th>Vulnerab.</th><th>Causa</th><th>Votó 2024</th><th>Jóvenes 2024</th><th>Lista nominal</th></tr></thead><tbody></tbody></table></div></div>

<div class="grid section">
 <div class="card"><h2>¿Y esto funciona? La prueba</h2>
  <p class="note">Hicimos la prueba más honesta posible: calculamos el semáforo <b>como si estuviéramos en 2018</b>, sin ver nada posterior, y revisamos qué pasó en la intermedia de 2021. Los distritos que ese semáforo marcó en rojo cayeron en promedio <b>{bb['rojo']:+.1f} puntos más</b> de lo que su propia historia anticipaba; los naranjas {bb['naranja']:+.1f}; los amarillos {bb['amarillo']:+.1f}; los verdes <b>{bb['verde']:+.1f}</b> (cayeron menos). El {bt['pct_rojos_con_sorpresa_sobre_mediana']} % de los rojos cayó más que la mediana del país, contra el {bt['pct_verdes_con_sorpresa_sobre_mediana']} % de los verdes. Correlación de Spearman: {bt['spearman_R_sorpresa']}.</p>
  <p class="note"><b>Lo que no anticipa.</b> La elección judicial de 2025 (votó 13 %) no se explica con este semáforo (correlación {ho['spearman_R_sorpresa']}). Fue una elección inédita en la que pesó la capacidad de organización para llevar gente a votar, no el desgaste que medimos. Lo decimos abiertamente: el instrumento sirve para elecciones federales ordinarias como la de 2027.</p></div>
 <div class="card"><h2>¿Y si cambiamos los pesos? La robustez</h2>
  <p class="note">Recalculamos todo de diez maneras distintas. La pregunta es cuántos distritos cambian de color y cuántos rojos siguen siendo rojos.</p>
  <table><thead><tr><th>Variante</th><th>Cambian de color</th><th>Rojos que siguen rojos</th><th>Parecido con el original</th></tr></thead><tbody>{sens_rows}</tbody></table>
  <p class="note" style="margin-top:8px">Mover un peso ±0.10 cambia el color de entre 9 y 13 % de los distritos y conserva más del 93 % de los rojos. Las variantes más drásticas mueven la frontera amarillo–verde, pero la lista roja se mantiene en más de 84 %.</p></div>
</div>

<div class="card section" id="metodo"><h2>Fundamentos matemáticos y análisis de sensibilidad</h2>
 <p class="note">Aquí está cada fórmula que produce los números de este tablero, en el orden en que se aplican, y la explicación de cómo se probó que los resultados no dependen de decisiones arbitrarias. Es la misma sección 3, 5 y 6 del reporte y el archivo <code>docs/METODOLOGIA.md</code> del repositorio.</p>
 <details><summary>Abrir la explicación completa (12 apartados)</summary><div class="met">{met_html}</div></details>
</div>

<p class="foot">Equipo: Leopoldo Bassoco Nova · Alan Anastasio (participación a título personal) · Hackathon INE 2026 «Hackea la participación», Eje 2. Datos: INE-DECEyEC, Conteos Censales de Participación Ciudadana 2009–2024 y PEEFPJ 2024–2025. Cartografía: shapefiles del INE sistematizados en el repositorio <i>Recent Mexican electoral geography</i> (E. Magar, ITAM). Mapa base: © OpenStreetMap, © CARTO (sólo con conexión). Sin datos personales.</p>
</div>

<script>{leaf_js}</script>
<script>
const FEATS={json.dumps(feats, ensure_ascii=False)};
const ENT={json.dumps(ent, ensure_ascii=False)};
const CUT={json.dumps(cut)}; const CNT={json.dumps(cnt)}; const BONO={json.dumps(E)}; const NAC={json.dumps(nac)};
const COL={{rojo:'#d03b3b',naranja:'#ec835a',amarillo:'#fab219',verde:'#0ca30c'}};
const MEC={{habito:'#6250d6',desafeccion:'#2a78d6',vulnerabilidad:'#1baf7a',mixto:'#898781'}};
const MECN={{habito:'Hábito (jóvenes)',desafeccion:'Desafección (adultos que dejaron de votar)',vulnerabilidad:'Vulnerabilidad del territorio',mixto:'Mixto'}};
const BN={{rojo:'Rojo',naranja:'Naranja',amarillo:'Amarillo',verde:'Verde'}};
const DATA=FEATS.map(f=>f.properties); const byId=Object.fromEntries(DATA.map(r=>[r.id_def,r]));
const st={{edo:'',mec:'',bands:new Set(['rojo','naranja','amarillo','verde']),sel:null,var:'banda',q:''}};
const fmt=(x,d=1)=>x==null?'–':Number(x).toFixed(d); const fmtN=x=>Number(x).toLocaleString('es-MX'); const dn=r=>`${{r.entidad}} · distrito ${{+r.id_def.slice(3)}}`;
const fE=document.getElementById('fEdo'); [...new Set(DATA.map(r=>r.entidad))].sort().forEach(e=>{{const o=document.createElement('option');o.value=o.textContent=e;fE.appendChild(o)}});
// ---- mapa ----
const map=L.map('map',{{zoomSnap:.5,attributionControl:true}}).setView([23.8,-102.3],5);
map.attributionControl.setPrefix('');
const tiles=L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_nolabels/{{z}}/{{x}}/{{y}}{{r}}.png',{{maxZoom:12,attribution:'© OpenStreetMap, © CARTO'}});
const labels=L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_only_labels/{{z}}/{{x}}/{{y}}{{r}}.png',{{maxZoom:12,pane:'shadowPane'}});
let online=false; tiles.on('tileload',()=>{{if(!online){{online=true;labels.addTo(map);document.getElementById('mapnote').textContent='Los límites gruesos son estados; los delgados, distritos. Acerca el mapa para ver ciudades y carreteras.'}}}}); tiles.addTo(map);
function seqColor(v,min,max){{const t=Math.max(0,Math.min(1,(v-min)/(max-min)));const ramp=['#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95','#0d366b'];return ramp[Math.round(t*(ramp.length-1))]}}
function fill(r){{if(st.var==='banda')return COL[r.banda];if(st.var==='mecanismo')return MEC[r.mecanismo];if(st.var==='dif'){{const g=r.p_2027_con_intervencion-r.p_2027_sin_intervencion;return g>=3?'#1c5cab':g>=2?'#3987e5':g>=1?'#86b6ef':'#dfe8f5'}};return seqColor(r[st.var],st.var==='p_J_2024'?25:40,st.var==='p_J_2024'?70:80)}}
function visible(r){{const q=st.q.trim().toLowerCase();const okq=!q||r.entidad.toLowerCase().includes(q)||dn(r).toLowerCase().includes(q)||String(+r.id_def.slice(3))===q;return (!st.edo||r.entidad===st.edo)&&(!st.mec||r.mecanismo===st.mec)&&st.bands.has(r.banda)&&okq}}
function style(f){{const r=f.properties;const v=visible(r);return {{fillColor:fill(r),fillOpacity:v?0.82:0.12,color:st.sel&&st.sel.id_def===r.id_def?'#0b0b0b':'#ffffff',weight:st.sel&&st.sel.id_def===r.id_def?2.5:0.7,opacity:v?1:0.4}}}}
const gj=L.geoJSON(FEATS,{{style,onEachFeature:(f,l)=>{{const r=f.properties;
 l.bindTooltip(()=>`<b>${{dn(r)}}</b><br><span class="b" style="--c:${{COL[r.banda]}}">${{BN[r.banda]}}</span> · R = ${{fmt(r.R)}}<br>Causa: ${{MECN[r.mecanismo]}}<br>Votó en 2024: ${{fmt(r.p_total_2024)}} % · jóvenes ${{fmt(r.p_J_2024)}} %<br><i>Clic para ver la ficha</i>`,{{sticky:true,className:'tt'}});
 l.on('mouseover',()=>{{if(!(st.sel&&st.sel.id_def===r.id_def))l.setStyle({{weight:2,color:'#0b0b0b'}});l.bringToFront()}});l.on('mouseout',()=>gj.resetStyle(l));l.on('click',()=>select(r,false))}}}}).addTo(map);
L.geoJSON(ENT,{{style:{{fill:false,color:'#52514e',weight:1.6,opacity:.9}},interactive:false}}).addTo(map);
const layers={{}}; gj.eachLayer(l=>layers[l.feature.properties.id_def]=l);
function legend(){{const L_=document.getElementById('legend');if(st.var==='banda')L_.innerHTML=`<span class="b" style="--c:${{COL.rojo}}">Rojo: riesgo más alto (R ≥ ${{CUT.rojo}})</span><span class="b" style="--c:${{COL.naranja}}">Naranja (R ≥ ${{CUT.naranja}})</span><span class="b" style="--c:${{COL.amarillo}}">Amarillo (R ≥ ${{CUT.amarillo}})</span><span class="b" style="--c:${{COL.verde}}">Verde: trayectoria estable</span>`;
 else if(st.var==='mecanismo')L_.innerHTML=Object.keys(MEC).map(m=>`<span class="b" style="--c:${{MEC[m]}}">${{MECN[m]}}</span>`).join('');
 else if(st.var==='dif')L_.innerHTML=[['#1c5cab','+3 puntos (rojos)'],['#3987e5','+2 (naranjas)'],['#86b6ef','+1 (amarillos)'],['#dfe8f5','0 (verdes)']].map(([c,t])=>`<span class="b" style="--c:${{c}}">${{t}}</span>`).join('');
 else L_.innerHTML=`<span>Más claro = menor participación · más oscuro = mayor</span><span class="b" style="--c:#cde2fb">${{st.var==='p_J_2024'?'25':'40'}} %</span><span class="b" style="--c:#3987e5">${{st.var==='p_J_2024'?'48':'60'}} %</span><span class="b" style="--c:#0d366b">${{st.var==='p_J_2024'?'70':'80'}} %</span>`}}
function paint(){{gj.setStyle(style);legend();tabla();if(st.edo){{const b=L.featureGroup(DATA.filter(r=>r.entidad===st.edo).map(r=>layers[r.id_def])).getBounds();map.fitBounds(b,{{padding:[20,20]}})}}}}
const tb=document.querySelector('#tabla tbody');
function tabla(){{const rows=DATA.filter(visible).sort((a,b)=>a.rango_prioridad-b.rango_prioridad).slice(0,80);tb.innerHTML=rows.map(r=>`<tr data-id="${{r.id_def}}" style="cursor:pointer"><td>${{r.rango_prioridad}}</td><td>${{+r.id_def.slice(3)}}</td><td>${{r.entidad}}</td><td><span class="b" style="--c:${{COL[r.banda]}}">${{BN[r.banda]}}</span></td><td>${{fmt(r.R)}}</td><td>${{fmt(r.A_habito,0)}}</td><td>${{fmt(r.B_desafeccion,0)}}</td><td>${{fmt(r.C_vulnerabilidad,0)}}</td><td>${{MECN[r.mecanismo].split(' (')[0]}}</td><td>${{fmt(r.p_total_2024)}} %</td><td>${{fmt(r.p_J_2024)}} %</td><td>${{fmtN(r.LN_2024)}}</td></tr>`).join('')||'<tr><td colspan="12" class="muted">Ningún distrito cumple los filtros.</td></tr>';
 tb.querySelectorAll('tr[data-id]').forEach(tr=>tr.addEventListener('click',()=>select(byId[tr.dataset.id],true)))}}
function scaleHTML(r){{const segs=[['verde',0,CUT.amarillo],['amarillo',CUT.amarillo,CUT.naranja],['naranja',CUT.naranja,CUT.rojo],['rojo',CUT.rojo,100]];
 let h=segs.map(([b,a,z])=>`<div class="seg" style="left:${{a}}%;width:${{z-a}}%;background:${{COL[b]}}"></div>`).join('');
 h+=Object.entries(CUT).map(([b,v])=>`<div class="cutl" style="left:${{v}}%">${{v}}</div>`).join('');
 h+=`<div class="cutl" style="left:0">0</div><div class="cutl" style="left:100%">100</div>`;
 if(r)h+=`<div class="dot" style="left:${{r.R}}%" title="R = ${{fmt(r.R)}}"></div>`;return h}}
document.getElementById('scaleAll').innerHTML=scaleHTML(null)+`<div class="cutl" style="left:7%;top:-6px;color:#0b0b0b">verde · ${{CNT.verde}}</div><div class="cutl" style="left:${{(CUT.amarillo+CUT.naranja)/2}}%;top:-6px;color:#0b0b0b">amarillo · ${{CNT.amarillo}}</div><div class="cutl" style="left:${{(CUT.naranja+CUT.rojo)/2}}%;top:-6px;color:#0b0b0b">naranja · ${{CNT.naranja}}</div><div class="cutl" style="left:${{(CUT.rojo+100)/2}}%;top:-6px;color:#0b0b0b">rojo · ${{CNT.rojo}}</div>`;
function cerca(r){{const b=r.banda;const up={{verde:['amarillo',CUT.amarillo],amarillo:['naranja',CUT.naranja],naranja:['rojo',CUT.rojo]}}[b];const down={{rojo:['naranja',CUT.rojo],naranja:['amarillo',CUT.naranja],amarillo:['verde',CUT.amarillo]}}[b];let s=[];
 if(up)s.push(`le faltan <b>${{fmt(up[1]-r.R)}} puntos</b> de R para pasar a ${{up[0]}}`);if(down)s.push(`si su R bajara <b>${{fmt(r.R-down[1]+0.05)}} puntos</b> pasaría a ${{down[0]}}`);return s.join('; ')}}
function pct(v){{return v>=50?`peor que el ${{fmt(v,0)}} % de los distritos`:`mejor que el ${{fmt(100-v,0)}} % de los distritos`}}
function mayor(r){{const m=[['A1 desgaste juvenil',r.pct_A1_desgaste_juvenil,'la participación de 18–29 viene cayendo'],['A2 brecha generacional',r.pct_A2_brecha_generacional,'los jóvenes se alejaron de los adultos desde 2012'],['A3 retención de cohorte',r.pct_A3_retencion_cohorte,'quienes debutaron en 2012 no siguieron votando'],['B1 rebote perdido',r.pct_B1_rebote_perdido,'en 2024 rebotó menos que en 2012'],['B2 caída adulta',r.pct_B2_caida_adulta,'los mayores de 30 votaron menos en 2024 que en 2018'],['B3 volatilidad',r.pct_B3_volatilidad,'su participación es errática'],['C1 rural y mixto',r.pct_C1_rural_mixto,'gran parte vive en secciones rurales o mixtas'],['C2 brecha de género',r.pct_C2_brecha_genero,'mujeres y hombres votan muy distinto'],['C3 peso juvenil',r.pct_C3_peso_juvenil,'tiene mucha población de 18–29']];m.sort((a,b)=>b[1]-a[1]);return m.slice(0,3)}}
function reco(r){{if(r.banda==='verde')return 'No requiere acciones extraordinarias: mantener la oferta ordinaria de educación cívica y vigilar a la cohorte de 18–29.';
 const m={{habito:'Trabajar con jóvenes y primovotantes: brigadas de credencialización e información en preparatorias y universidades, módulos itinerantes y mensajes claros sobre qué se elige en 2027 y para qué sirve.',
 desafeccion:'Reconstruir confianza con quienes dejaron de votar: diálogos distritales convocados por la Junta, explicación pública y sencilla del proceso y de los resultados anteriores, presencia visible del INE con anticipación.',
 vulnerabilidad:'Facilitar el acceso: ubicación y accesibilidad de casillas, materiales en lenguas indígenas, horarios y transporte en secciones rurales y mixtas, atención a la brecha de género.',
 mixto:'Combinar acciones de hábito y de confianza; la mezcla la define la Junta Distrital con los indicadores desagregados.'}};return (r.banda==='rojo'?'Intervención prioritaria. ':'Intervención focalizada. ')+m[r.mecanismo]}}
function select(r,zoom){{st.sel=r;gj.setStyle(style);if(zoom&&layers[r.id_def])map.fitBounds(layers[r.id_def].getBounds(),{{padding:[30,30],maxZoom:9}});
 const bar=(v,c)=>`<div class="bar"><i style="width:${{v}}%;background:${{c}}"></i></div>`;const top=mayor(r);const sin=r.p_2027_sin_intervencion,con=r.p_2027_con_intervencion;
 document.getElementById('detail').innerHTML=`<h2>${{dn(r)}}</h2>
 <p><span class="tag" style="background:${{COL[r.banda]}};font-size:14px">${{BN[r.banda].toUpperCase()}}</span> &nbsp; R = <b>${{fmt(r.R)}}</b> de 100 · lugar <b>${{DATA.filter(x=>x.R>r.R).length+1}}</b> de 300 en riesgo · prioridad de atención <b>#${{r.rango_prioridad}}</b></p>
 <h3>¿Por qué es ${{r.banda}}?</h3><div class="scale">${{scaleHTML(r)}}</div>
 <p class="note">Su R (${{fmt(r.R)}}) cae en el tramo ${{r.banda}} de la fila nacional; ${{cerca(r)}}.</p>
 <p class="note">Lo que más pesa: <b>${{top[0][0]}}</b> (${{pct(top[0][1])}}: ${{top[0][2]}}), <b>${{top[1][0]}}</b> (${{pct(top[1][1])}}) y <b>${{top[2][0]}}</b> (${{pct(top[2][1])}}).</p>
 <h3>Las tres causas</h3>
 <div class="kv"><span>Hábito · ¿los jóvenes aprenden a votar?</span><b>${{fmt(r.A_habito,0)}}</b></div>${{bar(r.A_habito,MEC.habito)}}
 <div class="kv"><span>Desafección · ¿sigue votando quien votaba?</span><b>${{fmt(r.B_desafeccion,0)}}</b></div>${{bar(r.B_desafeccion,MEC.desafeccion)}}
 <div class="kv"><span>Vulnerabilidad · ¿el territorio dificulta votar?</span><b>${{fmt(r.C_vulnerabilidad,0)}}</b></div>${{bar(r.C_vulnerabilidad,MEC.vulnerabilidad)}}
 <p class="note">Causa principal: <b>${{MECN[r.mecanismo]}}</b>. R = 0.40×${{fmt(r.A_habito,0)}} + 0.40×${{fmt(r.B_desafeccion,0)}} + 0.20×${{fmt(r.C_vulnerabilidad,0)}} = <b>${{fmt(r.R)}}</b>.</p>
 <h3>Su historia</h3>
 <div class="kv"><span>Votó en 2012 → 2018 → 2021 → 2024</span><b>${{fmt(r.p_total_2012)}} → ${{fmt(r.p_total_2018)}} → ${{fmt(r.p_total_2021)}} → ${{fmt(r.p_total_2024)}} %</b><span>Jóvenes 18–29: 2012 → 2024</span><b>${{fmt(r.p_J_2012)}} → ${{fmt(r.p_J_2024)}} %</b><span>30 años y más (2024)</span><b>${{fmt(r.p_A_2024)}} %</b><span>Mujeres / hombres (2024)</span><b>${{fmt(r.p_M_2024)}} / ${{fmt(r.p_H_2024)}} %</b><span>Personas en lista nominal (2024)</span><b>${{fmtN(r.LN_2024)}}</b></div>
 <h3>2027, paso a paso</h3>
 <div class="kv"><span>Partida: lo que votó en 2021</span><b>${{fmt(r.p_total_2021)}} %</b><span>Impulso reciente: 2024 − 2018</span><b>${{r.p_total_2024-r.p_total_2018>=0?'+':''}}${{fmt(r.p_total_2024-r.p_total_2018)}} pts</b><span><b>Sin intervención</b></span><b>${{fmt(sin)}} %</b><span>Promoción focalizada (${{r.banda}}: +${{BONO[r.banda]}} pts)</span><b>+${{BONO[r.banda]}}</b><span><b>Con intervención</b></span><b style="color:var(--accent)">${{fmt(con)}} %</b><span>Personas adicionales que votarían</span><b>≈ ${{fmtN(Math.round((con-sin)/100*r.LN_2024))}}</b></div>
 <h3>Qué hacer aquí</h3><p class="note">${{reco(r)}}</p>`;
 if(zoom)document.getElementById('detail').scrollIntoView({{behavior:'smooth',block:'nearest'}})}}
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{{const b=c.dataset.b;st.bands.has(b)?st.bands.delete(b):st.bands.add(b);c.classList.toggle('off',!st.bands.has(b));paint()}}));
fE.addEventListener('change',e=>{{st.edo=e.target.value;paint()}});document.getElementById('fMec').addEventListener('change',e=>{{st.mec=e.target.value;paint()}});document.getElementById('fVar').addEventListener('change',e=>{{st.var=e.target.value;paint()}});
document.getElementById('buscar').addEventListener('input',e=>{{st.q=e.target.value;gj.setStyle(style);tabla()}});
document.getElementById('reset').addEventListener('click',()=>{{st.edo='';st.mec='';st.var='banda';st.q='';st.bands=new Set(['rojo','naranja','amarillo','verde']);fE.value='';document.getElementById('fMec').value='';document.getElementById('fVar').value='banda';document.getElementById('buscar').value='';document.querySelectorAll('.chip').forEach(c=>c.classList.remove('off'));st.sel=null;gj.setStyle(style);legend();tabla();map.setView([23.8,-102.3],5)}});
document.getElementById('ej').addEventListener('click',e=>{{e.preventDefault();select(byId['30-18'],true)}});
legend();tabla();
</script></body></html>"""
out = os.path.join(ROOT, "entregables/tablero_alerta_temprana.html")
open(out, "w").write(html)
open(os.path.join(ROOT, "docs/index.html"), "w").write(html)  # copia para GitHub Pages
print("Tablero:", round(os.path.getsize(out) / 1e6, 2), "MB")
