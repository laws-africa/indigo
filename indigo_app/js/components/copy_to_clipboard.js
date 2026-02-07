export default class CopyToClipboard {
  constructor (element) {
    this.element = element;
    this.element.addEventListener('click', (event) => this.copyText(event));
  }

  async copyText (event) {
    this.element.disabled = true;
    const originalTextContent = this.element.textContent;
    let textToCopy = this.element.getAttribute('data-value');

    // TODO: hack for getting the live text editor value when the button is clicked
    if (textToCopy === 'getTextEditorValue') {
      textToCopy = window.Indigo.view.sourceEditorView.aknTextEditor.monacoEditor.getValue();
    }

    if (textToCopy) {
      try {
        await navigator.clipboard.writeText(textToCopy);
        this.element.textContent = this.element.getAttribute('data-confirmation');
      } catch (error) {
        this.element.textContent = this.element.getAttribute('data-failure');
      }
    } else {
      this.element.textContent = this.element.getAttribute('data-failure');
    }

    setTimeout(() => {
      this.element.textContent = originalTextContent;
      this.element.disabled = false;
    }, 500);
  }
}
