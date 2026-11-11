"""Comparação das três estimativas da fração construída nos perímetros (revisão pós-auditoria).

(a) classificação bruta (dados/proc/class), (b) pós-processada (dados/proc/class_final),
(c) GHSL GHS-BUILT-S R2023A (fração de superfície construída, independente deste estudo).
Saída: dados/proc/areas/envelopes_comparacao.csv
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util
import numpy as np, pandas as pd, rasterio

spec = importlib.util.spec_from_file_location("env", Path(__file__).with_name("07b_envelopes.py"))
env = importlib.util.module_from_spec(spec); spec.loader.exec_module(env)
PROC = env.PROC

def main():
    import geopandas as gpd
    dem, tr, shp, crs = env.ler(PROC / "dem.tif"); tpi, *_ = env.ler(PROC / "tpi.tif")
    agua = None
    for e in env.EPOCAS:
        c, *_ = env.ler(PROC / "class_final" / f"{e}.tif")
        agua = (c == 6) if agua is None else agua & (c == 6)
    lim = gpd.read_file(PROC / "limites.gpkg", layer="distritos").to_crs(crs)
    lim = lim[~lim["adm2_name"].astype(str).str.contains("Nyaka", case=False)]
    cid = env.mascara(lim, tr, shp)
    per = {"baixada_<15m_tpi<0": (dem < 15) & (tpi < 0)}
    for lay, nome in [("zv_permanentes", "plano1985_zv_permanentes"), ("zv_provisorias", "plano1985_zv_provisorias")]:
        per[nome] = env.mascara(gpd.read_file(PROC / "planos/zonas_1985.gpkg", layer=lay).to_crs(crs), tr, shp)
    per["peumm2008_agropecuaria"] = env.mascara(gpd.read_file(PROC / "planos/peumm_2008.gpkg", layer="agropecuaria").to_crs(crs), tr, shp)
    per["cidade_total"] = np.ones(shp, bool)
    rows = []
    for e in env.EPOCAS:
        bruto, *_ = env.ler(PROC / "class" / f"{e}.tif")
        final, *_ = env.ler(PROC / "class_final" / f"{e}.tif")
        gp = PROC / "val" / f"ghsl_built_{min(2025, int(round(e / 5) * 5))}.tif"
        ghsl = env.ler(gp)[0].astype(float) / 10000.0 if gp.exists() else None
        for nome, pm in per.items():
            m = pm & cid & ~agua & (final > 0)
            n = m.sum()
            rows.append(dict(perimetro=nome, epoca=e, area_ha=round(n * env.PIX_HA, 1),
                             pct_bruto=round(100 * (m & (bruto == 1)).sum() / n, 2),
                             pct_final=round(100 * (m & (final == 1)).sum() / n, 2),
                             ghsl_epoca=gp.stem.split("_")[-1] if ghsl is not None else None,
                             pct_ghsl=round(100 * np.clip(ghsl[m], 0, 1).mean(), 2) if ghsl is not None else None,
                             ha_bruto=round((m & (bruto == 1)).sum() * env.PIX_HA, 1),
                             ha_final=round((m & (final == 1)).sum() * env.PIX_HA, 1),
                             ha_ghsl=round(np.clip(ghsl[m], 0, 1).sum() * env.PIX_HA, 1) if ghsl is not None else None))
    out = PROC / "areas" / "envelopes_comparacao.csv"
    pd.DataFrame(rows).to_csv(out, index=False); print(out)

if __name__ == "__main__":
    main()
