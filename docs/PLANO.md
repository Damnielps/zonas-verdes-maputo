# Zonas verdes de Maputo — artigo científico + site interativo

> O levantamento sobre os planos atualmente em vigor ainda está em curso. Ele alimenta o conteúdo da seção 5 (planos atuais), não muda a abordagem.

## Contexto

Pasta do projeto vazia (`zonas.verdes.maputo/`), sem git. Objetivo: produzir, em português, (1) um artigo científico e (2) um site interativo sobre a evolução histórica das zonas verdes (cintura agrícola periurbana) de Maputo e seu papel em agricultura urbana, redução da pobreza, segurança alimentar e serviços ambientais.

Requisitos do usuário:
- Revisão bibliográfica aprofundada, com ênfase em agricultura urbana em cidades africanas.
- Painel evolutivo por imagens orbitais nos anos censitários de Moçambique (1980, 1997, 2007, 2017) e intercensitários quinquenais, até o presente (2026).
- Tensões e conflitos de uso do solo (expansão urbana sobre áreas agrícolas).
- Números da produção agropecuária urbana ao longo do período.
- Comparações com outros países africanos e casos selecionados em outros continentes.
- História dos planos diretores / planos de estrutura de Lourenço Marques (colonial) e de Maputo, com imagens dos planos como ilustrações.
- Como os planos atualmente em vigor ou em elaboração tratam a agricultura urbana e as zonas verdes.

Decisões tomadas com o usuário:
- Artigo: DOCX + PDF, ABNT (NBR 6022, 6023, 10520), ~9–12 mil palavras.
- Site: estático, sem build, publicado em GitHub Pages; licença MIT; DOI via Zenodo vinculado ao ORCID 0000-0002-6632-3991.
- Imagens: classificação própria + validação cruzada com produtos prontos.
- Identidade visual: Sistema Ardósia.

## Convenções reaproveitadas dos projetos irmãos

- Pipeline numerado em Python com uv, como `emendas-pix-igrejas/scripts/00_ambiente.sh` … `rodar_cadeia.sh`; scripts rodam com `python3 -I`.
- Site vanilla sem build, com dados embutidos por script, como `emendas-pix-igrejas/site/`; mapa em MapLibre GL com versão e `integrity` fixos, como `estratetia.2turno/chuva.js`.
- Ardósia: copiar `ardosia.css` e `palette.py` (`apply_ardosia()`) da skill `anthropic-skills:ardosia-brand-guidelines` sem alterar; nenhum hex literal em CSS novo; DOCX via `scripts/ardosia_docx.js` da skill (docx-js).
- Publicação: `CITATION.cff`, `.zenodo.json` e `.github/workflows/publicar.yml` com `workflow_dispatch`, como em `atlas-migração/`; varredura pré-publicação de caminhos locais, como `perfil.gov/scripts/checar-build.mjs`.
- README em português com seções Entregas, Reproduzir, Publicar; `docs/METODOLOGIA.md`.

## Orquestração entre modelos

Sessão principal em Opus 5.5 (trocar o modelo desta sessão logo após a aprovação do plano, antes de qualquer execução). Ela orquestra, decide e redige; o trabalho volumoso vai para subagentes com modelo mais barato. Agentes definidos em `.claude/agents/*.md` com `model` no frontmatter, como em `atlas-migração/.claude/agents/`.

| Agente | Modelo | Tarefas |
|---|---|---|
| Sessão principal | Opus 5.5 | Desenho metodológico, legenda de classes e critérios de validação; interpretação dos resultados; redação de introdução, discussão comparada e conclusões; integração e revisão final do artigo e do site; decisões sobre lacunas e harmonização de definições. |
| `implementacao` | Sonnet 5.5 | Scripts do pipeline (download, índices, Random Forest, transições, figuras); código do site (HTML/JS/CSS, MapLibre, gráficos); geração do DOCX. |
| `leitura` | Sonnet 5.5 | Leitura de bibliografia em lotes temáticos paralelos, com fichamento estruturado (tese, método, números com página, citações curtas) gravado em `fontes/fichas/`; extração de dispositivos dos planos; rascunho de seções descritivas (métodos, perfis dos casos comparados). |
| `mecanico` | Haiku 5.5 | Baixar arquivos; conferir que DOIs e ligações resolvem; formatar referências ABNT a partir de `referencias.csv`; transcrever tabelas para CSV; converter imagens para WebP; montar `CREDITOS.md`; varredura pré-publicação. |
| `auditoria` | Opus 5.5 (contexto novo) | Uma passada ao fim de cada entrega: números do artigo e do site contra `resultados.json`; cada afirmação citada contra a ficha da fonte; coerência das áreas classificadas; revisão do código do pipeline. |

