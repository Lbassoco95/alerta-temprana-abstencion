# Alerta temprana de abstención

**Índice territorial de riesgo de caída de la participación para los 300 distritos electorales federales de México**, construido únicamente con la Plataforma de Conteos Censales de Participación Ciudadana (CCPC) del INE.

Hackathon 2026 «Hackea la participación: datos que construyen democracia» · Instituto Nacional Electoral · **Eje 2: Predicción y escenarios de riesgo de abstención**
Equipo: Leopoldo Bassoco Nova · Alan Anastasio (participación a título personal) · Octubre de 2026

> **Tablero interactivo:** `docs/index.html` (publicado con GitHub Pages en `https://<usuario>.github.io/alerta-temprana-abstencion/`). También se puede abrir el archivo directamente en cualquier navegador: no requiere servidor ni conexión.

---

## 1. En una página

**La pregunta del INE:** ¿qué zonas podrían presentar mayor abstención si no se interviene?

**La respuesta de este trabajo:** la abstención es un proceso que deja rastro en los datos antes de ocurrir. Comparando a cada distrito con su propia historia (2009–2024) se construye un índice **R (0–100)** que resume nueve señales de alerta en tres causas: pérdida del **hábito** de votar en los jóvenes, **desafección** reciente del electorado adulto y **vulnerabilidad** del territorio. Los 300 distritos se ordenan por R y se pintan en un semáforo (45 rojos, 60 naranjas, 89 amarillos, 106 verdes); cada uno recibe además su causa principal y un lugar de prioridad que pondera riesgo por tamaño de lista nominal.

**Resultados principales**

| | |
|---|---|
| Distritos en rojo | 45 (14.4 millones de personas en lista nominal): Veracruz 13, Chiapas 9, Tabasco 6, Guerrero 5, Sinaloa 3 |
| Causa dominante en el rojo | Desafección reciente en 37 de 45; hábito en 8. La vulnerabilidad estructural no domina en ningún rojo |
| ¿Anticipa? | Calculado sólo con datos hasta 2018, ordena correctamente la caída de la intermedia 2021: Spearman 0.37, monótono por banda, 76 % de rojos vs 28 % de verdes cayeron más que la mediana |
| Límite declarado | No anticipa la elección judicial 2025 (Spearman 0.04): esa elección midió movilización organizada, no desgaste |
| Robustez | ±0.10 en los pesos cambia la banda de 9–13 % de los distritos; los rojos se conservan en > 84 % bajo todas las variantes |
| Escenarios 2027 | 49.2 % de participación si cada distrito sigue su impulso; 50.3 % con promoción focalizada (+3/+2/+1 puntos en rojo/naranja/amarillo): ≈ 1.1 millones de personas |

**Qué recibe cada junta distrital:** su color, su causa, su lugar de prioridad, su historia 2009–2024, su escenario 2027 y una recomendación alineada con los ejes de la ENCCÍVICA.

---

## 2. Entregables (carpeta `entregables/`)

| Entregable de la convocatoria | Archivo |
|---|---|
| Reporte metodológico y preventivo (10–15 cuartillas, PDF) | `Reporte-metodologico-Alerta-temprana-de-abstencion.pdf` (14 pp.; fuente editable `.docx`) |
| Mapa de escenarios (archivo ejecutable) | `tablero_alerta_temprana.html` (autocontenido) y `semaforo_riesgo_abstencion_distrital.geojson` |
| Base de datos anonimizada (CSV) | `indice_riesgo_abstencion_distrital.csv` (300 distritos × 35 columnas) |
| Presentación ejecutiva (máx. 10 diapositivas) | `Laminas-Alerta-temprana-de-abstencion.pptx` (y `.pdf`) |
| Código o repositorio | Este repositorio |
| Cartas firmadas | Se entregan en el ZIP de envío; guía en `CARTAS-guia-de-llenado.md` |

---

## 3. Estructura del repositorio

```
alerta-temprana-abstencion/
├── README.md                 ← este documento
├── config.json               ← todos los juicios de valor: pesos, normalización, cortes, supuestos
├── run.sh                    ← reproduce todo en < 2 min
├── requirements.txt
├── CITATION.cff · LICENSE.md · CHANGELOG.md
│
├── scripts/
│   ├── crosswalk.py          ← tabla sección → distrito 2023 (redistritación)
│   ├── agrega_def24.py       ← agrega los CSV originales del INE (paso opcional, 3.9 GB)
│   ├── indice.py             ← indicadores, percentiles, R, bandas, mecanismo, prioridad,
│   │                            validación (backtest 2021, estrés 2025), sensibilidad, escenarios
│   ├── exporta.py            ← CSV y GeoJSON entregables
│   ├── tablero.py            ← tablero HTML autocontenido (+ docs/index.html)
│   └── laminas.py            ← genera el PPTX
│
├── data/
│   ├── raw/README.md         ← cómo obtener los archivos originales del INE (no se versionan)
│   ├── agregados/            ← CCPC agregado a distrito 2023 × sexo × grupo de edad × tipo de sección
│   ├── crosswalk/            ← equivalencias seccionales y tabla sección → distrito 2023
│   └── geo/                  ← polígonos de distritos (2023) y entidades, simplificados
│
├── outputs/                  ← resultados intermedios (índice completo, series, backtest, sensibilidad, escenarios)
├── entregables/              ← lo que se envía al INE (sección 2)
├── db/
│   ├── migrations/0001_esquema_base.sql ← esquema de la plataforma (7 esquemas, probado)
│   ├── seed/                 ← CSV para poblar la base con los resultados de la fase 0
│   └── README.md
├── docs/
│   ├── index.html            ← tablero (GitHub Pages)
│   ├── ARQUITECTURA-PLATAFORMA.md ← fase 2: base de datos, API, web guiada, señales, analítica, tiempo real
│   ├── METODOLOGIA.md        ← fundamentos matemáticos, validación y sensibilidad, fórmula por fórmula
│   ├── DICCIONARIO-DE-DATOS.md
│   └── fig/                  ← figuras del reporte
├── reporte/                  ← fuente Markdown del reporte y figuras
└── vendor/leaflet/           ← biblioteca de mapas embebida (BSD-2)
```

