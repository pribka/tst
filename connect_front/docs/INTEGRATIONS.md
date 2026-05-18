# External Integrations
> The app integrates with a backend REST API, a real-time Socket.IO server, push notification service, and several third-party analytics/media services.

## APIs & External Services

**Backend REST API:**
- Primary HTTP client: `src/config/axios.js` — axios instance with `baseURL: VUE_APP_API_URL`
- Secondary HTTP client: `src/config/axiosPush.js` — axios instance with `baseURL: VUE_APP_PUSH_API_URL` (dedicated push/notification microservice)
- Auth: CSRF cookie (`VUE_APP_CSRF_NAME`), `withCredentials: true`, XSRF header `X-CSRFToken`
- Auto-logout on 401; retry on 503 (200ms delay); error surface via `throw response`
- All components access API via `Vue.prototype.$http` (main) and `Vue.prototype.$http2` (push)

**GIPHY API:**
- Endpoints: `https://api.giphy.com/v1/gifs/search` and `https://api.giphy.com/v1/gifs/trending`
- Used in: `src/components/Emoji.vue` — GIF picker tab in emoji popover
- Auth: `VUE_APP_GIPHY_API_KEY` (query param)
- Called directly via axios (no SDK)

**OnlyOffice (document preview):**
- File compatibility list in `src/utils/onlyoffice.js` (37 extension types: docx, xlsx, pptx, pdf, etc.)
- Integration: document preview URLs presumably constructed server-side; frontend only checks extension support

## Real-time Communication

**Socket.IO:**
- Client: `socket.io-client ^4.4.1`
- Vue plugin: `vue-socket.io-extended ^4.2.0`
- Config: `src/config/socket.js` — connects to `VUE_APP_SOCKET_HOST` at `VUE_APP_SOCKET_PATH`
- Transport: WebSocket with polling fallback
- Key event: `online_list` → updates `user/SET_ONLINE_USERS` in Vuex store (initialized once via `window.__socketPresenceListenersInited`)
- Used globally; socket instance exported from `src/config/socket.js` and passed to Vue via `Vue.use(VueSocketIOExt, socket)`

**Remote Access (VNC-style):**
- Constants in `src/utils/remoteAccess.js`: local WebSocket agent at `ws://127.0.0.1:9019`
- VNC ports: client and server both 443
- Represents a locally-running agent; browser connects via WebSocket to localhost agent

## Analytics & Monitoring

**Google Tag Manager:**
- SDK: `@gtm-support/vue2-gtm ^2.0.0`
- Container ID: `GTM-WR54QKMN` (hardcoded in `src/main.js`)
- Enabled: only when `NODE_ENV === 'production'` AND `VUE_APP_BUILD_TYPE === 'production'`
- Router-aware: `vueRouter: router` passed to GTM for automatic page-view tracking

**Yandex Metrika:**
- No npm package; injected as raw script via `vue-meta` in `src/utils/yandex-metrika.js`
- Counter ID: `VUE_APP_YM_ID`
- Features: `webvisor: true`, `clickmap: true`, `ecommerce: "dataLayer"`, `accurateTrackBounce: true`
- Script source: `https://mc.yandex.ru/metrika/tag.js`

**Sentry:**
- Packages: `@sentry/vue ^7.120.4`, `@sentry/browser ^7.120.4`, `@sentry/tracing ^7.120.4`
- Status: **currently commented out** in `src/main.js` — not active
- Config when enabled: `VUE_APP_SENTRY_DSN`, `VUE_APP_SENTRY_ENV`, `VUE_APP_SENTRY_PROJECT`
- Would use `BrowserTracing` with Vue Router instrumentation

## Push Notifications

**Web Push (Browser Push API):**
- Implementation: `src/utils/webPush.js`
- VAPID public key: `VUE_APP_PUSH_KEY`
- Subscription endpoints:
  - `POST /subscribe/subscribe/` via `axiosPush`
  - `POST /subscribe/update/` via `axiosPush` (fallback)
- Service worker handles `notificationclick` in `src/config/service-worker.js`
- Status: currently disabled (`initBrowserPush` is commented out in `src/main.js`)

## Mobile App Bridge

