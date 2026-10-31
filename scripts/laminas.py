"""Genera las 10 láminas (PPTX) con python-pptx."""
import os, json, pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "reporte/fig"); OUT = os.path.join(ROOT, "entregables/Laminas-Alerta-temprana-de-abstencion.pptx")
INK = RGBColor(0x19, 0x1C, 0x26); INK2 = RGBColor(0x4A, 0x55, 0x68); ACC = RGBColor(0x00, 0x7A, 0xF0); JADE = RGBColor(0x19, 0xA3, 0x72)
ROJO = RGBColor(0xD0, 0x3B, 0x3B); NAR = RGBColor(0xEC, 0x83, 0x5A); AMA = RGBColor(0xFA, 0xB2, 0x19); VER = RGBColor(0x0C, 0xA3, 0x0C); GRIS = RGBColor(0xE1, 0xE4, 0xEA)
prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BL = prs.slide_layouts[6]
val = json.load(open(os.path.join(ROOT, "outputs/validacion.json"))); nac = json.load(open(os.path.join(ROOT, "outputs/escenarios_nacional.json")))

def tb(s, x, y, w, h, text, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT, font="Calibri"):
    t = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = t.text_frame; tf.word_wrap = True
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        r = p.add_run(); r.text = ln; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = font
        p.space_after = Pt(6)
    return t
def rect(s, x, y, w, h, fill, line=None):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)); r.fill.solid(); r.fill.fore_color.rgb = fill
    if line is None: r.line.fill.background()
    else: r.line.color.rgb = line
    r.shadow.inherit = False; return r
def header(s, n, title, kicker=None):
    rect(s, 0, 0, 13.333, 0.08, ACC)
    tb(s, 0.6, 0.35, 11, 0.4, (kicker or "Alerta temprana de abstención · Hackathon INE 2026 · Eje 2").upper(), 10, True, JADE)
    tb(s, 0.6, 0.68, 12.2, 0.9, title, 24, True, INK)
    tb(s, 12.3, 6.95, 0.6, 0.3, f"{n}/10", 10, False, INK2, PP_ALIGN.RIGHT)
    tb(s, 0.6, 6.95, 8, 0.3, "Leopoldo Bassoco Nova · Alan Anastasio · Fuente única: Plataforma CCPC (INE-DECEyEC) · Sin datos personales", 9, False, INK2)
def bullets(s, x, y, w, h, items, size=15):
    t = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = t.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if isinstance(it, tuple): head, body = it
        else: head, body = None, it
        if head:
            r = p.add_run(); r.text = head + " "; r.font.bold = True; r.font.size = Pt(size); r.font.color.rgb = INK; r.font.name = "Calibri"
        r = p.add_run(); r.text = body; r.font.size = Pt(size); r.font.color.rgb = INK2; r.font.name = "Calibri"; p.space_after = Pt(10)
    return t
def stat(s, x, y, w, val, label, color=INK):
    rect(s, x, y, w, 1.35, RGBColor(0xF6, 0xF7, 0xF9)); tb(s, x + 0.15, y + 0.1, w - 0.3, 0.7, val, 30, True, color); tb(s, x + 0.15, y + 0.78, w - 0.3, 0.5, label, 11, False, INK2)

# 1 Portada
s = prs.slides.add_slide(BL); rect(s, 0, 0, 13.333, 7.5, INK)
tb(s, 0.8, 1.2, 11, 0.4, "HACKATHON 2026 · HACKEA LA PARTICIPACIÓN · EJE 2: PREDICCIÓN Y ESCENARIOS DE RIESGO DE ABSTENCIÓN", 11, True, JADE)
tb(s, 0.8, 1.8, 11.5, 1.6, "Alerta temprana de abstención", 54, True, RGBColor(0xFF, 0xFF, 0xFF))
tb(s, 0.8, 3.3, 11, 1.0, "Un índice territorial de riesgo de caída de la participación para los 300 distritos electorales federales, construido sólo con los Conteos Censales de Participación Ciudadana", 20, False, RGBColor(0xE6, 0xE9, 0xEF))
tb(s, 0.8, 5.6, 11, 0.9, ["Leopoldo Bassoco Nova · Alan Anastasio (participación a título personal)", "Octubre de 2026 · Reporte, tablero, CSV, GeoJSON y repositorio reproducible"], 14, False, RGBColor(0xB8, 0xBF, 0xCC))

