"""12 - Resultados consolidados (fonte única de números do site e do artigo) e exportação do site.

Entradas: dados/proc/areas/*, dados/proc/class/oob.json, dados/proc/validacao/exatidao_2020.json (opcional),
planos georreferenciados (gpkg + rasters), fontes/*.csv, CREDITOS.md, comp/ e class_final/.
Saídas:
  dados/proc/resultados.json
  site/dados/dados.js            (window.DADOS = {...}; funciona em file://)
  site/dados/limites.geojson, conflitos.geojson, plano_1985.geojson, plano_2008.geojson
  site/dados/*.csv               (tabelas para download) e resultados.json
  site/img/painel/*.webp         (imagem, classificação, conversão, planos; EPSG:3857) e painel.json (cantos lon/lat)
Uso: .venv/bin/python -I scripts/12_resultados.py [--sem-rasters]
"""
import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import shapely
from PIL import Image
from pyproj import Transformer
from rasterio import features
from rasterio.warp import calculate_default_transform, reproject, Resampling

from comum import *  # noqa
import ardosia_palette as P

AREAS = PROC / "areas"
FONTES = RAIZ / "fontes"
SITE = RAIZ / "site"
SDADOS = SITE / "dados"
SPAINEL = SITE / "img" / "painel"
CLS = PROC / "class_final"
HA = RES * RES / 1e4
AGR_COD = [1, 2, 3, 45, 6, 7]
AGR_NOME = {1: "Construído", 2: "Zonas verdes (agricultura de baixada)", 3: "Sequeiro e mosaico (indicativo)",
            45: "Vegetação não cultivada", 6: "Água", 7: "Solo exposto"}
AGR_MAP = {0: 0, 1: 1, 2: 2, 3: 3, 4: 45, 5: 45, 6: 6, 7: 7}
# cores do mapa classificado: apenas paleta Ardósia (ardosia_palette.py)
COR_CLASSE = {1: P.TERRACOTA, 2: P.PETROLEO, 3: P.OCRE, 45: P.VIZ_MUTED, 6: P.ARDOSIA, 7: P.BORDO}
EP_ANALISE = [e for e in EPOCAS if e != 1979]

TIPO_CONFLITO = {
    "eviction": "despejo", "land redistribution": "redistribuição de terra", "conversion rule": "regra de conversão",
    "provisional green zones": "zonas verdes provisórias", "sale": "venda", "usurpation of land": "usurpação de terra",
    "sale of land": "venda de terra", "extralegal concessions": "concessões extralegais", "pressure": "pressão",
    "land disputes": "disputas de terra", "road": "estrada", "flood": "cheia", "salinisation": "salinização",
    "flood damage": "danos de cheia", "flood-driven resettlement": "reassentamento por cheia",
    "mangrove occupation": "ocupação de mangal", "housing": "habitação", "resettlement pressure": "pressão de reassentamento",
    "resettlement": "reassentamento", "construction": "construção", "condominium": "condomínio",
    "conversion": "conversão", "association gave up land": "associação cedeu a terra",
    "policy response": "resposta de política", "ban on change of activity": "proibição de mudar de atividade",
    "ETAR": "ETAR", "land": "terra",
}


def tipo_pt(t):
    t = str(t)
    if t in TIPO_CONFLITO:
        return TIPO_CONFLITO[t]
    out = []
    for parte in re.split(r"\s*/\s*", t):
        m = re.match(r"^(.*?)\s*\((.*)\)$", parte)
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            out.append(f"{TIPO_CONFLITO.get(a, a)} ({TIPO_CONFLITO.get(b, b)})")
        else:
            out.append(TIPO_CONFLITO.get(parte, parte))
    return " / ".join(out)


def nn(v):
    """NaN -> None; numpy -> python."""
    if v is None:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if not np.isfinite(v) else float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def registros(df):
    return [{k: nn(v) for k, v in r.items()} for r in df.to_dict("records")]


def r0(x):
    return int(round(float(x)))


def r1(x):
    return round(float(x), 1)


