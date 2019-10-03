(function(exports) {
  "use strict";

  // South Africa
  exports.Indigo.traditions.za = new Indigo.Tradition({
    country: 'za',
    grammar: Indigo.traditions.default.settings.grammar,
    annotatable: Indigo.traditions.default.settings.annotatable,
    toc: {
      elements: Indigo.traditions.default.settings.toc.elements,
      titles: {
        // just rely on the defaults
      },
    },
  });
})(window);
