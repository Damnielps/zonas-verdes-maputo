"""08 - QA da classificacao.

Padrao (revisao): figuras a partir de dados/proc/class_final/ e das tabelas agregadas de 07
(areas_agregado_classe_epoca.csv, areas_luco.csv). Legenda agregada, paleta Ardosia, rotulos em portugues.
Nao reescreve docs/qa/classificacao.md.
--run1: comportamento da primeira rodada (concordancia externa + reescreve o documento QA inteiro a partir de
dados/proc/class/; NAO usar apos a revisao: apagaria as secoes de pos-processamento).
"""
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio import features

from comum import *  # noqa

m5 = importlib.import_module("05_rotulos")

CLS = PROC / "class"
AREAS = PROC / "areas"
ROT = PROC / "rotulos"
FIGC = FIG / "class"
HA = RES * RES / 1e4
NOMES = {1: "Construído", 2: "Agricultura de baixada (zonas verdes)", 3: "Agricultura de sequeiro e mosaico",
         4: "Vegetação arbórea e arbustiva", 5: "Herbácea e zonas húmidas", 6: "Água", 7: "Solo exposto e areia"}
INTCOLS = {"epoca", "t0", "t1", "luco", "ghsl_ano", "classe", "valor_glad", "n", "blocos", "percentil"}
CCI_CROP = (10, 11, 12, 20, 30, 40)


def le(p, b=1):
    with rasterio.open(p) as s:
        return s.read(b)


def md(df, fmt=None):
    if df.empty:
        return "(vazio)\n"
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cel = []
        for c in cols:
            v = r[c]
            if c in INTCOLS and not (isinstance(v, float) and np.isnan(v)):
                cel.append(str(int(v)))
            elif isinstance(v, (float, np.floating)):
                cel.append("" if np.isnan(v) else (f"{v:,.1f}" if abs(v) >= 100 else f"{v:.3g}" if abs(v) < 1 else f"{v:.1f}"))
            else:
                cel.append(str(v))
        out.append("| " + " | ".join(cel) + " |")
    return "\n".join(out) + "\n"


