const path = require('path');
const { VueLoaderPlugin } = require('vue-loader');
const ESLintPlugin = require('eslint-webpack-plugin');
const MonacoWebpackPlugin = require('monaco-editor-webpack-plugin');

const appConfig = {
  entry: './indigo_app/js/main.js',
  mode: 'production',
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
    chunkFormat: false
  },
  plugins: [
    new VueLoaderPlugin(),
    new ESLintPlugin({
      files: 'indigo_app/js/**/*.{js,vue}',
      exclude: ['**/legacy.js', 'node_modules/**', '**/*.ts']
    }),
  ]
};

const monacoConfig = {
  entry: './indigo_app/js/monaco.src.js',
  mode: 'production',
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      },
      {
        test: /\.ttf$/,
        use: ['file-loader']
      }
    ],
  },
  plugins: [new MonacoWebpackPlugin({
    languages: ['xml'],
    filename: '[name].worker.[contenthash].js',
  })],
  optimization: {
    usedExports: 'global',
  },
  output: {
    filename: 'monaco.js',
    path: path.resolve(__dirname, 'indigo_app/static/javascript/monaco'),
    chunkFormat: false
  }
};


module.exports = [appConfig, monacoConfig];