# 2 Tesis
s = prs.slides.add_slide(BL); header(s, 2, "La abstención no es un evento: es un proceso que deja rastro")
bullets(s, 0.6, 1.8, 6.4, 4.8, [
    ("Dos déficits documentados por el propio INE.", "Confianza en las instituciones (Informe País 2020: 22 % confía en los partidos) y comprensión de lo que está en juego (ENCUCI 2020). La abstención es su expresión territorial y medible."),
    ("Tres mecanismos observables en el CCPC.", "Pérdida del hábito en las cohortes jóvenes (Plutzer, Franklin), desafección reciente del electorado adulto (Easton, Reif y Schmitt) y vulnerabilidad estructural (Verba, Schlozman y Brady)."),
    ("Lo que se mide es lo que se puede prevenir.", "No la participación absoluta, que castiga a los distritos pobres para siempre, sino la caída respecto a la trayectoria propia de cada distrito."),
    ("Gramática de riesgo, lógica de alerta.", "Identificar, medir, clasificar, priorizar y monitorear (OCDE–JRC); indicadores adelantados, umbrales y acciones (Grabo). Mandato: art. 41 CPEUM; arts. 30 y 58 LGIPE; ENCCÍVICA.")], 14)
s.shapes.add_picture(os.path.join(FIG, "fig1_series_nacional.png"), Inches(7.3), Inches(2.0), width=Inches(5.6))
tb(s, 7.3, 5.1, 5.6, 1.2, "La brecha entre 18–29 y 30+ se mantiene en ~14 puntos desde 2009; la participación juvenil de 2024 (49.2 %) está 5 puntos por debajo de la de 2012.", 11, False, INK2)

# 3 Datos
s = prs.slides.add_slide(BL); header(s, 3, "Datos: 26.6 millones de registros del CCPC, 2009–2025, sin un solo dato personal")
stat(s, 0.6, 1.8, 2.9, "7", "elecciones federales: 6 ordinarias + judicial 2025 (hold-out)"); stat(s, 3.7, 1.8, 2.9, "3.9 GB", "archivos abiertos sección × sexo × edad"); stat(s, 6.8, 1.8, 2.9, "300", "distritos en cartografía 2023, comparables en el tiempo"); stat(s, 9.9, 1.8, 2.9, "0.08 %", "lista nominal máxima sin asignar al redistritar")
bullets(s, 0.6, 3.5, 12, 3.2, [
    ("Agregación.", "Distrito × sexo × grupo de edad (18–19, 20–24, 25–29, 30–39, …, 70+) × tipo de sección (urbana, mixta, rural). Participación = SV / (SV + NV), como la calcula el INE. Las cifras nacionales reproducen las oficiales (2024: 59.7 %; 2025: 13.0 %)."),
    ("Redistritación documentada.", "Los archivos 2009–2021 refieren al marco 2021 y los de 2024–2025 al marco 2023. Se construyó una tabla sección → distrito 2023 (74 002 directas, 1 076 por secciones hijas, 851 por mayoría) y se reasignó toda la serie."),
    ("Lo que la fuente no trae.", "La marca indígena/afromexicana sólo está en el visualizador, no en los archivos abiertos: el componente de vulnerabilidad usa tipo de sección, sexo y edad. No se agregan variables externas por diseño.")], 13)

