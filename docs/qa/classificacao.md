# QA da classificação (30 m, EPSG:32736)

Gerado por `scripts/08_qa_classificacao.py` a partir de `05_rotulos.py`, `06_classificar.py` e `07_areas_transicoes.py`. Números das tabelas lidos de `dados/proc/class/oob.json`, `dados/proc/rotulos/rotulos_resumo.json` e `dados/proc/areas/`.

## 1. Rótulos de treino

### 1.1 Âncora 2020 e regras

- Construído: WorldCover 2021 = 50 E IO LULC 2020 = Built E GHSL-BUILT-S 2020 ≥ 2000 m² por célula de 100 m.
- Arbórea/arbustiva: WC 10 E IO Trees; mangal: WC 95 sozinho (subclasse 41 marcada na coluna `sub`).
- Herbácea/húmida: (WC 30 ou 90) E IO (Rangeland ou Flooded vegetation), fora de polígonos OSM agrícolas.
- Água: WC 80 E IO Water. Solo exposto: WC 60 E IO Bare.
- Agricultura: polígonos OSM `farmland`, `allotments`, `greenhouse_horticulture` (`orchard` não usado) OU (WC 40 E IO Crops), com GHSL 2020 ≤ 500.
- Divisão 2 × 3: classe 2 se altitude < 15 m E TPI < 0, ou dentro de 100 m de polígono OSM `wetland`; caso contrário classe 3.
- Píxeis que cumprem mais de uma regra foram descartados (610 px); máscaras erodidas em 1 píxel (3×3); classes com menos de 300 px após erosão ficaram sem erosão (classes [7]: solo exposto, 1 093 px antes da erosão e 70 depois).
- Amostragem aleatória estratificada: reserva de até 6000 pontos por classe (`pool_2020.parquet`); a âncora `treino_2020` usa até 1500 por classe. Pontos disponíveis na âncora: {'1': 1500, '2': 1500, '3': 636, '4': 1500, '5': 1500, '6': 1500, '7': 1093}.

**Escolha 2 × 3 (limiares realmente usados).** Cerca de 98% dos píxeis dos polígonos OSM agrícolas estão abaixo de 15 m (mediana ≈ 5 m, p90 ≈ 12 m; ver `dados/fig/class/rotulos_2v3.png`), de modo que o critério altimétrico praticamente não discrimina nos vales do Infulene e Mahotas: quem separa é o TPI < 0, que envia ≈ 27% dos píxeis OSM (bordas e microrelevo mais alto da baixada) para a classe 3. O buffer de 100 m de zonas húmidas OSM acrescenta apenas ≈ 1% dos píxeis. A divisão é, portanto, um proxy topográfico e não uma observação de uso; a classe 3 tem apenas 636 píxeis de âncora e é a de menor confiabilidade. Suavizar o TPI (5×5, 9×9) não alterou a proporção (73,7% e 74,9% em classe 2).

### 1.2 Propagação temporal

Ângulo espectral entre o vetor 2020 e o da época t em (verde, vermelho, NIR, SWIR1, SWIR2; 1979: verde, vermelho, NIR), calculado sobre pseudo-invariantes: 1000 pontos de água profunda (WC80 E IO água, erodida 3 px) e 1000 pontos do núcleo construído antigo (GHSL 1975 ≥ 5000 e GHSL 2020 ≥ 5000 em KaMpfumo, erodido). Consistência com GHSL(t) (ano GHSL mais próximo): construído exige ≥ 2000; agricultura, árvore e herbácea exigem < 500.

**Desvio documentado do limiar.** O percentil 20 literal dos invariantes deixava as classes água (ângulos muito mais dispersos que no núcleo construído) e, em épocas afastadas de 2020, todas as classes agrícolas com poucos pontos (água 6–25 pontos; classe 3 < 100). A regra adotada: limiar da água calculado sobre os invariantes de água e o das demais classes sobre os do núcleo construído, no mesmo percentil; começa no p20 e sobe para p50 e p80 apenas enquanto alguma classe retiver menos de min(150; 50% do pool) pontos. Percentil e limiares por época:

| epoca | bandas | percentil | limiar_terra_rad | limiar_agua_rad | p20_terra | p20_agua |
|---|---|---|---|---|---|---|
| 1979 | green,red,nir | 50 | 0.0995 | 0.128 | 0.0471 | 0.0684 |
| 1985 | green,red,nir,swir1,swir2 | 50 | 0.141 | 0.277 | 0.082 | 0.205 |
| 1990 | green,red,nir,swir1,swir2 | 50 | 0.0634 | 0.245 | 0.0392 | 0.177 |
| 1995 | green,red,nir,swir1,swir2 | 50 | 0.1 | 0.219 | 0.0688 | 0.157 |
| 1997 | green,red,nir,swir1,swir2 | 50 | 0.0698 | 0.248 | 0.0413 | 0.18 |
| 2000 | green,red,nir,swir1,swir2 | 80 | 0.0808 | 0.294 | 0.0261 | 0.16 |
| 2005 | green,red,nir,swir1,swir2 | 80 | 0.0715 | 0.299 | 0.0277 | 0.161 |
| 2007 | green,red,nir,swir1,swir2 | 80 | 0.0712 | 0.272 | 0.0251 | 0.144 |
| 2010 | green,red,nir,swir1,swir2 | 80 | 0.0803 | 0.295 | 0.0303 | 0.143 |
| 2015 | green,red,nir,swir1,swir2 | 80 | 0.0401 | 0.256 | 0.0139 | 0.101 |
| 2017 | green,red,nir,swir1,swir2 | 80 | 0.0322 | 0.21 | 0.0116 | 0.0738 |
| 2025 | green,red,nir,swir1,swir2 | 80 | 0.0387 | 0.263 | 0.0146 | 0.0838 |
| 2026 | green,red,nir,swir1,swir2 | 80 | 0.0518 | 0.357 | 0.0214 | 0.159 |

Limite de pontos propagados: 1 500 por classe e época (reserva 6 000). Pontos LUCO: até 1 000 por classe, apenas se coerentes espectralmente na época-alvo (construído NDVI<0,40 e NDWI<0,20; agricultura NDWI<0,15 e NDVI>−0,05; arbórea NDVI>0,15 e NDWI<0,15; herbácea NDWI<0,20; água NDWI>−0,05; solo exposto NDVI<0,25 e NDWI<0,10; NDWI=(verde−NIR)/(verde+NIR)).

### 1.3 Crosswalk LUCO → classes do estudo

Nomenclatura: `ULU_Maputo_Nomenclatura_PT.pdf` (Henriques, Correia e Rolo, 2023). "excluido" = classe ambígua (baixa densidade, equipamentos, vias, vazio urbano, emergente), não usada. LUCO 1982 serve a 1979 e 1985; 1991 a 1990, 1995 e 1997; 2001 a 2000 e 2005. Áreas de todos os anos em `dados/proc/rotulos/luco_crosswalk.csv`.

