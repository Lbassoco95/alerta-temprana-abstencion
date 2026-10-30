"""
Alerta temprana de abstención — índice compuesto por distrito electoral federal.
Hackathon INE 2026 · Eje 2. Fuente única: Plataforma CCPC (datos abiertos DECEyEC).

Entrada : data/agregados/ccpc_{año}_def24.csv  (distrito 2023 × sexo × grupo de edad × tipo de sección)
Salida  : outputs/indice_distrital.csv, outputs/sensibilidad.csv, outputs/validacion_2025.json,
          outputs/escenarios.csv, outputs/series_distrital.csv
Config  : config.json (pesos, normalización, bandas)
"""
import json, glob, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json")))
OUT = os.path.join(ROOT, "outputs"); os.makedirs(OUT, exist_ok=True)
J = ["18-19", "20-24", "25-29"]            # jóvenes 18–29
C3039 = ["30-39"]                          # cohorte 18–29 de 2012 observada en 2024
ELEC = CFG["elecciones"]; PRES = CFG["presidenciales"]; HOLD = CFG["holdout"]

# ---------- 1. Carga y series por distrito ----------
raw = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(ROOT, "data/agregados/ccpc_*_def24.csv")))])
raw["id_def"] = raw.EDOCVE.astype(int).map("{:02d}".format) + "-" + raw.DEF2024.astype(int).map("{:02d}".format)

def part(df, mask=None):
    d = df if mask is None else df[mask]
    g = d.groupby(["id_def", "AELEC"])[["SV", "NV", "LN"]].sum()
    g["p"] = 100 * g.SV / (g.SV + g.NV)
    return g

tot = part(raw)
ser = tot[["p", "LN"]].rename(columns={"p": "p_total"})
ser["p_J"] = part(raw, raw.GEDAD.isin(J)).p
ser["p_A"] = part(raw, ~raw.GEDAD.isin(J)).p
ser["p_3039"] = part(raw, raw.GEDAD.isin(C3039)).p
ser["p_M"] = part(raw, raw.SEXO == 1).p
ser["p_H"] = part(raw, raw.SEXO == 0).p
ln = raw.groupby(["id_def", "AELEC"]).LN.sum()
ser["share_rural_mixto"] = 100 * raw[raw.TIPOSEC.isin(["R", "M"])].groupby(["id_def", "AELEC"]).LN.sum().reindex(ln.index).fillna(0) / ln
ser["share_LN_J"] = 100 * raw[raw.GEDAD.isin(J)].groupby(["id_def", "AELEC"]).LN.sum().reindex(ln.index).fillna(0) / ln
ser = ser.reset_index()
ser.to_csv(os.path.join(OUT, "series_distrital.csv"), index=False)

def indicadores(T, ser=ser):
    """Indicadores crudos con información hasta la presidencial T (todos orientados: más = más riesgo)."""
    elec = [y for y in ELEC if y <= T]; base = max(T - 12, min(elec)); prev = T - 6
    base_reb = base if (base - 3) in elec else base + 3
    W = ser[ser.AELEC.isin(elec)].pivot(index="id_def", columns="AELEC")
    def col(v, t): return W[(v, t)]
    def slope_resid(y_cols, years):
        t = np.array(years, dtype=float); t = t - t.mean()
        P = np.array([1.0 if y in PRES else 0.0 for y in years])
        X = np.column_stack([np.ones_like(t), t, P])
        Y = y_cols.values
        beta, *_ = np.linalg.lstsq(X, Y.T, rcond=None)
        resid = Y.T - X @ beta
        slope_resid.last = (beta, np.mean(years))
        return beta[1], resid.std(axis=0, ddof=1)
    ind = pd.DataFrame(index=W.index)
    bJ, _ = slope_resid(W["p_J"][elec], elec)
    ind["A1_desgaste_juvenil"] = -bJ
    ind["A2_brecha_generacional"] = (col("p_A", T) - col("p_J", T)) - (col("p_A", base) - col("p_J", base))
    r = col("p_3039", T) - col("p_J", base)
    ind["A3_retencion_cohorte"] = r.median() - r
    ind["B1_rebote_perdido"] = (col("p_total", base_reb) - col("p_total", base_reb - 3)) - (col("p_total", T) - col("p_total", T - 3))
    ind["B2_caida_adulta"] = col("p_A", prev) - col("p_A", T)
    bT, sd = slope_resid(W["p_total"][elec], elec)
    ind["B3_volatilidad"] = sd
    ind["C1_rural_mixto"] = col("share_rural_mixto", T)
    ind["C2_brecha_genero"] = (col("p_M", T) - col("p_H", T)).abs()
    ind["C3_peso_juvenil"] = col("share_LN_J", T)
    ind["LN_T"] = col("LN", T); ind["tendencia_total"] = bT
    beta, tm = slope_resid.last
    ind["mod_a"], ind["mod_b"], ind["mod_c"], ind["mod_tm"] = beta[0], beta[1], beta[2], tm
    return ind.dropna(), W, col

