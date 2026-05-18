# Architecture

> Vue 2 SPA with server-driven routing, Vuex state management, Socket.IO real-time layer, and a dynamically assembled module system resolved from API at startup.

**Analysis Date:** 2026-04-17

## Pattern Overview

**Overall:** Server-driven SPA — the backend (`/app_info/routes/`) dictates which menu items, pages, and permissions exist. The frontend resolves route components lazily from `src/views/Dashboard/PageWidgets/` based on the API response.

**Key Characteristics:**
- Routes are not statically declared; they are fetched from the API at boot and injected into Vue Router at runtime
- UI modules (apps) live outside `src/` as separate packages, referenced via the `@apps` webpack alias pointing to `src/modules/`
- Real-time events (chat, presence, calls) flow through Socket.IO; REST calls go through two separate Axios instances (`$http` and `$http2`)
- PWA-capable: service worker, IndexedDB caching, cross-tab BroadcastChannel sync (`chatSync`, `visibilityHub`, `tabSync`)
- Mobile/desktop layouts are selected at boot based on `window.matchMedia('(max-width: 768px)')` and never change mid-session

## Layers

**Bootstrap (`src/main.js`):**
- Purpose: App initialization sequence
- Executes: `getUserInfo` → `asyncInitLang` → `getCacheUID` → `configInit` → `navigation/routeInit` → `setupRouter` → `new Vue()`
- Registers all global plugins (Ant Design Vue components, Socket.IO, Tippy, GTM)
- Attaches `$http`, `$http2`, `$uploadFile`, `$moment`, `$message`, `$notification`, `$confirm` to `Vue.prototype`

**Layouts (`src/layouts/`):**
- Purpose: Shell wrappers rendered by the top-level `<router-view>`
- `Dashboard.vue` — desktop shell: sidebar + header + inner `<router-view>`
- `MobileDashboard.vue` — mobile shell: mobile header + footer nav + inner `<router-view>`
- `Authorization.vue` — unauthenticated shell for login/register/forgot flows
- `PageError.vue` — 404/error shell
- Layout is chosen at router setup time based on `store.state.isMobile`

**Views (`src/views/`):**
- Purpose: Static page-level components for known fixed routes
- `Authorization/` — login, forgot-password, registration, join-user
- `Dashboard/PageWidgets/` — one `.vue` per server-declared page (e.g. `Chat.vue`, `Tasks.vue`, `Calendar.vue`). Loaded lazily via `checkNewPageWidget()` in `src/utils/routerUtils.js`
- `Dashboard/` has ~37 page widget components; new pages from backend map to a new file here
- `Profile/`, `Menu/`, `Error/`, `OfficePreview/` — supplementary views

**App Modules (`src/modules/` aliased as `@apps`):**
- Purpose: Feature packages (chat, tasks, helpdesk, etc.) cloned from a separate GitLab group
- Each module exposes its own `config/router.js`, Vuex store, and components
- Currently `src/modules/` contains only a `README.md` (actual module packages are git-cloned separately)
- Referenced in navigation mutations: `@apps/Orders`, `@apps/InvestProject`, `@apps/HelpDesk`, `@apps/GOS24`, etc.

**Vuex Store (`src/store/`):**
- Purpose: Central state management
- Root modules: `user`, `navigation`, `config`, `table`, `filter`, `formInfo`, `comments`, `recentUsers`, `remoteAccess`
- Plugin: `recentUsersSyncPlugin` (cross-tab sync of recently viewed users)
- Root state tracks: `isMobile`, `online`, `visibilityState`, `windowWidth/Height`, `openDrawers`, `asideType`, `miniMenu`, `onlyofficePreview`

**Config (`src/config/`):**
- `router.js` — `setupRouter()` factory; builds route tree at runtime from `store.state.navigation.routerApp`
- `axios.js` — primary HTTP instance (`VUE_APP_API_URL`); handles 401 → logout, 503 → retry
- `axiosPush.js` — secondary HTTP instance for push/notification endpoint
- `socket.js` — Socket.IO client (`VUE_APP_SOCKET_HOST`); `autoConnect: false`
- `i18n-setup.js` — lazy language loading (ru / en / kk)
- `TokenService.js` — CSRF token handling (session-cookie auth, no JWT)

