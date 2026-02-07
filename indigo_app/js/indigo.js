import { components, vueComponents } from './components';
import * as indigoAkn from '@lawsafrica/indigo-akn';
import * as bluebellMonaco from '@lawsafrica/bluebell-monaco';
import '@lawsafrica/law-widgets/dist/components/la-akoma-ntoso';
import '@lawsafrica/law-widgets/dist/components/la-gutter';
import '@lawsafrica/law-widgets/dist/components/la-gutter-item';
import '@lawsafrica/law-widgets/dist/components/la-table-of-contents-controller';
import '@lawsafrica/law-widgets/dist/components/la-decorate-external-refs';
import '@lawsafrica/law-widgets/dist/components/la-decorate-internal-refs';
import '@lawsafrica/law-widgets/dist/components/la-decorate-terms';
import { relativeTimestamps } from './timestamps';
import * as enrichments from './enrichments/popups';
import htmx from 'htmx.org';
import { createComponent, getVue, registerComponents } from './vue';
import i18next from 'i18next';
import HttpApi from 'i18next-http-backend';
import tippy, { delegate } from 'tippy.js';
import 'tippy.js/dist/tippy.css';
import { setupLegacyJquery } from './legacy';
import setupXml from './xml';
import * as bootstrap from 'bootstrap';
import { fromRange as textPositionFromRange } from 'dom-anchor-text-position';

// make these libraries available globally for legacy code that expects them to be on the window
window.bootstrap = bootstrap;
window.indigoAkn = indigoAkn;
window.textPositionFromRange = textPositionFromRange;

window.tippy = tippy;

// Indigo is a global namespace for all things related to this app. It is a hold-over from the original Indigo
// vanilla javascript. It is still used by many vanilla JS components. It's mostly used to store singletons
// and registries that need to be accessed by multiple components.
if (!window.Indigo) window.Indigo = {};
const Indigo = window.Indigo;

// for registering remarks-related components
Indigo.remarks = {};

// for registering linting-related components
Indigo.Linting = {
  // map from names to linter functions
  linters: {}
};

// bluebell grammar
Indigo.grammars = {
  registry: {
    bluebell: bluebellMonaco.BluebellGrammarModel
  }
};

// make enrichments available to vanilla JS
Indigo.Enrichments = enrichments;

class IndigoApp {
  setup () {
    this.components = [];
    this.componentLibrary = {};
    this.Vue = getVue();
    this.setupI18n();
    this.setupCSRF();
    setupXml();

    window.dispatchEvent(new Event('indigo.beforebootstrap'));

    setupLegacyJquery();
    this.setupUser();
    this.setupMonaco();
    this.setupHtmx();
    this.setupPopups();
    this.setupTooltips();
    this.setupComponents();
    this.setupConfirm();
    this.setupToasts();

    window.dispatchEvent(new Event('indigo.beforecreateviews'));
    this.createLegacyViews();
    window.dispatchEvent(new Event('indigo.viewscreated'));

    this.disableWith();
    this.preventUnload();

    // osx vs windows
    const isOSX = navigator.userAgent.indexOf('OS X') > -1;
    document.body.classList.toggle('win', !isOSX);
    document.body.classList.toggle('osx', isOSX);

    window.dispatchEvent(new Event('indigo.afterbootstrap'));
  }

