"""06 - Classificacao Random Forest por epoca, filtro de moda 3x3 e regra temporal.

Entradas: dados/proc/comp (+indices), dem/declive/tpi, dados/proc/rotulos/treino_<epoca>.parquet.
Saidas: dados/proc/class/<epoca>.tif (uint8, 0=nodata), <epoca>_prob.tif (prob. maxima x100), oob.json.
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score

from comum import *  # noqa

ROT = PROC / "rotulos"
OUT = PROC / "class"
SEED = 42
NTREES = 500
MIN_CLASSE = 20
BANDAS_OPT = ["blue", "green", "red", "nir", "swir1", "swir2"]
MADS = ["smad", "emad", "bcmad"]
IDX_N = ["ndvi", "ndbi", "mndwi", "bsi"]
ELEV_BAIXADA, TPI_BAIXADA, BUF_WETLAND = 15.0, 0.0, 100.0
CV_EPOCAS = [2000, 2010, 2020]
CV_BLOCO = 3000.0


def le_arr(path):
    with rasterio.open(path) as s:
        return s.read()


def rast_geom(geoms):
    return features.rasterize(((g, 1) for g in geoms if g is not None and not g.is_empty), out_shape=SHAPE,
                              transform=TRANSFORM, fill=0, dtype="uint8").astype(bool)


def carrega_features(ep, topo):
    a = le_arr(COMP / f"{ep}.tif")
    ix = le_arr(COMP / "indices" / f"{ep}.tif")
    cols, nomes = [], []
    for b in BANDAS_OPT + MADS:
        arr = a[BANDAS.index(b)]
        if np.isfinite(arr).mean() > 0.5:
            cols.append(arr); nomes.append(b)
    for i, n in enumerate(IDX_N):
        if np.isfinite(ix[i]).mean() > 0.5:
            cols.append(ix[i]); nomes.append(n)
    for n, arr in topo.items():
        cols.append(arr); nomes.append(n)
    return np.stack(cols, 0).astype("float32"), nomes


def amostra_pts(F, x, y):
    c = np.floor((x - X0) / RES).astype(int); r = np.floor((Y1 - y) / RES).astype(int)
    ok = (r >= 0) & (r < HEIGHT) & (c >= 0) & (c < WIDTH)
    X = np.full((len(x), F.shape[0]), np.nan, dtype="float32")
    X[ok] = F[:, r[ok], c[ok]].T
    return X


def novo_rf(n=NTREES, oob=False):
    return RandomForestClassifier(n_estimators=n, class_weight="balanced_subsample", n_jobs=-1,
                                  random_state=SEED, oob_score=oob, bootstrap=True)


def f1_dict(y, p, classes):
    f = f1_score(y, p, labels=classes, average=None, zero_division=0)
    return {int(c): round(float(v), 4) for c, v in zip(classes, f)}


def moda3(cl, k_validos):
    """Filtro de maioria 3x3; empate favorece a classe do pixel central; 0 (nodata) preservado."""
    melhor = np.zeros(cl.shape, "float32"); saida = cl.copy()
    for k in k_validos:
        cnt = ndi.uniform_filter((cl == k).astype("float32"), size=3, mode="nearest") * 9.0
        cnt = cnt + (cl == k) * 0.5
        m = cnt > melhor
        saida[m] = k; melhor[m] = cnt[m]
    saida[cl == 0] = 0
    return saida.astype("uint8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dem = le_arr(PROC / "dem.tif")[0]; dec = le_arr(PROC / "declive.tif")[0]; tpi = le_arr(PROC / "tpi.tif")[0]
    topo = {"dem": dem, "declive": dec, "tpi": tpi}
    wet = gpd.read_file(PROC / "osm.gpkg", layer="osm_wetland")
    wet_buf = rast_geom(wet.geometry.buffer(BUF_WETLAND))
    baix = ((np.nan_to_num(dem, nan=99) < ELEV_BAIXADA) & (np.nan_to_num(tpi) < TPI_BAIXADA)) | wet_buf
    with rasterio.open(VAL / "worldcover_2021.tif") as s:
        mangue = s.read(1) == 95

    oob = {"features": {}, "oob": {}, "cv_bloques": {}, "n_treino": {}, "notas": {}}
    cls = {}; prob = {}
    for ep in EPOCAS:
        F, nomes = carrega_features(ep, topo)
        df = pd.read_parquet(ROT / f"treino_{ep}.parquet")
        X = amostra_pts(F, df.x.values, df.y.values)
        y = df.classe.values.astype(int)
        ok = np.isfinite(X).all(1)
        X, y, df = X[ok], y[ok], df[ok].reset_index(drop=True)
        ep79 = ep == 1979
        if ep79:
            # legenda reduzida: 1 construido, 3 vegetacao/agricultura (inclui 2, 4, 5), 6 agua, 7 solo exposto
            y_orig = y.copy()
            y = np.where(np.isin(y, (2, 3, 4, 5)), 3, y)
        cont = pd.Series(y).value_counts()
        validas = sorted(int(k) for k, n in cont.items() if n >= MIN_CLASSE)
        m = np.isin(y, validas)
        X, y, df = X[m], y[m], df[m].reset_index(drop=True)
        rf = novo_rf(oob=True).fit(X, y)
        p_oob = rf.classes_[np.argmax(rf.oob_decision_function_, 1)]
        ok_oob = np.isfinite(rf.oob_decision_function_).all(1)
        oob["features"][ep] = nomes
        oob["n_treino"][ep] = {int(k): int(v) for k, v in pd.Series(y).value_counts().sort_index().items()}
        oob["oob"][ep] = dict(acc=round(float(accuracy_score(y[ok_oob], p_oob[ok_oob])), 4),
                              f1=f1_dict(y[ok_oob], p_oob[ok_oob], validas), n=int(len(y)))
        imp = sorted(zip(nomes, rf.feature_importances_), key=lambda t: -t[1])[:5]
        oob["oob"][ep]["top_importancias"] = [(n, round(float(v), 3)) for n, v in imp]
        log(ep, "n=%d" % len(y), oob["n_treino"][ep], "OOB acc=%.3f" % oob["oob"][ep]["acc"])

        # CV espacial em blocos de 3 km
        if ep in CV_EPOCAS:
            bx = np.floor((df.x.values - X0) / CV_BLOCO).astype(int); by = np.floor((df.y.values - Y0) / CV_BLOCO).astype(int)
            bid = bx * 1000 + by
            ub = np.unique(bid)
            rng = np.random.default_rng(SEED)
            fold_de_bloco = dict(zip(ub, rng.permutation(len(ub)) % 5))
            fold = np.array([fold_de_bloco[b] for b in bid])
            pred = np.zeros(len(y), int)
            for f in range(5):
                tr, te = fold != f, fold == f
                if len(np.unique(y[tr])) < 2:
                    pred[te] = y[tr][0]; continue
                m_ = novo_rf().fit(X[tr], y[tr])
                pred[te] = m_.predict(X[te])
            oob["cv_bloques"][ep] = dict(acc=round(float(accuracy_score(y, pred)), 4), f1=f1_dict(y, pred, validas),
                                         n_blocos=int(len(ub)), nota="F1 sobre pontos de treino (rotulos derivados de produtos de terceiros), nao sobre verdade de campo")
            log(ep, "CV bloques acc=%.3f" % oob["cv_bloques"][ep]["acc"], oob["cv_bloques"][ep]["f1"])

        # previsao em toda a grade
        Fv = F.reshape(F.shape[0], -1).T
        bandas_ok = np.isfinite(F[nomes.index("green")]).ravel() & np.isfinite(F[nomes.index("red")]).ravel() \
            & np.isfinite(F[nomes.index("nir")]).ravel()
        cl = np.zeros(Fv.shape[0], "uint8"); pr = np.zeros(Fv.shape[0], "uint8")
        idx = np.flatnonzero(bandas_ok)
        for i0 in range(0, len(idx), 250000):
            ii = idx[i0:i0 + 250000]
            pp = rf.predict_proba(np.nan_to_num(Fv[ii], nan=0.0) if False else Fv[ii])
            cl[ii] = rf.classes_[np.argmax(pp, 1)].astype("uint8")
            pr[ii] = np.round(pp.max(1) * 100).astype("uint8")
        cl = cl.reshape(SHAPE); pr = pr.reshape(SHAPE)
        if ep79:
            nd = F[nomes.index("ndvi")]
            veg_baix = (cl == 3) & baix & ~mangue
            thr = float(np.percentile(X[(y_orig[m] == 2), nomes.index("ndvi")], 25)) if (y_orig[m] == 2).sum() >= 20 else 0.2
            oob["notas"][1979] = (f"legenda reduzida (1,2,3,6,7; 4 e 5 ausentes; 3 = vegetacao/agricultura fora da baixada, inclui "
                                  f"arborea e herbacea); 2 = classe 'vegetacao' com regra baixada (alt<{ELEV_BAIXADA} m e TPI<0 ou "
                                  f"buffer wetland OSM 100 m), fora de mangal WC95 e NDVI>={thr:.3f} (p25 do NDVI dos pontos 2 propagados)")
            cl[veg_baix & (nd >= thr)] = 2
        cl = moda3(cl, [int(k) for k in np.unique(cl) if k > 0])
        cls[ep] = cl; prob[ep] = pr

    # regra temporal: construido em t-1 e t+1 nao pode ser agricola (2/3) em t
    corr = {}; nao_corr = {}
    for i in range(1, len(EPOCAS) - 1):
        a, b, c = cls[EPOCAS[i - 1]], cls[EPOCAS[i]], cls[EPOCAS[i + 1]]
        m = (a == 1) & (c == 1) & np.isin(b, (2, 3))
        corr[EPOCAS[i]] = int(m.sum())
        b[m] = 1
        resto = (a == 1) & (c == 1) & (b != 1) & (b != 0)
        nao_corr[EPOCAS[i]] = int(resto.sum())  # reversoes para outras classes, mantidas (nao suavizar alem da regra)
    oob["regra_temporal_px_corrigidos"] = corr
    oob["reversoes_construido_nao_corrigidas_px"] = nao_corr
    for ep in EPOCAS:
        grava(OUT / f"{ep}.tif", cls[ep], nodata=0)
        grava(OUT / f"{ep}_prob.tif", prob[ep], nodata=0)
        log(ep, "classes", {int(k): int(v) for k, v in zip(*np.unique(cls[ep], return_counts=True))})
    with open(OUT / "oob.json", "w") as f:
        json.dump(oob, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