**Components (`src/components/`):**
- Purpose: Shared UI components used across multiple views
- Notable: `PageFilter/`, `TableWidgets/`, `UserSettings/`, `ModuleWrapper/`, `OnlyofficePreview/`, `VoiceMessagePlayer/`
- `initSwitch.vue` — renders injected feature components declared in `config.injectInit`

## Data Flow

**App Boot:**
1. `main.js` calls `store.dispatch('user/getUserInfo')` — authenticates via session cookie
2. If authenticated: fetches app config (`/app_info/global/`), then fetches routes (`/app_info/routes/?ver=alt`)
3. `navigation/SET_ROUTER_INIT` mutation assembles `routerApp` array — maps API route keys to lazy-loaded `PageWidgets/*.vue` components
4. `setupRouter()` injects `routerApp` as children of the root `/` route and mounts `new Vue()`

**Real-Time Events:**
- Socket connects via `VueSocketIOExt` (registered globally)
- `App.vue` handles `connect`, `chat_online_user`, `chat_offline_user` socket events
- `main.js` handles `online_list` socket event → `store.commit('user/SET_ONLINE_USERS')`
- App modules subscribe to their own socket events internally

**Cross-Tab Sync:**
- `chatSync` (`src/utils/chatSync.js`) — BroadcastChannel for menu counter sync across tabs
- `visibilityHub` (`src/utils/visibilityHub.js`) — detects if any tab is visible
- `tabSync` (`src/utils/tabSync.js`) — general cross-tab messaging

**State Management:**
- Vuex for global/shared state; local component `data()` for UI-only state
- IndexedDB (`src/indexedDb/`, `src/utils/cacheDb.js`) for offline/persistent caching of config, routes, tasks
- `localStorage` for user preferences: `asideType`, `miniMenu`, `cacheUID`, `documentReverse`

## Key Abstractions

**`checkNewPageWidget(route)`** (`src/utils/routerUtils.js:261`):
- Maps a server route object to a lazy `import()` of `src/views/Dashboard/PageWidgets/{route.pageWidget}.vue`
- Falls back to `NotPageWidget.vue` if the component file does not exist

**Drawer Query Params** (`src/utils/routerUtils.js:3`):
- Panel/drawer UI is opened by appending query params (e.g. `?task=123`, `?meeting=456`, `?my_profile=1`)
- ~30 recognized params defined in `drawerQueryParams` array
- `App.vue` watches `$route.query.my_profile` to lazy-load `UserSettings` drawer

**`initSwitch.vue`** (`src/components/initSwitch.vue`):
- Renders injected feature components listed in `config.injectInit` (server-controlled feature injection)

## Entry Points

**`src/main.js`:**
- Single entry point
- Calls `mainAppInit()` async IIFE
- Registers all global plugins before mounting

**`src/App.vue`:**
- Root Vue component
- Handles socket presence events, window resize, online/offline, visibility state
- Lazy-loads mobile/desktop stylesheets via `lazyLoadModeStyles()`
- Renders global overlays: `OnlyofficePreviewModal`, `NetworkStatus`, `vue-progress-bar`

## Error Handling

**Strategy:** Try/catch with console.log at action boundaries; HTTP errors thrown from Axios interceptors

**Patterns:**
- 401 → `store.dispatch('user/logout')` + `location.reload()`
- 503 → automatic retry (200ms delay, one attempt)
- 403/404/500/502 → `throw response` (caller handles)
- Route component load failure → falls back to `NotPageWidget.vue`
- Global `mainAppInit` wrapped in try/catch with `console.log(e, 'mainAppInit')`

## Cross-Cutting Concerns

**Logging:** `console.log` only; Sentry integration present but commented out
**Validation:** Form validation via Ant Design Vue `<a-form-model>` rules; no global validation layer
**Authentication:** Session cookie + CSRF token (`X-CSRFToken` header); `TokenService.js` manages CSRF; 401 triggers logout
**i18n:** `vue-i18n` with lazy locale loading; supported locales: `ru`, `en`, `kk`; locale stored in user profile on backend
**Analytics:** Google Tag Manager (`GTM-WR54QKMN`) — enabled in production only; Yandex Metrika head tag in production

---

*Architecture analysis: 2026-04-17*