Alternância automática:
- A troca de modelo é feita pela própria orquestração, sem intervenção do usuário: cada delegação sai da sessão principal já com o modelo da tabela, escolhido pelo tipo de tarefa (parâmetro `model` da ferramenta de agentes e `model` no frontmatter de `.claude/agents/*.md`). O usuário não precisa trocar de modelo nem aprovar cada roteamento.
- Agentes criados em `.claude/agents/` nesta sessão podem só ser carregados numa sessão nova; até lá, a sessão principal delega a agentes genéricos com o mesmo briefing e o `model` explícito, com efeito idêntico.
- A própria sessão principal passa a Opus 5.5 logo após a aprovação, por `set_session_model` (uma única confirmação do usuário).
- O escalonamento abaixo também é automático, e cada delegação fica registrada em `docs/ORQUESTRACAO.md` (tarefa, modelo, resultado da conferência) para se poder avaliar o custo-benefício ao fim.

Regras:
- Cada tarefa delegada recebe um briefing autossuficiente (objetivo, arquivos de entrada, esquema do arquivo de saída, critério de pronto) e grava o resultado em arquivo; a sessão principal recebe só o resumo.
- Lotes independentes rodam em paralelo; dois agentes nunca escrevem no mesmo arquivo.
- A sessão principal confere por amostragem o que os subagentes entregam antes de usar; nada entra no artigo sem ficha verificada.
- Escalonamento: tarefa que falhar na conferência duas vezes sobe um nível (Haiku → Sonnet → sessão principal).
- Sem fluxo de dezenas de agentes: da ordem de 4–6 lotes de leitura, 3–4 de implementação e tarefas mecânicas pontuais.

## Estrutura do projeto

```
zonas.verdes.maputo/
  README.md  LICENSE (MIT)  CREDITOS.md  CITATION.cff  .zenodo.json  .gitignore
  scripts/        00_ambiente.sh … 14_*.py, rodar_cadeia.sh, ardosia_palette.py
  fontes/         referencias.csv (bibliografia com status de verificação)
                  series_producao.csv, marcos.csv, planos.csv, casos_comparados.csv
  dados/raw/      rasters e vetores baixados (gitignored)
  dados/proc/     tabelas de áreas, transições, resultados.json
  dados/fig/      figuras PNG/SVG do artigo
  artigo/         artigo.md (fonte) → artigo.docx, artigo.pdf
  site/           index.html, assets/ (ardosia.css, js), dados/*.json,
                  img/painel/<ano>_{cor,classe}.webp, img/planos/*
  docs/           METODOLOGIA.md
  .github/workflows/publicar.yml
```

## Etapas

### 1. Ambiente e limites
- `uv venv` (Python 3.14; rasterio, pyogrio, geopandas, pystac-client, planetary-computer, odc-stac, rioxarray, scikit-learn, matplotlib têm wheels; recuar para 3.13 se algum import falhar).
- Área de estudo: bbox 32,40–32,75 E / 26,10–25,75 S (Cidade de Maputo + margem da Matola no Infulene + sul de Marracuene).
- Limites: HDX COD-AB `cod-ab-moz` v02 (7 distritos municipais, 64 bairros; Matola inclui "Vale de Infulene" e "Zona Verde"). OSM via Overpass: `landuse=farmland/allotments/orchard`, Estrada Circular, ponte Maputo–KaTembe.

### 2. Painel orbital (14 épocas)
Fonte principal: composições anuais GeoMAD do Digital Earth Africa, tile x213y043, leitura anônima por HTTPS. Reserva: cenas de estação seca Landsat C2 L2 path 167/row 078 no Planetary Computer (token SAS anônimo).