  setupCSRF () {
    Indigo.csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // legacy jquery/bootstrap ajax
    $.ajaxSetup({
      beforeSend: function (xhr, settings) {
        const requiresToken = !(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type));
        if (requiresToken && !this.crossDomain) {
          xhr.setRequestHeader('X-CSRFToken', Indigo.csrfToken);
        }
      }
    });
  }

  setupUser () {
    // setup legacy Backbone user model
    Indigo.user = new Indigo.User(Indigo.Preloads.user || {
      permissions: []
    });
  }

  setupMonaco () {
    // tell monaco where to load its files from
    window.require = {
      paths: {
        vs: '/static/lib/monaco-editor'
      }
    };
  }

  setupI18n () {
    const opts = Indigo.i18n;
    opts.backend = {};
    opts.backend.loadPath = function (languages, namespaces) {
      return opts.loadPaths[namespaces[0] + '-' + languages[0]];
    };
    i18next.use(HttpApi).init(opts);
    // setup a global translation function
    window.$t = i18next.t.bind(i18next);
  }

  setupHtmx () {
    window.htmx = htmx;
    // disable htmx's AJAX history; we don't use it, it causes problems with the back button and the cache, and
    // and it re-executes all javascript on the page
    htmx.config.refreshOnHistoryMiss = true;
    document.body.addEventListener('htmx:configRequest', (e) => {
      e.detail.headers['X-CSRFToken'] = Indigo.csrfToken;
    });
    document.body.addEventListener('htmx:beforeRequest', (e) => {
      Indigo.progressView.push();
    });
    document.body.addEventListener('htmx:afterRequest', (e) => {
      Indigo.progressView.pop();
    });
    // htmx:load is fired both when the page loads (weird) and when new content is loaded. We only care about the latter
    // case. See https://github.com/bigskysoftware/htmx/issues/1500
    const htmxHelper = { firstLoad: true };
    document.body.addEventListener('htmx:load', (e) => {
      if (htmxHelper.firstLoad) {
        htmxHelper.firstLoad = false;
        return;
      }
      // mount components on new elements
      this.createComponents(e.target);
      this.createVueComponents(e.target);
      relativeTimestamps(e.target);
      $('.selectpicker').selectpicker();
    });
    document.body.addEventListener('hx-messages', (e) => {
      e.detail.value.forEach(this.createToast);
    });
  }

  setupComponents () {
    for (const [name, component] of Object.entries(components)) {
      this.componentLibrary[name] = component;
    }

    registerComponents(vueComponents);
    window.dispatchEvent(new Event('indigo.vue-components-registered'));

    this.createComponents(document.body);
    this.createVueComponents(document.body);

    window.dispatchEvent(new Event('indigo.components-created'));
  }

  createToast (message) {
    // Clone the template
    const element = htmx.find('[data-toast-template]').cloneNode(true);

    // Remove the data-toast-template attribute
    delete element.dataset.toastTemplate;

    // Set the CSS class
    element.className += ' ' + message.tags;

    // Set the text
    htmx.find(element, '[data-toast-body]').innerText = message.message;

    // Add the new element to the container
    htmx.find('[data-toast-container]').appendChild(element);

    // Show the toast using Bootstrap's API
    // @ts-ignore
    const toast = new window.bootstrap.Toast(element, { delay: 5000 });
    toast.show();
  }

  createComponents (root) {
    // create components
    // check the root directly
    if (root.getAttribute('data-component')) {
      this.createComponent(root);
    }
    for (const element of root.querySelectorAll('[data-component]')) {
      this.createComponent(element);
    }
  }

  createComponent (element) {
    const name = element.getAttribute('data-component');

    if (this.componentLibrary[name] && !element.component) {
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

    if (this.Vue.options.components[name] && !element.component) {
      // create the component and attach it to the HTML element
      const vue = createComponent(name, { el: element, propsData: element.dataset });
      vue.$el.component = vue;
      this.components.push(vue);
    }
  }

  /** When a form is submitted, find elements that have data-disabled-with and disable them
   * and change their text to the value of data-disabled-with.
   */
  disableWith () {
    document.addEventListener('submit', (e) => {
      // we iterate over elements rather than use querySelector, because buttons may be outside the form
      // and link to it with their form attribute.
      for (const el of e.target.elements) {
        if (el.hasAttribute('data-disable-with')) {
          el.textContent = el.getAttribute('data-disable-with');
          el.removeAttribute('data-disable-with');
          // do this asynchronously, so that the form is submitted with the button value, if any
          setTimeout(() => {
            el.disabled = true;
          }, 10);
        }
      }
    });
  }

  /** Show popover when hovering on selected links. Links must have a 'data-popup-url' attribute. */
  setupPopups () {
    delegate('body', {
      target: 'a[data-popup-url]',
      content: '...',
      allowHTML: true,
      interactive: true,
      theme: 'light',
      placement: 'bottom-start',
      appendTo: document.body,
      onTrigger: async (instance, event) => {
        const url = event.currentTarget.getAttribute('data-popup-url');
        if (url) {
          try {
            const resp = await fetch(url);
            if (resp.ok) {
              instance.setContent(await resp.text());
            } else {
              instance.setContent(':(');
            }
          } catch (e) {
            // ignore errors
            console.log(e);
          }
        }
      }
    });
  }

  setupConfirm () {
    document.body.addEventListener('click', (event) => {
      const target = event.target.closest('a[data-confirm], button[data-confirm], input[data-confirm]');
      if (!target) {
        return;
      }

      const message = target.getAttribute('data-confirm');
      if (message && !confirm(message)) {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
      }
    });
  }

  setupToasts () {
    // hide auto-dismiss toasts after 3 seconds
    setTimeout(() => {
      for (const el of document.querySelectorAll('.alert-dismissible.auto-dismiss')) {
        window.bootstrap.Alert.getOrCreateInstance(el).close();
      }
    }, 3 * 1000);
  }

  createLegacyViews () {
    // Create legacy Backbone views based on the data-backbone-view attribute on the body.
    const viewsAttr = document.body.getAttribute('data-backbone-view') || '';
    const viewNames = viewsAttr.split(' ').filter((name) => name);
    const createdViews = [];

    for (const name of viewNames) {
      if (Indigo[name]) {
        const view = new Indigo[name]();
        Indigo.view = Indigo.view || view;
        window.dispatchEvent(new CustomEvent('indigo.createview', {
          detail: {
            name,
            view
          }
        }));
        createdViews.push(view);
      }
    }

    Indigo.views = createdViews;
    for (const view of Indigo.views) {
      if (view && typeof view.render === 'function') {
        view.render();
      }
    }
  }

  setupTooltips () {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]:not(.notooltip)'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      // eslint-disable-next-line no-undef
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  preventUnload () {
    // prevent navigating away from dirty views
    window.addEventListener('beforeunload', (e) => {
      if (Indigo.view && Indigo.view.isDirty && Indigo.view.isDirty()) {
        e.preventDefault();
        // eslint-disable-next-line no-undef
        return $t('You will lose your changes!');
      }
    });
  }
}

export default new IndigoApp();
