import Vue from 'vue';
import * as vueComponents from './components';

class IndigoApp {
  setup () {
    this.components = [];

    this.registerVueComponents(vueComponents);
    window.dispatchEvent(new Event('indigo.vue-components-registered'));

    this.createComponents();
    window.dispatchEvent(new Event('indigo.components-created'));
  }

  /**
   * Registers all vue components as globals, so that they can be overridden and used without explicit imports.
   */
  registerVueComponents (components) {
    for (const component of Object.values(components)) {
      Vue.component(component.name, component);
    }
  }

  createComponents () {
    // create vue-based components
    for (const element of document.querySelectorAll('[data-vue-component]')) {
      const name = element.getAttribute('data-vue-component');

      if (Vue.options.components[name]) {
        // create the component and attached it to the HTML element
        const Component = Vue.extend(Vue.options.components[name]);
        const vue = new Component({ el: element });
        this.components.push(vue);
      }
    }
  }
}

export default new IndigoApp();
