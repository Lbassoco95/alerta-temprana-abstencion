# Fundamentos matemáticos del índice

Este documento explica, paso a paso y con las fórmulas exactas, cómo se calcula cada número del semáforo. El criterio que lo guía es el del *Handbook on Constructing Composite Indicators* (OCDE y JRC, 2008): un índice compuesto es una cadena de decisiones (qué medir, cómo escalar, cómo pesar, cómo sumar, dónde cortar) y cada decisión debe estar escrita, justificada y sometida a prueba. Todo lo que sigue está implementado en `scripts/indice.py` y parametrizado en `config.json`.

## 1. Notación

* *d* = distrito electoral federal (300, cartografía 2023); *t* = elección federal, *t* ∈ {2009, 2012, 2015, 2018, 2021, 2024}; *P~t~* = 1 si *t* es presidencial (2012, 2018, 2024) y 0 si es intermedia.
* Para cada grupo *g* (total, 18–29, 30 y más, 30–39, mujeres, hombres): SV~d,t,g~ = personas con marca de voto; NV~d,t,g~ = personas sin marca; LN~d,t,g~ = lista nominal.
* **Participación:** *p~d,t,g~* = 100 · SV / (SV + NV). Es la misma definición que usa el INE en la plataforma CCPC; excluye los registros no especificados (NS).
* Se abrevia *p* = participación total, *p~J~* = 18–29, *p~A~* = 30 y más, *p~M~* = mujeres, *p~H~* = hombres.

## 2. La trayectoria propia de cada distrito (regresión)

Varios indicadores necesitan separar la tendencia de largo plazo del vaivén entre elecciones presidenciales e intermedias. Para eso se ajusta, **distrito por distrito**, una regresión lineal por mínimos cuadrados ordinarios con las seis elecciones:

> *y~t~* = *a* + *b*·(*t* − *t̄*) + *c*·*P~t~* + *e~t~*

donde *y* es la serie que se analice (*p* o *p~J~*), *t̄* es el año promedio (2016.5), *b* es la **pendiente** (puntos de participación por año, una vez descontado el efecto presidencial), *c* es el **efecto presidencial** (cuántos puntos más se vota en presidencial que en intermedia) y *e~t~* son los **residuos** (lo que la trayectoria no explica). Con seis observaciones y tres parámetros quedan tres grados de libertad; por eso los indicadores derivados se usan en percentil (posición relativa) y no en valor absoluto, y por eso se prueban en el análisis de sensibilidad.

## 3. Los nueve indicadores

Todos se construyen de modo que **un valor mayor signifique más riesgo**.

| | Indicador | Fórmula | Lectura |
|---|---|---|---|
| A1 | Desgaste juvenil | −*b~J~* (pendiente de *p~J~* con signo cambiado) | Cuántos puntos al año pierde la participación de 18–29 |
| A2 | Brecha generacional | (*p~A~* − *p~J~*)~2024~ − (*p~A~* − *p~J~*)~2012~ | Cuánto creció la distancia entre adultos y jóvenes |
| A3 | Retención de cohorte | mediana(*r*) − *r*, con *r~d~* = *p*~30–39, 2024~ − *p~J~*~, 2012~ | Quienes tenían 18–29 en 2012 tienen 30–41 en 2024; si votan menos que la mediana nacional de su cohorte, el hábito no cuajó |
| B1 | Rebote perdido | (*p*~2012~ − *p*~2009~) − (*p*~2024~ − *p*~2021~) | Cuánto menos "rebotó" el distrito en la última presidencial respecto a la de 2012 |
| B2 | Caída adulta | *p~A~*~, 2018~ − *p~A~*~, 2024~ | Cuántos puntos perdió el electorado de 30 y más entre presidenciales |
| B3 | Volatilidad | desviación estándar de los residuos *e~t~* de la regresión de *p* | Qué tan errática es la participación una vez descontada tendencia y ciclo |
| C1 | Peso rural y mixto | 100 · LN~rural+mixto, 2024~ / LN~2024~ | Porcentaje de la lista nominal en secciones rurales o mixtas |
| C2 | Brecha de género | \|*p~M~*~, 2024~ − *p~H~*~, 2024~\| | Distancia absoluta entre participación de mujeres y hombres |
| C3 | Peso juvenil | 100 · LN~18–29, 2024~ / LN~2024~ | Porcentaje de la lista nominal con 18–29 años |

## 4. Normalización: por qué percentiles

Los nueve indicadores están en unidades distintas (puntos por año, puntos porcentuales, porcentajes). Para sumarlos hay que llevarlos a una escala común. Se usa el **rango percentil**:

