// Sistema Ardosia - estilos nomeados para docx-js (A4).
// Uso:
//   const A = require('./ardosia_docx.js');
//   const doc = new Document({ styles: A.styles, sections: [{ properties: A.pageProps,
//     headers: A.headers(docx, 'Nota tecnica'), footers: A.footers(docx, 'Nota tecnica 04/2026'),
//     children: [...] }] });
//
// Lembretes docx-js:
//   - tamanhos sao meio-pontos: 11 pt = size 22
//   - bordas sao pontos-oitavos: 1 pt = size 8
//   - todo estilo referenciado por `style:` precisa existir aqui, senao o
//     paragrafo sai sem formatacao e o erro so aparece no Word real
//   - imagens: passe o Buffer com o `type` correto (PNG como 'png'), nunca
//     declare um PNG como 'svg' - renderiza no LibreOffice e quebra no Word
//   - o estilo Titulo1 tem pageBreakBefore: true. No PRIMEIRO H1 do documento
//     isso deixa a folha de rosto vazia - sobrescreva no paragrafo:
//     new Paragraph({ text: '...', style: 'Titulo1', pageBreakBefore: false })

const C = {
  tinta: '1B1F23', grafiteCl: '31383D', grafite: '4A5157', pedra: '7B7D78',
  filete: 'D8D4CC', fileteCl: 'E6E2DA',
  primaria: '24404F', acento: '9C5B41',
};

const F = { serif: 'Georgia', sans: 'Calibri' };

const pageProps = {
  page: {
    size: { width: 11906, height: 16838 },          // A4 em twips
    margin: { top: 1247, bottom: 1247, left: 1417, right: 1417 }, // 2,2 / 2,5 cm
  },
};

const styles = {
  default: {
    document: { run: { font: F.serif, size: 22, color: C.grafiteCl } },
  },
  paragraphStyles: [
    {
      id: 'TituloDoc', name: 'Titulo do documento', basedOn: 'Normal', next: 'Corpo',
      run: { font: F.serif, size: 48, color: C.tinta },
      paragraph: { spacing: { after: 240 } },
    },
    {
      id: 'Kicker', name: 'Kicker', basedOn: 'Normal', next: 'Titulo1',
      run: { font: F.sans, size: 16, color: C.acento, bold: true, allCaps: true, characterSpacing: 40 },
      paragraph: { spacing: { before: 240, after: 60 } },
    },
    {
      id: 'Titulo1', name: 'Titulo 1', basedOn: 'Normal', next: 'Corpo', quickFormat: true,
      run: { font: F.serif, size: 34, color: C.tinta },
      paragraph: {
        spacing: { before: 360, after: 160 },
        pageBreakBefore: true,
        border: { bottom: { color: C.filete, size: 4, space: 6, style: 'single' } },
      },
    },
    {
      id: 'Titulo2', name: 'Titulo 2', basedOn: 'Normal', next: 'Corpo', quickFormat: true,
      run: { font: F.serif, size: 26, color: C.tinta, bold: true },
      paragraph: { spacing: { before: 280, after: 120 } },
    },
    {
      id: 'Titulo3', name: 'Titulo 3', basedOn: 'Normal', next: 'Corpo', quickFormat: true,
      run: { font: F.serif, size: 22, color: C.grafite, bold: true, italics: true },
      paragraph: { spacing: { before: 240, after: 80 } },
    },
    {
      id: 'Corpo', name: 'Corpo', basedOn: 'Normal', next: 'Corpo', quickFormat: true,
      run: { font: F.serif, size: 22, color: C.grafiteCl },
      paragraph: { spacing: { after: 160, line: 276 }, alignment: 'both' },
    },
    {
      id: 'Destaque', name: 'Destaque', basedOn: 'Normal', next: 'Corpo',
      run: { font: F.serif, size: 21, color: C.grafite, italics: true },
      paragraph: {
        spacing: { before: 200, after: 200, line: 264 },
        indent: { left: 340 },
        border: { left: { color: C.acento, size: 16, space: 12, style: 'single' } },
      },
    },
    {
      id: 'Tabela', name: 'Tabela', basedOn: 'Normal', next: 'Tabela',
      run: { font: F.sans, size: 18, color: C.grafiteCl },
      paragraph: { spacing: { before: 40, after: 40 } },
    },
    {
      id: 'TabelaCab', name: 'Tabela cabecalho', basedOn: 'Normal', next: 'Tabela',
      run: { font: F.sans, size: 18, color: C.primaria, bold: true },
      paragraph: { spacing: { before: 40, after: 40 } },
    },
    {
      id: 'Legenda', name: 'Legenda', basedOn: 'Normal', next: 'Corpo',
      run: { font: F.sans, size: 18, color: C.pedra, italics: true },
      paragraph: { spacing: { before: 80, after: 240 } },
    },
    {
      id: 'Nota', name: 'Nota', basedOn: 'Normal', next: 'Nota',
      run: { font: F.sans, size: 16, color: C.pedra },
      paragraph: { spacing: { after: 80 } },
    },
  ],
};

// Cabecalho: monograma a esquerda, descritor em versalete a direita, filete abaixo.
function headers(docx, descritor) {
  const { Header, Paragraph, TextRun, TabStopType, AlignmentType } = docx;
  return {
    default: new Header({
      children: [new Paragraph({
        tabStops: [{ type: TabStopType.RIGHT, position: 9070 }],
        border: { bottom: { color: C.primaria, size: 8, space: 4, style: 'single' } },
        children: [
          new TextRun({ text: 'dps', font: F.serif, size: 20, color: C.primaria }),
          new TextRun({ text: '\t' }),
          new TextRun({
            text: (descritor || '').toUpperCase(), font: F.sans, size: 15,
            color: C.pedra, characterSpacing: 40,
          }),
        ],
        alignment: AlignmentType.LEFT,
      })],
    }),
  };
}

// Rodape: filete acima, identificacao a esquerda, numero de pagina a direita.
function footers(docx, identificacao) {
  const { Footer, Paragraph, TextRun, PageNumber, TabStopType } = docx;
  return {
    default: new Footer({
      children: [new Paragraph({
        tabStops: [{ type: TabStopType.RIGHT, position: 9070 }],
        border: { top: { color: C.filete, size: 4, space: 6, style: 'single' } },
        children: [
          new TextRun({ text: identificacao || '', font: F.sans, size: 15, color: C.pedra }),
          new TextRun({ text: '\t' }),
          new TextRun({ children: [PageNumber.CURRENT], font: F.sans, size: 15, color: C.pedra }),
        ],
      })],
    }),
  };
}

// Tabela sem borda vertical, sem zebra: so linha inferior por celula.
const tableBorders = {
  top: { style: 'none', size: 0 },
  bottom: { style: 'single', size: 4, color: C.fileteCl },
  left: { style: 'none', size: 0 },
  right: { style: 'none', size: 0 },
  insideHorizontal: { style: 'single', size: 4, color: C.fileteCl },
  insideVertical: { style: 'none', size: 0 },
};

const tableHeaderBorders = Object.assign({}, tableBorders, {
  bottom: { style: 'single', size: 8, color: C.primaria },
});

module.exports = { C, F, styles, pageProps, headers, footers, tableBorders, tableHeaderBorders };
