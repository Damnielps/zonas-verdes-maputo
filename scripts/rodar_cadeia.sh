#!/usr/bin/env bash
# Roda o pipeline do zero, na ordem.
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/00_ambiente.sh
# Ordem: 00-06, 06b (pos-processamento temporal), 07, 07b (envelopes), 07c (comparacao das tres estimativas; depende de 07b),
# 08-10, 11 (exatidao; so age se existir dados/proc/validacao/rotulos_2020.csv; 2.a execucao com --sem-baixa gera a sensibilidade) e 12.
for s in scripts/0[0-6]_*.py scripts/06b_consistencia.py scripts/07_areas_transicoes.py scripts/07b_envelopes.py scripts/07c_envelopes_comparacao.py scripts/0[8-9]_*.py scripts/10_*.py scripts/11_avaliacao_exatidao.py; do
  echo "=== $s"
  .venv/bin/python -I "$s"
done
echo "=== scripts/11_avaliacao_exatidao.py --sem-baixa"
.venv/bin/python -I scripts/11_avaliacao_exatidao.py --sem-baixa
echo "=== scripts/20_valores_artigo.py (antes do 12: o 12 confere os KPIs contra artigo/valores.json)"
.venv/bin/python -I scripts/20_valores_artigo.py
echo "=== scripts/12_resultados.py"
.venv/bin/python -I scripts/12_resultados.py
# 05_rotulos.py, 06_classificar.py, 07_areas_transicoes.py e 08_qa_classificacao.py rodam pelo laco acima
# (glob scripts/[0-9][0-9]_*.py, ordem numerica); nao repetir aqui para nao executar duas vezes.
echo "=== scripts/21_artigo.py"
.venv/bin/python -I scripts/21_artigo.py --tolerar
