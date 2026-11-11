"""09 - Georreferenciação e vectorização de dois planos históricos (INPF 1985 Mapa 7; PEUMM 2008).

Entradas : dados/raw/planos/pimentel/fig_1985_*.png, fig_2008_*.png
           dados/proc/planos/gcp_1985.csv, gcp_2008.csv (tipo = controlo | verificacao)
Saídas   : dados/proc/planos/plano_1985_mapa7.tif, peumm_2008_ordenamento.tif (RGBA, EPSG:32736)
           dados/proc/planos/zonas_1985.gpkg, peumm_2008.gpkg
           dados/fig/planos/sobreposicao_1985_2008.png ; docs/qa/planos_georref.md
Os GCP são lidos dos CSV (a reprodução não depende de medição manual nova).
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from rasterio.transform import from_origin
from shapely.geometry import shape, box, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
from PIL import Image
import cv2
from scipy import ndimage as ndi
from skimage import morphology as mo
import warnings
import comum as c

warnings.filterwarnings("ignore")

PL = c.PROC / "planos"
IMG85 = c.RAW / "planos" / "pimentel" / "fig_1985_plano_estrutura_mapas7e8.png"
IMG08 = c.RAW / "planos" / "pimentel" / "fig_2008_peumm_planta_ordenamento_anexo.png"
# janela do mapa (pixels): 1985 = Mapa 7 (metade esquerda); 2008 = painel esquerdo (município + Catembe)
JAN85 = (23, 63, 427, 553)      # x0, y0, x1, y1
JAN08 = (214, 119, 1858, 2158)


# ---------------------------------------------------------------- modelos de transformação
def _A(px, py, grau, s):
    u, v = (np.asarray(px, float) - s[0]) / s[2], (np.asarray(py, float) - s[1]) / s[2]
    cols = [np.ones_like(u), u, v]
    if grau >= 2:
        cols += [u * v, u * u, v * v]
    return np.stack(cols, -1)


class Modelo:
    """Polinómio de grau 1 (afim) ou 2: (px,py) -> (x,y) e inverso (x,y) -> (px,py)."""
    def __init__(self, p, q, grau):
        p, q = np.asarray(p, float), np.asarray(q, float)
        self.grau = grau
        self.sp = (p[:, 0].mean(), p[:, 1].mean(), p.std() + 1e-9)
        self.sq = (q[:, 0].mean(), q[:, 1].mean(), q.std() + 1e-9)
        self.f = np.linalg.lstsq(_A(p[:, 0], p[:, 1], grau, self.sp), (q - np.array(self.sq[:2])) / self.sq[2], rcond=None)[0]
        self.i = np.linalg.lstsq(_A(q[:, 0], q[:, 1], grau, self.sq), (p - np.array(self.sp[:2])) / self.sp[2], rcond=None)[0]

    def fwd(self, px, py):
        r = _A(px, py, self.grau, self.sp) @ self.f * self.sq[2] + np.array(self.sq[:2])
        return r[..., 0], r[..., 1]

    def inv(self, x, y):
        r = _A(x, y, self.grau, self.sq) @ self.i * self.sp[2] + np.array(self.sp[:2])
        return r[..., 0], r[..., 1]


def rmse(m, d):
    if len(d) == 0:
        return float("nan")
    x, y = m.fwd(d.px.values, d.py.values)
    return float(np.sqrt(np.mean((x - d.x_utm36s.values) ** 2 + (y - d.y_utm36s.values) ** 2)))


def loo(d, grau):
    e = []
    for k in range(len(d)):
        dd = d.drop(d.index[k]); m = Modelo(dd[["px", "py"]], dd[["x_utm36s", "y_utm36s"]], grau)
        x, y = m.fwd(d.px.values[k], d.py.values[k])
        e.append((x - d.x_utm36s.values[k]) ** 2 + (y - d.y_utm36s.values[k]) ** 2)
    return float(np.sqrt(np.mean(e)))


def ajusta(csv, nome):
    d = pd.read_csv(csv)
    ctl, chk = d[d.tipo == "controlo"].reset_index(drop=True), d[d.tipo == "verificacao"].reset_index(drop=True)
    res = {}
    for g in (1, 2):
        m = Modelo(ctl[["px", "py"]], ctl[["x_utm36s", "y_utm36s"]], g)
        res[g] = dict(m=m, ctl=rmse(m, ctl), loo=loo(ctl, g), chk=rmse(m, chk))
    # escolha: afim, salvo se o grau 2 melhorar o RMSE de verificação em >15 % e o LOO não piorar
    g = 2 if (res[2]["chk"] < 0.85 * res[1]["chk"] and res[2]["loo"] <= res[1]["loo"]) else 1
    c.log(nome, {k: {a: round(b, 1) for a, b in v.items() if a != "m"} for k, v in res.items()}, "-> grau", g)
    return res[g]["m"], g, res, ctl, chk


# ---------------------------------------------------------------- raster georreferenciado
def grava_raster(img, m, janela, res, saida, nome):
    x0, y0, x1, y1 = janela
    cant = np.array([[x0, y0], [x1, y0], [x0, y1], [x1, y1]])
    X, Y = m.fwd(cant[:, 0], cant[:, 1])
    bx0, by0 = max(X.min(), c.X0), max(Y.min(), c.Y0)
    bx1, by1 = min(X.max(), c.X1), min(Y.max(), c.Y1)
    bx0, by0 = np.floor(bx0 / 30) * 30, np.floor(by0 / 30) * 30
    bx1, by1 = np.ceil(bx1 / 30) * 30, np.ceil(by1 / 30) * 30
    W, H = int((bx1 - bx0) / res), int((by1 - by0) / res)
    xs = bx0 + (np.arange(W) + .5) * res
    ys = by1 - (np.arange(H) + .5) * res
    gx, gy = np.meshgrid(xs, ys)
    px, py = m.inv(gx, gy)
    arr = np.asarray(img.convert("RGB"))
    out = cv2.remap(arr, px.astype("float32") - .5, py.astype("float32") - .5, cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    dentro = (px >= x0) & (px < x1) & (py >= y0) & (py < y1)
    alfa = (dentro * 255).astype("uint8")
    out[~dentro] = 0
    data = np.dstack([out, alfa]).transpose(2, 0, 1)
    with rasterio.open(saida, "w", driver="GTiff", height=H, width=W, count=4, dtype="uint8", crs=c.CRS,
                       transform=from_origin(bx0, by1, res, res), compress="deflate", photometric="RGB",
                       alpha="YES") as dst:
        dst.write(data)
        dst.update_tags(fonte=nome, resolucao_m=res)
    c.log("raster", saida.name, W, H)


# ---------------------------------------------------------------- vectorização
def poligonos_utm(mask, m, janela, simplif=5.0, min_ha=0.5, tol_ha=0.3):
    """Máscara (pixels da imagem original) -> GeoSeries em EPSG:32736 usando o modelo m."""
    x0, y0 = janela[0], janela[1]
    geoms = []
    for g, v in shapes(mask.astype("uint8"), mask=mask.astype(bool), connectivity=8):
        p = shape(g)
        def tr(ring):
            a = np.array(ring.coords)
            X, Y = m.fwd(a[:, 0] + x0, a[:, 1] + y0)
            return list(zip(X, Y))
        pp = Polygon(tr(p.exterior), [tr(i) for i in p.interiors if Polygon(tr(i)).area > tol_ha * 1e4])
        if not pp.is_valid:
            pp = pp.buffer(0)
        geoms.append(pp)
    gs = gpd.GeoSeries(geoms, crs=c.CRS)
    gs = gs[gs.area > min_ha * 1e4].simplify(simplif)
    return gs


def para_gdf(gs, **cols):
    gdf = gpd.GeoDataFrame(geometry=list(gs), crs=c.CRS)
    gdf["area_ha"] = gdf.area / 1e4
    for k, v in cols.items():
        gdf[k] = v
    return gdf


def recorta(gdf, poly):
    g = gdf.copy()
    g["geometry"] = g.geometry.intersection(poly)
    g = g[~g.geometry.is_empty].explode(index_parts=False)
    g["area_ha"] = g.area / 1e4
    return g[g.area_ha > 0.3].reset_index(drop=True)


# ---------------------------------------------------------------- 1985: classificação por textura
def _pequenos(mask, amax, lado):
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype("uint8"), connectivity=8)
    ok = np.zeros(n, bool)
    ok[1:] = (st[1:, 4] <= amax) & (st[1:, 2] <= lado) & (st[1:, 3] <= lado)
    return ok[lab]


def segmenta_1985(img, par):
    """Pontos (manchas compactas) escuros face ao fundo local; densidade -> zonas tracejadas.
    Legenda: Permanentes = pontos grossos e espaçados (forte contraste); Provisórias = pontilhado fino e denso."""
    x0, y0, x1, y1 = JAN85
    g = np.asarray(img.convert("L")).astype("float32")[y0:y1, x0:x1]
    mean = cv2.GaussianBlur(g, (0, 0), 2.5)
    rel = g - cv2.GaussianBlur(g, (0, 0), 8)
    # linhas (hachura vertical de Habitação, grelha, estradas): estruturas alongadas, removidas antes de contar pontos
    esc = (rel < par["t_fraco"]).astype("uint8")
    linhas = np.zeros_like(esc)
    for se in (cv2.getStructuringElement(cv2.MORPH_RECT, (1, 13)), cv2.getStructuringElement(cv2.MORPH_RECT, (13, 1))):
        linhas |= cv2.morphologyEx(esc, cv2.MORPH_OPEN, se)
    linhas = cv2.dilate(linhas, np.ones((5, 5), np.uint8)).astype(bool)
    forte = _pequenos(rel < par["t_forte"], 16, 5) & ~linhas       # pontos grossos
    qualquer = _pequenos(rel < par["t_fraco"], 16, 5) & ~linhas    # qualquer ponto
    dA = cv2.GaussianBlur(forte.astype("float32"), (0, 0), par["sig_dens"])
    dB = cv2.GaussianBlur(qualquer.astype("float32"), (0, 0), par["sig_dens"])
    rA = cv2.GaussianBlur(forte.astype("float32"), (0, 0), par["sig_razao"])
    rB = cv2.GaussianBlur(qualquer.astype("float32"), (0, 0), par["sig_razao"])
    ocup = mean < par["ocup_media"]
    ocup = mo.remove_small_objects(mo.closing(ocup, mo.disk(2)), max_size=40)
    ocup = mo.remove_small_holes(ocup, max_size=60)
    pontilhado = (dB > par["dens_min"]) & ~ocup
    permanente = pontilhado & (rA / (rB + 1e-6) > par["razao_perm"])
    provisoria = pontilhado & ~permanente
    out = {}
    for nome, mk, kc in (("zv_permanentes", permanente, 5), ("zv_provisorias", provisoria, 4)):
        mk = mo.closing(mk, mo.disk(kc))
        mk = mo.opening(mk, mo.disk(3))
        mk = mo.remove_small_holes(mk, max_size=150)
        mk = mo.remove_small_objects(mk, max_size=150)
        out[nome] = mk
    out["ocupacao_actual"] = ocup
    return out, (g, mean, dA, dB)


PAR85 = dict(ocup_media=182, t_forte=-45, t_fraco=-18, sig_dens=4.0, dens_min=0.011, razao_perm=0.12, sig_razao=5.0)


# ---------------------------------------------------------------- 2008: classificação por cor
COR08 = {  # RGB das amostras da legenda (lidas em (x=2592, y) da imagem original)
    "agropecuaria": (89, 116, 0),
    "expansao_urbana": (255, 148, 40),
    "urbanizavel_planificada": (255, 148, 111),
    "urbanizavel_nao_planificada": (255, 209, 163),
}
AMARELO = (255, 255, 0)


def classe_cor(a, cor, tol=10):
    return np.abs(a - np.array(cor)).max(axis=-1) <= tol


def segmenta_2008(img):
    x0, y0, x1, y1 = JAN08
    a = np.asarray(img.convert("RGB")).astype(int)[y0:y1, x0:x1]
    out = {}
    agro = classe_cor(a, COR08["agropecuaria"])
    agro = mo.closing(agro, mo.disk(3))
    out["agropecuaria"] = mo.remove_small_objects(mo.remove_small_holes(agro, max_size=60), max_size=20)
    lar = classe_cor(a, COR08["expansao_urbana"])
    borda = classe_cor(a, AMARELO, 40) & ndi.binary_dilation(lar, mo.disk(7))
    exp = mo.closing(lar | borda, mo.disk(3))
    out["expansao_urbana"] = mo.remove_small_objects(mo.remove_small_holes(exp, max_size=200), max_size=20)
    for k in ("urbanizavel_planificada", "urbanizavel_nao_planificada"):
        m = mo.closing(classe_cor(a, COR08[k], 12 if k.endswith("nao_planificada") else 8), mo.disk(2))
        out[k] = mo.remove_small_objects(m, max_size=20)
    fundo_mar = classe_cor(a, (237, 255, 250), 4)
    return out, fundo_mar


# ---------------------------------------------------------------- verificação independente: linha de costa vs 2020
def agua_2020():
    with rasterio.open(c.COMP / "2020.tif") as s:
        g, sw = s.read(2).astype("float32"), s.read(5).astype("float32")
        tr = s.transform
    ndw = (g - sw) / (g + sw + 1e-6)
    valido = np.isfinite(ndw)
    agua = valido & (ndw > 0)
    costa = valido & ndi.binary_dilation(agua, iterations=1) & ndi.binary_dilation(~agua & valido, iterations=1)
    dist = ndi.distance_transform_edt(~costa) * 30.0
    return dist, tr, valido


def verif_costeira(mar, m, janela, nome):
    """Distância (m) dos pixels de costa do plano (fronteira da máscara de mar/estuário) à costa 2020."""
    x0, y0 = janela[0], janela[1]
    mar = mo.closing(mar, mo.disk(6))                     # fecha linhas de grelha e tracejados
    mar = mo.remove_small_objects(mar, max_size=5000)
    cst = mar & ndi.binary_dilation(~mar, iterations=2)
    cst[:6] = cst[-6:] = False; cst[:, :6] = cst[:, -6:] = False
    yy, xx = np.nonzero(cst)
    X, Y = m.fwd(xx + x0, yy + y0)
    dist, tr, valido = agua_2020()
    col = ((X - tr.c) / tr.a).astype(int); lin = ((Y - tr.f) / tr.e).astype(int)
    ok = (col >= 0) & (col < dist.shape[1]) & (lin >= 0) & (lin < dist.shape[0])
    col, lin = col[ok], lin[ok]
    ok2 = valido[lin, col]
    # só onde há dados 2020 e fora dos limites do mapa/grelha
    d = dist[lin, col][ok2]
    d = d[d < 600]  # exclui feições que mudaram de natureza (ex. canais, planícies de maré)
    r = dict(n=int(len(d)), mediana=float(np.median(d)), p90=float(np.percentile(d, 90)), rmse=float(np.sqrt(np.mean(d ** 2))))
    c.log("costa", nome, {k: round(v, 1) for k, v in r.items()})
    return r


def verif_costeira_1985(tif):
    """Distância (m) da costa 2020 (pixels MNDWI) à tinta escura mais próxima do plano 1985 georreferenciado."""
    with rasterio.open(tif) as r:
        p, al, tp = r.read(1), r.read(4), r.transform
    tinta = (p < 175) & (al > 0)
    dt = ndi.distance_transform_edt(~tinta) * 30.0
    with rasterio.open(c.COMP / "2020.tif") as s:
        g, sw, ts = s.read(2).astype("float32"), s.read(5).astype("float32"), s.transform
    ndw = (g - sw) / (g + sw + 1e-6)
    agua = np.isfinite(ndw) & (ndw > 0)
    costa = np.isfinite(ndw) & ndi.binary_dilation(agua) & ndi.binary_dilation(np.isfinite(ndw) & ~agua)
    yy, xx = np.nonzero(costa)
    X, Y = ts.c + (xx + .5) * ts.a, ts.f + (yy + .5) * ts.e
    col, lin = ((X - tp.c) / tp.a).astype(int), ((Y - tp.f) / tp.e).astype(int)
    ok = (col >= 0) & (col < p.shape[1]) & (lin >= 0) & (lin < p.shape[0])
    ok &= (X < 466000) & (Y < 7137000)                      # costa de baía/estuário; exclui rios a norte e nuvens a leste
    ok[ok] = al[lin[ok], col[ok]] > 0
    d = dt[lin[ok], col[ok]]
    d = d[d < 600]
    r_ = dict(n=int(len(d)), mediana=float(np.median(d)), p90=float(np.percentile(d, 90)), rmse=float(np.sqrt(np.mean(d ** 2))))
    c.log("costa 1985", {k: round(v, 1) for k, v in r_.items()})
    return r_


def ha(g):
    return float(g.area.sum() / 1e4)


def main():
    PL.mkdir(parents=True, exist_ok=True)
    (c.FIG / "planos").mkdir(parents=True, exist_ok=True)
    c.QA.mkdir(parents=True, exist_ok=True)
    ver = os.environ.get("PLANOS_ETAPA", "tudo")
    lim = gpd.read_file(c.PROC / "limites.gpkg", layer="distritos")
    cidade = lim.geometry.union_all()
    bbox = box(*c.BOUNDS)
    resumo = {}

    # ---------------- 2008
    m8, g8, r8, ctl8, chk8 = ajusta(PL / "gcp_2008.csv", "2008")
    img8 = Image.open(IMG08)
    grava_raster(img8, m8, JAN08, 15, PL / "peumm_2008_ordenamento.tif", "PEUMM 2008 Planta de Ordenamento")
    cl8, mar8 = segmenta_2008(img8)
    costa8 = verif_costeira(mar8, m8, JAN08, "2008")
    lay8 = {}
    for k, mk in cl8.items():
        gs = poligonos_utm(mk, m8, JAN08, simplif=5.0, min_ha=0.5)
        lay8[k] = recorta(para_gdf(gs, classe=k), bbox)
    out8 = PL / "peumm_2008.gpkg"
    if out8.exists():
        out8.unlink()
    for k, g in lay8.items():
        g.to_file(out8, layer=k, driver="GPKG")
    resumo["2008"] = dict(grau=g8, rmse_controlo=r8[g8]["ctl"], rmse_loo=r8[g8]["loo"], rmse_verif=r8[g8]["chk"],
                          n_ctl=len(ctl8), n_chk=len(chk8), costa=costa8,
                          afim=dict(ctl=r8[1]["ctl"], loo=r8[1]["loo"], chk=r8[1]["chk"]),
                          poly2=dict(ctl=r8[2]["ctl"], loo=r8[2]["loo"], chk=r8[2]["chk"]),
                          areas_ha_mapa={k: ha(g) for k, g in lay8.items()},
                          areas_ha_cidade={k: ha(g.intersection(cidade)) for k, g in lay8.items()})

    # ---------------- 1985
    m5, g5, r5, ctl5, chk5 = ajusta(PL / "gcp_1985.csv", "1985")
    img5 = Image.open(IMG85)
    grava_raster(img5, m5, JAN85, 30, PL / "plano_1985_mapa7.tif", "INPF 1985 Plano de Estrutura Mapa 7")
    cl5, aux = segmenta_1985(img5, PAR85)
    # costa 1985: máscara branca contígua ao estuário/baía (sem textura, sem tinta) é ambígua; usa-se só a verificação por pontos
    lay5 = {}
    for k, mk in cl5.items():
        gs = poligonos_utm(mk, m5, JAN85, simplif=15.0, min_ha=2.0)
        lay5[k] = recorta(para_gdf(gs, classe=k), bbox)
    out5 = PL / "zonas_1985.gpkg"
    if out5.exists():
        out5.unlink()
    for k, g_ in lay5.items():
        g_.to_file(out5, layer=k, driver="GPKG")
    costa5 = verif_costeira_1985(PL / "plano_1985_mapa7.tif")
    resumo["1985"] = dict(costa=costa5, grau=g5, rmse_controlo=r5[g5]["ctl"], rmse_loo=r5[g5]["loo"], rmse_verif=r5[g5]["chk"],
                          n_ctl=len(ctl5), n_chk=len(chk5),
                          afim=dict(ctl=r5[1]["ctl"], loo=r5[1]["loo"], chk=r5[1]["chk"]),
                          poly2=dict(ctl=r5[2]["ctl"], loo=r5[2]["loo"], chk=r5[2]["chk"]),
                          areas_ha_mapa={k: ha(g_) for k, g_ in lay5.items()},
                          areas_ha_cidade={k: ha(g_.intersection(cidade)) for k, g_ in lay5.items()})
    (PL / "tmp").mkdir(exist_ok=True)
    json.dump(resumo, open(PL / "tmp" / "resumo.json", "w"), indent=1)
    c.log(json.dumps(resumo, indent=1))
    figura(lay5, lay8, lim)
    relatorio(resumo, ctl5, chk5, ctl8, chk8, m5, m8)


def figura(lay5, lay8, lim):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from ardosia_palette import apply_ardosia
    apply_ardosia()
    with rasterio.open(c.COMP / "2020.tif") as s:
        a = s.read([3, 2, 1]).astype("float32")
        ext = (s.bounds.left, s.bounds.right, s.bounds.bottom, s.bounds.top)
    rgb = np.clip((np.nan_to_num(a, nan=0.2) - 0.02) / 0.16, 0, 1).transpose(1, 2, 0)
    cores5 = {"zv_permanentes": "#2e7d32", "zv_provisorias": "#f9a825", "ocupacao_actual": "#6a1b9a"}
    cores8 = {"agropecuaria": "#2e7d32", "expansao_urbana": "#f57c00", "urbanizavel_planificada": "#6a1b9a"}
    fig, axs = plt.subplots(1, 2, figsize=(14, 8.5), constrained_layout=True)
    for ax, tit, lay, cores in ((axs[0], "Plano de Estrutura INPF 1985 (Mapa 7)", lay5, cores5), (axs[1], "PEUMM 2008 (Planta de Ordenamento)", lay8, cores8)):
        ax.imshow(rgb, extent=ext)
        for k, col in cores.items():
            lay[k].plot(ax=ax, facecolor=col, edgecolor=col, alpha=0.45, linewidth=0.3)
        lim.boundary.plot(ax=ax, color="white", linewidth=0.8)
        ax.set_xlim(445000, 472000); ax.set_ylim(7114500, 7141500)
        ax.set_title(tit, fontsize=11); ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
        ax.legend(handles=[Patch(facecolor=col, alpha=.6, label=k.replace("_", " ")) for k, col in cores.items()], loc="lower left", fontsize=8, framealpha=0.92)
    fig.suptitle("Planeado vs. composição Sentinel-2 2020 (cor verdadeira); limites distritais em branco", fontsize=11)
    fig.savefig(c.FIG / "planos" / "sobreposicao_1985_2008.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def relatorio(R, ctl5, chk5, ctl8, chk8, m5, m8):
    r5, r8 = R["1985"], R["2008"]
    lit_p, lit_v = 5230.0, 2575.0
    def linha(d):
        return f"| {d['grau']} | {d['rmse_controlo']:.1f} | {d['rmse_loo']:.1f} | {d['rmse_verif']:.1f} | {d['afim']['chk']:.1f} / {d['poly2']['chk']:.1f} |"
    a5m, a5c = r5["areas_ha_mapa"], r5["areas_ha_cidade"]
    a8m, a8c = r8["areas_ha_mapa"], r8["areas_ha_cidade"]
    md = f"""# Georreferenciação e vectorização dos planos 1985 e 2008