# ----------------------------------------------------------------------------- tabelas
def tabelas():
    R = {}
    ac = pd.read_csv(AREAS / "areas_agregado_classe_epoca.csv")
    cid = ac[ac.ambito == "cidade"]
    R["areas_cidade"] = {}
    R["areas_cidade_pct"] = {}
    R["sem_dado_cidade_ha"] = {}
    for ep in EP_ANALISE:
        d = cid[cid.epoca == ep].set_index("classe_agr")
        R["areas_cidade"][str(ep)] = {str(k): r0(d.loc[k, "ha"]) for k in AGR_COD}
        R["areas_cidade_pct"][str(ep)] = {str(k): r1(d.loc[k, "pct_com_dado"]) for k in AGR_COD}
        R["sem_dado_cidade_ha"][str(ep)] = r0(d.loc[0, "ha"])
    d79 = cid[cid.epoca == 1979].set_index("classe_agr")
    R["areas_1979_nao_comparavel"] = {
        "nota": "1979 (MSS, 60 m) tem legenda reduzida: classe 3 = toda a vegetação, classe 45 ausente. Fica fora das séries quantitativas.",
        "ha": {str(k): r0(d79.loc[k, "ha"]) for k in AGR_COD}}
    R["area_cidade_ha"] = r0(sum(R["areas_cidade"]["2020"].values()))
    bb = ac[ac.ambito == "bbox"]
    R["areas_bbox"] = {str(ep): {str(k): r0(bb[(bb.epoca == ep) & (bb.classe_agr == k)].ha.iloc[0]) for k in AGR_COD}
                       for ep in EP_ANALISE}

    dd = pd.read_csv(AREAS / "areas_agregado_distrito.csv")
    R["areas_distrito"] = {}
    for dist, g in dd[dd.epoca != 1979].groupby("unidade"):
        R["areas_distrito"][dist] = {str(ep): {str(k): r0(x.ha.iloc[0]) for k, x in gg.groupby("classe_agr") if k in AGR_COD}
                                     for ep, gg in g.groupby("epoca")}

    cv = pd.read_csv(AREAS / "conversao.csv")
    cvc = cv[cv.ambito == "cidade"].copy()
    cons = cvc[cvc.consecutivo]
    R["conversao"] = {
        "nota": "Área agrícola (classes 2+3) e zonas verdes (classe 2) que passam a construído entre épocas consecutivas; a classe 3 é indicativa. O intervalo 1979–1985 não é comparável (legenda reduzida de 1979).",
        "intervalos": [dict(t0=int(r.t0), t1=int(r.t1), anos=int(r.anos), comparavel=bool(r.t0 != 1979),
                            agri_para_construido_ha=r0(r.ha_agri_para_construido), agri_ha_ano=r1(r.ha_agri_ano),
                            agri_pct_inicial=r1(r.pct_agri_inicial), zv_para_construido_ha=r0(r.ha_zv_para_construido),
                            zv_ha_ano=r1(r.ha_zv_ano), zv_pct_inicial=r1(r.pct_zv_inicial),
                            area_agri_inicial_ha=r0(r.area_agri_inicial_ha), area_zv_inicial_ha=r0(r.area_zv_inicial_ha))
                       for r in cons.itertuples()],
        "acumulada": [dict(t0=int(r.t0), t1=int(r.t1), anos=int(r.anos),
                           agri_para_construido_ha=r0(r.ha_agri_para_construido), agri_ha_ano=r1(r.ha_agri_ano),
                           agri_pct_inicial=r1(r.pct_agri_inicial), zv_para_construido_ha=r0(r.ha_zv_para_construido),
                           zv_ha_ano=r1(r.ha_zv_ano), zv_pct_inicial=r1(r.pct_zv_inicial),
                           area_agri_inicial_ha=r0(r.area_agri_inicial_ha), area_zv_inicial_ha=r0(r.area_zv_inicial_ha))
                      for r in cvc[~cvc.consecutivo].itertuples()],
    }

    pb = pd.read_csv(AREAS / "perda_bairro.csv")

    def top(g):
        d = pb[pb.grupo == g].sort_values("convertida_construido_ha", ascending=False).head(10)
        return [dict(bairro=r.unidade, pcode=r.pcode, zv_1990_ha=r0(r.zv_1990_ha), zv_2025_ha=r0(r.zv_2025_ha),
                     variacao_liquida_ha=r0(r.variacao_liquida_ha), perda_bruta_ha=r0(r.perda_bruta_ha),
                     convertida_construido_ha=r0(r.convertida_construido_ha), ganho_bruto_ha=r0(r.ganho_bruto_ha),
                     area_bairro_ha=r0(r.area_unidade_ha)) for r in d.itertuples()]
    R["perda_bairro_top10"] = {
        "nota": "Medida principal: área de classe 2 em 1990 que passou a construído até 2025 ('convertida', transição 2→1; a época 1985 usa cena de 1984 e fica fora da base). A variação líquida inclui também a passagem 2→vegetação, que não é interpretável (a classe 2 não se separa com segurança da vegetação não cultivada), e é só indicativa.",
        "maputo": top("bairro_maputo"), "matola_arredores": top("bairro_matola"), "rotulo_matola": "Matola e Marracuene"}

    lu = pd.read_csv(AREAS / "areas_luco.csv")
    R["luco"] = {
        "nota": "LUCO (Henriques, Correia & Rolo, 2023) cobre cerca de 54% da área da cidade; percentuais sobre a área classificada pelo LUCO (sem 'excluído'); não comparáveis em nível com a série de 30 m, que cobre a cidade inteira.",
        "anos": sorted(int(a) for a in lu.ano.unique()),
        "pct_cidade_coberta": {str(int(a)): r1(g.pct_cidade_coberta.iloc[0]) for a, g in lu.groupby("ano")},
        "cobertura_ha": {str(int(a)): r0(g.cobertura_ha.iloc[0]) for a, g in lu.groupby("ano")},
        "ha": {str(int(a)): {str(r.classe_agr): r0(r.ha) for r in g.itertuples()} for a, g in lu.groupby("ano")},
        "pct_classificada": {str(int(a)): {str(r.classe_agr): r1(r.pct_classificada) for r in g.itertuples() if str(r.classe_agr) != "excluido"} for a, g in lu.groupby("ano")},
    }
    return R, cid


# ----------------------------------------------------------------------------- exatidão
def exatidao():
    oob = json.load(open(PROC / "class" / "oob.json"))
    out = {"oob": {}, "cv_blocos": {}, "validacao_independente_2020": None,
           "quem_rotulou": ("Os rótulos da validação cega foram atribuídos por um agente automático de interpretação visual de imagens, cego ao mapa; "
                          "recomenda-se revisão humana de uma subamostra."),
           "nota": ("OOB e validação cruzada usam rótulos derivados de produtos de terceiros (não é verdade de campo). "
                    "A validação cega de 2020 (amostra estratificada interpretada visualmente) está em preparação quando o campo é nulo.")}
    for ep, v in oob["oob"].items():
        out["oob"][ep] = dict(acc=round(v["acc"], 3), n=v["n"], f1_zonas_verdes=v["f1"].get("2"), f1_construido=v["f1"].get("1"),
                              f1_sequeiro=v["f1"].get("3"))
    for ep, v in oob["cv_bloques"].items():
        out["cv_blocos"][ep] = dict(acc=round(v["acc"], 3), n_blocos=v["n_blocos"], f1_zonas_verdes=v["f1"].get("2"),
                                    f1_construido=v["f1"].get("1"), f1_sequeiro=v["f1"].get("3"))
    p = PROC / "validacao" / "exatidao_2020.json"
    if p.exists():
        out["validacao_independente_2020"] = json.load(open(p))
    if out["validacao_independente_2020"]:
        v = out["validacao_independente_2020"]
        out["validacao_resumo"] = {}
        for amb, a in v["ambitos"].items():
            out["validacao_resumo"][amb] = dict(
                n_pontos=int(sum(a["n_por_estrato"].values())), exatidao_global=round(a["exatidao_global"]["valor"], 3),
                exatidao_global_ic95=round(a["exatidao_global"]["ic95"], 3),
                classes={k: dict(ua=round(a["exatidao_usuario"][k]["valor"], 2), ua_ic95=round(a["exatidao_usuario"][k]["ic95"], 2),
                                 pa=round(a["exatidao_produtor"][k]["valor"], 2), pa_ic95=round(a["exatidao_produtor"][k]["ic95"], 2),
                                 area_mapeada_ha=r0(a["area_mapeada_ha"][k]), area_ajustada_ha=r0(a["area_ajustada_ha"][k]["valor"]),
                                 area_ajustada_ic95_ha=r0(a["area_ajustada_ha"][k]["ic95"])) for k in a["exatidao_usuario"]})
        out["nota"] = ("Validação cega de 2020 (amostra estratificada, interpretação visual de imagens Sentinel-2): a classe 1 (construído) é confiável; "
                       "a classe 2 (zonas verdes) não se separa com segurança da classe 45 (vegetação não cultivada). A série da classe 2 é indicativa.")
    # sensibilidade a rótulos de baixa confiança
    ps = PROC / "validacao" / "exatidao_2020_sem_baixa.json"
    if ps.exists():
        vs = json.load(open(ps))
        out["sem_baixa"] = {"distribuicao_confianca": vs.get("distribuicao_confianca"), "ambitos": {}}
        for amb, a in vs["ambitos"].items():
            out["sem_baixa"]["ambitos"][amb] = dict(
                n_pontos=int(sum(a["n_por_estrato"].values())), exatidao_global=round(a["exatidao_global"]["valor"], 3),
                exatidao_global_ic95=round(a["exatidao_global"]["ic95"], 3),
                classes={k: dict(ua=round(a["exatidao_usuario"][k]["valor"], 2), ua_ic95=round(a["exatidao_usuario"][k]["ic95"], 2),
                                 pa=round(a["exatidao_produtor"][k]["valor"], 2), pa_ic95=round(a["exatidao_produtor"][k]["ic95"], 2),
                                 area_ajustada_ha=r0(a["area_ajustada_ha"][k]["valor"]), area_ajustada_ic95_ha=r0(a["area_ajustada_ha"][k]["ic95"]))
                         for k in a["exatidao_usuario"]})
        out["distribuicao_confianca"] = vs.get("distribuicao_confianca")
    # concordância externa
    try:
        gh = pd.read_csv(AREAS / "qa_externo_ghsl.csv")
        out["ghsl_construido"] = [dict(epoca=int(r.epoca), ghsl_ano=int(r.ghsl_ano), construido_ha=r0(r.construido_ha), ghsl_ha=r0(r.ghsl_ge2000_ha),
                                       f1=round(r.f1 / 100, 3)) for r in gh.itertuples() if int(r.epoca) in EP_ANALISE]
    except Exception:
        out["ghsl_construido"] = None
    return out


