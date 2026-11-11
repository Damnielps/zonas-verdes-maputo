"""Definições comuns: grade de trabalho (EPSG:32736, 30 m), caminhos e funções auxiliares."""
import math
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds
from pyproj import Transformer

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "dados" / "raw"
PROC = RAIZ / "dados" / "proc"
COMP = PROC / "comp"
IDX = COMP / "indices"
VAL = PROC / "val"
FIG = RAIZ / "dados" / "fig"
QA = RAIZ / "docs" / "qa"

UA = "Mozilla/5.0 (compatible; zonas-verdes-research/1.0)"
HEADERS = {"User-Agent": UA}

CRS = "EPSG:32736"
RES = 30.0
LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = 32.40, 32.75, -26.10, -25.75
BBOX_LL = (LON_MIN, LAT_MIN, LON_MAX, LAT_MAX)

EPOCAS = [1979, 1985, 1990, 1995, 1997, 2000, 2005, 2007, 2010, 2015, 2017, 2020, 2025, 2026]
BANDAS = ["blue", "green", "red", "nir", "swir1", "swir2", "smad", "emad", "bcmad", "count"]


def _grade():
    t = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    xs, ys = [], []
    n = 50
    for i in range(n + 1):
        f = i / n
        lon = LON_MIN + f * (LON_MAX - LON_MIN)
        lat = LAT_MIN + f * (LAT_MAX - LAT_MIN)
        for p in ((lon, LAT_MIN), (lon, LAT_MAX), (LON_MIN, lat), (LON_MAX, lat)):
            x, y = t.transform(*p)
            xs.append(x); ys.append(y)
    x0 = math.floor(min(xs) / RES) * RES
    x1 = math.ceil(max(xs) / RES) * RES
    y0 = math.floor(min(ys) / RES) * RES
    y1 = math.ceil(max(ys) / RES) * RES
    return x0, y0, x1, y1


X0, Y0, X1, Y1 = _grade()
BOUNDS = (X0, Y0, X1, Y1)
WIDTH = int(round((X1 - X0) / RES))
HEIGHT = int(round((Y1 - Y0) / RES))
TRANSFORM = from_origin(X0, Y1, RES, RES)
SHAPE = (HEIGHT, WIDTH)


def perfil(count=1, dtype="float32", nodata=np.nan, **kw):
    p = dict(driver="GTiff", height=HEIGHT, width=WIDTH, count=count, dtype=dtype,
             crs=CRS, transform=TRANSFORM, nodata=nodata, compress="deflate",
             tiled=True, blockxsize=256, blockysize=256)
    p.update(kw)
    return p


def ll_para_utm(lon, lat):
    return Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform(lon, lat)


def bbox_em(crs, margem=0.0):
    """Bounds da grade (com margem em m) transformadas para outro CRS (envelope)."""
    t = Transformer.from_crs(CRS, crs, always_xy=True)
    m = margem
    pts = [(X0 - m, Y0 - m), (X1 + m, Y0 - m), (X0 - m, Y1 + m), (X1 + m, Y1 + m),
           ((X0 + X1) / 2, Y0 - m), ((X0 + X1) / 2, Y1 + m), (X0 - m, (Y0 + Y1) / 2), (X1 + m, (Y0 + Y1) / 2)]
    xs, ys = zip(*[t.transform(*p) for p in pts])
    return min(xs), min(ys), max(xs), max(ys)


def para_grade(src, band=1, resampling=Resampling.bilinear, dtype="float32", src_nodata=None,
               dst_nodata=np.nan, margem=600.0):
    """Lê uma banda de um dataset rasterio aberto (janela do bbox + margem) e reprojeta para a grade."""
    from rasterio.windows import Window
    b = bbox_em(src.crs, margem)
    w = from_bounds(*b, transform=src.transform)
    w = w.round_offsets(op="floor").round_lengths(op="ceil")
    w = w.intersection(Window(0, 0, src.width, src.height))
    arr = src.read(band, window=w, boundless=False)
    tr = src.window_transform(w)
    nd = src.nodata if src_nodata is None else src_nodata
    dst = np.full(SHAPE, dst_nodata, dtype=dtype)
    reproject(arr, dst, src_transform=tr, src_crs=src.crs, dst_transform=TRANSFORM, dst_crs=CRS,
              resampling=resampling, src_nodata=nd, dst_nodata=dst_nodata)
    return dst


def array_para_grade(arr, src_transform, src_crs, resampling=Resampling.bilinear, src_nodata=None,
                     dtype="float32", dst_nodata=np.nan):
    dst = np.full(SHAPE, dst_nodata, dtype=dtype)
    reproject(arr, dst, src_transform=src_transform, src_crs=src_crs, dst_transform=TRANSFORM,
              dst_crs=CRS, resampling=resampling, src_nodata=src_nodata, dst_nodata=dst_nodata)
    return dst


def grava(path, arr, descricoes=None, tags=None, **kw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if arr.ndim == 2:
        arr = arr[None]
    p = perfil(count=arr.shape[0], dtype=str(arr.dtype), **kw)
    tmp = path.with_suffix(".tmp.tif")
    with rasterio.open(tmp, "w", **p) as dst:
        dst.write(arr)
        if descricoes:
            for i, d in enumerate(descricoes, 1):
                dst.set_band_description(i, d)
        if tags:
            dst.update_tags(**{k: str(v) for k, v in tags.items()})
    tmp.replace(path)


def integro(path):
    try:
        with rasterio.open(path) as s:
            return s.width == WIDTH and s.height == HEIGHT and s.crs.to_string() == CRS
    except Exception:
        return False


def log(*a):
    print(*a, file=sys.stderr if False else sys.stdout, flush=True)


def http_get(url, **kw):
    import requests
    kw.setdefault("headers", HEADERS)
    kw.setdefault("timeout", 120)
    r = requests.get(url, **kw)
    r.raise_for_status()
    return r