| Época | Fonte | Observação |
|---|---|---|
| 1980 (censo) | Landsat MSS jun–jul 1979 (60 m, 4 bandas) | 1980 sem cena útil; declarar o desvio |
| 1985 | GeoMAD 1985 se banda COUNT for aceitável; senão TM 1984-06-01 | cobertura rala nos anos 1980 |
| 1990, 1995, 1997 (censo), 2000, 2005, 2007 (censo) | GeoMAD `gm_ls5_ls7_annual` | |
| 2010 | GeoMAD 2010; conferir faixas do Landsat 7; reserva TM 2008/2011 | ano fraco |
| 2015, 2017 (censo), 2020 | GeoMAD `gm_ls8_annual` (+ Sentinel-2 10 m a partir de 2017) | |
| 2025 | GeoMAD `gm_ls8_ls9_annual` e `gm_s2_annual` | |
| 2026 (presente) | cenas Landsat 9 / Sentinel-2 da estação seca de 2026 | sem composição anual ainda |

Para cada época: composição em cor verdadeira e falsa-cor, NDVI, e mapa classificado. Exportar WebP georreferenciado para o site (a 30 m o bbox tem cerca de 1 200 × 1 300 px).

### 3. Classificação e validação
- Classes: área construída; agricultura de baixada/hortícola (zonas verdes); agricultura de sequeiro e machambas mistas; vegetação natural e mangal; zonas húmidas; água; solo exposto/areia.
- Método: Random Forest por época sobre bandas, índices (NDVI, NDBI, MNDWI, BSI), medidas MAD do GeoMAD e relevo (Copernicus DEM 30 m: cota e declive, pois as zonas verdes ocupam baixadas). Amostras de treino a partir de píxeis estáveis onde WorldCover 2021, GLAD 2020, IO LULC e OSM concordam, propagadas para trás por estabilidade espectral e conferidas visualmente. MSS 1979 classificado à parte, com legenda reduzida.
- Validação: (a) amostra estratificada interpretada visualmente em épocas-chave, com matriz de confusão e áreas ajustadas (Olofsson et al. 2014); (b) concordância do construído com GHSL (1975–2025) e WSF Evolution (1985–2015); (c) agricultura contra GLAD cropland (2000–2020) e ESA CCI (1992–2022); (d) mapas de uso do solo de Henriques & Correia (1964, 1973, 1982, 1991, 2001, Zenodo) como linha de base pré-satélite e controle independente.
- Limitação a declarar: hortas pequenas são subpíxel a 30 m; a classe de sequeiro confunde-se com pousio e capim. Incertezas reportadas por época.

### 4. Áreas, transições e conflitos
- Área por classe × época × distrito/bairro; matrizes de transição entre épocas; taxa anual de conversão agricultura → construído.
- Perímetros de referência das zonas verdes: Vale do Infulene, Mahotas–Costa do Sol–Laulane–Albazine (KaMavota), KaTembe; quando a imagem do plano de 1985 for georreferenciável, comparar com os 5 230 ha "permanentes".
- Focos de conflito: conversão ao longo da Estrada Circular (2012–2018), Costa do Sol, Zimpeto/Magoanine, KaTembe pós-ponte (2018); sinais de salinização (queda de NDVI nas baixadas costeiras); cheias de 2000, 2013, 2023.
- Cada conflito mapeado é cruzado com fonte documental (Roth et al. 1995; Dürrnagel et al. 2022; Muchanga & Almeida 2025; Beja da Costa & Mazzolini 2021; SLE 2019; imprensa).