# ----------------------------------------------------------------------------- planos × ocorrido
def agr_counts(cnt):
    return {str(k): r0(c * HA) for k, c in zip(AGR_COD, [cnt[1], cnt[2], cnt[3], cnt[4] + cnt[5], cnt[6], cnt[7]])}


ENV_ROT = {"baixada_<15m_tpi<0": "Baixadas (altitude < 15 m, TPI < 0)", "plano1985_zv_permanentes": "Zonas verdes permanentes do plano de 1985",
           "plano1985_zv_provisorias": "Zonas verdes provisórias do plano de 1985", "peumm2008_agropecuaria": "Agropecuária do PEUMM 2008"}


def envelopes():
    e = pd.read_csv(AREAS / "envelopes.csv")
    out = {"nota": ("Percentual de área construída (classe 1, a mais confiável na validação) dentro de perímetros definidos de forma independente da classificação "
                    "agrícola. O salto 2005→2007 é em parte artefato das composições. 1985, 2010 e 2026 usam cenas substitutas."),
           "marcos": [dict(ano=2008, rotulo="Aprovação do PEUMM"), dict(ano=2012, rotulo="Início das obras da Circular")],
           "perimetros": {}}
    for per, g in e.groupby("perimetro"):
        d = {"rotulo": ENV_ROT.get(per, per)}
        for amb, gg in g.groupby("ambito"):
            d[amb] = {str(int(r.epoca)): dict(area_ha=r0(r.area_ha), construido_ha=r0(r.construido_ha), pct_construido=r1(r.pct_construido),
                                              classe2_ha=r0(r.classe2_ha)) for r in gg.itertuples()}
        out["perimetros"][per] = d
    return out


def _mm(vals):
    v = [x for x in vals if x is not None and np.isfinite(x)]
    return (min(v), max(v)) if v else (None, None)


def envelopes_comparacao():
    """Três estimativas da fração construída por perímetro (classificação bruta, pós-processada, GHSL) e faixa min–max."""
    e = pd.read_csv(AREAS / "envelopes_comparacao.csv")
    out = {"nota": ("Três estimativas da parcela construída: classificação bruta (Random Forest por época), classificação pós-processada "
                    "(janela de três épocas, monotonia do construído, suavização 2↔5) e GHSL GHS-BUILT-S R2023A (fração de superfície edificada). "
                    "As três não são independentes: bruta e pós-processada vêm do mesmo modelo, e o GHSL orientou os rótulos de treino. O GHSL R2023A observa só 1975, 1990, 2000, 2014 e 2018 e interpola ou extrapola as demais épocas (GHSL Data Package 2023, p. 6). O GHSL mede superfície de edifícios, não a mancha urbana, e por isso tende a ser o mais baixo. "
                    "A faixa é o mínimo e o máximo das três; as três são estimativas, nenhuma é a verdade. O salto 2005–2007 aparece nas classificações "
                    "e não aparece no GHSL, logo é artefato das composições. GHSL só existe em anos múltiplos de 5 (épocas intermediárias usam o ano GHSL anterior ou posterior mais próximo, ver ghsl_epoca)."),
           "perimetros": {}}
    for per, g in e.groupby("perimetro"):
        d = {"rotulo": ENV_ROT.get(per, "Cidade (6 distritos, sem água permanente)"), "cidade": {}}
        for r in g.itertuples():
            pcts = (r.pct_bruto, r.pct_final, r.pct_ghsl)
            has = (r.ha_bruto, r.ha_final, r.ha_ghsl)
            lo, hi = _mm(pcts)
            hlo, hhi = _mm(has)
            d["cidade"][str(int(r.epoca))] = dict(
                area_ha=r0(r.area_ha), pct_bruto=nn(r.pct_bruto), pct_final=nn(r.pct_final), pct_ghsl=nn(r.pct_ghsl),
                ha_bruto=nn(r.ha_bruto), ha_final=nn(r.ha_final), ha_ghsl=nn(r.ha_ghsl),
                ghsl_epoca=(int(r.ghsl_epoca) if pd.notna(r.ghsl_epoca) else None),
                pct_min=lo, pct_max=hi, ha_min=hlo, ha_max=hhi)
        out["perimetros"][per] = d
    return out


def faixas_kpi(ec):
    """Faixas (min–max das três estimativas) e crescimento do construído para os indicadores de abertura (ano final 2025)."""
    P = ec["perimetros"]
    cid = P["cidade_total"]["cidade"]
    cres = {}
    for k in ("ghsl", "bruto", "final"):
        a, b = cid["1985"]["ha_" + k], cid["2025"]["ha_" + k]
        cres[k] = round(100 * (b - a) / a, 1)
    out = dict(
        construido_ha_1985={k: r0(cid["1985"]["ha_" + k]) for k in ("ghsl", "bruto", "final")},
        construido_ha_2025={k: r0(cid["2025"]["ha_" + k]) for k in ("ghsl", "bruto", "final")},
        construido_crescimento_pct=cres, construido_crescimento_min_pct=min(cres.values()), construido_crescimento_max_pct=max(cres.values()),
        ano_final=2025, faixas={})
    for chave, per, anos in (("zv_permanentes", "plano1985_zv_permanentes", (1985, 2025)), ("agropecuaria", "peumm2008_agropecuaria", (2010, 2025)),
                             ("baixadas", "baixada_<15m_tpi<0", (1985, 2025))):
        out["faixas"][chave] = {str(a): [P[per]["cidade"][str(a)]["pct_min"], P[per]["cidade"][str(a)]["pct_max"]] for a in anos}
    # fonte única: as faixas devem coincidir com min/max recalculados direto do CSV
    e = pd.read_csv(AREAS / "envelopes_comparacao.csv")
    for chave, per, anos in (("zv_permanentes", "plano1985_zv_permanentes", (1985, 2025)), ("agropecuaria", "peumm2008_agropecuaria", (2010, 2025)),
                             ("baixadas", "baixada_<15m_tpi<0", (1985, 2025))):
        for a in anos:
            r = e[(e.perimetro == per) & (e.epoca == a)].iloc[0]
            v = [r.pct_bruto, r.pct_final, r.pct_ghsl]
            assert out["faixas"][chave][str(a)] == [min(v), max(v)], (chave, a)
    # e com os valores do artigo (artigo/valores.json, 1 casa decimal), quando disponível
    vp = RAIZ / "artigo" / "valores.json"
    if vp.exists():
        vj = json.load(open(vp))
        pref = {"zv_permanentes": "perm", "agropecuaria": "peumm", "baixadas": "baix"}
        for chave, f in out["faixas"].items():
            for a, (lo, hi) in f.items():
                for suf, val in (("min", lo), ("max", hi)):
                    k = f"r_{pref[chave]}_{a}_{suf}"
                    if k in vj:
                        assert abs(float(str(vj[k]).replace(",", ".")) - val) < 0.051, (k, vj[k], val)
        for k, v in cres.items():
            kk = f"cid_cresc_{k}"
            if kk in vj:
                assert abs(float(str(vj[kk]).replace(",", ".")) - v) < 0.6, (kk, vj[kk], v)
    return out


