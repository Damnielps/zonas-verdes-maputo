"""Constroi o artigo de ponta a ponta: artigo.md -> artigo_final.md, artigo.docx, artigo.pdf.

Uso: .venv/bin/python -I scripts/21_artigo.py [--tolerar] [--sem-pdf]

Etapas: (1) figuras 4 e 5 + conversao de imagens dos planos; (2) quadros gerados;
(3) placeholders {{chave}}; (4) citacoes [@chave] -> autor-data ABNT e lista NBR 6023;
(5) artigo_final.md; (6) blocos JSON -> artigo.docx (artigo/build/build_docx.js) e HTML -> PDF (Chrome);
(7) exportacao web: site/artigo.html + site/artigo/{img,artigo.pdf} (só o PDF é oferecido para download no site).
Falhas duras (chave sem ficha, placeholder nao resolvido, figura ausente) abortam,
exceto com --tolerar, que registra o problema e segue com um fallback explicito.
Nao edita a prosa de artigo/artigo.md.
"""
import csv
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from ardosia_palette import (apply_ardosia, ARDOSIA, TERRACOTA, PETROLEO, OCRE, PEDRA,  # noqa: E402
                             GRAFITE, FILETE)

TOLERAR = "--tolerar" in sys.argv
SEM_PDF = "--sem-pdf" in sys.argv
ART = RAIZ / "artigo"
BUILD = ART / "build"
IMG = BUILD / "img"
FIGART = RAIZ / "dados" / "fig" / "artigo"
FICHAS = RAIZ / "fontes" / "fichas"
ACESSO = "11 nov. 2026"
ERROS = []   # falhas duras
AVISOS = []


def erro(msg):
    ERROS.append(msg)
    print("ERRO:", msg)


def lr(path):
    return list(csv.DictReader(open(path, encoding="utf8")))


def nbsp(s):
    return s.replace("\u202f", "\u00a0")


