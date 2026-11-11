// Gera artigo.docx a partir de blocos.json (escrito por scripts/21_artigo.py).
// Uso: node build_docx.js blocos.json saida.docx
// Estilos do Sistema Ardosia (scripts/ardosia_docx.js) ajustados para ABNT: A4, margens 3/2/3/2 cm,
// corpo em 1,5 de espacamento, Titulo1 sem quebra de pagina forcada (artigo corrido).
const fs = require('fs');
const path = require('path');
const docx = require('docx');
const A = require(path.resolve(__dirname, '../../scripts/ardosia_docx.js'));
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, ShadingType, VerticalAlign,
} = docx;

const [, , inPath, outPath] = process.argv;
const { blocos, meta } = JSON.parse(fs.readFileSync(inPath, 'utf8'));

const CM = 567; // twips por cm
const TEXT_W = 11906 - 3 * CM - 2 * CM; // 9071 twips (16 cm)

// ---- estilos: copia dos Ardosia com ajustes ABNT
const styles = JSON.parse(JSON.stringify(A.styles));
const ps = styles.paragraphStyles;
const get = (id) => ps.find((s) => s.id === id);
get('Corpo').run.size = 24;
get('Corpo').paragraph = { spacing: { after: 0, line: 360 }, alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 709 } };
get('Titulo1').paragraph.pageBreakBefore = false;
get('Titulo1').paragraph.spacing = { before: 360, after: 160 };
get('Titulo1').paragraph.keepNext = true;
get('Titulo2').paragraph.keepNext = true;
ps.push({
  id: 'Resumo', name: 'Resumo', basedOn: 'Normal', next: 'Resumo',
  run: { font: A.F.serif, size: 22, color: A.C.grafiteCl },
  paragraph: { spacing: { after: 120, line: 276 }, alignment: AlignmentType.JUSTIFIED },
});
ps.push({
  id: 'Referencia', name: 'Referencia', basedOn: 'Normal', next: 'Referencia',
  run: { font: A.F.serif, size: 21, color: A.C.grafiteCl },
  paragraph: { spacing: { after: 200, line: 252 }, alignment: AlignmentType.LEFT },
});
ps.push({
  id: 'LegendaTab', name: 'Legenda de quadro', basedOn: 'Normal', next: 'Tabela',
  run: { font: A.F.sans, size: 18, color: A.C.grafite, bold: true },
  paragraph: { spacing: { before: 240, after: 80 }, keepNext: true },
});
ps.push({
  id: 'LegendaFig', name: 'Legenda de figura', basedOn: 'Normal', next: 'Nota',
  run: { font: A.F.sans, size: 18, color: A.C.grafite },
  paragraph: { spacing: { before: 80, after: 20 } },
});
ps.push({
  id: 'Autoria', name: 'Autoria', basedOn: 'Normal', next: 'Corpo',
  run: { font: A.F.sans, size: 20, color: A.C.grafite },
  paragraph: { spacing: { after: 20 } },
});
get('Nota').paragraph.spacing = { before: 20, after: 240 };

// ---- runs inline
function mkRuns(rs, extra = {}) {
  return rs.map((r) => new TextRun(Object.assign({ text: r.t, bold: !!r.b || extra.bold, italics: !!r.i }, extra.run || {})));
}

