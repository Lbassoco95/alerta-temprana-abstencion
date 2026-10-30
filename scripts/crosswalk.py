"""Construye data/crosswalk/seccion_a_def2024.csv a partir de la tabla de equivalencias seccionales de Magar (2019/2026).
Regla: (1) distrito 2024 directo de la tabla; (2) secciones divididas en 2022–2023 heredan el distrito de sus hijas;
(3) residuales: distrito 2024 más frecuente entre las secciones de su mismo distrito 2018."""
import pandas as pd, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
e = pd.read_csv(os.path.join(ROOT, "data/crosswalk/tablaEquivalenciasSeccionalesDesde1994.csv"), low_memory=False)
e = e[['edon','seccion','alta','baja','dis2018','dis2024','action','orig.dest','when']].copy()
e['dis2024'] = e.dis2024.fillna(0).astype(int); e['dis2018'] = e.dis2018.fillna(0).astype(int)
key = e.set_index(['edon','seccion'])['dis2024'].to_dict()
def children(r):
    out = []
    for part in str(r['orig.dest']).split(';'):
        part = part.strip()
        if ':' in part:
            a, b = part.split(':')
            try: out += list(range(int(a), int(b) + 1))
            except ValueError: pass
        elif part.isdigit(): out.append(int(part))
    return out
res, src = [], []
for _, r in e.iterrows():
    d, s = r.dis2024, 'directo'
    if d == 0 and r.action == 'split.to':
        ch = [key.get((r.edon, c), 0) for c in children(r)]; ch = [c for c in ch if c > 0]
        if ch: d = max(set(ch), key=ch.count); s = 'hijas'
    res.append(d); src.append(s)
e['def2024'] = res; e['fuente'] = src
maj = e[e.def2024 > 0].groupby('dis2018').def2024.agg(lambda x: x.value_counts().index[0]).to_dict()
m = (e.def2024 == 0) & (e.dis2018 > 0)
e.loc[m, 'def2024'] = e.loc[m, 'dis2018'].map(maj).fillna(0).astype(int); e.loc[m, 'fuente'] = 'mayoria_dis2018'
out = e[e.def2024 > 0].rename(columns={'edon': 'EDOCVE', 'seccion': 'SECCION'})
out['DEF2024'] = out.def2024 % 100
out[['EDOCVE', 'SECCION', 'DEF2024', 'fuente']].to_csv(os.path.join(ROOT, 'data/crosswalk/seccion_a_def2024.csv'), index=False)
print(e.fuente.value_counts())