| codigo_luco | descricao | classe_estudo | n_pol_2001 | area_ha_2001 |
|---|---|---|---|---|
| 1.0.1 | Multifuncional: totalmente infra-estruturado | 1 | 45 | 37.6 |
| 2.1.1 | Residencial infra-estruturada, alta densidade | 1 | 71 | 48.4 |
| 2.1.2 | Residencial infra-estruturada, media densidade | 1 | 260 | 268.4 |
| 2.1.3 | baixa densidade: quintais e arvores, ambiguo | excluido | 133 | 128.3 |
| 2.2.1 | Residencial parcialmente infra-estruturada, alta densidade | 1 | 108 | 65.4 |
| 2.2.2 | Residencial parcialmente infra-estruturada, media densidade | 1 | 1504 | 1,254.6 |
| 2.2.3 | baixa densidade (<2100 hab/km2), ambiguo | excluido | 155 | 504.5 |
| 2.3.1 | Residencial nao infra-estruturada, alta densidade | 1 | 37 | 161.9 |
| 2.3.2 | Residencial nao infra-estruturada, media densidade | 1 | 308 | 2,003.0 |
| 2.3.3 | baixa densidade, ambiguo | excluido | 39 | 877.9 |
| 2.4.1 | emergente intercalado com vazios, ambiguo | excluido | 19 | 43.1 |
| 2.4.2 | emergente intercalado com matos, ambiguo | excluido | 33 | 577.2 |
| 3.0.1 | Industria, armazenagem e reparacao | 1 | 305 | 300.4 |
| 3.0.2 | Comercio e servicos | 1 | 195 | 122.9 |
| 3.0.3 | Agricultura e pecuaria: talhoes horticolas/quintas -> 2 ou 3 pela regra dem/TPI | agri | 162 | 2,798.8 |
| 3.0.4 | Extraccao de areia e sal -> solo exposto | 7 | 5 | 30.2 |
| 4.0.1 | Saude | 1 | 41 | 49.2 |
| 4.0.2 | Educacao: recintos escolares com arvores, ambiguo | excluido | 183 | 216.3 |
| 4.0.3 | Outros equipamentos (cemiterio, lixeira, desporto), ambiguo | excluido | 359 | 334.7 |
| 4.0.4 | Vias e areas de apoio, ambiguo (poligonos grandes) | excluido | 10 | 913.0 |
| 4.0.5 | Infra-estruturas e transportes (aeroporto, porto), ambiguo | excluido | 91 | 1,083.2 |
| 4.0.6 | Administracao publica, recintos extensos, ambiguo | excluido | 123 | 789.7 |
| 4.0.7 | Outros servicos publicos, residual | excluido | 46 | 12.8 |
| 5.0.1 | Vazio urbano e ruina, ambiguo | excluido | 349 | 166.1 |
| 6.0.1 | Mangal -> arborea (subclasse 41) | 4 | 4 | 549.2 |
| 6.0.2 | Outras areas alagadas -> herbacea/zona humida | 5 | 14 | 1,570.1 |
| 6.0.3 | Cursos e planos de agua | 6 | 15 | 105.8 |
| 7.0.1 | Mato (vegetacao arbustiva natural) -> arborea/arbustiva | 4 | 77 | 1,106.2 |
| 7.0.2 | Area arborizada, parques e jardins -> arborea | 4 | 74 | 143.1 |
| 7.0.3 | Praia | 7 | 3 | 15.8 |
| 7.0.4 | Outras areas naturais, sem vegetacao | 7 | 9 | 13.2 |

### 1.4 Contagem de pontos de treino por época, classe e origem

| epoca | 1/ancora2020 | 1/luco1982 | 1/luco1991 | 1/luco2001 | 1/prop2020 | 2/ancora2020 | 2/luco1982 | 2/luco1991 | 2/luco2001 | 2/prop2020 | 3/ancora2020 | 3/luco1982 | 3/luco1991 | 3/luco2001 | 3/prop2020 | 4/ancora2020 | 4/luco1982 | 4/luco1991 | 4/luco2001 | 4/prop2020 | 5/ancora2020 | 5/luco1982 | 5/luco1991 | 5/luco2001 | 5/prop2020 | 6/ancora2020 | 6/luco1991 | 6/luco2001 | 6/prop2020 | 7/ancora2020 | 7/luco1982 | 7/luco1991 | 7/luco2001 | 7/prop2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1979 | 0 | 1000 | 0 | 0 | 1500 | 0 | 1000 | 0 | 0 | 290 | 0 | 1000 | 0 | 0 | 160 | 0 | 1000 | 0 | 0 | 454 | 0 | 1000 | 0 | 0 | 1500 | 0 | 0 | 0 | 1500 | 0 | 283 | 0 | 0 | 348 |
| 1985 | 0 | 1000 | 0 | 0 | 1463 | 0 | 1000 | 0 | 0 | 1319 | 0 | 1000 | 0 | 0 | 222 | 0 | 1000 | 0 | 0 | 1500 | 0 | 1000 | 0 | 0 | 1500 | 0 | 0 | 0 | 1500 | 0 | 153 | 0 | 0 | 274 |
| 1990 | 0 | 0 | 1000 | 0 | 1089 | 0 | 0 | 1000 | 0 | 498 | 0 | 0 | 1000 | 0 | 208 | 0 | 0 | 1000 | 0 | 159 | 0 | 0 | 1000 | 0 | 1030 | 0 | 0 | 0 | 1500 | 0 | 0 | 113 | 0 | 299 |
| 1995 | 0 | 0 | 1000 | 0 | 1500 | 0 | 0 | 1000 | 0 | 1500 | 0 | 0 | 1000 | 0 | 504 | 0 | 0 | 1000 | 0 | 419 | 0 | 0 | 1000 | 0 | 1500 | 0 | 8 | 0 | 1500 | 0 | 0 | 117 | 0 | 426 |
| 1997 | 0 | 0 | 1000 | 0 | 1023 | 0 | 0 | 1000 | 0 | 788 | 0 | 0 | 1000 | 0 | 213 | 0 | 0 | 1000 | 0 | 471 | 0 | 0 | 1000 | 0 | 1500 | 0 | 8 | 0 | 1500 | 0 | 0 | 90 | 0 | 290 |
| 2000 | 0 | 0 | 0 | 1000 | 1500 | 0 | 0 | 0 | 1000 | 968 | 0 | 0 | 0 | 1000 | 228 | 0 | 0 | 0 | 1000 | 1500 | 0 | 0 | 0 | 1000 | 1361 | 0 | 0 | 8 | 1500 | 0 | 0 | 0 | 46 | 325 |
| 2005 | 0 | 0 | 0 | 1000 | 1500 | 0 | 0 | 0 | 1000 | 1145 | 0 | 0 | 0 | 1000 | 295 | 0 | 0 | 0 | 1000 | 217 | 0 | 0 | 0 | 1000 | 1500 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 59 | 455 |
| 2007 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 1471 | 0 | 0 | 0 | 0 | 301 | 0 | 0 | 0 | 0 | 1078 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 538 |
| 2010 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 1324 | 0 | 0 | 0 | 0 | 200 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 565 |
| 2015 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 1432 | 0 | 0 | 0 | 0 | 220 | 0 | 0 | 0 | 0 | 1147 | 0 | 0 | 0 | 0 | 1476 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 532 |
| 2017 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 973 | 0 | 0 | 0 | 0 | 114 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 1180 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 576 |
| 2020 | 1500 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 636 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 1093 | 0 | 0 | 0 | 0 |
| 2025 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 856 | 0 | 0 | 0 | 0 | 147 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 587 |
| 2026 | 0 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 478 | 0 | 0 | 0 | 0 | 113 | 0 | 0 | 0 | 0 | 1186 | 0 | 0 | 0 | 0 | 1157 | 0 | 0 | 0 | 1500 | 0 | 0 | 0 | 0 | 566 |

Contagens efetivamente usadas no treino (após remover pontos sem feature): ver 2.1.

## 2. Modelos

Random Forest, 500 árvores, `class_weight="balanced_subsample"`, `random_state=42`. Atributos: bandas disponíveis, NDVI/NDBI/MNDWI/BSI, SMAD/EMAD/BCMAD onde existem, altitude, declive, TPI. Épocas sem MAD (1985, 2010, 2026) e 1979 (só verde, vermelho, NIR, NDVI) têm modelos próprios sem imputação. Filtro de moda 3×3 (empate favorece o píxel central). Regra temporal: construído em t−1 e t+1 não pode ser agrícola (2/3) em t.

### 2.1 Exatidão fora-do-saco (OOB) e F1 por classe