const children = [];
let firstH1 = true;
for (const b of blocos) {
  switch (b.type) {
    case 'title':
      children.push(new Paragraph({ text: b.titulo, style: 'TituloDoc' }));
      children.push(new Paragraph({ style: 'Autoria', children: [new TextRun({ text: b.autor, bold: true })] }));
      children.push(new Paragraph({
        style: 'Autoria', spacing: { after: 240 },
        border: { bottom: { color: A.C.filete, size: 4, space: 8, style: BorderStyle.SINGLE } },
        children: [new TextRun({ text: 'ORCID: https://orcid.org/' + b.orcid, color: A.C.pedra })],
      }));
      break;
    case 'h1':
      children.push(new Paragraph({ style: 'Titulo1', pageBreakBefore: false, children: mkRuns(b.runs) }));
      firstH1 = false;
      break;
    case 'h2':
      children.push(new Paragraph({ style: 'Titulo2', children: mkRuns(b.runs) }));
      break;
    case 'p':
      children.push(new Paragraph({ style: 'Corpo', children: mkRuns(b.runs) }));
      break;
    case 'resumo':
      children.push(new Paragraph({ style: 'Resumo', children: mkRuns(b.runs) }));
      break;
    case 'ref':
      children.push(new Paragraph({ style: 'Referencia', children: mkRuns(b.runs) }));
      break;
    case 'fig': {
      const wPx = Math.round(16 / 2.54 * 96);
      let w = wPx, h = Math.round(wPx * b.h / b.w);
      const maxH = Math.round(18.5 / 2.54 * 96);
      if (h > maxH) { w = Math.round(w * maxH / h); h = maxH; }
      const ext = path.extname(b.path).slice(1).toLowerCase().replace('jpeg', 'jpg');
      children.push(new Paragraph({
        alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 240, after: 60 },
        children: [new ImageRun({ type: ext, data: fs.readFileSync(b.path), transformation: { width: w, height: h },
          altText: { title: 'Figura', description: b.caption.map((r) => r.t).join(''), name: 'fig' } })],
      }));
      children.push(new Paragraph({ style: 'LegendaFig', keepNext: b.source.length > 0, children: mkRuns(b.caption) }));
      if (b.source.length) children.push(new Paragraph({ style: 'Nota', children: mkRuns(b.source) }));
      break;
    }
    case 'table': {
      const tot = b.widths.reduce((a, c) => a + c, 0);
      const cw = b.widths.map((x) => Math.round(TEXT_W * x / tot));
      cw[cw.length - 1] += TEXT_W - cw.reduce((a, c) => a + c, 0);
      const mkCell = (txt, i, head) => new TableCell({
        width: { size: cw[i], type: WidthType.DXA },
        verticalAlign: head ? VerticalAlign.BOTTOM : VerticalAlign.TOP,
        margins: { top: 30, bottom: 30, left: 60, right: 60 },
        borders: head
          ? { top: { style: BorderStyle.NONE, size: 0 }, bottom: { style: BorderStyle.SINGLE, size: 8, color: A.C.primaria }, left: { style: BorderStyle.NONE, size: 0 }, right: { style: BorderStyle.NONE, size: 0 } }
          : { top: { style: BorderStyle.NONE, size: 0 }, bottom: { style: BorderStyle.SINGLE, size: 4, color: A.C.fileteCl }, left: { style: BorderStyle.NONE, size: 0 }, right: { style: BorderStyle.NONE, size: 0 } },
        children: [new Paragraph({
          style: head ? 'TabelaCab' : 'Tabela',
          alignment: b.align[i] === 'r' ? AlignmentType.RIGHT : AlignmentType.LEFT,
          children: [new TextRun({ text: txt })],
        })],
      });
      const rows = [new TableRow({ tableHeader: true, cantSplit: true, children: b.header.map((c, i) => mkCell(c, i, true)) })];
      for (const r of b.rows) rows.push(new TableRow({ cantSplit: true, children: r.map((c, i) => mkCell(c, i, false)) }));
      children.push(new Paragraph({ style: 'LegendaTab', children: mkRuns(b.caption) }));
      children.push(new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: cw, rows }));
      if (b.source.length) children.push(new Paragraph({ style: 'Nota', spacing: { before: 60, after: 240 }, children: mkRuns(b.source) }));
      break;
    }
    default:
      throw new Error('tipo de bloco desconhecido: ' + b.type);
  }
}

const doc = new Document({
  creator: meta.autor,
  title: meta.titulo,
  styles,
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 3 * CM, left: 3 * CM, bottom: 2 * CM, right: 2 * CM } } },
    headers: A.headers(docx, 'Pessini Sobreira · Artigo científico'),
    footers: A.footers(docx, 'Pessini Sobreira · Zonas verdes de Maputo (1979–2026)'),
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log('docx', Math.round(buf.length / 1024), 'KB');
});