# 4 Método
s = prs.slides.add_slide(BL); header(s, 4, "Método: nueve indicadores, tres componentes, un índice con juicios de valor declarados")
cols = [("A · Hábito (0.40)", RGBColor(0x62, 0x50, 0xD6), ["A1 Desgaste juvenil: pendiente de la participación 18–29 (2009–2024)", "A2 Brecha generacional: (p30+ − p18–29) 2024 vs 2012", "A3 Retención de cohorte: p30–39 en 2024 − p18–29 en 2012"]),
        ("B · Desafección (0.40)", ACC, ["B1 Rebote perdido: (p2012 − p2009) − (p2024 − p2021)", "B2 Caída adulta: p30+ 2018 − 2024", "B3 Volatilidad: sd de residuos de la trayectoria"]),
        ("C · Vulnerabilidad (0.20)", JADE, ["C1 Peso rural y mixto en la lista nominal", "C2 Brecha de género |pM − pH|", "C3 Peso de 18–29 en la lista nominal"])]
for i, (t, c, items) in enumerate(cols):
    x = 0.6 + i * 4.15; rect(s, x, 1.8, 3.95, 0.5, c); tb(s, x + 0.1, 1.85, 3.8, 0.4, t, 14, True, RGBColor(0xFF, 0xFF, 0xFF))
    rect(s, x, 2.3, 3.95, 2.3, RGBColor(0xF6, 0xF7, 0xF9)); bullets(s, x + 0.1, 2.4, 3.75, 2.2, items, 11)
tb(s, 0.6, 4.8, 12, 0.5, "R = 0.40 · A + 0.40 · B + 0.20 · C      (percentil 0–100 por indicador · agregación lineal · Handbook OCDE–JRC 2008)", 16, True, ACC, PP_ALIGN.CENTER)
bullets(s, 0.6, 5.4, 12, 1.5, [("Bandas por cuantiles:", "rojo 15 % · naranja 20 % · amarillo 30 % · verde 35 % (capacidad operativa, no umbral natural)."), ("Mecanismo dominante:", "componente que aporta ≥ 40 % de R; conecta el diagnóstico con la acción."), ("Prioridad:", "R × tamaño relativo de la lista nominal.")], 12)

# 5 Mapa
s = prs.slides.add_slide(BL); header(s, 5, "Resultado: 45 distritos en rojo y 60 en naranja; 33.4 millones de personas en lista nominal")
s.shapes.add_picture(os.path.join(FIG, "fig0_mapa.png"), Inches(0.5), Inches(1.7), height=Inches(5.1))
stat(s, 8.6, 1.8, 2.1, "45", "rojo · 14.4 M", ROJO); stat(s, 10.8, 1.8, 2.1, "60", "naranja · 19.0 M", NAR); stat(s, 8.6, 3.3, 2.1, "89", "amarillo · 28.9 M", AMA); stat(s, 10.8, 3.3, 2.1, "106", "verde · 36.1 M", VER)
bullets(s, 8.6, 4.9, 4.3, 2.0, [("Dónde:", "Veracruz 13, Chiapas 9, Tabasco 6, Guerrero 5, Sinaloa 3; Oaxaca en naranja; Estado de México repartido; CDMX, Coahuila y Chihuahua en verde."), ("Por qué:", "los rojos participaban 66 % en 2012 y 2018; hoy 58.9 %. Están perdiendo electorado, no es que nunca lo tuvieran.")], 11)

# 6 Mecanismo
s = prs.slides.add_slide(BL); header(s, 6, "El mecanismo importa: el rojo es desafección reciente, no pobreza")
rows = [["Banda", "Desafección", "Hábito", "Mixto", "Vulnerab."], ["Rojo", "37", "8", "0", "0"], ["Naranja", "31", "28", "1", "0"], ["Amarillo", "39", "49", "1", "0"], ["Verde", "45", "47", "9", "5"]]
tbl = s.shapes.add_table(5, 5, Inches(0.6), Inches(1.9), Inches(5.8), Inches(2.4)).table
for i, r in enumerate(rows):
    for j, v in enumerate(r):
        c = tbl.cell(i, j); c.text = v; p = c.text_frame.paragraphs[0]; p.runs[0].font.size = Pt(13); p.runs[0].font.bold = (i == 0 or j == 0); p.runs[0].font.name = "Calibri"
        c.fill.solid(); c.fill.fore_color.rgb = GRIS if i == 0 else RGBColor(0xFF, 0xFF, 0xFF); p.runs[0].font.color.rgb = INK