T = max(ELEC)
ind, W, col = indicadores(T)
ind["LN_2024"] = ind.LN_T

# ---------- 3. Normalización, agregación, bandas ----------
WI = CFG["pesos_indicadores"]; WC = CFG["pesos_componentes"]
IND = {"A": ["A1_desgaste_juvenil", "A2_brecha_generacional", "A3_retencion_cohorte"],
       "B": ["B1_rebote_perdido", "B2_caida_adulta", "B3_volatilidad"],
       "C": ["C1_rural_mixto", "C2_brecha_genero", "C3_peso_juvenil"]}

def normaliza(x, metodo):
    if metodo == "percentil": return 100 * x.rank(pct=True, method="average")
    if metodo == "minmax":    return 100 * (x - x.min()) / (x.max() - x.min())
    if metodo == "zscore":    return 100 / (1 + np.exp(-(x - x.mean()) / x.std()))  # logística para llevar a 0–100
    raise ValueError(metodo)

def calcula(ind, wi, wc, metodo="percentil", agreg="lineal"):
    N = pd.DataFrame({k: normaliza(ind[k], metodo) for comp in IND.values() for k in comp})
    comp = pd.DataFrame(index=ind.index)
    for c, ks in IND.items():
        ws = np.array([wi[k.split("_")[0]] for k in ks]); ws = ws / ws.sum()
        if agreg == "lineal": comp[c] = (N[ks] * ws).sum(axis=1)
        else: comp[c] = np.exp((np.log(N[ks].clip(lower=1)) * ws).sum(axis=1))
    wsc = np.array([wc[c] for c in "ABC"]); wsc = wsc / wsc.sum()
    if agreg == "lineal": R = (comp[["A", "B", "C"]] * wsc).sum(axis=1)
    else: R = np.exp((np.log(comp[["A", "B", "C"]].clip(lower=1)) * wsc).sum(axis=1))
    return N, comp, R

def bandas(R):
    q = CFG["bandas_cuantiles"]; n = len(R); orden = R.rank(ascending=False, method="first")
    cortes = {"rojo": q["rojo"] * n, "naranja": (q["rojo"] + q["naranja"]) * n,
              "amarillo": (q["rojo"] + q["naranja"] + q["amarillo"]) * n}
    return pd.Series(np.select([orden <= cortes["rojo"], orden <= cortes["naranja"], orden <= cortes["amarillo"]],
                               ["rojo", "naranja", "amarillo"], "verde"), index=R.index)

N, comp, R = calcula(ind, WI, WC, CFG["normalizacion"], CFG["agregacion"])
res = ind.join(N.add_prefix("pct_")).join(comp.rename(columns={"A": "A_habito", "B": "B_desafeccion", "C": "C_vulnerabilidad"}))
res["R"] = R; res["banda"] = bandas(R)
contrib = pd.DataFrame({c: comp[c] * WC[c] for c in "ABC"})
dom = contrib.idxmax(axis=1); share = contrib.max(axis=1) / contrib.sum(axis=1)
nombres = {"A": "habito", "B": "desafeccion", "C": "vulnerabilidad"}
res["mecanismo"] = np.where(share >= CFG["umbral_mecanismo"], dom.map(nombres), "mixto")
res["prioridad"] = R * ind.LN_2024 / ind.LN_2024.max()
res["rango_prioridad"] = res.prioridad.rank(ascending=False, method="first").astype(int)
for v in ["p_total", "p_J", "p_A", "p_M", "p_H"]:
    for t in [2012, 2018, 2021, 2024]: res[f"{v}_{t}"] = col(v, t)
res["EDOCVE"] = res.index.str[:2].astype(int); res["DEF"] = res.index.str[3:].astype(int)

# ---------- 4. Validación fuera de muestra ----------
def valida(res, target, indT):
    """sorpresa = participación que la trayectoria propia del distrito (tendencia + efecto presidencial,
    estimada sólo con datos previos) predecía para `target`, menos la observada. Se centra en la mediana
    nacional para aislar la caída relativa del distrito del choque común a todos."""
    h = ser[ser.AELEC == target].set_index("id_def").p_total.reindex(res.index); m = h.notna()
    esperado = indT.mod_a + indT.mod_b * (target - indT.mod_tm) + indT.mod_c * (1.0 if target in PRES else 0.0)
    res[f"p_total_{target}"] = h; res[f"esperado_{target}"] = esperado
    s = (esperado - h); res[f"sorpresa_{target}"] = s - s.median()
    s = res[f"sorpresa_{target}"]
    rho = res[["R", f"sorpresa_{target}"]].corr(method="spearman").iloc[0, 1]
    por_banda = res.groupby("banda")[f"sorpresa_{target}"].mean().reindex(["rojo", "naranja", "amarillo", "verde"])
    arriba = s > s.median()
    return {"objetivo": target, "spearman_R_sorpresa": round(float(rho), 3),
            "sorpresa_media_por_banda": {k: round(float(v), 2) for k, v in por_banda.items()},
            "monotonia_por_banda": bool(por_banda.is_monotonic_decreasing),
            "pct_rojos_con_sorpresa_sobre_mediana": round(float(arriba[res.banda == "rojo"].mean() * 100), 1),
            "pct_verdes_con_sorpresa_sobre_mediana": round(float(arriba[res.banda == "verde"].mean() * 100), 1),
            "spearman_por_componente": {c: round(float(res[[c, f"sorpresa_{target}"]].corr(method="spearman").iloc[0, 1]), 3)
                                        for c in ["A_habito", "B_desafeccion", "C_vulnerabilidad"]},
            "n_distritos": int(m.sum())}