def main_run1():
    FIGC.mkdir(parents=True, exist_ok=True); QA.mkdir(parents=True, exist_ok=True)
    cl = {ep: le(CLS / f"{ep}.tif") for ep in EPOCAS}
    oob = json.load(open(CLS / "oob.json"))
    rot = json.load(open(ROT / "rotulos_resumo.json"))
    areas = pd.read_csv(AREAS / "areas_classe_epoca.csv")
    conv = pd.read_csv(AREAS / "conversao.csv")
    cid = areas[areas.ambito == "cidade"].pivot(index="epoca", columns="classe", values="ha")
    bb = areas[areas.ambito == "bbox"].pivot(index="epoca", columns="classe", values="ha")

    # ---------------- concordancia externa ----------------
    ext = {}
    # built vs GHSL
    wsf = le(VAL / "wsf_evolution.tif")
    linhas = []
    for ep in EPOCAS:
        b = cl[ep] == 1
        g = np.nan_to_num(m5.ghsl(m5.GHSL_ANO[ep])) >= 2000
        linhas.append(dict(epoca=ep, ghsl_ano=m5.GHSL_ANO[ep], construido_ha=b.sum() * HA, ghsl_ge2000_ha=g.sum() * HA,
                           pct_nosso_com_ghsl=100 * (b & g).sum() / max(b.sum(), 1),
                           pct_ghsl_no_nosso=100 * (b & g).sum() / max(g.sum(), 1),
                           f1=200 * (b & g).sum() / max(b.sum() + g.sum(), 1)))
    ext["ghsl"] = pd.DataFrame(linhas)
    linhas = []
    for ep in [e for e in EPOCAS if 1985 <= e <= 2015]:
        b = cl[ep] == 1
        w = (wsf > 0) & (wsf <= ep)
        linhas.append(dict(epoca=ep, construido_ha=b.sum() * HA, wsf_ha=w.sum() * HA,
                           pct_nosso_com_wsf=100 * (b & w).sum() / max(b.sum(), 1),
                           pct_wsf_no_nosso=100 * (b & w).sum() / max(w.sum(), 1)))
    ext["wsf"] = pd.DataFrame(linhas)

    # agricultura vs GLAD (legenda nao verificada: tabela crua)
    glad_tabs = {}
    for ep in (2000, 2005, 2010, 2015, 2020):
        gl = le(VAL / f"glad_{ep}.tif")
        ag = np.isin(cl[ep], (2, 3))
        tot = ag.sum()
        vals, cnt = np.unique(gl[gl != 255], return_counts=True)
        rows = []
        for v, n in zip(vals, cnt):
            ov = (ag & (gl == v)).sum()
            if ov >= 0.02 * tot:
                rows.append(dict(valor_glad=int(v), area_glad_ha=n * HA, sobreposicao_ha=ov * HA,
                                 pct_da_nossa_agri=100 * ov / tot, pct_do_valor_que_e_nossa_agri=100 * ov / n))
        glad_tabs[ep] = (pd.DataFrame(rows).sort_values("sobreposicao_ha", ascending=False), tot * HA)
    # CCI
    linhas = []
    for ep in (2000, 2005, 2010, 2015, 2020):
        cc = le(VAL / f"cci_{ep}.tif")
        crop = np.isin(cc, CCI_CROP)
        for nome, ag in (("2+3", np.isin(cl[ep], (2, 3))), ("2", cl[ep] == 2)):
            linhas.append(dict(epoca=ep, nossa=nome, nossa_ha=ag.sum() * HA, cci_crop_ha=crop.sum() * HA,
                               pct_nossa_em_cci=100 * (ag & crop).sum() / max(ag.sum(), 1),
                               pct_cci_na_nossa=100 * (ag & crop).sum() / max(crop.sum(), 1)))
    ext["cci"] = pd.DataFrame(linhas)
    # WorldCover 40 / IO crops (2020)
    wc = le(VAL / "worldcover_2021.tif"); io = le(VAL / "io_lulc_2020.tif")
    linhas = []
    for nome, ref in (("WorldCover 2021 cropland (40)", wc == 40), ("IO LULC 2020 crops (5)", io == 5)):
        for k, ag in (("2+3", np.isin(cl[2020], (2, 3))), ("2", cl[2020] == 2)):
            linhas.append(dict(referencia=nome, nossa=k, nossa_ha=ag.sum() * HA, ref_ha=ref.sum() * HA,
                               pct_nossa_na_ref=100 * (ag & ref).sum() / max(ag.sum(), 1),
                               pct_ref_na_nossa=100 * (ag & ref).sum() / max(ref.sum(), 1)))
    ext["wc"] = pd.DataFrame(linhas)

    # LUCO
    linhas = []
    for ano, eps in ((1982, (1979, 1985)), (1991, (1990, 1995)), (2001, (2000, 2005))):
        gdf = gpd.read_file(RAW / "luco" / f"ulu_maputo_{ano}" / f"ulu_maputo_{ano}.shp")
        cobertura = m5.rast_geom(gdf.geometry)
        cod = gdf["N_II_C"].astype(str)
        luco_ag = m5.rast_geom(gdf[cod == "3.0.3"].geometry)
        built_codes = [c for c, (d, _) in m5.CROSS.items() if d == 1]
        luco_bt = m5.rast_geom(gdf[cod.isin(built_codes)].geometry)
        for ep in eps:
            c = cl[ep]
            ag = np.isin(c, (2, 3)) & cobertura
            linhas.append(dict(luco=ano, epoca=ep, luco_agri_ha=luco_ag.sum() * HA, nossa_agri_na_cobertura_ha=ag.sum() * HA,
                               pct_luco_agri_que_e_nossa_23=100 * (luco_ag & ag).sum() / max(luco_ag.sum(), 1),
                               pct_luco_agri_que_e_nossa_2=100 * (luco_ag & (c == 2)).sum() / max(luco_ag.sum(), 1),
                               pct_nossa_agri_em_luco_agri=100 * (luco_ag & ag).sum() / max(ag.sum(), 1),
                               luco_construido_inequivoco_ha=luco_bt.sum() * HA,
                               pct_luco_construido_que_e_nosso=100 * (luco_bt & (c == 1)).sum() / max(luco_bt.sum(), 1)))
    ext["luco"] = pd.DataFrame(linhas)
    for k, v in ext.items():
        v.to_csv(AREAS / f"qa_externo_{k}.csv", index=False)

    # ---------------- figuras ----------------
    figuras(cl, cid)

    # ---------------- sanidade ----------------
    s_built = cid[1]
    quedas = [(a, b, s_built[a], s_built[b]) for a, b in zip(EPOCAS[:-1], EPOCAS[1:]) if s_built[b] < s_built[a] * 0.99]
    z = cid[2]
    saltos = []
    for i, ep in enumerate(EPOCAS):
        for j in (i - 1,):
            if j >= 0:
                r = z[ep] / z[EPOCAS[j]] - 1
                if abs(r) > 0.30:
                    saltos.append((EPOCAS[j], ep, z[EPOCAS[j]], z[ep], 100 * r))
    desvio = []
    for i in range(1, len(EPOCAS) - 1):
        viz = (z[EPOCAS[i - 1]] + z[EPOCAS[i + 1]]) / 2
        r = z[EPOCAS[i]] / viz - 1
        if abs(r) > 0.30:
            desvio.append((EPOCAS[i], z[EPOCAS[i]], viz, 100 * r))
    expl = []
    for a, b, *_ in saltos:
        t = pd.read_csv(AREAS / f"transicoes_{a}_{b}.csv"); t = t[t.ambito == "cidade"]
        sai = t[(t.de == 2) & (t.para != 2)].sort_values("ha", ascending=False).head(3)
        ent = t[(t.para == 2) & (t.de != 2)].sort_values("ha", ascending=False).head(3)
        expl.append((a, b, ", ".join(f"2→{int(r.para)}: {r.ha:.0f} ha" for r in sai.itertuples()),
                     ", ".join(f"{int(r.de)}→2: {r.ha:.0f} ha" for r in ent.itertuples())))

    escreve_md(oob, rot, cid, bb, ext, glad_tabs, conv, quedas, saltos, desvio, expl)
    log("ok")


