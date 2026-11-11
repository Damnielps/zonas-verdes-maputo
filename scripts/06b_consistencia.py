"""06b - Pos-processamento de consistencia temporal (decisoes da revisao).

Entrada: dados/proc/class/<epoca>.tif (nao e alterada). Saida: dados/proc/class_final/<epoca>.tif.
Sequencia das regras: 1985..2026 (13 epocas); 1979 fica fora das regras e e copiada sem alteracao.
 Regra 1 (construido): built_final(t) = (classe(t)==1) E (fracao de epocas >= t, incluindo t, com classe 1 >= 0,5);
   depois monotonia: construido em t permanece construido em todas as epocas seguintes (pixels
   acrescentados recebem classe 1; pixels sem dado (0) nao sao alterados). Pixels construidos em t
   removidos pela regra recebem a classe nao construida mais frequente entre as suas proprias epocas
   (empate: classe em t+1 se estiver entre as empatadas; senao a primeira classe empatada que aparece
   nas epocas seguintes; senao a de menor codigo).
 Regra 2 (tremulacao 2<->5): epocas interiores; se classe(t) em {2,5}, classe(t-1)==classe(t+1) em {2,5} e
   classe(t) != classe(t-1), classe(t) = classe(t-1). Uma passagem, simultanea, sobre o resultado da regra 1.
Saidas: class_final/<epoca>.tif, class_final/consistencia.json e consistencia.csv (pixels alterados por epoca e regra).
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import rasterio

from comum import *  # noqa

CLS = PROC / "class"
OUT = PROC / "class_final"
SEQ = [1985, 1990, 1995, 1997, 2000, 2005, 2007, 2010, 2015, 2017, 2020, 2025, 2026]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    perfil_in = None
    st = []
    for ep in SEQ:
        with rasterio.open(CLS / f"{ep}.tif") as s:
            st.append(s.read(1))
            perfil_in = s.profile
    A = np.stack(st, 0).astype("uint8")
    n = len(SEQ)
    orig = A.copy()
    B = (A == 1)

    # ---- regra 1a (revista após a auditoria final): maioria numa janela de 3 épocas ----
    # A versão anterior usava a fração de épocas >= t, que nunca removia nada nas duas últimas
    # épocas e, com a monotonia, propagava os seus erros de comissão. Agora o píxel construído
    # em t só é mantido se estiver construído em pelo menos 2 das 3 épocas da janela
    # {t-1, t, t+1}, deslocada nas extremidades ({0,1,2} e {n-3,n-2,n-1}).
    keep = np.zeros_like(B)
    for t in range(n):
        a = min(max(t - 1, 0), n - 3)
        keep[t] = B[t] & (B[a:a + 3].sum(0) >= 2)
    removidos_share = B & ~keep
    # ---- regra 1b: monotonia ----
    mono = np.maximum.accumulate(keep, axis=0)
    adicionados = mono & ~B & (A != 0)
    mono &= (A != 0) | keep            # pixels sem dado nunca viram construido
    removidos = B & ~mono          # construidos em t que nao ficam construidos (regra 1a e nao revertidos pela monotonia)

    F = A.copy()
    F[adicionados] = 1
    # reatribuicao dos removidos
    nr = removidos.any(0)
    rr, cc = np.nonzero(nr)
    cnt = np.zeros((8, len(rr)), int)
    sub = A[:, rr, cc]                                        # (n, k)
    for k in range(2, 8):
        cnt[k] = (sub == k).sum(0)
    # (se nao ha classe nao construida, o pixel nao seria removido: share=1)
    topo = cnt.max(0)
    emp = cnt == topo
    rem_k = removidos[:, rr, cc]
    for t in range(n):
        idx = np.nonzero(rem_k[t])[0]
        if len(idx) == 0:
            continue
        e = emp[:, idx]                                       # (8, m)
        nemp = e.sum(0)
        nova = np.argmax(e, 0)                                # menor codigo entre empatadas (fallback)
        for j in np.nonzero(nemp > 1)[0]:
            col = idx[j]
            for tt in range(t + 1, n):
                c = sub[tt, col]
                if c >= 2 and e[c, j]:
                    nova[j] = c
                    break
        F[t, rr[idx], cc[idx]] = nova
    conta = {}
    for t, ep in enumerate(SEQ):
        conta[ep] = {"regra1a_fracao_removeria": int(removidos_share[t].sum()),
                     "regra1_removidos_construido": int(removidos[t].sum()),
                     "regra1_acrescentados_construido": int(adicionados[t].sum())}
    pos1 = F.copy()

    # ---- regra 2: tremulacao 2<->5 (simultanea, epocas interiores) ----
    for t in range(1, n - 1):
        a, b, c = pos1[t - 1], pos1[t], pos1[t + 1]
        m = np.isin(b, (2, 5)) & np.isin(a, (2, 5)) & (a == c) & (b != a)
        F[t][m] = a[m]
        conta[SEQ[t]]["regra2_flicker_2_5"] = int(m.sum())
    for ep in SEQ:
        conta[ep].setdefault("regra2_flicker_2_5", 0)
        conta[ep]["total_alterados"] = 0
    for t, ep in enumerate(SEQ):
        conta[ep]["total_alterados"] = int((F[t] != orig[t]).sum())

    # ---- grava ----
    for t, ep in enumerate(SEQ):
        p = perfil_in.copy()
        with rasterio.open(OUT / f"{ep}.tif.tmp", "w", **p) as d:
            d.write(F[t], 1)
            d.update_tags(origem="06b_consistencia.py", regras="1 construido consistente+monotonico; 2 flicker 2-5")
        (OUT / f"{ep}.tif.tmp").replace(OUT / f"{ep}.tif")
    shutil.copy2(CLS / "1979.tif", OUT / "1979.tif")

    # ---- verificacoes ----
    nb = (F == 1)
    v = nb[:-1] & ~nb[1:]
    viol_nodata = int((v & (F[1:] == 0)).sum())          # construido em t e sem dado em t+1 (nao alterado)
    viol = int((v & (F[1:] != 0)).sum())
    mono_ok = viol == 0
    resumo = dict(sequencia=SEQ, contagens_por_epoca=conta, monotonico=mono_ok, violacoes_monotonia=viol, pixels_construido_seguido_de_sem_dado=viol_nodata,
                  construido_bbox_ha={ep: round(float(nb[t].sum() * RES * RES / 1e4), 1) for t, ep in enumerate(SEQ)})
    json.dump(resumo, open(OUT / "consistencia.json", "w"), indent=1, ensure_ascii=False)
    pd.DataFrame.from_dict(conta, orient="index").rename_axis("epoca").to_csv(OUT / "consistencia.csv")
    log(pd.DataFrame.from_dict(conta, orient="index").to_string())
    log("construido monotonico:", mono_ok, "violacoes:", viol, "| construido->sem dado:", viol_nodata)
    log("ok")


if __name__ == "__main__":
    main()
