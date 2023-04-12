(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.grammars = {
    registry: {
      bluebell: exports.bluebellMonaco.BluebellGrammarModel
    }
  };
})(window);