| epoca | n | acc_oob | F1_1 | F1_2 | F1_3 | F1_4 | F1_5 | F1_6 | F1_7 |
|---|---|---|---|---|---|---|---|---|---|
| 1979 | 11035 | 0.909 | 0.788 |  | 0.925 |  |  | 0.997 | 0.965 |
| 1985 | 12931 | 0.903 | 0.912 | 0.922 | 0.801 | 0.909 | 0.852 | 0.999 | 0.947 |
| 1990 | 9887 | 0.937 | 0.933 | 0.938 | 0.888 | 0.91 | 0.932 | 0.999 | 0.966 |
| 1995 | 12474 | 0.904 | 0.878 | 0.94 | 0.844 | 0.847 | 0.892 | 1 | 0.959 |
| 1997 | 10872 | 0.919 | 0.933 | 0.931 | 0.827 | 0.896 | 0.901 | 0.999 | 0.98 |
| 2000 | 12436 | 0.914 | 0.911 | 0.934 | 0.846 | 0.901 | 0.884 | 0.999 | 0.976 |
| 2005 | 11671 | 0.923 | 0.912 | 0.958 | 0.86 | 0.854 | 0.916 | 0.999 | 0.967 |
| 2007 | 7888 | 0.961 | 0.973 | 0.974 | 0.905 | 0.955 | 0.905 | 0.999 | 0.99 |
| 2010 | 8089 | 0.957 | 0.979 | 0.957 | 0.859 | 0.959 | 0.892 | 1 | 0.989 |
| 2015 | 7807 | 0.973 | 0.983 | 0.975 | 0.932 | 0.971 | 0.933 | 0.999 | 0.991 |
| 2017 | 7343 | 0.978 | 0.988 | 0.974 | 0.933 | 0.979 | 0.941 | 0.999 | 0.983 |
| 2020 | 8851 | 0.966 | 0.985 | 0.967 | 0.933 | 0.972 | 0.911 | 1 | 0.99 |
| 2025 | 7590 | 0.975 | 0.99 | 0.97 | 0.865 | 0.974 | 0.947 | 1 | 0.987 |
| 2026 | 6500 | 0.973 | 0.988 | 0.928 | 0.835 | 0.981 | 0.936 | 0.999 | 0.984 |

**Leitura.** O OOB e o CV medem a reprodução dos rótulos (derivados de WorldCover, IO LULC, GHSL, OSM, LUCO), não a exatidão contra verdade de campo; pontos vizinhos são autocorrelacionados, logo o OOB é otimista. A validação independente de 2000, 2010 e 2020 por interpretação visual (METODOLOGIA, seção 5) não faz parte deste passo.

### 2.2 Validação cruzada espacial (5 dobras, blocos de 3 km)

| epoca | blocos | acc | F1_1 | F1_2 | F1_3 | F1_4 | F1_5 | F1_6 | F1_7 |
|---|---|---|---|---|---|---|---|---|---|
| 2000 | 149 | 0.829 | 0.846 | 0.849 | 0.671 | 0.806 | 0.775 | 0.998 | 0.894 |
| 2010 | 152 | 0.91 | 0.968 | 0.883 | 0.607 | 0.925 | 0.782 | 1 | 0.979 |
| 2020 | 156 | 0.931 | 0.982 | 0.922 | 0.805 | 0.961 | 0.834 | 0.994 | 0.978 |

### 2.3 Importância das variáveis (top 5) e atributos por época

| epoca | atributos | top5 |
|---|---|---|
| 1979 | green, red, nir, ndvi, dem, declive, tpi | dem 0.25, ndvi 0.249, declive 0.144, nir 0.129, red 0.105 |
| 1985 | blue, green, red, nir, swir1, swir2, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | dem 0.189, ndvi 0.126, mndwi 0.103, swir2 0.093, tpi 0.086 |
| 1990 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | dem 0.205, ndvi 0.113, nir 0.086, mndwi 0.075, tpi 0.074 |
| 1995 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | dem 0.175, ndvi 0.122, mndwi 0.089, nir 0.089, tpi 0.084 |
| 1997 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | dem 0.169, ndvi 0.12, mndwi 0.109, tpi 0.077, nir 0.072 |
| 2000 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | dem 0.136, ndvi 0.121, mndwi 0.108, green 0.072, swir2 0.072 |
| 2005 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | dem 0.146, ndvi 0.116, mndwi 0.099, swir2 0.076, swir1 0.072 |
| 2007 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | blue 0.117, dem 0.111, green 0.108, tpi 0.103, ndvi 0.096 |
| 2010 | blue, green, red, nir, swir1, swir2, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | tpi 0.106, green 0.105, blue 0.105, ndvi 0.095, dem 0.094 |
| 2015 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | tpi 0.115, ndvi 0.112, red 0.095, dem 0.087, mndwi 0.086 |
| 2017 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | green 0.127, tpi 0.109, ndvi 0.106, red 0.1, dem 0.089 |
| 2020 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | green 0.118, ndvi 0.112, mndwi 0.104, tpi 0.096, dem 0.086 |
| 2025 | blue, green, red, nir, swir1, swir2, smad, emad, bcmad, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | ndvi 0.115, green 0.107, tpi 0.096, mndwi 0.089, red 0.083 |
| 2026 | blue, green, red, nir, swir1, swir2, ndvi, ndbi, mndwi, bsi, dem, declive, tpi | ndvi 0.113, tpi 0.111, green 0.099, mndwi 0.098, dem 0.094 |

Regra temporal: píxeis corrigidos (construído→agrícola→construído) por época intermediária: {'1985': 13005, '1990': 4181, '1995': 7113, '1997': 6849, '2000': 4192, '2005': 6773, '2007': 134, '2010': 457, '2015': 138, '2017': 267, '2020': 168, '2025': 420}. Reversões construído→outra classe→construído mantidas (a regra não alisa além do especificado): {'1985': 20875, '1990': 7475, '1995': 7362, '1997': 24695, '2000': 18763, '2005': 16162, '2007': 11283, '2010': 31956, '2015': 9131, '2017': 31934, '2020': 8403, '2025': 11836}.

**1979.** legenda reduzida (1,2,3,6,7; 4 e 5 ausentes; 3 = vegetacao/agricultura fora da baixada, inclui arborea e herbacea); 2 = classe 'vegetacao' com regra baixada (alt<15.0 m e TPI<0 ou buffer wetland OSM 100 m), fora de mangal WC95 e NDVI>=0.382 (p25 do NDVI dos pontos 2 propagados).

## 3. Áreas (ha)

Área terrestre da Cidade de Maputo = união dos distritos municipais exceto KaNyaka (HDX COD-AB), 29 861 ha; bbox = grade inteira (inclui mar, Matola, Marracuene).

### Cidade

| epoca | c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
|---|---|---|---|---|---|---|---|---|
| 1979 | 0 | 8,498.0 | 2,050.0 | 16,764.0 | 0 | 0 | 747.0 | 1,803.0 |
| 1985 | 13.0 | 6,899.0 | 1,990.0 | 2,475.0 | 11,467.0 | 5,851.0 | 704.0 | 462.0 |
| 1990 | 0 | 8,284.0 | 2,515.0 | 5,274.0 | 2,843.0 | 9,482.0 | 842.0 | 620.0 |
| 1995 | 0 | 8,252.0 | 2,593.0 | 3,240.0 | 4,675.0 | 9,976.0 | 836.0 | 289.0 |
| 1997 | 0 | 7,138.0 | 2,557.0 | 2,432.0 | 5,410.0 | 11,275.0 | 824.0 | 226.0 |
| 2000 | 0 | 8,546.0 | 1,701.0 | 1,755.0 | 7,488.0 | 9,285.0 | 801.0 | 285.0 |
| 2005 | 0 | 9,375.0 | 1,566.0 | 2,450.0 | 2,710.0 | 12,653.0 | 766.0 | 341.0 |
| 2007 | 0 | 11,377.0 | 1,630.0 | 262.0 | 3,678.0 | 11,750.0 | 716.0 | 449.0 |
| 2010 | 1.0 | 10,608.0 | 1,531.0 | 304.0 | 5,802.0 | 10,347.0 | 802.0 | 466.0 |
| 2015 | 0 | 11,717.0 | 1,342.0 | 316.0 | 2,703.0 | 12,494.0 | 767.0 | 523.0 |
| 2017 | 0 | 11,137.0 | 1,128.0 | 198.0 | 3,916.0 | 12,347.0 | 749.0 | 386.0 |
| 2020 | 0 | 11,562.0 | 1,502.0 | 256.0 | 3,398.0 | 11,752.0 | 708.0 | 683.0 |
| 2025 | 0 | 10,988.0 | 1,257.0 | 163.0 | 3,544.0 | 12,726.0 | 731.0 | 453.0 |
| 2026 | 0 | 10,952.0 | 1,227.0 | 152.0 | 5,033.0 | 11,249.0 | 767.0 | 481.0 |