def planejado_ocorrido(cidade):
    dist = gpd.read_file(PROC / "limites.gpkg", layer="distritos")
    dist = dist[dist.adm2_name != "KaNyaka"]
    uni = dist.geometry.union_all()
    cl = {ep: rasterio.open(CLS / f"{ep}.tif").read(1) for ep in (1985, 2010, 2025)}
    # mesmas máscaras de 07b_envelopes.py: água permanente (classe 6 em todas as 13 épocas) excluída; cidade sem KaNyaka; sem dado fora
    agua = None
    for e in EP_ANALISE:
        c6 = rasterio.open(CLS / f"{e}.tif").read(1) == 6
        agua = c6 if agua is None else agua & c6
    env = pd.read_csv(AREAS / "envelopes.csv")
    ENVN = {"zv_permanentes": "plano1985_zv_permanentes", "zv_provisorias": "plano1985_zv_provisorias", "agropecuaria": "peumm2008_agropecuaria"}
    z85 = PROC / "planos" / "zonas_1985.gpkg"
    z08 = PROC / "planos" / "peumm_2008.gpkg"
    plano = {
        "1985": dict(arq=z85, camadas=["zv_permanentes", "zv_provisorias", "ocupacao_actual"], ep=[1985, 2025],
                     nomes={"zv_permanentes": "Zonas verdes permanentes", "zv_provisorias": "Zonas verdes provisórias",
                            "ocupacao_actual": "Ocupação atual"}),
        "2008": dict(arq=z08, camadas=["agropecuaria", "expansao_urbana", "urbanizavel_planificada", "urbanizavel_nao_planificada"],
                     ep=[2010, 2025],
                     nomes={"agropecuaria": "Agropecuária", "expansao_urbana": "Expansão urbana",
                            "urbanizavel_planificada": "Urbanizável planificada",
                            "urbanizavel_nao_planificada": "Urbanizável não planificada"}),
    }
    saida = {"nota": ("Zonas vetorizadas de plantas georreferenciadas (RMSE de 12–18 m nos pontos de controle; verificação independente por costa de 65–133 m; "
                      "zonas de 1985 com incerteza de área superior a 30%). Sobreposição rasterizada na grade de 30 m; 'cidade' = 6 distritos continentais."),
             "plano_1985": {}, "plano_2008": {}, "areas_vetoriais_ha": {}}
    for ano, cfg in plano.items():
        idz = np.zeros(SHAPE, "uint8")
        gdfs = {}
        for i, cam in enumerate(cfg["camadas"], 1):
            g = gpd.read_file(cfg["arq"], layer=cam)
            gdfs[cam] = g
            m = features.rasterize(((geo, i) for geo in g.geometry), out_shape=SHAPE, transform=TRANSFORM, fill=0, dtype="uint8")
            idz = np.where((idz == 0) & (m > 0), m, idz)
        dest = saida["plano_" + ano]
        dest["categorias"] = {}
        for i, cam in enumerate(cfg["camadas"], 1):
            g = gdfs[cam]
            ha_mapa = float(g.geometry.area.sum() / 1e4)
            ha_cid = float(g.geometry.intersection(uni).area.sum() / 1e4)
            saida["areas_vetoriais_ha"][f"{ano}_{cam}"] = dict(no_mapa=r0(ha_mapa), dentro_dos_distritos=r0(ha_cid))
            zi = idz == i
            zm = features.rasterize(((geo, 1) for geo in g.geometry), out_shape=SHAPE, transform=TRANSFORM, fill=0, dtype="uint8").astype(bool) & ~agua
            if cam in ENVN:
                er = env[(env.perimetro == ENVN[cam]) & (env.ambito == "cidade") & (env.epoca == cfg["ep"][0])]
                ha_cid = float(er.area_ha.iloc[0])
            ent = dict(nome=cfg["nomes"][cam], area_mapa_ha=r0(ha_mapa), area_distritos_ha=r0(ha_cid), por_epoca={})
            for ep in cfg["ep"]:
                c = cl[ep]
                mc = zm & cidade & (c > 0)
                cnt = np.bincount(c[mc], minlength=8)
                d = agr_counts(cnt)
                tot = cnt[1:].sum() * HA
                d["pct_construido"] = round(100 * cnt[1] * HA / tot, 2) if tot else None
                ent["por_epoca"][str(ep)] = dict(cidade=d, area_ha=round(float(tot), 1))
                if cam in ENVN:
                    er = env[(env.perimetro == ENVN[cam]) & (env.ambito == "cidade") & (env.epoca == ep)].iloc[0]
                    assert abs(d["pct_construido"] - er.pct_construido) < 0.05, (cam, ep, d["pct_construido"], er.pct_construido)
                    assert abs(tot - er.area_ha) < 0.2, (cam, ep, tot, er.area_ha)
                    d["pct_construido_envelopes"] = float(er.pct_construido)
            dest["categorias"][cam] = ent
        # quanto das zonas verdes de 2025 (classe 2) cai em cada categoria
        c25 = cl[2025]
        z2 = (c25 == 2) & cidade
        tot = int(z2.sum())
        rev = {}
        for i, cam in enumerate(cfg["camadas"], 1):
            rev[cam] = r0((z2 & (idz == i)).sum() * HA)
        rev["fora_das_zonas_vetorizadas"] = r0((z2 & (idz == 0)).sum() * HA)
        dest["zonas_verdes_2025_por_categoria_ha"] = rev
        dest["zonas_verdes_2025_total_cidade_ha"] = r0(tot * HA)
        dest["epocas_comparadas"] = cfg["ep"]
    return saida


