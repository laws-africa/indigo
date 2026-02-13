import app from './indigo';

document.addEventListener('DOMContentLoaded', () => {
  window.Indigo.app = app;
  app.setup();
});
