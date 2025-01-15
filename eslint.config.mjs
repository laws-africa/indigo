import globals from "globals";
import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    ignores: ["indigo_app/static/javascript/indigo/bluebell-monaco.js"],
  },
  {
    rules: {
      "no-undef": "off",
      "no-unused-vars": "off"
    }
  },
  {
    languageOptions: {
      globals: globals.browser
    }
  },
];