# ----------------------------------------------------------------------------- fontes
def fontes_csv():
    out = {}
    mar = pd.read_csv(FONTES / "marcos.csv")
    mar["tipo_pt"] = mar.tipo.map({"plano": "Plano", "instituicao": "Instituição", "lei": "Lei", "politica": "Política",
                                   "obra": "Obra", "cheia": "Cheia"})
    out["marcos"] = registros(mar)
    pl = pd.read_csv(FONTES / "planos.csv")
    out["planos"] = registros(pl)
    co = pd.read_csv(FONTES / "conflitos.csv")
    co["tipo_pt"] = co.tipo.map(tipo_pt)
    co["georreferenciado"] = co.lat.notna() & co.lon.notna()
    out["conflitos"] = registros(co)
    ca = pd.read_csv(FONTES / "casos_comparados.csv")
    out["casos_comparados"] = registros(ca)
    return out


def series_producao():
    s = pd.read_csv(FONTES / "series_producao.csv")
    s["ano"] = s.ano_referencia.astype(str)

    def linha(r):
        return dict(valor=nn(r.valor), unidade=r.unidade, ano=r.ano, recorte=r.recorte_espacial, definicao=r.definicao,
                    fonte=r.fonte_chave, pagina=nn(r.pagina_tabela), status=r.status)

    ugc = {}
    for chave, var in [("cooperativas", "cooperativas UGC (numero)"), ("membros", "cooperativas UGC (membros)"),
                       ("area_ha", "cooperativas UGC (area)"), ("producao_agricola_t", "producao agricola cooperativas UGC"),
                       ("producao_pecuaria_t", "producao pecuaria cooperativas UGC")]:
        d = s[(s.variavel == var) & (s.fonte_chave == "christie_1996_l5")]
        for r in d.itertuples():
            ugc.setdefault(int(r.ano), {"ano": int(r.ano)})[chave] = float(r.valor)
            if r.status != "VERIFICADO":
                ugc[int(r.ano)].setdefault("parcial", []).append(chave)
    ugc = [ugc[k] for k in sorted(ugc)]
    ref_ugc = s[(s.variavel == "cooperativas UGC (membros)") & (s.fonte_chave == "christie_1996_l5")].iloc[0]

    def pick(var, ano, recorte_inicio=None, fonte=None):
        d = s[(s.variavel == var) & (s.ano == str(ano))]
        if recorte_inicio:
            d = d[d.recorte_espacial.str.startswith(recorte_inicio)]
        if fonte:
            d = d[d.fonte_chave == fonte]
        if len(d) != 1:
            raise SystemExit(f"seleção ambígua/ausente em series_producao: {var} {ano} {recorte_inicio} ({len(d)})")
        return d.iloc[0]

    pontos = []

    def add(grupo, rotulo, var, ano, rec=None, fonte=None, valor_num=None):
        r = pick(var, ano, rec, fonte)
        d = linha(r)
        d.update(grupo=grupo, rotulo=rotulo, ano_num=int(str(ano)[:4]))
        if valor_num is not None:
            d["valor"] = valor_num
        pontos.append(d)

    # (a) número de associações — definições distintas, nunca ligadas por linha
    add("associacoes_n", "Associações de produtores, distritos 4 a 8 (Roth et al.)", "associacoes de produtores (numero)", 1991)
    add("associacoes_n", "Associações, zonas verdes (Sumbane, 1988, apud Engel et al.)", "associacoes de produtores", 1986)
    add("associacoes_n", "Associações e cooperativas, 4 distritos (DASACM)", "associacoes agricolas (numero)", 2018, "Total")
    # (b) produtores
    add("produtores", "Agricultores, total das zonas verdes (estimativa GZV)", "agricultores (total GZV)", 1988)
    add("produtores", "Agricultores familiares, zonas verdes (avaliação GZV)", "agricultores familiares", 1993)
    add("produtores", "Número de produtores, 4 distritos (GCM/PAPAP)", "numero de produtores", 2016, "Total")
    add("produtores", "Agricultores de pequena escala, 4 distritos", "agricultores de pequena escala (total)", 2017)
    add("produtores", "Produtores associados, 4 distritos (DASACM)", "produtores associados", 2018, "Total")
    add("produtores", "Agricultores em associações (zonas verdes, Dürrnagel)", "agricultores em associacoes (zonas verdes)", 2022)
    # (c) agregados
    add("agregados_pct", "Agregados de baixa renda que produzem algum alimento (AFSUN)", "agregados de baixa renda que produzem algum alimento proprio", 2008)
    add("agregados_pct", "Agregados que cultivam hortícolas, % da amostra (Raimundo et al.)", "agregados que cultivam hortícolas (incl. ervas)", 2014)
    add("agregados_pct", "Agregados que obtêm alimento da agricultura urbana", "agregados a obter alimento da agricultura urbana", 2017)
    add("agregados_pct", "Agregados envolvidos em agricultura urbana (até)", "agregados a praticar agricultura urbana (ate)", 2018)
    # (d) áreas segundo definições distintas
    areas = []

    def addA(rotulo, var, ano, rec=None, fonte=None):
        r = pick(var, ano, rec, fonte)
        d = linha(r)
        d.update(rotulo=rotulo)
        areas.append(d)
    addA("Cooperativas da UGC (área das cooperativas)", "cooperativas UGC (area)", 1990, fonte="christie_1996_l5")
    addA("Zonas verdes permanentes legais (plano de 1985)", "area de zonas verdes permanentes", 1985)
    addA("Zonas verdes provisórias legais (plano de 1985)", "area de zonas verdes provisorias", 1985)
    addA("Zonas verdes legais, distritos 3–8 (plano de 1985)", "area total de zonas verdes (permanentes+provisorias)", 1985, "zonas verdes legais (1985), Distritos")
    addA("Agricultura urbana excluindo associações (Sumbane, 1988)", "area total em agricultura urbana (excl. associacoes)", 1986)
    addA("Estimativa GZV de zonas verdes", "area zonas verdes (estimativa GZV)", 1988)
    addA("Uso do solo 'zonas verdes', município", "zonas verdes (uso do solo)", 1998)
    addA("Área ocupada por associações, 4 distritos (DASACM)", "area ocupada por associacoes", 2018, "Total")
    addA("Área das zonas verdes, 4 de 7 distritos (Dürrnagel)", "area das zonas verdes", 2022, fonte="durrnagel_2022")
    return dict(
        nota=("Cada ponto tem a sua própria definição espacial e conceitual; não se somam nem se ligam por linha entre definições distintas. "
              "Valores PARCIAL foram lidos em fontes secundárias ou resumos."),
        ugc=dict(serie=ugc, fonte="christie_1996_l5", pagina=nn(ref_ugc.pagina_tabela), definicao=ref_ugc.definicao),
        pontos=pontos, areas_por_definicao=areas)


# ----------------------------------------------------------------------------- créditos
def split_row(l):
    return [c.strip() for c in l.strip().strip("|").split("|")]