### Bbox (c0 = sem dado; 2020 tem lacuna de 3 667 ha no mar, sem efeito na terra)

| epoca | c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
|---|---|---|---|---|---|---|---|---|
| 1979 | 0 | 18,600.0 | 6,440.0 | 67,729.0 | 0 | 0 | 40,388.0 | 3,885.0 |
| 1985 | 47.0 | 14,494.0 | 6,339.0 | 10,666.0 | 49,446.0 | 14,558.0 | 40,126.0 | 1,365.0 |
| 1990 | 12.0 | 19,836.0 | 6,818.0 | 16,224.0 | 17,717.0 | 34,297.0 | 40,706.0 | 1,431.0 |
| 1995 | 0 | 22,229.0 | 6,396.0 | 13,731.0 | 17,975.0 | 34,892.0 | 41,000.0 | 818.0 |
| 1997 | 9.0 | 16,541.0 | 6,630.0 | 6,553.0 | 24,203.0 | 41,474.0 | 40,922.0 | 708.0 |
| 2000 | 0 | 19,846.0 | 4,423.0 | 5,545.0 | 30,943.0 | 34,658.0 | 40,877.0 | 749.0 |
| 2005 | 0 | 27,251.0 | 3,207.0 | 6,714.0 | 9,408.0 | 48,840.0 | 40,877.0 | 746.0 |
| 2007 | 0 | 32,993.0 | 3,474.0 | 1,381.0 | 10,285.0 | 47,265.0 | 40,649.0 | 994.0 |
| 2010 | 50.0 | 32,431.0 | 3,470.0 | 1,070.0 | 16,060.0 | 42,260.0 | 40,871.0 | 828.0 |
| 2015 | 0 | 39,951.0 | 2,612.0 | 965.0 | 8,462.0 | 43,313.0 | 40,874.0 | 864.0 |
| 2017 | 4.0 | 37,827.0 | 2,344.0 | 464.0 | 11,596.0 | 43,252.0 | 40,860.0 | 695.0 |
| 2020 | 3,667.0 | 42,358.0 | 3,490.0 | 1,730.0 | 10,202.0 | 37,732.0 | 36,472.0 | 1,391.0 |
| 2025 | 0 | 41,214.0 | 2,694.0 | 352.0 | 11,121.0 | 39,939.0 | 40,770.0 | 951.0 |
| 2026 | 0 | 40,400.0 | 2,596.0 | 268.0 | 15,324.0 | 36,563.0 | 40,950.0 | 940.0 |

### Conversão agricultura → construído (consecutivos, cidade)

| t0 | t1 | area_agri_inicial_ha | ha_agri_para_construido | ha_agri_ano | pct_agri_inicial | area_zv_inicial_ha | ha_zv_para_construido | ha_zv_ano | pct_zv_inicial |
|---|---|---|---|---|---|---|---|---|---|
| 1979 | 1985 | 18,813.2 | 1,124.4 | 187.4 | 6.0 | 2,049.6 | 28.6 | 4.8 | 1.4 |
| 1985 | 1990 | 4,464.8 | 297.5 | 59.5 | 6.7 | 1,990.1 | 78.8 | 15.8 | 4.0 |
| 1990 | 1995 | 7,788.4 | 514.6 | 102.9 | 6.6 | 2,514.6 | 59.6 | 11.9 | 2.4 |
| 1995 | 1997 | 5,832.7 | 47.9 | 23.9 | 0.82 | 2,592.6 | 10.8 | 5.4 | 0.42 |
| 1997 | 2000 | 4,988.6 | 350.3 | 116.8 | 7.0 | 2,556.7 | 72.8 | 24.3 | 2.9 |
| 2000 | 2005 | 3,456.4 | 322.4 | 64.5 | 9.3 | 1,701.3 | 45.7 | 9.1 | 2.7 |
| 2005 | 2007 | 4,015.4 | 909.6 | 454.8 | 22.6 | 1,565.6 | 37.5 | 18.8 | 2.4 |
| 2007 | 2010 | 1,891.6 | 11.8 | 3.9 | 0.62 | 1,629.8 | 11.5 | 3.8 | 0.71 |
| 2010 | 2015 | 1,834.6 | 88.1 | 17.6 | 4.8 | 1,530.9 | 60.6 | 12.1 | 4.0 |
| 2015 | 2017 | 1,657.6 | 13.4 | 6.7 | 0.81 | 1,341.6 | 12.0 | 6.0 | 0.89 |
| 2017 | 2020 | 1,326.0 | 11.0 | 3.7 | 0.83 | 1,127.6 | 9.9 | 3.3 | 0.88 |
| 2020 | 2025 | 1,758.2 | 35.7 | 7.2 | 2.0 | 1,502.5 | 29.4 | 5.9 | 2.0 |
| 2025 | 2026 | 1,419.5 | 8.0 | 8.0 | 0.56 | 1,256.9 | 8.0 | 8.0 | 0.64 |

Os fluxos de agricultura→construído por intervalo são pequenos frente à troca entre classes 2, 3 e 5 (ruído de classificação), ver seção 5. Em 1979→1985 a classe 3 (1979) inclui toda a vegetação: usar só a classe 2.

## 4. Concordância externa

### 4.1 Construído × GHSL-BUILT-S (≥ 2000 m² por célula de 100 m; ano GHSL mais próximo; bbox)

| epoca | ghsl_ano | construido_ha | ghsl_ge2000_ha | pct_nosso_com_ghsl | pct_ghsl_no_nosso | f1 |
|---|---|---|---|---|---|---|
| 1979 | 1980 | 18,599.8 | 16,166.6 | 47.9 | 55.2 | 51.3 |
| 1985 | 1985 | 14,493.9 | 17,647.1 | 67.3 | 55.3 | 60.7 |
| 1990 | 1990 | 19,836.1 | 19,664.1 | 66.0 | 66.6 | 66.3 |
| 1995 | 1995 | 22,228.7 | 22,282.9 | 65.7 | 65.5 | 65.6 |
| 1997 | 1995 | 16,541.2 | 22,282.9 | 77.5 | 57.5 | 66.0 |
| 2000 | 2000 | 19,845.5 | 25,401.4 | 79.5 | 62.1 | 69.7 |
| 2005 | 2005 | 27,251.0 | 28,239.7 | 75.3 | 72.7 | 74.0 |
| 2007 | 2005 | 32,993.2 | 28,239.7 | 73.8 | 86.3 | 79.6 |
| 2010 | 2010 | 32,431.0 | 34,042.2 | 82.5 | 78.6 | 80.5 |
| 2015 | 2015 | 39,951.1 | 38,054.3 | 82.9 | 87.1 | 85.0 |
| 2017 | 2015 | 37,826.5 | 38,054.3 | 85.0 | 84.5 | 84.8 |
| 2020 | 2020 | 42,357.6 | 38,890.3 | 82.8 | 90.2 | 86.3 |
| 2025 | 2025 | 41,213.5 | 39,306.5 | 82.9 | 86.9 | 84.8 |
| 2026 | 2025 | 40,400.3 | 39,306.5 | 82.4 | 84.7 | 83.6 |

