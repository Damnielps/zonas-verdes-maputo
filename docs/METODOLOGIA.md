# Metodologia

## 1. Área e grade
Retângulo 32,40–32,75 E × 26,10–25,75 S (Cidade de Maputo, margem da Matola no vale do Infulene, sul de
Marracuene), grade de 30 m em EPSG:32736 definida em `scripts/comum.py`. Unidades de agregação: 7
distritos municipais e 64 bairros (HDX COD-AB v02, 2025), bairros da Matola que tocam o vale.
KaNyaka (Inhaca) fica fora do retângulo e da análise.

## 2. Épocas
Anos censitários 1980, 1997, 2007, 2017 e intercensitários quinquenais até 2026:
1979*, 1985, 1990, 1995, 1997, 2000, 2005, 2007, 2010, 2015, 2017, 2020, 2025, 2026.
*1980 é representado por Landsat MSS da estação seca de 1979 (não há cena útil de 1980).
Substituições de 1985 e 2010 ficam registradas em `docs/qa/composicoes.md`.

Fonte principal: composições geomedianas anuais (GeoMAD) do Digital Earth Africa, que reduzem nuvem
e ruído sazonal e trazem medidas de variabilidade intra-anual (SMAD, EMAD, BCMAD). A variabilidade
é útil aqui: hortas irrigadas de baixada têm ciclos curtos e sucessivos, logo alta variabilidade
espectral ao longo do ano, ao contrário de telhados, mangal ou capim.

## 3. Legenda
| código | classe | definição operacional |
|---|---|---|
| 1 | Construído | telhados, pavimento, solo compactado de assentamento; inclui assentamento informal denso |
| 2 | Agricultura de baixada (zonas verdes) | canteiros hortícolas irrigados e machambas em solos hidromórficos de vales e baixadas costeiras (machongo) |
| 3 | Agricultura de sequeiro e mosaico | machambas de milho/mandioca em interflúvios arenosos, pousios curtos, mosaico com quintais |
| 4 | Vegetação arbórea e arbustiva | mata, cajueiral, eucaliptal, matagal; inclui mangal (subclasse 41 quando separável) |
| 5 | Herbácea e zonas húmidas não cultivadas | caniçal, capim, pântano salino, pousio longo |
| 6 | Água | rios, lagoas, estuário, mar dentro do retângulo |
| 7 | Solo exposto e areia | dunas, praias, terraplenagem, areeiros, obras |

Na análise de conflito, "zonas verdes" = classe 2; "agricultura" = classes 2 + 3. A classe 2 é o
objeto central; a 3 é reportada à parte por ser a de maior confusão (com 5 e com o construído
disperso).

## 4. Classificação
- Atributos por época: 6 bandas de reflectância, NDVI, NDBI, MNDWI, BSI, SMAD, EMAD, BCMAD; constantes:
  altitude, declive e TPI (Copernicus DEM 30 m). As baixadas cultivadas ficam abaixo de ~10 m e em TPI
  negativo, o que separa a classe 2 da 3.
- Modelo: Random Forest (500 árvores, `class_weight="balanced_subsample"`), um por época, mesma legenda.
- Treino:
  1. Época âncora 2020: píxeis estáveis onde concordam WorldCover 2021, IO LULC 2020 e GLAD 2020
     (construído, árvore, água, herbácea, solo exposto); para as classes agrícolas, polígonos OSM
     `landuse=farmland/allotments` e digitalização visual sobre a composição 2020 e imagem de alta
     resolução de referência (Esri World Imagery) de canteiros no Infulene, Mahotas, Costa do Sol,
     Albazine e KaTembe.
  2. Propagação temporal: um ponto de treino de 2020 é reutilizado numa época anterior somente se a
     distância espectral (ângulo espectral sobre bandas normalizadas) entre as duas épocas for menor
     que o limiar calibrado no percentil 20 dos pontos de controle estáveis; caso contrário é descartado
     para essa época.
  3. Para épocas anteriores a 2000, acréscimo de pontos digitalizados sobre os mapas LUCO 1982 e 1991
     (Henriques e Correia, 2023) quando coerentes com a imagem.
- 1979 (MSS, 4 bandas, 60 m): legenda reduzida (construído, vegetação/agricultura, água, solo exposto)
  mais separação de agricultura de baixada por altitude/TPI e NDVI de estação seca; tratada como
  estimativa de ordem de grandeza.
- Pós-processamento: filtro de moda 3×3; regra temporal leve (construído não reverte a agrícola entre
  épocas consecutivas, salvo evidência de demolição com confirmação visual).

## 5. Validação
- Amostra estratificada por classe mapeada (≥ 50 pontos por classe) em 2000, 2010 e 2020, rotulada por
  interpretação visual independente do treino; matriz de confusão, exatidão global, do produtor e do
  usuário, e áreas ajustadas com intervalos de 95% (Olofsson et al., 2014).
- Concordância externa: construído × GHSL BUILT-S (fração ≥ 0,2) 1975–2025 e WSF Evolution; agricultura
  × GLAD cropland 2000–2020 e ESA CCI; comparação com LUCO 1982, 1991, 2001.
- Incerteza reportada por época; épocas 1979 e 1985 com ressalva explícita.

## 6. Métricas
- Área por classe × época × distrito/bairro (ha), com área ajustada quando houver amostra.
- Matrizes de transição entre épocas consecutivas; taxa anual de conversão agricultura → construído
  (ha/ano e % da área agrícola inicial).
- Perda acumulada de zonas verdes desde 1979/1985 por bairro; mapa de "frentes de conversão".
- "Planejado × ocorrido": sobreposição do zoneamento do Plano de Estrutura de 1985 e do PEUMM 2008
  (quando georreferenciáveis) com a classificação.
- Proxy de salinização/abandono: tendência de NDVI de estação seca nas baixadas costeiras (Costa do
  Sol, Mahotas) 1990–2025.

## 7. Séries de produção
Cada número com fonte, página e definição espacial em `fontes/series_producao.csv`. Não se
interpola nem se soma entre definições distintas. A área agrícola classificada serve de árbitro entre
as definições de área das fontes (171 ha, 1 300 ha, 5 230 ha, 47 000 ha).

## Referência
OLOFSSON, P. et al. Good practices for estimating area and assessing accuracy of land change.
*Remote Sensing of Environment*, v. 148, p. 42–57, 2014. (conferir DOI na lista final)

## 8. Revisão após a validação cega (2026-11-11)
A amostra cega de 280 pontos (2020) deu exatidão global de 0,73 (bbox). Construído: usuário 0,88, produtor 0,87.
Zonas verdes (classe 2): usuário 0,33, produtor 0,16; confusão principal com vegetação não cultivada (45).
Decisão: a métrica central passa a ser a fração construída dentro de perímetros independentes da classificação
agrícola (baixada por relevo; zonas verdes do plano de 1985; agropecuária do PEUMM 2008) — `scripts/07b_envelopes.py`,
`dados/proc/areas/envelopes.csv`. A série da classe 2 fica como indicativa, com intervalo da área ajustada.
A transição 2→45 não é interpretada como abandono, pois não se distingue de erro de classificação.