# ------------------------------------------------------------------ 1. figuras
def fig4():
    """Figura 4 (revista pós-auditoria): três estimativas por perímetro, 1985–2025, pequenos múltiplos."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    apply_ardosia()
    d = pd.read_csv(RAIZ / "dados/proc/areas/envelopes_comparacao.csv")
    d = d[d.epoca <= 2025]
    paineis = [
        ("plano1985_zv_permanentes", "Zonas verdes permanentes (plano de 1985)"),
        ("plano1985_zv_provisorias", "Zonas verdes provisórias (plano de 1985)"),
        ("peumm2008_agropecuaria", "Área agropecuária (PEUMM 2008)"),
        ("baixada_<15m_tpi<0", "Baixadas (relevo)"),
    ]
    est = [("pct_ghsl", "GHSL (superfície construída)", (0, (1, 1.6)), "o"),
           ("pct_bruto", "Classificação bruta", (0, (4, 2)), "s"),
           ("pct_final", "Classificação pós-processada", "-", "^")]
    fig, axs = plt.subplots(2, 2, figsize=(6.3, 5.0), sharex=True)
    ymax = max(d[["pct_ghsl", "pct_bruto", "pct_final"]].max()) * 1.08
    for ax, (per, tit) in zip(axs.flat, paineis):
        s_ = d[d.perimetro == per].sort_values("epoca")
        lo = s_[["pct_ghsl", "pct_bruto", "pct_final"]].min(axis=1)
        hi = s_[["pct_ghsl", "pct_bruto", "pct_final"]].max(axis=1)
        ax.fill_between(s_.epoca, lo, hi, color=FILETE, alpha=0.6, lw=0, zorder=1)
        for col, lab, ls, mk in est:
            ax.plot(s_.epoca, s_[col], color=ARDOSIA if col != "pct_final" else TERRACOTA,
                    ls=ls, marker=mk, ms=2.8, lw=1.3, zorder=3, label=lab)
        for xv in (2008, 2012):
            ax.axvline(xv, color=PEDRA, lw=0.7, ls=(0, (3, 3)), zorder=0)
        ax.set_title(tit, fontsize=8, loc="left", family="sans-serif")
        ax.set_ylim(0, ymax)
        ax.yaxis.grid(True)
        ax.tick_params(labelsize=7)
    for ax in axs[:, 0]:
        ax.set_ylabel("Fração construída (%)", fontsize=7.5, family="sans-serif")
    axs[0, 0].text(2008.4, ymax * 0.92, "PEUMM", fontsize=6, color=GRAFITE, family="sans-serif")
    axs[0, 0].text(2012.4, ymax * 0.82, "Circular", fontsize=6, color=GRAFITE, family="sans-serif")
    for ax in axs[1]:
        ax.set_xticks([1985, 1995, 2005, 2015, 2025])
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    out = FIGART / "fig4_envelopes.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("fig4 ->", out)


def fig5():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    apply_ardosia()
    rows = lr(RAIZ / "fontes/series_producao.csv")
    usadas = []

    def pega(var, chave, recorte):
        out = {}
        for r in rows:
            if (r["variavel"] == var and r["fonte_chave"] == chave and r["status"] == "VERIFICADO"
                    and r["recorte_espacial"] == recorte):
                a = int(r["ano_referencia"])
                if a not in out:
                    out[a] = float(r["valor"])
                    usadas.append((chave, var, a, r["valor"], r["pagina_tabela"]))
        return out

    ch = "christie_1996_l5"
    rec = "cooperativas UGC"
    memb = pega("cooperativas UGC (membros)", ch, rec)
    area = pega("cooperativas UGC (area)", ch, rec)
    agr = pega("producao agricola cooperativas UGC", ch, rec)
    pec = pega("producao pecuaria cooperativas UGC", ch, rec)
    tot = "Total (4 distritos)"
    asso = pega("associacoes agricolas (numero)", "engel_2019_l5", tot)
    prod = pega("produtores associados", "engel_2019_l5", tot)
    hect = pega("area ocupada por associacoes", "engel_2019_l5", tot)

    fig = plt.figure(figsize=(6.3, 7.4))
    gs = fig.add_gridspec(3, 6, height_ratios=[1, 1, 0.95], hspace=0.62, wspace=1.4)
    painel = [
        (gs[0, 0:3], memb, "Membros", "nº", ARDOSIA),
        (gs[0, 3:6], area, "Área das cooperativas", "ha", PETROLEO),
        (gs[1, 0:3], agr, "Produção agrícola", "t", ARDOSIA),
        (gs[1, 3:6], pec, "Produção pecuária (carne)", "t", OCRE),
    ]
    for pos, ser, tit, un, cor in painel:
        ax = fig.add_subplot(pos)
        anos = sorted(ser)
        full = list(range(min(anos), max(anos) + 1))
        y = [ser.get(a, np.nan) for a in full]
        ax.plot(full, y, color=cor, marker="o", ms=3.2, lw=1.5)
        ax.set_title(f"{tit} ({un})", fontsize=8.5, family="sans-serif", pad=6)
        ax.set_xlim(1980.5, 1994.5)
        ax.set_xticks([1981, 1985, 1989, 1993])
        ax.set_ylim(bottom=0)
        ax.tick_params(labelsize=7)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
            lambda v, _: f"{v:,.0f}".replace(",", "\u00a0")))
    fig.text(0.02, 0.965, "A  Cooperativas da UGC, 1981–1994 (série contínua; anos sem valor verificado ficam em branco)",
             fontsize=8.5, family="sans-serif", color=GRAFITE, ha="left")
    fig.text(0.02, 0.335, "B  Associações de produtores, 2018 (4 distritos; definição distinta, não ligada à série A)",
             fontsize=8.5, family="sans-serif", color=GRAFITE, ha="left")
    for i, (ser, tit, un) in enumerate([(asso, "Associações", "nº"), (prod, "Produtores", "pessoas"),
                                        (hect, "Área ocupada", "ha")]):
        ax = fig.add_subplot(gs[2, 2 * i:2 * i + 2])
        for a, v in ser.items():
            ax.plot([a], [v], marker="D", ms=7, color=TERRACOTA, ls="none")
            ax.annotate(f"{v:,.0f}".replace(",", "\u00a0"), (a, v), textcoords="offset points",
                        xytext=(0, 9), ha="center", fontsize=8, color=TERRACOTA, family="sans-serif")
        ax.set_xlim(2017, 2019)
        ax.set_xticks([2018])
        ax.set_ylim(0, max(ser.values()) * 1.35 if ser else 1)
        ax.set_title(f"{tit} ({un})", fontsize=8.5, family="sans-serif", pad=6)
        ax.tick_params(labelsize=7)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
            lambda v, _: f"{v:,.0f}".replace(",", "\u00a0")))
    out = FIGART / "fig5_producao.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("fig5 ->", out, "| linhas de series_producao.csv usadas:", len(usadas))
    for u in usadas:
        print("   ", u)


def imagens_planos():
    from PIL import Image
    IMG.mkdir(parents=True, exist_ok=True)
    mapa = {}
    for nome in ("1985_plano_estrutura", "2008_peumm_ordenamento"):
        src = RAIZ / "site/img/planos" / f"{nome}.webp"
        dst = IMG / f"{nome}.png"
        if not src.exists():
            erro(f"imagem ausente: {src}")
            continue
        im = Image.open(src).convert("RGB")
        if im.width > 2400:
            im = im.resize((2400, round(im.height * 2400 / im.width)), Image.LANCZOS)
        im.save(dst)
        mapa[f"../site/img/planos/{nome}.webp"] = f"build/img/{nome}.png"
    return mapa


# ------------------------------------------------------------------ 2. quadros
def tabela_md(cab, linhas, alinh=None):
    alinh = alinh or ["---"] * len(cab)
    esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    out = ["| " + " | ".join(esc(c) for c in cab) + " |", "|" + "|".join(alinh) + "|"]
    out += ["| " + " | ".join(esc(c) for c in l) + " |" for l in linhas]
    return "\n".join(out)


Q1 = {  # id: (ano exibido, plano, autor/orgao, estatuto, tratamento)  -- condensado de fontes/planos.csv
    "hall_1876": ("1876", "Plano de esgoto e aterro do pântano de Lourenço Marques", "R. T. Hall, a pedido do governador A. de Castilho", "Não executado como cidade nova; drenagem do pântano realizada", "Sem tratamento de agricultura nas fontes lidas"),
    "alternativos_1878": ("1878", "Planta da nova povoação / Projecto de melhoramentos", "F. Jeppe; J. A. Ferreira Maia (autoria divergente entre fontes)", "Não realizados", "Sem tratamento de agricultura"),
    "araujo_1887": ("1887", "Projecto de Ampliação da Cidade de Lourenço Marques (Plano Araújo)", "A. J. de Araújo, diretor de Obras Públicas", "Aprovado; execução parcial", "Sem agricultura nem cintura; reserva espaços para jardins e protege de construção a encosta da Malanga"),
    "cristino_1940s": ("1940", "Eixo cívico / plano de urbanização", "L. Cristino da Silva", "Parcialmente executado", "Sem tratamento de agricultura"),
    "aguiar_1955": ("1955", "Plano Geral de Urbanização de Lourenço Marques (Plano Aguiar)", "J. A. Aguiar; Gabinete de Urbanização do Ultramar", "Aprovado", "Zona de reserva junto à cidade e “zona rural de protecção” de pelo menos 5 km: primeira cintura formal, de função urbana e não agrícola"),
    "revisao_1962_67": ("1962–67", "Estudos de urbanização e revisão do PGULM", "V. Camelo; F. Mesquita (serviços da Câmara Municipal)", "Estudos; sem aprovação referida", "Sem tratamento de agricultura"),
    "prosalm_1960s": ("anos 1960", "Plano Regulador da Ocupação do Solo nos Arredores de Lourenço Marques (PROSALM)", "Comissão criada para o plano", "n.d.", "Conteúdo não descrito nas fontes lidas"),
    "azevedo_1969": ("1969", "Plano Director de Urbanização de Lourenço Marques", "M. de Azevedo; Gabinete de Urbanização da Câmara Municipal", "Aprovado em 1972; seguido na gestão depois de 1975", "Sem agricultura no texto de Pimentel; “áreas verdes” como património natural e corredor de drenagem; zonamento pela vocação biofísica"),
    "guharlm_1960_70": ("1960–70", "Plano de Beneficiação da Área Suburbana; Plano Parcial das Lagoas", "GUHARLM", "Poucas ações concretizadas", "Sem tratamento de agricultura nas fontes lidas"),
    "reuniao_1979": ("1979", "1.ª Reunião Nacional das Cidades e Bairros Comunais", "Governo/Frelimo", "Decisão política, não plano", "Zonas verdes incorporadas ao território urbano como base do autoabastecimento urbano"),
    "plano_estrutura_1985": ("1985", "Plano de Estrutura da Cidade de Maputo", "Instituto Nacional de Planeamento Físico (INPF)", "Não aprovado; o plano de 1969 continuou a vigorar", "Zona agropecuária de pequenas quintas no Infulene e na Costa do Sol; legenda com zonas verdes permanentes e provisórias"),
    "peamm_1999": ("1999", "Plano de Estrutura da Área Metropolitana de Maputo (PEAMM)", "Arcadis Euroconsult; IHS; JTK Associates (Banco Mundial)", "Não entrou em vigor", "Sem agricultura no texto lido"),
    "peumm_2008": ("2008", "Plano de Estrutura Urbana do Município de Maputo (PEUMM)", "Conselho Municipal de Maputo; UEM", "Em vigor; revisão devida após 10 anos", "Classe “Espaço para Actividade Agrícola”, com exceções amplas (edifícios, aterros) e, no art. 74(e), unidades hoteleiras em lotes de 10 000 m² ou mais"),
    "ppu_norte_2010": ("2010", "Planos Parciais de Urbanização de Zimpeto, Magoanine B e C e Maxaquene A", "Conselho Municipal de Maputo", "Aprovados", "Conteúdo agrícola não descrito"),
    "peu_matola_2010": ("2010", "Plano de Estrutura Urbana da Cidade da Matola", "Município da Matola", "Aprovado (segundo JICA; não verificado em ato)", "Não verificado"),
    "pgu_katembe_2012": ("2012", "Plano Geral de Urbanização de KaTembe", "Betar", "Revisão financiada pelo PTUM", "Sem classe agrícola; IDA (2024) prevê “50km2 of protected area and public equipment”"),
    "ppu_luis_cabral_2014": ("2014", "Plano Parcial de Urbanização do Bairro Luís Cabral", "Conselho Municipal de Maputo", "Em vigor", "Espaços agrícolas de produção e a recuperar; permite e incentiva agricultura e silvicultura; prevê demolir construções de outro uso"),
    "jica_2014": ("2014", "Plano Diretor de Transportes da Grande Maputo", "JICA; PADECO; Nippon Koei; Conselho Municipal de Maputo", "Estudo técnico", "“Greenbelt” como bacia de retenção; variante da EN1 ao longo dela afeta terra agrícola; Marracuene e Boane tratados como áreas de crescimento"),
    "ptum_2021_2024": ("2021", "PTUM (P171449), componente 3(c)(i): plano espacial urbano", "Conselho Municipal de Maputo; Banco Mundial (IDA)", "Em execução", "Agricultura não mencionada no acordo"),
    "peumm_revisao_2026": ("2026", "Revisão do PEUMM / novo modelo territorial", "Conselho Municipal de Maputo", "Consultoria lançada; sem prazo nem consultor divulgados", "Agricultura e zonas verdes não mencionadas na notícia"),
}


def quadro1():
    rows = lr(RAIZ / "fontes/planos.csv")
    ids = [r["id"] for r in rows]
    for i in ids:
        if i not in Q1:
            erro(f"Quadro 1: id sem condensacao: {i}")
    for i in Q1:
        if i not in ids:
            erro(f"Quadro 1: condensacao sem linha no CSV: {i}")
    linhas = []
    for r in sorted(rows, key=lambda r: int(r["ano"])):
        if r["id"] in Q1:
            t = Q1[r["id"]]
            if len(t[4].split()) > 30:
                erro(f"Quadro 1: tratamento > 30 palavras em {r['id']}")
            linhas.append(t)
    return ("Quadro 1 – Planos urbanísticos e decisões políticas relativos à periferia agrícola, Lourenço Marques e Maputo, 1876–2026\n\n"
            + tabela_md(["Ano", "Plano", "Autor/órgão", "Estatuto", "Tratamento da agricultura"], linhas)
            + "\n\nFonte: elaboração própria a partir de [@pimentel_2013; @mendonca_2018; @raposo_2018; "
              "@christie_1996; @cmm_2021a; @cmm_2021b; @jica_2014; @ida_2024].")


def quadro2():
    oob = json.load(open(RAIZ / "dados/proc/class/oob.json"))["oob"]
    linhas = []
    txt = (RAIZ / "docs/qa/composicoes.md").read_text(encoding="utf8").split("## Percentis")[0]
    for l in txt.splitlines():
        m = re.match(r"\|\s*(\d{4})\s*\|(.*)\|\s*$", l)
        if not m:
            continue
        ep = m.group(1)
        c = [x.strip() for x in m.group(2).split("|")]
        fonte, sensor = c[0], c[1]
        acc = oob.get(ep, {}).get("acc")
        obs_oob = f"{acc:.2f}".replace(".", ",") if acc is not None else "—"
        if ep == "1979":
            ep_exib, f, s = "1980", "Cena LM03 de 9 jun. 1979 (substitui o censo de 1980)", "Landsat 3 MSS, 60 m"
            o = "Reamostrada a 30 m; sem bandas azul e SWIR; mapa tratado como ordem de grandeza"
        elif ep == "1985":
            ep_exib, f, s = "1985", "Cena LT05 de 1.º jun. 1984", "Landsat 5 TM"
            o = "Substitui o GeoMAD de 1985, que cobria apenas 30% da área"
        elif ep == "2010":
            ep_exib, f, s = "2010", "Cena LT05 de 9 abr. 2011", "Landsat 5 TM"
            o = "Substitui o GeoMAD de 2010, com faixas de falha do Landsat 7; fora da estação seca"
        elif ep == "2026":
            ep_exib, f, s = "2026", "Mediana de 12 cenas LC08/LC09, mai.–ago. 2026", "Landsat 8/9 OLI"
            o = "Sem composição anual disponível"
        else:
            g = re.search(r"(gm_[a-z0-9_]+)", fonte)
            ep_exib, f = ep, f"GeoMAD anual, Digital Earth Africa ({g.group(1)})"
            s = {"Landsat 5/7 TM/ETM+": "Landsat 5/7 TM/ETM+", "Landsat 8 OLI": "Landsat 8 OLI",
                 "Landsat 8/9 OLI": "Landsat 8/9 OLI"}.get(sensor, sensor)
            o = ""
        linhas.append((ep_exib, f, s, o or "—", obs_oob))
    if len(linhas) != 14:
        erro(f"Quadro 2: esperadas 14 epocas, achei {len(linhas)}")
    return ("Quadro 2 – Imagens, sensores e substituições por época do painel Landsat\n\n"
            + tabela_md(["Época", "Fonte/imagem", "Sensor", "Observação", "Exatidão OOB"], linhas)
            + "\n\nFonte: elaboração própria. A coluna de exatidão é a out-of-bag dos modelos (reprodução dos rótulos "
              "de treino, não validação independente).")


Q3 = {  # cidade: (instrumento, escala/abastecimento, licao)
    "Dar es Salaam": ("Nenhum identificado; autores recomendam posse incremental e preservar terra agrícola", "70% do amaranto consumido vem da região da cidade", "Sem proteção formal, a quota urbana cai com a conversão do solo; posse provisória incremental como compromisso"),
    "Kampala": ("Ordenança de 2006 (permit e licença); proteção do solo não identificada", "49% dos agregados cultivam na cidade (2002, fonte secundária; citado)", "Licenciamento não equivale a proteção do solo; precisa de zonamento complementar"),
    "Nairobi": ("Lei do condado (2015): agricultura no planeamento físico e uso de terra vaga", "—", "Prever na lei local o uso temporário de terra vaga e a ligação ao plano físico"),
    "Accra": ("Nenhum; plano setorial (METASIP) previa zonear áreas para agricultura", "~10% do repolho vem da agricultura de espaço aberto na cidade (citado)", "Posse informal e fragmentação institucional (7 ministérios) limitam a proteção, mesmo com plano setorial"),
    "Kumasi": ("Nenhum identificado", "~90% da alface e da cebolinha; periurbana 36% do abastecimento no pico (todas as culturas)", "Folhosas perecíveis são nicho defensável; vale proteger a proximidade ao mercado"),
    "Lusaka": ("Nenhum a favor da agricultura", "—", "Exemplo negativo: o zonamento monofuncional criminaliza a agricultura urbana"),
    "Harare": ("Nenhum", "—", "Mudar a visão oficial exige evidência"),
    "Cape Town": ("Limite urbano e reserva de terra agrícola de alto potencial (CTSDF)", "~1% do abastecimento alimentar urbano (citado); ~3 000 produtores apoiados por ONGs e 300 pelo UAAP (c. 2011)", "Zonamento protege terra de alto potencial, mas exige salvaguardas contra flexibilizações sucessivas"),
    "Havana": ("Usufruto sem propriedade; sem proteção formal do solo nas fontes lidas", "Cuba 2012: ~70% da procura de hortícolas e frutas frescas (dado nacional)", "Estado cede terra e compra com apoio técnico; quase não há dados de Havana isolada"),
    "Rosario": ("Cessão de terrenos fiscais ou privados (Ord. 7341, art. 3)", "—", "Cessão formal de terra pública a famílias vulneráveis, com feiras de venda direta, é replicável em lotes vagos"),
    "São Paulo": ("Zona rural no PDE-2014 (22,9% do município); Reserva da Biosfera do Cinturão Verde", "435 produtores cadastrados em 5 092 ha (slides, ano incerto; citado)", "O estatuto rural do solo é pré-condição para acessar apoio público"),
    "Belo Horizonte": ("Não identificado", "—", "Integração com saúde e escolas via segurança alimentar; fontes fracas"),
    "Hanói": ("Cinturão verde para hortaliça segura (Plano 2030); sem proteção geral", "40% das hortaliças consumidas na cidade são produzidas dentro dos seus limites (estudo de 2004, citado)", "Quando o plano converte a terra, são necessários compensação, aviso e cinturão reservado desde o início"),
    "Lisboa": ("Espaços verdes do PDM; Parque Periférico (300 ha) de 1994 não concretizado", "179 ha de hortas em 1947; pico em 1987; queda desde 1995", "Legalizar e dotar de infraestrutura as hortas informais, em vez de apenas fiscalizar"),
}


def quadro3():
    rows = lr(RAIZ / "fontes/casos_comparados.csv")
    linhas, chaves = [], []
    for r in rows:
        if r["cidade"].strip().lower().startswith("maputo"):
            continue
        for k in r["fontes_chaves"].split(";"):
            if k.strip() and k.strip() not in chaves:
                chaves.append(k.strip())
        if r["cidade"] not in Q3:
            erro(f"Quadro 3: cidade sem condensacao: {r['cidade']}")
            continue
        i, e, l = Q3[r["cidade"]]
        linhas.append((f"{r['cidade']} ({r['pais']})", i or "—", e or "—", l or "—"))
    return ("Quadro 3 – Instrumentos de proteção do solo agrícola urbano e lições em cidades comparadas\n\n"
            + tabela_md(["Cidade (país)", "Instrumento de proteção do solo", "Escala/abastecimento", "Lição para Maputo"], linhas)
            + "\n\nFonte: elaboração própria a partir de " + "[" + "; ".join(f"@{k}" for k in chaves) + "].")


# ------------------------------------------------------------------ 4. citacoes
SURN = re.compile(r"^\s*((?:[A-ZÀ-ÝÇ][A-ZÀ-ÝÇ'’\- ]+)|(?:Mc[A-Z]+)),\s")
OVERRIDE_LABEL = {"uccla_2020": "UCCLA"}
# Autores institucionais: (regex do inicio da entrada na ficha, novo inicio "SIGLA – NOME", sigla usada na citacao)
SIGLAS = [
    (r"^JAPAN INTERNATIONAL COOPERATION AGENCY \(JICA\)", "JICA – JAPAN INTERNATIONAL COOPERATION AGENCY", "JICA"),
    (r"^CONSELHO MUNICIPAL DE MAPUTO(?: \(CMM\))?", "CMM – CONSELHO MUNICIPAL DE MAPUTO", "CMM"),
    (r"^REPÚBLICA DE MOÇAMBIQUE; INTERNATIONAL DEVELOPMENT ASSOCIATION", "IDA – INTERNATIONAL DEVELOPMENT ASSOCIATION; REPÚBLICA DE MOÇAMBIQUE", "IDA"),
    (r"^OCHA FIELD INFORMATION SERVICES SECTION(?: \(FISS\))?", "OCHA – FIELD INFORMATION SERVICES SECTION (FISS)", "OCHA"),
    (r"^FAO(?=\.)", "FAO – FOOD AND AGRICULTURE ORGANIZATION OF THE UNITED NATIONS", "FAO"),
    (r"^INSTITUTO NACIONAL DE PLANEAMENTO FÍSICO(?: \(INPF\))?", "INPF – INSTITUTO NACIONAL DE PLANEAMENTO FÍSICO", "INPF"),
]


def aplicar_sigla(ref):
    for rx, novo, sig in SIGLAS:
        if re.match(rx, ref):
            return re.sub(rx, novo, ref, count=1)
    return ref
BOLD_OVERRIDE = {"mougeot_2000": "Growing cities, growing food"}
REF_OVERRIDE = {
    "leitgeb_2015": ("LEITGEB, Friedrich; SCHNEIDER, Sarah; VOGL, Christian R. Increasing food sovereignty with urban "
                     "agriculture in Cuba. **Agriculture and Human Values**, 2015. DOI: 10.1007/s10460-015-9616-9."),
    "rosario_2002": ("MUNICIPALIDAD DE ROSARIO. Concejo Municipal. **Ordenanza n. 7341: crea el Programa Municipal de "
                     "Desarrollo de la Agricultura Orgánica**. Sala de Sesiones, 17 jun. 2002."),
    "mougeot_2000": ("MOUGEOT, L. J. A. Urban agriculture: definition, presence, potentials and risks. In: "
                     "*Growing cities, growing food*: urban agriculture on the policy agenda. Feldafing: DSE/ZEL, 2000. "
                     "(Thematic Paper 1). Disponível em: https://ruaf.org/assets/2019/11/Growing-Cities-Growing-Food.pdf."),
}


def cabeca(linha):
    """Retorna (head, resto) separando autoria do resto da referencia."""
    for m in re.finditer(r"\.\s+", linha):
        pre = linha[:m.start()]
        prev = re.search(r"(\S+)$", pre).group(1)
        nxt = linha[m.end():].split(" ", 1)[0]
        if len(prev) == 1 and prev.isupper():
            if re.match(r"^[A-Z]\.[;,]?$", nxt) or nxt.startswith("(ed") or nxt[:1].islower():
                continue
        return linha[:m.start()], linha[m.end():]
    return linha, ""


def ficha_info(chave):
    p = FICHAS / f"{chave}.md"
    if not p.exists():
        return None
    ls = p.read_text(encoding="utf8").splitlines()
    ref = aplicar_sigla(ls[0].lstrip("# ").strip())
    st = next((l for l in ls if l.startswith("- status")), "- status: ?")
    url = next((l for l in ls if l.startswith("- url")), "")
    return {"ref": ref, "status": st.split(":", 1)[1].strip(), "url": url}


def autores_label(chave, head):
    if chave in OVERRIDE_LABEL:
        return OVERRIDE_LABEL[chave]
    for _, novo, sig in SIGLAS:
        if head.startswith(sig + " – "):
            return sig
    segs = [s.strip() for s in head.split(";")]
    if not SURN.match(segs[0] + ", x"):  # institucional (sem 'SOBRENOME,')
        pass
    if SURN.match(head + " ") or SURN.match(segs[0] + " "):
        sob = []
        for s in segs:
            m = SURN.match(s + " ") or re.match(r"^((?:[A-ZÀ-ÝÇ][A-ZÀ-ÝÇ'’\- ]+)|(?:Mc[A-Z]+)),", s)
            if m:
                sob.append(m.group(1).strip().upper())
        etal = "et al" in head
        if etal or len(sob) >= 4:
            return sob[0] + " et al."
        return "; ".join(sob)
    return re.sub(r"\s+", " ", head).upper() if head.isupper() or not head[:1].islower() else head.upper()


def ano_ref(ref):
    t = re.sub(r"\(catálogo:\s*\d{4}\)", "", ref)
    t = re.sub(r"Acesso em:\s*\d{1,2}\s\w+\.\s\d{4}\.?", "", t)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"DOI:?\s*\S+", "", t)
    t = re.sub(r"\(?\b\d{4}\s*[-–]\s*\d{4}\)?", "", t)
    t = re.sub(r"\d+\.\s*º|n\.º\s*\d+/\d{4}", "", t)
    anos = re.findall(r"(?<![\d/-])(1[89]\d\d|20[0-3]\d)(?![\d])", t)
    return anos[-1] if anos else "s.d."


def formatar_ref(chave, info):
    """Referencia NBR 6023 em markdown (** = destaque tipografico do titulo)."""
    if chave in REF_OVERRIDE:
        s = REF_OVERRIDE[chave]
    else:
        s = info["ref"]
    s = re.sub(r"\s*\(catálogo:\s*\d{4}\)", "", s)
    s = re.sub(r"\s*Acesso aberto,\s*CC BY[-A-Z]*\s*\d\.\d\.?", "", s)
    s = re.sub(r"\s*\(acesso aberto\)", "", s)
    s = re.sub(r"\s*\(CC BY 4\.0\)", "", s)
    s = re.sub(r"\s*Licença:\s*CC BY-IGO\.", "", s)
    s = re.sub(r"\bDOI\s+(?=10\.)", "DOI: ", s)
    s = re.sub(r"\bDOI:\s*10", "DOI: 10", s)
    s = s.strip()
    # titulo em destaque
    if "*" in s:
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"**\1**", s)
    elif chave in BOLD_OVERRIDE:
        pass
    else:
        head, resto = cabeca(s)
        if head and not head.isupper() and "," not in head and not head.startswith("Mc"):
            head = head.upper()   # autor institucional em caixa mista
        m = re.search(r"([.?!])\s+([^.?!]*?),\s+(?=v\.\s|n\.\s\d|\d{1,2}\s\w+\.\s\d{4})", resto)
        if " In: " in " " + resto:
            # capitulo de livro: titulo do capitulo simples, titulo do livro em negrito
            s = head + ". " + re.sub(
                r"(In:\s.*?\((?:ed|eds|org|orgs|coord)\.?\)\.?\s+)([^.?!*]+?)([.?!](?:\s|$))",
                lambda mm: f"{mm.group(1)}**{mm.group(2).strip()}**{mm.group(3)}", resto, count=1)
        elif m and ":" not in m.group(2) and not resto.lstrip().startswith("In:"):
            # artigo de periodico: destaca o periodico
            jr = m.group(2).strip()
            if jr and len(jr) < 120:
                s = head + ". " + resto[:m.start(2)] + f"**{jr}**" + resto[m.end(2):]
        elif resto and not resto.lstrip().startswith(("In:", "[", "\"")) and not head.startswith("MOÇAMBIQUE"):
            mt = re.search(r"(?<=[.?!])\s", resto)
            tit, post = (resto[:mt.start()], resto[mt.end():]) if mt else (resto, "")
            if tit and len(tit) > 8:
                tit = tit.rstrip(".")
                pt = "" if tit[-1] in "?!" else "."
                s = f"{head}. **{tit}**{pt}" + (f" {post}" if post else "")
    s = re.sub(r"(?:DOI:?\s*)?<?https?://(?:dx\.)?doi\.org/(10\.[^\s<>]+?)>?\.?(?=\s|$)", r"DOI: \1.", s)
    s = re.sub(r"(?<![\[\w])s\.\s?d\.(?!\])", "[s.d.]", s)
    # online / DOI
    tem_doi = re.search(r"DOI:?\s*10\.", s) is not None
    if "Disponível em:" not in s and "Acesso em" in s:
        s = re.sub(r"\s*Acesso em:\s*\d{1,2}\s\w+\.\s\d{4}\.?", "", s)
    if "Disponível em:" in s:
        s = re.sub(r"Disponível em:\s*(https?://\S+?)(?=\.?(?:\s|$))", r"Disponível em: <\1>", s)
        if "Acesso em" not in s:
            s = s.rstrip() + f" Acesso em: {ACESSO}."
    elif not tem_doi:
        u = re.search(r"https://doi\.org/(10\.\S+?)(?=[\s;.]*(?:\s|;|$))", info["url"])
        if u:
            s = s.rstrip() + f" DOI: {u.group(1).rstrip('.')}."
        else:
            u = re.search(r"https?://[^\s;()]+", info["url"])
            if u:
                s = s.rstrip() + f" Disponível em: <{u.group(0).rstrip('.')}>. Acesso em: {ACESSO}."
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\.\s*\.", ".", s)
    s = s.rstrip()
    if s and s[-1] not in ".?!":
        s += "."
    return s


def processar_citacoes(md):
    chaves = []
    for m in re.finditer(r"\[(@[^\]]+)\]", md):
        for part in m.group(1).split(";"):
            k = re.match(r"\s*@([A-Za-z0-9_]+)", part)
            if k and k.group(1) not in chaves:
                chaves.append(k.group(1))
    infos, base = {}, {}
    nao_verif, sem_ficha = [], []
    for k in chaves:
        info = ficha_info(k)
        if info is None:
            sem_ficha.append(k)
            erro(f"chave citada sem ficha em fontes/fichas/: {k}")
            if k == "clubofmozambique_2026":   # fallback explicito a partir de fontes/ref_L4.csv
                r = next(x for x in lr(RAIZ / "fontes/ref_L4.csv") if x["chave"] == k)
                info = {"ref": f"CLUB OF MOZAMBIQUE (LUSA). {r['titulo']}. {r['veiculo']}. Disponível em: {r['url']}. "
                               f"Acesso em: {ACESSO}.", "status": f"SEM FICHA (ref_L4.csv: {r['status']})", "url": ""}
            else:
                info = {"ref": f"[{k}: ficha ausente]", "status": "SEM FICHA", "url": ""}
        infos[k] = info
        if not info["status"].startswith("VERIFICADO") or info["status"].startswith("SEM FICHA"):
            nao_verif.append((k, info["status"]))
        head, _ = cabeca(info["ref"])
        base[k] = (autores_label(k, head), ano_ref(info["ref"]))
    # colisao autor+ano -> sufixos a, b, ...
    grupos = {}
    for k, v in base.items():
        grupos.setdefault(v, []).append(k)
    anos = {}
    for v, ks in grupos.items():
        if len(ks) > 1:
            for i, k in enumerate(sorted(ks)):
                anos[k] = v[1] + "abcdefghij"[i]
        else:
            anos[ks[0]] = v[1]

    def cit(m):
        partes = []
        for part in m.group(1).split(";"):
            mm = re.match(r"\s*@([A-Za-z0-9_]+)\s*(?:,\s*(.*))?$", part.strip())
            if not mm:
                erro(f"citacao mal formada: {m.group(0)}")
                return m.group(0)
            k, loc = mm.group(1), mm.group(2)
            t = f"{base[k][0]}, {'[s.d.]' if anos[k] == 's.d.' else anos[k]}" + (f", {loc.strip()}" if loc else "")
            partes.append(t)
        return "(" + "; ".join(partes) + ")"

    md2 = re.sub(r"\[(@[^\]]+)\]", cit, md)
    # lista de referencias (alfabetica)
    itens = []
    for k in chaves:
        s = formatar_ref(k, infos[k])
        ano = anos[k]
        if ano != base[k][1] or ano == "s.d.":
            # reescreve ano com sufixo (a/b) no texto da referencia
            if ano != "s.d.":
                corpo_s, sep, cauda = s.partition(" Disponível em:")
                corpo_s = re.sub(rf"(?<![\d]){base[k][1]}(?![\d])(?!.*{base[k][1]})", ano, corpo_s, count=1)
                s = corpo_s + sep + cauda
        itens.append((base[k][0], s, k))
    itens.sort(key=lambda t: (re.sub(r"[^A-ZÀ-Ý0-9 ]", "", t[0].upper().replace("Ç", "C")), t[1]))
    lista = "\n\n".join(t[1] for t in itens)
    nao_citadas = sorted(p.stem for p in FICHAS.glob("*.md") if p.stem not in chaves)
    return md2, lista, nao_verif, chaves, sem_ficha, nao_citadas, base, anos


def _num_en(m):
    t = m.group(0)
    if "," in t and re.search(r"[.\u00a0\u202f]", t.split(",")[0]) is None:
        return t.replace(",", ".")                       # decimal: 39,2 -> 39.2
    inteiro, _, dec = t.partition(",")
    inteiro = re.sub(r"[.\u00a0\u202f]", ",", inteiro)   # milhares: 6.239 -> 6,239
    return inteiro + ("." + dec if dec else "")


def abstract_decimais(md):
    """Apenas na secao Abstract: formato numerico ingles (39,2% -> 39.2%; 6.239 -> 6,239)."""
    m = re.search(r"(^#\s+Abstract\s*\n)(.*?)(?=^#\s|\Z)", md, re.S | re.M)
    if not m:
        AVISOS.append("secao Abstract nao encontrada: decimais nao convertidos")
        return md
    rx = r"(?<![\d.,])(?:[1-9]\d{0,2}(?:[.\u00a0\u202f]\d{3})+(?:,\d+)?|\d+,\d+)(?![\d])"
    corpo = re.sub(rx, _num_en, m.group(2))
    return md[:m.start(2)] + corpo + md[m.end(2):]


# ------------------------------------------------------------------ 5. markdown -> blocos
def runs(texto):
    out = []
    for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", texto):
        if not tok:
            continue
        if tok.startswith("**"):
            out.append({"t": tok[2:-2], "b": True})
        elif tok.startswith("*") and len(tok) > 2:
            out.append({"t": tok[1:-1], "i": True})
        else:
            out.append({"t": tok})
    return out


def para_blocos(md, meta):
    from PIL import Image
    linhas = md.split("\n")
    blocos = [{"type": "title", "titulo": meta["titulo"], "autor": meta["autor"], "orcid": meta["orcid"]}]
    i, modo = 0, "corpo"
    while i < len(linhas):
        l = linhas[i]
        if not l.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,2})\s+(.*)$", l)
        if m:
            nivel, t = len(m.group(1)), m.group(2).strip()
            modo = "resumo" if t in ("Resumo", "Abstract") else ("ref" if t == "Referências" else "corpo")
            blocos.append({"type": f"h{nivel}", "runs": runs(t), "unnum": not re.match(r"^\d", t)})
            i += 1
            continue
        m = re.match(r"^!\[(.*)\]\(([^)]*)\)\s*$", l)
        if m:
            alt, path = m.group(1), m.group(2)
            cap, _, fonte = alt.partition(" Fonte:")
            p = (ART / path).resolve()
            if not p.exists():
                erro(f"figura ausente: {path}")
                w = h = 1
            else:
                w, h = Image.open(p).size
            blocos.append({"type": "fig", "path": str(p), "w": w, "h": h, "caption": runs(cap.strip()),
                           "source": runs("Fonte:" + fonte) if fonte else []})
            i += 1
            continue
        if re.match(r"^(Quadro|Tabela) \d+ – ", l):
            cap = l.strip()
            i += 1
            while not linhas[i].strip():
                i += 1
            tab = []
            while i < len(linhas) and linhas[i].startswith("|"):
                tab.append(linhas[i])
                i += 1
            while i < len(linhas) and not linhas[i].strip():
                i += 1
            fonte = ""
            if i < len(linhas) and (linhas[i].startswith("Fonte:")):
                fonte = linhas[i].strip()
                i += 1
            cel = lambda ln: [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", ln.strip().strip("|"))]
            cab = cel(tab[0])
            alin = ["r" if c.strip().endswith(":") else "l" for c in cel(tab[1])]
            corpo = [cel(x) for x in tab[2:]]
            blocos.append({"type": "table", "caption": runs(cap), "header": cab, "rows": corpo, "align": alin,
                           "source": runs(fonte) if fonte else []})
            continue
        # paragrafo (linhas contiguas)
        buf = [l]
        i += 1
        while i < len(linhas) and linhas[i].strip() and not re.match(r"^(#|!\[|\|)", linhas[i]):
            buf.append(linhas[i])
            i += 1
        t = " ".join(x.strip() for x in buf)
        if modo == "ref":
            blocos.append({"type": "ref", "runs": runs(t)})
        elif modo == "resumo":
            blocos.append({"type": "resumo", "runs": runs(t)})
        else:
            blocos.append({"type": "p", "runs": runs(t)})
    return blocos


def contar_palavras(blocos):
    n_corpo = n_total = 0
    em_corpo = False
    for b in blocos:
        if b["type"] in ("h1", "h2"):
            t = "".join(r["t"] for r in b["runs"])
            if b["type"] == "h1":
                em_corpo = bool(re.match(r"^\d", t))
                if t == "Referências":
                    em_corpo = False
        if b["type"] in ("p",) and em_corpo:
            n_corpo += len(re.findall(r"\S+", "".join(r["t"] for r in b["runs"])))
        if b["type"] in ("p", "resumo"):
            n_total += len(re.findall(r"\S+", "".join(r["t"] for r in b["runs"])))
    return n_corpo, n_total


# ------------------------------------------------------------------ HTML / PDF
def html_runs(rs):
    out = ""
    for r in rs:
        t = html.escape(r["t"])
        if r.get("b"):
            t = f"<strong>{t}</strong>"
        if r.get("i"):
            t = f"<em>{t}</em>"
        out += t
    return out


CSS_IMPRESSAO = """
@page { size: A4; margin: 3cm 2cm 2cm 3cm;
  @bottom-right { content: counter(page); font-family: var(--ard-sans); font-size: 8pt; color: var(--ard-text-3); }
  @bottom-left { content: "Pessini Sobreira · Zonas verdes de Maputo (1979–2026)"; font-family: var(--ard-sans); font-size: 8pt; color: var(--ard-text-3); } }