### 4.2 Construído × WSF Evolution (valor = ano de detecção; semântica PARCIAL, ver legendas.json)

| epoca | construido_ha | wsf_ha | pct_nosso_com_wsf | pct_wsf_no_nosso |
|---|---|---|---|---|
| 1985 | 14,493.9 | 20,288.7 | 74.0 | 52.9 |
| 1990 | 19,836.1 | 22,492.6 | 72.5 | 64.0 |
| 1995 | 22,228.7 | 26,411.8 | 74.1 | 62.3 |
| 1997 | 16,541.2 | 27,674.9 | 85.2 | 50.9 |
| 2000 | 19,845.5 | 29,686.6 | 85.9 | 57.5 |
| 2005 | 27,251.0 | 34,576.4 | 84.0 | 66.2 |
| 2007 | 32,993.2 | 35,989.3 | 86.8 | 79.5 |
| 2010 | 32,431.0 | 39,453.2 | 91.5 | 75.2 |
| 2015 | 39,951.1 | 42,948.8 | 90.0 | 83.7 |

### 4.3 Agricultura (2+3) × GLAD (tabela crua, legenda NÃO verificada; sem rótulos)

Valores GLAD com sobreposição ≥ 2% da nossa agricultura. Sem nomes de classe: não interpretar como cropland.

**2000** (nossa agricultura 2+3: 9,968 ha)

| valor_glad | area_glad_ha | sobreposicao_ha | pct_da_nossa_agri | pct_do_valor_que_e_nossa_agri |
|---|---|---|---|---|
| 24 | 26,598.2 | 4,468.8 | 44.8 | 16.8 |
| 250 | 27,663.8 | 2,968.5 | 29.8 | 10.7 |
| 23 | 11,422.8 | 855.8 | 8.6 | 7.5 |
| 124 | 3,839.6 | 605.9 | 6.1 | 15.8 |
| 22 | 8,467.7 | 544.0 | 5.5 | 6.4 |
| 244 | 2,788.7 | 317.3 | 3.2 | 11.4 |

**2005** (nossa agricultura 2+3: 9,920 ha)

| valor_glad | area_glad_ha | sobreposicao_ha | pct_da_nossa_agri | pct_do_valor_que_e_nossa_agri |
|---|---|---|---|---|
| 24 | 24,954.0 | 3,837.1 | 38.7 | 15.4 |
| 250 | 35,456.6 | 3,782.8 | 38.1 | 10.7 |
| 23 | 9,564.7 | 632.7 | 6.4 | 6.6 |
| 124 | 3,894.8 | 493.3 | 5.0 | 12.7 |
| 244 | 2,941.9 | 327.1 | 3.3 | 11.1 |
| 22 | 5,502.7 | 295.6 | 3.0 | 5.4 |
| 26 | 1,770.1 | 220.8 | 2.2 | 12.5 |

**2010** (nossa agricultura 2+3: 4,540 ha)

| valor_glad | area_glad_ha | sobreposicao_ha | pct_da_nossa_agri | pct_do_valor_que_e_nossa_agri |
|---|---|---|---|---|
| 24 | 23,282.3 | 2,309.0 | 50.9 | 9.9 |
| 250 | 41,588.0 | 1,165.0 | 25.7 | 2.8 |
| 124 | 3,833.0 | 475.8 | 10.5 | 12.4 |
| 23 | 7,757.1 | 253.5 | 5.6 | 3.3 |
| 244 | 2,909.4 | 182.4 | 4.0 | 6.3 |

**2015** (nossa agricultura 2+3: 3,576 ha)

| valor_glad | area_glad_ha | sobreposicao_ha | pct_da_nossa_agri | pct_do_valor_que_e_nossa_agri |
|---|---|---|---|---|
| 24 | 19,833.4 | 1,873.6 | 52.4 | 9.4 |
| 250 | 53,544.9 | 1,183.2 | 33.1 | 2.2 |
| 124 | 3,888.0 | 216.4 | 6.0 | 5.6 |
| 244 | 3,012.3 | 181.3 | 5.1 | 6.0 |

**2020** (nossa agricultura 2+3: 5,220 ha)

| valor_glad | area_glad_ha | sobreposicao_ha | pct_da_nossa_agri | pct_do_valor_que_e_nossa_agri |
|---|---|---|---|---|
| 24 | 17,930.9 | 2,483.8 | 47.6 | 13.9 |
| 250 | 57,139.1 | 1,696.7 | 32.5 | 3.0 |
| 124 | 3,875.8 | 467.7 | 9.0 | 12.1 |
| 244 | 3,499.7 | 443.7 | 8.5 | 12.7 |

### 4.4 Agricultura × ESA CCI (cropland = 10, 11, 12, 20, 30, 40; 300 m, reamostrado)

| epoca | nossa | nossa_ha | cci_crop_ha | pct_nossa_em_cci | pct_cci_na_nossa |
|---|---|---|---|---|---|
| 2000 | 2+3 | 9,967.7 | 35,140.0 | 48.9 | 13.9 |
| 2000 | 2 | 4,422.7 | 35,140.0 | 50.4 | 6.3 |
| 2005 | 2+3 | 9,920.2 | 41,741.1 | 55.2 | 13.1 |
| 2005 | 2 | 3,206.5 | 41,741.1 | 56.0 | 4.3 |
| 2010 | 2+3 | 4,540.1 | 41,659.6 | 57.5 | 6.3 |
| 2010 | 2 | 3,469.7 | 41,659.6 | 55.7 | 4.6 |
| 2015 | 2+3 | 3,576.3 | 40,635.2 | 52.2 | 4.6 |
| 2015 | 2 | 2,611.5 | 40,635.2 | 47.9 | 3.1 |
| 2020 | 2+3 | 5,219.6 | 35,220.7 | 51.7 | 7.7 |
| 2020 | 2 | 3,490.0 | 35,220.7 | 41.2 | 4.1 |

### 4.5 Agricultura 2020 × WorldCover 2021 e IO LULC 2020 (estas referências geraram parte dos rótulos de 2020; concordância não é independente)

| referencia | nossa | nossa_ha | ref_ha | pct_nossa_na_ref | pct_ref_na_nossa |
|---|---|---|---|---|---|
| WorldCover 2021 cropland (40) | 2+3 | 5,219.6 | 4,017.7 | 12.7 | 16.5 |
| WorldCover 2021 cropland (40) | 2 | 3,490.0 | 4,017.7 | 5.9 | 5.1 |
| IO LULC 2020 crops (5) | 2+3 | 5,219.6 | 1,115.5 | 7.6 | 35.4 |
| IO LULC 2020 crops (5) | 2 | 3,490.0 | 1,115.5 | 6.5 | 20.2 |

### 4.6 × LUCO (área de polígonos; LUCO cobre só a cidade)

| luco | epoca | luco_agri_ha | nossa_agri_na_cobertura_ha | pct_luco_agri_que_e_nossa_23 | pct_luco_agri_que_e_nossa_2 | pct_nossa_agri_em_luco_agri | luco_construido_inequivoco_ha | pct_luco_construido_que_e_nosso |
|---|---|---|---|---|---|---|---|---|
| 1982 | 1979 | 1,984.5 | 9,602.1 | 87.5 | 37.1 | 18.1 | 2,689.9 | 95.1 |
| 1982 | 1985 | 1,984.5 | 2,565.2 | 68.2 | 42.0 | 52.8 | 2,689.9 | 93.8 |
| 1991 | 1990 | 3,872.7 | 3,847.2 | 68.4 | 40.1 | 68.9 | 3,899.3 | 94.0 |
| 1991 | 1995 | 3,872.7 | 3,506.8 | 71.6 | 43.2 | 79.1 | 3,899.3 | 96.3 |
| 2001 | 2000 | 2,796.0 | 2,381.3 | 62.7 | 34.2 | 73.6 | 4,312.6 | 94.6 |
| 2001 | 2005 | 2,796.0 | 2,426.7 | 64.6 | 36.0 | 74.4 | 4,312.6 | 97.3 |