Script: `scripts/09_georref_planos.py` (reprodutível a partir de `dados/proc/planos/gcp_1985.csv` e `gcp_2008.csv`).

## Método
- **PEUMM 2008** (3306x2337 px): a planta traz grelha UTM (zona 36, datum Moznet ~ WGS84) rotulada de 2,5 em 2,5 km.
  36 cruzamentos de grelha (E 445-470 k, N 7115-7142,5 k) servem de controlo; posições das linhas medidas por
  centróide sub-pixel. Resolução ~15,8 m/pixel. Só o painel esquerdo (município + Catembe) é usado; o painel direito (Inhaca) fica fora da área.
- **INPF 1985, Mapa 7** (927x712 px; mapa em ~404x490 px, ~65 m/pixel): 9 cruzamentos da graticula (3 meridianos x 3 paralelos)
  convertidos de lon/lat para UTM 36S. Paralelos 25°50', 25°55', 26°00' S (rótulos lidos na imagem).
  **Meridianos**: no digitalizado os rótulos aparecem como 32°40', 32°45', 32°50' E, mas com essa leitura o mapa cai ~10 km a leste de Maputo
  (Baixa/Ponta Vermelha em lon ~32,59). A leitura 32°30', 32°35', 32°40' E (os rótulos de baixa resolução são ambíguos: 30/40, 35/45, 40/50)
  coloca a costa, o estuário e Catembe sobre a costa 2020 (ver QA). Adoptada a segunda; o deslocamento de 10' foi decidido por
  correspondência de feições, logo a escala e a rotação são verificadas independentemente, mas a origem em longitude não.
