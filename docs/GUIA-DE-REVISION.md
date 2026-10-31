# Guía de revisión — diseño y base teórica

Para quien revisa el proyecto por primera vez (en particular Alan, 31-oct-2026). Treinta minutos bastan si se sigue este orden. Todo lo que se cita está en este repositorio o en los enlaces.

**Dónde verlo funcionando:** https://alerta-temprana-abstencion.vercel.app · https://lbassoco95.github.io/alerta-temprana-abstencion/

## 1. La pregunta y la respuesta en tres frases

El INE pregunta qué zonas podrían presentar mayor abstención si no se interviene. Respondemos que la abstención es un proceso que deja rastro antes de ocurrir, y que ese rastro se puede medir distrito por distrito comparando a cada uno con su propia historia. El resultado es un semáforo de 300 distritos con un índice R (0–100), una causa principal y un orden de prioridad; 45 quedan en rojo, concentrados en Veracruz, Chiapas, Tabasco, Guerrero y Sinaloa, y la causa dominante ahí es desafección reciente, no pobreza.

## 2. Base teórica: de dónde sale cada pieza

| Pieza del sistema | De dónde viene | Qué aporta al diseño |
|---|---|---|
| Dos déficits (confianza y comprensión) | Easton (1975): apoyo difuso; Norris (1999): ciudadanos críticos; Delli Carpini y Keeter (1996): conocimiento político. Evidencia mexicana: Informe País 2020 (INE/PNUD), ENCUCI 2020 (INEGI/INE) | La tesis: la abstención es la expresión territorial de esos déficits, no un evento aislado |
| Componente A, hábito | Plutzer (2002): el voto es un hábito que se forma o se pierde en las primeras elecciones; Gerber, Green y Shachar (2003); Franklin (2004); Ryder (1965): análisis de cohortes | Mirar a los 18–29 y seguir a la cohorte que debutó en 2012 hasta 2024 |
| Componente B, desafección | Easton (1975); Reif y Schmitt (1980): elecciones de segundo orden; Rosenstone y Hansen (1993): participación dependiente de movilización | Rebote presidencial, caída del electorado adulto, volatilidad |
| Componente C, vulnerabilidad | Verba, Schlozman y Brady (1995): recursos y costos de participar | Ruralidad, brecha de género, peso de la población joven |
| Lógica de riesgo y alerta | OCDE y JRC (2008), *Handbook on Constructing Composite Indicators*; Grabo (2004), *Anticipating Surprise* | Índice compuesto con pesos declarados y sensibilidad obligatoria; indicadores adelantados con umbrales y acciones |
| Mandato y acción | CPEUM art. 41; LGIPE arts. 30 y 58; ENCCÍVICA 2017–2023 (ejes Verdad, Diálogo, Exigencia) | Las recomendaciones por banda y causa caen en atribuciones existentes del INE |

Lo que **no** es: no es una analogía del cumplimiento regulatorio ni una securitización de la abstención; la gramática de riesgo se toma prestada, el contenido es teoría política y evidencia del propio INE. Referencias completas en el reporte (`entregables/Reporte-…pdf`, sección 10).

## 3. Decisiones de diseño y por qué

1. **Medir caída respecto a la trayectoria propia, no participación absoluta.** La participación absoluta reproduce la estructura socioeconómica y castiga para siempre a los distritos pobres; la caída relativa es lo prevenible. Por eso los rojos participaban *más* que el promedio en 2012 y 2018.
2. **Una sola fuente, el CCPC.** Lo pide la convocatoria y demuestra cuánto anticipa el INE con lo que ya produce. Sin variables externas en la fase 0; el esquema `analitica` está listo para agregarlas después.
3. **Grano sección × sexo × edad, nunca personas.** Impuesto por el esquema de datos, no por buena voluntad.
4. **Redistritación explícita.** Los archivos 2009–2021 vienen en cartografía 2021 y los de 2024–2025 en la 2023; se construyó un crosswalk sección → distrito 2023 (74 002 directas, 1 076 por secciones hijas, 851 por mayoría), con pérdida máxima de 0.085 % de lista nominal. Sin esto la serie no es comparable.
5. **Percentiles, no valores crudos.** Nueve indicadores en unidades distintas; el percentil es inmune a atípicos y legible («peor que el 92 % de los distritos»). Min–max y *z* se prueban en sensibilidad.
6. **Pesos declarados, no estimados.** 0.40 hábito, 0.40 desafección, 0.20 vulnerabilidad: el riesgo prevenible está en los procesos, no en la estructura. Son juicios de valor y están en `config.json`; cambiarlos es editar una línea.
7. **Bandas por cuantiles, no por umbral.** 15/20/30/35 % porque la capacidad operativa de las juntas es finita; el color es un lugar en la fila, se recalcula cada elección.
8. **Mecanismo dominante.** La causa que aporta ≥ 40 % de R; conecta el diagnóstico con la acción (un rojo por hábito y uno por desafección se atienden distinto).
9. **Validación honesta.** Backtest con datos a 2018 contra 2021 (Spearman 0.37, monótono por banda, 76 % de rojos vs 28 % de verdes sobre la mediana). La judicial 2025 no se anticipa (0.04) y se declara como límite.
10. **Escenarios como orden de magnitud, no pronóstico.** Sin intervención = 2021 + (2024 − 2018). Con intervención = campaña concentrada por banda con rendimiento **supuesto** +3/+2/+1; la banda sólo decide dónde se concentra, los puntos no están medidos ni los documenta la literatura, y la prioridad por riesgo se sostiene en el índice y su backtest, no en el escenario.

## 4. Cómo está construido (para el revisor técnico)

```
CSV originales INE (3.9 GB)  →  agrega_def24.py (+ crosswalk.py)  →  data/agregados/ccpc_AAAA_def24.csv
                                                                           ↓
                                         indice.py  →  outputs/ (índice, validación, sensibilidad, escenarios)
                                                                           ↓
                              exporta.py → CSV + GeoJSON      tablero.py → HTML autocontenido (docs/index.html)
                                                               laminas.py → PPTX
```

`./run.sh` reproduce todo en menos de dos minutos desde los agregados. `config.json` concentra todos los parámetros. Fórmulas, una por una, en `docs/METODOLOGIA.md`; columnas, en `docs/DICCIONARIO-DE-DATOS.md`. El esquema de base de datos para la fase 2 (Supabase, 7 esquemas) está en `db/migrations/0001_esquema_base.sql` con semillas en `db/seed/`, y la arquitectura completa en `docs/ARQUITECTURA-PLATAFORMA.md`.

## 5. Qué revisar, en orden

1. Clonar, `pip install -r requirements.txt`, `./run.sh`, `git status` limpio.
2. Las cifras del README contra `outputs/`: 45/60/89/106; 49.19/50.31; Spearman 0.367 / 0.044.
3. En `scripts/indice.py`: orientación de los nueve indicadores (más = más riesgo), percentil con empates promediados, pesos renormalizados, cortes por `rank`, backtest estimado sólo con elecciones ≤ 2018.
4. En el tablero: cambiar «pintar por» y ver que la leyenda del mapa cambia; abrir Veracruz 18 y comprobar R = 0.40×92 + 0.40×97 + 0.20×91 = 93.5.
5. Leer la sección 7 del reporte y confirmar que el escenario se presenta como supuesto y que la priorización no depende de él.

Si todo cuadra, la línea que avala la firma de las cartas es: «Revisado, reproducible, sin diferencias».
