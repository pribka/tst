const path = require('path')
//const DuplicatePackageCheckerPlugin = require("duplicate-package-checker-webpack-plugin")
const zlib = require('zlib')
const CompressionPlugin = require('compression-webpack-plugin')
const webpack = require('webpack')
const TerserPlugin = require('terser-webpack-plugin')
const CKEditorWebpackPlugin = require( '@ckeditor/ckeditor5-dev-webpack-plugin' )
const { styles } = require( '@ckeditor/ckeditor5-dev-utils' )
const createThemeColorReplacerPlugin = require('./src/config/plugin.config.js')
const buildDate = JSON.stringify(new Date().toLocaleString())
/*const RetryChunkLoadPlugin = require('webpack-retry-chunk-load-plugin').RetryChunkLoadPlugin
  || require('webpack-retry-chunk-load-plugin').default
  || require('webpack-retry-chunk-load-plugin')*/

const isProd = process.env.NODE_ENV === 'production'
const isDev = !isProd
const proxyHostHeader = process.env.VUE_APP_PROXY_HOST_HEADER
//const RETRY_ENABLED = process.env.VUE_APP_RETRY_CHUNKS !== '0'

const vueConfig = {
    pwa: isProd ? {
        themeColor: '#e6efe3',
        msTileColor: '#e6efe3',
        appleMobileWebAppCapable: 'no',
        appleMobileWebAppStatusBarStyle: 'default',
        workboxPluginMode: 'InjectManifest',
        workboxOptions: {
            swSrc: 'src/config/service-worker.js',
            exclude: [/\.map$/, /media/, /frontend-media/, /_redirects/, /audio/]
        },
        manifestOptions: false,
        iconPaths: {
            favicon32: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/favicon-32x32.png` : 'img/icons/favicon-32x32.png',
            favicon16: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/favicon-16x16.png` : 'img/icons/favicon-16x16.png',
            appleTouchIcon: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/apple-touch-icon-152x152.png` : 'img/icons/apple-touch-icon-152x152.png',
            maskIcon: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/safari-pinned-tab.svg` : 'img/icons/safari-pinned-tab.svg',
            msTileImage: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/msapplication-icon-144x144.png` : 'img/icons/msapplication-icon-144x144.png'
        }
    } : {
        iconPaths: {
            favicon32: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/favicon-32x32.png` : 'img/icons/favicon-32x32.png',
            favicon16: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/favicon-16x16.png` : 'img/icons/favicon-16x16.png',
            appleTouchIcon: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/apple-touch-icon-152x152.png` : 'img/icons/apple-touch-icon-152x152.png',
            maskIcon: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/safari-pinned-tab.svg` : 'img/icons/safari-pinned-tab.svg',
            msTileImage: process.env.VUE_APP_CODE_NAME ? `img/${process.env.VUE_APP_CODE_NAME}/icons/msapplication-icon-144x144.png` : 'img/icons/msapplication-icon-144x144.png'
        }
    },
    publicPath: '/',
    productionSourceMap: false,
    transpileDependencies: [
        /ckeditor5-[^/\\]+[/\\]src[/\\].+\.js$/,
        '@gtm-support/core',
        '@gtm-support/vue2-gtm',
        '@dhx/trial-gantt',
        /^@sentry/,
        /^@sentry-internal/
    ],
    pluginOptions: {
        compression:{
            brotli: {
                filename: '[file].br[query]',
                algorithm: 'brotliCompress',
                include: /\.(js|css|html|svg|json)(\?.*)?$/i,
                compressionOptions: {
                    params: {
                        [zlib.constants.BROTLI_PARAM_QUALITY]: 11
                    }
                },
                minRatio: 0.8
            },
            gzip: {
                filename: '[file].gz[query]',
                algorithm: 'gzip',
                include: /\.(js|css|html|svg|json)(\?.*)?$/i,
                minRatio: 0.8
            }
        }
    },
    configureWebpack: {
        output: {
            filename: isDev ? 'test-bkz-page-[name].[hash:28].js' : '[name]-legacy.[contenthash:8].js',
            chunkFilename: isDev ? 'js/[name].[hash:28].js' : 'js/[name].[contenthash:8].js',
            path: path.resolve(__dirname, 'dist'),
            pathinfo: false,
            crossOriginLoading: 'anonymous'
        },
        performance: {
            hints: false
        },
        devtool: isDev ? 'source-map' : false,
        optimization: {
            runtimeChunk: 'single',
            splitChunks: {
                chunks: 'all',
                maxInitialRequests: 30,
                maxAsyncRequests: 30,
                minSize: 20000,
                automaticNameDelimiter: '-',
                cacheGroups: {
                    ckeditor: {
                        test: /[\\/]node_modules[\\/]@ckeditor[\\/]/,
                        name: 'chunk-ckeditor',
                        priority: 20,
                        reuseExistingChunk: true
                    },
                    antdv: {
                        test: /[\\/]node_modules[\\/]ant-design-vue[\\/]/,
                        name: 'chunk-antdv',
                        priority: 15,
                        reuseExistingChunk: true
                    },
                    aggrid: {
                        test: /[\\/]node_modules[\\/](ag-grid-community|ag-grid-vue)[\\/]/,
                        name: 'chunk-aggrid',
                        priority: 15,
                        reuseExistingChunk: true
                    },
                    fullcalendar: {
                        test: /[\\/]node_modules[\\/]@fullcalendar[\\/]/,
                        name: 'chunk-fullcalendar',
                        priority: 14,
                        reuseExistingChunk: true
                    },
                    leaflet: {
                        test: /[\\/]node_modules[\\/]leaflet[\\/]/,
                        name: 'chunk-leaflet',
                        priority: 13,
                        reuseExistingChunk: true
                    },
                    vendors: {
                        test: /[\\/]node_modules[\\/]/,
                        name: 'chunk-vendors',
                        priority: 10,
                        reuseExistingChunk: true
                    }
                }
            },
            minimize: isProd,
            minimizer: isProd ? [
                new TerserPlugin({
                    terserOptions: {
                        compress: {
                            drop_console: false,
                            drop_debugger: false
                        },
                        format: { comments: false }
                    },
                    extractComments: false,
                    parallel: true,
                    cache: true
                })
            ] : []
        },
        module: {
            rules: [
                {
                    test: /\.js$/,
                    include: /node_modules\/@ckeditor/,
                    use: [
                        {
                            loader: 'babel-loader',
                            options: {
                                presets: ['@babel/preset-env'],
                            },
                        }
                    ]
                }
            ]
        },
        plugins: [
            //new DuplicatePackageCheckerPlugin(),
            new webpack.IgnorePlugin({
                resourceRegExp: /^\.\/locale$/,
                contextRegExp: /moment$/
            }),
            new webpack.ContextReplacementPlugin(/moment[/\\]locale$/, /en|kk|ru/),
            new CKEditorWebpackPlugin({
                language: 'ru',
                additionalLanguages: ['kk','en'],
                translationsOutputFile: /app/,
            }),
            /*...(isProd && RETRY_ENABLED ? [new RetryChunkLoadPlugin({
                retryDelay: 1500,
                maxRetries: 2,
                cacheBust: `function(){try{return 'v='+(window.__APP_BUILD_VERSION||'${require('./package.json').version}')}catch(e){return 'v='+Date.now()}}`,
                test: `function(url){
                  try{
                    var u=new URL(url,window.location.origin)
                    if(u.origin!==window.location.origin) return false
                    return /\\.js($|\\?)/.test(u.pathname)
                  }catch(e){
                    return false
                  }
                }`,
                lastResortScript: `if(window.__onceChunkReload){}else{window.__onceChunkReload=true;location.reload()}`
            })] : [])*/
        ]
    },
    devServer: {
        disableHostCheck: true,
        proxy: {
            "^/api": {
                target: process.env.VUE_APP_PROXY_TARGET,
                changeOrigin: true,
                onProxyReq(proxyReq) {
                    if (proxyHostHeader) {
                        proxyReq.setHeader('Host', proxyHostHeader)
                    }
                },
                pathRewrite: {
                    '^/api': '/api'
                }
            }
            /*
            Для работы голосовых в чате хэлпдэска
            '^/download_file': {
                target: process.env.VUE_APP_PROXY_TARGET,
                changeOrigin: true,
                secure: false
            }
            */
        }
    },
    css: {
        extract: isProd,
        sourceMap: false,
        loaderOptions: {
            sass: {
                sassOptions: {
                    silenceDeprecations: ['import', 'legacy-js-api']
                }
            },
            less: {
                lessOptions: {
                    modifyVars: {
                        'primary-color': '#4777FF',
                        'border-color-base': '#d9d9d9',
                        'border-radius-base': '8px',
                        'cyan-6': '#04d182',
                        'text-color': '#505050'
                    },
                    javascriptEnabled: true
                }
            }
        }
    },
    chainWebpack: config => {
        config.resolve.alias
            .set('@apps', path.resolve(__dirname, './src/modules'))
            .set('AutoNumeric', path.resolve(__dirname, './node_modules/autonumeric/dist/autoNumeric.min'))
            .set('lodash$', 'lodash-es')
            .set('moment', path.resolve(__dirname, './node_modules/moment'))

        config.plugin('define').tap(args => {
            args[0]['process.env'].VUE_APP_VERSION = `"${require("./package.json").version}"`
            args[0]['process.env'].VUE_APP_BUILD_DATE = buildDate
            return args
        })
        config.plugins.delete('prefetch')
        config.plugin('preload').tap(options => {
            options[0].include = 'initial'
            return options
        })

        const svgRule = config.module.rule( 'svg' )
        svgRule.exclude.add( path.join( __dirname, 'node_modules', '@ckeditor' ) )

        config.module
            .rule('js')
            .exclude.add(/node_modules\/@ckeditor/).end()

        config.module
            .rule( 'cke-svg' )
            .test( /ckeditor5-[^/\\]+[/\\]theme[/\\]icons[/\\][^/\\]+\.svg$/ )
            .use( 'raw-loader' )
            .loader( 'raw-loader' )

        config.module
            .rule( 'cke-css' )
            .test( /ckeditor5-[^/\\]+[/\\].+\.css$/ )
            .use( 'postcss-loader' )
            .loader( 'postcss-loader' )
            .tap( () => {
                return styles.getPostCssConfig( {
                    themeImporter: {
                        themePath: require.resolve( '@ckeditor/ckeditor5-theme-lark' ),
                    },
                    minify: true
                })
            })

        // Avoid collision with backend /media route in production.
        config.module
            .rule('media')
            .use('url-loader')
            .tap(options => ({
                ...options,
                name: 'frontend-media/[name].[hash:8].[ext]',
                fallback: {
                    ...options.fallback,
                    options: {
                        ...options.fallback?.options,
                        name: 'frontend-media/[name].[hash:8].[ext]'
                    }
                }
            }))
    }
}

vueConfig.configureWebpack.plugins.push(createThemeColorReplacerPlugin())

module.exports = vueConfig
