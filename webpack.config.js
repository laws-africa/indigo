const path = require('path');
const { VueLoaderPlugin } = require('vue-loader');
const ESLintPlugin = require('eslint-webpack-plugin');
const MonacoWebpackPlugin = require('monaco-editor-webpack-plugin');

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
  optimization: {
    usedExports: 'global'
  },
  output: {
    filename: 'external-imports.js',
    path: path.resolve(__dirname, 'indigo_app/static/lib'),
    chunkFormat: false
  }
};

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
      exclude: ['**/legacy.js']
    }),
  ]
};

const bluebellMonacoConfig = {
  entry: './indigo_app/js/bluebell-monaco.src.js',
  mode: 'production',
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ['css-loader']
      }
    ],
  },
  optimization: {
    usedExports: 'global',
  },
  output: {
    filename: 'bluebell-monaco.js',
    path: path.resolve(__dirname, 'indigo_app/static/javascript/indigo'),
    chunkFormat: false
  }
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


module.exports = [legacyConfig, appConfig, bluebellMonacoConfig, monacoConfig];