- Modelo: polinómio de grau 1 (afim) ou 2, escolhido pelo RMSE nos pontos de verificação (grau 2 só se melhorar >15 % e o LOO não piorar). Com 9 pontos de controlo
  o grau 2 ajusta-se quase exactamente (sobreajuste), por isso não é usado no 1985.
- Rasters RGBA (EPSG:32736): 2008 a 15 m, 1985 a 30 m (alinhados à grade do projecto).
- Vectorização em espaço de pixel (sem reamostragem) e transformação dos vértices pelo modelo; simplificação 5 m (2008) / 15 m (1985).

## RMSE (m)
| plano | grau | controlo | LOO controlo | verificação (landmarks) | afim / grau 2 (verif.) |
|---|---|---|---|---|---|
| 2008 (n_ctl={r8['n_ctl']}, n_chk={r8['n_chk']}) {linha(r8)}
| 1985 (n_ctl={r5['n_ctl']}, n_chk={r5['n_chk']}) {linha(r5)}

Verificação independente por linha de costa (distância à costa 2020, MNDWI Sentinel-2; a costa mudou 1985/2008-2020, logo é um limite superior do erro posicional):
- 2008: n={r8['costa']['n']}, mediana {r8['costa']['mediana']:.0f} m, p90 {r8['costa']['p90']:.0f} m, RMSE {r8['costa']['rmse']:.0f} m
- 1985: n={r5['costa']['n']}, mediana {r5['costa']['mediana']:.0f} m, p90 {r5['costa']['p90']:.0f} m, RMSE {r5['costa']['rmse']:.0f} m

