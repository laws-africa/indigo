import app from "./indigo";

window.addEventListener("indigo.beforecreateviews", () => {
  window.indigoApp = app;
  app.setup();
});
