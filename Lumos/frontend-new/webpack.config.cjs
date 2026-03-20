const HtmlWebpackPlugin = require('html-webpack-plugin');
const path = require('path');

module.exports = {
  entry: {
    main: './src/main.jsx',
    admin: './src/Admin.jsx',
    behavior: './src/UserBehavior.jsx',
    interestGraph: './src/InterestGraph.jsx',
  },
  output: {
    filename: 'bundle.[contenthash].js',
    path: path.resolve(__dirname, 'dist'),
    clean: true,
    publicPath: '/',
  },
  resolve: {
    extensions: ['.js', '.jsx'],
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
          },
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.svg$/,
        type: 'asset/resource',
      },
      {
        test: /\.(png|jpe?g|gif|ico)$/,
        type: 'asset/resource',
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './index.html',
      filename: 'index.html',
      chunks: ['main'],
    }),
    new HtmlWebpackPlugin({
      template: './admin.html',
      filename: 'admin.html',
      chunks: ['admin'],
    }),
    new HtmlWebpackPlugin({
      template: './behavior.html',
      filename: 'behavior.html',
      chunks: ['behavior'],
    }),
    new HtmlWebpackPlugin({
      template: './interest-graph.html',
      filename: 'interest-graph.html',
      chunks: ['interestGraph'],
    }),
  ],
  devServer: {
    static: [
      {
        directory: path.join(__dirname, 'dist'),
      },
      {
        directory: path.join(__dirname, 'public'),
        publicPath: '/',
      },
    ],
    port: 3000,
    hot: false,
    historyApiFallback: true,
    proxy: [
      {
        context: ['/api'],
        target: process.env.BACKEND_URL || 'http://localhost:5000',
        changeOrigin: true,
      },
    ],
  },
};
