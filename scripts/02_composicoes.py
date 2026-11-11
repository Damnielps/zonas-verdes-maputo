"""02 - Composições multibanda por época (30 m, EPSG:32736, reflectância 0-1) + índices. Idempotente.

Fontes: GeoMAD anual do Digital Earth Africa (tile x213y043), Landsat C2 L2 (Planetary Computer)
para substituições, 2026 e Landsat MSS C2 L1 para 1979.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rasterio
import requests
import pystac_client
import planetary_computer as pc
from rasterio.warp import Resampling
from shapely.geometry import box, shape
import comum as c

DEA_STAC = "https://explorer.digitalearth.africa/stac/search"
PC_STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
TILE = "x213y043"
ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="6", GDAL_HTTP_RETRY_DELAY="3",
           CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF", GDAL_HTTP_USERAGENT=c.UA,
           GDAL_HTTP_TIMEOUT="120", GDAL_HTTP_MULTIRANGE="YES")

# mapeamento de bandas GeoMAD -> nomes harmonizados
MAPA_LS57 = {"blue": "SR_B1", "green": "SR_B2", "red": "SR_B3", "nir": "SR_B4", "swir1": "SR_B5", "swir2": "SR_B7"}
MAPA_LS89 = {"blue": "SR_B2", "green": "SR_B3", "red": "SR_B4", "nir": "SR_B5", "swir1": "SR_B6", "swir2": "SR_B7"}
GEOMAD_ESCALA = 1e-4  # DEA GeoMAD: SR em 0-10000 (conferido: mediana vermelho ~900 = 0,09)

# substituições PC para 1985 e 2010
CENA_1985 = "LT05_L2SP_167078_19840601"
CENAS_2010 = ["LT05_L2SP_167078_20080907", "LT05_L2SP_167078_20110409"]


def colecao_geomad(ano):
    if ano <= 2012:
        return "gm_ls5_ls7_annual", MAPA_LS57, "Landsat 5/7 TM/ETM+"
    if ano <= 2020:
        return "gm_ls8_annual", MAPA_LS89, "Landsat 8 OLI"
    return "gm_ls8_ls9_annual", MAPA_LS89, "Landsat 8/9 OLI"


def https(href):
    return href.replace("s3://deafrica-services/", "https://deafrica-services.s3.af-south-1.amazonaws.com/")


def geomad(ano):
    col, mapa, sensor = colecao_geomad(ano)
    r = requests.post(DEA_STAC, json={"collections": [col], "bbox": list(c.BBOX_LL),
                                      "datetime": f"{ano}-01-01/{ano}-12-31", "limit": 10},
                      headers=c.HEADERS, timeout=60)
    r.raise_for_status()
    feats = r.json()["features"]
    feats = [f for f in feats if f["properties"].get("odc:region_code") == TILE]
    assert feats, f"sem item GeoMAD {col} {ano}"
    a = feats[0]["assets"]
    out = {}
    for nome, k in mapa.items():
        with rasterio.open(https(a[k]["href"])) as s:
            arr = c.para_grade(s, resampling=Resampling.bilinear, src_nodata=0)
        out[nome] = arr * GEOMAD_ESCALA
    for nome in ("SMAD", "EMAD", "BCMAD"):
        with rasterio.open(https(a[nome]["href"])) as s:
            out[nome.lower()] = c.para_grade(s, resampling=Resampling.bilinear)
    with rasterio.open(https(a["COUNT"]["href"])) as s:
        cnt = c.para_grade(s, resampling=Resampling.nearest)
    ok = np.isfinite(out["red"])
    out["count"] = np.where(ok, cnt, np.nan).astype("float32")
    stack = np.stack([out[b] for b in c.BANDAS]).astype("float32")
    med_cnt_all = float(np.nanmedian(cnt))
    meta = dict(fonte=f"Digital Earth Africa {col} v1.0.0 tile {TILE}", sensor=sensor,
                datas=f"{ano}-01-01/{ano}-12-31", item=feats[0]["id"],
                count_mediana_bbox_todos=med_cnt_all)
    return stack, meta


# ---------------- Landsat C2 L2 (Planetary Computer) ----------------
_cat = None


def catalogo():
    global _cat
    if _cat is None:
        _cat = pystac_client.Client.open(PC_STAC, modifier=pc.sign_inplace)
    return _cat


def busca_item_l2(prefixo):
    """prefixo tipo LT05_L2SP_167078_19840601 -> item PC."""
    d = prefixo.split("_")[-1]
    data = f"{d[:4]}-{d[4:6]}-{d[6:]}"
    res = catalogo().search(collections=["landsat-c2-l2"], bbox=list(c.BBOX_LL), datetime=f"{data}/{data}",
                            max_items=20).item_collection()
    for it in res:
        if it.id.startswith(prefixo):
            return it
    raise RuntimeError(f"item {prefixo} não encontrado no PC")


def bandas_l2(item):
    p = item.properties["platform"]
    mapa = {"blue": "blue", "green": "green", "red": "red", "nir": "nir08", "swir1": "swir16", "swir2": "swir22"}
    return mapa


def le_cena_l2(item):
    """Retorna dict banda->array reflectância (NaN mascarado por QA_PIXEL) e fração de máscara."""
    mapa = bandas_l2(item)
    with rasterio.open(item.assets["qa_pixel"].href) as s:
        qa = c.para_grade(s, resampling=Resampling.nearest, dtype="float32", src_nodata=None, dst_nodata=1)
    qa = np.nan_to_num(qa, nan=1).astype("uint16")
    # bits: 0 fill, 1 dilated cloud, 2 cirrus, 3 cloud, 4 shadow
    ruim = (qa & 0b11111) != 0
    out = {}
    for nome, asset in mapa.items():
        with rasterio.open(item.assets[asset].href) as s:
            dn = c.para_grade(s, resampling=Resampling.bilinear, src_nodata=0)
        refl = dn * 0.0000275 - 0.2
        refl = np.where(ruim, np.nan, refl)
        refl = np.where((refl < -0.05) | (refl > 1.0), np.nan, refl)
        out[nome] = np.clip(refl, 0, 1).astype("float32")
    # qualquer banda NaN invalida todas
    inval = ~np.all([np.isfinite(out[b]) for b in out], axis=0)
    for b in out:
        out[b][inval] = np.nan
    return out, float(ruim.mean())


def nuvem_bbox(item):
    with rasterio.open(item.assets["qa_pixel"].href) as s:
        qa = c.para_grade(s, resampling=Resampling.nearest, dtype="float32", dst_nodata=1)
    qa = np.nan_to_num(qa, nan=1).astype("uint16")
    return float(((qa & 0b11111) != 0).mean())


def empilha(d, count, extras=None):
    n = np.full(c.SHAPE, np.nan, "float32")
    lista = []
    for b in c.BANDAS:
        if b in ("blue", "green", "red", "nir", "swir1", "swir2"):
            lista.append(d[b])
        elif b == "count":
            lista.append(count.astype("float32"))
        else:
            lista.append(n)
    return np.stack(lista).astype("float32")


def cena_unica(prefixo):
    item = busca_item_l2(prefixo)
    d, frac = le_cena_l2(item)
    ok = np.isfinite(d["red"])
    cnt = np.where(ok, 1.0, np.nan)
    meta = dict(fonte=f"Planetary Computer landsat-c2-l2 {item.id}", sensor=item.properties["platform"],
                datas=item.datetime.strftime("%Y-%m-%d"), item=item.id, mascara_nuvem_sombra_frac=round(frac, 4))
    return empilha(d, cnt), meta


def composicao_2026():
    res = catalogo().search(collections=["landsat-c2-l2"], bbox=list(c.BBOX_LL),
                            datetime="2026-05-01/2026-09-30",
                            query={"landsat:wrs_path": {"eq": "167"}, "landsat:wrs_row": {"eq": "078"},
                                   "eo:cloud_cover": {"lt": 30}, "platform": {"in": ["landsat-8", "landsat-9"]}},
                            max_items=60).item_collection()
    itens = sorted(res, key=lambda i: i.datetime)
    c.log("  2026: cenas candidatas", [i.id for i in itens])
    assert itens, "sem cenas 2026"
    pilhas = {b: [] for b in ("blue", "green", "red", "nir", "swir1", "swir2")}
    usadas = []
    for it in itens:
        d, frac = le_cena_l2(it)
        if np.isfinite(d["red"]).mean() < 0.2:
            c.log("  2026: descartada (quase tudo mascarado)", it.id, round(frac, 3))
            continue
        for b in pilhas:
            pilhas[b].append(d[b])
        usadas.append(it)
    med = {b: np.nanmedian(np.stack(v), axis=0).astype("float32") for b, v in pilhas.items()}
    cnt = np.isfinite(np.stack(pilhas["red"])).sum(axis=0).astype("float32")
    cnt = np.where(cnt == 0, np.nan, cnt)
    datas = [i.datetime.strftime("%Y-%m-%d") for i in usadas]
    meta = dict(fonte="Planetary Computer landsat-c2-l2, mediana estação seca (mai-set 2026), p167 r078, nuvem<30%, QA_PIXEL",
                sensor="Landsat 8/9 OLI", datas=f"{min(datas)}/{max(datas)}", item=",".join(i.id for i in usadas),
                n_cenas=len(usadas))
    return empilha(med, cnt), meta


# ---------------- MSS 1979 ----------------
MSS_ITEM = "LM03_L1TP_179078_19790609_02_T2"


def mss_1979():
    res = catalogo().search(collections=["landsat-c2-l1"], ids=[MSS_ITEM]).item_collection()
    item = res[0]
    mtl = requests.get(item.assets["mtl.json"].href, timeout=60).json()["LANDSAT_METADATA_FILE"]
    sun = float(mtl["IMAGE_ATTRIBUTES"]["SUN_ELEVATION"])
    rs = mtl["LEVEL1_RADIOMETRIC_RESCALING"]
    # Landsat 3 MSS: B4 verde 0,5-0,6; B5 vermelho 0,6-0,7; B6 NIR 0,7-0,8; B7 NIR 0,8-1,1 um
    escolha = {"green": ("green", 4), "red": ("red", 5), "nir": ("nir09", 7)}
    saida = {}
    for nome, (asset, n) in escolha.items():
        m = float(rs[f"REFLECTANCE_MULT_BAND_{n}"]); a = float(rs[f"REFLECTANCE_ADD_BAND_{n}"])
        with rasterio.open(item.assets[asset].href) as s:
            dn = c.para_grade(s, resampling=Resampling.bilinear, src_nodata=0)
        refl = (m * dn + a) / np.sin(np.deg2rad(sun))
        saida[nome] = np.clip(refl, 0, 1).astype("float32")
        saida[nome][~np.isfinite(dn) | (dn <= 0)] = np.nan
    inval = ~np.all([np.isfinite(saida[b]) for b in saida], axis=0)
    for b in saida:
        saida[b][inval] = np.nan
    n = np.full(c.SHAPE, np.nan, "float32")
    for b in ("blue", "swir1", "swir2"):
        saida[b] = n
    cnt = np.where(np.isfinite(saida["red"]), 1.0, np.nan)
    meta = dict(fonte=f"Planetary Computer landsat-c2-l1 {item.id} (Tier 2)", sensor="Landsat 3 MSS (60 m)",
                datas=item.datetime.strftime("%Y-%m-%d"), item=item.id, sol_elevacao=sun,
                notas=("TOA, (M*DN+A)/sin(elev solar); verde=B4, vermelho=B5, nir=B7 (0,8-1,1um; B6 0,7-0,8um nao usada); "
                       "60 m -> grade 30 m por reamostragem bilinear; blue/swir ausentes. "
                       "Cena de junho de 1979 como substituta do censo de 1980"))
    return empilha(saida, cnt), meta


# ---------------- índices ----------------
def nd(a, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        r = (a - b) / (a + b)
    r = np.where(np.isfinite(r), r, np.nan)
    return r.astype("float32")


def indices(stack):
    B = dict(zip(c.BANDAS, stack))
    ndvi = nd(B["nir"], B["red"])
    ndbi = nd(B["swir1"], B["nir"])
    mndwi = nd(B["green"], B["swir1"])
    with np.errstate(divide="ignore", invalid="ignore"):
        bsi = nd(B["swir1"] + B["red"], B["nir"] + B["blue"])
    return np.stack([ndvi, ndbi, mndwi, bsi])


def estatisticas(stack):
    red = stack[c.BANDAS.index("red")]
    nan_pct = float(np.isnan(red).mean() * 100)
    cnt = stack[c.BANDAS.index("count")]
    cnt_med = float(np.nanmedian(cnt)) if np.isfinite(cnt).any() else float("nan")
    return nan_pct, cnt_med


def escolhe_cena_2010():
    res = []
    for p in CENAS_2010:
        it = busca_item_l2(p)
        res.append((nuvem_bbox(it), p))
        c.log(f"  2010: candidata {p} nuvem/sombra no bbox = {res[-1][0]:.3f}")
    return min(res)[1]


def main():
    c.COMP.mkdir(parents=True, exist_ok=True)
    c.IDX.mkdir(parents=True, exist_ok=True)
    # inspeção visual do GeoMAD 2010 (RGB, quick-look): listras horizontais evidentes (resíduo SLC-off do ETM+) -> substituir
    forcar_2010 = os.environ.get("FORCAR_SUBST_2010", "1") == "1"
    with rasterio.Env(**ENV):
        for ano in c.EPOCAS:
            dest = c.COMP / f"{ano}.tif"
            didx = c.IDX / f"{ano}.tif"
            if c.integro(dest) and c.integro(didx):
                c.log(ano, "já existe, pulando")
                continue
            c.log(ano, "construindo ...")
            subst = ""
            if ano == 1979:
                stack, meta = mss_1979()
            elif ano == 2026:
                stack, meta = composicao_2026()
            else:
                stack, meta = geomad(ano)
                nan_pct, cnt_med = estatisticas(stack)
                c.log(f"  GeoMAD {ano}: NaN {nan_pct:.1f}%, COUNT mediana (válidos) {cnt_med}, (todos) {meta['count_mediana_bbox_todos']}")
                if ano == 1985 and (cnt_med < 3 or nan_pct > 5):
                    subst = (f"GeoMAD 1985 rejeitado (NaN {nan_pct:.1f}%, COUNT mediana {cnt_med:.0f}); substituído por TM de "
                             f"{CENA_1985[-8:]} (1984-06-01)")
                    stack, meta = cena_unica(CENA_1985)
                elif ano == 2010 and (nan_pct > 5 or cnt_med < 3 or forcar_2010):
                    p = escolhe_cena_2010()
                    subst = (f"GeoMAD 2010 rejeitado (NaN {nan_pct:.1f}%, COUNT mediana {cnt_med:.0f}"
                             f"{', listrado SLC-off' if forcar_2010 else ''}); substituído por TM {p[-8:]}")
                    stack, meta = cena_unica(p)
            nan_pct, cnt_med = estatisticas(stack)
            meta.update(epoca=ano, substituicao=subst or "nenhuma", nan_pct=round(nan_pct, 2),
                        count_mediana=cnt_med)
            c.grava(dest, stack, descricoes=c.BANDAS, tags=meta)
            c.grava(didx, indices(stack), descricoes=["ndvi", "ndbi", "mndwi", "bsi"], tags=meta)
            p2, p98 = np.nanpercentile(stack[2], [2, 98]) if np.isfinite(stack[2]).any() else (np.nan, np.nan)
            c.log(f"  gravado {dest.name}: NaN {nan_pct:.1f}%, vermelho p2/p98 {p2:.3f}/{p98:.3f}  {subst}")


if __name__ == "__main__":
    main()