> *N~k,d~* = 100 · rango(*X~k,d~*) / *n*, con *n* = 300 y empates promediados

Un valor de 92 significa "este distrito está por encima del 92 % de los distritos en esa señal". El percentil tiene tres ventajas para este problema: es inmune a valores extremos (un distrito con un dato atípico no estira la escala de los demás), es comparable entre indicadores de naturaleza distinta y es directamente interpretable para quien no es especialista. Su costo es que pierde la distancia entre distritos (el 1.° y el 2.° quedan a la misma distancia que el 150.° y el 151.°); por eso se prueban dos alternativas que sí conservan distancias:

* **Min–max:** *N* = 100 · (*X* − mín) / (máx − mín).
* ***z* logística:** *N* = 100 / (1 + exp(−(*X* − media)/desv. est.)), una puntuación estándar llevada al intervalo 0–100.

## 5. Agregación: suma ponderada

Dentro de cada componente y entre componentes se usa una **media aritmética ponderada**:

> A = 0.30·N~A1~ + 0.30·N~A2~ + 0.40·N~A3~
> B = 0.45·N~B1~ + 0.35·N~B2~ + 0.20·N~B3~
> C = 0.40·N~C1~ + 0.35·N~C2~ + 0.25·N~C3~
> **R = 0.40·A + 0.40·B + 0.20·C**

Los pesos suman 1 en cada nivel y son **juicios de valor declarados**, no coeficientes estimados: expresan que el riesgo prevenible está en los procesos (hábito y desafección) más que en la estructura (vulnerabilidad), y que dentro de cada proceso la señal más directa pesa más (retención de cohorte en A; rebote perdido en B). La suma ponderada es **compensatoria**: un valor alto en una señal puede compensarse con uno bajo en otra. La alternativa no compensatoria es la **media geométrica ponderada**, R = A^0.40^ · B^0.40^ · C^0.20^, que castiga más los perfiles desbalanceados; se calcula en la sensibilidad para ver cuánto importa esa elección.

## 6. Bandas: cuantiles, no umbrales

El semáforo no usa un umbral fijo ("rojo si R > 70") sino **cuantiles**: se ordenan los 300 distritos por R y los primeros 15 % (45) son rojos, los siguientes 20 % (60) naranjas, los siguientes 30 % (89) amarillos y el 35 % restante (106) verdes. Con los datos actuales eso equivale a R ≥ 66.7 (rojo), R ≥ 55.7 (naranja) y R ≥ 42.8 (amarillo), pero esos valores son consecuencia del orden, no la regla. La razón es operativa: la capacidad de atención de las juntas distritales es finita y el instrumento debe producir siempre una lista de tamaño manejable, independientemente de cómo se mueva la distribución de R entre elecciones. Un distrito cambia de banda cuando su posición en la fila cruza un corte, ya sea porque sus indicadores cambian o porque cambian los de los demás.

## 7. Mecanismo dominante y prioridad

* **Contribución** de cada componente a R: *w~A~*·A, *w~B~*·B, *w~C~*·C. El **mecanismo dominante** es el componente con mayor contribución si ésta es al menos 40 % de R; si ninguno llega, el distrito es "mixto". Con tres componentes, 40 % garantiza que el dominante supera claramente al promedio (33 %).
* **Prioridad** = R · LN~d,2024~ / máx~d~(LN~d,2024~). Entre dos distritos con el mismo riesgo, primero el que tiene más personas. El rango de prioridad ordena los 300 por ese producto.

## 8. Escenarios 2027

* **Sin intervención:** *p̂*~d,2027~ = *p*~d,2021~ + (*p*~d,2024~ − *p*~d,2018~). Se parte de la última intermedia (2027 también lo es) y se aplica el cambio del distrito entre las dos últimas presidenciales: su impulso reciente de ciclo a ciclo. Se acota al intervalo [5, 95].
* **Con intervención:** *p̂*~d,2027~ + δ~banda~, con δ = 3 (rojo), 2 (naranja), 1 (amarillo), 0 (verde). δ es un **supuesto declarado** en `config.json`, en el rango bajo de la literatura experimental de movilización electoral (Gerber y Green: el contacto personal mueve varios puntos; el impersonal, casi nada).
* **Nacional:** promedio ponderado por lista nominal, Σ~d~ *p̂~d~*·LN~d~ / Σ~d~ LN~d~. Con 98.3 millones en lista nominal, un punto porcentual equivale a unas 983 mil personas.

## 9. Validación fuera de muestra

