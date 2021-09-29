import app from "./indigo";
import Vue from "vue";

window.addEventListener("indigo.beforecreateviews", () => {
  window.indigoApp = app;
  window.indigoApp.Vue = Vue;
  app.setup();
});