val = {}
# 4a. Prueba de estrés con la elección judicial 2025 (hold-out)
if HOLD: val["holdout_2025"] = valida(res, HOLD[0], ind)
# 4b. Backtest: índice con información hasta 2018, contrastado con la intermedia 2021 (el caso de uso real: 2027)
ind18, W18, col18 = indicadores(2018)
N18, comp18, R18 = calcula(ind18, WI, WC, CFG["normalizacion"], CFG["agregacion"])
bt = comp18.rename(columns={"A": "A_habito", "B": "B_desafeccion", "C": "C_vulnerabilidad"}).copy()
bt["R"] = R18; bt["banda"] = bandas(R18); bt["p_total_2018"] = col18("p_total", 2018)
val["backtest_2018_a_2021"] = valida(bt, 2021, ind18)
bt.round(3).to_csv(os.path.join(OUT, "backtest_2018_2021.csv"))
json.dump(val, open(os.path.join(OUT, "validacion.json"), "w"), indent=2, ensure_ascii=False)

# ---------- 5. Sensibilidad ----------
base = res.banda; filas = []
def registra(nombre, Rv):
    bv = bandas(Rv); filas.append({"variante": nombre, "pct_cambia_banda": round(100 * (bv != base).mean(), 1),
                                   "pct_rojos_se_mantienen": round(100 * ((bv == "rojo") & (base == "rojo")).sum() / (base == "rojo").sum(), 1),
                                   "spearman_con_base": round(float(pd.Series(Rv).corr(R, method="spearman")), 3)})
S = CFG["sensibilidad"]; d = S["delta_pesos"]
for c in "ABC":
    for sgn in (+1, -1):
        wc = dict(WC); wc[c] = max(0.0, wc[c] + sgn * d)
        registra(f"peso_{c}{'+' if sgn > 0 else '-'}{d}", calcula(ind, WI, wc)[2])
registra("pesos_iguales", calcula(ind, {k: 1 for k in WI}, {c: 1 for c in WC})[2])
registra("minmax", calcula(ind, WI, WC, "minmax")[2])
registra("zscore", calcula(ind, WI, WC, "zscore")[2])
registra("geometrica", calcula(ind, WI, WC, "percentil", "geometrica")[2])
sens = pd.DataFrame(filas); sens.to_csv(os.path.join(OUT, "sensibilidad.csv"), index=False)

# ---------- 6. Escenarios 2027 (intermedia) ----------
# sin intervención: a la última intermedia (2021) se le aplica el cambio del distrito entre las dos últimas
# presidenciales (2018→2024), es decir, su impulso reciente de ciclo a ciclo
sin = (col("p_total", 2021) + (col("p_total", 2024) - col("p_total", 2018))).clip(5, 95)
E = CFG["escenarios"]["elasticidad_puntos"]
con = (sin + res.banda.map(E).fillna(0)).clip(5, 95)
esc = pd.DataFrame({"id_def": res.index, "banda": res.banda, "LN_2024": ind.LN_2024,
                    "p_2021": col("p_total", 2021), "p_2024": col("p_total", 2024),
                    "p_2027_sin_intervencion": sin.round(2), "p_2027_con_intervencion": con.round(2)})
esc.to_csv(os.path.join(OUT, "escenarios.csv"), index=False)
nac = {k: round(float((esc[k] * esc.LN_2024).sum() / esc.LN_2024.sum()), 2) for k in ["p_2021", "p_2024", "p_2027_sin_intervencion", "p_2027_con_intervencion"]}
json.dump(nac, open(os.path.join(OUT, "escenarios_nacional.json"), "w"), indent=2)

res.round(3).to_csv(os.path.join(OUT, "indice_distrital.csv"))
print("Distritos:", len(res)); print(res.banda.value_counts()); print(res.mecanismo.value_counts())
print("Validación:", json.dumps(val, indent=1, ensure_ascii=False)); print(sens.to_string(index=False)); print("Escenarios nacional:", nac)
