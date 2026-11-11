# L6 — tentativas de acesso aberto (segunda passagem)

Rotas aplicadas a todos os alvos com DOI: Unpaywall (e-mail placeholder), OpenAlex (oa_url, locations), Semantic Scholar (openAccessPdf), Crossref (dados bibliográficos), repositórios institucionais apontados por esses serviços. Sem Sci-Hub/LibGen, sem contornar desafios anti-robô, sem `curl -k`. scholar.archive.org devolveu "Session Verification" (verificação anti-robô; não contornada). CORE exige chave de API (não usada). Cópias em `dados/raw/biblio/L6/`.

## Lidos integralmente nesta passagem (fichas reescritas)
| Alvo | Rota | Resultado |
|---|---|---|
| Paganini & Lemke 2020 | Unpaywall/OpenAlex -> Coventry Pure (post-print) | VERIFICADO (páginas do manuscrito) |
| Halder et al. 2018 (SLE S 275) | busca na API DSpace do edoc HU Berlin (título "Perspectives of Urban Agriculture in Maputo and Cape Town"; DOI 10.18452/18944) | VERIFICADO; também há versão portuguesa DOI 10.18452/19172 |
| AFSUN n. 4 (Crush, Hovorka, Tevera 2010) | afsun.org/.../AFSUN_4.pdf (via OpenAlex) | VERIFICADO (ficha crush_2010) |
| AFSUN n. 1 (Crush & Frayne 2010) | afsun.org/.../AFSUN_1.pdf | VERIFICADO (ficha nova crush_2010_afsun1) |
| AFSUN n. 20 (Raimundo, Crush, Pendleton 2014) | afsun.org/.../AFSUN20.pdf | VERIFICADO (ficha raimundo_2014) |
| Warren et al. 2015 | Semantic Scholar -> LSHTM Research Online (manuscrito submetido .doc) | lido, mas status PARCIAL: versão não final, números internamente inconsistentes |

## Não abertos
- Melo & Jenkins 2021 (JSAS): Unpaywall/OpenAlex/S2 = fechado; só T&F. Sem repositório.
- Andersen, Jenkins & Nielsen 2015 p.1 e p.2: fechados (Liverpool UP); só registros Pure (Aarhus: pure.au.dk) sem arquivo. Crossref: p.1 = v.37 n.3 p.329-350; p.2 = v.37 n.4 p.423-443 (cabeçalho da ficha corrigido).
- Jenkins 2000 (Cities): fechado (Elsevier); sem cópia OA.
- Sheldon 1999 (Lusotopie): página de registro abre; PDF em persee.fr protegido por altcha; não contornado.
- Paganini 2021 (tese Hohenheim): hohPublica atrás de Anubis (verificação anti-robô); não contornado. OpenAlex sem localização alternativa.
- Niquice 2025 (tese) e Niquice-Janeiro et al. 2023 (Agriculture 13(11):2158, DOI 10.3390/agriculture13112158; OA gold): mdpi.com devolve 403 (Akamai) a curl e a WebFetch; resolver.tudelft.nl e repository.tudelft.nl recusam conexão; DOAJ com Cloudflare. A cópia em dados/raw/biblio/L1/niquice2023_agriculture.pdf é HTML de erro, não PDF.
- Beja da Costa & Mazzolini 2021: OA verde em hdl.handle.net/10400.5/21981 (repositório ISA/ULisboa), mas protegido por Anubis. Crossref: AGR 40(3):231-248, título "Maputo's coastline in mutation..." (cabeçalho corrigido).
- Sitoe & Sitole 2019 (AgEcon record 357701) e Boucher et al. RP 121: ageconsearch.umn.edu responde 202 sem conteúdo (desafio anti-robô); RP 123 (Roth, Boucher, Francisco) está disponível mas já é outra ficha. RP 121 não identificado com certeza.
- Cruz e Silva 2006 (Verso): capítulo de livro, sem versão OA localizada.
- Zezza & Tasciotti 2010: Unpaywall fechado; repositórios SOAS (eprints.soas.ac.uk sem resposta) e Greenwich GALA ("Full text not available").
- Poulsen et al. 2015: fechado, sem repositório.
- Crush, Hovorka & Tevera 2011: repositório UWC (hdl 10566/1008) só tem licença, sem arquivo; CiteSeerX indisponível.
- Frayne, McCordic & Shilomboleni 2014: fechado.
- Davies et al. 2021: OA híbrido CC-BY, mas sciencedirect.com devolve 403/desafio (não contornado).
- Badami & Ramankutty 2015: fechado.
- Maxwell 1995: CGSpace/IFPRI tem registro (hdl 10568/171536) sem arquivo (bundles vazios, acesso restrito).
- Ellis & Sumberg 1998: UEA eprints "Full text not available".
- Orsini et al. 2013: HAL em hal-01201393 e CIRAD agritrop 571129 (PDF embargado, HTTP 401); Bologna CRIS com Cloudflare.
- Drechsel & Dongus 2010: CGSpace registro sem arquivo (bundles vazios).
- Lee-Smith 2010 (também alvo da seção "Casos"): SAGE 403; Semantic Scholar marca "bronze" mas o PDF da SAGE é bloqueado.
- Simatele & Binns 2008: fechado; Manchester Research Explorer sem arquivo.
- Bryld 2003: fechado.
- Thornton, Nel & Hampwaye 2010: "bronze" na T&F, PDF 403 a curl.
- Halloran & Magid 2013: fechado.
- Altieri et al. 1999: Springer, fechado. Crossref conferido: 7 autores, v.16 n.2 p.131-140.
- Obuobie et al. 2006 (IWMI): link do iwmi.cgiar.org devolve casca HTML; AgEcon (record 137958) 202 anti-robô; CGSpace hdl 10568/17092 sem acesso via API.
- Thapa & Murayama 2008: DOI correto via Crossref = 10.1016/j.landusepol.2007.06.004 (Land Use Policy 25(2):225-239, "Land evaluation for peri-urban agriculture using AHP and GIS techniques: a case study of Hanoi"). Cópia OA em tsukuba.repo.nii.ac.jp/record/17587 devolve HTTP 406 (WAF) a curl.
- Informe Rosario 2022: datos.rosario.gob.ar sem resposta (conexão recusada/timeout).
- Hungry Cities/outros AFSUN (n. 1, 4, 20): obtidos em afsun.org; scholars.wlu.ca devolve 403.

## Correções de cabeçalho (Crossref)
andersen_2015 (329-350; 423-443), bejadacosta_2021 (título e páginas), paganini_2020 (v.25, n.11-12, p.1000-1020). Demais fichas com DOI conferem em autor, ano, volume, número e páginas (melo_2021, jenkins_2000, zezza, poulsen, crush_2011a, frayne, davies, warren, badami, maxwell, ellis, orsini, drechsel, leesmith, simatele, bryld, thornton, halloran).
