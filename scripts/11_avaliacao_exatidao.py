"""11 - Avaliacao de exatidao de 2020 e areas ajustadas (Olofsson et al., 2014).

Entradas: dados/proc/validacao/rotulos_2020.csv (id, classe_ref, confianca, nota; classe_ref em {1,2,3,45,6,7,indeterminado}),
dados/proc/validacao/.chave/chave_2020.csv (id, classe_mapeada, estrato), dados/proc/class_final/2020.tif.
Estratos = classe mapeada agregada (1 Construido, 2 Zonas verdes, 3 Sequeiro, 45 Vegetacao nao cultivada, 6 Agua, 7 Solo exposto).
Pontos "indeterminado" sao excluidos (e contados); n_h passa a ser o numero de pontos rotulados do estrato.
Dois ambitos: 'bbox' (todos os pixels mapeados, terra + agua) e 'cidade' (mascara terrestre; so pontos dentro da mascara).
Saidas: dados/proc/validacao/exatidao_2020.json e secao em docs/qa/classificacao.md (substituida a cada execucao).
Se rotulos_2020.csv nao existe, avisa e sai sem erro.
Uso: 11_avaliacao_exatidao.py [--sem-baixa]
  --sem-baixa: exclui rotulos com confianca == "baixa"; grava exatidao_2020_sem_baixa.json (mesmo esquema), nao altera a
  secao principal do QA e (re)escreve a secao de sensibilidade (todos os rotulos x sem baixa) e a distribuicao de confianca.
"""
import argparse
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

VALD = PROC / "validacao"
HA = RES * RES / 1e4
CLASSES = [1, 2, 3, 45, 6, 7]
NOME = {1: "Construído", 2: "Zonas verdes", 3: "Sequeiro e mosaico", 45: "Vegetação não cultivada", 6: "Água", 7: "Solo exposto"}
LUT = np.array([0, 1, 2, 3, 45, 45, 6, 7])
Z = 1.96
INI = "<!-- exatidao_2020:inicio -->"
FIM = "<!-- exatidao_2020:fim -->"
INI_S = "<!-- sensibilidade_2020:inicio -->"
FIM_S = "<!-- sensibilidade_2020:fim -->"


def norm_classe(v):
    v = str(v).strip().lower()
    if v in ("indeterminado", "indet", "nan", ""):
        return "indeterminado"
    v = v.replace(".0", "")
    if v in ("4", "5", "4+5"):
        return 45
    return int(v)


def estima(cm, N):
    """cm: matriz n_ij (linhas = mapa, colunas = referencia) para CLASSES; N: pixels por estrato (mapa).
    Retorna dicionario com estimadores de Olofsson et al. (2014)."""
    k = len(CLASSES)
    ni = cm.sum(1).astype(float)
    Ntot = N.sum()
    W = N / Ntot
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.where(ni[:, None] > 0, cm / ni[:, None], np.nan)          # n_ij / n_i
        pij = W[:, None] * frac
        pj = np.nansum(pij, 0)                                              # proporcao de area (referencia)
        den = np.where(ni > 1, ni - 1, np.nan)
        var_pj = np.nansum((W[:, None] ** 2) * frac * (1 - frac) / den[:, None], 0)
        U = np.diag(cm) / ni
        seU = np.sqrt(U * (1 - U) / den)
        O = np.nansum(np.diag(pij))
        seO = np.sqrt(np.nansum(W ** 2 * U * (1 - U) / den))
        Ncj = np.nansum((N / ni)[:, None] * cm, 0)                          # N.j estimado
        P = np.diag(pij) / pj
        seP = np.full(k, np.nan)
        for j in range(k):
            if not np.isfinite(Ncj[j]) or Ncj[j] == 0:
                continue
            outros = [i for i in range(k) if i != j]
            t2 = np.nansum([(N[i] ** 2) * frac[i, j] * (1 - frac[i, j]) / den[i] for i in outros])
            t1 = (N[j] ** 2) * (1 - P[j]) ** 2 * U[j] * (1 - U[j]) / den[j]
            seP[j] = np.sqrt((t1 + P[j] ** 2 * t2) / Ncj[j] ** 2)
    return dict(ni=ni, U=U, seU=seU, P=P, seP=seP, O=float(O), seO=float(seO), pj=pj, sepj=np.sqrt(var_pj),
                area_ha=pj * Ntot * HA, se_area_ha=np.sqrt(var_pj) * Ntot * HA)


def f(v, p=1):
    return "" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:,.{p}f}"


