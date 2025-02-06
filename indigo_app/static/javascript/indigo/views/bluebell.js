/**
 * Parses bluebell text into Akoma Ntoso XML.
 *
 * Either uses pyodide to run the python code in the browser, or sends the text to the server to be parsed.
 */
class BluebellParser {
  constructor (url, headers) {
    this.url = url;
    this.headers = headers;
    this.pyodide = null;
    // python dependencies
    this.packages = Indigo.pyodide_packages;
    this.pyBootstrap = `
import json
from bluebell.parser import AkomaNtosoParser, ParseError
from cobalt import FrbrUri
from cobalt.akn import AKN_NAMESPACES, DEFAULT_VERSION
from lxml import etree

# parse bluebell text and return an [error, result] tuple
def parseBluebellText(text, frbr_uri, fragment, eid_prefix):
    # see indigo.pipelines.base.ParseBluebellText for context
    frbr_uri = FrbrUri.parse(frbr_uri)
    frbr_uri.work_component = 'main'
    root = fragment or frbr_uri.doctype

    try:
        parser = AkomaNtosoParser(frbr_uri, eid_prefix or '')
        xml = parser.parse_to_xml(text, root)
    except ParseError as e:
        return True, str(e)

    if fragment:
        # fragment must be wrapped in AKN tags
        xml = etree.tostring(xml, encoding='unicode')
        ns = AKN_NAMESPACES[DEFAULT_VERSION]
        xml = f'<akomaNtoso xmlns="{ns}">{xml}</akomaNtoso>'
        return False, xml

    xml = etree.tostring(xml, encoding='unicode')
    return False, xml

def rewriteEids(xml, frbr_uri, provision_counters, eid_counter):
    # see indigo_api.views.documents.ParseView.check_rewrite_eids for context
    frbr_uri = FrbrUri.parse(frbr_uri)
    parser = AkomaNtosoParser(frbr_uri)
    parser.generator.ids.counters = json.loads(provision_counters)
    parser.generator.ids.eid_counter = json.loads(eid_counter)
    xml = etree.fromstring(xml)
    parser.generator.ids.rewrite_eid(xml)
    return etree.tostring(xml, encoding='unicode')
`;
  }

  async setup () {
    if (window.loadPyodide && this.packages && this.packages.length) {
      let pyodide = await loadPyodide();

      // install dependencies
      console.log('Installing pyodide packages: ' + this.packages);
      await pyodide.loadPackage("micropip");
      const micropip = pyodide.pyimport("micropip");
      await micropip.install(this.packages);

      // run the bootstrap code
      pyodide.runPython(this.pyBootstrap);

      this.pyodide = pyodide;
      console.log('Pyodide setup complete');
    } else {
      console.log('No pyodide packages to install');
    }
  }

  async parse (text, frbr_uri, fragment, eidPrefix) {
    if (this.pyodide) {
      return this.parseWithPyodide(text, frbr_uri, fragment, eidPrefix);
    } else {
      return this.parseWithServer(text, frbr_uri, fragment, eidPrefix);
    }
  }

  async parseWithPyodide (text, frbr_uri, fragment, eidPrefix) {
    console.log('Parsing with pyodide');
    const [error, resp] = this.pyodide.globals.get('parseBluebellText')(text, frbr_uri, fragment, eidPrefix);
    // check for error
    if (error) {
      throw resp;
    }
    // in provision mode at the top level only, re-write the eids taking into account the injected counters
    if (Indigo.Preloads.provisionEid && !eidPrefix) {
      const provision_counters = JSON.stringify(Indigo.Preloads.provisionCounters);
      const eid_counter = JSON.stringify(Indigo.Preloads.eidCounter);
      return this.pyodide.globals.get('rewriteEids')(resp, frbr_uri, provision_counters, eid_counter);
    }
    return resp;
  }

  async parseWithServer (text, frbr_uri, fragment, eidPrefix) {
    const body = {
      content: text,
    };

    if (fragment) {
      body.fragment = fragment;
    }

    if (eidPrefix) {
      body.id_prefix = eidPrefix;
    }

    if (Indigo.Preloads.provisionEid) {
      body.provision_counters = JSON.parse(JSON.stringify(Indigo.Preloads.provisionCounters));
      body.eid_counter = JSON.parse(JSON.stringify(Indigo.Preloads.eidCounter));
    }

    const resp = await fetch(this.url, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(body),
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