def figuras(cl, cid):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch
    import ardosia_palette as ap
    ap.apply_ardosia()
    cor = {1: ap.GRAFITE, 2: ap.TERRACOTA, 3: ap.OCRE, 4: ap.PETROLEO, 5: ap.VIZ_DIVERGING[4], 6: ap.ARDOSIA_MED, 7: ap.FILETE}
    lab = {1: "1 Construído", 2: "2 Agricultura de baixada", 3: "3 Sequeiro e mosaico", 4: "4 Arbórea e arbustiva",
           5: "5 Herbácea e húmidas", 6: "6 Água", 7: "7 Solo exposto"}
    cm = ListedColormap([ap.PAPEL_FIG] + [cor[k] for k in range(1, 8)])
    norm = BoundaryNorm(np.arange(-0.5, 8.5, 1), cm.N)
    fig, axs = plt.subplots(4, 4, figsize=(18, 21))
    for ax in axs.ravel():
        ax.set_axis_off(); ax.grid(False)
    for ax, ep in zip(axs.ravel(), EPOCAS):
        ax.imshow(cl[ep], cmap=cm, norm=norm, interpolation="nearest")
        t = f"{ep}" + (" (MSS, legenda reduzida)" if ep == 1979 else " (cena 1984)" if ep == 1985 else " (cena abr/2011)" if ep == 2010 else "")
        ax.set_title(t, fontsize=11, loc="left", pad=4)
    lax = axs.ravel()[14]
    lax.legend(handles=[Patch(color=cor[k], label=lab[k]) for k in range(1, 8)], loc="center left", frameon=False, fontsize=11,
               title="Classes de cobertura", title_fontsize=12)
    axs.ravel()[15].text(0, 0.5, "Retângulo 32,40–32,75 E × 26,10–25,75 S\nGrade 30 m, EPSG:32736\nRandom Forest por época\nFiltro de moda 3×3",
                         fontsize=10, color=ap.PEDRA, va="center")
    fig.suptitle("Cobertura e uso do solo, Maputo, 1979–2026", x=0.05, ha="left", fontsize=16)
    fig.savefig(FIGC / "mapas_classes.png", dpi=110)
    plt.close(fig)

    # area empilhada
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.stackplot(cid.index, [cid[k] / 1000 for k in range(1, 8)], colors=[cor[k] for k in range(1, 8)],
                 labels=[lab[k] for k in range(1, 8)])
    ax.set_ylabel("área (mil ha)"); ax.set_xlabel("época")
    ax.set_title("Classes na área terrestre da Cidade de Maputo", fontsize=13)
    ax.axvline(1979.5, color=ap.PEDRA, lw=0.8, ls=":")
    ax.text(1980, ax.get_ylim()[1] * 0.02, "1979: legenda reduzida", fontsize=8, color=ap.TEXTO_ESC if False else ap.GRAFITE)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)
    ax.set_xticks(EPOCAS); ax.set_xticklabels(EPOCAS, rotation=60)
    fig.savefig(FIGC / "area_empilhada_cidade.png", dpi=150); plt.close(fig)

    # linhas classe 1 e 2
    fig, ax = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)
    for a, k, c in ((ax[0], 1, ap.GRAFITE), (ax[1], 2, ap.TERRACOTA)):
        a.plot(cid.index, cid[k], marker="o", color=c)
        a.set_ylabel("ha"); a.set_title(lab[k], fontsize=11)
        for ep in (1979, 1985, 2010, 2026):
            a.plot([ep], [cid.loc[ep, k]], marker="o", mfc="none", mec=ap.PEDRA, ms=11, lw=0)
    ax[1].set_xticks(EPOCAS); ax[1].set_xticklabels(EPOCAS, rotation=60)
    ax[0].text(0.01, 0.04, "círculos vazios: épocas com ressalva (1979 MSS; 1985 e 2010 cena única; 2026 sem MAD)",
               transform=ax[0].transAxes, fontsize=8, color=ap.PEDRA)
    fig.suptitle("Construído e agricultura de baixada, Cidade de Maputo", x=0.1, ha="left", fontsize=13)
    fig.savefig(FIGC / "linhas_classe1_classe2.png", dpi=150); plt.close(fig)

    # mapa do ano de conversao
    cv = le(CLS / "conversao_agri_construido.tif")
    anos = [e for e in EPOCAS if e > 1979]
    from matplotlib.colors import ListedColormap as LC
    seq = ap.VIZ_SEQUENTIAL
    import matplotlib as mpl
    cmap = mpl.colormaps["ardosia_seq"].resampled(len(anos))
    fig, ax = plt.subplots(figsize=(9, 10))
    fundo = np.where(np.isin(cl[2026], (1,)), 1, np.where(cl[2026] == 6, 2, 0))
    ax.imshow(fundo, cmap=LC([ap.PAPEL_FIG, ap.FILETE_CL, ap.ARDOSIA_NEV]), vmin=0, vmax=2, interpolation="nearest")
    ys, xs = np.where(cv > 0)
    sc = ax.scatter(xs, ys, c=[anos.index(int(a)) for a in cv[ys, xs]], s=1.2, cmap=cmap, vmin=-0.5, vmax=len(anos) - 0.5, marker="s")
    cb = fig.colorbar(sc, ax=ax, ticks=range(len(anos)), shrink=0.6)
    cb.ax.set_yticklabels(anos)
    cb.set_label("ano da conversão estável (agricultura para construído)")
    ax.set_axis_off(); ax.grid(False)
    ax.set_title("Frentes de conversão de áreas agrícolas em construído", fontsize=13)
    fig.savefig(FIGC / "mapa_ano_conversao.png", dpi=150); plt.close(fig)


