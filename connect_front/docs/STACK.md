# Technology Stack
> Vue 2 SPA with Vuex state management, built by Vue CLI/Webpack, serving a corporate CRM/collaboration platform.

## Languages

**Primary:**
- JavaScript (ES2020+) — all application code in `src/`
- No TypeScript; uses Babel for transpilation

**Styles:**
- SCSS — global styles at `src/assets/css/main.scss`
- Less — component-level and Ant Design theming at `src/assets/css/var.less`
- Tailwind CSS (JIT mode, postcss7-compat) — utility classes, purged from `src/**/*.{vue,js}`

## Runtime

**Environment:**
- Node.js (no `.nvmrc`; targeted at Node 14+ based on packages)

**Package Manager:**
- npm
- Lockfile: `package-lock.json` (present)

## Frameworks

**Core:**
- Vue 2 `^2.6.14` — component framework
- Vuex `^3.4.0` — centralized state, modules in `src/store/modules/`
- Vue Router `^3.2.0` — SPA routing, dynamic route loading from backend, configured in `src/config/router.js`
- vue-i18n `^8.28.2` — runtime i18n with lazy-loaded locale files from `src/lang/`, supports `ru`, `kk`, `en`

**UI Component Library:**
- Ant Design Vue `^1.7.8` — primary component kit; many components are wrapped/extended in `src/modules/UIModules/antDesign/`
- Tree-shaken via `babel-plugin-import`; Less variables overridden in `vue.config.js` (`primary-color: #4777FF`)

**CSS Utilities:**
- Tailwind CSS `npm:@tailwindcss/postcss7-compat@^2.2.14` — configured in `tailwind.config.js` (JIT, no dark mode)

**Charts/Visualization:**
- ApexCharts `^3.35.0` + vue-apexcharts `^1.6.2`
- Chart.js `^3.7.1` + vue-chartjs `^4.0.6`
- AG Grid `ag-grid-community ^30.2.1` + `ag-grid-vue ^30.2.1` — data grid
- FullCalendar `^6.1.8` (daygrid, timegrid, list, multimonth, interaction, moment) — calendar views
- DHX Gantt `@dhx/trial-gantt ^9.0.4` — Gantt chart (trial license)
- Leaflet `^1.8.0` + vue2-leaflet `^2.7.1` + geosearch + routing machine + markercluster — maps

**Rich Text Editor:**
- CKEditor 5 (Vue2 adapter `@ckeditor/ckeditor5-vue2 ^1.0.5`) — custom build with 20+ plugins as devDependencies
- Built with `@ckeditor/ckeditor5-dev-webpack-plugin`; locales: ru, kk, en

**Testing:**
- Jest `^29.5.0`
- `@vue/cli-plugin-unit-jest ^5.0.8` + `@vue/test-utils ^1.1.3`
- `@testing-library/vue ^5.9.0`
- Config: `jest.config.js` (minimal: `preset: '@vue/cli-plugin-unit-jest'`)
- Test command: `vue-cli-service test:unit`

**Build/Dev:**
- Vue CLI `@vue/cli-service ~4.5.13` with Webpack 4 (pinned via `overrides.webpack: 4.46.0`)
- Babel `@vue/cli-plugin-babel ~4.5.13`, preset `@vue/cli-plugin-babel/preset`
- TerserPlugin `^4.2.3` — minification in production
- CompressionPlugin `compression-webpack-plugin ^6.1.1` — gzip + brotli (quality 11) static assets
- vue-cli-plugin-compression `1.0.3`
- `cross-env ^7.0.3` — cross-platform env vars in npm scripts

## Key Dependencies

**HTTP:**
- axios `^0.21.4` — two configured instances: `src/config/axios.js` (main API) and `src/config/axiosPush.js` (push notification service)

**Real-time:**
- socket.io-client `^4.4.1` — WebSocket connection to backend, configured in `src/config/socket.js`
- vue-socket.io-extended `^4.2.0` — Vue integration for socket.io