LUCO `Agricultura e pecuária` (3.0.3) são talhões hortícolas e quintas muradas e a classe 3.0.3 foi usada nos rótulos de treino (≤ 2005), logo a concordância das épocas 1979–2005 não é independente.

## 5. Problemas conhecidos por época

- **1979 (MSS, 9/jun/1979, Tier 2):** 3 bandas (verde, vermelho, NIR), 60 m reamostrado, TOA, sem SWIR. Legenda reduzida (1, 2, 3, 6, 7); a classe 3 contém toda a vegetação fora da baixada (inclui arbórea e herbácea) e a classe 2 é regra topográfica + NDVI. Só ordem de grandeza; não comparar classe 3 com épocas posteriores.
- **1985 (cena única TM, 1/jun/1984):** sem MAD; uma data apenas; construído subdetectado (revocação com GHSL ≈ 0,55) e queda do construído vs 1979 é artefato de método.
- **1990–2007 (GeoMAD, COUNT 6–17):** épocas com COUNT baixo (1990, 1997 = 6) ruidosas; 1997 tem queda do construído (≈ −13% na cidade) em relação a 1995 e 2000.
- **2010 (cena única TM, 9/abr/2011):** abril, fim da estação chuvosa: vegetação mais verde, mais confusão 2/5; sem MAD.
- **2020:** 2,5% de NaN na composição, quase todos no mar (3 667 ha no bbox); é também a época-âncora (treino direto), com ajuste mais fiel aos rótulos que nas demais, o que explica parte do salto da classe 2 de 2017 para 2020.
- **2026:** mediana de 12 cenas de estação seca (mai–set), sem MAD, modelo sem SMAD/EMAD/BCMAD; as outras épocas OLI têm MAD anual.
- **Classe 3 e classe 7:** poucos pontos de âncora (636 e 70 px erodidos). Após o ano 2000 a classe 3 colapsa para poucas centenas de hectares porque os pontos propagados são os de píxeis que continuam agrícolas e espectralmente estáveis; tratar classe 3 como indicativa. Classe 4 × 5 oscila muito entre épocas (arbórea vs herbácea), sem relação com mudança real.
- **Treino enviesado para a estabilidade:** a propagação exige ângulo pequeno em relação a 2020 e GHSL consistente, logo as áreas que mudaram (justamente as periferias em adensamento) ficam sub-representadas no treino das épocas antigas; o construído periférico é subestimado em 1985–2000.

## 6. Sanidade

Construído na área terrestre da cidade (ha) por época: 1979: 8,498, 1985: 6,899, 1990: 8,284, 1995: 8,252, 1997: 7,138, 2000: 8,546, 2005: 9,375, 2007: 11,377, 2010: 10,608, 2015: 11,717, 2017: 11,137, 2020: 11,562, 2025: 10,988, 2026: 10,952.

**Quedas do construído (> 1%) entre épocas consecutivas:**

- 1979 → 1985: 8,498 → 6,899 ha (-18.8%).
- 1995 → 1997: 8,252 → 7,138 ha (-13.5%).
- 2007 → 2010: 11,377 → 10,608 ha (-6.8%).
- 2015 → 2017: 11,717 → 11,137 ha (-4.9%).
- 2020 → 2025: 11,562 → 10,988 ha (-5.0%).

O construído real não decresce; estas quedas são erro de classificação (sensibilidade do modelo por época), não demolição. Não foram corrigidas além da regra temporal especificada (que só trata a reversão para agricultura); ver contagem de reversões não corrigidas em 2.3.

**Crescimento anual do construído > 5%/ano (cidade):** 1997→2000: 6.2%/ano; 2005→2007: 10.2%/ano. Saltos assim em intervalos curtos (2005→2007) refletem diferenças entre composições, não expansão real, e inflam a conversão agricultura→construído do intervalo.

**Classe 2 (cidade): variações > 30% entre épocas consecutivas:**

- 1997 → 2000: 2,557 → 1,701 ha (-33%).
- 2017 → 2020: 1,128 → 1,502 ha (+33%).

- Fluxos 1997 → 2000: saídas da classe 2: 2→5: 700 ha, 2→4: 280 ha, 2→1: 73 ha; entradas: 5→2: 161 ha, 3→2: 28 ha, 4→2: 14 ha.
- Fluxos 2017 → 2020: saídas da classe 2: 2→5: 67 ha, 2→3: 25 ha, 2→4: 17 ha; entradas: 5→2: 378 ha, 4→2: 102 ha, 1→2: 9 ha.

Inspeção: os fluxos mostram troca entre classes 2 e 5 (agricultura de baixada × herbácea/zona húmida), isto é, confusão espectral entre hortas irrigadas e capim/pântano na mesma baixada, amplificada por diferenças sazonais e de sensor entre composições (1997 vs 2000: COUNT 6 vs 10; 2017 vs 2020: 2020 é âncora), e não conversão de terra. As tendências decenais (queda da classe 2 de ≈ 2 500 ha em 1990–1997 para ≈ 1 200–1 500 ha após 2015) são mais confiáveis do que as variações entre épocas vizinhas.


## 7. Pós-processamento (decisões da revisão)

Decisões da investigação após a primeira rodada. `dados/proc/class/` fica intacto; a classificação final está em `dados/proc/class_final/` (scripts `06b_consistencia.py`, `07_areas_transicoes.py --entrada class_final`, `08_qa_classificacao.py`). As seções 1 a 6 acima descrevem a primeira rodada (bruta); as tabelas anteriores de áreas estão preservadas em `dados/proc/areas_run1/`. Os números das seções 3 e 6 não valem para a classificação final. O `08` passou a gerar só as figuras (a opção `--run1` regera o documento antigo e não deve ser usada, pois apagaria esta seção).

### 7.1 Regras de consistência temporal (06b)

Sequência das regras: 1985, 1990, 1995, 1997, 2000, 2005, 2007, 2010, 2015, 2017, 2020, 2025, 2026. A época 1979 fica fora de todas as regras e das séries quantitativas (copiada sem alteração; nas tabelas agregadas aparece com a nota correspondente).

1. Construído. construído_final(t) = 1 se classe(t) = 1 e a fração das épocas ≥ t (incluindo t) classificadas como construído for ≥ 0,5. Em seguida impõe-se monotonia: construído em t permanece construído em todas as épocas posteriores (píxeis acrescentados recebem classe 1; píxeis sem dado, classe 0, não são alterados). Píxeis construídos em t que deixam de sê-lo recebem a classe não construída mais frequente entre as suas próprias épocas (empate: classe em t+1 se estiver entre as empatadas; senão a primeira empatada nas épocas seguintes; senão a de menor código). Um píxel removido pela fração em t mas já construído_final numa época anterior permanece construído (monotonia), por isso "removidos (líquido)" ≤ "removeria".
2. Tremulação 2↔5. Em épocas interiores, se classe(t) ∈ {2,5}, classe(t−1) = classe(t+1) ∈ {2,5} e classe(t) ≠ classe(t−1), então classe(t) = classe(t−1). Uma passagem, simultânea, sobre o resultado da regra 1 (píxeis não construídos por definição).

Píxeis alterados por época e regra (cada píxel conta em uma época; o total compara com `class/`):

