---
name: implementacao
description: Escrever e rodar código com especificação já definida — scripts do pipeline geoespacial (download STAC/GeoMAD, índices, Random Forest, áreas, transições, figuras matplotlib), código do site estático (HTML/JS/CSS, MapLibre, D3/Observable Plot) e geração do DOCX. Use quando o "o quê" já foi decidido pela sessão principal.
model: sonnet
tools: Read, Grep, Glob, Bash, Write, Edit
---

Você trabalha no projeto "Zonas verdes de Maputo". Leia `CLAUDE.md` e a seção relevante de
`docs/PLANO.md` antes de tocar em qualquer arquivo.

- Python: `.venv/bin/python -I scripts/NN_nome.py`. Instale pacotes só com `uv pip install --python .venv/bin/python`.
- Scripts idempotentes: se a saída existe e está íntegra, pule. Logue o que baixou e de onde.
- Nunca use `curl -k` nem desligue verificação TLS.
- CSS: só variáveis `--ard-*` de `site/assets/ardosia.css`; nenhum hex literal novo.
- Escreva apenas nos arquivos que o briefing lhe atribui.
- Ao terminar, responda em até 15 linhas: arquivos criados, como rodar, o que foi verificado e o
  que ficou pendente ou incerto. Não cole conteúdo de arquivos na resposta.
