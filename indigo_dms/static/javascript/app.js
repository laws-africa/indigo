$(function() {
  "use strict";

  // TODO: how do we know to load this view?
  var view = new DocumentView();
  window.view = view;

  view.document.set('title', 'foo');
});
