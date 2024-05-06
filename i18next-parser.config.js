module.exports = {
  "defaultNamespace": "indigo_app",
  "locales": [
    "en",
    "fr"
  ],
  "keySeparator": false,
  "lexers": {
    "js": [
      {
        "lexer": "JavascriptLexer",
        "functions": ["t", "$t"]
      }
    ]
  },
  "input": [
    "indigo_app/static/javascript/indigo/**/*.js",
  ],
  "output": "indigo_app/static/i18n/$NAMESPACE-$LOCALE.json"
}
