import Vue from 'vue';
import * as vueComponents from './components';

class IndigoApp {
  setup () {
    this.components = [];
    this.Vue = Vue;

    this.registerVueComponents(vueComponents);
    window.dispatchEvent(new Event('indigo.vue-components-registered'));

    this.createVueComponents(document);
    window.dispatchEvent(new Event('indigo.components-created'));
    window.globalVue = Vue;
  }

  /**
   * Registers all vue components as globals, so that they can be overridden and used without explicit imports.
   */
  registerVueComponents (components) {
    for (const component of Object.values(components)) {
      this.Vue.component(component.name, component);
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
      // create the component and attached it to the HTML element
      const Component = this.Vue.extend(this.Vue.options.components[name]);
      const vue = new Component({ el: element });
      vue.$el.component = vue;
      this.components.push(vue);
    }
  }
}

export default new IndigoApp();
