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
    this.packages = [
      "lxml",
      "https://files.pythonhosted.org/packages/6c/0c/f37b6a241f0759b7653ffa7213889d89ad49a2b76eb2ddf3b57b2738c347/iso8601-2.1.0-py3-none-any.whl",
      "https://files.pythonhosted.org/packages/15/83/d5be80b572064329066b8738e91f6b8dd42712007ae0c13e5e8911cdb1b0/cobalt-9.0.1-py3-none-any.whl",
      "https://files.pythonhosted.org/packages/c2/92/10103079d1ed56a950235ca23399d6a5bd3a38ea7d0c6c17b67e1dbc2abe/bluebell_akn-3.1.0-py3-none-any.whl",
    ]
    this.pyBootstrap = `
from bluebell.parser import AkomaNtosoParser
from cobalt import FrbrUri
from cobalt.akn import AKN_NAMESPACES, DEFAULT_VERSION
from lxml import etree

def parseBluebellText(text, frbr_uri, fragment, eid_prefix):
    # see indigo.pipelines.base.ParseBluebellText for context
    frbr_uri = FrbrUri.parse(frbr_uri)
    frbr_uri.work_component = 'main'
    root = fragment or frbr_uri.doctype

    parser = AkomaNtosoParser(frbr_uri, eid_prefix or '')
    xml = parser.parse_to_xml(text, root)

    if fragment:
        # fragment must be wrapped in AKN tags
        xml = etree.tostring(xml, encoding='unicode')
        ns = AKN_NAMESPACES[DEFAULT_VERSION]
        xml = f'<akomaNtoso xmlns="{ns}">{xml}</akomaNtoso>'
        return xml
            
    return etree.tostring(xml, encoding='unicode')
`;
  }

  async setup () {
    // TODO: where does this come from?
    let pyodide = await loadPyodide();

    //await pyodide.loadPackage("micropip");
    //micropip = pyodide.pyimport("micropip");
    //await micropip.install('bluebell-akn');

    await pyodide.loadPackage(this.packages);
    pyodide.runPython(this.pyBootstrap);

    this.pyodide = pyodide;
  }

  async parse (text, frbr_uri, fragment, eidPrefix) {
    if (this.pyodide) {
      return this.parseWithPyodide(text, frbr_uri, fragment, eidPrefix);
    } else {
      return this.parseWithServer(text, frbr_uri, fragment, eidPrefix);
    }
  }

  async parseWithPyodide (text, frbr_uri, fragment, eidPrefix) {
    return this.pyodide.globals.get('parseBluebellText')(text, frbr_uri, fragment, eidPrefix);
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
