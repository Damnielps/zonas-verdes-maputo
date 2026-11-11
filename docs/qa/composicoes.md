# QA das composições (30 m, EPSG:32736)

Gerado por `scripts/04_qa_composicoes.py`. NaN % = fração da grade do bbox sem dado válido na banda vermelha; COUNT = número de observações por píxel (GeoMAD: banda COUNT; cena única: 1; 2026: observações válidas).

| Época | Fonte | Sensor | Datas | NaN % | COUNT mediana | Substituição / notas |
|---|---|---|---|---|---|---|
| 1979 | Planetary Computer landsat-c2-l1 LM03_L1TP_179078_19790609_02_T2 (Tier 2) (LM03_L1TP_179078_19790609_02_T2) | Landsat 3 MSS (60 m) | 1979-06-09 | 0.00 | 1 | TOA, (M*DN+A)/sin(elev solar); verde=B4, vermelho=B5, nir=B7 (0,8-1,1um; B6 0,7-0,8um nao usada); 60 m -> grade 30 m por reamostragem bilinear; blue/swir ausentes. Cena de junho de 1979 como substituta do censo de 1980 |
| 1985 | Planetary Computer landsat-c2-l2 LT05_L2SP_167078_19840601_02_T1 (LT05_L2SP_167078_19840601_02_T1) | landsat-5 | 1984-06-01 | 0.03 | 1 | GeoMAD 1985 rejeitado (NaN 69.8%, COUNT mediana 1); substituído por TM de 19840601 (1984-06-01).  |
| 1990 | Digital Earth Africa gm_ls5_ls7_annual v1.0.0 tile x213y043 (e612eb76-f810-5f07-9106-6c93ec8be81e) | Landsat 5/7 TM/ETM+ | 1990-01-01/1990-12-31 | 0.01 | 6 | - |
| 1995 | Digital Earth Africa gm_ls5_ls7_annual v1.0.0 tile x213y043 (be1265a1-9acf-5355-a150-986d4695a35a) | Landsat 5/7 TM/ETM+ | 1995-01-01/1995-12-31 | 0.00 | 16 | - |
| 1997 | Digital Earth Africa gm_ls5_ls7_annual v1.0.0 tile x213y043 (949b30d5-73e1-5dac-ac0f-b3c9f7fef965) | Landsat 5/7 TM/ETM+ | 1997-01-01/1997-12-31 | 0.01 | 6 | - |
| 2000 | Digital Earth Africa gm_ls5_ls7_annual v1.0.0 tile x213y043 (3344711f-d580-5262-88ee-6e0e801e5322) | Landsat 5/7 TM/ETM+ | 2000-01-01/2000-12-31 | 0.00 | 10 | - |
| 2005 | Digital Earth Africa gm_ls5_ls7_annual v1.0.0 tile x213y043 (06463f80-319a-5d5d-b229-55c9d50fbdf3) | Landsat 5/7 TM/ETM+ | 2005-01-01/2005-12-31 | 0.00 | 13 | - |
| 2007 | Digital Earth Africa gm_ls5_ls7_annual v1.0.0 tile x213y043 (7d47d554-daf5-5900-b355-725aa4e97ecd) | Landsat 5/7 TM/ETM+ | 2007-01-01/2007-12-31 | 0.00 | 17 | - |
| 2010 | Planetary Computer landsat-c2-l2 LT05_L2SP_167078_20110409_02_T2 (LT05_L2SP_167078_20110409_02_T2) | landsat-5 | 2011-04-09 | 0.04 | 1 | GeoMAD 2010 rejeitado (NaN 0.0%, COUNT mediana 7, listrado SLC-off); substituído por TM 20110409.  |
| 2015 | Digital Earth Africa gm_ls8_annual v1.0.0 tile x213y043 (bfed7ff0-c0a6-528f-8ea6-7fd095265ae4) | Landsat 8 OLI | 2015-01-01/2015-12-31 | 0.00 | 13 | - |
| 2017 | Digital Earth Africa gm_ls8_annual v1.0.0 tile x213y043 (0240c119-3154-5ed9-8343-ef49e83d7d3a) | Landsat 8 OLI | 2017-01-01/2017-12-31 | 0.00 | 18 | - |
| 2020 | Digital Earth Africa gm_ls8_annual v1.0.0 tile x213y043 (c1aac252-b1c9-5496-b69a-659cef01e4fa) | Landsat 8 OLI | 2020-01-01/2020-12-31 | 2.47 | 16 | - |
| 2025 | Digital Earth Africa gm_ls8_ls9_annual v1.0.0 tile x213y043 (08c63fb5-b19f-5fb7-b7e4-7ea36a4c823e) | Landsat 8/9 OLI | 2025-01-01/2025-12-31 | 0.00 | 24 | - |
| 2026 | Planetary Computer landsat-c2-l2, mediana estação seca (mai-set 2026), p167 r078, nuvem<30%, QA_PIXEL (LC08_L2SP_167078_20260504_02_T1,LC09_L2SP_167078_20260512_02_T1,LC09_L2SP_167078_20260528_02_T1,LC09_L2SP_167078_20260613_02_T1,LC09_L2SP_167078_20260629_02_T1,LC08_L2SP_167078_20260707_02_T1,LC09_L2SP_167078_20260715_02_T1,LC08_L2SP_167078_20260723_02_T1,LC09_L2SP_167078_20260731_02_T1,LC08_L2SP_167078_20260808_02_T1,LC09_L2SP_167078_20260816_02_T1,LC08_L2SP_167078_20260824_02_T1) | Landsat 8/9 OLI | 2026-05-04/2026-08-24 | 0.00 | 11 | - |

