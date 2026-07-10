import initBluebellWasm, { parseToXml, version } from '@lawsafrica/bluebell-wasm/bluebell_wasm.js';

if (!window.Indigo) window.Indigo = {};
const Indigo = window.Indigo;

/**
 * Parses bluebell text into Akoma Ntoso XML.
 *
 * Either uses bluebell-wasm to parse in the browser, or sends the text to the server to be parsed.
 */
class BluebellParser {
  static setupWasm () {
    if (!BluebellParser.wasmSetup) {
      BluebellParser.wasmSetup = initBluebellWasm();
    }
    return BluebellParser.wasmSetup;
  }

  constructor (url, headers) {
    this.url = url;
    this.headers = headers;
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
      if (this.wasm) {
        return this.parseWithWasm(text, frbrUri, fragment, eidPrefix);
      }
    } catch (e) {
      console.error('Error parsing with bluebell-wasm, will fall back to server:', e);
    }

    return await this.parseWithServer(text, frbrUri, fragment, eidPrefix);
  }

  parseWithWasm (text, frbrUri, fragment, eidPrefix) {
    console.log('Parsing with bluebell-wasm');
    const xml = this.wasm.parseToXml(text, fragment || this.getRoot(frbrUri), frbrUri, eidPrefix || '');
    return fragment ? this.wrapFragment(xml) : xml;
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