---

## 4. Cómo reproducir

```bash
git clone https://github.com/<usuario>/alerta-temprana-abstencion.git
cd alerta-temprana-abstencion
pip install -r requirements.txt
./run.sh
```

`run.sh` ejecuta `indice.py → exporta.py → tablero.py` sobre los agregados incluidos y regenera `outputs/`, `entregables/*.csv|geojson|html` y `docs/index.html`. Para cambiar un peso, un corte o el supuesto de los escenarios basta editar `config.json` y volver a correr.

Para reproducir **desde los archivos originales del INE** (3.9 GB), siga `data/raw/README.md`: descargue los siete ZIP, descomprima cada uno en su carpeta y ejecute `scripts/agrega_def24.py` por año antes de `run.sh`.

Requisitos: Python ≥ 3.10, pandas, numpy, geopandas (sólo `exporta.py`), matplotlib y python-pptx (sólo figuras y láminas), pandoc (sólo para incrustar `METODOLOGIA.md` en el tablero).

---

## 5. Método en breve

Nueve indicadores a nivel distrito, todos orientados a «más = más riesgo», convertidos a percentil (0–100) y agregados linealmente con pesos declarados:

| Componente | Indicadores | Peso |
|---|---|---|
| **A. Hábito** | A1 desgaste de la participación 18–29 (pendiente 2009–2024, controlando elección presidencial) · A2 brecha generacional 2024 vs 2012 · A3 retención de la cohorte que debutó en 2012 | 0.40 |
| **B. Desafección** | B1 rebote perdido (p2012 − p2009) − (p2024 − p2021) · B2 caída de la participación 30+ entre 2018 y 2024 · B3 volatilidad residual | 0.40 |
| **C. Vulnerabilidad** | C1 peso rural y mixto · C2 brecha de género · C3 peso de 18–29 en la lista nominal | 0.20 |

`R = 0.40·A + 0.40·B + 0.20·C` · bandas por cuantiles 15/20/30/35 % · mecanismo dominante = componente que aporta ≥ 40 % de R · prioridad = R × lista nominal relativa · escenario 2027 sin intervención = p2021 + (p2024 − p2018); con intervención = + 3/2/1/0 puntos por banda.

Cada fórmula, la construcción de la validación fuera de muestra y el procedimiento del análisis de sensibilidad están en **`docs/METODOLOGIA.md`**. El marco teórico (Easton, Norris, Plutzer, Franklin, Reif y Schmitt, Verba–Schlozman–Brady, Rosenstone y Hansen, Grabo) y las referencias completas están en el reporte.

---

## 6. Datos y tratamiento

* **Fuente única:** INE-DECEyEC, Conteos Censales de Participación Ciudadana 2009, 2012, 2015, 2018, 2021 y 2024, más PEEFPJ 2024–2025 (26.6 millones de registros sección × sexo × edad). Participación = SV / (SV + NV), como en la plataforma. Las cifras nacionales reproducen las oficiales.
* **Redistritación:** los archivos 2009–2021 refieren al marco cartográfico 2021 y los de 2024–2025 al de 2023. Toda la serie se llevó a los 300 distritos de 2023 con una tabla sección → distrito (74 002 asignaciones directas, 1 076 por secciones hijas, 851 por mayoría); lista nominal no asignable ≤ 0.085 %.
* **Lo que la fuente abierta no trae:** la marca indígena/afromexicana (sólo en el visualizador); se recomienda al INE liberarla.
* **Cartografía:** shapefiles del INE sistematizados en *Recent Mexican electoral geography* (E. Magar, ITAM, 2019/2026).

---

## 7. De pipeline a plataforma

La fase 0 es un pipeline reproducible y un tablero estático. `docs/ARQUITECTURA-PLATAFORMA.md` describe cómo convertirlo en un sistema que el INE pueda seguir alimentando: base de datos como fuente de verdad (`db/migrations/0001_esquema_base.sql`, con catálogos y cartografía versionada, hechos del CCPC, corridas del índice, decisiones e intervenciones, señales continuas, panel analítico abierto a nuevas variables y registro de modelos), API de sólo lectura para el público, una web guiada y, hacia 2027, lectura de agregados por sección durante la jornada electoral. Siempre sobre agregados territoriales, nunca sobre personas.

## 8. Privacidad y uso responsable

No se utiliza, requiere ni produce ningún dato personal. La unidad mínima de la fuente es el agregado sección × sexo × edad y los resultados se expresan a nivel distrito. El instrumento orienta la promoción del voto y la educación cívica; no infiere preferencias, no decide ubicación de casillas y no califica poblaciones. La etiqueta «rojo» describe una trayectoria, no a las personas de un territorio.

---

## 9. Cómo citar

Bassoco Nova, L., y Anastasio, A. (2026). *Alerta temprana de abstención: índice territorial de riesgo de caída de la participación para los 300 distritos electorales federales* [Código y datos]. Hackathon 2026 «Hackea la participación», INE. Ver `CITATION.cff`.

Términos de uso en `LICENSE.md` (cesión de derechos patrimoniales al INE por diez años conforme a la convocatoria; autoría conservada).
