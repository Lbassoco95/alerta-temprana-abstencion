# Datos originales (no incluidos en el repositorio)

Los archivos originales del CCPC pesan 3.9 GB y se descargan de la página de datos abiertos del INE:
https://ine.mx/transparencia/datos-abiertos/visualizacion-datos/conteos-censales-participacion/

| Archivo | Elección | Marco cartográfico del campo DEF |
|---|---|---|
| DatosAbiertos_DECEyEC_ConteosCensales2009.zip | Federal 2009 | DERFE 2021 |
| DatosAbiertos_DECEyEC_ConteosCensales2012.zip | Federal 2012 | DERFE 2021 |
| DatosAbiertos_DECEyEC_ConteosCensales2015.zip | Federal 2015 | DERFE 2021 |
| DatosAbiertos_DECEyEC_ConteosCensales2018.zip | Federal 2018 | DERFE 2021 |
| DatosAbiertos_DECEyEC_ConteosCensales2021.zip | Federal 2021 | DERFE 2021 |
| DatosAbiertos_DECEyEC_ConteosCensales2024.zip | Federal 2024 | DERFE 2023 |
| DatosAbiertos_DECEyEC_ConteosCensalesPJ2025.zip | Judicial 2025 | DERFE 2023 |

Cada ZIP contiene un CSV por entidad con las columnas `AELEC, FELECCION, EDOCVE, EDONOM, MPIOCVE, MPIONOM, SECCION, TIPOSEC, DEF, DEL, SEXO, EDAD, LN, SV, NV, NS` (el de 2025 sustituye DEL por `CJ, DEJ`). Descomprímalos en carpetas separadas y ejecute `scripts/agrega_def24.py` para cada año; los agregados resultantes son los que ya están en `data/agregados/`.