| index | época | regra 1a: removeria (fração) | regra 1: removidos (líquido) | regra 1: acrescentados (monotonia) | regra 2: tremulação 2↔5 | total alterados |
|---|---|---|---|---|---|---|
| 0 | 1985 | 26153 | 26153 | 0 | 0 | 26153 |
| 1 | 1990 | 35391 | 35391 | 17301 | 15743 | 68368 |
| 2 | 1995 | 38783 | 34521 | 39529 | 12443 | 86398 |
| 3 | 1997 | 11564 | 9843 | 92470 | 10809 | 113120 |
| 4 | 2000 | 17915 | 14285 | 86757 | 12206 | 113188 |
| 5 | 2005 | 25305 | 22288 | 57162 | 8828 | 88250 |
| 6 | 2007 | 37856 | 28222 | 41903 | 7377 | 77386 |
| 7 | 2010 | 18527 | 14258 | 58579 | 11868 | 84689 |
| 8 | 2015 | 38984 | 24864 | 25343 | 5335 | 55389 |
| 9 | 2017 | 15338 | 9735 | 48135 | 5637 | 63469 |
| 10 | 2020 | 38959 | 17362 | 26908 | 8914 | 53024 |
| 11 | 2025 | 0 | 0 | 46364 | 5715 | 52079 |
| 12 | 2026 | 0 | 0 | 68151 | 0 | 68151 |

Construído monotônico: sim (violações: 0 píxeis). Exceção declarada: 28 píxeis construídos em t cuja época seguinte é sem dado (classe 0, lacuna de composição) não são alterados.

### 7.2 Áreas finais, legenda agregada (cidade, ha)

Legenda: 1 Construído; 2 Zonas verdes (agricultura de baixada); 3 Sequeiro e mosaico (indicativo); 45 Vegetação não cultivada (4+5); 6 Água; 7 Solo exposto. Tabelas completas em `dados/proc/areas/areas_agregado_*.csv` (classe×época bbox/cidade, distrito, bairro, transições). As tabelas de legenda completa (`areas_classe_epoca.csv`, `areas_distrito.csv`, `areas_bairro.csv`, transições, `conversao.csv`, `perda_bairro.csv`) e o raster `class_final/conversao_agri_construido.tif` foram regerados a partir de `class_final`. 1979 não entra (legenda reduzida: classe 3 = toda a vegetação).

| epoca | 1 Construído | 2 Zonas verdes | 3 Sequeiro (indicativo) | 45 Veg. não cultivada | 6 Água | 7 Solo exposto |
|---|---|---|---|---|---|---|
| 1979 | 8498 | 2050 | 16764 | 0 | 747 | 1803 |
| 1985 | 6239 | 2007 | 2497 | 17930 | 705 | 471 |
| 1990 | 7464 | 2540 | 5236 | 13196 | 842 | 583 |
| 1995 | 8275 | 2472 | 3076 | 14934 | 832 | 272 |
| 1997 | 8353 | 2449 | 2135 | 15878 | 824 | 222 |
| 2000 | 9225 | 1704 | 1456 | 16375 | 804 | 296 |
| 2005 | 9749 | 1667 | 2200 | 15142 | 768 | 337 |
| 2007 | 10918 | 1530 | 312 | 15973 | 715 | 413 |
| 2010 | 11064 | 1465 | 325 | 15841 | 799 | 367 |
| 2015 | 11471 | 1291 | 346 | 15542 | 768 | 443 |
| 2017 | 11632 | 1257 | 214 | 15662 | 748 | 348 |
| 2020 | 11832 | 1318 | 265 | 15141 | 706 | 598 |
| 2025 | 12219 | 1288 | 162 | 15041 | 724 | 426 |
| 2026 | 12479 | 1197 | 151 | 14876 | 762 | 396 |

### 7.3 LUCO 1964, 1973, 1982, 1991, 2001 na máscara terrestre da cidade

Polígonos LUCO rasterizados a 30 m (sem erosão) com o crosswalk de `05_rotulos.py` (agricultura 3.0.3 dividida em 2 e 3 pela mesma regra altitude/TPI/zona húmida; 4 e 5 somam 45; classes ambíguas ficam em "excluido"). O LUCO cobre só parte da cidade; por isso são dadas a área coberta e as proporções sobre a área coberta (`pct_cobertura`, incluindo "excluido") e sobre a área classificada (`pct_classificada`, sem "excluido"). Arquivo: `dados/proc/areas/areas_luco.csv`. Os valores LUCO não são comparáveis em nível com a série de 30 m, que cobre a cidade inteira.

| ano | 1 | 2 | 3 | 45 | 6 | 7 | excluido | cobertura_ha | pct_cidade_coberta |
|---|---|---|---|---|---|---|---|---|---|
| 1964 | 1,266.0 | 632.8 | 413.3 | 11,095.1 | 17.2 | 41.0 | 2,717.1 | 16,182.4 | 54.2 |
| 1973 | 1,939.0 | 390.0 | 592.1 | 9,733.6 | 18.0 | 61.9 | 3,501.6 | 16,236.3 | 54.4 |
| 1982 | 2,684.5 | 1,034.4 | 947.3 | 7,605.6 | 18.1 | 77.1 | 3,860.2 | 16,227.3 | 54.3 |
| 1991 | 3,893.7 | 2,182.7 | 1,687.1 | 4,343.4 | 27.5 | 56.6 | 4,037.8 | 16,228.9 | 54.3 |
| 2001 | 4,306.9 | 1,337.0 | 1,456.7 | 3,338.3 | 101.1 | 52.6 | 5,636.7 | 16,229.2 | 54.3 |

Percentual da área classificada (LUCO) em classe 1 e 2:

| ano | 1 | 2 |
|---|---|---|
| 1964 | 9.4 | 4.7 |
| 1973 | 15.2 | 3.1 |
| 1982 | 21.7 | 8.4 |
| 1991 | 31.9 | 17.9 |
| 2001 | 40.7 | 12.6 |

### 7.4 Figuras

`dados/fig/class/`: `mapas_classes.png`, `area_empilhada_cidade.png` (1985–2026), `linhas_classe1_classe2.png` (1979 marcada como excluída; pontos LUCO como losangos sobre os mesmos gráficos das classes 1 e 2, com nota de cobertura parcial), `mapa_ano_conversao.png`. Legenda agregada, paleta Ardósia, rótulos em português.

### 7.5 Amostra de validação cega de 2020 (script 10)

- Amostra estratificada aleatória de `class_final/2020.tif` (legenda agregada), estratos 1 (n=60), 2 (60), 45 (60), 3 (40), 6 (30), 7 (30); 280 pontos no bbox (terra + água), distância mínima 300 m (verificada), semente 20260611; estratos raros sorteados primeiro.
- Imagem: DE Africa `gm_s2_annual` 2020, tile x213y043 (STAC explorer.digitalearth.africa, HTTPS anônimo), bandas B02, B03, B04, B08, B11 na janela do bbox + 1 km: janelas nativas em `dados/raw/s2_geomad_2020/`, raster UTM 36S 10 m alinhado à grade em `dados/proc/s2_2020_10m.tif` (uint16, reflectância × 10⁴). Falsa-cor Landsat de `comp/2020.tif` (SWIR1, NIR, vermelho).
- Chip por ponto, três painéis: Sentinel-2 cor verdadeira (janela 600 m), Sentinel-2 falsa-cor NIR-vermelho-verde (600 m), Landsat 30 m falsa-cor (1,5 km); quadrado vermelho = píxel de 30 m; barra de 100 m; texto apenas com id, altitude (`dem.tif`) e EMAD (valor de `comp/2020.tif`, unidades da composição). Nenhuma informação de classe. Estiramento por canal no percentil 2–98 da área; janela fora da grade preenchida em cinza.
- 47 folhas de 6 chips (2 colunas × 3 linhas, 1920 px de largura) em `dados/proc/validacao/folhas/folha_NN.png`, ordem embaralhada entre estratos, ids atribuídos após o embaralhamento. Pontos sem classe: `dados/proc/validacao/pontos_2020_cego.csv` (id, x, y, lon, lat, folha). Chave (id, classe mapeada, estrato) em `dados/proc/validacao/.chave/chave_2020.csv`: não ler ao rotular.
- Rótulos esperados em `dados/proc/validacao/rotulos_2020.csv` (id, classe_ref, confianca, nota; classe_ref ∈ {1, 2, 3, 45, 6, 7, indeterminado}). `scripts/11_avaliacao_exatidao.py` (testado com rótulos sintéticos, já removidos) calcula matriz de confusão, exatidões global, do usuário e do produtor com IC 95%, e áreas ajustadas (Olofsson et al., 2014) para bbox e máscara da cidade, excluindo e contando os indeterminados; grava `exatidao_2020.json` e acrescenta a seção 8 a este documento (marcadores HTML, substituída a cada execução).