## Percentis 2-98% por banda (reflectância)

| Época | Bandas |
|---|---|
| 1979 | green 0.057-0.099; red 0.045-0.118; nir 0.007-0.219 |
| 1985 | blue 0.024-0.060; green 0.045-0.098; red 0.029-0.121; nir 0.013-0.308; swir1 0.000-0.267; swir2 0.000-0.199 |
| 1990 | blue 0.044-0.087; green 0.056-0.122; red 0.035-0.148; nir 0.017-0.288; swir1 0.005-0.335; swir2 0.004-0.267 |
| 1995 | blue 0.046-0.085; green 0.055-0.124; red 0.031-0.145; nir 0.018-0.298; swir1 0.006-0.328; swir2 0.006-0.257 |
| 1997 | blue 0.043-0.076; green 0.051-0.105; red 0.030-0.127; nir 0.018-0.275; swir1 0.006-0.306; swir2 0.005-0.230 |
| 2000 | blue 0.036-0.079; green 0.050-0.114; red 0.032-0.142; nir 0.018-0.305; swir1 0.009-0.330; swir2 0.008-0.257 |
| 2005 | blue 0.048-0.089; green 0.055-0.126; red 0.033-0.155; nir 0.019-0.290; swir1 0.008-0.351; swir2 0.007-0.292 |
| 2007 | blue 0.040-0.085; green 0.051-0.124; red 0.028-0.153; nir 0.016-0.287; swir1 0.007-0.344; swir2 0.006-0.287 |
| 2010 | blue 0.027-0.089; green 0.031-0.131; red 0.014-0.155; nir 0.009-0.330; swir1 0.003-0.346; swir2 0.001-0.281 |
| 2015 | blue 0.020-0.084; green 0.050-0.128; red 0.036-0.163; nir 0.006-0.308; swir1 0.010-0.359; swir2 0.009-0.303 |
| 2017 | blue 0.022-0.084; green 0.048-0.127; red 0.029-0.161; nir 0.002-0.319; swir1 0.009-0.351; swir2 0.009-0.294 |
| 2020 | blue 0.020-0.089; green 0.044-0.132; red 0.023-0.164; nir 0.001-0.300; swir1 0.006-0.347; swir2 0.006-0.295 |
| 2025 | blue 0.019-0.080; green 0.045-0.122; red 0.028-0.154; nir 0.006-0.301; swir1 0.007-0.334; swir2 0.007-0.281 |
| 2026 | blue 0.016-0.077; green 0.034-0.119; red 0.010-0.148; nir 0.000-0.300; swir1 0.001-0.324; swir2 0.002-0.271 |

## Notas

- 1979 (MSS): sem banda azul; quick-look 'rgb' é pseudo-cor (R=vermelho, G=verde, B=verde); falsa-cor = NIR-vermelho-verde.
- Quick-looks com estiramento 2-98% por banda e por imagem; NaN em branco.
- Painel de contato: `dados/fig/qa/painel_rgb.png`.