**Utilities:**
- lodash `^4.17.21` (aliased to `lodash-es` in webpack for tree-shaking)
- moment `^2.29.1` — dates; locale-aware, overrides in `src/utils/moment-overrides/`
- uuid `^8.3.2` — UUID generation
- device-uuid `^1.0.4` — device fingerprinting
- imask `^6.4.2` — input masking
- autonumeric `^4.6.0` + vue-autonumeric `^1.2.6` — number formatting
- vue-virtual-scroller `^1.1.2` — virtual lists
- vuedraggable `^2.24.3` — drag-and-drop lists
- vue-pdf-embed `^1.2.1` — inline PDF rendering
- cropperjs `^1.5.12` — image cropping
- lazysizes `^5.3.2` — lazy image loading
- swiper `5.2.0` + vue-awesome-swiper `^4.1.1` — touch sliders
- lightgallery.js `1.1.3` + lg-zoom, lg-thumbnail, lg-fullscreen, lg-rotate — image/media gallery
- tippy.js `^6.3.7` + vue-tippy `^4.11.0` — tooltips
- vue-grid-layout `^2.4.0` — drag-resize dashboard widgets
- vuescroll `^4.17.3` — custom scrollbar
- vue-infinite-loading `^2.4.5` — infinite scroll
- vue-qrcode-component `^2.1.1` — QR code display
- vue-excel-export `^0.1.3` — Excel file export
- leaflet-routing-machine `^3.2.12` + leaflet-geosearch `^3.7.0`

**PWA:**
- `@vue/cli-plugin-pwa ^4.5.17` + `register-service-worker ^1.7.2`
- Custom service worker: `src/config/service-worker.js` (Workbox InjectManifest mode)

## Configuration

**Environment:**
- Multiple `.env` mode files: `.env.production`, `.env.bkz`, `.env.connect`, `.env.dcstand`, `.env.production_dc`
- Key env vars consumed by the app:
  - `VUE_APP_API_URL` — backend REST API base URL
  - `VUE_APP_PUSH_API_URL` — push notification service URL
  - `VUE_APP_SOCKET_HOST` + `VUE_APP_SOCKET_PATH` — Socket.IO server
  - `VUE_APP_CSRF_NAME` — CSRF cookie name
  - `VUE_APP_AUTH_URL` — auth service URL
  - `VUE_APP_MAIN_COLOR` — default primary theme color
  - `VUE_APP_PUSH_KEY` — Web Push VAPID public key
  - `VUE_APP_SENTRY_DSN`, `VUE_APP_SENTRY_ENV`, `VUE_APP_SENTRY_PROJECT` — Sentry (currently commented out)
  - `VUE_APP_YM_ID` — Yandex Metrika counter ID
  - `VUE_APP_GIPHY_API_KEY` — Giphy API key for GIF picker
  - `VUE_APP_CODE_NAME` — skin/brand identifier for icon paths

**Build:**
- `vue.config.js` — webpack config, chunk splitting (ckeditor, antdv, aggrid, fullcalendar, leaflet, vendors), brotli/gzip compression
- `babel.config.js` — `@vue/cli-plugin-babel/preset` + `babel-plugin-import` for Ant Design tree-shaking
- `tailwind.config.js` — JIT purge mode
- `jsconfig.json` — path alias `@/*` → `src/*`

## Platform Requirements

**Development:**
- Dev server: `vue-cli-service serve --host d.centersoft.kz --port 8080`
- Proxy: `/api` → `VUE_APP_PROXY_TARGET` (configured in `vue.config.js` devServer)
- High memory build option: `dev4gb` script uses `--max-old-space-size=4096`

**Production:**
- Output: `dist/` with gzip + brotli pre-compressed assets
- Served behind nginx (see `nginx/` directory)
- `productionSourceMap: false`
- Build variants: `build` (production), `buildbkz`, `buildc` (dcstand), `buildconnect`
- Version written to `version.json` by `scripts/write-version.js` before each build

---

*Stack analysis: 2026-04-17*