def escreve_md(oob, rot, cid, bb, ext, glad_tabs, conv, quedas, saltos, desvio, expl):
    L = []
    w = L.append
    w("# QA da classificação (30 m, EPSG:32736)\n")
    w("Gerado por `scripts/08_qa_classificacao.py` a partir de `05_rotulos.py`, `06_classificar.py` e `07_areas_transicoes.py`. "
      "Números das tabelas lidos de `dados/proc/class/oob.json`, `dados/proc/rotulos/rotulos_resumo.json` e `dados/proc/areas/`.\n")
    w("## 1. Rótulos de treino\n")
    p = rot["params"]
    w("### 1.1 Âncora 2020 e regras\n")
    w("- Construído: WorldCover 2021 = 50 E IO LULC 2020 = Built E GHSL-BUILT-S 2020 ≥ 2000 m² por célula de 100 m.\n"
      "- Arbórea/arbustiva: WC 10 E IO Trees; mangal: WC 95 sozinho (subclasse 41 marcada na coluna `sub`).\n"
      "- Herbácea/húmida: (WC 30 ou 90) E IO (Rangeland ou Flooded vegetation), fora de polígonos OSM agrícolas.\n"
      "- Água: WC 80 E IO Water. Solo exposto: WC 60 E IO Bare.\n"
      "- Agricultura: polígonos OSM `farmland`, `allotments`, `greenhouse_horticulture` (`orchard` não usado) OU (WC 40 E IO Crops), com GHSL 2020 ≤ 500.\n"
      f"- Divisão 2 × 3: classe 2 se altitude < {p['ELEV_BAIXADA']:.0f} m E TPI < {p['TPI_BAIXADA']:.0f}, ou dentro de {p['BUF_WETLAND']:.0f} m de polígono OSM `wetland`; caso contrário classe 3.\n"
      "- Píxeis que cumprem mais de uma regra foram descartados "
      f"({rot['ancora_conflito_px']} px); máscaras erodidas em 1 píxel (3×3); classes com menos de 300 px após erosão ficaram sem erosão "
      f"(classes {rot.get('ancora_sem_erosao')}: solo exposto, 1 093 px antes da erosão e 70 depois).\n"
      f"- Amostragem aleatória estratificada: reserva de até {p['N_POOL']} pontos por classe (`pool_2020.parquet`); a âncora `treino_2020` usa "
      f"até {p['N_ANCORA']} por classe. Pontos disponíveis na âncora: {rot['treino_2020']}.\n")
    w("**Escolha 2 × 3 (limiares realmente usados).** Cerca de 98% dos píxeis dos polígonos OSM agrícolas estão abaixo de 15 m (mediana ≈ 5 m, "
      "p90 ≈ 12 m; ver `dados/fig/class/rotulos_2v3.png`), de modo que o critério altimétrico praticamente não discrimina nos vales do Infulene e Mahotas: "
      "quem separa é o TPI < 0, que envia ≈ 27% dos píxeis OSM (bordas e microrelevo mais alto da baixada) para a classe 3. "
      "O buffer de 100 m de zonas húmidas OSM acrescenta apenas ≈ 1% dos píxeis. A divisão é, portanto, um proxy topográfico e não uma observação de uso; "
      "a classe 3 tem apenas 636 píxeis de âncora e é a de menor confiabilidade. Suavizar o TPI (5×5, 9×9) não alterou a proporção (73,7% e 74,9% em classe 2).\n")
    w("### 1.2 Propagação temporal\n")
    w("Ângulo espectral entre o vetor 2020 e o da época t em (verde, vermelho, NIR, SWIR1, SWIR2; 1979: verde, vermelho, NIR), calculado sobre pseudo-invariantes: "
      f"{rot['invariantes']['agua_profunda']} pontos de água profunda (WC80 E IO água, erodida 3 px) e {rot['invariantes']['nucleo_construido_KaMpfumo']} pontos do núcleo "
      "construído antigo (GHSL 1975 ≥ 5000 e GHSL 2020 ≥ 5000 em KaMpfumo, erodido). Consistência com GHSL(t) (ano GHSL mais próximo): "
      "construído exige ≥ 2000; agricultura, árvore e herbácea exigem < 500.\n")
    w("**Desvio documentado do limiar.** O percentil 20 literal dos invariantes deixava as classes água (ângulos muito mais dispersos que no núcleo construído) "
      "e, em épocas afastadas de 2020, todas as classes agrícolas com poucos pontos (água 6–25 pontos; classe 3 < 100). A regra adotada: limiar da água calculado "
      "sobre os invariantes de água e o das demais classes sobre os do núcleo construído, no mesmo percentil; começa no p20 e sobe para p50 e p80 apenas "
      f"enquanto alguma classe retiver menos de min(150; 50% do pool) pontos. Percentil e limiares por época:\n")
    rows = []
    for ep, v in rot["angulos"].items():
        rows.append(dict(epoca=int(ep), bandas=",".join(v["bandas"]), percentil=v["percentil_usado"], limiar_terra_rad=v["limiar_terra_rad"],
                         limiar_agua_rad=v["limiar_agua_rad"], p20_terra=v["p20_nucleo"], p20_agua=v["p20_agua"]))
    w(md(pd.DataFrame(rows)))
    w("Limite de pontos propagados: 1 500 por classe e época (reserva 6 000). Pontos LUCO: até 1 000 por classe, apenas se coerentes espectralmente na época-alvo "
      "(construído NDVI<0,40 e NDWI<0,20; agricultura NDWI<0,15 e NDVI>−0,05; arbórea NDVI>0,15 e NDWI<0,15; herbácea NDWI<0,20; água NDWI>−0,05; solo exposto NDVI<0,25 e NDWI<0,10; NDWI=(verde−NIR)/(verde+NIR)).\n")
    w("### 1.3 Crosswalk LUCO → classes do estudo\n")
    cw = pd.read_csv(ROT / "luco_crosswalk.csv")
    cw = cw[cw.ano == 2001].drop(columns=["ano"]).rename(columns={"n_poligonos": "n_pol_2001", "area_ha": "area_ha_2001"})
    w("Nomenclatura: `ULU_Maputo_Nomenclatura_PT.pdf` (Henriques, Correia e Rolo, 2023). \"excluido\" = classe ambígua (baixa densidade, equipamentos, vias, "
      "vazio urbano, emergente), não usada. LUCO 1982 serve a 1979 e 1985; 1991 a 1990, 1995 e 1997; 2001 a 2000 e 2005. Áreas de todos os anos em `dados/proc/rotulos/luco_crosswalk.csv`.\n")
    w(md(cw))
    w("### 1.4 Contagem de pontos de treino por época, classe e origem\n")
    rows = []
    for ep, lst in rot["contagem"].items():
        for r in lst:
            rows.append(dict(epoca=int(ep), classe=int(r["classe"]), origem=r["origem"], n=int(r["n"])))
    dfc = pd.DataFrame(rows).pivot_table(index="epoca", columns=["classe", "origem"], values="n", aggfunc="sum", fill_value=0)
    dfc.columns = [f"{a}/{b}" for a, b in dfc.columns]
    w(md(dfc.reset_index()))
    w("Contagens efetivamente usadas no treino (após remover pontos sem feature): ver 2.1.\n")

    w("## 2. Modelos\n")
    w("Random Forest, 500 árvores, `class_weight=\"balanced_subsample\"`, `random_state=42`. Atributos: bandas disponíveis, NDVI/NDBI/MNDWI/BSI, "
      "SMAD/EMAD/BCMAD onde existem, altitude, declive, TPI. Épocas sem MAD (1985, 2010, 2026) e 1979 (só verde, vermelho, NIR, NDVI) têm modelos próprios sem imputação. "
      "Filtro de moda 3×3 (empate favorece o píxel central). Regra temporal: construído em t−1 e t+1 não pode ser agrícola (2/3) em t.\n")
    w("### 2.1 Exatidão fora-do-saco (OOB) e F1 por classe\n")
    rows = []
    for ep in EPOCAS:
        o = oob["oob"][str(ep)]
        r = dict(epoca=ep, n=o["n"], acc_oob=o["acc"])
        for k in range(1, 8):
            r[f"F1_{k}"] = o["f1"].get(str(k), np.nan)
        rows.append(r)
    w(md(pd.DataFrame(rows)))
    w("**Leitura.** O OOB e o CV medem a reprodução dos rótulos (derivados de WorldCover, IO LULC, GHSL, OSM, LUCO), não a exatidão contra verdade de campo; "
      "pontos vizinhos são autocorrelacionados, logo o OOB é otimista. A validação independente de 2000, 2010 e 2020 por interpretação visual "
      "(METODOLOGIA, seção 5) não faz parte deste passo.\n")
    w("### 2.2 Validação cruzada espacial (5 dobras, blocos de 3 km)\n")
    rows = []
    for ep, v in oob["cv_bloques"].items():
        r = dict(epoca=int(ep), blocos=v["n_blocos"], acc=v["acc"])
        for k in range(1, 8):
            r[f"F1_{k}"] = v["f1"].get(str(k), np.nan)
        rows.append(r)
    w(md(pd.DataFrame(rows)))
    w("### 2.3 Importância das variáveis (top 5) e atributos por época\n")
    rows = [dict(epoca=ep, atributos=", ".join(oob["features"][str(ep)]),
                 top5=", ".join(f"{n} {v}" for n, v in oob["oob"][str(ep)]["top_importancias"])) for ep in EPOCAS]
    w(md(pd.DataFrame(rows)))
    w(f"Regra temporal: píxeis corrigidos (construído→agrícola→construído) por época intermediária: {oob['regra_temporal_px_corrigidos']}. "
      f"Reversões construído→outra classe→construído mantidas (a regra não alisa além do especificado): {oob['reversoes_construido_nao_corrigidas_px']}.\n")
    if "1979" in oob["notas"]:
        w(f"**1979.** {oob['notas']['1979']}.\n")

    w("## 3. Áreas (ha)\n")
    w("Área terrestre da Cidade de Maputo = união dos distritos municipais exceto KaNyaka (HDX COD-AB), 29 861 ha; bbox = grade inteira (inclui mar, Matola, Marracuene).\n")
    t = cid.copy(); t.columns = [f"c{c}" for c in t.columns]
    w("### Cidade\n"); w(md(t.reset_index().round(0)))
    t = bb.copy(); t.columns = [f"c{c}" for c in t.columns]
    w("### Bbox (c0 = sem dado; 2020 tem lacuna de 3 667 ha no mar, sem efeito na terra)\n"); w(md(t.reset_index().round(0)))
    w("### Conversão agricultura → construído (consecutivos, cidade)\n")
    c = conv[(conv.ambito == "cidade") & (conv.consecutivo)][["t0", "t1", "area_agri_inicial_ha", "ha_agri_para_construido", "ha_agri_ano", "pct_agri_inicial",
                                                             "area_zv_inicial_ha", "ha_zv_para_construido", "ha_zv_ano", "pct_zv_inicial"]]
    w(md(c))
    w("Os fluxos de agricultura→construído por intervalo são pequenos frente à troca entre classes 2, 3 e 5 (ruído de classificação), ver seção 5. "
      "Em 1979→1985 a classe 3 (1979) inclui toda a vegetação: usar só a classe 2.\n")

    w("## 4. Concordância externa\n")
    w("### 4.1 Construído × GHSL-BUILT-S (≥ 2000 m² por célula de 100 m; ano GHSL mais próximo; bbox)\n")
    w(md(ext["ghsl"]))
    w("### 4.2 Construído × WSF Evolution (valor = ano de detecção; semântica PARCIAL, ver legendas.json)\n")
    w(md(ext["wsf"]))
    w("### 4.3 Agricultura (2+3) × GLAD (tabela crua, legenda NÃO verificada; sem rótulos)\n")
    w("Valores GLAD com sobreposição ≥ 2% da nossa agricultura. Sem nomes de classe: não interpretar como cropland.\n")
    for ep, (tab, tot) in glad_tabs.items():
        w(f"**{ep}** (nossa agricultura 2+3: {tot:,.0f} ha)\n"); w(md(tab))
    w("### 4.4 Agricultura × ESA CCI (cropland = 10, 11, 12, 20, 30, 40; 300 m, reamostrado)\n")
    w(md(ext["cci"]))
    w("### 4.5 Agricultura 2020 × WorldCover 2021 e IO LULC 2020 (estas referências geraram parte dos rótulos de 2020; concordância não é independente)\n")
    w(md(ext["wc"]))
    w("### 4.6 × LUCO (área de polígonos; LUCO cobre só a cidade)\n")
    w(md(ext["luco"]))
    w("LUCO `Agricultura e pecuária` (3.0.3) são talhões hortícolas e quintas muradas e a classe 3.0.3 foi usada nos rótulos de treino (≤ 2005), logo a concordância das épocas 1979–2005 não é independente.\n")

    w("## 5. Problemas conhecidos por época\n")
    w("- **1979 (MSS, 9/jun/1979, Tier 2):** 3 bandas (verde, vermelho, NIR), 60 m reamostrado, TOA, sem SWIR. Legenda reduzida (1, 2, 3, 6, 7); a classe 3 contém toda a vegetação fora da baixada "
      "(inclui arbórea e herbácea) e a classe 2 é regra topográfica + NDVI. Só ordem de grandeza; não comparar classe 3 com épocas posteriores.\n"
      "- **1985 (cena única TM, 1/jun/1984):** sem MAD; uma data apenas; construído subdetectado (revocação com GHSL ≈ 0,55) e queda do construído vs 1979 é artefato de método.\n"
      "- **1990–2007 (GeoMAD, COUNT 6–17):** épocas com COUNT baixo (1990, 1997 = 6) ruidosas; 1997 tem queda do construído (≈ −13% na cidade) em relação a 1995 e 2000.\n"
      "- **2010 (cena única TM, 9/abr/2011):** abril, fim da estação chuvosa: vegetação mais verde, mais confusão 2/5; sem MAD.\n"
      "- **2020:** 2,5% de NaN na composição, quase todos no mar (3 667 ha no bbox); é também a época-âncora (treino direto), com ajuste mais fiel aos rótulos que nas demais, o que explica parte do salto da classe 2 de 2017 para 2020.\n"
      "- **2026:** mediana de 12 cenas de estação seca (mai–set), sem MAD, modelo sem SMAD/EMAD/BCMAD; as outras épocas OLI têm MAD anual.\n"
      "- **Classe 3 e classe 7:** poucos pontos de âncora (636 e 70 px erodidos). Após o ano 2000 a classe 3 colapsa para poucas centenas de hectares porque os pontos propagados "
      "são os de píxeis que continuam agrícolas e espectralmente estáveis; tratar classe 3 como indicativa. Classe 4 × 5 oscila muito entre épocas (arbórea vs herbácea), "
      "sem relação com mudança real.\n"
      "- **Treino enviesado para a estabilidade:** a propagação exige ângulo pequeno em relação a 2020 e GHSL consistente, logo as áreas que mudaram (justamente as periferias em adensamento) "
      "ficam sub-representadas no treino das épocas antigas; o construído periférico é subestimado em 1985–2000.\n")

    w("## 6. Sanidade\n")
    w("Construído na área terrestre da cidade (ha) por época: " + ", ".join(f"{ep}: {cid.loc[ep, 1]:,.0f}" for ep in EPOCAS) + ".\n")
    if quedas:
        w("**Quedas do construído (> 1%) entre épocas consecutivas:**\n")
        for a, b, va, vb in quedas:
            w(f"- {a} → {b}: {va:,.0f} → {vb:,.0f} ha ({100*(vb/va-1):.1f}%).")
        w("\nO construído real não decresce; estas quedas são erro de classificação (sensibilidade do modelo por época), não demolição. "
          "Não foram corrigidas além da regra temporal especificada (que só trata a reversão para agricultura); ver contagem de reversões não corrigidas em 2.3.\n")
    else:
        w("Construído não decresce > 1% em nenhum intervalo.\n")
    rap = [(a, b, 100 * ((cid.loc[b, 1] / cid.loc[a, 1]) ** (1 / (b - a)) - 1)) for a, b in zip(EPOCAS[:-1], EPOCAS[1:])]
    rap = [r for r in rap if r[2] > 5]
    if rap:
        w("**Crescimento anual do construído > 5%/ano (cidade):** " + "; ".join(f"{a}→{b}: {r:.1f}%/ano" for a, b, r in rap) +
          ". Saltos assim em intervalos curtos (2005→2007) refletem diferenças entre composições, não expansão real, e inflam a conversão agricultura→construído do intervalo.\n")
    w("**Classe 2 (cidade): variações > 30% entre épocas consecutivas:**\n")
    if saltos:
        for a, b, va, vb, r in saltos:
            w(f"- {a} → {b}: {va:,.0f} → {vb:,.0f} ha ({r:+.0f}%).")
        w("")
        for a, b, s, e in expl:
            w(f"- Fluxos {a} → {b}: saídas da classe 2: {s}; entradas: {e}.")
        w("")
    else:
        w("Nenhum salto > 30%.\n")
    if desvio:
        w("Desvio > 30% em relação à média das épocas vizinhas: " + "; ".join(f"{ep} ({v:,.0f} ha vs {m:,.0f}, {r:+.0f}%)" for ep, v, m, r in desvio) + ".\n")
    w("Inspeção: os fluxos mostram troca entre classes 2 e 5 (agricultura de baixada × herbácea/zona húmida), isto é, confusão espectral entre hortas irrigadas e capim/pântano na mesma baixada, "
      "amplificada por diferenças sazonais e de sensor entre composições (1997 vs 2000: COUNT 6 vs 10; 2017 vs 2020: 2020 é âncora), e não conversão de terra. "
      "As tendências decenais (queda da classe 2 de ≈ 2 500 ha em 1990–1997 para ≈ 1 200–1 500 ha após 2015) são mais confiáveis do que as variações entre épocas vizinhas.\n")
    (QA / "classificacao.md").write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------- figuras da revisao (legenda agregada)