bullets(s, 6.8, 1.9, 6, 4.8, [
    ("Desafección (Golfo, sureste, Sinaloa).", "Electorado adulto que votaba y dejó de hacerlo; rebote presidencial débil. 37 de los 45 rojos."),
    ("Hábito (metrópolis del centro y norte).", "La cohorte 18–29 no adquiere el hábito: Nuevo León 13 pasó de 61.5 % a 41.8 % de participación juvenil entre 2012 y 2024. Domina en Estado de México, Nuevo León, Jalisco y Sonora."),
    ("Vulnerabilidad estructural.", "Sólo domina en 5 distritos, todos verdes: ser rural y pobre con participación estable no enciende la alerta. Es deliberado."),
    ("Consecuencia.", "Un rojo por hábito y un rojo por desafección necesitan intervenciones distintas; el semáforo las separa.")], 13)

# 7 Validación
s = prs.slides.add_slide(BL); header(s, 7, "¿Funciona? Sí para la intermedia; no para la judicial, y lo decimos")
s.shapes.add_picture(os.path.join(FIG, "fig3_validacion.png"), Inches(0.5), Inches(1.8), width=Inches(6.6))
bt = val["backtest_2018_a_2021"]; ho = val["holdout_2025"]
bullets(s, 7.3, 1.8, 5.6, 5.0, [
    ("Backtest 2018 → 2021.", f"Índice calculado sólo con datos hasta 2018 y contrastado con la caída no anticipada de 2021. Spearman {bt['spearman_R_sorpresa']}; orden monótono por banda; {bt['pct_rojos_con_sorpresa_sobre_mediana']} % de los rojos cayeron más que la mediana frente a {bt['pct_verdes_con_sorpresa_sobre_mediana']} % de los verdes."),
    ("Prueba de estrés: judicial 2025.", f"Spearman {ho['spearman_R_sorpresa']}: el índice no anticipa ese evento. La participación de 13 % respondió a una elección inédita y a capacidad de movilización organizada, no a la erosión del hábito y del apoyo difuso que el índice mide."),
    ("Qué significa.", "El instrumento es válido para elecciones federales ordinarias (el caso de 2027) y no debe usarse para extraordinarias de otra naturaleza. Un límite declarado vale más que una correlación inflada.")], 13)

# 8 Sensibilidad
s = prs.slides.add_slide(BL); header(s, 8, "Robustez: la lista roja resiste los cambios de pesos y de método")
sens = pd.read_csv(os.path.join(ROOT, "outputs/sensibilidad.csv"))
tbl = s.shapes.add_table(len(sens) + 1, 4, Inches(0.6), Inches(1.8), Inches(7.2), Inches(4.6)).table
hdr = ["Variante", "Cambian de banda", "Rojos que se mantienen", "ρ con base"]
for j, v in enumerate(hdr): c = tbl.cell(0, j); c.text = v; c.fill.solid(); c.fill.fore_color.rgb = GRIS
for i, r in sens.iterrows():
    for j, v in enumerate([r.variante, f"{r.pct_cambia_banda} %", f"{r.pct_rojos_se_mantienen} %", f"{r.spearman_con_base}"]):
        c = tbl.cell(i + 1, j); c.text = v; c.fill.solid(); c.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
for i in range(len(sens) + 1):
    for j in range(4):
        p = tbl.cell(i, j).text_frame.paragraphs[0]; p.runs[0].font.size = Pt(11); p.runs[0].font.name = "Calibri"; p.runs[0].font.color.rgb = INK; p.runs[0].font.bold = (i == 0)