<!-- exatidao_2020:inicio -->
## 8. Exatidão e áreas ajustadas de 2020 (validação cega)

Gerado por `scripts/11_avaliacao_exatidao.py`. Amostra estratificada pela classe mapeada de 2020 (`class_final`), legenda agregada, rotulada às cegas por interpretação visual de chips Sentinel-2 10 m / Landsat 30 m. Pontos: 280; indeterminados excluídos: 0; sem rótulo: 0; usados: 280. Estimadores de Olofsson et al. (2014); IC 95% = ±1,96 EP. Linhas = classe mapeada, colunas = referência.

### 8.1 Âmbito: bbox (terra + água, todos os píxeis mapeados)

Matriz de confusão (contagem de pontos):

| mapa \ referência | 1 | 2 | 3 | 45 | 6 | 7 | total |
|---|---|---|---|---|---|---|---|
| 1 Construído | 53 | 1 | 5 | 0 | 0 | 1 | 60 |
| 2 Zonas verdes | 9 | 20 | 0 | 28 | 0 | 3 | 60 |
| 3 Sequeiro e mosaico | 0 | 9 | 20 | 10 | 0 | 1 | 40 |
| 45 Vegetação não cultivada | 5 | 5 | 19 | 28 | 0 | 3 | 60 |
| 6 Água | 1 | 0 | 0 | 0 | 28 | 1 | 30 |
| 7 Solo exposto | 5 | 0 | 0 | 0 | 6 | 19 | 30 |
| total | 73 | 35 | 44 | 66 | 34 | 28 | 280 |

Exatidão global (ponderada pela área): 73.7% ± 5.7 p.p.

| classe | área mapeada (ha) | área ajustada (ha) | IC 95% (± ha) | exatidão do usuário (%) | ± | exatidão do produtor (%) | ± |
|---|---|---|---|---|---|---|---|
| 1 Construído | 45,480 | 45,794 | 5,476 | 88.3 | 8.2 | 87.7 | 7.8 |
| 2 Zonas verdes | 2,760 | 5,849 | 3,548 | 33.3 | 12.0 | 15.7 | 10.6 |
| 3 Sequeiro e mosaico | 1,753 | 19,019 | 6,270 | 50.0 | 15.7 | 4.6 | 2.1 |
| 45 Vegetação não cultivada | 45,325 | 22,878 | 5,786 | 46.7 | 12.7 | 92.5 | 2.6 |
| 6 Água | 36,849 | 34,634 | 3,350 | 93.3 | 9.1 | 99.3 | 0.5 |
| 7 Solo exposto | 1,208 | 5,200 | 3,799 | 63.3 | 17.5 | 14.7 | 11.3 |

### 8.2 Âmbito: máscara terrestre da Cidade de Maputo

Só pontos dentro da máscara; estratos com menos de 2 pontos não têm erro padrão (células vazias). Amostra pequena: ler com cautela.

Matriz de confusão (contagem de pontos):

| mapa \ referência | 1 | 2 | 3 | 45 | 6 | 7 | total |
|---|---|---|---|---|---|---|---|
| 1 Construído | 21 | 0 | 0 | 0 | 0 | 1 | 22 |
| 2 Zonas verdes | 3 | 12 | 0 | 13 | 0 | 0 | 28 |
| 3 Sequeiro e mosaico | 0 | 3 | 0 | 4 | 0 | 1 | 8 |
| 45 Vegetação não cultivada | 1 | 1 | 2 | 12 | 0 | 1 | 17 |
| 6 Água | 1 | 0 | 0 | 0 | 1 | 0 | 2 |
| 7 Solo exposto | 5 | 0 | 0 | 0 | 0 | 7 | 12 |
| total | 31 | 16 | 2 | 29 | 1 | 10 | 89 |

Exatidão global (ponderada pela área): 78.5% ± 11.7 p.p.

| classe | área mapeada (ha) | área ajustada (ha) | IC 95% (± ha) | exatidão do usuário (%) | ± | exatidão do produtor (%) | ± |
|---|---|---|---|---|---|---|---|
| 1 Construído | 12,632 | 13,640 | 2,131 | 95.5 | 8.9 | 88.4 | 11.8 |
| 2 Zonas verdes | 1,295 | 1,500 | 1,678 | 42.9 | 18.7 | 37.0 | 42.2 |
| 3 Sequeiro e mosaico | 266 | 1,691 | 2,269 | 0.0 | 0.0 | 0.0 | 0.0 |
| 45 Vegetação não cultivada | 14,375 | 10,881 | 3,220 | 70.6 | 22.3 | 93.3 | 3.0 |
| 6 Água | 704 | 352 | 690 | 50.0 | 98.0 | 100.0 | 0.0 |
| 7 Solo exposto | 588 | 1,796 | 2,012 | 58.3 | 29.1 | 19.1 | 22.7 |

<!-- exatidao_2020:fim -->

<!-- sensibilidade_2020:inicio -->
## 9. Sensibilidade a rótulos de baixa confiança (validação cega de 2020)

Gerado por `scripts/11_avaliacao_exatidao.py --sem-baixa`. Os rótulos foram atribuídos por um agente automático de interpretação visual de imagens, cego ao mapa; recomenda-se revisão humana de uma subamostra. A tabela compara o conjunto completo com o conjunto sem os rótulos de confiança 'baixa'.

Distribuição da confiança dos rótulos (todos os pontos rotulados): alta 54, baixa 118, media 108.

### Cidade (máscara terrestre)

| medida | todos os rótulos | sem confiança baixa |
|---|---|---|
| pontos usados | 89 | 57 |
| exatidão global (%) | 78.5 ± 11.7 | 81.1 ± 17.6 |
| UA classe 1 (construído) (%) | 95.5 ± 8.9 | 100.0 ± 0.0 |
| PA classe 1 (construído) (%) | 88.4 ± 11.8 | 94.0 ± 5.3 |
| UA classe 2 (zonas verdes) (%) | 42.9 ± 18.7 | 50.0 ± 27.2 |
| PA classe 2 (zonas verdes) (%) | 37.0 ± 42.2 | 70.8 ± 11.2 |
| área ajustada classe 2 (ha) | 1,500 ± 1,678 | 914 ± 352 |

### Retângulo de estudo

| medida | todos os rótulos | sem confiança baixa |
|---|---|---|
| pontos usados | 280 | 162 |
| exatidão global (%) | 73.7 ± 5.7 | 82.2 ± 7.0 |
| UA classe 1 (construído) (%) | 88.3 ± 8.2 | 95.7 ± 6.0 |
| PA classe 1 (construído) (%) | 87.7 ± 7.8 | 92.5 ± 8.2 |
| UA classe 2 (zonas verdes) (%) | 33.3 ± 12.0 | 55.6 ± 23.6 |
| PA classe 2 (zonas verdes) (%) | 15.7 ± 10.6 | 34.9 ± 31.9 |
| área ajustada classe 2 (ha) | 5,849 ± 3,548 | 4,396 ± 3,883 |

<!-- sensibilidade_2020:fim -->

## 10. Nota sobre a revisão da regra temporal e a amostra de 2020
A amostra de validação foi sorteada sobre `class_final/2020` antes da revisão da regra de consistência (janela de 3 épocas,
pós-auditoria). No mapa revisto, 6 dos 280 pontos (2%) mudaram de classe mapeada, todos para construído (3 de 45→1, 3 de 2→1).
O estimador de Olofsson continua a usar os estratos do desenho original (`estrato` na chave) com as áreas por classe do mapa
revisto; a inconsistência resultante é pequena e foi mantida em vez de sortear nova amostra. Registrado pela sessão principal.
