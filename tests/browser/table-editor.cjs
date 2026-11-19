/* Real CKEditor + HTML-to-AKN integration. Run with:
 * CHROME_BIN=/path/to/chrome INDIGO_AKN_SOURCE=/path/to/indigo-akn npm run test:table-editor
 * Without INDIGO_AKN_SOURCE, use the installed dependency.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const puppeteer = require('puppeteer-core');
const webpack = require('webpack');

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
  const scripts = ['bower_components/jquery/dist/jquery.js', 'bower_components/underscore/underscore.js', 'bower_components/backbone/backbone.js', 'ckeditor/ckeditor.js', 'javascript/indigo/views/table_editor.js'];
  const html = `<!doctype html><html><head><link rel="stylesheet" href="/static/stylesheets/app.css"></head><body>${toolbar}<div class="document-primary-pane-content-pane"><la-akoma-ntoso></la-akoma-ntoso></div>${scripts.map(s => `<script src="/static/${s}"></script>`).join('')}<script src="/bootstrap.js"></script><script src="/converter.js"></script></body></html>`;
  const server = http.createServer((req, res) => {
    if (req.url === '/') { res.end(html); return; }
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
      const container = document.querySelector('la-akoma-ntoso'); container.innerHTML = fixture;
      view.makeTablesEditable(container); view.editTable(container.querySelector('table'));
    });
    await page.waitForFunction(() => window.view.table && window.view.ckeditor.status === 'ready');
    assert.equal(await page.evaluate(() => view.ckeditor.getData().includes('fontsize')), false);
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
    console.log('PASS: unchanged save, formatting save, mixed selection, explicit Left/Default, cancel, disabled controls (real CKEditor + converter)');
  } finally {
    if (browser) await browser.close();
    server.close();
    fs.rmSync(temp, {recursive: true, force: true});
  }
}
run().catch(e => { console.error(e); process.exitCode = 1; });
