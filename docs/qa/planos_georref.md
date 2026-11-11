# Georreferenciação e vectorização dos planos 1985 e 2008

Script: `scripts/09_georref_planos.py` (reprodutível a partir de `dados/proc/planos/gcp_1985.csv` e `gcp_2008.csv`).

## Método
- **PEUMM 2008** (3306x2337 px): a planta traz grelha UTM (zona 36, datum Moznet ~ WGS84) rotulada de 2,5 em 2,5 km.
  36 cruzamentos de grelha (E 445-470 k, N 7115-7142,5 k) servem de controlo; posições das linhas medidas por
  centróide sub-pixel. Resolução ~15,8 m/pixel. Só o painel esquerdo (município + Catembe) é usado; o painel direito (Inhaca) fica fora da área.
- **INPF 1985, Mapa 7** (927x712 px; mapa em ~404x490 px, ~65 m/pixel): 9 cruzamentos da graticula (3 meridianos x 3 paralelos)
  convertidos de lon/lat para UTM 36S. Paralelos 25°50', 25°55', 26°00' S (rótulos lidos na imagem).
  **Meridianos**: no digitalizado os rótulos aparecem como 32°40', 32°45', 32°50' E, mas com essa leitura o mapa cai ~10 km a leste de Maputo
  (Baixa/Ponta Vermelha em lon ~32,59). A leitura 32°30', 32°35', 32°40' E (os rótulos de baixa resolução são ambíguos: 30/40, 35/45, 40/50)
  coloca a costa, o estuário e Catembe sobre a costa 2020 (ver QA). Adoptada a segunda; o deslocamento de 10' foi decidido por
  correspondência de feições, logo a escala e a rotação são verificadas independentemente, mas a origem em longitude não.
- Modelo: polinómio de grau 1 (afim) ou 2, escolhido pelo RMSE nos pontos de verificação (grau 2 só se melhorar >15 % e o LOO não piorar). Com 9 pontos de controlo
  o grau 2 ajusta-se quase exactamente (sobreajuste), por isso não é usado no 1985.
- Rasters RGBA (EPSG:32736): 2008 a 15 m, 1985 a 30 m (alinhados à grade do projecto).
- Vectorização em espaço de pixel (sem reamostragem) e transformação dos vértices pelo modelo; simplificação 5 m (2008) / 15 m (1985).

## RMSE (m)
| plano | grau | controlo | LOO controlo | verificação (landmarks) | afim / grau 2 (verif.) |
|---|---|---|---|---|---|
| 2008 (n_ctl=36, n_chk=3) | 1 | 11.7 | 12.7 | 22.1 | 22.1 / 22.5 |
| 1985 (n_ctl=9, n_chk=6) | 1 | 18.0 | 26.2 | 84.4 | 84.4 / 86.6 |

Verificação independente por linha de costa (distância à costa 2020, MNDWI Sentinel-2; a costa mudou 1985/2008-2020, logo é um limite superior do erro posicional):
- 2008: n=14366, mediana 30 m, p90 60 m, RMSE 65 m
- 1985: n=10262, mediana 67 m, p90 218 m, RMSE 133 m

Pontos de verificação: ver colunas `tipo=verificacao` nos CSV (2008: 3 pontos de costa lidos visualmente em recortes com grelha, incerteza de leitura ~20 m;
1985: 6 posições extraídas numericamente do raster do plano e da máscara de água 2020, quantizadas a 30 m).

## Áreas (ha)
| camada | no mapa (recortado à grade do projecto) | dentro dos 7 distritos de Maputo |
|---|---|---|
| 1985 zv_permanentes | 16,945 | 5,826 |
| 1985 zv_provisorias | 7,149 | 1,928 |
| 1985 ocupacao_actual | 15,073 | 8,558 |
| 2008 agropecuaria | 3,365 | 3,365 |
| 2008 expansao_urbana | 3,639 | 3,639 |
| 2008 urbanizavel_planificada | 2,923 | 2,923 |
| 2008 urbanizavel_nao_planificada | 2,377 | 2,377 |

Literatura (Christie 1996 citando Roth et al., reportado): ZV permanentes 5 230 ha, provisórias 2 575 ha (razão perm/prov = 2.03).
Medido: permanentes 16,945 ha (mapa) / 5,826 ha (cidade); provisórias 7,149 / 1,928 ha;
razão perm/prov = 2.37 (mapa) / 3.02 (cidade). Sem forçar concordância.

## Ressalvas
- **Legenda 1985**: no digitalizado, "Zonas Verdes Permanentes" tem pontos grossos e espaçados e "Zonas Verdes Provisórias" pontilhado fino e denso (o briefing indicava o inverso). Seguiu-se a legenda.
- A segmentação 1985 é por textura (densidade de manchas escuras compactas após remoção de linhas) em imagem de ~65 m/pixel: as fronteiras entre fino/grosso são difusas,
  o pontilhado fino de baixo contraste é subdetectado e zonas de Habitação (hachura vertical) vizinhas de pontilhado podem receber falsos positivos. Tratar as áreas como ordem de grandeza (incerteza facilmente >30 %).
- O Mapa 7 inclui território fora do município (Matola, Boane); a comparação com a literatura faz-se com o recorte aos 7 distritos e com o mapa inteiro, mas a definição espacial do valor da literatura é desconhecida.
- 2008: extracção por cor exacta da legenda (tolerância 8-12/255), fecho morfológico de 3 px; estradas, círculos hachurados de centros urbanos propostos e contornos amarelos fragmentam polígonos (subestimativa pequena).
  A borda amarela de "Área para Expansão Urbana" foi incorporada ao polígono. Os padrões hachurados sobre outras classes não são recuperados.
- Datum Moznet tratado como WGS84 (diferença sub-métrica a métrica). Imagens de terceiros: ver `CREDITOS.md`.