def le_creditos():
    txt = (RAIZ / "CREDITOS.md").read_text(encoding="utf-8")
    secoes = re.split(r"^## ", txt, flags=re.M)
    res = {"intro": None, "mapas": [], "planos": [], "dados": []}
    for s in secoes[1:]:
        titulo, _, corpo = s.partition("\n")
        linhas = [l for l in corpo.splitlines() if l.startswith("|")]
        if titulo.startswith("Licença"):
            res["intro"] = corpo.strip()
        if not linhas:
            continue
        cab = split_row(linhas[0])
        rows = [dict(zip(cab, split_row(l))) for l in linhas[2:]]
        if titulo.startswith("Mapas"):
            res["mapas"] = rows
        elif titulo.startswith("Planos"):
            res["planos"] = rows
        elif titulo.startswith("Dados"):
            res["dados"] = rows
    return res


def imagens(cred):
    fig = pd.read_csv(FONTES / "figuras_planos.csv")
    baix = pd.read_csv(FONTES / "imagens_baixadas.csv")
    out = []
    webdir = SITE / "img" / "planos"
    for r in cred["mapas"]:
        f = r["Arquivo web"]
        b = baix[baix.titulo_commons == r["Título"]]
        cred_sug = nn(b.credito_sugerido.iloc[0]) if len(b) else None
        out.append(dict(arquivo=f, tipo="mapa", titulo=r["Título"].rsplit(".", 1)[0], data=r["Data"], autor=r["Autor"], detentor=None,
                        licenca=r["Licença"], fonte=r["Fonte (URL página)"], pagina=None, apud=None, credito_sugerido=cred_sug,
                        legenda=None, mini=(webdir / f.replace(".webp", "_mini.webp")).exists(), existe=(webdir / f).exists()))
    for r in cred["planos"]:
        f = r["Arquivo web"]
        if not f.endswith(".webp"):
            continue
        m = fig[(fig.plano == r["Plano"]) & (fig.ano.astype(str) == r["Ano"])]
        if "Figura" in r["Página / figura"]:
            mm = fig[(fig.plano == r["Plano"]) & (fig.ano.astype(str) == r["Ano"]) & (fig.figura_fonte.apply(lambda x: x in r["Página / figura"]))]
            m = mm if len(mm) else m
        legenda = nn(m.legenda_pt.iloc[0]) if len(m) else None
        out.append(dict(arquivo=f, tipo="plano", titulo=r["Plano"], data=r["Ano"], autor=r["Autor original"], detentor=r["Detentor original"],
                        licenca=r["Situação de direitos"], fonte=r["Obtido de"], pagina=r["Página / figura"], apud=r["Obtido de"],
                        credito_sugerido=None, legenda=legenda,
                        mini=(webdir / f.replace(".webp", "_mini.webp")).exists(), existe=(webdir / f).exists()))
    return [i for i in out if i["existe"]]


# ----------------------------------------------------------------------------- rasters
def _tr_ll():
    return Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)


def _ver(p):
    """Marcador de versão pelo conteúdo, para o navegador não reaproveitar imagem antiga do cache."""
    import hashlib
    return hashlib.md5(Path(p).read_bytes()).hexdigest()[:8]


def para_3857(arr, src_transform, src_crs, resampling, dtype, fill=0, src_nodata=None):
    """arr (H,W) ou (B,H,W) -> (B,H',W') em EPSG:3857 + cantos lon/lat [[NW],[NE],[SE],[SW]].

    Mapas categóricos devem passar src_nodata com um valor AUSENTE do mapa (ex.: 255): com src_nodata=None
    o GDAL tratava 0 como sem-dado e preenchia esses píxeis com a classe vizinha (bug corrigido em 11/11/2026:
    buracos de nuvem apareciam como construído no painel)."""
    if arr.ndim == 2:
        arr = arr[None]
    b, h, w = arr.shape
    left = src_transform.c
    top = src_transform.f
    right = left + w * src_transform.a
    bottom = top + h * src_transform.e
    dtr, dw, dh = calculate_default_transform(src_crs, "EPSG:3857", w, h, left, bottom, right, top)
    out = np.full((b, dh, dw), fill, dtype=dtype)
    for i in range(b):
        reproject(arr[i], out[i], src_transform=src_transform, src_crs=src_crs, dst_transform=dtr, dst_crs="EPSG:3857",
                  resampling=resampling, src_nodata=src_nodata, dst_nodata=(fill if src_nodata is None else src_nodata))
        if src_nodata is not None:
            out[i][out[i] == src_nodata] = fill
    x0, y1 = dtr.c, dtr.f
    x1, y0 = x0 + dw * dtr.a, y1 + dh * dtr.e
    t = _tr_ll()
    nw, ne, se, sw = t.transform(x0, y1), t.transform(x1, y1), t.transform(x1, y0), t.transform(x0, y0)
    cantos = [[round(nw[0], 6), round(nw[1], 6)], [round(ne[0], 6), round(ne[1], 6)],
              [round(se[0], 6), round(se[1], 6)], [round(sw[0], 6), round(sw[1], 6)]]
    return out, cantos


def salva_webp(rgba, path, lossless=False, q=80):
    im = Image.fromarray(np.moveaxis(rgba, 0, -1) if rgba.shape[0] == 4 else rgba, "RGBA")
    im.save(path, "WEBP", lossless=lossless, quality=q, method=6)
    return path.stat().st_size


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def estica(a):
    ok = np.isfinite(a)
    lo, hi = np.nanpercentile(a[ok], [2, 98])
    return np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1), ok


