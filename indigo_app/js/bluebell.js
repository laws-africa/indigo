import initBluebellWasm, { parseToXml, version } from '@lawsafrica/bluebell-wasm/bluebell_wasm.js';
import bluebellWasmUrl from '@lawsafrica/bluebell-wasm/bluebell_wasm_bg.wasm';

if (!window.Indigo) window.Indigo = {};
const Indigo = window.Indigo;
const AKN_NS = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0';

/**
 * Parses bluebell text into Akoma Ntoso XML.
 *
 * Either uses bluebell-wasm to parse in the browser, or sends the text to the server to be parsed.
 */
class BluebellParser {
  static setupWasm () {
    if (!BluebellParser.wasmSetup) {
      BluebellParser.wasmSetup = initBluebellWasm({ module_or_path: bluebellWasmUrl });
    }
    return BluebellParser.wasmSetup;
  }

  static sourceFromIndigo () {
    const showAs = Indigo.indigoOrganisation || '';
    return {
      showAs,
      eid: showAs.replace(/[^a-zA-Z0-9]/g, '-'),
      href: Indigo.indigoUrl || ''
    };
  }

  constructor (url, headers, source) {
    this.url = url;
    this.headers = headers;
    this.source = source || BluebellParser.sourceFromIndigo();
    this.wasm = null;
  }

  async setup () {
    if (!this.wasm) {
      await this.setupWasm();
    }
  }

  async setupWasm () {
    await BluebellParser.setupWasm();
    this.wasm = { parseToXml, version };
    console.log('bluebell-wasm setup complete: ' + this.wasm.version());
    return this.wasm;
  }

  async parse (text, frbrUri, fragment, eidPrefix) {
    try {
      await this.setup();
    } catch (e) {
      console.error('Error setting up bluebell-wasm, will fall back to server:', e);
      return await this.parseWithServer(text, frbrUri, fragment, eidPrefix);
    }

    if (this.wasm) {
      return this.parseWithWasm(text, frbrUri, fragment, eidPrefix);
    }

    return await this.parseWithServer(text, frbrUri, fragment, eidPrefix);
  }

  parseWithWasm (text, frbrUri, fragment, eidPrefix) {
    console.log('Parsing with bluebell-wasm');
    const root = fragment || this.getRoot(frbrUri);
    const start = performance.now();

    try {
      const xml = this.wasm.parseToXml(text, root, frbrUri, eidPrefix || '', this.source);
      const elapsed = performance.now() - start;
      const n = text.length;
      console.log(`bluebell-wasm parse of ${n} bytes completed in ${elapsed.toFixed(2)}ms`, { root, fragment: !!fragment });
      return fragment ? this.wrapFragment(xml) : xml;
    } catch (e) {
      const elapsed = performance.now() - start;
      console.warn(`bluebell-wasm parse failed in ${elapsed.toFixed(2)}ms`, e);
      throw this.errorMessage(e);
    }
  }

  errorMessage (error) {
    if (error && error.message) {
      return error.message;
    }

    return String(error);
  }

  getRoot (frbrUri) {
    const parts = frbrUri.split('/').filter((part) => part);
    return parts[2];
  }

  wrapFragment (xml) {
    return `<akomaNtoso xmlns="${AKN_NS}">${xml}</akomaNtoso>`;
  }

  async parseWithServer (text, frbrUri, fragment, eidPrefix) {
    const body = {
      content: text
    };

    if (fragment) {
      body.fragment = fragment;
    }

    if (eidPrefix) {
      body.id_prefix = eidPrefix;
    }

    const resp = await fetch(this.url, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(body)
    });

    if (resp.ok) {
      return (await resp.json()).output;
    } else if (resp.status === 400) {
      throw (await resp.json()).content || resp.statusText;
    } else {
      throw resp.statusText;
    }
  }
}

Indigo.BluebellParser = BluebellParser;

export default BluebellParser;