### 5. Planos urbanísticos
- Cronologia (`fontes/planos.csv`), com o fio condutor da cintura periurbana reservada em cada plano:
  - 1876 Hall (enxugo do pântano); 1887 Plano de Ampliação, Araújo (malha ortogonal).
  - 1955 Plano Geral de Urbanização, Aguiar: "zona de reserva" e "zona rural de protecção" de ≥ 5 km em torno da cidade — primeira cintura formal.
  - 1969–72 Plano Director de Urbanização, Azevedo: escala regional, levantamento do caniço, expansão para Mahotas e Machava, corredor verde de drenagem.
  - 1979 Reunião Nacional das Cidades: zonas verdes incorporadas à cidade como base do autoabastecimento; 1980 Gabinete das Zonas Verdes.
  - 1985 Plano de Estrutura (INPF): "zona agropecuária" no Infulene e junto à Costa do Sol; nunca aprovado formalmente.
  - 1999 PEAMM (metropolitano; nunca aprovado); 2008 PEUMM ("Espaço para Actividade Agrícola" e "Estrutura Ecológica"); PGU KaTembe; JICA 2014.
  - Fontes-base: Pimentel (2013, Univ. Évora, lida na íntegra), HPIP, Pinto et al. (2022), Raposo & Jorge, Mendonça (2018), Reyes Tejada et al. (2024).
- Imagens em `site/img/planos/` e como figuras do artigo, em três níveis de direitos:
  - Reprodução segura (domínio público ou licença aberta, Wikimedia Commons): carta de 1893 (Couceiro), Planta geral de 1925 e mapa de 1929 (CFLM), carta do Almirantado de 1951, fotografia aérea de 1958 (CC BY-SA), e mapas próprios gerados do conjunto LUCO 1964–2001 (CC BY 4.0).
  - Direitos incertos ou reservados (planta de 1940 da BNP; Aguiar 1955; Azevedo 1969; plano de 1985; PEAMM 1999; PEUMM 2008; JICA 2014): por decisão do usuário, reproduzir as peças com a devida citação da fonte, como citação para fins científicos. Legenda de cada figura com autor, data, instituição detentora e fonte de onde a imagem foi obtida (por exemplo "apud Pimentel, 2013, fig. 24"), mais ligação ao original.
  - Essas imagens ficam fora da licença MIT e do que o `CITATION.cff` declara como obra do autor: `CREDITOS.md` lista cada uma (fonte, autor, data, detentor, situação de direitos) e o `LICENSE`/README dizem que material de terceiros mantém os direitos dos titulares. Resolução limitada ao necessário para leitura.
  - Complementar com esquemas próprios quando a peça original for ilegível na escala do site (zona de protecção de 1955, zona agropecuária de 1985, espaço agrícola de 2008).
  - Imagens de blogues sem fonte identificável: só ligação.
- Seção própria sobre os planos em vigor: categorias de uso agrícola, regras de edificação, áreas mapeadas, contradições com infraestrutura e fiscalização, com citações curtas e página/artigo.
- Onde a imagem permitir, georreferenciar o zoneamento (1985, PEUMM 2008) e sobrepor ao uso do solo classificado: "planejado × ocorrido".

### 6. Bibliografia e séries estatísticas
- Regra de integridade: só entra no artigo referência aberta e conferida (DOI resolvido ou documento lido); `fontes/referencias.csv` guarda status, ligação e o que foi lido. Nada citado de memória.
- Leitura em profundidade por subagentes, em lotes temáticos: (a) Maputo e zonas verdes (Christie 1996; Sheldon; Roth et al. 1995; SLE 2019; Paganini; Raimundo, McCordic & Chikanda 2018; Reyes Tejada et al. 2024; Melo & Jenkins 2021; Andersen, Jenkins & Nielsen 2015; Niquice); (b) agricultura urbana africana (Mougeot; Egziabher et al.; Maxwell; Prain et al.; Zezza & Tasciotti 2010; Crush, Hovorka & Tevera 2011; Frayne et al. 2014; Poulsen et al. 2015; Drechsel; Lwasa et al.; Badami & Ramankutty 2015; Davies et al. 2021; Battersby); (c) benefícios e riscos ambientais (drenagem e retenção de cheias, ilha de calor, reuso de águas residuais, metais pesados, mangal); (d) casos comparados; (e) história do planeamento.
- Casos comparados: África — Dar es Salaam, Kampala, Nairobi, Acra/Kumasi, Lusaka ou Harare, Cidade do Cabo; outros continentes — Havana, Rosario, Belo Horizonte/São Paulo, Hanói, e um caso europeu ou norte-americano. Quadro comparativo com indicadores homogêneos quando existirem.
- `fontes/series_producao.csv`: cada número com fonte, página, ano e definição espacial. Séries viáveis: cooperativas/associações, membros e hectares (1980–86; 2017–25); área das zonas verdes; parcela de agregados praticantes (2008, 2014). Lacunas conhecidas: toneladas por cultura e pecuária (só 1981, 1993–94 e 2024 duvidoso), leite e ovos. Tentar preencher com anuários do INE (Cidade de Maputo 2008–2012 e 2016–2022), CAP 2009–10 e 2023–24, FAO *Growing Greener Cities* (2012), relatórios GZV/UGC citados em Christie.
- As definições de área divergem (171 ha em 1981; 5 230 ha no plano de 1985; 47 000 ha em Sumbane 1988; ~1 300 ha hoje): harmonizar explicitamente e confrontar com a área classificada.
- O certificado TLS de ine.gov.mz falha; não contornar a verificação. Usar espelhos ou pedir ao usuário que baixe os anuários.