def rasters_painel():
    SPAINEL.mkdir(parents=True, exist_ok=True)
    B = {b: i for i, b in enumerate(BANDAS)}
    info = {"imagem": {}, "classes": {}, "conversao": {}, "planos": {}, "tamanhos_bytes": {}}
    tot = 0
    for ep in EPOCAS:
        with rasterio.open(COMP / f"{ep}.tif") as s:
            st = s.read()
        bandas = ["nir", "red", "green"] if ep == 1979 else ["red", "green", "blue"]
        ch, ok = [], None
        for b in bandas:
            r, o = estica(st[B[b]])
            ch.append(r)
            ok = o if ok is None else ok & o
        rgb = (np.stack(ch) * 255).astype("uint8")
        med = np.array([np.median(rgb[i][ok]) for i in range(3)], dtype="uint8")
        for i in range(3):
            rgb[i][~ok] = med[i]
        a = (ok * 255).astype("uint8")
        rgb3, cantos = para_3857(rgb, TRANSFORM, CRS, Resampling.bilinear, "uint8")
        al, _ = para_3857(a, TRANSFORM, CRS, Resampling.nearest, "uint8", src_nodata=1)
        rgba = np.concatenate([rgb3, al], 0)
        p = SPAINEL / f"img_{ep}.webp"
        tot += salva_webp(rgba, p, lossless=False, q=80)
        info["imagem"][str(ep)] = dict(arquivo=f"img/painel/{p.name}?v={_ver(p)}", coordenadas=cantos,
                                       composicao="falsa-cor NIR-vermelho-verde" if ep == 1979 else "cor verdadeira (vermelho, verde, azul)",
                                       estiramento="percentis 2-98% por canal")
        if ep == 1979:
            continue
        cl = rasterio.open(CLS / f"{ep}.tif").read(1)
        agr = np.array([0, 1, 2, 3, 4, 4, 5, 6], dtype="uint8")[cl]  # índice 1..6 em AGR_COD
        idx, cantos = para_3857(agr, TRANSFORM, CRS, Resampling.nearest, "uint8", src_nodata=255)
        rgba = np.zeros((4,) + idx.shape[1:], "uint8")
        for i, k in enumerate(AGR_COD, 1):
            m = idx[0] == i
            for j, v in enumerate(hex_rgb(COR_CLASSE[k])):
                rgba[j][m] = v
            rgba[3][m] = 255
        p = SPAINEL / f"cls_{ep}.webp"
        tot += salva_webp(rgba, p, lossless=True)
        info["classes"][str(ep)] = dict(arquivo=f"img/painel/{p.name}?v={_ver(p)}", coordenadas=cantos)
    # conversão
    cv = rasterio.open(CLS / "conversao_agri_construido.tif").read(1)
    idx, cantos = para_3857(cv, TRANSFORM, CRS, Resampling.nearest, "uint16", src_nodata=65535)
    anos = [e for e in EP_ANALISE if e != 1985]
    from matplotlib.colors import LinearSegmentedColormap
    cm = LinearSegmentedColormap.from_list("seq", P.VIZ_SEQUENTIAL[1:])
    cores = {a: tuple(int(round(255 * c)) for c in cm(i / (len(anos) - 1))[:3]) for i, a in enumerate(anos)}
    rgba = np.zeros((4,) + idx.shape[1:], "uint8")
    for a, c in cores.items():
        m = idx[0] == a
        for j in range(3):
            rgba[j][m] = c[j]
        rgba[3][m] = 255
    p = SPAINEL / "conversao.webp"
    tot += salva_webp(rgba, p, lossless=True)
    info["conversao"] = dict(arquivo=f"img/painel/{p.name}?v={_ver(p)}", coordenadas=cantos, anos=anos,
                             cores_hex={str(a): "#%02X%02X%02X" % c for a, c in cores.items()})
    # planos
    for nome, arq in (("plano_1985", "plano_1985_mapa7.tif"), ("peumm_2008", "peumm_2008_ordenamento.tif")):
        with rasterio.open(PROC / "planos" / arq) as s:
            a = s.read()
            tr = s.transform
        out, cantos = para_3857(a, tr, CRS, Resampling.bilinear, "uint8")
        p = SPAINEL / f"{nome}.webp"
        tot += salva_webp(out, p, lossless=False, q=80)
        info["planos"][nome] = dict(arquivo=f"img/painel/{p.name}?v={_ver(p)}", coordenadas=cantos)
    info["tamanho_total_bytes"] = int(tot)
    json.dump(info, open(SPAINEL / "painel.json", "w"), indent=1, ensure_ascii=False)
    return info


def vetores(perda):
    SDADOS.mkdir(parents=True, exist_ok=True)

    def prep(g, tol):
        g = g.copy()
        g["geometry"] = g.geometry.simplify(tol, preserve_topology=True)
        g = g.to_crs("EPSG:4326")
        g["geometry"] = shapely.set_precision(g.geometry.values, 1e-5)
        return g

    # limites
    dist = gpd.read_file(PROC / "limites.gpkg", layer="distritos")
    dist = dist[dist.adm2_name != "KaNyaka"]
    d = dist[["adm2_name", "adm2_pcode", "geometry"]].rename(columns={"adm2_name": "nome", "adm2_pcode": "pcode"})
    d["camada"] = "distrito"
    pb = perda.set_index("pcode")
    partes = [d]
    for lay, cam in (("bairros", "bairro_maputo"), ("matola_bairros", "bairro_matola")):
        b = gpd.read_file(PROC / "limites.gpkg", layer=lay)
        b = b[["adm4_name", "adm4_pcode", "geometry"]].rename(columns={"adm4_name": "nome", "adm4_pcode": "pcode"})
        b["camada"] = cam
        b["zv1990"] = b.pcode.map(lambda p: r0(pb.zv_1990_ha[p]) if p in pb.index else None)
        b["zv2025"] = b.pcode.map(lambda p: r0(pb.zv_2025_ha[p]) if p in pb.index else None)
        b["dif"] = b.pcode.map(lambda p: r0(pb.variacao_liquida_ha[p]) if p in pb.index else None)
        partes.append(b)
    lim = gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs=dist.crs)
    prep(lim, 25).to_file(SDADOS / "limites.geojson", driver="GeoJSON")
    # planos
    for nome, arq, cams in (("plano_1985", "zonas_1985.gpkg", ["zv_permanentes", "zv_provisorias", "ocupacao_actual"]),
                            ("plano_2008", "peumm_2008.gpkg", ["agropecuaria", "expansao_urbana", "urbanizavel_planificada",
                                                              "urbanizavel_nao_planificada"])):
        g = pd.concat([gpd.read_file(PROC / "planos" / arq, layer=c) for c in cams], ignore_index=True)
        g = gpd.GeoDataFrame(g[["classe", "area_ha", "geometry"]], crs=CRS)
        g["area_ha"] = g.area_ha.round(0).astype(int)
        prep(g, 10).to_file(SDADOS / f"{nome}.geojson", driver="GeoJSON")
    # conflitos
    co = pd.read_csv(FONTES / "conflitos.csv")
    co["tipo_pt"] = co.tipo.map(tipo_pt)
    c = co.dropna(subset=["lat", "lon"])
    feats = [dict(type="Feature", geometry=dict(type="Point", coordinates=[float(r.lon), float(r.lat)]),
                  properties=dict(id=r.id, local=r.local, ano=nn(r.ano_inicio), tipo=r.tipo_pt, desc=r.descricao_curta,
                                  fonte=r.fonte_chave, pagina=nn(r.pagina_ou_url))) for r in c.itertuples()]
    json.dump(dict(type="FeatureCollection", features=feats,
                   nota="Posições aproximadas (local descrito na fonte), não coordenadas medidas."),
              open(SDADOS / "conflitos.geojson", "w"), ensure_ascii=False)