Pontos de verificação: ver colunas `tipo=verificacao` nos CSV (2008: 3 pontos de costa lidos visualmente em recortes com grelha, incerteza de leitura ~20 m;
1985: 6 posições extraídas numericamente do raster do plano e da máscara de água 2020, quantizadas a 30 m).

## Áreas (ha)
| camada | no mapa (recortado à grade do projecto) | dentro dos 7 distritos de Maputo |
|---|---|---|
""" + "\n".join(f"| 1985 {k} | {v:,.0f} | {a5c[k]:,.0f} |" for k, v in a5m.items()) + "\n" + "\n".join(f"| 2008 {k} | {v:,.0f} | {a8c[k]:,.0f} |" for k, v in a8m.items()) + f"""

Literatura (Christie 1996 citando Roth et al., reportado): ZV permanentes 5 230 ha, provisórias 2 575 ha (razão perm/prov = {lit_p/lit_v:.2f}).
Medido: permanentes {a5m['zv_permanentes']:,.0f} ha (mapa) / {a5c['zv_permanentes']:,.0f} ha (cidade); provisórias {a5m['zv_provisorias']:,.0f} / {a5c['zv_provisorias']:,.0f} ha;
razão perm/prov = {a5m['zv_permanentes']/max(a5m['zv_provisorias'],1):.2f} (mapa) / {a5c['zv_permanentes']/max(a5c['zv_provisorias'],1):.2f} (cidade). Sem forçar concordância.

