// const path = require('path');
const path = require("path");
const { composePlugins, withNx } = require("@nx/webpack");
const { withReact } = require("@nx/react");
const { merge } = require("webpack-merge");

require("dotenv").config({
  // resolve the .env file in the root of the project ../
  path: path.resolve(__dirname, "../.env"),
});

const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const {
  EnvironmentPlugin,
  DefinePlugin,
  ProgressPlugin,
  optimize,
} = require("webpack");
const TerserPlugin = require("terser-webpack-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");

const RELEASE = require("./release").getReleaseName();

const css_prefix = "sf-";
const mode = process.env.BUILD_MODULE
  ? "production"
  : process.env.NODE_ENV || "development";
const isDevelopment = mode !== "production";
const devtool =
  process.env.NODE_ENV === "production"
    ? "source-map"
    : "cheap-module-source-map";
const FRONTEND_HMR = process.env.FRONTEND_HMR === "true";
const FRONTEND_HOSTNAME = FRONTEND_HMR
  ? process.env.FRONTEND_HOSTNAME || "http://localhost:8010"
  : "";
const DJANGO_HOSTNAME = process.env.DJANGO_HOSTNAME || "http://127.0.0.1:8080";
const HMR_PORT = FRONTEND_HMR ? +new URL(FRONTEND_HOSTNAME).port : 8010;

const LOCAL_ENV = {
  NODE_ENV: mode,
  CSS_PREFIX: css_prefix,
  RELEASE_NAME: RELEASE,
};

const BUILD = {
  NO_MINIMIZE: isDevelopment || !!process.env.BUILD_NO_MINIMIZATION,
};

const CopyPlugin = require("copy-webpack-plugin");

const plugins = [
  new MiniCssExtractPlugin(),
  // new CopyPlugin({
  //   patterns: [],
  // }),
  new DefinePlugin({
    "process.env.CSS_PREFIX": JSON.stringify(css_prefix),
  }),
  new EnvironmentPlugin(LOCAL_ENV),
];

const optimizer = () => {
  const result = {
    minimize: true,
    minimizer: [],
  };

  if (mode === "production") {
    result.minimizer.push(
      new TerserPlugin({
        parallel: true,
      }),
      new CssMinimizerPlugin({
        parallel: true,
      })
    );
  }

  if (BUILD.NO_MINIMIZE) {
    result.minimize = false;
    result.minimizer = undefined;
  }

  if (process.env.MODE?.startsWith("standalone")) {
    result.runtimeChunk = false;
    result.splitChunks = { cacheGroups: { default: false } };
  }

  return result;
};

