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
      try {
        return await this.parseWithPyodide(text, frbr_uri, fragment, eidPrefix);
      } catch (e) {
        console.error('Error parsing with pyodide, will fall back to server:', e);
      }
    }

    return await this.parseWithServer(text, frbr_uri, fragment, eidPrefix);
  }

  async parseWithPyodide (text, frbr_uri, fragment, eidPrefix) {
    console.log('Parsing with pyodide');
    const [error, resp] = this.pyodide.globals.get('parseBluebellText')(text, frbr_uri, fragment, eidPrefix);
    // check for error
    if (error) {
      throw resp;
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
