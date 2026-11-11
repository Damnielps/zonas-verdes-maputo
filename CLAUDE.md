# Zonas verdes de Maputo — regras do projeto

Artigo científico (DOCX + PDF, ABNT) e site estático interativo sobre a evolução das zonas verdes
(cintura agrícola periurbana) de Maputo, 1979–2026. Plano completo: `docs/PLANO.md`.
Notas dos levantamentos iniciais: `fontes/levantamentos/*.md`.

## Integridade científica (inegociável)
- Nenhuma referência, número, data, artigo de lei ou citação entra no artigo ou no site sem fonte
  aberta e conferida nesta pesquisa. Nada de memória. Cada fonte tem linha em
  `fontes/referencias.csv` (coluna `status`: VERIFICADO / PARCIAL / NAO_VERIFICADO) e, se usada no
  texto, ficha em `fontes/fichas/<chave>.md` com página/tabela de cada número e citação.
- Citações literais curtas (≤ 15 palavras), entre aspas, com página.
- Todo número de séries vai para `fontes/series_producao.csv` com fonte, página, ano e definição
  espacial. Definições divergentes não se somam nem se comparam sem nota.
- Números de resultados do artigo e do site são lidos de `dados/proc/resultados.json`; nunca
  digitados à mão.
- Não contornar verificação TLS (`curl -k` proibido). Se um site falhar, registrar e usar espelho.

## Dados
- `dados/raw/` nunca é versionado. Downloads em subpasta própria por fonte.
- Scripts numerados em `scripts/NN_nome.py`, rodam com `.venv/bin/python -I`; `scripts/rodar_cadeia.sh`
  roda tudo do zero.
- CRS de trabalho: EPSG:32736 (UTM 36S), 30 m. Área: bbox 32.40–32.75 E, −26.10 a −25.75 S.

## Identidade visual (Sistema Ardósia)
- `site/assets/ardosia.css` e `scripts/ardosia_palette.py` são cópias verbatim da skill; não editar.
- Nenhum hex literal em CSS novo: usar as variáveis `--ard-*`.
- Figuras matplotlib: `from ardosia_palette import apply_ardosia; apply_ardosia()`.
- Sem emoji. Serifa no texto, sans em rótulos e eixos. Máximo seis cores categóricas.

## Direitos de imagem
- Imagens de terceiros (planos históricos, mapas antigos) ficam fora da licença MIT. Cada uma tem
  linha em `CREDITOS.md` (fonte, autor, data, detentor, situação de direitos) e legenda com autor,
  data, instituição e fonte de onde foi obtida.

## Orquestração
- Sessão principal (Opus) decide e redige; implementação e leitura em Sonnet; tarefas mecânicas em
  Haiku; auditoria em Opus com contexto novo. Agentes em `.claude/agents/`. Registro em
  `docs/ORQUESTRACAO.md`.
- Dois agentes nunca escrevem no mesmo arquivo.
