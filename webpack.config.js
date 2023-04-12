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
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
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
    },
    extensions: ['.tsx', '.ts', '.js'],
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
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

const bluebellMonaco = {
  entry: './indigo_app/js/bluebell-monaco.src.js',
  mode: 'production',
  module: {
    rules: [{
      test: /\.css$/,
      use: ['css-loader']
    }],
  },
  output: {
    filename: 'bluebell-monaco.js',
    path: path.resolve(__dirname, 'indigo_app/static/javascript/indigo'),
  }
};


module.exports = [legacyConfig, appConfig, bluebellMonaco];
