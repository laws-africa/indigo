const path = require('path');
const { VueLoaderPlugin } = require('vue-loader');
const ESLintPlugin = require('eslint-webpack-plugin');

const legacyConfig = {
  entry: './indigo_app/js/external-imports.src.js',
  mode: 'development',
  resolve: {
    modules: [
      './node_modules',
    ],
  },
  output: {
    filename: 'external-imports.js',
    path: path.resolve(__dirname, 'indigo_app/static/lib'),
  }
};

const appConfig = {
  entry: './indigo_app/js/main.js',
  mode: 'development',
  resolve: {
    modules: [
      './node_modules',
    ],
    alias: {
      vue: 'vue/dist/vue.esm.js',
    }
  },
  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue-loader'
      },
      {
        test: /\.css$/,
        use: ['vue-style-loader', 'css-loader']
      },
      {
        test: /\.scss$/,
        use: ['vue-style-loader', 'css-loader', 'sass-loader']
      }
    ]
  },
  output: {
    filename: 'indigo-app.js',
    path: path.resolve(__dirname, 'indigo_app/static/javascript'),
  },
  plugins: [
    new VueLoaderPlugin(),
    new ESLintPlugin(),
  ]
};


module.exports = [legacyConfig, appConfig];
