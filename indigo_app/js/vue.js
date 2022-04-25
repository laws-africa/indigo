import Vue from 'vue';

/**
 * Registers all vue components as globals, so that they can be overridden and used without explicit imports.
 * @param components object mapping component names to component objects
 */
export function registerComponents (components) {
  for (const component of Object.values(components)) {
    Vue.component(component.name, component);
  }
}

/**
 * Fetch a Vue component from the Vue component registry and create it.
 * @param name the name of the component
 * @param options options to pass to the component constructor
 * @returns {*}
 */
export function createComponent (name, options) {
  const Component = Vue.extend(Vue.options.components[name]);
  return new Component(options);
}

/**
 * Get the global Vue instance.
 * @returns {Vue | VueConstructor}
 */
export function getVue () {
  return Vue;
}
