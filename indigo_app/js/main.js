// preserve imports for legacy code
import './external-imports.src';
import indigo from './indigo';

window.addEventListener('DOMContentLoaded', () => {
  console.log('indigo-app loaded');
  window.indigo = indigo;
  indigo.setup();
});