**React Native / Flutter WebView bridge:**
- Implementation: `src/utils/appBridge.js`
- Supports multiple bridge targets:
  - `window.ReactNativeWebView.postMessage` — React Native
  - `window.Flutter.postMessage` — Flutter
  - `window.webkit.messageHandlers.app.postMessage` — iOS WKWebView
  - `window.flutter_inappwebview.callHandler` — flutter_inappwebview plugin
- Messages include: `logout`, and presumably other action types
- Used for logout sync and likely other native-web interactions

## Authentication

**Auth Strategy:**
- Session/cookie-based (CSRF tokens, `withCredentials: true`)
- Auth URL: `VUE_APP_AUTH_URL` (separate auth service endpoint)
- Token refresh: code for `TokenService.getAccessToken` exists at `src/config/TokenService.js` but is currently commented out in `src/config/axios.js` — interceptor skips refresh and throws on 403/405
- Logout: `store.dispatch('user/logout')` + `location.reload()` on 401

## Tab Synchronization (BroadcastChannel)

**Cross-tab state sync:**
- `src/utils/tabSync.js` — uses `BroadcastChannel` API (fallback: localStorage events)
- Channel name: `recent_users_sync`
- `src/utils/chatSync.js` — syncs chat menu counters across tabs
- `src/utils/visibilityHub.js` — coordinates tab visibility state for sound/notification management
- `src/utils/soundMaster.js` — cross-tab audio coordination via `tabId`

## Local Storage / Browser APIs

**IndexedDB:**
- Custom wrapper in `src/utils/cacheDb.js` — raw `indexedDB` API, no library
- Used for: `src/indexedDb/filter.js` (filter state persistence) and `src/indexedDb/routeConfig.js` (route config caching)

**Service Worker / PWA:**
- Workbox InjectManifest mode, custom SW at `src/config/service-worker.js`
- Excludes: `.map`, `/media`, `/frontend-media`, `/_redirects`, `/audio` from precache
- Handles `notificationclick`, `SKIP_WAITING`, `GET_VERSION` messages
- Version check: fetches `/version.json` and broadcasts to all tabs

**Web Audio API:**
- `src/utils/sounds.js` + `src/utils/voicePlayback.js` — in-app sound playback (notifications, call ringing)
- `src/utils/voice.js` — `MediaRecorder` for voice message recording with echo cancellation, noise suppression, auto gain

## Maps

**Leaflet:**
- `leaflet ^1.8.0` + `vue2-leaflet ^2.7.1`
- Plugins: `leaflet-geosearch ^3.7.0`, `vue2-leaflet-geosearch ^1.0.6`, `leaflet-routing-machine ^3.2.12`, `vue2-leaflet-markercluster ^3.1.0`
- Tile source: not hardcoded in config files (likely set per-component or from backend config)

## Environment Configuration Summary

| Variable | Purpose |
|---|---|
| `VUE_APP_API_URL` | Main backend REST API |
| `VUE_APP_PUSH_API_URL` | Push notification microservice |
| `VUE_APP_SOCKET_HOST` | Socket.IO server host |
| `VUE_APP_SOCKET_PATH` | Socket.IO path |
| `VUE_APP_CSRF_NAME` | CSRF cookie name |
| `VUE_APP_AUTH_URL` | Auth service URL |
| `VUE_APP_PUSH_KEY` | Web Push VAPID public key |
| `VUE_APP_GIPHY_API_KEY` | Giphy GIF search API |
| `VUE_APP_YM_ID` | Yandex Metrika counter |
| `VUE_APP_SENTRY_DSN` | Sentry error tracking (inactive) |
| `VUE_APP_SENTRY_ENV` | Sentry environment tag |
| `VUE_APP_SENTRY_PROJECT` | Sentry project name |
| `VUE_APP_MAIN_COLOR` | Default primary theme color |
| `VUE_APP_CODE_NAME` | Brand skin identifier |
| `VUE_APP_URL` | App public URL |
| `VUE_APP_BUILD_TYPE` | `dev` or `production` (controls GTM) |
| `VUE_APP_BUILD_VERSION` | Injected at build time by `scripts/write-version.js` |

---

*Integration audit: 2026-04-17*