// Nx plugins for webpack.
module.exports = composePlugins(
  withNx({
    nx: {
      svgr: true,
    },
    skipTypeChecking: true,
  }),
  withReact({ svgr: true }),
  (config) => {
    // Synapse entrypoint
    if (!process.env.MODE?.startsWith("standalone")) {
      config.entry = {
        main: {
          import: path.resolve(__dirname, "apps/synapse/src/main.tsx"),
        },
      };

      config.output = {
        ...config.output,
        uniqueName: "synapse",
        publicPath:
          isDevelopment && FRONTEND_HOSTNAME
            ? `${FRONTEND_HOSTNAME}/react-app/`
            : process.env.MODE === "standalone-playground"
            ? "/playground-assets/"
            : "auto",
        scriptType: "text/javascript",
      };

      config.optimization = {
        runtimeChunk: "single",
        sideEffects: true,
        splitChunks: {
          cacheGroups: {
            commonVendor: {
              test: /[\\/]node_modules[\\/](react|react-dom|react-router|react-router-dom|mobx|mobx-react|mobx-react-lite|mobx-state-tree)[\\/]/,
              name: "vendor",
              chunks: "all",
            },
            defaultVendors: {
              test: /[\\/]node_modules[\\/]/,
              priority: -10,
              reuseExistingChunk: true,
              chunks: "async",
            },
            default: {
              minChunks: 2,
              priority: -20,
              reuseExistingChunk: true,
              chunks: "async",
            },
          },
        },
      };
    }

    config.resolve.fallback = {
      fs: false,
      path: false,
      crypto: false,
      worker_threads: false,
    };

    config.experiments = {
      cacheUnaffected: true,
      syncWebAssembly: true,
      asyncWebAssembly: true,
    };

    config.module.rules.forEach((rule) => {
      const testString = rule.test.toString();
      const isScss = testString.includes("scss");
      const isCssModule = testString.includes(".module");

      if (isScss) {
        rule.oneOf.forEach((loader) => {
          if (loader.use) {
            const cssLoader = loader.use.find(
              (use) => use.loader && use.loader.includes("css-loader")
            );

            if (cssLoader && cssLoader.options) {
              cssLoader.options.modules = {
                mode: "local",
                auto: true,
                namedExport: false,
                localIdentName: "[local]--[hash:base64:5]",
              };
            }
          }
        });
      }

      if (rule.test.toString().match(/scss|sass/) && !isCssModule) {
        const r = rule.oneOf.filter((r) => {
          // we don't need rules that don't have loaders
          if (!r.use) return false;

          const testString = r.test.toString();

          // we also don't need css modules as these are used directly
          // in the code and don't need prefixing
          if (testString.match(/module|raw|antd/)) return false;

          // we only target pre-processors that has 'css-loader included'
          return (
            testString.match(/scss|sass/) &&
            r.use.some((u) => u.loader && u.loader.includes("css-loader"))
          );
        });

        r.forEach((_r) => {
          const cssLoader = _r.use.find(
            (use) => use.loader && use.loader.includes("css-loader")
          );

          if (!cssLoader) return;

          const isSASS = _r.use.some(
            (use) => use.loader && use.loader.match(/sass|scss/)
          );

          if (isSASS) _r.exclude = /node_modules/;

          if (cssLoader.options) {
            cssLoader.options.modules = {
              localIdentName: `${css_prefix}[local]`, // Customize this format
              getLocalIdent(_ctx, _ident, className) {
                if (className.includes("ant")) return className;
              },
            };
          }
        });
      }

      if (testString.includes(".css")) {
        rule.exclude = /tailwind\.css/;
      }
    });

    config.module.rules.push(
      {
        test: /\.svg$/,
        exclude: /node_modules/,
        use: [
          {
            loader: "@svgr/webpack",
            options: {
              ref: true,
            },
          },
          "url-loader",
        ],
      },
      {
        test: /\.xml$/,
        exclude: /node_modules/,
        loader: "url-loader",
      },
      {
        test: /\.wasm$/,
        type: "javascript/auto",
        loader: "file-loader",
        options: {
          name: "[name].[ext]",
        },
      },
      // tailwindcss
      {
        test: /tailwind\.css/,
        exclude: /node_modules/,
        use: [
          "style-loader",
          {
            loader: "css-loader",
            options: {
              importLoaders: 1,
            },
          },
          "postcss-loader",
        ],
      }
    );

    // Suppress source map and SCSS deprecation warnings
    config.ignoreWarnings = [
      {
        module: /node_modules\/parse5/,
      },
      (warning) => {
        return (
          warning.message &&
          (warning.message.includes("Failed to parse source map") ||
            warning.message.includes("Sass @import rules are deprecated") ||
            warning.message.includes("Deprecation Warning") ||
            warning.message.includes("repetitive deprecation warnings omitted"))
        );
      },
    ];

    if (isDevelopment) {
      config.optimization = {
        ...config.optimization,
        moduleIds: "named",
      };
    }

    config.resolve.alias = {
      // Common dependencies across at least two sub-packages
      react: path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      "react-joyride": path.resolve(__dirname, "node_modules/react-joyride"),
      "@synapse/ui": path.resolve(__dirname, "libs/ui"),
      "@synapse/core": path.resolve(__dirname, "libs/core"),
    };

    return merge(config, {
      devtool,
      mode,
      plugins,
      optimization: optimizer(),
      devServer: process.env.MODE?.startsWith("standalone")
        ? {}
        : {
            // Port for the Webpack dev server
            port: HMR_PORT,
            // Enable HMR
            hot: true,
            headers: { 
              "Access-Control-Allow-Origin": "*",
              "Cross-Origin-Opener-Policy": "same-origin",
              "Cross-Origin-Embedder-Policy": "require-corp",
              "Cross-Origin-Resource-Policy": "cross-origin",
            },
            static: {
              directory: path.resolve(__dirname, "../synapse/core/static/"),
              publicPath: "/static/",
            },
            devMiddleware: {
              publicPath: `${FRONTEND_HOSTNAME}/react-app/`,
            },
            allowedHosts: "all", // Allow access from Django's server
            proxy: [
              {
                context: ["/api", "/user", "/admin", "/django-rq", "/static", "/data", "/media", "/storage-data"],
                target: `${DJANGO_HOSTNAME}`,
                changeOrigin: true,
                secure: false,
              },
              {
                context: ["/"],
                target: `${DJANGO_HOSTNAME}`,
                changeOrigin: true,
                secure: false,
              },
            ],
          },
    });
  }
);
