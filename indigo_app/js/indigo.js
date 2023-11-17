import * as vueComponents from './components';
import {
  LaAkomaNtoso,
  LaGutter,
  LaGutterItem,
  LaTableOfContentsController,
  LaTableOfContents,
  LaTocItem,
  LaDecorateExternalRefs,
  LaDecorateInternalRefs,
  LaDecorateTerms
} from '@lawsafrica/law-widgets/dist/components';
import './compat-imports';
import { relativeTimestamps } from './timestamps';
import htmx from 'htmx.org';
import { createComponent, getVue, registerComponents } from './vue';

customElements.define('la-akoma-ntoso', LaAkomaNtoso);
customElements.define('la-gutter', LaGutter);
customElements.define('la-gutter-item', LaGutterItem);
customElements.define('la-decorate-external-refs', LaDecorateExternalRefs);
customElements.define('la-decorate-internal-refs', LaDecorateInternalRefs);
customElements.define('la-decorate-terms', LaDecorateTerms);
customElements.define('la-table-of-contents-controller', LaTableOfContentsController);
customElements.define('la-table-of-contents', LaTableOfContents);
customElements.define('la-toc-item', LaTocItem);

class IndigoApp {
  setup () {
    this.components = [];
    this.componentLibrary = {};
    this.Vue = getVue();
    this.setupHtmx();

    registerComponents(vueComponents);
    window.dispatchEvent(new Event('indigo.vue-components-registered'));

    this.createComponents(document);
    this.createVueComponents(document);
    window.dispatchEvent(new Event('indigo.components-created'));
  }

  setupHtmx () {
    window.htmx = htmx;
    document.body.addEventListener('htmx:configRequest', (e) => {
      e.detail.headers['X-CSRFToken'] = window.Indigo.csrfToken;
    });
    document.body.addEventListener('htmx:load', (e) => {
      // mount components on new elements
      this.createComponents(e.target);
      this.createVueComponents(e.target);
      relativeTimestamps(e.target);
    });
  }

  createComponents (root) {
    // create components
    for (const element of root.querySelectorAll('[data-component]')) {
      this.createComponent(element);
    }
  }

  createComponent (element) {
    const name = element.getAttribute('data-component');

    if (this.componentLibrary[name]) {
      // create the component and attach it to the HTML element
      this.components.push(element.component = new this.componentLibrary[name](element));
    }
  }

  /**
   * Create Vue-based components on this root and its descendants.
   * @param root
   */
  createVueComponents (root) {
    // create vue-based components
    for (const element of root.querySelectorAll('[data-vue-component]')) {
      this.createVueComponent(element);
    }
  }

  createVueComponent (element) {
    const name = element.getAttribute('data-vue-component');

    if (this.Vue.options.components[name]) {
      // create the component and attach it to the HTML element
      const vue = createComponent(name, { el: element });
      vue.$el.component = vue;
      this.components.push(vue);
    }
  }
}

export default new IndigoApp();