def escreve_sensibilidade(res_sb, dist_conf):
    base_p = VALD / "exatidao_2020.json"
    if not base_p.exists():
        log("exatidao_2020.json ausente; rode primeiro sem --sem-baixa.")
        return
    base = json.load(open(base_p))
    md = [INI_S, "## 9. Sensibilidade a rótulos de baixa confiança (validação cega de 2020)\n",
          "Gerado por `scripts/11_avaliacao_exatidao.py --sem-baixa`. Os rótulos foram atribuídos por um agente automático de interpretação visual de imagens, "
          "cego ao mapa; recomenda-se revisão humana de uma subamostra. A tabela compara o conjunto completo com o conjunto sem os rótulos de confiança 'baixa'.\n",
          "Distribuição da confiança dos rótulos (todos os pontos rotulados): " + ", ".join(f"{k} {v}" for k, v in sorted(dist_conf.items())) + ".\n"]
    for amb, nome in (("cidade", "Cidade (máscara terrestre)"), ("bbox", "Retângulo de estudo")):
        A, B = base["ambitos"][amb], res_sb["ambitos"][amb]
        md.append(f"### {nome}\n")
        md.append("| medida | todos os rótulos | sem confiança baixa |")
        md.append("|---|---|---|")
        md.append(f"| pontos usados | {sum(A['n_por_estrato'].values())} | {sum(B['n_por_estrato'].values())} |")
        md.append(f"| exatidão global (%) | {100*A['exatidao_global']['valor']:.1f} ± {100*A['exatidao_global']['ic95']:.1f} | {100*B['exatidao_global']['valor']:.1f} ± {100*B['exatidao_global']['ic95']:.1f} |")
        for k, n in (("1", "construído"), ("2", "zonas verdes")):
            for tag, key in (("UA", "exatidao_usuario"), ("PA", "exatidao_produtor")):
                a, b = A[key][k], B[key][k]
                md.append(f"| {tag} classe {k} ({n}) (%) | {100*a['valor']:.1f} ± {100*a['ic95']:.1f} | {100*b['valor']:.1f} ± {100*b['ic95']:.1f} |")
        a, b = A["area_ajustada_ha"]["2"], B["area_ajustada_ha"]["2"]
        md.append(f"| área ajustada classe 2 (ha) | {a['valor']:,.0f} ± {a['ic95']:,.0f} | {b['valor']:,.0f} ± {b['ic95']:,.0f} |")
        md.append("")
    md.append(FIM_S)
    qa = QA / "classificacao.md"
    txt = qa.read_text(encoding="utf-8")
    bloco = "\n".join(md) + "\n"
    if INI_S in txt and FIM_S in txt:
        a = txt.index(INI_S); b = txt.index(FIM_S) + len(FIM_S)
        txt = txt[:a] + bloco.rstrip("\n") + txt[b:]
    else:
        txt = txt.rstrip("\n") + "\n\n" + bloco
    qa.write_text(txt, encoding="utf-8")


