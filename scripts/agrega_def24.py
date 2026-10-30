"""Paso 0 (opcional): agrega los archivos originales del CCPC (sección × sexo × edad) a distrito 2023 × sexo × grupo
de edad × tipo de sección, aplicando la tabla de equivalencias seccionales a los años 2009–2021.
Uso: python agrega_def24.py <carpeta_csv_del_año> <carpeta_salida> <año> data/crosswalk/seccion_a_def2024.csv
Los agregados resultantes ya vienen incluidos en data/agregados/, por lo que este paso sólo es necesario para reproducir desde cero."""
import sys, glob, os, pandas as pd
src, out, year = sys.argv[1], sys.argv[2], sys.argv[3]
cw = pd.read_csv(sys.argv[4])
files = sorted(glob.glob(os.path.join(src, "*.csv")))
bins = [17,19,24,29,39,49,59,69,200]
labels = ["18-19","20-24","25-29","30-39","40-49","50-59","60-69","70+"]
cols = ["LN","SV","NV","NS"]; store=[]; lost=0; tot=0
for f in files:
    df = pd.read_csv(f, low_memory=False, encoding="utf-8-sig")
    df.columns=[c.strip().upper() for c in df.columns]
    for c in cols: df[c]=pd.to_numeric(df[c],errors="coerce").fillna(0).astype("int64")
    df["GEDAD"]=pd.cut(pd.to_numeric(df["EDAD"],errors="coerce"),bins=bins,labels=labels)
    if year in ("2024","2025"):
        df["DEF2024"]=pd.to_numeric(df["DEF"],errors="coerce")   # estos archivos ya vienen en cartografía 2023
    else:
        df=df.merge(cw,on=["EDOCVE","SECCION"],how="left")
    tot+=df.LN.sum(); lost+=df.loc[df.DEF2024.isna(),"LN"].sum()
    df=df.dropna(subset=["DEF2024"]); df["DEF2024"]=df.DEF2024.astype(int)
    store.append(df.groupby(["AELEC","EDOCVE","DEF2024","SEXO","GEDAD","TIPOSEC"],observed=True)[cols].sum().reset_index())
pd.concat(store).groupby(["AELEC","EDOCVE","DEF2024","SEXO","GEDAD","TIPOSEC"],observed=True)[cols].sum().reset_index().to_csv(os.path.join(out,f"ccpc_{year}_def24.csv"),index=False)
print("OK",year,"LN sin distrito:",lost,"de",tot, round(lost/tot*100,3),"%")
