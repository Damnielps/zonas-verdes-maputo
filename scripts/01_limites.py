"""01 - Limites administrativos (HDX COD-AB) e vetores OSM (Overpass). Idempotente."""
import os, sys, time, json, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum as c
import geopandas as gpd
import requests
from shapely.geometry import box, shape, LineString, Polygon

URL_HDX = ("https://data.humdata.org/dataset/5e8d83a5-1210-49be-b7d9-cf286dbc15df/resource/"
           "f1d97232-4cb5-4083-b3cc-d192aa9bdcfe/download/moz_admin_boundaries.geojson.zip")
HDX_DIR = c.RAW / "hdx"
ZIP = HDX_DIR / "moz_admin_boundaries.geojson.zip"
OUT_LIM = c.PROC / "limites.gpkg"
OUT_OSM = c.PROC / "osm.gpkg"
OVERPASS = "https://overpass-api.de/api/interpreter"


def zip_ok():
    try:
        with zipfile.ZipFile(ZIP) as z:
            return z.testzip() is None
    except Exception:
        return False


def baixa_hdx():
    HDX_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP.exists() and zip_ok():
        c.log("HDX zip já presente e íntegro:", ZIP.stat().st_size)
        return
    c.log("baixando HDX ...")
    with requests.get(URL_HDX, headers=c.HEADERS, stream=True, timeout=(30, 120)) as r:
        r.raise_for_status()
        with open(ZIP, "wb") as f:
            for ch in r.iter_content(1 << 20):
                f.write(ch)
    assert zip_ok(), "zip corrompido"


def limites():
    if OUT_LIM.exists() and all(
            l in gpd.list_layers(OUT_LIM)["name"].tolist() for l in ["distritos", "bairros", "matola_bairros", "bbox"]):
        c.log("limites.gpkg já existe, pulando")
        return
    baixa_hdx()
    with zipfile.ZipFile(ZIP) as z:
        nomes = z.namelist()
        c.log("conteúdo do zip:", nomes)
        dest = HDX_DIR / "extraido"
        dest.mkdir(exist_ok=True)
        z.extractall(dest)
    def le(nivel):
        cand = [p for p in (HDX_DIR / "extraido").rglob("*.geojson") if p.name.lower().endswith(f"admin{nivel}.geojson")]
        assert cand, f"adm{nivel} não encontrado"
        return gpd.read_file(cand[0])
    adm2, adm4 = le(2), le(4)
    c.log("adm2 cols:", list(adm2.columns)[:20], len(adm2))
    c.log("adm4 cols:", list(adm4.columns)[:25], len(adm4))
    bb = gpd.GeoDataFrame({"nome": ["bbox"]}, geometry=[box(*c.BBOX_LL)], crs="EPSG:4326")
    def col(df, nivel, suf):
        for k in (f"adm{nivel}_{suf}", f"ADM{nivel}_{suf.upper()}"):
            if k in df.columns:
                return k
        raise KeyError((nivel, suf, list(df.columns)))
    # Cidade de Maputo: adm1_pt/adm1_name
    a1 = [k for k in adm4.columns if k.lower().startswith("adm1_") and "pcode" not in k.lower()]
    c.log("adm1 cols:", a1)
    a1n = a1[0]
    def eh_maputo_cidade(df):
        cols = [k for k in df.columns if k.lower().startswith("adm1_") and "pcode" not in k.lower()]
        m = False
        for k in cols:
            m = m | df[k].astype(str).str.contains("Cidade de Maputo|Maputo Cidade|Maputo City", case=False, regex=True)
        return m
    dist = adm2[eh_maputo_cidade(adm2)].copy()
    bair = adm4[eh_maputo_cidade(adm4)].copy()
    c.log("distritos:", len(dist), "bairros:", len(bair))
    # Matola: adm4 que intersectam o bbox, fora da cidade de Maputo
    inter = adm4[adm4.intersects(bb.geometry.iloc[0])]
    mat = inter[~inter.index.isin(bair.index)].copy()
    c.log("outros adm4 no bbox:", len(mat))
    to = lambda g: g.to_crs(c.CRS)
    c.PROC.mkdir(parents=True, exist_ok=True)
    tmp = OUT_LIM.with_suffix(".tmp.gpkg")
    if tmp.exists():
        tmp.unlink()
    to(dist).to_file(tmp, layer="distritos", driver="GPKG")
    to(bair).to_file(tmp, layer="bairros", driver="GPKG")
    to(mat).to_file(tmp, layer="matola_bairros", driver="GPKG")
    to(bb).to_file(tmp, layer="bbox", driver="GPKG")
    tmp.replace(OUT_LIM)
    c.log("limites.gpkg gravado")


