"""04 - QA das composições: tabela em docs/qa/composicoes.md, quick-looks PNG e painel de contato."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rasterio
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import comum as c
from ardosia_palette import apply_ardosia

B = {b: i for i, b in enumerate(c.BANDAS)}


def estica(a, lo=None, hi=None):
    ok = np.isfinite(a)
    if lo is None:
        lo, hi = np.nanpercentile(a[ok], [2, 98])
    r = np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1)
    return r, ok


def rgb_img(stack, bands):
    ch, ok = [], None
    rng = []
    for b in bands:
        a = stack[B[b]]
        r, o = estica(a)
        ch.append(r); ok = o if ok is None else ok & o
    im = (np.stack(ch, -1) * 255).astype("uint8")
    im[~ok] = 255
    return im


def main():
    c.QA.mkdir(parents=True, exist_ok=True)
    (c.FIG / "qa").mkdir(parents=True, exist_ok=True)
    linhas = []
    imgs = {}
    perc = []
    for ano in c.EPOCAS:
        with rasterio.open(c.COMP / f"{ano}.tif") as s:
            st = s.read()
            t = s.tags()
        mss = ano == 1979
        if mss:
            rgb = rgb_img(st, ["red", "green", "green"])
            fc = rgb_img(st, ["nir", "red", "green"])
        else:
            rgb = rgb_img(st, ["red", "green", "blue"])
            fc = rgb_img(st, ["swir1", "nir", "red"])
        Image.fromarray(rgb).save(c.FIG / "qa" / f"{ano}_rgb.png")
        Image.fromarray(fc).save(c.FIG / "qa" / f"{ano}_falsacor.png")
        imgs[ano] = rgb
        nan_pct = float(np.mean(~np.isfinite(st[B["red"]])) * 100)
        cnt = st[B["count"]]
        cm = np.nanmedian(cnt) if np.isfinite(cnt).any() else float("nan")
        ps = []
        for b in ["blue", "green", "red", "nir", "swir1", "swir2"]:
            a = st[B[b]]
            if np.isfinite(a).any():
                p2, p98 = np.nanpercentile(a, [2, 98])
                ps.append(f"{b} {p2:.3f}-{p98:.3f}")
        perc.append((ano, "; ".join(ps)))
        linhas.append((ano, t.get("fonte", ""), t.get("sensor", ""), t.get("datas", ""), nan_pct, cm,
                       t.get("substituicao", ""), t.get("item", ""), t.get("notas", "")))
    md = ["# QA das composições (30 m, EPSG:32736)", "",
          "Gerado por `scripts/04_qa_composicoes.py`. NaN % = fração da grade do bbox sem dado válido na banda vermelha; "
          "COUNT = número de observações por píxel (GeoMAD: banda COUNT; cena única: 1; 2026: observações válidas).", "",
          "| Época | Fonte | Sensor | Datas | NaN % | COUNT mediana | Substituição / notas |",
          "|---|---|---|---|---|---|---|"]
    for a, f, se, d, n, cm, sub, it, no in linhas:
        nota = ("" if sub in ("", "nenhuma") else sub + ". ") + no
        md.append(f"| {a} | {f} ({it}) | {se} | {d} | {n:.2f} | {cm:.0f} | {nota or '-'} |")
    md += ["", "## Percentis 2-98% por banda (reflectância)", "", "| Época | Bandas |", "|---|---|"]
    md += [f"| {a} | {p} |" for a, p in perc]
    md += ["", "## Notas", "",
           "- 1979 (MSS): sem banda azul; quick-look 'rgb' é pseudo-cor (R=vermelho, G=verde, B=verde); falsa-cor = NIR-vermelho-verde.",
           "- Quick-looks com estiramento 2-98% por banda e por imagem; NaN em branco.",
           "- Painel de contato: `dados/fig/qa/painel_rgb.png`."]
    (c.QA / "composicoes.md").write_text("\n".join(md) + "\n")
    apply_ardosia()
    fig, axs = plt.subplots(2, 7, figsize=(21, 8.2))
    for ax, ano in zip(axs.ravel(), c.EPOCAS):
        ax.imshow(imgs[ano]); ax.set_title(str(ano) + (" (MSS)" if ano == 1979 else "")); ax.axis("off")
    fig.tight_layout()
    fig.savefig(c.FIG / "qa" / "painel_rgb.png", dpi=110)
    c.log("QA escrito")


if __name__ == "__main__":
    main()