La pregunta es si el índice **anticipa** caídas que todavía no han ocurrido. Para no engañarse con el futuro ya conocido, el índice se recalcula con información truncada y se contrasta con lo que pasó después.

1. **Sorpresa.** Para cada distrito se estima la regresión de la sección 2 sólo con las elecciones anteriores al año de prueba *T*, se proyecta la participación esperada *p̂*~d,T~ = *a* + *b*·(*T* − *t̄*) + *c*·*P~T~* y se define la sorpresa *s~d~* = *p̂*~d,T~ − *p*~d,T~, centrada en su mediana nacional (*s~d~* − mediana(*s*)) para separar el choque común a todo el país de la caída relativa del distrito. Una sorpresa positiva significa que el distrito cayó más de lo que su trayectoria anticipaba.
2. **Correlación de Spearman** ρ entre R y *s*: mide si el orden de riesgo coincide con el orden de las caídas (ρ = 1 orden idéntico; 0 sin relación). Se usa Spearman y no Pearson porque R es una variable ordinal construida con percentiles.
3. **Monotonía por banda:** la sorpresa media debe decrecer de rojo a verde.
4. **Backtest 2018 → 2021.** Índice con datos hasta 2018 (cuatro elecciones), contrastado con la intermedia de 2021: ρ = 0.37; sorpresa media rojo +3.9, naranja +2.7, amarillo +1.6, verde −3.2; 75.6 % de los rojos y 28.3 % de los verdes por encima de la mediana.
5. **Prueba de estrés 2025.** Índice completo (hasta 2024) contra la elección judicial: ρ = 0.04. No anticipa ese evento, que respondió a movilización organizada y no al desgaste que mide el índice. Se reporta como límite de alcance.

## 10. Análisis de sensibilidad: qué es y cómo se hizo

Un índice compuesto depende de decisiones que otro analista razonable podría tomar distinto. El análisis de sensibilidad responde: **¿cuánto cambiarían los resultados si esas decisiones fueran otras?** El procedimiento fue:

1. Fijar **de antemano** el criterio de estabilidad: ante una perturbación de ±0.10 en el peso de cualquier componente, menos de 15 % de los distritos deben cambiar de banda.
2. Definir diez variantes: peso de A, B y C a +0.10 y −0.10 (seis variantes; los demás pesos se renormalizan para sumar 1); pesos iguales en todos los niveles; normalización min–max; normalización *z* logística; agregación geométrica.
3. Recalcular R y las bandas bajo cada variante **con los mismos datos** y medir tres cosas: el porcentaje de distritos que cambian de banda respecto al índice base; el porcentaje de los 45 rojos base que siguen siendo rojos; y la correlación de Spearman entre el R de la variante y el R base.
4. Resultado: las seis perturbaciones de pesos cambian la banda de entre 9.3 % y 13.3 % de los distritos (criterio cumplido) y conservan entre 93.3 % y 95.6 % de los rojos, con ρ ≥ 0.988. Las variantes estructurales mueven más: pesos iguales y agregación geométrica cambian 24.7 % de las bandas, min–max 14.0 % y *z* 10.7 %; aun así, los rojos se conservan entre 84.4 % y 91.1 % y ρ ≥ 0.914.
5. Lectura: la **lista de atención prioritaria (rojo) es robusta** a la forma de construir el índice; la **frontera amarillo–verde es la más sensible**, y así debe comunicarse. Que la agregación geométrica mueva más que las demás indica que una parte de los distritos tiene perfiles desbalanceados (muy alto en una causa y bajo en otra); el mecanismo dominante captura precisamente eso.

## 11. Datos faltantes y redistritación

* Las series están completas para los 300 distritos en las seis elecciones (298 en 2025); no se imputó ningún valor.
* Los archivos 2009–2021 refieren el distrito a la cartografía 2021 y los de 2024–2025 a la de 2023. Se construyó una tabla sección → distrito 2023 (74 002 secciones directas, 1 076 secciones divididas que heredan el distrito de sus hijas, 851 asignadas por el distrito 2023 más frecuente de su distrito 2018) y se reagregó toda la serie. La lista nominal no asignable fue de 0.085 % (2009), 0.077 % (2012), 0 % (2015, 2018), 0.004 % (2021) y 0 % (2024, 2025).

## 12. Qué no hace el índice

No estima probabilidades individuales (no hay datos individuales). No pronostica la participación absoluta de 2027: ordena distritos por riesgo relativo y cuantifica, bajo supuestos explícitos, cuánto se recuperaría con focalización. No incorpora variables externas al CCPC. No es válido para elecciones extraordinarias de naturaleza distinta a las federales ordinarias.