# ---------------- Overpass ----------------
S, W, N, E = c.LAT_MIN, c.LON_MIN, c.LAT_MAX, c.LON_MAX
BB = f"({S},{W},{N},{E})"
CONSULTAS = {
    "osm_agricola": f'[out:json][timeout:180];(way["landuse"~"^(farmland|allotments|orchard|greenhouse_horticulture)$"]{BB};'
                    f'relation["landuse"~"^(farmland|allotments|orchard|greenhouse_horticulture)$"]{BB};);out geom;',
    "osm_circular": f'[out:json][timeout:180];(way["highway"]["name"~"Circular",i]{BB};way["highway"]["ref"~"^(EN|N)?\\s?(CM|Circular)",i]{BB};);out geom;',
    "osm_ponte": f'[out:json][timeout:180];(way["bridge"]["name"~"Maputo.*Katembe|Katembe|KaTembe|Ponte Maputo",i]{BB};'
                 f'way["man_made"="bridge"]["name"~"Katembe|KaTembe",i]{BB};relation["name"~"Ponte Maputo.*(Katembe|KaTembe)",i]{BB};);out geom;',
    "osm_wetland": f'[out:json][timeout:180];(way["natural"="wetland"]{BB};relation["natural"="wetland"]{BB};);out geom;',
}


def consulta(nome, q, tentativas=7):
    esp = 30
    for i in range(tentativas):
        try:
            r = requests.post(OVERPASS, data={"data": q}, headers={"User-Agent": "zonas-verdes-research/1.0", "Accept": "application/json"}, timeout=300)  # UA tipo navegador recebe 406 no Overpass
            if r.status_code == 200:
                return r.json()
            c.log(f"  {nome}: HTTP {r.status_code}, tentativa {i+1}")
        except Exception as e:
            c.log(f"  {nome}: erro {e!r}, tentativa {i+1}")
        time.sleep(esp)
        esp = min(esp * 2, 240)
    return None


def elementos_para_gdf(js):
    feats = []
    for el in js.get("elements", []):
        tags = el.get("tags", {})
        geoms = []
        if el["type"] == "way" and "geometry" in el:
            pts = [(p["lon"], p["lat"]) for p in el["geometry"]]
            geoms.append(pts)
        elif el["type"] == "relation":
            for m in el.get("members", []):
                if m.get("type") == "way" and "geometry" in m and m.get("role") in ("outer", ""):
                    geoms.append([(p["lon"], p["lat"]) for p in m["geometry"]])
        for pts in geoms:
            if len(pts) < 2:
                continue
            if len(pts) >= 4 and pts[0] == pts[-1]:
                g = Polygon(pts)
            else:
                g = LineString(pts)
            if g.is_empty:
                continue
            d = {k: tags.get(k) for k in ("name", "ref", "highway", "landuse", "natural", "bridge", "crop", "surface")}
            d.update(osm_id=el["id"], osm_tipo=el["type"], geometry=g)
            feats.append(d)
    return gpd.GeoDataFrame(feats, geometry="geometry", crs="EPSG:4326") if feats else None


def osm():
    existentes = gpd.list_layers(OUT_OSM)["name"].tolist() if OUT_OSM.exists() else []
    falt = [n for n in CONSULTAS if n not in existentes]
    if not falt:
        c.log("osm.gpkg completo, pulando")
        return
    brutos = c.RAW / "overpass"
    brutos.mkdir(parents=True, exist_ok=True)
    for nome in falt:
        f = brutos / f"{nome}.json"
        if f.exists():
            js = json.loads(f.read_text())
        else:
            c.log("Overpass:", nome)
            js = consulta(nome, CONSULTAS[nome])
            if js is None:
                c.log(f"  FALHA em {nome} (continuando)")
                continue
            f.write_text(json.dumps(js))
            time.sleep(10)
        gdf = elementos_para_gdf(js)
        if gdf is None:
            c.log(f"  {nome}: 0 feições; camada vazia não gravada")
            gdf = gpd.GeoDataFrame({"osm_id": []}, geometry=[], crs="EPSG:4326")
        gdf.to_crs(c.CRS).to_file(OUT_OSM, layer=nome, driver="GPKG")
        c.log(f"  {nome}: {len(gdf)} feições")


if __name__ == "__main__":
    limites()
    osm()
