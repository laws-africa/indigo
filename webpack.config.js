const path = require('path');
const { VueLoaderPlugin } = require('vue-loader')

module.exports = {
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
  ]
};
