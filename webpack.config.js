const path = require('path');

module.exports = {
  entry: './indigo_app/js/external-imports.src.js',
  mode: 'production',
  output: {
    filename: 'external-imports.js',
    path: path.resolve(__dirname, 'indigo_app/static/lib'),
  }
};
