/* Real CKEditor + HTML-to-AKN integration. Run with:
 * CHROME_BIN=/path/to/chrome INDIGO_AKN_SOURCE=/path/to/indigo-akn npm run test:table-editor
 * Requires the Sass CLI, as used by the application asset build.
 * Without INDIGO_AKN_SOURCE, use the installed dependency.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const webpack = require('webpack');
const {execFileSync} = require('node:child_process');

const root = path.resolve(__dirname, '../..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'indigo-table-test-'));
const source = process.env.INDIGO_AKN_SOURCE;
const converter = source ? path.join(source, 'src/html.js') : require.resolve('@lawsafrica/indigo-akn/dist/html.js');
fs.writeFileSync(path.join(temp, 'entry.js'), `import {htmlToAkn} from ${JSON.stringify(converter)}; window.indigoAkn = {htmlToAkn, foreignElementsSelector: '.foreign'};`);

async function run () {
  await new Promise((resolve, reject) => webpack({
    mode: 'development', entry: path.join(temp, 'entry.js'),
    output: {path: temp, filename: 'converter.js'},
    resolve: {fallback: {fs: false, crypto: false}}
  }, (err, stats) => err || stats.hasErrors() ? reject(err || stats.toString()) : resolve()));
  const templates = path.join(root, 'indigo_app/templates/indigo_api/document');
  function english (s) { return s.replace(/{% trans (["'])(.*?)\1 %}/g, '$2'); }
  let toolbar = fs.readFileSync(path.join(templates, '_toolbar.html'), 'utf8').split('<div class="table-editor-wrapper')[1].split('<!-- end table editor wrapper -->')[0];
  toolbar = '<div class="table-editor-wrapper' + toolbar;
  toolbar = english(toolbar.replace(/{% include 'indigo_api\/document\/_table_size_options.html' %}/g, fs.readFileSync(path.join(templates, '_table_size_options.html'), 'utf8')));
  const scripts = ['bower_components/jquery/dist/jquery.js', 'bower_components/underscore/underscore.js', 'bower_components/backbone/backbone.js', 'ckeditor/ckeditor.js', 'javascript/indigo/table_layout.js', 'javascript/indigo/views/table_editor.js'];
  const html = `<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="/static/stylesheets/app.css"></head><body class="document-editor-view">${toolbar}<div class="document-primary-pane-content-pane"><la-akoma-ntoso></la-akoma-ntoso></div>${scripts.map(s => `<script src="/static/${s}"></script>`).join('')}<script src="/bootstrap.js"></script><script src="/converter.js"></script></body></html>`;
  const appCss = execFileSync('sass', ['--no-source-map', '--load-path', path.join(root, 'indigo_app/static'),
    '--load-path', path.join(root, 'node_modules'), path.join(root, 'indigo_app/static/stylesheets/app.scss')], {encoding: 'utf8'});
  const widgetCss = fs.readFileSync(require.resolve('@lawsafrica/law-widgets/dist/collection/components/akoma-ntoso/akoma-ntoso.css'), 'utf8');
  const server = http.createServer((req, res) => {
    if (req.url === '/') { res.end(html); return; }
    if (req.url === '/static/stylesheets/app.css') { res.setHeader('Content-Type', 'text/css'); res.end(widgetCss + '\n' + appCss); return; }
    const name = req.url === '/bootstrap.js' ? require.resolve('bootstrap/dist/js/bootstrap.bundle.min.js') : req.url === '/converter.js' ? path.join(temp, 'converter.js') : path.join(root, 'indigo_app', req.url.split('?')[0]);
    fs.readFile(name, (err, data) => { res.statusCode = err ? 404 : 200; res.setHeader('Content-Type', name.endsWith('.js') ? 'application/javascript' : 'text/css'); res.end(err ? '' : data); });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await puppeteer.launch({executablePath: process.env.CHROME_BIN, headless: true});
    const page = await browser.newPage();
    await page.setViewport({width: 1280, height: 900});
    page.on('pageerror', e => console.error(e));
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    async function openTableFormatting () {
      if (await page.$eval('.table-format-toggle', el => el.getAttribute('aria-expanded')) !== 'true') await page.click('.table-format-toggle');
    }
    async function chooseCellSize (value) {
      await page.click('.table-cell-size-toggle');
      await page.click(`.table-format-action[value="${value}"]`);
      assert.equal(await page.$eval('.table-cell-size-toggle', el => el.getAttribute('aria-expanded')), 'false');
    }
    await page.evaluate(() => {
      window.$t = s => s;
      window.confirm = () => true;
      const xml = '<table xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" eId="t1" class="custom akn--text-small" fontsize="9"><tr><td class="cell-custom akn--text-right"><p class="paragraph-custom akn--text-normal akn--text-left">First</p><p class="akn--text-xxsmall">Second</p></td><td class="akn--text-small"><p>Other</p></td></tr></table>';
      window.sourceXml = new DOMParser().parseFromString(xml, 'text/xml');
      window.fixture = '<table id="t1" data-eid="t1" class="akn-table custom akn--text-small"><tbody><tr><td class="akn-td cell-custom akn--text-right"><span class="akn-p paragraph-custom akn--text-normal akn--text-left">First</span><span class="akn-p akn--text-xxsmall">Second</span></td><td class="akn-td akn--text-small"><span class="akn-p">Other</span></td></tr></tbody></table>';
      const content = Object.assign({}, Backbone.Events, {
        document: sourceXml, getElementByScopedId: () => sourceXml.documentElement,
        replaceNode: (old, nodes) => { window.saved = new XMLSerializer().serializeToString(nodes[0]); }
      });
      const parent = {render: () => {}, htmlRenderer: {renderXmlElement: () => {
        const div = document.createElement('div'); div.innerHTML = fixture; return div;
      }}};
      window.view = new Indigo.TableEditorView({parent, documentContent: content});
      const container = document.querySelector('la-akoma-ntoso'); container.innerHTML = '<div class="akn--table-container">' + fixture + '<div id="table-note">Table footnote</div></div>';
      view.makeTablesEditable(container); view.editTable(container.querySelector('table'));
      // A detached fragment may contain a top-level table without a parentElement.
      const fragment = document.createDocumentFragment();
      const table = document.createElement('table'); table.id = 'fragment-table'; fragment.append(table);
      view.makeTablesEditable(fragment);
      if (!fragment.querySelector('.table-editor-wrapper table')) throw new Error('Detached table was not wrapped');
    });
    await page.waitForFunction(() => window.view.table && window.view.ckeditor.status === 'ready');
    assert.equal(await page.evaluate(() => view.ckeditor.getData().includes('fontsize')), false);
    assert.equal(await page.evaluate(() => view.editable.contains(document.getElementById('table-note'))), false);
    assert.equal(await page.evaluate(() => view.editable.parentElement.contains(document.getElementById('table-note'))), true);
    // Exercise the real rendered wrapper and real CSS: a dropdown must escape
    // the short table, while only the table scrolls horizontally.
    await page.evaluate(() => {
      const wrapper = view.editable.closest('.table-editor-wrapper');
      wrapper.style.width = '450px';
      view.table.style.minWidth = '1100px';
    });
    await openTableFormatting();
    const layout = await page.evaluate(() => {
      const wrapper = view.editable.closest('.table-editor-wrapper');
      const toggle = wrapper.querySelector('.table-format-toggle');
      const menu = toggle.nextElementSibling;
      const last = menu.lastElementChild;
      const rect = last.getBoundingClientRect();
      const hit = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
      const toggleLeft = toggle.getBoundingClientRect().left;
      const tableLeft = view.table.getBoundingClientRect().left;
      const scroller = view.editable.closest('.akn--table-container');
      const scrollable = scroller.scrollWidth > scroller.clientWidth;
      scroller.scrollLeft = 100;
      return {menuVisible: last.contains(hit), extendsBelowTable: rect.bottom > view.editable.getBoundingClientRect().bottom,
        scrollable, scrolled: scroller.scrollLeft > 0,
        toolbarMovement: toggle.getBoundingClientRect().left - toggleLeft,
        tableMovement: view.table.getBoundingClientRect().left - tableLeft};
    });
    assert.equal(layout.extendsBelowTable, true);
    assert.equal(layout.menuVisible, true, 'dropdown is visible beyond the short table');
    assert.equal(layout.scrollable, true);
    assert.equal(layout.scrolled, true, 'the table area scrolls horizontally');
    assert.equal(layout.toolbarMovement, 0, 'horizontal scrolling leaves the toolbar in place');
    assert.equal(layout.tableMovement, -100);
    await page.click('.table-format-toggle');
    await page.evaluate(() => {
      view.editable.closest('.akn--table-container').scrollLeft = 0;
      view.table.style.removeProperty('min-width');
      view.editable.closest('.table-editor-wrapper').style.removeProperty('width');
    });

    // Saving without changes must preserve authored table/cell/paragraph classes and legacy fontsize.
    let saved = await page.evaluate(() => { view.saveChanges(); return window.saved; });
    assert.match(saved, /class="custom akn--text-small"/);
    assert.match(saved, /fontsize="9"/);
    assert.match(saved, /class="(?=[^"]*cell-custom)(?=[^"]*akn--text-right)[^"]*"/);
    assert.match(saved, /<p class="(?=[^"]*paragraph-custom)(?=[^"]*akn--text-normal)(?=[^"]*akn--text-left)[^"]*">First<\/p>/);
    assert.match(saved, /<p class="akn--text-xxsmall">Second<\/p>/);
    await page.evaluate(() => view.editTable(document.querySelector('la-akoma-ntoso table')));
    await page.waitForFunction(() => window.view.table && window.view.ckeditor.status === 'ready');
    await page.evaluate(() => {
      const cells = Array.from(view.table.querySelectorAll('td'));
      cells.forEach(c => c.classList.add('cke_table-faked-selection'));
      view.updateToolbar();
    });
    assert.equal(await page.$eval('.table-cell-size-label', e => e.textContent.trim()), 'Mixed');
    // Real Bootstrap dropdowns preserve selection and stay open for table controls.
    await openTableFormatting();
    await page.select('[data-format-target="table"][data-format="size"]', 'normal');
    await page.select('[data-format-target="table"][data-format="alignment"]', 'justify');
    await page.click('.table-remove-padding');
    assert.equal(await page.$eval('.table-toggle-border', el => el.type), 'checkbox');
    await page.evaluate(() => {
      view.table.querySelector('td').classList.add('akn--no-border');
      view.updateToolbar();
    });
    // Legacy cell flags represented a whole-table PDF setting; unchecking clears them.
    assert.equal(await page.$eval('.table-toggle-border', el => el.checked), true);
    await page.click('.table-toggle-border');
    assert.equal(await page.evaluate(() => view.table.querySelector('.akn--no-border') === null), true);
    await page.click('.table-toggle-border');
    assert.equal(await page.evaluate(() => view.table.classList.contains('akn--no-border')), true);
    const borderStyles = await page.evaluate(() => {
      const nodes = [view.table, ...view.table.querySelectorAll('th, td')];
      const read = () => nodes.map(el => { const s = getComputedStyle(el); return [s.borderTopWidth, s.borderTopStyle]; });
      const editing = read();
      document.body.classList.remove('document-editor-view');
      const published = read();
      document.body.classList.add('document-editor-view');
      return {editing, published};
    });
    assert.ok(borderStyles.editing.every(border => border[0] === '1px' && border[1] === 'dashed'));
    assert.ok(borderStyles.published.every(border => border[0] === '0px'));

    assert.equal(await page.evaluate(() => view.table.querySelector('.akn--no-border') === null), true);
    await page.click('.table-toggle-border');
    assert.equal(await page.evaluate(() => view.table.classList.contains('akn--no-border')), false);
    assert.equal(await page.$eval('.table-format-toggle', el => el.getAttribute('aria-expanded')), 'true');
    if (process.env.TABLE_EDITOR_SCREENSHOT) await page.screenshot({path: process.env.TABLE_EDITOR_SCREENSHOT, fullPage: true});
    await page.click('.table-format-toggle');
    await chooseCellSize('xxsmall');
    await page.click('.table-text-left');
    assert.equal(await page.evaluate(() => view.table.querySelector('td').classList.contains('akn--text-left')), true);
    await page.click('.table-text-default');
    assert.equal(await page.evaluate(() => view.table.querySelector('td').classList.contains('akn--text-left')), false);
    await page.click('.table-text-justify');
    if (process.env.TABLE_EDITOR_SCREENSHOT) {
      await page.click('.table-cell-size-toggle');
      await page.screenshot({path: process.env.TABLE_EDITOR_SCREENSHOT.replace('.png', '-cells.png'), fullPage: true});
      await page.click('.table-cell-size-toggle');
    }
    // A caret selection must survive focus moving to a size selector.
    await page.evaluate(() => {
      view.table.querySelectorAll('td').forEach(c => c.classList.remove('cke_table-faked-selection'));
      const range = view.ckeditor.createRange();
      range.moveToElementEditStart(new CKEDITOR.dom.element(view.table.querySelector('td')));
      view.ckeditor.getSelection().selectRanges([range]);
      view.updateToolbar();
    });
    await chooseCellSize('xsmall');
    assert.equal(await page.evaluate(() => view.table.querySelector('td').classList.contains('akn--text-xsmall')), true);
    await chooseCellSize('xxsmall');
    await page.evaluate(() => view.table.setAttribute('fontsize', '123'));
    saved = await page.evaluate(() => { view.saveChanges(); return window.saved; });
    assert.match(saved, /fontsize="9"/);
    assert.match(saved, /class="(?=[^"]*custom)(?=[^"]*akn--text-normal)(?=[^"]*akn--text-justify)(?=[^"]*akn--no-padding)[^"]*"/);
    assert.match(saved, /class="(?=[^"]*cell-custom)(?=[^"]*akn--text-xxsmall)(?=[^"]*akn--text-justify)[^"]*"/);
    assert.match(saved, /class="(?=[^"]*paragraph-custom)(?=[^"]*akn--text-normal)(?=[^"]*akn--text-left)[^"]*"/);
    // Cancel restores the exact original rendered table and never calls replaceNode.
    await page.evaluate(() => { window.saved = null; window.original = document.querySelector('la-akoma-ntoso table').outerHTML; view.editTable(document.querySelector('la-akoma-ntoso table')); });
    await page.waitForFunction(() => window.view.table && window.view.ckeditor.status === 'ready');
    await openTableFormatting();
    await page.select('[data-format-target="table"][data-format="size"]', 'xsmall');
    await page.evaluate(() => view.discardChanges(true));
    assert.equal(await page.evaluate(() => window.saved), null);
    assert.equal(await page.evaluate(() => document.querySelector('la-akoma-ntoso table').outerHTML === window.original), true);
    // No selected cell means cell controls are disabled, table controls remain available.
    await page.evaluate(() => view.editTable(document.querySelector('la-akoma-ntoso table')));
    await page.waitForFunction(() => window.view.table && window.view.ckeditor.status === 'ready');
    await page.evaluate(() => { view.ckeditor.getSelection().removeAllRanges(); view.updateToolbar(); });
    assert.equal(await page.$$eval('[data-selected-cells]', nodes => nodes.every(n => n.disabled)), true);
    assert.equal(await page.$eval('[data-format-target="table"]', e => e.disabled), false);
    assert.equal(await page.$eval('.table-toggle-border', e => e.disabled), false);
    await openTableFormatting();
    await page.click('.table-toggle-border');
    assert.equal(await page.evaluate(() => view.table.classList.contains('akn--no-border')), true);
    // HTML cannot introduce an override absent from the original XML.
    await page.evaluate(() => {
      sourceXml.documentElement.removeAttribute('fontsize');
      view.table.setAttribute('fontsize', '123');
    });
    assert.equal(await page.evaluate(() => view.ckeditor.filter.check('table[fontsize]')), false);
    saved = await page.evaluate(() => { view.saveChanges(); return window.saved; });
    assert.doesNotMatch(saved, /fontsize=/);
    assert.match(saved, /class="[^"]*akn--no-border[^"]*"/);
    // One language-neutral corpus is consumed by Python and the actual JS planner.
    const cases = JSON.parse(fs.readFileSync(path.join(root, 'indigo_api/tests/table_layout_cases.json'), 'utf8')).cases;
    const results = await page.evaluate(cases => cases.map(test => {
      const plan = new Indigo.TableLayout(test.rows, test.columns === undefined ? null : test.columns).plan();
      const doc = new DOMParser().parseFromString('<table xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>', 'text/xml');
      const table = doc.documentElement;
      if (test.columns) {
        const group = doc.createElementNS(table.namespaceURI, 'colgroup');
        for (const width of test.columns) { const col = doc.createElementNS(table.namespaceURI, 'col'); col.setAttribute('width', width + '%'); group.append(col); }
        table.append(group);
      }
      for (const row of test.rows) {
        const tr = doc.createElementNS(table.namespaceURI, 'tr');
        for (const attrs of row) {
          const td = doc.createElementNS(table.namespaceURI, 'td');
          for (const name of ['colspan', 'rowspan', 'style']) if (attrs[name] !== undefined) td.setAttribute(name, attrs[name]);
          tr.append(td);
        }
        table.append(tr);
      }
      const original = new XMLSerializer().serializeToString(table);
      view.removeRedundantColspans(table);
      const xml = new XMLSerializer().serializeToString(table);
      const savedPlan = Indigo.TableLayout.fromTable(table).plan();
      return {plan, savedPlan, xml, unchanged: xml === original};
    }), cases);
    function closeNumbers (actual, expected, name) {
      assert.equal(actual.length, expected.length, name);
      actual.forEach((n, i) => assert.ok(Math.abs(n - expected[i]) < 1e-7, `${name}: ${n} != ${expected[i]}`));
    }
    cases.forEach((test, i) => {
      const result = results[i];
      if (test.expected === null) { assert.equal(result.plan, null, test.name); assert.equal(result.unchanged, true, test.name); return; }
      assert.ok(result.plan, test.name);
      const spans = test.rows.map(() => []);
      result.plan.cells.forEach(cell => spans[cell.row].push(cell.colspan));
      assert.deepEqual(spans, test.expected.spans, test.name);
      closeNumbers(result.plan.compact_widths, test.expected.widths, test.name);
      assert.ok(result.savedPlan, test.name + ' saved plan');
      closeNumbers(result.savedPlan.widths, test.expected.widths, test.name + ' saved widths');
    });
    if (process.env.TABLE_LAYOUT_RESULTS) fs.writeFileSync(process.env.TABLE_LAYOUT_RESULTS, JSON.stringify(results));
    // Saving an otherwise unchanged real CKEditor table cleans both outer and nested spans.
    await page.evaluate(() => {
      fixture = '<table id="t1" data-eid="t1" class="akn-table custom akn--text-small"><tr><th colspan="3" rowspan="1" class="cell-custom" style="width:35%"><p data-eid="p1" class="paragraph-custom akn--text-left">First</p><p class="akn--text-normal">Second</p></th><td colspan="3" style="width:65%">Value</td></tr><tr><td colspan="3"><table><tr><td colspan="4">Nested A</td><td colspan="4">Nested B</td></tr></table></td><td colspan="3">Other</td></tr></table>';
      const html = new DOMParser().parseFromString(fixture, 'text/html').querySelector('table');
      const xml = indigoAkn.htmlToAkn(html).firstElementChild;
      xml.setAttribute('fontsize', '9');
      sourceXml = new DOMParser().parseFromString(new XMLSerializer().serializeToString(xml), 'text/xml');
      view.documentContent.document = sourceXml;
      window.saved = null;
      view.editTable(document.querySelector('la-akoma-ntoso table'));
    });
    await page.waitForFunction(() => window.view.table && window.view.ckeditor.status === 'ready');
    assert.equal(await page.evaluate(() => view.ckeditor.getData().includes('colspan="3"')), true);
    await page.evaluate(() => view.discardChanges(true));
    assert.equal(await page.evaluate(() => window.saved), null);
    assert.equal(await page.evaluate(() => sourceXml.querySelector('th').getAttribute('colspan')), '3');
    await page.evaluate(() => view.editTable(document.querySelector('la-akoma-ntoso table')));
    await page.waitForFunction(() => window.view.table && window.view.ckeditor.status === 'ready');
    const normalized = await page.evaluate(() => {
      view.saveChanges();
      const table = new DOMParser().parseFromString(window.saved, 'text/xml').documentElement;
      return {spans: table.querySelectorAll('[colspan]').length, tables: table.querySelectorAll('table').length,
        classes: table.getAttribute('class'), fontsize: table.getAttribute('fontsize'), heading: table.querySelector('th').getAttribute('class'),
        rowspan: table.querySelector('th').getAttribute('rowspan'), width: table.querySelector('th').getAttribute('style'),
        paragraphs: Array.from(table.querySelector('th').children).map(el => [(el.getAttribute('class') || '').split(/\s+/).sort().join(' '), el.getAttribute('eId'), el.textContent])};
    });
    assert.equal(normalized.spans, 0);
    assert.equal(normalized.tables, 1);
    assert.match(normalized.classes, /custom/);
    assert.match(normalized.classes, /akn--text-small/);
    assert.equal(normalized.fontsize, '9');
    assert.equal(normalized.heading, 'cell-custom');
    assert.equal(normalized.rowspan, '1');
    assert.match(normalized.width, /35%/);
    assert.deepEqual(normalized.paragraphs, [['akn--text-left paragraph-custom', 'p1', 'First'], ['akn--text-normal', null, 'Second']]);
    console.log('PASS: unclipped dropdowns and horizontal table scrolling, formatting, unchanged save/cancel, selection controls, ' + cases.length + ' shared layout cases, and real CKEditor save normalization with nested tables and metadata preservation');
  } finally {
    if (browser) await browser.close();
    server.close();
    fs.rmSync(temp, {recursive: true, force: true});
  }
}
run().catch(e => { console.error(e); process.exitCode = 1; });
