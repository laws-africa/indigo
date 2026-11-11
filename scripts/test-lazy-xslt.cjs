// Run with: node --experimental-vm-modules scripts/test-lazy-xslt.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

(async () => {
  let constructions = 0;
  let imports = 0;
  const context = vm.createContext({
    XMLSerializer: class { serializeToString(node) { return node; } }
  });
  const module = new vm.SourceTextModule(fs.readFileSync('indigo_app/js/xml.js', 'utf8'), { context });
  await module.link(() => { throw new Error('Unexpected import'); });
  await module.evaluate();
  const xml = {};
  assert.throws(() => module.namespace.prettyPrintXml(xml), /XSLTProcessor/);
  context.DOMParser = class { parseFromString(text) { return text; } };
  context.XSLTProcessor = class {
    constructor() { constructions++; }
    importStylesheet() { imports++; }
    transformToDocument(node) { return node; }
  };
  assert.equal(module.namespace.prettyPrintXml(xml), xml);
  assert.equal(module.namespace.prettyPrintXml(xml), xml);
  assert.equal(constructions, 1);
  assert.equal(imports, 1);
  console.log('Lazy XML formatter: import without XSLT, retry and caching passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