### 7. Artigo
- `artigo/artigo.md` como fonte única; números lidos de `dados/proc/resultados.json` para não divergir do site.
- Estrutura: resumo/abstract e palavras-chave; introdução; referencial (agricultura urbana em África; pobreza e segurança alimentar; serviços ambientais); área de estudo e história (colonial → GZV 1980 → UGC → ajuste estrutural → Lei de Terras → PEUMM → Circular); planos urbanísticos históricos e atuais; materiais e métodos; resultados (painel 1979–2026, transições, conflitos, produção); discussão comparada; conclusões e implicações de política; referências ABNT.
- Saídas: DOCX com `ardosia_docx.js` (tipografia Ardósia, citações autor-data e referências ABNT) e PDF exportado do Word (reserva: HTML impresso por Chrome headless, padrão de `emendas-pix-igrejas/scripts/06_relatorio.py`).
- Figuras em matplotlib com `apply_ardosia()`, seguindo a skill `dataviz`.

### 8. Site
- Página única com seções: abertura e números-chave; linha do tempo (marcos legais, cheias, obras, planos com imagens); painel evolutivo (seletor de ano e comparação lado a lado, alternância imagem/classificação, limites de bairros); áreas por classe ao longo do tempo; mapa de conversão agricultura → urbano por bairro e focos de conflito; produção e produtores; planos históricos (galeria) e planos atuais; quadro comparativo de cidades; metodologia, dados para download, como citar, bibliografia.
- MapLibre GL com as imagens do painel como fontes `image` georreferenciadas (sem servidor de tiles); gráficos em D3/Observable Plot; `ardosia.css` verbatim; modo claro/escuro; responsivo.
- Pré-visualização local por `.claude/launch.json` (servidor estático).

### 9. Publicação
- `git init`, `LICENSE` MIT, `CREDITOS.md` para material de terceiros (não coberto pela MIT), `CITATION.cff` e `.zenodo.json` com o ORCID, workflow de Pages com `workflow_dispatch` e varredura de caminhos locais.
- Criar o repositório remoto, dar push e cunhar o DOI no Zenodo só com confirmação explícita do usuário na hora; o nome do repositório é definido nesse momento.

## Verificação

- Pipeline: `scripts/rodar_cadeia.sh` roda do zero; soma das áreas por classe igual à área do bbox em todas as épocas; série de construído monotônica dentro da incerteza e coerente com GHSL/WSF; matrizes de confusão e áreas ajustadas reportadas.
- Séries: toda linha de `series_producao.csv` e toda referência de `referencias.csv` com fonte verificada; script confere que todo DOI resolve e que toda citação do artigo tem entrada na lista e vice-versa.
- Artigo: abrir o DOCX no Word, conferir figuras, tabelas e referências ABNT; números do texto idênticos a `resultados.json`.
- Site: abrir no navegador embutido, percorrer cada seção, testar o seletor de anos e a comparação, modo escuro e largura de celular; console sem erros; todas as imagens de planos com crédito visível.
- Pré-publicação: varredura sem caminhos locais nem dados brutos em `site/`; `CREDITOS.md` completo.