bullets(s, 8.2, 1.8, 4.7, 4.8, [("Criterio previo:", "menos de 15 % de distritos cambian de banda ante ±0.10 en los pesos de componente. Se cumple en los seis casos."), ("Variantes estructurales", "(pesos iguales, geométrica) mueven el centro de la distribución, pero los rojos se conservan en más de 84 % de los casos."), ("Lectura:", "la lista de atención prioritaria es robusta; la frontera amarillo/verde es la más sensible.")], 13)

# 9 Escenarios
s = prs.slides.add_slide(BL); header(s, 9, "Escenarios 2027: qué pasa si no se interviene y qué se recuperaría con una campaña focalizada")
s.shapes.add_picture(os.path.join(FIG, "fig4_escenarios.png"), Inches(0.5), Inches(1.8), width=Inches(6.6))
stat(s, 7.4, 1.8, 2.7, f"{nac['p_2027_sin_intervencion']} %", "2027 sin intervención (impulso reciente de cada distrito)"); stat(s, 10.2, 1.8, 2.7, f"{nac['p_2027_con_intervencion']} %", "2027 con campaña focalizada (supuesto +3/+2/+1 pp)", ACC)
bullets(s, 7.4, 3.4, 5.5, 3.4, [("Sin intervención:", "a la última intermedia (2021) se aplica el cambio 2018 → 2024 de cada distrito. Los rojos pasarían de 58.6 % a 51.1 %."), ("Con intervención:", "el INE concentra una campaña en rojos, naranjas y amarillos. Se supone que rinde +3, +2 y +1 puntos. Es un supuesto ajustable, no un resultado medido."), ("Diferencia:", "1.1 puntos nacionales, algo más de un millón de personas; 3 puntos en los rojos (unas 430 mil). No es pronóstico: es el orden de magnitud de lo recuperable si la campaña rinde lo supuesto. La prioridad por riesgo se apoya en el índice y su backtest, no en este escenario.")], 12)

# 10 Recomendaciones y entregables
s = prs.slides.add_slide(BL); header(s, 10, "Recomendaciones por banda y mecanismo, y qué entregamos")
for i, (t, c, body) in enumerate([("Rojo/naranja por desafección · 68", ROJO, "Ejes Diálogo y Exigencia: diálogos distritales con la Junta, explicación pública del proceso y de los resultados anteriores, presencia anticipada del INE. Indicador a mover: participación 30+."),
                                  ("Rojo/naranja por hábito · 36", NAR, "Eje Verdad y primovotantes: brigadas en media superior y superior, módulos itinerantes, mensajes sobre qué se elige en 2027. Indicador a mover: participación 18–29 y retención de cohorte."),
                                  ("Amarillo · 89 / Verde · 106", AMA, "Vigilancia y oferta ordinaria; atención logística en los cinco verdes con vulnerabilidad dominante (casillas, lenguas indígenas).")]):
    y = 1.8 + i * 1.35; rect(s, 0.6, y, 0.12, 1.15, c); tb(s, 0.85, y, 3.4, 1.1, t, 13, True, INK); tb(s, 4.2, y, 4.6, 1.2, body, 11, False, INK2)
bullets(s, 9.1, 1.8, 3.9, 2.6, [("Para el INE:", "incorporar el índice al SMS&E de la ENCCÍVICA; liberar la marca indígena/afro en los datos abiertos; publicar la tabla oficial de equivalencias seccionales.")], 11)
rect(s, 9.1, 4.3, 3.9, 2.4, RGBColor(0xF6, 0xF7, 0xF9)); bullets(s, 9.2, 4.35, 3.7, 2.3, [("Entregables:", "reporte metodológico (14 pp.) · tablero web autocontenido · CSV distrital (300 × 35) · GeoJSON con semáforo · repositorio con config.json y 4 scripts · corre en < 10 min · sin datos personales.")], 11)
tb(s, 0.6, 6.0, 8.3, 0.8, "La etiqueta «rojo» describe una trayectoria, no una población. El instrumento orienta la promoción del voto y la educación cívica; no infiere preferencias ni califica territorios.", 12, False, INK2)
prs.save(OUT); print("OK", OUT)