## Ressalvas
- **Legenda 1985**: no digitalizado, "Zonas Verdes Permanentes" tem pontos grossos e espaçados e "Zonas Verdes Provisórias" pontilhado fino e denso (o briefing indicava o inverso). Seguiu-se a legenda.
- A segmentação 1985 é por textura (densidade de manchas escuras compactas após remoção de linhas) em imagem de ~65 m/pixel: as fronteiras entre fino/grosso são difusas,
  o pontilhado fino de baixo contraste é subdetectado e zonas de Habitação (hachura vertical) vizinhas de pontilhado podem receber falsos positivos. Tratar as áreas como ordem de grandeza (incerteza facilmente >30 %).
- O Mapa 7 inclui território fora do município (Matola, Boane); a comparação com a literatura faz-se com o recorte aos 7 distritos e com o mapa inteiro, mas a definição espacial do valor da literatura é desconhecida.
- 2008: extracção por cor exacta da legenda (tolerância 8-12/255), fecho morfológico de 3 px; estradas, círculos hachurados de centros urbanos propostos e contornos amarelos fragmentam polígonos (subestimativa pequena).
  A borda amarela de "Área para Expansão Urbana" foi incorporada ao polígono. Os padrões hachurados sobre outras classes não são recuperados.
- Datum Moznet tratado como WGS84 (diferença sub-métrica a métrica). Imagens de terceiros: ver `CREDITOS.md`.
"""
    (c.QA / "planos_georref.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