AGR_LAB = {1: "1 Construído", 2: "2 Zonas verdes (agricultura de baixada)", 3: "3 Sequeiro e mosaico (indicativo)",
           45: "4+5 Vegetação não cultivada", 6: "6 Água", 7: "7 Solo exposto"}
LUCO_ANOS = [1964, 1973, 1982, 1991, 2001]


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    import ardosia_palette as ap
    ap.apply_ardosia()
    FIGC.mkdir(parents=True, exist_ok=True)
    entrada = PROC / "class_final"
    cl = {ep: le(entrada / f"{ep}.tif") for ep in EPOCAS}
    ag = pd.read_csv(AREAS / "areas_agregado_classe_epoca.csv")
    cid = ag[ag.ambito == "cidade"].pivot(index="epoca", columns="classe_agr", values="ha")
    luco = pd.read_csv(AREAS / "areas_luco.csv")
    lut = np.array([0, 1, 2, 3, 4, 4, 5, 6])        # 1..7 -> indice agregado (4+5 juntos)
    cor = {1: ap.GRAFITE, 2: ap.TERRACOTA, 3: ap.OCRE, 45: ap.PETROLEO, 6: ap.ARDOSIA_MED, 7: ap.FILETE}
    ordem = [1, 2, 3, 45, 6, 7]
    cm = ListedColormap([ap.PAPEL_FIG] + [cor[k] for k in ordem])
    norm = BoundaryNorm(np.arange(-0.5, 7.5, 1), cm.N)

    # --- mapas por epoca
    fig, axs = plt.subplots(4, 4, figsize=(18, 21))
    for ax in axs.ravel():
        ax.set_axis_off(); ax.grid(False)
    for ax, ep in zip(axs.ravel(), EPOCAS):
        ax.imshow(lut[cl[ep]], cmap=cm, norm=norm, interpolation="nearest")
        t = f"{ep}" + (" (MSS, excluída das séries)" if ep == 1979 else " (cena 1984)" if ep == 1985 else " (cena abr/2011)" if ep == 2010 else "")
        ax.set_title(t, fontsize=11, loc="left", pad=4)
    axs.ravel()[14].legend(handles=[Patch(color=cor[k], label=AGR_LAB[k]) for k in ordem], loc="center left", frameon=False,
                           fontsize=11, title="Classes (legenda agregada)", title_fontsize=12)
    axs.ravel()[15].text(0, 0.5, "Retângulo 32,40–32,75 E × 26,10–25,75 S\nGrade 30 m, EPSG:32736\nRandom Forest por época\n"
                         "Pós-processamento de consistência\n(construído monotônico; tremulação 2 e 5)", fontsize=10, color=ap.PEDRA, va="center")
    fig.suptitle("Cobertura e uso do solo, Maputo, 1979–2026 (classificação final)", x=0.05, ha="left", fontsize=16)
    fig.savefig(FIGC / "mapas_classes.png", dpi=110); plt.close(fig)

    # --- area empilhada (1985-2026)
    eps = [e for e in EPOCAS if e != 1979]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.stackplot(eps, [cid.loc[eps, k] / 1000 for k in ordem], colors=[cor[k] for k in ordem], labels=[AGR_LAB[k] for k in ordem])
    ax.set_ylabel("área (mil ha)"); ax.set_xlabel("época")
    ax.set_title("Classes na área terrestre da Cidade de Maputo, 1985–2026", fontsize=13)
    ax.text(0.01, -0.28, "1979 excluída das séries quantitativas (MSS, legenda reduzida).", transform=ax.transAxes, fontsize=8, color=ap.PEDRA)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)
    ax.set_xticks(eps); ax.set_xticklabels(eps, rotation=60)
    fig.savefig(FIGC / "area_empilhada_cidade.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # --- linhas classe 1 e classe 2 com LUCO
    cob = luco.cidade_ha.iloc[0], luco.pct_cidade_coberta.iloc[0]
    fig, axs = plt.subplots(2, 1, figsize=(9.5, 7.5), sharex=True)
    for a, k, c in ((axs[0], 1, ap.GRAFITE), (axs[1], 2, ap.TERRACOTA)):
        a.plot(eps, cid.loc[eps, k], marker="o", color=c, label="Classificação 30 m (cidade inteira)")
        a.plot([1979], [cid.loc[1979, k]], marker="x", color=ap.PEDRA, lw=0, ms=8, label="1979 (excluída)")
        lk = luco[luco.classe_agr.astype(str) == str(k)].set_index("ano").ha
        a.plot(lk.index, lk.values, marker="D", ms=7, lw=0, mfc=ap.PAPEL_FIG, mec=ap.ARDOSIA_MED, mew=1.6,
               label="LUCO (só área coberta)")
        for ep in (1985, 2010, 2026):
            a.plot([ep], [cid.loc[ep, k]], marker="o", mfc="none", mec=ap.PEDRA, ms=11, lw=0)
        a.set_ylabel("ha"); a.set_title(AGR_LAB[k], fontsize=11, loc="left")
        a.set_ylim(bottom=0)
    axs[0].legend(loc="upper left", frameon=False, fontsize=8)
    axs[1].set_xticks([1964, 1973, 1979, 1982] + eps); axs[1].set_xticklabels([1964, 1973, 1979, 1982] + eps, rotation=60, fontsize=8)
    fig.text(0.1, 0.005, f"Círculos vazios: cena única (1985, 2010) ou sem MAD (2026). LUCO 1964, 1973, 1982, 1991, 2001 cobre {cob[1]:.0f}% da área terrestre da cidade;\n"
             "os pontos LUCO não são comparáveis em nível com a série de 30 m (cobertura parcial).", fontsize=7.5, color=ap.PEDRA, va="bottom")
    fig.suptitle("Construído e zonas verdes, Cidade de Maputo", x=0.1, ha="left", fontsize=13)
    fig.tight_layout(rect=(0, 0.045, 1, 0.97))
    fig.savefig(FIGC / "linhas_classe1_classe2.png", dpi=150); plt.close(fig)

    # --- mapa do ano de conversao
    cv = le(entrada / "conversao_agri_construido.tif")
    anos = [e for e in EPOCAS if e > 1979]
    cmap = mpl.colormaps["ardosia_seq"].resampled(len(anos))
    fig, ax = plt.subplots(figsize=(9, 10))
    fundo = np.where(cl[2026] == 1, 1, np.where(cl[2026] == 6, 2, 0))
    ax.imshow(fundo, cmap=ListedColormap([ap.PAPEL_FIG, ap.FILETE_CL, ap.ARDOSIA_NEV]), vmin=0, vmax=2, interpolation="nearest")
    ys, xs = np.where(cv > 0)
    sc = ax.scatter(xs, ys, c=[anos.index(int(a)) for a in cv[ys, xs]], s=1.2, cmap=cmap, vmin=-0.5, vmax=len(anos) - 0.5, marker="s")
    cb = fig.colorbar(sc, ax=ax, ticks=range(len(anos)), shrink=0.6)
    cb.ax.set_yticklabels(anos)
    cb.set_label("ano da conversão estável (agricultura para construído)")
    ax.set_axis_off(); ax.grid(False)
    ax.set_title("Frentes de conversão de áreas agrícolas em construído", fontsize=13)
    fig.savefig(FIGC / "mapa_ano_conversao.png", dpi=150); plt.close(fig)
    log("figuras ok:", FIGC)


if __name__ == "__main__":
    if "--run1" in sys.argv:
        main_run1()
    else:
        main()
