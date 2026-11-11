# Síntese L5 — séries quantitativas da produção agropecuária urbana em Maputo

Base: `fontes/series_producao.csv` (253 linhas; 200 VERIFICADO, 53 PARCIAL = citações de segunda mão ou lacunas de ano/unidade). Nada foi estimado nem interpolado.

## Séries construíveis

1. **Cooperativas UGC, 1980-1994 (anual).** Christie (1996), Tabela 5, p. 61: nº de cooperativas, membros, área e produção agrícola e pecuária (t), 1981-94; 1980 em texto (7 coop., 500 membros, 4 t). É a única série anual de produção, mas **só do sector cooperativo** e sem desagregação por cultura ou espécie. Pico em 1987 (210 coop., 11 000 membros); queda de membros a 5 400 em 1990 com área constante de 1 000 ha (valores arredondados na fonte). Outras fontes (Sumbane 1988 via SLE, UCLG 2010, Roth 1995, dossier mozambiquehistory) divergem 1-15% em pontos coincidentes.
2. **Área e agricultores de todo o sector, pontos 1985, 1986, 1988, 1993-94.** Plano de 1985 (Roth, Tabela 2.1): 5 230 ha permanentes + 2 575 provisórias = 7 805 ha (área legal, não cultivada); GZV: 15,3 mil ha e 71,4 mil agricultores (1988); 12,4 mil ha (1993, ano inferido) e 9,7 mil ha (1994) familiar+privado; ~60 mil familiares (1993). Vão de 1995 a 2016 **sem dados**.
3. **Associações, 2017-2025 (pontos).** DASACM 2018 (SLE Tabela 8): 34 associações, 11 194 produtores, 1 300 ha, por distrito; 14 500 agricultores (2017); Dürrnagel (2021): KaMavota 814 ha, KaMubukwana 422 ha; Vianna/PAPAP 2016: 14 508 produtores; Muchanga (2025): vale de Mavota 891,5 ha, 9 784 membros. Pontes: 64 associações (1986, Sumbane via SLE) e 74 (c. 1991, Roth).
4. **Previsões de campanha (CMM/Conselho dos Serviços de Representação), 2018, 2024, 2024/25, 2026/27.** Hortícolas 132 374 t (comercialização 2024) a 203 014 t (2026/27); frango 8 598-8 625 t; carnes por espécie e ovos (2024/25 e 2026/27). **São metas, não produção realizada.**
5. **Produção média PAPAP 2017** (média de 10 anos): 75 000 t de hortícolas e 1 100 t de frango por ano; 75% vendidos na cidade/província e 25% exportados para Essuatíni e África do Sul; potencial 200 000 t; necessidade 366 000 t (Vianna 2019, p. 35; documento primário não lido).
6. **Agregados praticantes:** AFSUN (bairros de baixa renda; 22%, ano a reconfirmar, via HCP 2); HCP 2014 (Raimundo 2018): ~1 em 5, hortícolas 12,7%, galinhas 12,1%, porcos 0,6%, bovinos 0,3%; SLE: "até 20%" e 22% (sem inquérito citado). Não há série censitária.
7. **Rendimentos e preços:** 1991 (Roth) e 2017 (SLE); pontos isolados, não série.

## Rupturas de definição (não somar nem comparar sem nota)

- **Área:** 7 805 ha (zonas legais 1985) ≠ 47 000 ha (Sumbane: inclui sequeiro familiar) ≠ 12,4/9,7 mil ha (cultivada familiar+privada) ≠ 1 300 ha (ocupada por associações) ≠ ~1 100 ha (Embrapa: hortícolas na estação fresca, inclui Matola) ≠ 8 632 ha (campanha 2024/25: área **acumulada** de ciclos, ~6,6x a física) ≠ 45 mil ha (UCLG: Maputo+Matola, território).
- **Produtores:** membros de associações (11 194) ≠ produtores (14 508, GCM 2016) ≠ "pessoas que dependem" (40 000). KaMubukwana: 1 597 (SLE 2018) vs 2 904 (Vianna 2016); KaTembe: 162 vs 2 165.
- **Fronteira:** 1987 separou Matola de Maputo; Embrapa e UCLG incluem Matola.
- **Sector:** cooperativas (UGC) vs. associações vs. familiar vs. privado, que mudam de peso no tempo.
- **Produção:** colhida (UGC, GZV) vs. comercializada vs. meta; toneladas totais sem cultura; unidades inconsistentes (AIM 2024-04: cereais 236 mil t, total não fecha).

## Fiabilidade

Alta: Tabela 5 de Christie e Tabela 8 do SLE. Média: cifras citadas (40 000 pessoas, 20% dos agregados, PAPAP), sem fonte primária localizada (Sitoe 2010, João 2018, White & Hamm 2017). Baixa: previsões de campanha (816 ha de KaMavota em 2024 repete 2018). SLE p. 73 é internamente inconsistente (22 associações/~5 000 produtores no texto vs. 23/2 403 na Tabela 8).

## Harmonização sugerida

Manter **séries separadas por definição**: (A) cooperativas UGC 1981-94; (B) associações 1986-1991-2018-2025 com recorte de distrito; (C) área cultivada GZV 1986-94; (D) metas de campanha 2018-2026 rotuladas "meta". Não calcular razões entre séries A-D.

## Lacunas

Toneladas por cultura (alface, couve, repolho, tomate, cebola, milho), leite, suínos e bovinos observados; todos os anos 1995-2016 e 2019-2023; participação das zonas verdes no abastecimento (nenhum estudo Banco Mundial/IFPRI/MSU com percentagem encontrado; só o 75%/25% do PAPAP e relatos qualitativos de importação da África do Sul).

## Documentos que o utilizador deve obter manualmente (TLS do INE falha; sem espelho encontrado)

1. INE, *Anuário Estatístico da Cidade de Maputo* (2008-2012; 2016-2022), https://www.ine.gov.mz (levantamento 02: view_file/47154).
2. INE, *Anuário Estatístico* nacional (tabela provincial "Cidade de Maputo").
3. INE/MASA, *Censo Agro-Pecuário 1999-2000*, *CAP II 2009-2010* (resultados definitivos; microdados via declaração de confidencialidade, https://microdata.fao.org/index.php/catalog/1586) e *CAP 2023-24*.
4. Censo 2007 e 2017 (PX-Web http://41.94.86.11/Censo2017/ recusou a ligação) — agregados com actividade agro-pecuária, Maputo Cidade.
5. MASA/MADER, TIA/IAI (relatórios por província), e o PAPAP 2017 (Governo da Cidade de Maputo).
6. Sitoe (2010), tese UFRGS; FAO (2012), *Growing Greener Cities in Africa*; AFSUN 4 e 20 (downloads devolveram HTML); dossier mozambiquehistory MZ-0163 (PDF zipado de recortes 1984-94).
