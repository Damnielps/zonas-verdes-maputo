# Levantamento 1 — dados orbitais (verificado em 2026-11-11)

Cobertura: só Landsat WRS-2 **path 167 / row 078** cobre todo o bbox (32.40–32.75 E, −26.10 a −25.75 S).
Path 168/078 cobre só a faixa oeste. Sentinel-2: tile MGRS **36JVS**.

## Composições anuais Digital Earth Africa (rota principal) — leitura anônima HTTPS
Tile **x213y043** (EPSG:6933, 3200×3200 px; lon 31.84–32.83, lat −26.50 a −25.66).
- `gm_ls5_ls7_annual` 1984–2012 (sem 1988). Bandas SR_B1–B7, SMAD, EMAD, BCMAD, COUNT. 1984–87 provavelmente
  com 1–3 cenas: conferir COUNT. Ex.:
  `https://deafrica-services.s3.af-south-1.amazonaws.com/gm_ls5_ls7_annual/1-0-0/x213/y043/1985--P1Y/gm_ls5_ls7_annual_x213y043_1985--P1Y_SR_B3.tif`
- `gm_ls8_annual` 2013–2020; `gm_ls8_ls9_annual` 2021–2025; `gm_s2_annual` 2017–2025 (10 m).
- `fc_ls_summary_annual` 1984–2025 (cobertura fracional); `wsf_evolution` (tiles 32_-26, 32_-28);
  `crop_mask_southeast` 2019.
- STAC: `POST https://explorer.digitalearth.africa/stac/search` (o `/stac/collections` dá erro).
  Use o `href` dos assets devolvidos pelo STAC em vez de montar URLs.

## Cenas Landsat C2 L2 — Planetary Computer (reserva / anos-lacuna)
Token SAS anônimo: `GET https://planetarycomputer.microsoft.com/api/sas/v1/token/landsat-c2-l2` (~24 h).
Melhores cenas de estação seca (path 167):
| alvo | cena |
|---|---|
| 1980 | lacuna. MSS 1979: LM03_L1TP_179078_19790609 (0%), LM02_…180078_19790725 (0%) — coleção `landsat-c2-l1`, Tier 2 |
| 1985 | lacuna no path 167. LT05_L2SP_167078_19840601 (10%); MSS LM05_L1TP_167078_19840719 (0%); LT05_…19861114 |
| 1990 | LT05_L2SP_167078_19900602 (2%) |
| 1995 | LT05_L2SP_167078_19950718 (0%) |
| 1997 | LT05_L2SP_167078_19970723 (0%) |
| 2000 | LE07_L2SP_167078_20000808 (5%); LT05_…20000901 (6%) |
| 2005 | LT05_L2SP_167078_20050830 (1%) |
| 2007 | LT05_L2SP_167078_20070820 (0%) |
| 2010 | fraco: LE07_…20100921 (faixas SLC-off); reserva LT05_…20080907 ou LT05_…20110409 |
| 2015 | LC08_L2SP_167078_20150927 (1%) |
| 2017, 2020 | várias LC08/LE07 |
| 2025 | LC08_L2SP_167078_20250618, LC09_…20250610 |
| 2026 | LC09_L2SP_167078_20260629 (0%), …20260512 |
Earth Search Landsat aponta para bucket requester-pays (403). DE Africa tem cópia anônima em `s3://deafrica-landsat`.

## Sentinel-2 L2A
Planetary Computer `sentinel-2-l2a`: 2016+ (dezenas de cenas secas/ano). Earth Search `sentinel-2-l2a` (2017+), anônimo.

## Produtos prontos para validação
- GHSL GHS-BUILT-S R2023A, épocas 1975–2030 a 100 m, tile R13_C22 (confirmar R12/R13):
  `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/GHS_BUILT_S_E{ano}_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_BUILT_S_E{ano}_GLOBE_R2023A_54009_100_V1_0_R13_C22.zip`
- GLAD GLCLUC v2 (2000, 2005, 2010, 2015, 2020 + change): `https://storage.googleapis.com/earthenginepartners-hansen/GLCLU2000-2020/v2/{ano}/20S_030E.tif` (~189 MB)
- ESA WorldCover 2021: `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S27E030_Map.tif`
- ESA CCI LC 300 m: PC `esa-cci-lc` 1992–2020; DE Africa `cci_landcover` 1992–2022.
- IO LULC 10 m: PC `io-lulc-annual-v02`, item 36J, 2017–2023.
- Dynamic World: só Earth Engine (não usar).

## Vetores
- HDX COD-AB `cod-ab-moz` v02 (2025): `https://data.humdata.org/dataset/5e8d83a5-1210-49be-b7d9-cf286dbc15df/resource/f1d97232-4cb5-4083-b3cc-d192aa9bdcfe/download/moz_admin_boundaries.geojson.zip`
  (precisa User-Agent de navegador). adm2: 7 distritos municipais; adm4: 64 bairros; Matola adm4 tem "Vale de Infulene" e "Zona Verde".
- OSM Overpass (precisa User-Agent): no bbox 473 farmland, 24 allotments, 117 orchard.
- LUCO (Henriques & Correia 2023): uso do solo 1964, 1973, 1982, 1991, 2001, CC BY 4.0, https://zenodo.org/records/8089260

## CORONA/KH-9
Exige login USGS; não verificado; fora do escopo.