# ----------------------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-rasters", action="store_true")
    args = ap.parse_args()
    SDADOS.mkdir(parents=True, exist_ok=True)

    R, cid = tabelas()
    dist = gpd.read_file(PROC / "limites.gpkg", layer="distritos")
    dist = dist[dist.adm2_name != "KaNyaka"]
    cidade = features.rasterize(((g, 1) for g in dist.geometry), out_shape=SHAPE, transform=TRANSFORM, fill=0, dtype="uint8") > 0
    log("cidade ha:", int(cidade.sum() * HA))

    # épocas
    eps = []
    for ep in EPOCAS:
        t = rasterio.open(COMP / f"{ep}.tif").tags()
        d = dict(ano=ep, fonte=t.get("fonte"), sensor=t.get("sensor"), datas=t.get("datas"), count_mediana=t.get("count_mediana"),
                 substituicao=t.get("substituicao") if t.get("substituicao") != "nenhuma" else None, quantitativa=ep != 1979)
        eps.append(d)
    cav = {
        1979: ("Imagem Landsat 3 MSS de 9 de junho de 1979 (60 m, falsa-cor NIR, vermelho, verde), usada no lugar do censo de 1980. "
               "Imagem MSS, sem classificação quantitativa: fica fora das séries de área."),
        1985: "Cena Landsat 5 TM de 1.º de junho de 1984, no lugar da composição anual de 1985 (rejeitada por cobertura insuficiente).",
        2010: "Cena Landsat 5 TM de 9 de abril de 2011, no lugar da composição anual de 2010 (faixas de falha do Landsat 7). Abril: fora da estação seca.",
        2026: "Mediana de 12 cenas Landsat 8 e 9 de maio a agosto de 2026 (ainda não há composição anual).",
    }
    rot = {1979: "1979 (imagem MSS)", 1985: "1985 (cena de 1984)", 2010: "2010 (cena de abril de 2011)", 2026: "2026 (cenas mai.–ago.)"}
    for d in eps:
        d["rotulo"] = rot.get(d["ano"], str(d["ano"]))
        d["caveat"] = cav.get(d["ano"], "Composição anual geomediana do Digital Earth Africa (GeoMAD).")
        d["marca_cena_substituta"] = d["ano"] in (1985, 2010, 2026)
    R["epocas"] = eps
    R["classes"] = [dict(cod=k, nome=AGR_NOME[k], cor_hex=COR_CLASSE[k]) for k in AGR_COD]
    R["ressalvas"] = [
        "1979 (Landsat MSS, 60 m) fica fora das séries quantitativas: legenda reduzida.",
        "1985 usa a cena de 1984-06-01; 2010 usa a cena de 2011-04-09 (abril); 2026 é a mediana de cenas de maio a agosto de 2026.",
        "A classe 3 (sequeiro e mosaico) é indicativa: é a de maior confusão com herbácea e construído disperso.",
        "Hortas pequenas são subpíxel a 30 m; as áreas são estimativas do mapa, não áreas ajustadas por amostra probabilística.",
        "As três estimativas da parcela construída não são independentes (o GHSL orientou os rótulos de treino), e o GHSL interpola entre 1975, 1990, 2000, 2014 e 2018: compare períodos, não épocas isoladas (correção da versão 1.0.2).",
    ]

    acum = [x for x in R["conversao"]["acumulada"] if x["t0"] == 1985 and x["t1"] == 2026][0]
    fo = fontes_csv()
    R["kpi"] = dict(
        pct_agricola_convertido_1985_2026=acum["agri_pct_inicial"], pct_zonas_verdes_convertido_1985_2026=acum["zv_pct_inicial"],
        agricola_convertido_ha=acum["agri_para_construido_ha"], zonas_verdes_convertidas_ha=acum["zv_para_construido_ha"],
        conflitos_documentados=len(fo["conflitos"]), conflitos_georreferenciados=sum(1 for c in fo["conflitos"] if c["georreferenciado"]))
    R.update(fo)
    R["exatidao"] = exatidao()
    R["envelopes"] = envelopes()
    R["envelopes_comparacao"] = envelopes_comparacao()
    R["kpi"].update(faixas_kpi(R["envelopes_comparacao"]))
    R["kpi"]["nota"] = ("Ano final dos indicadores: 2025 (a composição de 2026 é atípica, só maio–agosto). Cada indicador é uma faixa entre três estimativas: "
                        "GHSL, classificação bruta e classificação pós-processada.")
    log("overlay planos...")
    R["planos_vs_ocorrido"] = planejado_ocorrido(cidade)
    R["producao"] = series_producao()
    cred = le_creditos()
    R["creditos"] = cred
    R["imagens"] = imagens(cred)
    R["citacao"] = "PESSINI SOBREIRA, Daniel. Zonas verdes de Maputo (1979–2026): agricultura urbana, uso do solo e planos urbanísticos. Zenodo, 2026. DOI: 10.5281/zenodo.24141821. Disponível em: https://doi.org/10.5281/zenodo.24141821."
    R["doi"] = {"conceito": "10.5281/zenodo.24141821", "v1.0.0": "10.5281/zenodo.24141822"}
    R["meta"] = dict(
        gerado_em=datetime.date.today().isoformat(), script="scripts/12_resultados.py", crs_trabalho=CRS, resolucao_m=RES,
        bbox_lonlat=[LON_MIN, LAT_MIN, LON_MAX, LAT_MAX], area_cidade_ha=R["area_cidade_ha"],
        entradas=["dados/proc/areas/*.csv", "dados/proc/class_final/*.tif", "dados/proc/class/oob.json",
                  "dados/proc/validacao/exatidao_2020.json (opcional)", "dados/proc/validacao/exatidao_2020_sem_baixa.json (opcional)", "dados/proc/areas/envelopes_comparacao.csv", "dados/proc/planos/zonas_1985.gpkg", "dados/proc/planos/peumm_2008.gpkg",
                  "fontes/series_producao.csv", "fontes/marcos.csv", "fontes/planos.csv", "fontes/conflitos.csv",
                  "fontes/casos_comparados.csv", "fontes/figuras_planos.csv", "fontes/imagens_baixadas.csv", "CREDITOS.md"],
        validacao_independente_disponivel=R["exatidao"]["validacao_independente_2020"] is not None,
        ressalvas=R["ressalvas"])

    json.dump(R, open(PROC / "resultados.json", "w"), indent=1, ensure_ascii=False)
    log("resultados.json ok")

    # site
    perda = pd.read_csv(AREAS / "perda_bairro.csv")
    vetores(perda)
    if not args.sem_rasters:
        info = rasters_painel()
        log("rasters ok:", round(info["tamanho_total_bytes"] / 1e6, 1), "MB")
    pj = SPAINEL / "painel.json"
    painel = json.load(open(pj)) if pj.exists() else None
    D = dict(R)
    D["painel"] = painel
    with open(SDADOS / "dados.js", "w", encoding="utf-8") as f:
        f.write("/* Gerado por scripts/12_resultados.py; não editar. */\nwindow.DADOS = ")
        json.dump(D, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    shutil.copy(PROC / "resultados.json", SDADOS / "resultados.json")
    for nome, src in [("areas_agregado_classe_epoca.csv", AREAS), ("areas_agregado_distrito.csv", AREAS), ("areas_agregado_bairro.csv", AREAS),
                      ("areas_agregado_transicoes.csv", AREAS), ("conversao.csv", AREAS), ("perda_bairro.csv", AREAS), ("areas_luco.csv", AREAS), ("envelopes_comparacao.csv", AREAS),
                      ("series_producao.csv", FONTES), ("conflitos.csv", FONTES), ("marcos.csv", FONTES), ("planos.csv", FONTES),
                      ("casos_comparados.csv", FONTES)]:
        shutil.copy(src / nome, SDADOS / nome)
    log("site/dados ok")


if __name__ == "__main__":
    main()
