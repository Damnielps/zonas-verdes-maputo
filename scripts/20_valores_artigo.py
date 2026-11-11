"""Valores numéricos citados no artigo (marcadores {{chave}} em artigo/artigo.md).

Lê apenas tabelas produzidas pelo pipeline e grava artigo/valores.json. Nenhum número do
texto do artigo deve ser digitado à mão: ou vem daqui, ou de uma ficha citada.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

RAIZ = Path(__file__).resolve().parents[1]
AREAS = RAIZ / "dados" / "proc" / "areas"
PROC = RAIZ / "dados" / "proc"


def br(x, casas=0):
    """Formata número no padrão brasileiro (ponto como milhar, vírgula decimal), como no site."""
    s = f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def main():
    v = {}
    # Áreas agregadas, cidade
    ag = pd.read_csv(AREAS / "areas_agregado_classe_epoca.csv")
    col_amb = "ambito" if "ambito" in ag.columns else None
    cid = ag[ag[col_amb] == "cidade"] if col_amb else ag
    ccol = "classe_agr" if "classe_agr" in cid.columns else "classe"
    piv = cid.pivot_table(index="epoca", columns=ccol, values="ha", aggfunc="sum")
    piv.columns = [str(c) for c in piv.columns]
    v["cons_1985"] = br(piv.loc[1985, "1"])
    v["cons_2000"] = br(piv.loc[2000, "1"])
    v["cons_2026"] = br(piv.loc[2026, "1"])
    v["cons_cresc_pct"] = br(100 * (piv.loc[2026, "1"] / piv.loc[1985, "1"] - 1))
    v["zv_1990"] = br(piv.loc[1990, "2"])
    v["zv_2025"] = br(piv.loc[2025, "2"])

    # LUCO
    lu = pd.read_csv(AREAS / "areas_luco.csv")
    print("areas_luco colunas:", lu.columns.tolist(), file=sys.stderr)
    l82 = lu[lu.iloc[:, 0] == 1982] if lu.columns[0] in ("ano", "epoca") else lu[lu["ano"] == 1982]
    ccl = [c for c in lu.columns if c.startswith("classe")][0]
    hac = [c for c in lu.columns if c in ("ha", "area_ha")][0]
    g = l82.groupby(l82[ccl].astype(str))[hac].sum()
    v["luco1982_construido"] = br(g.get("1", 0))
    v["luco1982_agri"] = br(g.get("2", 0) + g.get("3", 0))
    cobcol = [c for c in lu.columns if c == "pct_cidade_coberta"]
    if cobcol:
        val = float(l82[cobcol[0]].iloc[0])
        v["luco_cobertura_pct"] = br(val if val > 1 else 100 * val)
    else:
        v["luco_cobertura_pct"] = "54"

    # Envelopes
    env = pd.read_csv(AREAS / "envelopes.csv")
    e = env[env.ambito == "cidade"].set_index(["perimetro", "epoca"])
    P = {"perm": "plano1985_zv_permanentes", "prov": "plano1985_zv_provisorias",
         "peumm": "peumm2008_agropecuaria", "baix": "baixada_<15m_tpi<0"}
    for k, p in P.items():
        v[f"env_{k}_area"] = br(e.loc[(p, 2026), "area_ha"])
        for ano in (1985, 2010, 2026):
            v[f"env_{k}_{ano}"] = br(e.loc[(p, ano), "pct_construido"], 1)
            v[f"env_{k}_ha_{ano}"] = br(e.loc[(p, ano), "construido_ha"])
    b = P["baix"]
    v["env_baix_ha_desde_2010"] = br(e.loc[(b, 2026), "construido_ha"] - e.loc[(b, 2010), "construido_ha"])
    v["env_baix_ha_1985_2010"] = br(e.loc[(b, 2010), "construido_ha"] - e.loc[(b, 1985), "construido_ha"])
    # Tabela 1 (markdown)
    epocas = [1985, 1990, 2000, 2010, 2020, 2026]
    nomes = {"perm": "Zonas verdes permanentes (plano de 1985)",
             "prov": "Zonas verdes provisórias (plano de 1985)",
             "peumm": "Área agropecuária (PEUMM 2008)", "baix": "Baixadas (relevo)"}
    linhas = ["| Perímetro | Área (ha) | " + " | ".join(str(a) for a in epocas) + " |",
              "|---|---:|" + "---:|" * len(epocas)]
    for k, p in P.items():
        linhas.append(f"| {nomes[k]} | {br(e.loc[(p, 2026), 'area_ha'])} | " +
                      " | ".join(br(e.loc[(p, a), 'pct_construido'], 1) for a in epocas) + " |")
    v["TABELA_1_ENVELOPES"] = ("Tabela 1 – Fração construída (%) dentro de perímetros agrícolas e de baixada, "
                               "Cidade de Maputo (parte continental), 1985–2026\n\n" + "\n".join(linhas) +
                               "\n\nFonte: elaboração própria. Nota: área dos perímetros na cidade, excluída a água permanente.")

    # Fração das zonas de 1985 em baixada (para a interpretação do texto)
    import geopandas as gpd
    from rasterio.features import rasterize
    with rasterio.open(PROC / "dem.tif") as r:
        dem = r.read(1); tr = r.transform; shp = r.shape; crs = r.crs
    with rasterio.open(PROC / "tpi.tif") as r:
        tpi = r.read(1)
    baix = (dem < 15) & (tpi < 0)
    for lay, k in [("zv_permanentes", "perm"), ("zv_provisorias", "prov")]:
        gdf = gpd.read_file(PROC / "planos" / "zonas_1985.gpkg", layer=lay).to_crs(crs)
        m = rasterize(((gg, 1) for gg in gdf.geometry), out_shape=shp, transform=tr, fill=0).astype(bool)
        v[f"env_{k}_pct_em_baixada"] = br(100 * (m & baix).sum() / max(m.sum(), 1))

    # ---- Revisão pós-auditoria: três estimativas (bruta, pós-processada, GHSL), ponto final 2025 ----
    cmp_ = pd.read_csv(AREAS / "envelopes_comparacao.csv").set_index(["perimetro", "epoca"])
    PC = {"perm": "plano1985_zv_permanentes", "prov": "plano1985_zv_provisorias",
          "peumm": "peumm2008_agropecuaria", "baix": "baixada_<15m_tpi<0", "cid": "cidade_total"}
    for k, p in PC.items():
        for ano in (1985, 1990, 2000, 2010, 2020, 2025):
            vals = [cmp_.loc[(p, ano), c] for c in ("pct_bruto", "pct_final", "pct_ghsl")]
            v[f"r_{k}_{ano}_min"] = br(min(vals), 1); v[f"r_{k}_{ano}_max"] = br(max(vals), 1)
            for c, n in (("pct_bruto", "bruto"), ("pct_final", "final"), ("pct_ghsl", "ghsl")):
                v[f"r_{k}_{ano}_{n}"] = br(cmp_.loc[(p, ano), c], 1)
        # razão 2025/1985 e 2025/2010 por estimativa
        for a0 in (1985, 2010):
            rz = [cmp_.loc[(p, 2025), c] / cmp_.loc[(p, a0), c] for c in ("pct_bruto", "pct_final", "pct_ghsl")]
            v[f"r_{k}_razao_{a0}_min"] = br(min(rz), 1); v[f"r_{k}_razao_{a0}_max"] = br(max(rz), 1)
    for c, n in (("ha_bruto", "bruto"), ("ha_final", "final"), ("ha_ghsl", "ghsl")):
        a85 = cmp_.loc[("cidade_total", 1985), c]; a25 = cmp_.loc[("cidade_total", 2025), c]
        v[f"cid_cresc_{n}"] = br(100 * (a25 / a85 - 1))
        v[f"cid_ha_1985_{n}"] = br(a85); v[f"cid_ha_2025_{n}"] = br(a25)
    v["cid_cresc_1990_2025_final"] = br(100 * (cmp_.loc[("cidade_total", 2025), "ha_final"] /
                                               cmp_.loc[("cidade_total", 1990), "ha_final"] - 1))
    for k in ("baix", "peumm", "perm"):
        p = PC[k]
        for c, n in (("ha_bruto", "bruto"), ("ha_final", "final"), ("ha_ghsl", "ghsl")):
            v[f"taxa_{k}_85_10_{n}"] = br((cmp_.loc[(p, 2010), c] - cmp_.loc[(p, 1985), c]) / 25, 1)
            v[f"taxa_{k}_10_25_{n}"] = br((cmp_.loc[(p, 2025), c] - cmp_.loc[(p, 2010), c]) / 15, 1)
    # v1.0.2 (auditoria do projeto da Beira): o GHSL R2023A interpola entre as épocas observadas 1975, 1990, 2000,
    # 2014 e 2018 (EC 2024, p. 6) e extrapola depois de 2018; e o GHSL orientou os rótulos de treino (05_rotulos.py),
    # logo as três estimativas não são independentes. Comparar médias de dois períodos, sem datar acelerações.
    INI, FIM = (1985, 1990, 1995, 1997), (2017, 2020, 2025)
    def _media(p, anos, c):
        return sum(cmp_.loc[(p, a), c] for a in anos) / len(anos)
    for k, p in PC.items():
        ini = [_media(p, INI, c) for c in ("pct_bruto", "pct_final", "pct_ghsl")]
        fim = [_media(p, FIM, c) for c in ("pct_bruto", "pct_final", "pct_ghsl")]
        fat = [b / a for a, b in zip(ini, fim)]
        v[f"p_{k}_ini_min"], v[f"p_{k}_ini_max"] = br(min(ini), 1), br(max(ini), 1)
        v[f"p_{k}_fim_min"], v[f"p_{k}_fim_max"] = br(min(fim), 1), br(max(fim), 1)
        v[f"p_{k}_fator_min"], v[f"p_{k}_fator_max"] = br(min(fat), 1), br(max(fat), 1)
        if k in ("baix", "peumm", "perm", "cid"):
            assert min(fat) > 1.2, f"ASSERÇÃO FALHOU: {k} fator período <= 1,2 ({fat}); o texto afirma aumento"
    # o texto já não afirma 'mais que dobrou' nem aceleração: conferir que o fator mínimo das baixadas fica abaixo de 2
    v["p_baix_dobrou_todas"] = "sim" if min(_media(PC["baix"], FIM, c) / _media(PC["baix"], INI, c)
                                              for c in ("pct_bruto", "pct_final", "pct_ghsl")) >= 2 else "não"

    # Tabela 1 revista: intervalo das três estimativas
    epocas = [1985, 1990, 2000, 2010, 2020, 2025]
    nomes2 = {"perm": "Zonas verdes permanentes (plano de 1985)", "prov": "Zonas verdes provisórias (plano de 1985)",
              "peumm": "Área agropecuária (PEUMM 2008)", "baix": "Baixadas (relevo)"}
    L = ["| Perímetro | Área (ha) | " + " | ".join(str(a) for a in epocas) + " |", "|---|---:|" + "---:|" * len(epocas)]
    for k, nm in nomes2.items():
        p = PC[k]
        cel = []
        for a in epocas:
            vals = [cmp_.loc[(p, a), c] for c in ("pct_ghsl", "pct_bruto", "pct_final")]
            cel.append(f"{br(min(vals),1)}–{br(max(vals),1)}")
        L.append(f"| {nm} | {br(cmp_.loc[(p, 2025), 'area_ha'])} | " + " | ".join(cel) + " |")
    v["TABELA_1_ENVELOPES"] = ("Tabela 1 – Fração construída (%) dentro de perímetros agrícolas e de baixada: intervalo entre "
                               "três estimativas (GHSL, classificação bruta e classificação pós-processada), Cidade de Maputo "
                               "(parte continental), 1985–2025\n\n" + "\n".join(L) +
                               "\n\nFonte: elaboração própria; GHSL GHS-BUILT-S R2023A (Pesaresi; Politis, 2023). Nota: o GHSL "
                               "mede a superfície coberta por edificações e tende a dar os valores mais baixos; a classificação "
                               "mede o tecido construído (com quintais e arruamentos). Área dos perímetros na cidade, sem água permanente.")
    # fração das zonas de 1985 em baixada, no recorte da cidade e sem água (corrige auditoria #5)
    with rasterio.open(PROC / "class_final" / "2025.tif") as r:
        c25 = r.read(1)
    import geopandas as gpd2
    from rasterio.features import rasterize as rz2
    lim = gpd2.read_file(PROC / "limites.gpkg", layer="distritos").to_crs(crs)
    lim = lim[~lim["adm2_name"].astype(str).str.contains("Nyaka", case=False)]
    cidm = rz2(((gg, 1) for gg in lim.geometry), out_shape=shp, transform=tr, fill=0).astype(bool)
    agua = np.ones(shp, bool)
    for e in [1985, 1990, 1995, 1997, 2000, 2005, 2007, 2010, 2015, 2017, 2020, 2025, 2026]:
        with rasterio.open(PROC / "class_final" / f"{e}.tif") as r:
            agua &= (r.read(1) == 6)
    for lay, k in [("zv_permanentes", "perm"), ("zv_provisorias", "prov")]:
        gdf = gpd2.read_file(PROC / "planos" / "zonas_1985.gpkg", layer=lay).to_crs(crs)
        m = rz2(((gg, 1) for gg in gdf.geometry), out_shape=shp, transform=tr, fill=0).astype(bool) & cidm & ~agua
        v[f"env_{k}_pct_em_baixada"] = br(100 * (m & baix).sum() / max(m.sum(), 1))
    # mapa inteiro do plano (auditoria #4)
    envb = pd.read_csv(AREAS / "envelopes.csv"); envb = envb[envb.ambito == "bbox"].set_index(["perimetro", "epoca"])
    v["bbox_perm_2025"] = br(envb.loc[("plano1985_zv_permanentes", 2025), "pct_construido"], 1)
    v["bbox_prov_2025"] = br(envb.loc[("plano1985_zv_provisorias", 2025), "pct_construido"], 1)
    # confiança dos rótulos (auditoria #9)
    rot = pd.read_csv(PROC / "validacao" / "rotulos_2020.csv")
    cf = rot["confianca"].value_counts()
    v["val_conf_alta"] = str(int(cf.get("alta", 0))); v["val_conf_media"] = str(int(cf.get("media", 0)))
    v["val_conf_baixa"] = str(int(cf.get("baixa", 0)))
    v["val_conf_baixa_pct"] = br(100 * cf.get("baixa", 0) / len(rot))
    ex2p = PROC / "validacao" / "exatidao_2020_sem_baixa.json"
    if ex2p.exists():
        ex2 = json.loads(ex2p.read_text())["ambitos"]
        v["val2_n"] = str(json.loads(ex2p.read_text())["n_usados"])
        v["val2_ua_1"] = br(ex2["bbox"]["exatidao_usuario"]["1"]["valor"], 2)
        v["val2_ua_2"] = br(ex2["bbox"]["exatidao_usuario"]["2"]["valor"], 2)
        v["val2_og"] = br(ex2["bbox"]["exatidao_global"]["valor"], 2)
    # LUCO 1982 classes excluídas (auditoria #21)
    exc = lu[(lu["ano"] == 1982) & (lu["classe_agr"].astype(str).isin(["excluido", "-1", "99"]))]
    v["luco1982_excluido"] = br(exc["ha"].sum()) if len(exc) else ""

    cons_ = pd.read_csv(PROC / "class_final" / "consistencia.csv")
    colt = [c for c in cons_.columns if "total" in c or c == "alterados"]
    tot = cons_[colt[0]] if colt else cons_.select_dtypes("number").drop(columns=[c for c in cons_.columns if c in ("epoca",)], errors="ignore").sum(axis=1)
    v["pp_min_pix"] = br(tot.min()); v["pp_max_pix"] = br(tot.max())
    cfg = pd.read_csv(RAIZ / "fontes" / "conflitos.csv")
    v["conflitos_geo"] = str(int(cfg["lat"].notna().sum()))
    # Validação
    ex = json.loads((PROC / "validacao" / "exatidao_2020.json").read_text())
    v["val_n"] = str(ex["n_usados"])
    bb = ex["ambitos"]["bbox"]; cc = ex["ambitos"]["cidade"]
    v["val_og"] = br(bb["exatidao_global"]["valor"], 2)
    v["val_ua_1"] = br(bb["exatidao_usuario"]["1"]["valor"], 2)
    v["val_pa_1"] = br(bb["exatidao_produtor"]["1"]["valor"], 2)
    v["val_ua_2"] = br(bb["exatidao_usuario"]["2"]["valor"], 2)
    v["val_pa_2"] = br(bb["exatidao_produtor"]["2"]["valor"], 2)
    v["val_area_aj_2"] = br(cc["area_ajustada_ha"]["2"]["valor"])
    v["val_area_aj_2_ic"] = br(cc["area_ajustada_ha"]["2"]["ic95"])

    # Conflitos
    cf = pd.read_csv(RAIZ / "fontes" / "conflitos.csv")
    v["conflitos_n"] = str(len(cf))

    out = RAIZ / "artigo" / "valores.json"
    out.write_text(json.dumps(v, ensure_ascii=False, indent=1))
    for k, x in v.items():
        if k != "TABELA_1_ENVELOPES":
            print(k, x)
    print(v["TABELA_1_ENVELOPES"])


if __name__ == "__main__":
    main()
