"""Ocupação por construção de perímetros independentes da classificação agrícola.

A validação cega de 2020 mostrou que a classe 1 (construído) é confiável (exatidão do usuário e
do produtor ~0,87–0,88), mas que a classe 2 (zonas verdes) se confunde com vegetação não
cultivada. Por isso a métrica central do artigo mede a classe validada (construído) dentro de
perímetros definidos sem a classificação agrícola:

- baixada: altitude < 15 m e TPI < 0 (Copernicus DEM), excluída a água permanente;
- zonas verdes permanentes e provisórias do Plano de Estrutura de 1985 (georreferenciadas);
- "Área de Agro-Pecuária" do PEUMM 2008 (georreferenciada).

Saída: dados/proc/areas/envelopes.csv (perimetro, ambito, epoca, area_ha, construido_ha, pct).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "proc"
EPOCAS = [1985, 1990, 1995, 1997, 2000, 2005, 2007, 2010, 2015, 2017, 2020, 2025, 2026]
PIX_HA = 30 * 30 / 10_000


def ler(p):
    with rasterio.open(p) as r:
        return r.read(1), r.transform, r.shape, r.crs


def mascara(gdf, transform, shape):
    if gdf is None or gdf.empty:
        return np.zeros(shape, bool)
    return rasterize(((g, 1) for g in gdf.geometry if g is not None and not g.is_empty),
                     out_shape=shape, transform=transform, fill=0, dtype="uint8").astype(bool)


def main():
    dem, transform, shape, crs = ler(PROC / "dem.tif")
    tpi, *_ = ler(PROC / "tpi.tif")
    agua = np.zeros(shape, bool)
    for e in EPOCAS:  # água permanente: água em todas as épocas
        c, *_ = ler(PROC / "class_final" / f"{e}.tif")
        agua = (c == 6) if e == EPOCAS[0] else (agua & (c == 6))

    lim = gpd.read_file(PROC / "limites.gpkg", layer="distritos").to_crs(crs)
    col = next((k for k in lim.columns if k.lower().startswith("adm2_pt") or k.lower() == "adm2_name"), None)
    if col is not None:
        lim = lim[~lim[col].astype(str).str.contains("Nyaka", case=False)]
    cidade = mascara(lim, transform, shape)
    ambitos = {"bbox": np.ones(shape, bool), "cidade": cidade}

    perimetros = {"baixada_<15m_tpi<0": (dem < 15) & (tpi < 0) & ~agua}
    z85 = PROC / "planos" / "zonas_1985.gpkg"
    for lay, nome in [("zv_permanentes", "plano1985_zv_permanentes"),
                      ("zv_provisorias", "plano1985_zv_provisorias")]:
        perimetros[nome] = mascara(gpd.read_file(z85, layer=lay).to_crs(crs), transform, shape) & ~agua
    p08 = PROC / "planos" / "peumm_2008.gpkg"
    perimetros["peumm2008_agropecuaria"] = mascara(
        gpd.read_file(p08, layer="agropecuaria").to_crs(crs), transform, shape) & ~agua

    linhas = []
    for e in EPOCAS:
        c, *_ = ler(PROC / "class_final" / f"{e}.tif")
        for pnome, pm in perimetros.items():
            for anome, am in ambitos.items():
                m = pm & am & (c > 0)
                area = m.sum() * PIX_HA
                cons = (m & (c == 1)).sum() * PIX_HA
                zv = (m & (c == 2)).sum() * PIX_HA
                linhas.append(dict(perimetro=pnome, ambito=anome, epoca=e, area_ha=round(area, 1),
                                   construido_ha=round(cons, 1),
                                   pct_construido=round(100 * cons / area, 2) if area else None,
                                   classe2_ha=round(zv, 1)))
    out = PROC / "areas" / "envelopes.csv"
    pd.DataFrame(linhas).to_csv(out, index=False)
    print(out)


if __name__ == "__main__":
    main()
