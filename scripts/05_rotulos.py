"""05 - Rotulos de treino (pontos) por epoca.

Ancora 2020 por concordancia WorldCover 2021 x IO LULC 2020 x GHSL 2020 x OSM; propagacao para as demais
epocas por distancia espectral (angulo) e consistencia com GHSL(t); pontos LUCO (<=2001) via crosswalk.
Saidas: dados/proc/rotulos/treino_<epoca>.parquet (x, y, classe, origem, sub), pool_2020.parquet,
rotulos_resumo.json, luco_crosswalk.csv; figura dados/fig/class/rotulos_2v3.png.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio import features
from scipy import ndimage as ndi

from comum import *  # noqa

ROT = PROC / "rotulos"
FIGC = FIG / "class"
SEED = 42
N_ANCORA = 1500       # pontos por classe na ancora 2020 (spec)
N_POOL = 6000         # reserva de candidatos por classe para propagar (ver docs/qa/classificacao.md)
N_MAX_EPOCA = 1500    # maximo de pontos propagados por classe e epoca
N_LUCO = 1000         # maximo de pontos LUCO por classe e epoca
PERC_ANG = 20         # percentil (spec) dos pontos pseudo-invariantes (nivel inicial da escada)
ESCADA = [20, 50, 80]  # se o limiar p20 deixa alguma classe com poucos pontos, sobe-se a escada
MIN_RET = 150          # retencao minima por classe (ou 50 % do pool, se menor)
MIN_EROSAO = 300       # classes com menos pixeis apos erosao de 1 px ficam sem erosao
ELEV_BAIXADA = 15.0   # m
TPI_BAIXADA = 0.0
BUF_WETLAND = 100.0   # m
GHSL_CONST = 2000.0   # m2 por celula de 100 m (>=20 %)
GHSL_AGRI = 500.0
GHSL_ANO = {1979: 1980, 1985: 1985, 1990: 1990, 1995: 1995, 1997: 1995, 2000: 2000, 2005: 2005, 2007: 2005,
            2010: 2010, 2015: 2015, 2017: 2015, 2020: 2020, 2025: 2025, 2026: 2025}
LUCO_ANO = {1979: 1982, 1985: 1982, 1990: 1991, 1995: 1991, 1997: 1991, 2000: 2001, 2005: 2001}
BANDAS_ANG = ["green", "red", "nir", "swir1", "swir2"]
IDXB = {b: i for i, b in enumerate(BANDAS)}

# crosswalk LUCO (nivel II) -> classe do estudo; None = ambiguo, excluido
CROSS = {
    "1.0.1": (1, "Multifuncional: totalmente infra-estruturado"),
    "2.1.1": (1, "Residencial infra-estruturada, alta densidade"),
    "2.1.2": (1, "Residencial infra-estruturada, media densidade"),
    "2.1.3": (None, "baixa densidade: quintais e arvores, ambiguo"),
    "2.2.1": (1, "Residencial parcialmente infra-estruturada, alta densidade"),
    "2.2.2": (1, "Residencial parcialmente infra-estruturada, media densidade"),
    "2.2.3": (None, "baixa densidade (<2100 hab/km2), ambiguo"),
    "2.3.1": (1, "Residencial nao infra-estruturada, alta densidade"),
    "2.3.2": (1, "Residencial nao infra-estruturada, media densidade"),
    "2.3.3": (None, "baixa densidade, ambiguo"),
    "2.4.1": (None, "emergente intercalado com vazios, ambiguo"),
    "2.4.2": (None, "emergente intercalado com matos, ambiguo"),
    "3.0.1": (1, "Industria, armazenagem e reparacao"),
    "3.0.2": (1, "Comercio e servicos"),
    "3.0.3": ("agri", "Agricultura e pecuaria: talhoes horticolas/quintas -> 2 ou 3 pela regra dem/TPI"),
    "3.0.4": (7, "Extraccao de areia e sal -> solo exposto"),
    "4.0.1": (1, "Saude"),
    "4.0.2": (None, "Educacao: recintos escolares com arvores, ambiguo"),
    "4.0.3": (None, "Outros equipamentos (cemiterio, lixeira, desporto), ambiguo"),
    "4.0.4": (None, "Vias e areas de apoio, ambiguo (poligonos grandes)"),
    "4.0.5": (None, "Infra-estruturas e transportes (aeroporto, porto), ambiguo"),
    "4.0.6": (None, "Administracao publica, recintos extensos, ambiguo"),
    "4.0.7": (None, "Outros servicos publicos, residual"),
    "5.0.1": (None, "Vazio urbano e ruina, ambiguo"),
    "6.0.1": (4, "Mangal -> arborea (subclasse 41)"),
    "6.0.2": (5, "Outras areas alagadas -> herbacea/zona humida"),
    "6.0.3": (6, "Cursos e planos de agua"),
    "7.0.1": (4, "Mato (vegetacao arbustiva natural) -> arborea/arbustiva"),
    "7.0.2": (4, "Area arborizada, parques e jardins -> arborea"),
    "7.0.3": (7, "Praia"),
    "7.0.4": (7, "Outras areas naturais, sem vegetacao"),
}


def le(path, b=1):
    with rasterio.open(path) as s:
        return s.read(b)


def le_comp(ep):
    with rasterio.open(COMP / f"{ep}.tif") as s:
        a = s.read()
    return {b: a[i] for b, i in IDXB.items()}


def ghsl(ano):
    return le(VAL / f"ghsl_built_{ano}.tif")


def ero(m, it=1):
    return ndi.binary_erosion(m, structure=np.ones((3, 3), bool), iterations=it, border_value=0)


def rast_geom(geoms):
    geoms = [g for g in geoms if g is not None and not g.is_empty]
    if not geoms:
        return np.zeros(SHAPE, bool)
    return features.rasterize(((g, 1) for g in geoms), out_shape=SHAPE, transform=TRANSFORM, fill=0,
                              dtype="uint8").astype(bool)


def xy_de(idx):
    r, c = np.unravel_index(idx, SHAPE)
    x = X0 + (c + 0.5) * RES
    y = Y1 - (r + 0.5) * RES
    return x, y


def rc_de(x, y):
    c = np.floor((np.asarray(x) - X0) / RES).astype(int)
    r = np.floor((Y1 - np.asarray(y)) / RES).astype(int)
    return r, c


def amostra(mask, n, rng):
    idx = np.flatnonzero(mask.ravel())
    if len(idx) > n:
        idx = rng.choice(idx, n, replace=False)
    return np.sort(idx)


def cap(df, n):
    return pd.concat([d.sample(min(len(d), n), random_state=SEED) for _, d in df.groupby("classe")],
                     ignore_index=True)


def baixada_regra(dem, tpi, wet):
    return ((dem < ELEV_BAIXADA) & (tpi < TPI_BAIXADA)) | wet


def angulo(a, b):
    na = np.linalg.norm(a, axis=1); nb = np.linalg.norm(b, axis=1)
    cos = (a * b).sum(1) / np.maximum(na * nb, 1e-9)
    return np.arccos(np.clip(cos, -1, 1))


def vetor(comp, r, c, bandas):
    return np.stack([comp[b][r, c] for b in bandas], 1)


def ndvi_ndwi(comp, r, c):
    g = comp["green"][r, c]; rd = comp["red"][r, c]; n = comp["nir"][r, c]
    return (n - rd) / np.maximum(n + rd, 1e-6), (g - n) / np.maximum(g + n, 1e-6)


def coerente(classe, ndvi, ndwi):
    ok = np.isfinite(ndvi) & np.isfinite(ndwi)
    k = classe
    r = np.zeros_like(ok)
    r |= (k == 1) & (ndvi < 0.40) & (ndwi < 0.20)
    r |= np.isin(k, (2, 3)) & (ndwi < 0.15) & (ndvi > -0.05)
    r |= (k == 4) & (ndvi > 0.15) & (ndwi < 0.15)
    r |= (k == 5) & (ndwi < 0.20)
    r |= (k == 6) & (ndwi > -0.05)
    r |= (k == 7) & (ndvi < 0.25) & (ndwi < 0.10)
    return r & ok


def main():
    ROT.mkdir(parents=True, exist_ok=True); FIGC.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    resumo = {"params": dict(N_ANCORA=N_ANCORA, N_POOL=N_POOL, N_MAX_EPOCA=N_MAX_EPOCA, N_LUCO=N_LUCO,
                             PERC_ANG=PERC_ANG, ELEV_BAIXADA=ELEV_BAIXADA, TPI_BAIXADA=TPI_BAIXADA,
                             BUF_WETLAND=BUF_WETLAND, SEED=SEED)}

    dem = le(PROC / "dem.tif"); tpi = le(PROC / "tpi.tif")
    wc = le(VAL / "worldcover_2021.tif"); io = le(VAL / "io_lulc_2020.tif")
    g20 = ghsl(2020)
    osm = gpd.read_file(PROC / "osm.gpkg", layer="osm_agricola")
    osm = osm[osm.landuse.isin(["farmland", "allotments", "greenhouse_horticulture"])]
    osm_ag = rast_geom(osm.geometry)
    wet = gpd.read_file(PROC / "osm.gpkg", layer="osm_wetland")
    wet_buf = rast_geom(wet.geometry.buffer(BUF_WETLAND))
    baix = baixada_regra(np.nan_to_num(dem, nan=99), np.nan_to_num(tpi, nan=0), wet_buf)

    # ---------- ancora 2020 ----------
    g20n = np.nan_to_num(g20, nan=0)
    m = {}
    m[1] = (wc == 50) & (io == 7) & (g20n >= GHSL_CONST)
    m[4] = ((wc == 10) & (io == 2)) | (wc == 95)
    m[5] = np.isin(wc, (30, 90)) & np.isin(io, (11, 4)) & ~osm_ag
    m[6] = (wc == 80) & (io == 1)
    m[7] = (wc == 60) & (io == 8)
    agri = (osm_ag | ((wc == 40) & (io == 5))) & (g20n <= GHSL_AGRI)
    m[2] = agri & baix
    m[3] = agri & ~baix
    bruto = {k: int(v.sum()) for k, v in m.items()}
    soma = sum(v.astype(int) for v in m.values())
    resumo["ancora_px_bruto"] = bruto
    resumo["ancora_conflito_px"] = int((soma > 1).sum())
    resumo["ancora_sem_erosao"] = []
    for k in m:
        uni = m[k] & (soma == 1)
        er = ero(uni)
        if er.sum() < MIN_EROSAO and uni.sum() > er.sum():
            m[k] = uni  # classe com poucos pixeis (ex.: solo exposto): sem erosao, documentado
            resumo["ancora_sem_erosao"].append(int(k))
        else:
            m[k] = er
    resumo["ancora_px_erodido"] = {k: int(v.sum()) for k, v in m.items()}
    mang = ero(wc == 95)

    pool = []
    for k in range(1, 8):
        idx = amostra(m[k], N_POOL, rng)
        x, y = xy_de(idx)
        sub = np.where((k == 4) & mang.ravel()[idx], 41, 0)
        pool.append(pd.DataFrame(dict(x=x, y=y, classe=k, origem="ancora2020", sub=sub)))
    pool = pd.concat(pool, ignore_index=True)
    pool.to_parquet(ROT / "pool_2020.parquet", index=False)
    anc = cap(pool, N_ANCORA)
    anc.to_parquet(ROT / "treino_2020.parquet", index=False)
    resumo["pool_2020"] = pool.classe.value_counts().sort_index().to_dict()
    resumo["treino_2020"] = anc.classe.value_counts().sort_index().to_dict()

    # figura 2 vs 3
    plot_2v3(dem, tpi, osm_ag, wet_buf, baix, g20n)

    # ---------- pontos pseudo-invariantes ----------
    agua_prof = ero((wc == 80) & (io == 1), 3)
    d = gpd.read_file(PROC / "limites.gpkg", layer="distritos")
    kmp = rast_geom(d[d.adm2_name == "KaMpfumo"].geometry)
    g75 = np.nan_to_num(ghsl(1975), nan=0)
    nucleo = ero((g75 >= 5000) & kmp & (g20n >= 5000))
    ia = amostra(agua_prof, 1000, rng); inn = amostra(nucleo, 1000, rng)
    resumo["invariantes"] = {"agua_profunda": int(len(ia)), "nucleo_construido_KaMpfumo": int(len(inn))}
    inv_idx = np.concatenate([ia, inn])
    inv_tipo = np.array(["agua"] * len(ia) + ["nucleo"] * len(inn))
    ri, ci = np.unravel_index(inv_idx, SHAPE)

    # ---------- LUCO: rasteriza por ano e classe ----------
    luco = {}
    cw_rows = []
    for ano in sorted(set(LUCO_ANO.values())):
        gdf = gpd.read_file(RAW / "luco" / f"ulu_maputo_{ano}" / f"ulu_maputo_{ano}.shp")
        luco[ano] = {}
        cod = gdf["N_II_C"].astype(str)
        for kk in ("1", "2", "3", "4", "5", "6", "7", "agri"):
            pass
        for c, (dest, desc) in CROSS.items():
            sel = gdf[cod == c]
            area_ha = float(sel.area.sum() / 1e4)
            cw_rows.append(dict(ano=ano, codigo_luco=c, descricao=desc, classe_estudo=dest if dest else "excluido",
                                n_poligonos=len(sel), area_ha=round(area_ha, 1)))
            if dest is None or len(sel) == 0:
                continue
            mk = ero(rast_geom(sel.geometry))
            if dest == "agri":
                luco[ano].setdefault(2, np.zeros(SHAPE, bool)); luco[ano].setdefault(3, np.zeros(SHAPE, bool))
                luco[ano][2] |= mk & baix; luco[ano][3] |= mk & ~baix
            else:
                luco[ano].setdefault(dest, np.zeros(SHAPE, bool)); luco[ano][dest] |= mk
                if c == "6.0.1":
                    luco[ano].setdefault("mang", np.zeros(SHAPE, bool)); luco[ano]["mang"] |= mk
        # pixels em mais de uma classe LUCO sao descartados
        ks = [k for k in luco[ano] if k != "mang"]
        s = sum(luco[ano][k].astype(int) for k in ks)
        for k in ks:
            luco[ano][k] &= (s == 1)
    cw = pd.DataFrame(cw_rows)
    cw.to_csv(ROT / "luco_crosswalk.csv", index=False)

    # ---------- propagacao por epoca ----------
    pxy = np.c_[pool.x.values, pool.y.values]
    pr, pc = rc_de(pxy[:, 0], pxy[:, 1])
    c20 = le_comp(2020)
    resumo["angulos"] = {}; resumo["contagem"] = {}
    for ep in EPOCAS:
        if ep == 2020:
            df = anc.copy()
            resumo["contagem"][ep] = df.groupby(["classe", "origem"]).size().rename("n").reset_index().to_dict("records")
            continue
        ct = le_comp(ep)
        bs = [b for b in BANDAS_ANG if np.isfinite(ct[b]).any()] if ep != 1979 else ["green", "red", "nir"]
        # limiares: percentil dos angulos dos invariantes. Agua e nucleo construido tem distribuicoes muito
        # diferentes (agua escura e ruidosa), entao o limiar da classe 6 vem dos invariantes de agua e o das
        # demais dos invariantes de nucleo construido, ao mesmo percentil.
        ang_inv = angulo(vetor(c20, ri, ci, bs), vetor(ct, ri, ci, bs))
        ok = np.isfinite(ang_inv)
        a = angulo(vetor(c20, pr, pc, bs), vetor(ct, pr, pc, bs))
        gt = np.nan_to_num(ghsl(GHSL_ANO[ep]), nan=0)[pr, pc]
        k = pool.classe.values
        cons = np.where(k == 1, gt >= GHSL_CONST, np.where(np.isin(k, (2, 3, 4, 5)), gt < GHSL_AGRI, True))
        npool = pool.classe.value_counts().to_dict()
        for perc in ESCADA:
            lim_l = float(np.percentile(ang_inv[ok & (inv_tipo == "nucleo")], perc))
            lim_a = float(np.percentile(ang_inv[ok & (inv_tipo == "agua")], perc))
            lim = np.where(k == 6, lim_a, lim_l)
            keep = np.isfinite(a) & (a < lim) & cons
            ret = pd.Series(keep).groupby(k).sum().to_dict()
            if all(ret.get(c, 0) >= min(MIN_RET, 0.5 * n) for c, n in npool.items() if n >= 20):
                break
        resumo["angulos"][ep] = dict(bandas=bs, percentil_usado=perc, limiar_terra_rad=lim_l,
                                     limiar_agua_rad=lim_a,
                                     p20_agua=float(np.percentile(ang_inv[ok & (inv_tipo == "agua")], 20)),
                                     p20_nucleo=float(np.percentile(ang_inv[ok & (inv_tipo == "nucleo")], 20)),
                                     retidos_por_classe={int(a_): int(b_) for a_, b_ in ret.items()})
        dfp = pool[keep].copy(); dfp["origem"] = "prop2020"
        dfp = cap(dfp, N_MAX_EPOCA)
        partes = [dfp]
        resumo.setdefault("propagacao_descartes", {})[ep] = dict(
            por_angulo=int((~(np.isfinite(a) & (a < lim))).sum()), por_ghsl=int((~cons).sum()), pool=int(len(pool)))
        lim_txt = "p%d terra=%.4f agua=%.4f" % (perc, lim_l, lim_a)
        # LUCO
        if ep in LUCO_ANO:
            ano = LUCO_ANO[ep]
            for kcl in (1, 2, 3, 4, 5, 6, 7):
                mk = luco[ano].get(kcl)
                if mk is None:
                    continue
                idx = amostra(mk, N_LUCO * 3, rng)
                if len(idx) == 0:
                    continue
                r_, c_ = np.unravel_index(idx, SHAPE)
                nv, nw = ndvi_ndwi(ct, r_, c_)
                good = coerente(np.full(len(idx), kcl), nv, nw)
                idx = idx[good][:N_LUCO]
                x, y = xy_de(idx)
                sub = np.where((kcl == 4) & luco[ano].get("mang", np.zeros(SHAPE, bool)).ravel()[idx], 41, 0)
                partes.append(pd.DataFrame(dict(x=x, y=y, classe=kcl, origem=f"luco{ano}", sub=sub)))
                resumo.setdefault("luco_coerencia", {}).setdefault(ep, {})[kcl] = dict(
                    candidatos=int(good.size), coerentes=int(good.sum()), usados=int(len(idx)))
        df = pd.concat(partes, ignore_index=True)
        df.to_parquet(ROT / f"treino_{ep}.parquet", index=False)
        resumo["contagem"][ep] = df.groupby(["classe", "origem"]).size().rename("n").reset_index().to_dict("records")
        log(ep, lim_txt, df.classe.value_counts().sort_index().to_dict())
    with open(ROT / "rotulos_resumo.json", "w") as f:
        json.dump(resumo, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    log("ok; ancora:", resumo["treino_2020"])


def plot_2v3(dem, tpi, osm_ag, wet_buf, baix, g20n):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ardosia_palette import apply_ardosia, ARDOSIA, TERRACOTA, PEDRA
    apply_ardosia()
    sel = osm_ag & (g20n <= GHSL_AGRI)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.8))
    bins = np.arange(-2, 40, 1)
    ax[0].hist(dem[sel & baix], bins=bins, color=ARDOSIA, label="classe 2 (baixada)")
    ax[0].hist(dem[sel & ~baix], bins=bins, color=TERRACOTA, label="classe 3 (sequeiro)", alpha=.9)
    ax[0].axvline(ELEV_BAIXADA, color=PEDRA, ls="--"); ax[0].set_xlabel("altitude (m)"); ax[0].set_ylabel("píxeis OSM farmland/allotments")
    ax[0].set_title("Altitude dos polígonos OSM agrícolas", fontsize=11); ax[0].legend()
    ax[1].hist(tpi[sel & baix], bins=np.arange(-8, 8, .25), color=ARDOSIA)
    ax[1].hist(tpi[sel & ~baix], bins=np.arange(-8, 8, .25), color=TERRACOTA)
    ax[1].axvline(TPI_BAIXADA, color=PEDRA, ls="--"); ax[1].set_xlabel("TPI"); ax[1].set_title("TPI", fontsize=11)
    rr, cc = np.where(sel)
    r0, r1, c0, c1 = max(rr.min() - 20, 0), rr.max() + 20, max(cc.min() - 20, 0), cc.max() + 20
    rgb = np.zeros(SHAPE + (3,)) + 0.93
    rgb[sel & baix] = (0.14, 0.25, 0.31); rgb[sel & ~baix] = (0.61, 0.36, 0.25)
    ax[2].imshow(rgb[r0:r1, c0:c1]); ax[2].set_axis_off(); ax[2].grid(False)
    ax[2].set_title("OSM agrícola: baixada (azul) / outro (terracota)", fontsize=11)
    fig.savefig(FIGC / "rotulos_2v3.png", dpi=150)
    plt.close(fig)
    resumo_pct = float((sel & baix).sum() / max(sel.sum(), 1))
    log("OSM agricola em classe 2 pela regra: %.1f%%; wetland buffer sozinho: %.1f%%" % (
        100 * resumo_pct, 100 * float((sel & wet_buf & ~((dem < ELEV_BAIXADA) & (tpi < TPI_BAIXADA))).sum() / max(sel.sum(), 1))))


if __name__ == "__main__":
    main()