def main(sem_baixa=False):
    rot_p = VALD / "rotulos_2020.csv"
    if not rot_p.exists():
        log("rotulos_2020.csv ausente; nada a fazer.")
        return
    rot = pd.read_csv(rot_p, dtype=str)
    rot["ref"] = rot.classe_ref.map(norm_classe)
    chave = pd.read_csv(VALD / ".chave" / "chave_2020.csv")
    pts = pd.read_csv(VALD / "pontos_2020_cego.csv")
    d = chave.merge(rot[["id", "ref", "confianca"]], on="id", how="left").merge(pts[["id", "x", "y"]], on="id")
    dist_conf = {k: int(v) for k, v in rot.confianca.fillna("").str.strip().str.lower().value_counts().items()}
    if sem_baixa:
        d = d[d.confianca.fillna("").str.strip().str.lower() != "baixa"]
    n_sem_rotulo = int(d.ref.isna().sum())
    d = d.dropna(subset=["ref"])
    indet = d[d.ref == "indeterminado"]
    d = d[d.ref != "indeterminado"].copy()
    d["ref"] = d.ref.astype(int)

    with rasterio.open(PROC / "class_final" / "2020.tif") as s:
        cl = s.read(1)
    agr = LUT[cl]
    dist = gpd.read_file(PROC / "limites.gpkg", layer="distritos")
    dist = dist[dist.adm2_name != "KaNyaka"]
    cidade = features.rasterize(((g, 1) for g in dist.geometry), out_shape=SHAPE, transform=TRANSFORM, fill=0, dtype="uint8").astype(bool)
    r = np.floor((Y1 - d.y.values) / RES).astype(int); c = np.floor((d.x.values - X0) / RES).astype(int)
    d["na_cidade"] = cidade[r, c]
    ambitos = {"bbox": (np.ones(SHAPE, bool) & (cl > 0), d), "cidade": (cidade & (cl > 0), d[d.na_cidade])}
    res = dict(n_pontos=int(len(chave)), n_sem_rotulo=n_sem_rotulo, n_indeterminados=int(len(indet)),
               indeterminados_por_estrato={str(k): int(v) for k, v in indet.estrato.value_counts().items()} if len(indet) else {},
               n_usados=int(len(d)), classes=CLASSES, ambitos={})
    res["sem_baixa"] = bool(sem_baixa)
    res["distribuicao_confianca"] = dist_conf
    md = []
    md.append(INI)
    md.append("## 8. Exatidão e áreas ajustadas de 2020 (validação cega)\n")
    md.append(f"Gerado por `scripts/11_avaliacao_exatidao.py`. Amostra estratificada pela classe mapeada de 2020 (`class_final`), legenda agregada, "
              f"rotulada às cegas por interpretação visual de chips Sentinel-2 10 m / Landsat 30 m. Pontos: {res['n_pontos']}; "
              f"indeterminados excluídos: {res['n_indeterminados']}; sem rótulo: {n_sem_rotulo}; usados: {res['n_usados']}. "
              "Estimadores de Olofsson et al. (2014); IC 95% = ±1,96 EP. Linhas = classe mapeada, colunas = referência.\n")
    for amb, (msk, dd) in ambitos.items():
        N = np.array([(agr[msk] == k).sum() for k in CLASSES], float)
        cm = np.zeros((6, 6), int)
        for a, b in zip(dd.estrato, dd.ref):
            if a in CLASSES and b in CLASSES:
                cm[CLASSES.index(a), CLASSES.index(b)] += 1
        E = estima(cm, N)
        res["ambitos"][amb] = dict(
            area_mapeada_ha={str(k): float(N[i] * HA) for i, k in enumerate(CLASSES)}, matriz_confusao=cm.tolist(),
            n_por_estrato={str(k): int(cm[i].sum()) for i, k in enumerate(CLASSES)},
            exatidao_global=dict(valor=E["O"], ic95=Z * E["seO"]),
            exatidao_usuario={str(k): dict(valor=float(E["U"][i]), ic95=float(Z * E["seU"][i])) for i, k in enumerate(CLASSES)},
            exatidao_produtor={str(k): dict(valor=float(E["P"][i]), ic95=float(Z * E["seP"][i])) for i, k in enumerate(CLASSES)},
            area_ajustada_ha={str(k): dict(valor=float(E["area_ha"][i]), ic95=float(Z * E["se_area_ha"][i]),
                                           mapeada=float(N[i] * HA)) for i, k in enumerate(CLASSES)},
            area_total_ha=float(N.sum() * HA))
        md.append(f"### 8.{1 if amb == 'bbox' else 2} Âmbito: {'bbox (terra + água, todos os píxeis mapeados)' if amb == 'bbox' else 'máscara terrestre da Cidade de Maputo'}\n")
        if amb == "cidade":
            md.append("Só pontos dentro da máscara; estratos com menos de 2 pontos não têm erro padrão (células vazias). Amostra pequena: ler com cautela.\n")
        md.append("Matriz de confusão (contagem de pontos):\n")
        md.append("| mapa \\ referência | " + " | ".join(str(k) for k in CLASSES) + " | total |")
        md.append("|---|" + "---|" * (len(CLASSES) + 1))
        for i, k in enumerate(CLASSES):
            md.append(f"| {k} {NOME[k]} | " + " | ".join(str(v) for v in cm[i]) + f" | {cm[i].sum()} |")
        md.append(f"| total | " + " | ".join(str(v) for v in cm.sum(0)) + f" | {cm.sum()} |\n")
        md.append(f"Exatidão global (ponderada pela área): {100*E['O']:.1f}% ± {100*Z*E['seO']:.1f} p.p.\n")
        md.append("| classe | área mapeada (ha) | área ajustada (ha) | IC 95% (± ha) | exatidão do usuário (%) | ± | exatidão do produtor (%) | ± |")
        md.append("|---|---|---|---|---|---|---|---|")
        for i, k in enumerate(CLASSES):
            md.append(f"| {k} {NOME[k]} | {f(N[i]*HA,0)} | {f(E['area_ha'][i],0)} | {f(Z*E['se_area_ha'][i],0)} | {f(100*E['U'][i])} | "
                      f"{f(100*Z*E['seU'][i])} | {f(100*E['P'][i])} | {f(100*Z*E['seP'][i])} |")
        md.append("")
    md.append(FIM)
    if sem_baixa:
        json.dump(res, open(VALD / "exatidao_2020_sem_baixa.json", "w"), indent=1, ensure_ascii=False)
        escreve_sensibilidade(res, dist_conf)
        log("ok (sem baixa); global bbox:", round(res["ambitos"]["bbox"]["exatidao_global"]["valor"], 3), "usados:", res["n_usados"])
        return
    json.dump(res, open(VALD / "exatidao_2020.json", "w"), indent=1, ensure_ascii=False)
    # secao no documento QA (substitui a anterior, se houver)
    qa = QA / "classificacao.md"
    txt = qa.read_text(encoding="utf-8")
    bloco = "\n".join(md) + "\n"
    if INI in txt and FIM in txt:
        a = txt.index(INI); b = txt.index(FIM) + len(FIM)
        txt = txt[:a] + bloco.rstrip("\n") + txt[b:]
    else:
        txt = txt.rstrip("\n") + "\n\n" + bloco
    qa.write_text(txt, encoding="utf-8")
    log("ok; global bbox:", round(res["ambitos"]["bbox"]["exatidao_global"]["valor"], 3), "indeterminados:", res["n_indeterminados"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-baixa", action="store_true", help='exclui rotulos com confianca "baixa"')
    main(ap.parse_args().sem_baixa)