html { background: #fff; }
body { font-family: Georgia, var(--ard-serif); font-size: 11pt; line-height: 1.5; color: var(--ard-grafite-cl); margin: 0; background: transparent; }
h1.titulo { font-weight: 400; font-size: 20pt; line-height: 1.2; color: var(--ard-tinta); margin: 0 0 10pt; }
.autor { font-family: var(--ard-sans); font-size: 10pt; color: var(--ard-grafite); margin: 0; }
.orcid { font-family: var(--ard-sans); font-size: 8.5pt; color: var(--ard-text-3); margin: 0 0 18pt; padding-bottom: 10pt; border-bottom: 1px solid var(--ard-filete); }
h1 { font-weight: 400; font-size: 15pt; color: var(--ard-tinta); margin: 22pt 0 8pt; padding-bottom: 3pt; border-bottom: 1px solid var(--ard-filete); break-after: avoid; }
h2 { font-weight: 700; font-size: 11.5pt; color: var(--ard-tinta); margin: 16pt 0 5pt; break-after: avoid; }
p { text-align: justify; hyphens: auto; margin: 0 0 7pt; text-indent: 1.25cm; orphans: 3; widows: 3; }
p.resumo { text-indent: 0; line-height: 1.3; font-size: 10pt; }
p.ref { text-indent: 0; text-align: left; line-height: 1.25; font-size: 9.5pt; margin: 0 0 7pt; hyphens: manual; overflow-wrap: anywhere; }
figure { margin: 12pt 0 12pt; padding: 0; break-inside: avoid; text-align: center; }
figure img { max-width: 100%; max-height: 17.5cm; }
figcaption { font-family: var(--ard-sans); font-size: 8.5pt; color: var(--ard-grafite); text-align: left; line-height: 1.3; margin-top: 4pt; }
figcaption .fonte { color: var(--ard-text-3); display: block; }
.quadro { margin: 12pt 0; }
.quadro .cap { font-family: var(--ard-sans); font-size: 8.5pt; color: var(--ard-grafite); font-weight: 600; margin-bottom: 4pt; break-after: avoid; }
.quadro .fonte { font-family: var(--ard-sans); font-size: 8pt; color: var(--ard-text-3); margin-top: 3pt; line-height: 1.3; }
table { width: 100%; border-collapse: collapse; font-family: var(--ard-sans); font-size: 8pt; line-height: 1.3; }
th { text-align: left; color: var(--ard-primaria); font-weight: 600; border-bottom: 1.5px solid var(--ard-primaria); border-top: 0; padding: 3pt 4pt; vertical-align: bottom; }
td { padding: 3pt 4pt; border-bottom: 0.5pt solid var(--ard-filete-cl); vertical-align: top; }
th.r, td.r { text-align: right; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
"""


def montar_html(blocos, meta, saida):
    css_ard = (RAIZ / "site/assets/ardosia.css").read_text(encoding="utf8")
    css_ard = re.sub(r"@import[^;]+;", "", css_ard)
    # remove regras de body/h1.. do ardosia.css que conflitem: usamos apenas os tokens (:root)
    tokens = css_ard.split("[data-theme")[0]
    partes = []
    for b in blocos:
        t = b["type"]
        if t == "title":
            partes.append(f'<h1 class="titulo">{html.escape(b["titulo"])}</h1><p class="autor">{html.escape(b["autor"])}</p>'
                          f'<p class="orcid">ORCID: https://orcid.org/{b["orcid"]}</p>')
        elif t in ("h1", "h2"):
            partes.append(f"<{t}>{html_runs(b['runs'])}</{t}>")
        elif t == "p":
            partes.append(f"<p>{html_runs(b['runs'])}</p>")
        elif t == "resumo":
            partes.append(f'<p class="resumo">{html_runs(b["runs"])}</p>')
        elif t == "ref":
            partes.append(f'<p class="ref">{html_runs(b["runs"])}</p>')
        elif t == "fig":
            rel = Path(b["path"]).as_uri()
            src = f'<span class="fonte">{html_runs(b["source"])}</span>' if b["source"] else ""
            partes.append(f'<figure><img src="{rel}" alt=""><figcaption>{html_runs(b["caption"])}{src}</figcaption></figure>')
        elif t == "table":
            w = b.get("widths") or [1] * len(b["header"])
            tot = sum(w)
            cg = "".join(f'<col style="width:{100 * x / tot:.1f}%">' for x in w)
            th = "".join(f'<th class="{"r" if a == "r" else ""}">{html.escape(c)}</th>' for c, a in zip(b["header"], b["align"]))
            tb = "".join("<tr>" + "".join(f'<td class="{"r" if a == "r" else ""}">{html.escape(c)}</td>'
                                          for c, a in zip(r, b["align"])) + "</tr>" for r in b["rows"])
            src = f'<div class="fonte">{html_runs(b["source"])}</div>' if b["source"] else ""
            partes.append(f'<div class="quadro"><div class="cap">{html_runs(b["caption"])}</div>'
                          f'<table><colgroup>{cg}</colgroup><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>{src}</div>')
    doc = (f'<!doctype html><html lang="pt"><head><meta charset="utf-8"><title>{html.escape(meta["titulo"])}</title>'
           f'<style>{tokens}\n{CSS_IMPRESSAO}</style></head><body>{"".join(partes)}</body></html>')
    Path(saida).write_text(doc, encoding="utf8")


# ------------------------------------------------------------------ 7. exportacao web (site/artigo.html)
SITE = RAIZ / "site"
CITACAO_SITE = ("PESSINI SOBREIRA, Daniel. Zonas verdes de Maputo (1979–2026): agricultura urbana, uso do solo e "
                "planos urbanísticos. Zenodo, 2026. DOI: 10.5281/zenodo.24141821. "
                "Disponível em: https://doi.org/10.5281/zenodo.24141821.")
NAV_SITE = [("linha-do-tempo", "Linha do tempo"), ("painel", "Painel"), ("areas", "Áreas"), ("conversao", "Conversão"),
            ("planejado", "Planejado × ocorrido"), ("producao", "Produção"), ("planos", "Planos"),
            ("comparacao", "Cidades"), ("metodologia", "Metodologia")]


def _slug(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def _linkar(h):
    """Transforma URLs soltas (ja escapadas) em links; tira pontuacao final do href."""
    def sub(m):
        u = m.group(0)
        fim = ""
        while u and u[-1] in ".,;)":
            fim = u[-1] + fim
            u = u[:-1]
        return f'<a href="{u}" rel="noopener">{u}</a>{fim}'
    return re.sub(r"https?://[^\s<]+", sub, h)


def exportar_web(blocos, meta):
    from PIL import Image
    dest = SITE / "artigo"
    (dest / "img").mkdir(parents=True, exist_ok=True)
    if (ART / "artigo.pdf").exists():
        shutil.copy2(ART / "artigo.pdf", dest / "artigo.pdf")
    (dest / "artigo.docx").unlink(missing_ok=True)  # o site oferece só o PDF
    tam = lambda ext: f"{(dest / f'artigo.{ext}').stat().st_size / 1e6:.1f}".replace(".", ",") + " MB" if (dest / f"artigo.{ext}").exists() else ""

    partes, sumario = [], []
    aberta = False
    n_fig = 0
    lang_en = False

    def fecha():
        nonlocal aberta
        if aberta:
            partes.append("</section>")
            aberta = False

    for b in blocos:
        t = b["type"]
        if t == "title":
            continue
        if t in ("h1", "h2"):
            txt = "".join(r["t"] for r in b["runs"])
            sid = "s-" + _slug(txt)
            if t == "h1":
                fecha()
                lang_en = txt == "Abstract"
                partes.append(f'<section class="sec-art" id="{sid}"' + (' lang="en"' if lang_en else "") + ">")
                aberta = True
                partes.append(f'<h2>{html_runs(b["runs"])}</h2>')
                sumario.append((1, sid, txt))
            else:
                partes.append(f'<h3 id="{sid}">{html_runs(b["runs"])}</h3>')
                sumario.append((2, sid, txt))
        elif t == "p":
            partes.append(f'<p>{html_runs(b["runs"])}</p>')
        elif t == "resumo":
            partes.append(f'<p class="resumo">{html_runs(b["runs"])}</p>')
        elif t == "ref":
            partes.append(f'<p class="ref">{_linkar(html_runs(b["runs"]))}</p>')
        elif t == "fig":
            n_fig += 1
            nome = f"fig{n_fig}.webp"
            if Path(b["path"]).exists():
                im = Image.open(b["path"]).convert("RGB")
                if im.width > 1800:
                    im = im.resize((1800, round(im.height * 1800 / im.width)), Image.LANCZOS)
                im.save(dest / "img" / nome, "WEBP", quality=84, method=6)
                w, h = im.size
            else:
                w = h = 1
            legenda = "".join(r["t"] for r in b["caption"])
            alt = legenda.split(". ")[0][:200]
            src = f'<span class="fonte">{html_runs(b["source"])}</span>' if b["source"] else ""
            partes.append(f'<figure class="fig-art" id="fig-{n_fig}"><a href="artigo/img/{nome}" aria-label="Abrir a figura {n_fig} em tamanho inteiro">'
                          f'<img src="artigo/img/{nome}" width="{w}" height="{h}" loading="lazy" alt="{html.escape(alt)}"></a>'
                          f'<figcaption>{html_runs(b["caption"])}{src}</figcaption></figure>')
        elif t == "table":
            cap = "".join(r["t"] for r in b["caption"])
            tid = "q-" + _slug(cap.split(" – ")[0])
            th = "".join(f'<th scope="col"{" class=num" if a == "r" else ""}>{html.escape(c)}</th>' for c, a in zip(b["header"], b["align"]))
            tb = "".join("<tr>" + "".join((f'<th scope="row">{html.escape(c)}</th>' if k == 0 and a != "r" else
                                          f'<td{" class=num" if a == "r" else ""}>{html.escape(c)}</td>')
                                         for k, (c, a) in enumerate(zip(r, b["align"]))) + "</tr>" for r in b["rows"])
            src = f'<p class="fonte">{html_runs(b["source"])}</p>' if b["source"] else ""
            partes.append(f'<div class="quadro-art" id="{tid}"><p class="cap" id="{tid}-cap">{html_runs(b["caption"])}</p>'
                          f'<div class="tab-rolavel" tabindex="0" role="region" aria-labelledby="{tid}-cap">'
                          f'<table class="tab-art"><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>{src}</div>')
    fecha()

    toc, sub_aberta, item_aberto = [], False, False
    for nivel, sid, txt in sumario:
        li = f'<a href="#{sid}">{html.escape(txt)}</a>'
        if nivel == 1:
            if sub_aberta:
                toc.append("</ol>")
                sub_aberta = False
            if item_aberto:
                toc.append("</li>")
            toc.append(f"<li>{li}")
            item_aberto = True
        else:
            if not sub_aberta:
                toc.append('<ol class="sub">')
                sub_aberta = True
            toc.append(f"<li>{li}</li>")
    if sub_aberta:
        toc.append("</ol>")
    if item_aberto:
        toc.append("</li>")
    toc_html = "<ol>" + "".join(toc) + "</ol>"

    nav = "".join(f'<a href="index.html#{i}">{html.escape(n)}</a>' for i, n in NAV_SITE) + '<a href="artigo.html" aria-current="page">Artigo</a>'
    baixar = (f'<div class="baixar" role="group" aria-label="Baixar o artigo">'
              f'<a class="btn-baixar" href="artigo/artigo.pdf" download>Baixar PDF <span>{tam("pdf")}</span></a>'
              '</div>')
    # metadados de indexacao (Google, Google Scholar, Bing)
    base_url = "https://damnielps.github.io/zonas-verdes-maputo/"
    url_art, url_pdf = base_url + "artigo.html", base_url + "artigo/artigo.pdf"
    doi, orcid_url = "10.5281/zenodo.24141821", "https://orcid.org/" + meta["orcid"]
    txt_resumos = ["".join(r["t"] for r in b["runs"]) for b in blocos if b["type"] == "resumo"]
    resumo_pt = txt_resumos[0] if txt_resumos else ""
    palavras = ""
    for t in txt_resumos:
        if t.startswith("Palavras-chave:"):
            palavras = t.split(":", 1)[1].strip().rstrip(".")
            break
    resumo_pt = next((t for t in txt_resumos if not t.startswith(("Palavras-chave:", "Keywords:"))), "")
    resumo_pt = re.sub(r"\s+", " ", resumo_pt.replace("\u00a0", " ")).strip()
    desc = resumo_pt[:155].rsplit(" ", 1)[0].rstrip(",;:") + "…" if len(resumo_pt) > 155 else resumo_pt
    kw_tags = "".join(f'<meta name="citation_keywords" content="{html.escape(k.strip())}">\n'
                      for k in palavras.split(";") if k.strip())
    og_img = base_url + "img/painel/img_2026.webp"
    jsonld = {
        "@context": "https://schema.org", "@type": "ScholarlyArticle",
        "headline": meta["titulo"], "name": meta["titulo"],
        "author": {"@type": "Person", "name": "Daniel Pessini Sobreira", "sameAs": orcid_url},
        "datePublished": "2026-11-11", "inLanguage": "pt",
        "identifier": "https://doi.org/" + doi, "url": url_art,
        "isPartOf": {"@type": "WebSite", "name": "Zonas verdes de Maputo", "url": base_url},
        "license": "https://opensource.org/licenses/MIT",
        "abstract": resumo_pt,
        "keywords": [k.strip() for k in palavras.split(";") if k.strip()],
    }
    jsonld_txt = json.dumps(jsonld, ensure_ascii=False, indent=2).replace("</", "<\\/")
    e = lambda x: html.escape(x, quote=True)
    cabeca_seo = f"""<link rel="canonical" href="{url_art}">
<meta name="robots" content="index, follow">
<meta name="author" content="Daniel Pessini Sobreira">
<meta property="og:type" content="article">
<meta property="og:title" content="{e(meta["titulo"])}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url_art}">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Zonas verdes de Maputo">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="citation_title" content="{e(meta["titulo"])}">
<meta name="citation_author" content="Pessini Sobreira, Daniel">
<meta name="citation_publication_date" content="2026/11/11">
<meta name="citation_language" content="pt">
<meta name="citation_doi" content="{doi}">
<meta name="citation_pdf_url" content="{url_pdf}">
<meta name="citation_abstract_html_url" content="{url_art}">
{kw_tags}<meta name="citation_publisher" content="Zenodo">
<script type="application/ld+json">
{jsonld_txt}
</script>
"""
    doc = f"""<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(meta["titulo"])} (artigo)</title>
<meta name="description" content="{e(desc)}">
{cabeca_seo}<link rel="stylesheet" href="assets/ardosia.css">
<link rel="stylesheet" href="assets/site.css">
<link rel="stylesheet" href="assets/correcoes.css">
<link rel="stylesheet" href="assets/artigo.css">
</head>
<body class="pagina-artigo">
<a class="skip" href="#texto">Ir para o texto</a>
<header class="topo">
  <div class="wrap">
    <a class="topo__marca" href="index.html">Zonas verdes de Maputo</a>
    <nav aria-label="Seções">{nav}</nav>
    <button type="button" class="btn-tema" id="btnTema" aria-label="Alternar tema claro e escuro">Tema</button>
  </div>
</header>
<main class="wrap artigo-layout">
  <aside class="artigo-lado" aria-label="Sumário e downloads">
    <div class="caixa-baixar">
      <p class="rot">Baixar</p>
      {baixar}
    </div>
    <details class="sumario" open>
      <summary>Sumário</summary>
      <nav aria-label="Sumário do artigo">{toc_html}</nav>
    </details>
  </aside>
  <article class="artigo" id="texto" lang="pt-BR">
    <header class="artigo-cab">
      <p class="ard-kicker">Artigo científico</p>
      <h1>{html.escape(meta["titulo"])}</h1>
      <p class="autor">{html.escape(meta["autor"])}</p>
      <p class="orcid">ORCID: <a href="https://orcid.org/{html.escape(meta["orcid"])}" rel="noopener">https://orcid.org/{html.escape(meta["orcid"])}</a></p>
      {baixar}
    </header>
    {"".join(partes)}
    <section class="sec-art citar" id="como-citar">
      <h2>Como citar</h2>
      <p class="cit">{html.escape(CITACAO_SITE)}</p>
      <p class="nota">Este texto é a versão web do artigo, gerada a partir do mesmo arquivo-fonte do PDF; os números vêm de <code>dados/proc/resultados.json</code>. A <a href="index.html#metodologia">seção de metodologia do site</a> descreve como os números foram produzidos.</p>
      {baixar}
    </section>
  </article>
</main>
<footer class="rodape"><div class="wrap"><p>{html.escape(CITACAO_SITE)}</p></div></footer>
<script src="assets/artigo.js"></script>
</body>
</html>
"""
    (SITE / "artigo.html").write_text(doc, encoding="utf8")
    print(f"web: site/artigo.html ({len(doc) // 1024} KB), {n_fig} figuras em site/artigo/img/")


LARGURAS = {  # pesos relativos de colunas por tabela (identificadas pelo no de colunas e 1o cabecalho)
    "Ano": [8, 24, 20, 17, 31],
    "Época": [8, 31, 17, 34, 10],
    "Cidade (país)": [14, 30, 25, 31],
    "Perímetro": [30, 9, 8.5, 8.5, 8.5, 8.5, 8.5, 8.5],
}


def main():
    FIGART.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    fig4()
    fig5()
    mapa_img = imagens_planos()
    for f in ("dados/fig/class/mapas_classes.png", "dados/fig/planos/sobreposicao_1985_2008.png",
              "dados/fig/artigo/fig4_envelopes.png", "dados/fig/artigo/fig5_producao.png"):
        if not (RAIZ / f).exists():
            erro(f"figura ausente: {f}")

    bruto = (ART / "artigo.md").read_text(encoding="utf8")
    m = re.match(r"^---\n(.*?)\n---\n", bruto, re.S)
    if not m:
        erro("cabecalho YAML nao encontrado")
        return
    cab = m.group(1)
    meta = {k: re.search(rf'^{k}:\s*"(.*)"\s*$', cab, re.M).group(1) for k in ("titulo", "autor", "orcid")}
    md = bruto[m.end():]

    vals = json.load(open(ART / "valores.json", encoding="utf8"))
    blocos_gerados = {
        "QUADRO_1_PLANOS": quadro1(), "QUADRO_2_EPOCAS": quadro2(), "QUADRO_3_CASOS": quadro3(),
        "TABELA_1_ENVELOPES": vals["TABELA_1_ENVELOPES"].strip(),
    }
    # quadros gerados entram antes: as chaves citadas nas linhas "Fonte:" contam como citadas
    for k, v in blocos_gerados.items():
        md = md.replace("{{" + k + "}}", v)
    md, lista, nao_verif, chaves, sem_ficha, nao_citadas, base, anos = processar_citacoes(md)
    md = md.replace("{{REFERENCIAS}}", lista)
    md = re.sub(r"\{\{(\w+)\}\}", lambda mm: vals[mm.group(1)] if mm.group(1) in vals and mm.group(1) != "TABELA_1_ENVELOPES" else mm.group(0), md)
    pend = sorted(set(re.findall(r"\{\{[^}]*\}\}", md)))
    if pend:
        erro(f"placeholders nao resolvidos: {pend}")
    for a, b in mapa_img.items():
        md = md.replace(a, b)
    md = abstract_decimais(md)
    md = nbsp(md)
    (ART / "artigo_final.md").write_text(md, encoding="utf8")

    (BUILD / "citacoes_nao_verificadas.txt").write_text(
        "Chaves citadas em artigo.md cuja ficha NAO esta VERIFICADO (status da ficha):\n"
        + "\n".join(f"{k}\t{s}" for k, s in sorted(nao_verif)) + "\n", encoding="utf8")

    blocos = para_blocos(md, meta)
    for b in blocos:
        if b["type"] == "table":
            b["widths"] = LARGURAS.get(b["header"][0], [1] * len(b["header"]))
    n_corpo, n_total = contar_palavras(blocos)
    n_fig = sum(b["type"] == "fig" for b in blocos)
    n_tab = sum(b["type"] == "table" for b in blocos)
    json.dump({"blocos": blocos, "meta": meta}, open(BUILD / "blocos.json", "w", encoding="utf8"), ensure_ascii=False)

    # docx
    r = subprocess.run(["node", str(BUILD / "build_docx.js"), str(BUILD / "blocos.json"), str(ART / "artigo.docx")],
                       capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[:2000])
    if r.returncode != 0:
        erro("falha ao gerar docx")

    # html + pdf
    montar_html(blocos, meta, BUILD / "artigo.html")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if SEM_PDF:
        pass
    elif Path(chrome).exists():
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={ART / 'artigo.pdf'}", (BUILD / "artigo.html").as_uri()],
                       timeout=240, capture_output=True)
        print("pdf", (ART / "artigo.pdf").stat().st_size // 1024, "KB" if (ART / "artigo.pdf").exists() else "")
    else:
        AVISOS.append("Chrome nao encontrado: PDF nao gerado")

    try:
        exportar_web(blocos, meta)
    except Exception as e:  # noqa: BLE001
        erro(f"exportacao web falhou: {e!r}")

    print("\n=== RELATORIO ===")
    print(f"palavras do corpo (secoes 1-8, sem referencias, quadros, legendas): {n_corpo}")
    print(f"palavras incl. resumo e abstract: {n_total}")
    print(f"figuras: {n_fig} | tabelas/quadros: {n_tab} | chaves citadas: {len(chaves)}")
    print(f"chaves sem ficha: {sem_ficha}")
    print(f"citadas nao VERIFICADO ({len(nao_verif)}): {[k for k, _ in nao_verif]}")
    print(f"fichas nao citadas (informativo, nao entram na lista): {len(nao_citadas)}")
    print("avisos:", AVISOS)
    if ERROS:
        print("ERROS:", *ERROS, sep="\n  ")
        if not TOLERAR:
            sys.exit(1)


if __name__ == "__main__":
    main()
