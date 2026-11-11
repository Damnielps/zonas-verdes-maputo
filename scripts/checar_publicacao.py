#!/usr/bin/env python3
"""Verifica site/ antes da publicação. Só biblioteca padrão. Sai com código 1 se houver problema."""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SITE = RAIZ / "site"
LIMITE_ARQ = 15 * 1024 * 1024
LIMITE_SITE = 60 * 1024 * 1024
CAMINHOS = ("/Users/", "/private/", "file://")
EXT_TEXTO = {".html", ".js", ".mjs", ".css", ".json", ".geojson", ".csv", ".txt", ".xml", ".svg", ".md"}
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")

erros = []
if not SITE.is_dir():
    print("ERRO: site/ não existe")
    sys.exit(1)

arquivos = [p for p in SITE.rglob("*") if p.is_file()]
total = sum(p.stat().st_size for p in arquivos)

for p in arquivos:
    rel = p.relative_to(RAIZ)
    if p.name == ".DS_Store":
        erros.append(f".DS_Store: {rel}")
    if p.suffix == ".map":
        erros.append(f"sourcemap: {rel}")
    if p.stat().st_size > LIMITE_ARQ:
        erros.append(f"arquivo > 15 MB ({p.stat().st_size / 1e6:.1f} MB): {rel}")
    if p.suffix.lower() in EXT_TEXTO:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for c in CAMINHOS:
            if c in txt:
                erros.append(f'caminho local "{c}" em {rel}')

css = SITE / "assets" / "site.css"
if css.is_file():
    txt = css.read_text(encoding="utf-8", errors="ignore")
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    achados = sorted(set(HEX.findall(txt)))
    if achados:
        erros.append(f"hex literal em assets/site.css: {', '.join(achados[:10])}")
else:
    erros.append("site/assets/site.css ausente")

# créditos: cada imagem de planos (exceto *_mini.webp) precisa de linha em CREDITOS.md
cred = RAIZ / "CREDITOS.md"
texto_cred = cred.read_text(encoding="utf-8") if cred.is_file() else ""
if not texto_cred:
    erros.append("CREDITOS.md ausente ou vazio")
planos = SITE / "img" / "planos"
sem_credito = []
if planos.is_dir():
    for p in sorted(planos.iterdir()):
        if not p.is_file() or p.name.endswith("_mini.webp") or p.name == ".DS_Store":
            continue
        base = p.stem
        if not any(l.lstrip().startswith("|") and base in l for l in texto_cred.splitlines()):
            sem_credito.append(p.name)
for n in sem_credito:
    erros.append(f"imagem sem linha em CREDITOS.md: img/planos/{n}")

if total > LIMITE_SITE:
    erros.append(f"site/ com {total / 1e6:.1f} MB (limite 60 MB)")

print(f"site/: {len(arquivos)} arquivos, {total / 1e6:.1f} MB")
if erros:
    print(f"FALHOU: {len(erros)} problema(s)")
    for e in erros:
        print("  -", e)
    sys.exit(1)
print("OK: nenhuma pendência")
