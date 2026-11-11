/* Zonas verdes de Maputo - site estático. Todos os números vêm de window.DADOS (scripts/12_resultados.py). */
(function () {
  "use strict";
  const D = window.DADOS;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const nf0 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const fmt = (x, d) => (x == null || isNaN(x) ? "—" : d === 1 ? nf1.format(x) : nf0.format(x));
  const pct = (x) => fmt(x, 1) + "%";
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const CLS_VAR = { 1: "--viz-2", 2: "--viz-3", 3: "--viz-5", 45: "--viz-muted", 6: "--viz-1", 7: "--viz-6" };
  const corCls = (k) => css(CLS_VAR[k]);
  const NOME = {}; D.classes.forEach((c) => (NOME[c.cod] = c.nome));
  const NOME_CURTO = { 1: "Construído", 2: "Zonas verdes (indicativa)", 3: "Sequeiro e mosaico (indicativa)", 45: "Vegetação não cultivada", 6: "Água", 7: "Solo exposto" };
  const EP = D.epocas.map((e) => e.ano);
  const EP_Q = EP.filter((a) => a !== 1979);
  const EPINFO = {}; D.epocas.forEach((e) => (EPINFO[e.ano] = e));
  const SUBST = new Set(D.epocas.filter((e) => e.marca_cena_substituta).map((e) => e.ano));
  const reg = [];
  function chart(fn) { reg.push(fn); fn(); }
  function redraw() { reg.forEach((f) => f()); }
  let rt; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(redraw, 150); });
  const largura = (host) => Math.max(260, Math.floor(host.getBoundingClientRect().width - 28));

  /* ---------------------------------------------------------------- tema */
  const root = document.documentElement;
  function setTema(t) { root.setAttribute("data-theme", t); try { localStorage.setItem("zv-tema", t); } catch (e) {} }
  (function () {
    let t = null; try { t = localStorage.getItem("zv-tema"); } catch (e) {}
    if (!t) t = window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    setTema(t);
    $("#btnTema").addEventListener("click", () => { setTema(root.getAttribute("data-theme") === "dark" ? "light" : "dark"); redraw(); });
  })();

  /* ---------------------------------------------------------------- abertura */
  (function () {
    const k = D.kpi; const F = k.faixas;
    const rg = (v) => `${fmt(v[0], 1)}–${fmt(v[1], 1)}%`;
    const seta = ' <span class="seta">→</span> ';
    const ch = k.construido_crescimento_pct;
    const tiles = [
      [`Área construída da cidade, 1985${"→"}${k.ano_final}`, `+${fmt(k.construido_crescimento_min_pct)}% a +${fmt(k.construido_crescimento_max_pct)}%`, `Crescimento segundo três estimativas: GHSL +${fmt(ch.ghsl)}%, classificação bruta +${fmt(ch.bruto)}%, pós-processada +${fmt(ch.final)}%. Cidade (6 distritos continentais).`],
      ["Construído nas zonas verdes permanentes do plano de 1985", `${rg(F.zv_permanentes["1985"])}${seta}${rg(F.zv_permanentes["2025"])}`, "Faixa (mínimo–máximo das três estimativas) da parcela construída do perímetro, 1985 e 2025."],
      ["Construído na zona agropecuária do PEUMM 2008", `${rg(F.agropecuaria["2010"])}${seta}${rg(F.agropecuaria["2025"])}`, "Faixa (mínimo–máximo das três estimativas) da parcela construída do perímetro, 2010 e 2025."],
      ["Construído nas baixadas (altitude < 15 m, TPI < 0)", `${rg(F.baixadas["1985"])}${seta}${rg(F.baixadas["2025"])}`, "Faixa (mínimo–máximo das três estimativas) da parcela construída do perímetro, 1985 e 2025."],
      ["Conflitos documentados", `${fmt(k.conflitos_documentados)}`, `${fmt(k.conflitos_documentados)} episódios documentados (${fmt(k.conflitos_georreferenciados)} com localização).`],
    ];
    $("#kpis").innerHTML = tiles.map((t) => `<div class="ard-card kpi"><p class="ard-kpi-label">${t[0]}</p><p class="ard-kpi-value num">${t[1]}</p><p class="kpi-sub">${t[2]}</p></div>`).join("");
    $("#kpiNota").textContent = "Os indicadores são faixas entre três estimativas (GHSL, classificação bruta e classificação pós-processada); o ano final é 2025, porque a composição de 2026 é atípica (só maio a agosto). Os perímetros são definidos independentemente da classificação agrícola. A área de zonas verdes mapeada (classe 2) não é destaque porque a validação cega de 2020 não a separa com segurança da vegetação não cultivada.";
  })();

  /* ---------------------------------------------------------------- lightbox */
  const IMG = {}; D.imagens.forEach((i) => (IMG[i.arquivo] = i));
  const DIREITOS = { dominio_publico: "domínio público", reproducao_com_citacao: "reprodução com citação (direitos do titular original)" };
  function credito(i) {
    const p = [];
    if (i.autor) p.push(i.autor);
    if (i.data) p.push(i.data);
    let s = p.join(", ");
    if (i.detentor) s += `. Detentor original: ${i.detentor}`;
    s += `. Situação de direitos: ${DIREITOS[i.licenca] || i.licenca}`;
    if (i.apud) s += `. Apud ${i.apud}${i.pagina ? ", " + i.pagina : ""}`;
    else if (i.fonte) s += `. Fonte: ${i.fonte}`;
    if (i.credito_sugerido) s += `. ${i.credito_sugerido}`;
    return s + ".";
  }
  const lb = $("#lightbox");
  function abre(arq) {
    const i = IMG[arq]; if (!i) return;
    $("#lbImg").src = "img/planos/" + i.arquivo; $("#lbImg").alt = i.titulo + (i.data ? " (" + i.data + ")" : "");
    $("#lbCred").innerHTML = `<b>${esc(i.titulo)}</b>${i.data ? " (" + esc(i.data) + ")" : ""}. ${i.legenda ? esc(i.legenda) + " " : ""}${esc(credito(i))}`;
    if (lb.showModal) lb.showModal(); else lb.setAttribute("open", "");
  }
  $("#lbFechar").addEventListener("click", () => lb.close());
  lb.addEventListener("click", (e) => { if (e.target === lb) lb.close(); });
  function thumb(arq) {
    const i = IMG[arq]; if (!i) return "";
    const mini = i.mini ? arq.replace(".webp", "_mini.webp") : arq;
    return `<button type="button" class="thumb" data-lb="${esc(arq)}" aria-label="Ampliar: ${esc(i.titulo)}"><img src="img/planos/${esc(mini)}" alt="${esc(i.titulo)}${i.data ? ", " + esc(i.data) : ""}" loading="lazy"><span>${esc(i.titulo)}</span></button>`;
  }
  document.addEventListener("click", (e) => { const b = e.target.closest("[data-lb]"); if (b) abre(b.dataset.lb); });
  const imgsPor = (prefixo) => D.imagens.filter((i) => i.arquivo.startsWith(prefixo)).map((i) => i.arquivo);

  /* ---------------------------------------------------------------- linha do tempo */
  (function () {
    const THUMBS = { "1876-12": ["1876_hall"], "1887-12": ["1887_araujo"], "1955": ["1955_"], "1972": ["1969_"], "1985": ["1985_"], "1999": ["1999_"], "2008-12-10": ["2008_"], "2014-03": ["2014_"] };
    const tipos = [["todos", "Todos"], ["plano", "Plano"], ["lei", "Lei"], ["politica", "Política"], ["instituicao", "Instituição"], ["obra", "Obra"], ["cheia", "Cheia"]];
    let filtro = "todos";
    const f = $("#tlFiltros");
    f.innerHTML = tipos.map((t) => `<button type="button" class="chip" data-t="${t[0]}" aria-pressed="${t[0] === "todos"}">${t[1]}</button>`).join("");
    const lista = D.marcos.slice().sort((a, b) => String(a.data).localeCompare(String(b.data)));
    function render() {
      const itens = lista.filter((m) => filtro === "todos" || m.tipo === filtro);
      $("#tlLista").innerHTML = itens.map((m) => {
        const th = (THUMBS[m.data] && m.tipo === "plano") ? THUMBS[m.data].flatMap((p) => imgsPor(p)).map(thumb).join("") : "";
        return `<li><div><div class="ano num">${esc(m.ano)}</div><div class="data">${esc(m.data)}</div></div><div><p class="ev"><span class="tipo-pill" data-tipo="${esc(m.tipo)}">${esc(m.tipo_pt)}</span>${esc(m.evento)}</p><p class="meta">Fonte: ${esc(m.fonte_chave)}${m.pagina_ou_url ? " · " + esc(m.pagina_ou_url) : ""}</p>${th ? `<div class="thumbs">${th}</div>` : ""}</div></li>`;
      }).join("") || "<li>Nenhum marco neste filtro.</li>";
    }
    f.addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return; filtro = b.dataset.t; $$("button", f).forEach((x) => x.setAttribute("aria-pressed", x === b)); render(); });
    render();
  })();

  /* ---------------------------------------------------------------- utilitários de gráfico */
  const SYM = [d3.symbolCircle, d3.symbolSquare, d3.symbolTriangle, d3.symbolDiamond, d3.symbolCross, d3.symbolStar];
  const symPath = (i, size) => d3.symbol().type(SYM[i % SYM.length]).size(size || 60)();
  function eixos(g, x, y, w, h, opts) {
    opts = opts || {};
    g.append("g").attr("class", "grade").call(d3.axisLeft(y).ticks(opts.ny || 5).tickSize(-w).tickFormat("")).select(".domain").remove();
    const gx = g.append("g").attr("class", "eixo").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).ticks(opts.nx || 8).tickFormat(d3.format("d")).tickSizeOuter(0));
    const gy = g.append("g").attr("class", "eixo").call(d3.axisLeft(y).ticks(opts.ny || 5).tickFormat((v) => nf0.format(v) + (opts.sufy || "")).tickSize(0).tickPadding(6));
    gy.select(".domain").remove();
    return { gx, gy };
  }
  function tabela(cab, linhas, cap) {
    return `<div class="tab-rolavel"><table>${cap ? `<caption>${esc(cap)}</caption>` : ""}<thead><tr>${cab.map((c, i) => `<th scope="col"${i ? ' class="num"' : ""}>${esc(c)}</th>`).join("")}</tr></thead><tbody>${linhas.map((l) => `<tr>${l.map((c, i) => `<${i ? "td class=\"num\"" : "th scope=\"row\""}>${c == null ? "—" : c}</${i ? "td" : "th"}>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  }
  const altDet = (html, t) => `<details class="alt"><summary>${t || "Ver dados em tabela"}</summary>${html}</details>`;

  /* ---------------------------------------------------------------- envelopes (headline) */
  chart(function figEnv() {
    const host = $("#figEnv");
    const per = D.envelopes_comparacao.perimetros;
    const chaves = ["baixada_<15m_tpi<0", "plano1985_zv_permanentes", "plano1985_zv_provisorias", "peumm2008_agropecuaria"];
    const EPH = EP_Q.filter((e) => e <= 2025);
    const ser = [["ghsl", "GHSL (fração edificada)", "2 3"], ["bruto", "Classificação bruta", "6 3"], ["final", "Classificação pós-processada", ""]];
    const cores = ["--viz-1", "--viz-2", "--viz-3", "--viz-5"].map(css);
    const w0 = largura(host); const cw = Math.max(250, Math.floor((w0 - 12) / (w0 > 760 ? 2 : 1)));
    host.innerHTML = `<h4>Ocupação construída nas zonas agrícolas planejadas e nas baixadas: três estimativas</h4><p class="fig-sub">Parcela (%) de cada perímetro construída, cidade, 1985–2025. Faixa sombreada: mínimo e máximo das três estimativas. Pontilhada: GHSL; tracejada: classificação bruta; contínua: classificação pós-processada. Linhas verticais: 2008 (aprovação do PEUMM) e 2012 (início das obras da Circular). Cada painel tem a sua escala vertical.</p><div class="multiplos" id="multEnv"></div><ul class="legenda" id="legEnv"></ul><p class="nota">O GHSL mede a fração de superfície ocupada por edifícios e por isso é a estimativa mais baixa. O salto de 2005 para 2007 aparece nas duas classificações e não aparece no GHSL (que tem passo de cinco anos): é em parte artefato das composições de imagem. A série pós-processada do construído é não decrescente por construção. A faixa expressa a incerteza entre estimativas, não um intervalo de confiança.</p>`;
    const mult = $("#multEnv", host);
    chaves.forEach((k, i) => {
      const dados = (n) => EPH.map((e) => ({ e, v: per[k].cidade[e]["pct_" + n] }));
      const band = EPH.map((e) => ({ e, lo: per[k].cidade[e].pct_min, hi: per[k].cidade[e].pct_max }));
      const m = { t: 8, r: 10, b: 22, l: 38 }, w = cw, h = 190, iw = w - m.l - m.r, ih = h - m.t - m.b;
      const x = d3.scaleLinear([1985, 2025], [0, iw]); const y = d3.scaleLinear([0, d3.max(band, (d) => d.hi) * 1.1], [ih, 0]).nice(4);
      const div = document.createElement("div");
      const f25 = per[k].cidade["2025"];
      div.innerHTML = `<h5>${esc(per[k].rotulo)}</h5><svg role="img" aria-label="${esc(per[k].rotulo)}: parcela construída em 2025 entre ${fmt(f25.pct_min, 1)}% e ${fmt(f25.pct_max, 1)}% segundo três estimativas" viewBox="0 0 ${w} ${h}"></svg>`;
      mult.appendChild(div);
      const g = d3.select(div).select("svg").append("g").attr("transform", `translate(${m.l},${m.t})`);
      g.append("g").attr("class", "grade").call(d3.axisLeft(y).ticks(4).tickSize(-iw).tickFormat("")).select(".domain").remove();
      g.append("g").attr("class", "eixo").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickValues([1985, 1995, 2005, 2015, 2025]).tickFormat(d3.format("d")).tickSizeOuter(0));
      g.append("g").attr("class", "eixo").call(d3.axisLeft(y).ticks(4).tickFormat((v) => nf0.format(v) + "%").tickSize(0).tickPadding(4)).select(".domain").remove();
      D.envelopes.marcos.forEach((mk) => g.append("line").attr("x1", x(mk.ano)).attr("x2", x(mk.ano)).attr("y1", 0).attr("y2", ih).attr("stroke", css("--ard-text-3")).attr("stroke-dasharray", "3 3").attr("stroke-width", 1));
      g.append("path").datum(band).attr("fill", cores[i]).attr("fill-opacity", 0.18).attr("d", d3.area().x((d) => x(d.e)).y0((d) => y(d.lo)).y1((d) => y(d.hi)));
      ser.forEach((sr) => g.append("path").datum(dados(sr[0])).attr("fill", "none").attr("stroke", cores[i]).attr("stroke-width", 2).attr("stroke-dasharray", sr[2]).attr("d", d3.line().defined((d) => d.v != null).x((d) => x(d.e)).y((d) => y(d.v))));
    });
    $("#legEnv", host).innerHTML = ser.map((sr) => `<li><svg width="34" height="12" aria-hidden="true"><line x1="0" x2="34" y1="6" y2="6" stroke="${css("--ard-text-2")}" stroke-width="2" stroke-dasharray="${sr[2]}"/></svg>${sr[1]}</li>`).join("") + `<li><i class="sw" style="background:${css("--ard-text-3")};opacity:.35"></i>Faixa mín.–máx.</li>`;
    const cab = ["Época"]; chaves.forEach((k) => ["GHSL", "bruta", "pós-proc."].forEach((n) => cab.push(per[k].rotulo + ", " + n + " (%)")));
    host.insertAdjacentHTML("beforeend", altDet(tabela(cab, EPH.map((e) => [e].concat(...chaves.map((k) => ["ghsl", "bruto", "final"].map((n) => fmt(per[k].cidade[e]["pct_" + n], 1))))), "Parcela construída por perímetro e estimativa (cidade)")));
  });

  /* ---------------------------------------------------------------- áreas por classe */
  const ordemEmp = ["1", "2", "3", "7", "6", "45"];
  const sel = $("#selDistrito");
  sel.innerHTML = `<option value="cidade">Cidade (6 distritos)</option>` + Object.keys(D.areas_distrito).filter((n) => n !== "KaNyaka").sort().map((n) => `<option>${esc(n)}</option>`).join("");
  let areasVista = "emp";
  $("#areasVista").addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return; areasVista = b.dataset.v; $$("#areasVista button").forEach((x) => x.setAttribute("aria-pressed", x === b)); figAreas(); });
  sel.addEventListener("change", figAreas);
  const dadosArea = () => (sel.value === "cidade" ? D.areas_cidade : D.areas_distrito[sel.value]);
  function figAreas() {
    const host = $("#figAreas"); const A = dadosArea();
    const eps = EP_Q.filter((e) => A[e]);
    const lab = sel.value === "cidade" ? "cidade" : sel.value;
    $("#notaAreas").innerHTML = `Épocas: 1985 = cena de 1984-06-01; 2010 = cena de 2011-04-09 (abril); 2026 = mediana de maio a agosto; 1979 (MSS) fora das séries. Classes 2 e 3: indicativas (ver validação). LUCO (losangos) cobre cerca de ${fmt(D.luco.pct_cidade_coberta["1982"])}% da cidade: use-o pela forma, não pelo nível. Sobre 1985–2026, as épocas 2005 e 2007 têm salto parcialmente devido às composições.`;
    if (areasVista === "tab") {
      const cab = ["Época"].concat(D.classes.map((c) => NOME_CURTO[c.cod] + " (ha)"));
      host.innerHTML = `<h4>Área por classe, ${esc(lab)} (ha)</h4>` + tabela(cab, eps.map((e) => [e + (SUBST.has(+e) ? "*" : "")].concat(D.classes.map((c) => fmt(A[e][c.cod])))), "Hectares por classe agregada") +
        (sel.value === "cidade" ? `<h4 style="margin-top:16px">LUCO 1964–2001 (% da área classificada pelo LUCO)</h4>` + tabela(["Ano", "Cobertura (% da cidade)"].concat(D.classes.map((c) => NOME_CURTO[c.cod])), D.luco.anos.map((a) => [a, fmt(D.luco.pct_cidade_coberta[a], 1)].concat(D.classes.map((c) => fmt(D.luco.pct_classificada[a][c.cod], 1)))), "Fonte: Henriques, Correia & Rolo (2023)") : "");
      return;
    }
    if (areasVista === "emp") {
      const w = largura(host), h = Math.min(380, Math.max(260, w * 0.5)), m = { t: 10, r: 14, b: 28, l: 52 };
      const iw = w - m.l - m.r, ih = h - m.t - m.b;
      host.innerHTML = `<h4>Uso do solo por classe agregada, ${esc(lab)}</h4><p class="fig-sub">Hectares empilhados; de baixo para cima na mesma ordem da legenda.</p><svg role="img" aria-label="Área empilhada por classe de uso do solo de 1985 a 2026" viewBox="0 0 ${w} ${h}" tabindex="0"></svg><ul class="legenda" id="legEmp"></ul><p class="leitura" aria-live="polite"></p>`;
      const dt = eps.map((e) => Object.assign({ e: +e }, A[e]));
      const st = d3.stack().keys(ordemEmp)(dt);
      const x = d3.scaleLinear([1985, 2026], [0, iw]); const y = d3.scaleLinear([0, d3.max(st[st.length - 1], (d) => d[1])], [ih, 0]).nice();
      const svg = d3.select(host).select("svg"); const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
      eixos(g, x, y, iw, ih, { nx: 6 });
      const area = d3.area().x((d) => x(d.data.e)).y0((d) => y(d[0])).y1((d) => y(d[1]));
      st.forEach((s) => g.append("path").datum(s).attr("d", area).attr("fill", corCls(s.key)).attr("fill-opacity", 0.9).attr("stroke", css("--ard-surface")).attr("stroke-width", 0.8));
      eps.forEach((e) => g.append("circle").attr("cx", x(+e)).attr("cy", ih + 12).attr("r", 3).attr("fill", SUBST.has(+e) ? css("--ard-surface") : css("--ard-text-3")).attr("stroke", css("--ard-text-3")));
      $("#legEmp", host).innerHTML = ordemEmp.slice().reverse().map((k) => `<li><i class="sw" style="background:${corCls(k)}"></i>${NOME_CURTO[k]}</li>`).join("");
      const lei = $(".leitura", host);
      const mostra = (e) => { lei.innerHTML = `<b>${e}</b>${SUBST.has(e) ? " (cena substituta)" : ""}: ` + D.classes.map((c) => `${NOME_CURTO[c.cod]} ${fmt(A[e][c.cod])} ha`).join(" · "); };
      mostra(+eps[eps.length - 1]);
      const idx = (px) => { const a = x.invert(px - m.l); return eps.map(Number).reduce((p, c) => (Math.abs(c - a) < Math.abs(p - a) ? c : p)); };
      svg.on("pointermove", (ev) => mostra(idx(d3.pointer(ev, svg.node())[0])));
      svg.on("keydown", (ev) => { const l = eps.map(Number); const cur = +(lei.dataset.e || l[l.length - 1]); let i = l.indexOf(cur); if (ev.key === "ArrowLeft") i = Math.max(0, i - 1); else if (ev.key === "ArrowRight") i = Math.min(l.length - 1, i + 1); else return; lei.dataset.e = l[i]; mostra(l[i]); ev.preventDefault(); });
      host.insertAdjacentHTML("beforeend", altDet(tabela(["Época"].concat(D.classes.map((c) => NOME_CURTO[c.cod] + " (ha)")), eps.map((e) => [e].concat(D.classes.map((c) => fmt(A[e][c.cod])))), "Hectares por classe")));
      return;
    }
    // linhas por classe (% da área com dado)
    host.innerHTML = `<h4>Parcela de cada classe, ${esc(lab)} (% da área)</h4><p class="fig-sub">Círculos: classificação de 30 m (vazados = cena substituta). Losangos: LUCO 1964–2001 em % da área classificada pelo LUCO${sel.value === "cidade" ? "" : " (disponível só para a cidade inteira)"}. Cada painel tem a sua escala vertical.</p><div class="multiplos" id="mult"></div>`;
    const mult = $("#mult", host); const cw = Math.max(240, Math.min(360, (largura(host) - 28) / (largura(host) > 760 ? 3 : largura(host) > 520 ? 2 : 1)));
    D.classes.forEach((c) => {
      const tot = (e) => D.classes.reduce((s, k) => s + A[e][k.cod], 0);
      const dt = eps.map((e) => ({ e: +e, v: 100 * A[e][c.cod] / tot(e) }));
      const lu = sel.value === "cidade" ? D.luco.anos.map((a) => ({ e: a, v: D.luco.pct_classificada[a][c.cod] })) : [];
      const m = { t: 8, r: 8, b: 22, l: 34 }, w = cw, h = 150, iw = w - m.l - m.r, ih = h - m.t - m.b;
      const x = d3.scaleLinear([1960, 2030], [0, iw]); const y = d3.scaleLinear([0, d3.max(dt.concat(lu), (d) => d.v) * 1.15], [ih, 0]).nice(4);
      const div = document.createElement("div");
      div.innerHTML = `<h5>${NOME_CURTO[c.cod]}</h5><svg role="img" aria-label="${esc(NOME_CURTO[c.cod])}: parcela da área de ${fmt(dt[0].v, 1)}% em 1985 para ${fmt(dt[dt.length - 1].v, 1)}% em 2026" viewBox="0 0 ${w} ${h}"></svg>`;
      mult.appendChild(div);
      const g = d3.select(div).select("svg").append("g").attr("transform", `translate(${m.l},${m.t})`);
      g.append("g").attr("class", "grade").call(d3.axisLeft(y).ticks(4).tickSize(-iw).tickFormat("")).select(".domain").remove();
      g.append("g").attr("class", "eixo").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickValues([1970, 1985, 2000, 2015, 2026]).tickFormat(d3.format("d")).tickSizeOuter(0));
      g.append("g").attr("class", "eixo").call(d3.axisLeft(y).ticks(4).tickFormat((v) => v + "%").tickSize(0).tickPadding(4)).select(".domain").remove();
      g.append("path").datum(dt).attr("fill", "none").attr("stroke", corCls(c.cod)).attr("stroke-width", 2).attr("d", d3.line().x((d) => x(d.e)).y((d) => y(d.v)));
      g.selectAll(null).data(dt).enter().append("circle").attr("cx", (d) => x(d.e)).attr("cy", (d) => y(d.v)).attr("r", 3.2).attr("fill", (d) => (SUBST.has(d.e) ? css("--ard-surface") : corCls(c.cod))).attr("stroke", corCls(c.cod)).attr("stroke-width", 1.5);
      g.selectAll(null).data(lu).enter().append("path").attr("d", d3.symbol().type(d3.symbolDiamond).size(46)()).attr("transform", (d) => `translate(${x(d.e)},${y(d.v)})`).attr("fill", css("--ard-text")).attr("fill-opacity", 0.75);
    });
    host.insertAdjacentHTML("beforeend", altDet(tabela(["Época"].concat(D.classes.map((c) => NOME_CURTO[c.cod] + " (%)")), eps.map((e) => { const t = D.classes.reduce((s, k) => s + A[e][k.cod], 0); return [e].concat(D.classes.map((c) => fmt(100 * A[e][c.cod] / t, 1))); }), "Percentual da área com dado")));
  }
  chart(figAreas);

  /* ---------------------------------------------------------------- conversão */
  chart(function figConv() {
    const host = $("#figConv");
    const iv = D.conversao.intervalos.filter((d) => d.comparavel);
    const w = largura(host), h = Math.min(360, Math.max(260, w * 0.48)), m = { t: 12, r: 10, b: 40, l: 44 };
    const iw = w - m.l - m.r, ih = h - m.t - m.b;
    const x0 = d3.scaleBand(iv.map((d) => d.t0 + "-" + d.t1), [0, iw]).padding(0.18); const x1 = d3.scaleBand(["agri", "zv"], [0, x0.bandwidth()]).padding(0.08);
    const y = d3.scaleLinear([0, d3.max(iv, (d) => d.agri_ha_ano)], [ih, 0]).nice();
    const cA = css("--viz-2"), cZ = css("--viz-3");
    host.innerHTML = `<h4>Conversão de terra agrícola em construído, por ano</h4><p class="fig-sub">Hectares por ano entre épocas consecutivas, cidade. Barras cheias: agricultura (classes 2 e 3, a 3 indicativa); barras hachuradas: classe 2. O intervalo 1985–1990 parte da cena de 1984 e o de 2005–2007 inclui o artefato de composição.</p><svg role="img" aria-label="Barras agrupadas de hectares por ano convertidos de agricultura e de zonas verdes em construído, 1985 a 2026" viewBox="0 0 ${w} ${h}"><defs><pattern id="hach" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" fill="${css("--ard-surface")}"/><rect width="2" height="5" fill="${cZ}"/></pattern></defs></svg><ul class="legenda"><li><i class="sw" style="background:${cA}"></i>Agricultura (2+3) para construído</li><li><svg width="14" height="14" aria-hidden="true"><rect width="14" height="14" fill="url(#hach)" stroke="${cZ}"/></svg>Zonas verdes (2) para construído, indicativo</li></ul>`;
    const g = d3.select(host).select("svg").append("g").attr("transform", `translate(${m.l},${m.t})`);
    g.append("g").attr("class", "grade").call(d3.axisLeft(y).ticks(5).tickSize(-iw).tickFormat("")).select(".domain").remove();
    g.append("g").attr("class", "eixo").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x0).tickFormat((k) => { const [a, b] = k.split("-"); return a + "–" + b.slice(2); }).tickSizeOuter(0)).selectAll("text").attr("transform", "rotate(-35)").style("text-anchor", "end");
    g.append("g").attr("class", "eixo").call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(6)).select(".domain").remove();
    iv.forEach((d) => {
      const k = d.t0 + "-" + d.t1;
      g.append("rect").attr("x", x0(k) + x1("agri")).attr("width", x1.bandwidth()).attr("y", y(d.agri_ha_ano)).attr("height", ih - y(d.agri_ha_ano)).attr("fill", cA);
      g.append("rect").attr("x", x0(k) + x1("zv")).attr("width", x1.bandwidth()).attr("y", y(d.zv_ha_ano)).attr("height", ih - y(d.zv_ha_ano)).attr("fill", "url(#hach)").attr("stroke", cZ).attr("stroke-width", 1);
    });
    const ac = D.conversao.acumulada.find((a) => a.t0 === 1985 && a.t1 === 2026);
    host.insertAdjacentHTML("beforeend", `<p class="leitura">1985–2026: ${fmt(ac.agri_para_construido_ha)} ha de terra agrícola (${pct(ac.agri_pct_inicial)} da área agrícola de 1985) passaram a construído; destes, ${fmt(ac.zv_para_construido_ha)} ha eram classe 2 (${pct(ac.zv_pct_inicial)} da classe 2 de 1985; indicativo).</p>` +
      altDet(tabela(["Intervalo", "Anos", "Agricultura → construído (ha)", "ha/ano", "Classe 2 → construído (ha)", "ha/ano"], iv.map((d) => [`${d.t0}–${d.t1}`, d.anos, fmt(d.agri_para_construido_ha), fmt(d.agri_ha_ano, 1), fmt(d.zv_para_construido_ha), fmt(d.zv_ha_ano, 1)]), "Conversão entre épocas consecutivas")));
  });

  let grupoBairro = "maputo";
  chart(function figBairros() {
    const host = $("#figBairros");
    const dt = D.perda_bairro_top10[grupoBairro];
    const w = largura(host), rowh = 40, m = { t: 6, r: 70, b: 24, l: Math.min(150, w * 0.36) }, h = m.t + m.b + rowh * dt.length;
    const iw = w - m.l - m.r;
    const x = d3.scaleLinear([0, d3.max(dt, (d) => Math.max(d.convertida_construido_ha, -d.variacao_liquida_ha))], [0, iw]).nice();
    const y = d3.scaleBand(dt.map((d) => d.bairro), [0, rowh * dt.length]).padding(0.18);
    const rotM = D.perda_bairro_top10.rotulo_matola;
    host.innerHTML = `<h4>Dez bairros com maior conversão de zonas verdes em construído, 1990–2025</h4><p class="fig-sub">Barra principal: área de classe 2 em 1990 que passou a construído até 2025 (transição 2→1), em hectares. Barra cinzenta: variação líquida da classe 2, apenas indicativa (inclui a passagem para vegetação, que não é interpretável). Base em 1990 porque 1985 usa cena de 1984.</p><div class="grupo" role="group" aria-label="Grupo de bairros"><button type="button" class="chip" data-g="maputo" aria-pressed="${grupoBairro === "maputo"}">Cidade de Maputo</button><button type="button" class="chip" data-g="matola_arredores" aria-pressed="${grupoBairro !== "maputo"}">${esc(rotM)}</button></div><svg role="img" aria-label="Barras horizontais com a área de zonas verdes convertida em construído em dez bairros, com a variação líquida indicativa em cinza" viewBox="0 0 ${w} ${h}"></svg><ul class="legenda"><li><i class="sw" style="background:${css("--viz-3")}"></i>Convertida em construído (2→1), ha</li><li><i class="sw" style="background:${css("--ard-text-3")};opacity:.45"></i>Variação líquida, indicativa (inclui 2→vegetação, não interpretável)</li></ul>`;
    const g = d3.select(host).select("svg").append("g").attr("transform", `translate(${m.l},${m.t})`);
    g.append("g").attr("class", "grade").attr("transform", `translate(0,0)`).call(d3.axisBottom(x).ticks(4).tickSize(rowh * dt.length).tickFormat("")).select(".domain").remove();
    g.append("g").attr("class", "eixo").attr("transform", `translate(0,${rowh * dt.length})`).call(d3.axisBottom(x).ticks(4).tickSizeOuter(0).tickFormat((v) => nf0.format(v)));
    dt.forEach((d) => {
      const y0 = y(d.bairro), bh = y.bandwidth() * 0.58, nl = d.variacao_liquida_ha;
      g.append("rect").attr("x", 0).attr("y", y0).attr("height", bh).attr("width", x(d.convertida_construido_ha)).attr("fill", css("--viz-3"));
      g.append("rect").attr("x", 0).attr("y", y0 + bh + 2).attr("height", y.bandwidth() * 0.3).attr("width", x(Math.max(0, -nl))).attr("fill", css("--ard-text-3")).attr("fill-opacity", 0.45);
      g.append("text").attr("x", -6).attr("y", y0 + y.bandwidth() / 2 + 4).attr("text-anchor", "end").text(d.bairro).style("fill", css("--ard-text"));
      g.append("text").attr("x", x(d.convertida_construido_ha) + 4).attr("y", y0 + bh - 3).text(nf0.format(d.convertida_construido_ha) + " ha");
      g.append("text").attr("x", x(Math.max(0, -nl)) + 4).attr("y", y0 + bh + 2 + y.bandwidth() * 0.3 - 1).style("fill", css("--ard-text-3")).style("font-size", "10px").text((nl < 0 ? "−" : "+") + nf0.format(Math.abs(nl)) + " ha (indicativa)");
    });
    $$("[data-g]", host).forEach((b) => b.addEventListener("click", () => { grupoBairro = b.dataset.g; figBairros(); }));
    host.insertAdjacentHTML("beforeend", altDet(tabela(["Bairro", "Zonas verdes 1990 (ha)", "2025 (ha)", "Convertida em construído (ha)", "Variação líquida, indicativa (ha)"], dt.map((d) => [d.bairro, fmt(d.zv_1990_ha), fmt(d.zv_2025_ha), fmt(d.convertida_construido_ha), fmt(d.variacao_liquida_ha)]), D.perda_bairro_top10.nota)));
  });

  /* conflitos */
  (function () {
    $("#notaConf").textContent = `${D.kpi.conflitos_documentados} casos; ${D.kpi.conflitos_georreferenciados} têm posição aproximada no mapa (local descrito na fonte, não coordenada medida).`;
    $("#listaConf").innerHTML = D.conflitos.map((c) => {
      const per = c.ano_inicio ? c.ano_inicio + (c.ano_fim && c.ano_fim !== c.ano_inicio ? "–" + c.ano_fim : "") : (c.ano_fim ? "até " + c.ano_fim : "ano não indicado");
      return `<li id="conf-${esc(c.id)}"><div class="cab">${esc(c.local)} · ${esc(per)}</div><p class="corpo">${esc(c.descricao_curta)}</p><div class="meta">Tipo: ${esc(c.tipo_pt)}${c.atores ? " · Atores: " + esc(c.atores) : ""}${c.desfecho ? " · Desfecho: " + esc(c.desfecho) : ""} · Fonte: ${esc(c.fonte_chave)}${c.pagina_ou_url ? ", " + esc(c.pagina_ou_url) : ""}</div>${c.georreferenciado ? `<button type="button" class="link-mapa" data-conf="${esc(c.id)}">Ver no mapa</button>` : `<div class="meta">Sem posição precisa na fonte.</div>`}</li>`;
    }).join("");
  })();

  /* ---------------------------------------------------------------- planejado × ocorrido */
  (function () {
    const P = D.planos_vs_ocorrido;
    const ordem = ["1", "2", "3", "45", "6", "7"];
    const ENVN = { zv_permanentes: "plano1985_zv_permanentes", zv_provisorias: "plano1985_zv_provisorias", agropecuaria: "peumm2008_agropecuaria" };
    const EC = D.envelopes_comparacao.perimetros;
    function bloco(titulo, chave, eps, intro) {
      const pl = P[chave]; let h = `<p class="grupo-plano">${titulo}</p><p class="nota">${intro}</p>`;
      Object.keys(pl.categorias).forEach((cam) => {
        const c = pl.categorias[cam];
        h += `<h3 style="font-size:17px;margin-top:14px">${esc(c.nome)} <span class="sans nota" style="font-size:12px">(${fmt(c.area_distritos_ha)} ha na cidade, sem água permanente; ${fmt(c.area_mapa_ha)} ha no mapa inteiro)</span></h3>`;
        eps.forEach((e) => {
          const d = c.por_epoca[e].cidade; const tot = ordem.reduce((s, k) => s + d[k], 0) || 1;
          h += `<div class="linhapilha"><span><b>${e}</b> · ${fmt(tot)} ha na cidade</span><div class="pilha" role="img" aria-label="${esc(c.nome)} em ${e}: ` + ordem.map((k) => `${NOME_CURTO[k]} ${fmt(100 * d[k] / tot, 1)}%`).join(", ") + `">` + ordem.map((k) => `<i style="width:${(100 * d[k] / tot).toFixed(2)}%;background:${corCls(k)}" title="${esc(NOME_CURTO[k])}: ${fmt(d[k])} ha (${fmt(100 * d[k] / tot, 1)}%)"></i>`).join("") + `</div><span class="num">${pct(100 * d["1"] / tot)} constr.</span></div>`;
          const ec = ENVN[cam] && EC[ENVN[cam]] ? EC[ENVN[cam]].cidade[e] : null;
          if (ec) h += `<p class="nota" style="margin:2px 0 10px"><b>${e}</b>, parcela construída segundo três estimativas: GHSL ${pct(ec.pct_ghsl)} · classificação bruta ${pct(ec.pct_bruto)} · classificação pós-processada ${pct(ec.pct_final)}.</p>`;
        });
      });
      const rev = pl.zonas_verdes_2025_por_categoria_ha;
      h += `<details class="alt"><summary>Onde estavam as zonas verdes mapeadas em 2025 (indicativo)</summary>${tabela(["Categoria do plano", "Classe 2 em 2025 (ha)"], Object.keys(rev).map((k) => [pl.categorias[k] ? pl.categorias[k].nome : "Fora das zonas vetorizadas", fmt(rev[k])]), `Total na cidade: ${fmt(pl.zonas_verdes_2025_total_cidade_ha)} ha`)}</details>`;
      return h;
    }
    const leg = `<ul class="legenda" style="margin:8px 0">${ordem.map((k) => `<li><i class="sw" style="background:${corCls(k)}"></i>${NOME_CURTO[k]}</li>`).join("")}</ul>`;
    $("#planejadoCorpo").innerHTML = leg + bloco("Plano de Estrutura de 1985 (INPF)", "plano_1985", ["1985", "2025"], "Cada barra é a composição do perímetro segundo a classificação pós-processada da época indicada, na parte dentro dos distritos da cidade; abaixo de cada barra, as três estimativas da parcela construída (a pós-processada, a bruta e o GHSL).") +
      bloco("PEUMM 2008", "plano_2008", ["2010", "2025"], "Comparação com a classificação pós-processada de 2010 (cena de abril de 2011) e de 2025, com as três estimativas da parcela construída.") +
      `<p class="nota nota--aviso" style="margin-top:16px">${esc(P.nota)} A razão de 1985 é dependente da legenda adotada na planta digitalizada. Os valores da literatura sobre zonas verdes de 1985 usam definições espaciais diferentes e estão na seção de produção.</p>`;
  })();

  /* ---------------------------------------------------------------- produção */
  chart(function producao() {
    const host = $("#producaoCorpo"); const PR = D.producao;
    const w0 = host.getBoundingClientRect().width || 600;
    const cw = Math.max(240, Math.min(360, w0 / (w0 > 760 ? 3 : w0 > 520 ? 2 : 1) - 10));
    let h = `<div class="fig"><h4>Cooperativas da União Geral (UGC), 1981–1994</h4><p class="fig-sub">Uma só definição (cooperativas filiadas na UGC de Maputo; ${esc(PR.ugc.fonte)}, ${esc(PR.ugc.pagina)}). Cada painel tem a sua escala.</p><div class="multiplos" id="mUgc"></div>${altDet(tabela(["Ano", "Cooperativas", "Membros", "Área (ha)", "Produção agrícola (t)", "Produção pecuária (t)"], PR.ugc.serie.map((s) => [s.ano, fmt(s.cooperativas), fmt(s.membros), fmt(s.area_ha, 1), fmt(s.producao_agricola_t), fmt(s.producao_pecuaria_t) + (s.parcial && s.parcial.includes("producao_pecuaria_t") ? "*" : "")]), "* valor parcialmente verificado"))}</div>`;
    const grp = [["associacoes_n", "Número de associações", "associações"], ["produtores", "Produtores e agricultores", "pessoas"], ["agregados_pct", "Agregados que praticam agricultura urbana", "% dos agregados / da amostra"]];
    grp.forEach((g) => { h += `<div class="fig" id="f-${g[0]}"><h4>${g[1]}</h4><p class="fig-sub">Cada marcador é uma definição diferente; sem linhas entre pontos. ${g[0] === "agregados_pct" ? "Os valores de 2008, 2017 e 2018 são PARCIAL." : ""}</p><div id="c-${g[0]}"></div><ul class="legenda" id="l-${g[0]}"></ul></div>`; });
    h += `<div class="fig"><h4>Áreas segundo definições distintas</h4><p class="fig-sub">Não são comparáveis entre si. Para referência, a classificação de satélite da cidade dá ${fmt(D.areas_cidade["1985"]["2"])} ha de classe 2 em 1985 e ${fmt(D.areas_cidade["2025"]["2"])} ha em 2025, série indicativa.</p>${tabela(["Definição", "Ano", "Valor (ha)", "Recorte", "Fonte"], PR.areas_por_definicao.map((a) => [esc(a.rotulo), esc(a.ano), esc(a.valor), esc(a.recorte), esc(a.fonte) + (a.pagina ? ", " + esc(a.pagina) : "") + (a.status !== "VERIFICADO" ? " (" + esc(a.status) + ")" : "")]))}</div><p class="nota">${esc(PR.nota)}</p>`;
    host.innerHTML = h;
    [["membros", "Membros", 0], ["area_ha", "Área (ha)", 1], ["producao_agricola_t", "Produção agrícola (t)", 2]].forEach((v) => {
      const m = { t: 8, r: 8, b: 22, l: 44 }, w = cw, hh = 150, iw = w - m.l - m.r, ih = hh - m.t - m.b;
      const dt = PR.ugc.serie.filter((s) => s[v[0]] != null);
      const x = d3.scaleLinear(d3.extent(dt, (d) => d.ano), [0, iw]); const y = d3.scaleLinear([0, d3.max(dt, (d) => d[v[0]])], [ih, 0]).nice(4);
      const div = document.createElement("div"); div.innerHTML = `<h5>${v[1]}</h5><svg role="img" aria-label="${v[1]} das cooperativas UGC de ${dt[0].ano} a ${dt[dt.length - 1].ano}" viewBox="0 0 ${w} ${hh}"></svg>`; $("#mUgc").appendChild(div);
      const g = d3.select(div).select("svg").append("g").attr("transform", `translate(${m.l},${m.t})`);
      g.append("g").attr("class", "grade").call(d3.axisLeft(y).ticks(4).tickSize(-iw).tickFormat("")).select(".domain").remove();
      g.append("g").attr("class", "eixo").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(4).tickFormat(d3.format("d")).tickSizeOuter(0));
      g.append("g").attr("class", "eixo").call(d3.axisLeft(y).ticks(4).tickFormat((t) => nf0.format(t)).tickSize(0).tickPadding(4)).select(".domain").remove();
      g.append("path").datum(dt).attr("fill", "none").attr("stroke", css("--viz-1")).attr("stroke-width", 2).attr("d", d3.line().x((d) => x(d.ano)).y((d) => y(d[v[0]])));
      g.selectAll(null).data(dt).enter().append("circle").attr("cx", (d) => x(d.ano)).attr("cy", (d) => y(d[v[0]])).attr("r", 2.6).attr("fill", css("--viz-1"));
    });
    grp.forEach((gg) => {
      const pts = PR.pontos.filter((p) => p.grupo === gg[0]); const hostc = $("#c-" + gg[0]);
      const w = Math.max(260, hostc.getBoundingClientRect().width || w0 - 28), hh = 210, m = { t: 10, r: 14, b: 24, l: 50 }, iw = w - m.l - m.r, ih = hh - m.t - m.b;
      const num = (p) => (typeof p.valor === "number" ? p.valor : parseFloat(String(p.valor).replace(",", ".")));
      const x = d3.scaleLinear([1984, 2026], [0, iw]); const y = d3.scaleLinear([0, d3.max(pts, num)], [ih, 0]).nice(4);
      hostc.innerHTML = `<svg role="img" aria-label="${esc(gg[1])}: pontos isolados por definição, de ${d3.min(pts, (p) => p.ano_num)} a ${d3.max(pts, (p) => p.ano_num)}" viewBox="0 0 ${w} ${hh}"></svg>`;
      const g = d3.select(hostc).select("svg").append("g").attr("transform", `translate(${m.l},${m.t})`);
      g.append("g").attr("class", "grade").call(d3.axisLeft(y).ticks(4).tickSize(-iw).tickFormat("")).select(".domain").remove();
      g.append("g").attr("class", "eixo").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(6).tickFormat(d3.format("d")).tickSizeOuter(0));
      g.append("g").attr("class", "eixo").call(d3.axisLeft(y).ticks(4).tickFormat((t) => nf0.format(t) + (gg[0] === "agregados_pct" ? "%" : "")).tickSize(0).tickPadding(4)).select(".domain").remove();
      const cores = ["--viz-1", "--viz-2", "--viz-3", "--viz-5", "--viz-6", "--viz-4"].map(css);
      pts.forEach((p, i) => g.append("path").attr("d", symPath(i, 70)).attr("transform", `translate(${x(p.ano_num)},${y(num(p))})`).attr("fill", p.status === "VERIFICADO" ? cores[i % 6] : css("--ard-surface")).attr("stroke", cores[i % 6]).attr("stroke-width", 1.6));
      $("#l-" + gg[0]).innerHTML = pts.map((p, i) => `<li><svg width="14" height="14" aria-hidden="true"><path d="${symPath(i, 70)}" transform="translate(7,7)" fill="${p.status === "VERIFICADO" ? cores[i % 6] : "none"}" stroke="${cores[i % 6]}" stroke-width="1.5"/></svg><span><b>${esc(p.ano)}</b>: ${esc(p.valor)} ${esc(p.unidade)}. ${esc(p.rotulo)}; ${esc(p.recorte)}. ${esc(p.fonte)}${p.pagina ? ", " + esc(p.pagina) : ""}${p.status !== "VERIFICADO" ? " (marcador vazado: " + esc(p.status) + ")" : ""}</span></li>`).join("");
      $("#l-" + gg[0]).style.display = "grid";
    });
  });

  /* ---------------------------------------------------------------- planos */
  (function () {
    const MAPA = { hall_1876: ["1876_"], araujo_1887: ["1887_"], aguiar_1955: ["1955_"], azevedo_1969: ["1969_"], plano_estrutura_1985: ["1985_"], peamm_1999: ["1999_"], peumm_2008: ["2008_"], jica_2014: ["2014_"] };
    $("#planosLista").innerHTML = D.planos.map((p) => {
      const th = (MAPA[p.id] || []).flatMap((x) => imgsPor(x)).map(thumb).join("");
      return `<article class="plano"><h4><span class="num">${esc(p.ano)}</span> · ${esc(p.nome_oficial)}</h4><p class="ap">${esc(p.autor_orgao)}${p.escala ? " · escala: " + esc(p.escala) : ""} · ${esc(p.estatuto)}</p><p>${esc(p.proposta_sintese)}</p><p><b class="sans" style="font-size:13px">Agricultura:</b> ${esc(p.tratamento_agricultura)}</p><p class="ap">Fonte: ${esc(p.fonte_chave)}${p.pagina ? " (" + esc(p.pagina) + ")" : ""}</p>${th ? `<div class="thumbs">${th}</div>` : ""}</article>`;
    }).join("");
    $("#galeriaMapas").innerHTML = D.imagens.filter((i) => i.tipo === "mapa").map((i) => thumb(i.arquivo)).join("");
  })();

  /* ---------------------------------------------------------------- casos */
  (function () {
    const v = (x) => (x == null || x === "" ? "—" : esc(x));
    $("#tabCasos").innerHTML = `<thead><tr><th>Cidade</th><th>Modelo institucional</th><th>Proteção do solo</th><th>Números</th><th>Pressões e resultados</th><th>Lição para Maputo</th><th>Fontes</th></tr></thead><tbody>` + D.casos_comparados.map((c) =>
      `<tr><td data-rot="Cidade"><b>${v(c.cidade)}</b><br>${v(c.pais)} · ${v(c.continente)}</td><td data-rot="Modelo institucional">${v(c.modelo_institucional)}</td><td data-rot="Proteção do solo">${v(c.instrumento_de_protecao_do_solo)}</td><td data-rot="Números">Ano: ${v(c.ano_referencia)}<br>Produtores: ${v(c.produtores)}<br>Área (ha): ${v(c.area_ha)}<br>Abastecimento de hortaliças: ${v(c.participacao_abastecimento_hortalicas)}<br>Agregados praticantes: ${v(c.agregados_praticantes_pct)}</td><td data-rot="Pressões e resultados">${v(c.principais_pressoes)}<br><br>${v(c.resultados)}</td><td data-rot="Lição para Maputo">${v(c.licao_para_maputo)}</td><td data-rot="Fontes">${v(c.fontes_chaves)}</td></tr>`).join("") + "</tbody>";
    $("#tabCasos").style.minWidth = "1000px";
  })();

  /* ---------------------------------------------------------------- metodologia */
  let vAmbito = "cidade";
  chart(function metodologia() {
    const host = $("#metCorpo"); const ex = D.exatidao; const vr = ex.validacao_resumo;
    let h = `<p class="lead">Catorze épocas (1979, 1985, 1990, 1995, 1997, 2000, 2005, 2007, 2010, 2015, 2017, 2020, 2025 e 2026) numa grade de 30 m (EPSG:32736), sobre a Cidade de Maputo, a margem da Matola no vale do Infulene e o sul de Marracuene. A fonte principal são as composições geomedianas anuais do Digital Earth Africa; um modelo Random Forest por época usa bandas, índices espectrais e relevo (Copernicus DEM). As amostras de treino derivam de mapas globais concordantes e de polígonos do OpenStreetMap, propagadas entre épocas por estabilidade espectral.</p>`;
    h += `<h3>Ressalvas de leitura</h3><ul class="sans" style="font:400 14px/1.6 var(--ard-sans);color:var(--ard-text-2)">${D.ressalvas.map((r) => `<li>${esc(r)}</li>`).join("")}<li>O salto de 2005 para 2007 é em parte artefato das composições de imagem; não aparece no GHSL.</li><li>Pós-processamento temporal: o construído de cada época segue a maioria numa janela de três épocas; depois disso é forçado a ser não decrescente (uma vez construído, permanece construído), e a oscilação entre as classes 2 e 5 é suavizada. Por construção, a série pós-processada do construído não decresce, e por isso não mede reversões reais; a classificação bruta e o GHSL são mostrados ao lado para expor essa diferença.</li><li>As faixas dos indicadores vão do mínimo ao máximo de três estimativas (GHSL, bruta, pós-processada) e não são intervalos de confiança.</li><li>Os perímetros (baixadas, zonas do plano de 1985, agropecuária do PEUMM 2008) são independentes da classificação agrícola; a classe 1 (construído) é a mais confiável.</li></ul>`;
    h += `<h3>Exatidão</h3>`;
    if (vr) {
      h += `<p class="nota nota--aviso">${esc(ex.nota)}</p><div class="grupo" id="vAmb" role="group" aria-label="Âmbito da validação"><button type="button" class="chip" data-a="cidade" aria-pressed="${vAmbito === "cidade"}">Cidade</button><button type="button" class="chip" data-a="bbox" aria-pressed="${vAmbito === "bbox"}">Retângulo de estudo</button></div>`;
      const a = vr[vAmbito];
      h += tabela(["Classe", "Exatidão do usuário", "Exatidão do produtor", "Área mapeada (ha)", "Área ajustada (ha, IC 95%)"], Object.keys(a.classes).map((k) => { const c = a.classes[k]; return [esc(NOME_CURTO[k]), `${fmt(100 * c.ua)}% ± ${fmt(100 * c.ua_ic95)}`, `${fmt(100 * c.pa)}% ± ${fmt(100 * c.pa_ic95)}`, fmt(c.area_mapeada_ha), `${fmt(c.area_ajustada_ha)} ± ${fmt(c.area_ajustada_ic95_ha)}`]; }), `Validação cega de 2020, ${a.n_pontos} pontos; exatidão global ${fmt(100 * a.exatidao_global)}% ± ${fmt(100 * a.exatidao_global_ic95)} (IC 95%). Áreas ajustadas segundo Olofsson et al. (2014).`);
    } else h += `<p class="nota">A validação cega de 2020 ainda não foi concluída.</p>`;
    h += `<p class="nota">${esc(ex.quem_rotulou)}</p>`;
    if (ex.sem_baixa && vr) {
      const A = vr[vAmbito], B = ex.sem_baixa.ambitos[vAmbito], dc = ex.distribuicao_confianca || {};
      const pm = (c, k) => `${fmt(100 * c.classes[k].ua)} ± ${fmt(100 * c.classes[k].ua_ic95)} / ${fmt(100 * c.classes[k].pa)} ± ${fmt(100 * c.classes[k].pa_ic95)}`;
      const lin = (nome, a, b) => [nome, a, b];
      h += `<h3>Sensibilidade a rótulos de baixa confiança</h3><p class="nota">Confiança dos rótulos: alta ${fmt(dc.alta)}, média ${fmt(dc.media)}, baixa ${fmt(dc.baixa)}. Excluir os de confiança baixa muda pouco o construído e melhora a classe 2, mas reduz a amostra e alarga os intervalos.</p>` + tabela(["Medida (âmbito selecionado)", "Todos os rótulos", "Sem confiança baixa"], [
        lin("Pontos usados", fmt(A.n_pontos), fmt(B.n_pontos)),
        lin("Exatidão global (%)", `${fmt(100 * A.exatidao_global, 1)} ± ${fmt(100 * A.exatidao_global_ic95, 1)}`, `${fmt(100 * B.exatidao_global, 1)} ± ${fmt(100 * B.exatidao_global_ic95, 1)}`),
        lin("Construído: usuário / produtor (%)", pm(A, "1"), pm(B, "1")),
        lin("Zonas verdes: usuário / produtor (%)", pm(A, "2"), pm(B, "2")),
        lin("Área ajustada da classe 2 (ha)", `${fmt(A.classes["2"].area_ajustada_ha)} ± ${fmt(A.classes["2"].area_ajustada_ic95_ha)}`, `${fmt(B.classes["2"].area_ajustada_ha)} ± ${fmt(B.classes["2"].area_ajustada_ic95_ha)}`)], "Validação cega de 2020; IC 95%");
    }
    const oo = Object.keys(ex.oob);
    h += `<details class="alt"><summary>Exatidão fora-do-saco e validação cruzada espacial por época</summary>${tabela(["Época", "Exatidão OOB", "F1 classe 2", "F1 construído", "Validação cruzada em blocos (exat.)"], oo.map((e) => [e, fmt(100 * ex.oob[e].acc, 1) + "%", fmt(ex.oob[e].f1_zonas_verdes != null ? 100 * ex.oob[e].f1_zonas_verdes : null, 1), fmt(ex.oob[e].f1_construido != null ? 100 * ex.oob[e].f1_construido : null, 1), ex.cv_blocos[e] ? fmt(100 * ex.cv_blocos[e].acc, 1) + "%" : "—"]), "Rótulos derivados de produtos de terceiros, não verdade de campo")}</details>`;
    if (ex.ghsl_construido) h += `<details class="alt"><summary>Concordância do construído com o GHSL</summary>${tabela(["Época", "Ano GHSL", "Construído (ha)", "GHSL (ha)", "F1"], ex.ghsl_construido.map((g) => [g.epoca, g.ghsl_ano, fmt(g.construido_ha), fmt(g.ghsl_ha), fmt(g.f1, 2)]), "Bbox; GHSL com fração ≥ 0,2")}</details>`;
    const dl = [["resultados.json", "Todos os números do site e do artigo"], ["areas_agregado_classe_epoca.csv", "Área por classe e época"], ["areas_agregado_distrito.csv", "Área por distrito"], ["areas_agregado_bairro.csv", "Área por bairro"], ["areas_agregado_transicoes.csv", "Matrizes de transição"], ["conversao.csv", "Conversão agricultura para construído"], ["perda_bairro.csv", "Perda por bairro"], ["areas_luco.csv", "LUCO 1964–2001"], ["series_producao.csv", "Séries de produção com fonte e definição"], ["conflitos.csv", "Conflitos documentados"], ["marcos.csv", "Marcos da linha do tempo"], ["planos.csv", "Planos urbanísticos"], ["casos_comparados.csv", "Comparação internacional"], ["limites.geojson", "Distritos e bairros"], ["plano_1985.geojson", "Zonas do plano de 1985 (vetorizadas)"], ["plano_2008.geojson", "Zonas do PEUMM 2008 (vetorizadas)"], ["conflitos.geojson", "Conflitos (posição aproximada)"]];
    h += `<h3>Dados para baixar</h3><ul class="downloads">${dl.map((d) => `<li><a href="dados/${d[0]}" download>${d[0]}</a> <span class="nota">${d[1]}</span></li>`).join("")}</ul>`;
    h += `<h3>Como citar</h3><p class="cit">${esc(D.citacao)}</p><h3>Licenças e créditos</h3><p class="nota">O código está sob licença MIT. O material de terceiros (planos históricos, mapas e dados) não é coberto por essa licença e mantém os direitos dos titulares; é reproduzido para fins de citação científica, com indicação da fonte.</p>`;
    h += `<details class="alt"><summary>Créditos das imagens (${D.imagens.length})</summary>${tabela(["Arquivo", "Título", "Crédito"], D.imagens.map((i) => [esc(i.arquivo), esc(i.titulo), esc(credito(i))]))}</details>`;
    h += `<details class="alt"><summary>Fontes de dados e licenças</summary>${tabela(["Fonte", "Licença"], D.creditos.dados.map((d) => [esc(d["Fonte"]), esc(d["Licença"])]))}</details>`;
    host.innerHTML = h;
    $$("#vAmb button", host).forEach((b) => b.addEventListener("click", () => { vAmbito = b.dataset.a; metodologia(); }));
  });
  $("#rodape").textContent = `${D.citacao} Dados gerados em ${D.meta.gerado_em}.`;

  /* ---------------------------------------------------------------- mapa */
  const estado = { modo: "cls", ano: 2026, anoB: 2026, anoA: 1985, comp: false, play: null };
  const M = {};
  const GEO = {};
  const get = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(u); return r.json(); });
  let geoPromise = null;
  function carregaGeo() {
    if (!geoPromise) geoPromise = Promise.all(["limites", "plano_1985", "plano_2008", "conflitos"].map((n) => get("dados/" + n + ".geojson").then((j) => (GEO[n] = j))));
    return geoPromise;
  }
  const PLCOR = { zv_permanentes: "--viz-3", zv_provisorias: "--viz-5", ocupacao_actual: "--ard-pedra", agropecuaria: "--viz-3", expansao_urbana: "--viz-2", urbanizavel_planificada: "--viz-4", urbanizavel_nao_planificada: "--viz-6" };
  const PLNOME = { zv_permanentes: "Zonas verdes permanentes (1985)", zv_provisorias: "Zonas verdes provisórias (1985)", ocupacao_actual: "Ocupação atual (1985)", agropecuaria: "Agropecuária (2008)", expansao_urbana: "Expansão urbana (2008)", urbanizavel_planificada: "Urbanizável planificada (2008)", urbanizavel_nao_planificada: "Urbanizável não planificada (2008)" };
  const camadas = { dist: false, bairro: false, p85: false, p08: false, conf: false, planoImg: "" };

  function iniciaMapa(id, chave) {
    const map = new maplibregl.Map({ container: id, style: "https://tiles.openfreemap.org/styles/positron", center: [32.585, -25.93], zoom: 10.4, attributionControl: { compact: true }, cooperativeGestures: false });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
    const o = { map, pronto: false, ativa: null, fila: [] };
    M[chave] = o;
    map.on("load", () => {
      carregaGeo().then(() => {
        const L = (n, d) => map.addSource(n, { type: "geojson", data: d });
        ["plano_1985", "peumm_2008"].forEach((k) => {
          const p = D.painel.planos[k];
          map.addSource("pi-" + k, { type: "image", url: p.arquivo, coordinates: p.coordenadas });
          map.addLayer({ id: "pi-" + k, type: "raster", source: "pi-" + k, layout: { visibility: "none" }, paint: { "raster-opacity": 0.7, "raster-fade-duration": 0 } });
        });
        L("limites", GEO.limites); L("p85", GEO.plano_1985); L("p08", GEO.plano_2008); L("conf", GEO.conflitos);
        const colMatch = (prop) => ["match", ["get", "classe"]].concat(Object.keys(PLCOR).flatMap((k) => [k, css(PLCOR[k])])).concat([css("--viz-muted")]);
        map.addLayer({ id: "p85-fill", type: "fill", source: "p85", layout: { visibility: "none" }, paint: { "fill-color": colMatch(), "fill-opacity": 0.45 } });
        map.addLayer({ id: "p85-line", type: "line", source: "p85", layout: { visibility: "none" }, paint: { "line-color": colMatch(), "line-width": 1.2 } });
        map.addLayer({ id: "p08-fill", type: "fill", source: "p08", layout: { visibility: "none" }, paint: { "fill-color": colMatch(), "fill-opacity": 0.45 } });
        map.addLayer({ id: "p08-line", type: "line", source: "p08", layout: { visibility: "none" }, paint: { "line-color": colMatch(), "line-width": 1.2 } });
        map.addLayer({ id: "bairro-fill", type: "fill", source: "limites", filter: ["in", ["get", "camada"], ["literal", ["bairro_maputo", "bairro_matola"]]], layout: { visibility: "none" }, paint: { "fill-color": css("--viz-1"), "fill-opacity": 0.03 } });
        map.addLayer({ id: "bairro-line", type: "line", source: "limites", filter: ["in", ["get", "camada"], ["literal", ["bairro_maputo", "bairro_matola"]]], layout: { visibility: "none" }, paint: { "line-color": css("--viz-1"), "line-width": 0.8, "line-dasharray": [2, 2] } });
        map.addLayer({ id: "dist-line", type: "line", source: "limites", filter: ["==", ["get", "camada"], "distrito"], layout: { visibility: "none" }, paint: { "line-color": css("--viz-1"), "line-width": 2 } });
        map.addLayer({ id: "conf-pt", type: "circle", source: "conf", layout: { visibility: "none" }, paint: { "circle-radius": 7, "circle-color": css("--viz-2"), "circle-stroke-color": css("--ard-papel-fig"), "circle-stroke-width": 2 } });
        map.on("click", "conf-pt", (e) => { const f = e.features[0]; popupConf(map, f.properties, e.lngLat); });
        map.on("click", "bairro-fill", (e) => {
          if (map.queryRenderedFeatures(e.point, { layers: ["conf-pt"] }).length) return;
          const f = e.features[0].properties;
          const t = f.zv1990 != null && f.zv1990 !== "null" ? `<br>Classe 2 (indicativa): ${fmt(+f.zv1990)} ha em 1990, ${fmt(+f.zv2025)} ha em 2025 (${fmt(+f.dif)} ha)` : "";
          new maplibregl.Popup({ maxWidth: "280px" }).setLngLat(e.lngLat).setHTML(`<b>${esc(f.nome)}</b>${t}`).addTo(map);
        });
        map.on("mouseenter", "conf-pt", () => (map.getCanvas().style.cursor = "pointer")); map.on("mouseleave", "conf-pt", () => (map.getCanvas().style.cursor = ""));
        o.pronto = true;
        aplicaCamadas(); aplicaRaster(o);
      }).catch(() => { $("#" + id).insertAdjacentHTML("beforeend", `<div class="mapa-erro">Não foi possível carregar as camadas vetoriais. Abra o site por um servidor HTTP, e não diretamente do disco.</div>`); o.pronto = true; o.semGeo = true; aplicaRaster(o); });
    });
    return o;
  }
  function popupConf(map, p, ll) { new maplibregl.Popup({ maxWidth: "300px" }).setLngLat(ll).setHTML(`<b>${esc(p.local)}</b> (${esc(p.ano)})<br>${esc(p.tipo)}<br>${esc(p.desc)}<br><i>${esc(p.fonte)}${p.pagina && p.pagina !== "null" ? ", " + esc(p.pagina) : ""}. Posição aproximada.</i>`).addTo(map); }

  const vis = (map, ids, on) => ids.forEach((i) => map.getLayer(i) && map.setLayoutProperty(i, "visibility", on ? "visible" : "none"));
  function aplicaCamadas() {
    Object.values(M).forEach((o) => {
      if (!o.pronto || o.semGeo) return; const m = o.map;
      vis(m, ["dist-line"], camadas.dist); vis(m, ["bairro-line", "bairro-fill"], camadas.bairro); vis(m, ["p85-fill", "p85-line"], camadas.p85);
      vis(m, ["p08-fill", "p08-line"], camadas.p08); vis(m, ["conf-pt"], camadas.conf);
      ["plano_1985", "peumm_2008"].forEach((k) => vis(m, ["pi-" + k], camadas.planoImg === k));
    });
    legenda();
  }
  function chaveRaster(ano) {
    if (estado.modo === "img") return "img_" + ano;
    if (estado.modo === "conv") return "conv";
    return ano === 1979 ? null : "cls_" + ano;
  }
  function infoRaster(ch) {
    if (ch === "conv") return D.painel.conversao;
    const [t, a] = ch.split("_"); return t === "img" ? D.painel.imagem[a] : D.painel.classes[a];
  }
  function aplicaRaster(o) {
    if (!o.pronto) return;
    const m = o.map; const ano = o === M.B ? estado.anoB : (estado.comp ? estado.anoA : estado.ano);
    const ch = chaveRaster(ano);
    if (o.ativa && o.ativa !== ch && m.getLayer("r-" + o.ativa)) m.setPaintProperty("r-" + o.ativa, "raster-opacity", 0);
    if (ch) {
      if (!m.getSource("s-" + ch)) {
        const r = infoRaster(ch);
        m.addSource("s-" + ch, { type: "image", url: r.arquivo, coordinates: r.coordenadas });
        m.addLayer({ id: "r-" + ch, type: "raster", source: "s-" + ch, paint: { "raster-opacity": 0, "raster-fade-duration": 0, "raster-opacity-transition": { duration: 0 }, "raster-resampling": ch.startsWith("img") ? "linear" : "nearest" } }, m.getLayer("pi-plano_1985") ? "pi-plano_1985" : undefined);
      }
      m.setPaintProperty("r-" + ch, "raster-opacity", ch.startsWith("img") ? 1 : 0.88);
    }
    o.ativa = ch;
  }
  function legenda() {
    let h = "";
    if (estado.modo === "cls") h += D.classes.map((c) => `<li><i class="sw" style="background:${corCls(c.cod)}"></i>${esc(NOME_CURTO[c.cod])}</li>`).join("");
    else if (estado.modo === "conv") h += Object.keys(D.painel.conversao.cores_hex).map((a) => `<li><i class="sw" style="background:${D.painel.conversao.cores_hex[a]}"></i>${a}</li>`).join("") + `<li>Ano da primeira conversão estável de agricultura para construído</li>`;
    else h += `<li>Cor verdadeira (1979: falsa-cor NIR, vermelho, verde); vegetação verde, áreas construídas em tons claros e rosados.</li>`;
    if (camadas.p85) h += ["zv_permanentes", "zv_provisorias", "ocupacao_actual"].map((k) => `<li><i class="sw" style="background:${css(PLCOR[k])};opacity:.6"></i>${PLNOME[k]}</li>`).join("");
    if (camadas.p08) h += ["agropecuaria", "expansao_urbana", "urbanizavel_planificada", "urbanizavel_nao_planificada"].map((k) => `<li><i class="sw" style="background:${css(PLCOR[k])};opacity:.6"></i>${PLNOME[k]}</li>`).join("");
    if (camadas.conf) h += `<li><i class="sw" style="background:${css("--viz-2")};border-radius:50%"></i>Conflito (posição aproximada)</li>`;
    $("#legenda").innerHTML = h;
  }
  function textos() {
    const mA = estado.comp ? estado.anoA : estado.ano; const eA = EPINFO[mA], eB = EPINFO[estado.anoB];
    let t = (estado.comp ? `Esquerda, ${eA.rotulo}: ` : "") + eA.caveat;
    if (estado.comp) t += ` Direita, ${eB.rotulo}: ` + eB.caveat;
    if (estado.modo === "conv") t = "Ano da primeira conversão estável de agricultura (classes 2 ou 3) para construído, 1990 a 2026. A classe 3 é indicativa.";
    if (estado.modo === "cls") { if (mA === 1979 || (estado.comp && estado.anoB === 1979)) t += " Sem classificação para 1979: legenda reduzida e MSS de 60 m."; t += " Classes 2 e 3 indicativas: ver validação."; }
    $("#caveat").textContent = t;
    $("#rotA").textContent = estado.comp ? EPINFO[estado.anoA].rotulo : ""; $("#rotB").textContent = estado.comp ? EPINFO[estado.anoB].rotulo : "";
    $("#notaMapa").textContent = estado.modo === "cls" ? "Classificação a 30 m; classe 'Zonas verdes' = agricultura de baixada. Hortas pequenas são subpíxel." : "";
    $("#anoGrande").textContent = estado.modo === "conv" ? "1990–2026" : estado.comp ? `${estado.anoA} | ${estado.anoB}` : String(estado.ano);
    $("#sliderAno").setAttribute("aria-valuetext", EPINFO[estado.ano].rotulo);
  }
  function atualiza() {
    $("#sliderAno").value = EP.indexOf(estado.ano); $("#sliderAno").disabled = estado.comp || estado.modo === "conv";
    $("#chkComp").disabled = estado.modo === "conv"; $("#selComp").hidden = !estado.comp;
    $("#mapaWrap").dataset.comp = estado.comp ? "1" : "0";
    $("#selA").value = estado.anoA; $("#selB").value = estado.anoB;
    $$("#modoGrupo button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.modo === estado.modo));
    Object.values(M).forEach(aplicaRaster); textos(); legenda();
    if (estado.comp && M.B) { M.B.map.resize(); sincroniza(M.A.map, M.B.map); }
  }
  let sync = false;
  function sincroniza(a, b) { sync = true; b.jumpTo({ center: a.getCenter(), zoom: a.getZoom(), bearing: a.getBearing(), pitch: a.getPitch() }); sync = false; }
  function setClip() { const v = +$("#compRange").value; $("#mapaB").style.clipPath = `inset(0 0 0 ${v}%)`; $("#compLinha").style.left = v + "%"; }

  function montaControles() {
    const opts = D.epocas.map((e) => `<option value="${e.ano}">${esc(e.rotulo)}</option>`).join("");
    $("#selA").innerHTML = opts; $("#selB").innerHTML = opts;
    $("#ticksAno").innerHTML = EP.map((a) => `<span>${[1979, 1990, 2000, 2010, 2020, 2026].includes(a) ? a : ""}</span>`).join("");
    $("#sliderAno").addEventListener("input", (e) => { estado.ano = EP[+e.target.value]; atualiza(); });
    $("#modoGrupo").addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return; estado.modo = b.dataset.modo; if (estado.modo === "conv") { estado.comp = false; $("#chkComp").checked = false; } atualiza(); });
    $("#chkComp").addEventListener("change", (e) => { estado.comp = e.target.checked; if (estado.comp) { estado.anoA = Math.min(estado.anoA, estado.ano) === estado.ano ? 1985 : estado.anoA; estado.anoB = estado.ano; } else { estado.ano = estado.anoB; } if (estado.comp && !M.B) { M.B = iniciaMapa("mapaB", "B"); M.B.map.on("move", () => { if (!sync) { sync = true; M.A.map.jumpTo({ center: M.B.map.getCenter(), zoom: M.B.map.getZoom(), bearing: M.B.map.getBearing(), pitch: M.B.map.getPitch() }); sync = false; } }); M.A.map.on("move", () => { if (!sync && M.B) sincroniza(M.A.map, M.B.map); }); M.B.map.once("load", () => sincroniza(M.A.map, M.B.map)); } atualiza(); });
    $("#selA").addEventListener("change", (e) => { estado.anoA = +e.target.value; atualiza(); });
    $("#selB").addEventListener("change", (e) => { estado.anoB = +e.target.value; atualiza(); });
    $("#compRange").addEventListener("input", setClip);
    [["chkDist", "dist"], ["chkBairro", "bairro"], ["chkP85", "p85"], ["chkP08", "p08"], ["chkConf", "conf"]].forEach(([id, k]) => $("#" + id).addEventListener("change", (e) => { camadas[k] = e.target.checked; aplicaCamadas(); }));
    $("#selPlanoImg").addEventListener("change", (e) => { camadas.planoImg = e.target.value; aplicaCamadas(); });
    $("#btnPlay").addEventListener("click", () => {
      const b = $("#btnPlay");
      if (estado.play) { clearInterval(estado.play); estado.play = null; b.textContent = "Reproduzir"; b.setAttribute("aria-pressed", "false"); return; }
      if (estado.comp || estado.modo === "conv") return;
      b.textContent = "Pausar"; b.setAttribute("aria-pressed", "true");
      if (estado.ano === EP[EP.length - 1]) estado.ano = EP[0];
      atualiza();
      estado.play = setInterval(() => { const i = EP.indexOf(estado.ano); if (i >= EP.length - 1) { clearInterval(estado.play); estado.play = null; b.textContent = "Reproduzir"; b.setAttribute("aria-pressed", "false"); return; } estado.ano = EP[i + 1]; atualiza(); }, 1400);
    });
    document.addEventListener("click", (e) => {
      const b = e.target.closest("[data-conf]"); if (!b) return;
      const f = (GEO.conflitos ? GEO.conflitos.features : []).find((x) => x.properties.id === b.dataset.conf); if (!f) return;
      camadas.conf = true; $("#chkConf").checked = true; aplicaCamadas();
      $("#painel").scrollIntoView({ behavior: "smooth" });
      M.A.map.flyTo({ center: f.geometry.coordinates, zoom: 13 });
      setTimeout(() => popupConf(M.A.map, f.properties, f.geometry.coordinates), 900);
    });
  }
  if (window.maplibregl && D.painel) {
    montaControles(); setClip();
    M.A = iniciaMapa("mapaA", "A");
    atualiza();
  } else {
    $("#mapaA").innerHTML = `<div class="mapa-erro">O mapa não carregou neste aparelho (biblioteca MapLibre ou dados do painel indisponíveis).</div>`;
    $("#caveat").textContent = "Sem o mapa, use as seções de gráficos e tabelas abaixo.";
  }

  /* navegação ativa */
  if ("IntersectionObserver" in window) {
    const links = $$(".topo nav a");
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) links.forEach((l) => l.setAttribute("aria-current", l.getAttribute("href") === "#" + e.target.id)); }), { rootMargin: "-40% 0px -55% 0px" });
    $$("main section[id]").forEach((s) => io.observe(s));
  }
})();
