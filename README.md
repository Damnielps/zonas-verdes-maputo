# Zonas verdes de Maputo (1979–2026): agricultura urbana, uso do solo e planos urbanísticos

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24141821.svg)](https://doi.org/10.5281/zenodo.24141821)

Site: https://damnielps.github.io/zonas-verdes-maputo/ · Repositório: https://github.com/Damnielps/zonas-verdes-maputo

Artigo científico e site interativo sobre a evolução da cintura agrícola periurbana de Maputo (as "zonas verdes" dos vales do Infulene e de Mahotas e da planície costeira de KaMavota). O projeto combina a história institucional e dos planos urbanísticos de Lourenço Marques e Maputo com um painel de 14 épocas de imagens Landsat (1979–2026), classificado por Random Forest, validado por amostra cega e cruzado com perímetros independentes da classificação (plano de 1985, PEUMM 2008, relevo de baixada). Todo o código, os dados agregados e o site estão neste repositório.

## Entregas

- Artigo: `artigo/artigo.docx` (DOCX, ABNT) e `artigo/artigo.pdf`; texto-fonte em `artigo/artigo_final.md`.
- Site estático interativo: `site/` (abrir `site/index.html` por um servidor estático local; publicação em GitHub Pages, ver "Publicar").
- Dados abertos: `site/dados/` (áreas por classe, época, distrito e bairro; transições; perda por bairro; séries de produção; conflitos; planos; limites e planos de 1985 e 2008 em GeoJSON; `resultados.json`).

## Principais resultados

Números lidos de `artigo/valores.json`.

- A fração construída dentro das zonas verdes permanentes do plano de 1985 passou de 4,6% (1985) para 39,2% (2026).
- Na área agropecuária do PEUMM 2008, a fração construída foi de 2,0% (1985) para 7,5% (2010) e 16,0% (2026).
- Nas baixadas definidas por relevo, a fração construída subiu de 3,5% (1985) para 14,9% (2026), com aceleração depois de 2010 (7,7% em 2010).
- A área construída da cidade (parte continental) passou de 6.239 ha em 1985 para 12.479 ha em 2026.
- Validação cega (2020, n = 280): o construído é bem mapeado (exatidão do usuário 0,88), mas a agricultura de baixada não (exatidão do usuário 0,33), o que levou à mudança da métrica central (ver "Métodos").

## Métodos em uma página

Detalhes em `docs/METODOLOGIA.md`.

- Área: retângulo 32,40–32,75 E × 26,10–25,75 S, grade de 30 m em EPSG:32736; unidades de agregação: 7 distritos municipais e 64 bairros (HDX COD-AB).
- Épocas: 14 (1979, 1985, 1990, 1995, 1997, 2000, 2005, 2007, 2010, 2015, 2017, 2020, 2025, 2026), a partir das composições geomedianas anuais do Digital Earth Africa e de cenas Landsat em substituição onde necessário (1979 em Landsat MSS; 1985 e 2010 com cenas TM, registradas em `docs/qa/composicoes.md`).
- Legenda de 7 classes (construído, agricultura de baixada, agricultura de sequeiro/mosaico, vegetação arbórea, herbácea e zonas húmidas, água, solo exposto).
- Classificação: Random Forest (500 árvores) por época, com bandas, índices (NDVI, NDBI, MNDWI, BSI), medidas de variabilidade intra-anual e relevo (Copernicus DEM, declive, TPI). Treino ancorado em 2020 (concordância entre WorldCover, IO LULC e GLAD, mais OSM e digitalização visual) e propagado no tempo por distância espectral; 1979 é tratado como ordem de grandeza.
- Validação: amostra estratificada e cega, avaliada pelas boas práticas de Olofsson et al. (2014); concordância externa com GHSL, GLAD, ESA CCI e LUCO.
- Revisão após a validação cega (seção 8 da metodologia): como a classe de agricultura de baixada separa-se mal da vegetação não cultivada a 30 m, a métrica central passou a ser a fração construída em perímetros independentes da classificação agrícola (`scripts/07b_envelopes.py`, `dados/proc/areas/envelopes.csv`). A série da classe 2 é indicativa, com intervalo da área ajustada, e a transição agricultura para vegetação não é interpretada como abandono.
- Séries de produção: cada número com fonte, página e definição espacial em `fontes/series_producao.csv`; definições divergentes não são somadas nem comparadas sem nota.

## Reproduzir

Requer `uv` e Python 3.14. Os downloads somam cerca de 1–2 GB (Landsat/GeoMAD, DEM, produtos de cobertura do solo), e `dados/raw/` não é versionado.

```bash
bash scripts/00_ambiente.sh        # cria .venv com uv e instala as dependências
bash scripts/rodar_cadeia.sh       # roda o pipeline 00–12 do zero, na ordem
.venv/bin/python -I scripts/20_valores_artigo.py   # lê dados/proc/resultados.json e gera artigo/valores.json
.venv/bin/python -I scripts/21_artigo.py           # monta o artigo (DOCX/PDF)
```

Os intermediários reprodutíveis (`dados/proc/comp/`, `dados/proc/class/`, `dados/proc/class_final/`, `dados/proc/rotulos/` e `artigo/build/node_modules/`) estão no `.gitignore` e são regenerados pela cadeia. `dados/proc/validacao/.chave/` fica versionado, pois é necessário para reproduzir a avaliação de exatidão. A rotulagem cega externa (`dados/proc/validacao/rotulos_2020.csv`) é o insumo de `scripts/11_avaliacao_exatidao.py`.

## Limitações

- A agricultura de baixada (classe 2) tem exatidão do usuário de 0,33 e do produtor de 0,16 na amostra cega de 2020, com confusão principal com vegetação não cultivada; as áreas dessa classe são indicativas.
- 1979 (Landsat MSS, 60 m, legenda reduzida) e 1985 têm ressalva explícita; 1985 e 2010 usam cenas substitutas (2010 em abril, fora da estação seca).
- A validação cobre 2020; as demais épocas dependem de concordância externa.
- Pendências de conferência (`docs/PENDENCIAS.md`): fichas de fontes a criar ou completar, número e data da resolução de aprovação do PEUMM, data de criação do Cinturão (GZV) divergente entre fontes, fontes só parcialmente abertas (citadas apenas em teses gerais), ficha do Landsat 4-5 TM, e semântica do WSF Evolution não confirmada (excluído da validação).
- Séries de produtores e de produção usam definições espaciais distintas e não são comparáveis entre si sem as notas.

## Publicar

A ser feito pelo autor, depois de conferir `docs/PENDENCIAS.md` e `CREDITOS.md`:

1. Criar o repositório remoto no GitHub, definir o nome e fazer o push.
2. Em Settings > Pages, escolher "GitHub Actions" e rodar o workflow "Publicar" (Actions > Publicar > Run workflow). O gatilho é apenas `workflow_dispatch`; antes de publicar, o job `verificar` roda `scripts/checar_publicacao.py` (caminhos locais, sourcemaps, arquivos grandes, cores hexadecimais no CSS, créditos de imagens).
3. Para o DOI, ativar a integração GitHub–Zenodo no repositório e criar uma release; o Zenodo lê `.zenodo.json` e `CITATION.cff`. Depois de cunhado, adicionar o DOI a `CITATION.cff` e a este README.

## Como citar

PESSINI SOBREIRA, Daniel. *Zonas verdes de Maputo (1979–2026): agricultura urbana, uso do solo e planos urbanísticos*. Zenodo, 2026. DOI: 10.5281/zenodo.24141821. Disponível em: https://doi.org/10.5281/zenodo.24141821. Ver `CITATION.cff`.

## Licença e créditos

O código está sob licença MIT (`LICENSE`). Imagens de terceiros (mapas e planos históricos) e dados de terceiros não são cobertos pela MIT e mantêm os direitos dos titulares; fontes, autores, detentores e situação de direitos estão em `CREDITOS.md`.

## Orquestração

O projeto foi conduzido com orquestração entre modelos (sessão principal decide e redige; implementação e leitura em modelos intermediários; auditoria com contexto novo). O registro de cada delegação, saídas e conferência está em `docs/ORQUESTRACAO.md`.
