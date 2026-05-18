# Codebase Structure

> Vue 2 SPA using a flat feature-widget model; app modules are external git packages resolved via the `@apps` alias.

**Analysis Date:** 2026-04-17

## Directory Layout

```
project-root/
├── src/                    # Application source
│   ├── main.js             # Entry point — boot sequence, plugin registration
│   ├── App.vue             # Root component — socket listeners, global overlays
│   ├── assets/             # Static CSS, images, fonts, SVG icons
│   ├── components/         # Shared UI components (reusable across views)
│   ├── config/             # App-level configuration (router, axios, socket, i18n)
│   ├── indexedDb/          # IndexedDB schema helpers (filter.js, routeConfig.js)
│   ├── lang/               # i18n locale files (ru.js, en.js, kk.js + per-module)
│   ├── layouts/            # Page shell components (Dashboard, MobileDashboard, Authorization)
│   ├── mixins/             # Global Vue mixins (launchQueue, pageMeta, appBadge)
│   ├── modules/            # App modules mount point (aliased as @apps — external packages)
│   ├── plugins/            # Vue plugin wrappers (versionWatch.js)
│   ├── store/              # Vuex store (modules: user, navigation, config, table, filter, etc.)
│   ├── utils/              # Utility functions (axios helpers, sound, tab sync, routing, upload)
│   └── views/              # Route-level page components
│       ├── Authorization/  # Login, registration, forgot-password pages
│       ├── Dashboard/
│       │   └── PageWidgets/# One .vue per server-declared page module
│       ├── Error/          # 404 and error pages
│       ├── Menu/           # Mobile menu tab view
│       ├── OfficePreview/  # Standalone OnlyOffice document viewer page
│       └── Profile/        # User profile view (mobile)
├── public/                 # Static assets served as-is (icons, sounds, manifests)
│   ├── img/                # Favicon and brand icon sets
│   ├── sound/              # Notification audio files
│   └── manifests/          # PWA manifest JSONs
├── docs/                   # Internal documentation (not shipped)
├── nginx/                  # Nginx config for Docker deployments
├── scripts/                # Deployment / utility shell scripts
├── vue.config.js           # Webpack/Vue CLI config (aliases, chunk splitting, PWA)
├── jsconfig.json           # Path alias: @/* → src/*
├── babel.config.js         # Babel config
├── jest.config.js          # Jest test config
├── tailwind.config.js      # Tailwind CSS config
├── postcss.config.js       # PostCSS config
└── Dockerfile              # Production Docker image definition
```

## Directory Purposes

**`src/config/`:**
- Purpose: Infrastructure configuration, not business logic
- Key files:
  - `router.js` — `setupRouter()` factory; assembles dynamic routes from Vuex state
  - `axios.js` — primary REST client (`VUE_APP_API_URL`); interceptors for 401/503
  - `axiosPush.js` — secondary REST client for push notification endpoint
  - `socket.js` — Socket.IO client singleton (`VUE_APP_SOCKET_HOST`)
  - `i18n-setup.js` — lazy locale loading (ru/en/kk)
  - `TokenService.js` — CSRF token management
  - `dynamicTheme.js` — runtime CSS variable injection for primary color theming
  - `registerServiceWorker.js` / `service-worker.js` — PWA service worker setup

**`src/store/`:**
- Purpose: All shared application state via Vuex
- Structure: root `state.js` / `mutations.js` / `actions.js` + named modules in `modules/`
- Modules: `user`, `navigation`, `config`, `table`, `filter`, `formInfo`, `comments`, `recentUsers`, `remoteAccess`
- Plugin: `plugins/recentUsersSyncPlugin.js` — cross-tab sync via BroadcastChannel
- Each module follows the pattern: `index.js`, `state.js`, `mutations.js`, `actions.js`, `getters.js`

**`src/views/Dashboard/PageWidgets/`:**
- Purpose: One component per server-configurable application page
- Naming: `PascalCase.vue` matching `route.pageWidget` value from `/app_info/routes/` API
- Examples: `Chat.vue`, `Tasks.vue`, `Calendar.vue`, `HelpDesk.vue`, `Documents.vue`
- New pages from the backend require a matching `.vue` file here; missing files fall back to `NotPageWidget.vue`
- Do NOT add routing logic here — routing is handled by `navigation/mutations.js` and `routerUtils.js`

**`src/layouts/`:**
- Purpose: Full-page shell templates wrapping `<router-view>`
- `Dashboard.vue` — desktop: sidebar + header + content
- `MobileDashboard.vue` — mobile: top/bottom nav + content
- `Authorization.vue` — unauthenticated shell
- `PageError.vue` — error/404 shell
- `components/` — sub-components used exclusively by layouts (Sidebar, Header, Mobile nav)
- `mixins/` — layout-specific mixins (theme application)

**`src/components/`:**
- Purpose: Shared UI components used by multiple views or modules
- Each complex component lives in its own named subdirectory with an `index.vue` or main component
- Key components:
  - `PageFilter/` — generic server-configurable filter panel
  - `TableWidgets/` — data table with widget extensions
  - `UserSettings/` — user profile drawer (opened via `?my_profile=1`)
  - `ModuleWrapper/` — wrapper for injecting dynamic module UI
  - `OnlyofficePreview/` — document preview modal
  - `VoiceMessagePlayer/` — audio message playback
  - `DrawerTemplate.vue` — base template for all drawer/panel overlays
  - `initSwitch.vue` — renders server-injected feature components from `config.injectInit`

**`src/utils/`:**
- Purpose: Stateless helper functions and singleton services
- Key files:
  - `routerUtils.js` — `checkNewPageWidget()`, `drawerQueryParams`, route helpers
  - `cacheDb.js` — IndexedDB CRUD wrappers
  - `chatSync.js` / `tabSync.js` / `visibilityHub.js` — BroadcastChannel cross-tab utilities
  - `soundMaster.js` / `sounds.js` — notification audio management
  - `titleBlinker.js` — browser tab title blinking for unread notifications
  - `upload.js` — file upload utility (attached as `Vue.prototype.$uploadFile`)
  - `eventBus.js` — global Vue event bus instance
  - `utils.js` — general helpers (device UUID, etc.)

**`src/lang/`:**
- Purpose: i18n translation files
- Root: `ru.js`, `en.js`, `kk.js` — base translations
- `mobules/` (sic) — per-feature translation chunks loaded lazily (auth, emoji, table, profiler, upload, reports, remote)

**`src/modules/`** (aliased as `@apps`):
- Purpose: Mount point for external app module packages
- Currently contains only `README.md` — actual modules are cloned from GitLab group `bkz/frontend/appcomponents`
- Referenced modules: `Orders`, `InvestProject`, `SportsFacilities`, `Moderation`, `HelpDesk`, `Directories`, `WorkPlan`, `GOS24`, `Support`, `vue2ChatComponent`, `Profiler`, `UIModules`
- Each module is expected to export: `config/router.js`, Vuex store module, and Vue components

**`src/indexedDb/`:**
- Purpose: IndexedDB database schema configuration
- `filter.js` — filter state DB schema
- `routeConfig.js` — route/config cache DB schema

**`src/mixins/`:**
- Purpose: Global Vue mixins applied at layout or App level
- `launchQueue.js` — PWA launch queue handler
- `pageMeta.js` — document title / meta management
- `appBadge.js` — PWA app badge (unread count)
- `selectMixins.js` — shared select/dropdown behavior

## Naming Conventions

**Files:**
- Vue components: `PascalCase.vue` (e.g. `UserSettings.vue`, `Dashboard.vue`)
- Utility/config JS: `camelCase.js` (e.g. `routerUtils.js`, `chatSync.js`)
- Store files: descriptive lowercase (`state.js`, `mutations.js`, `actions.js`, `getters.js`, `index.js`)
- i18n modules directory spelled `mobules/` (not `modules/`) — this is intentional existing convention

**Directories:**
- Feature components: `PascalCase/` with an `index.vue` or main named component inside
- Store modules: `camelCase/` (e.g. `navigation/`, `formInfo/`, `recentUsers/`)
- View groups: `PascalCase/` (e.g. `Authorization/`, `Dashboard/`, `OfficePreview/`)

## Where to Add New Code

**New server-declared page (new menu item from backend):**
- Create `src/views/Dashboard/PageWidgets/{PageWidgetName}.vue`
- The `pageWidget` value from `/app_info/routes/` API must match the filename exactly

**New shared UI component:**
- Create `src/components/{ComponentName}/index.vue` (or `{ComponentName}.vue` if simple)
- Import in consuming views or layouts directly

**New Vuex store module:**
- Create `src/store/modules/{moduleName}/` with `index.js`, `state.js`, `mutations.js`, `actions.js`, `getters.js`
- Register in `src/store/modules.js`

**New global utility / service:**
- Add to `src/utils/{utilName}.js`
- If it needs to be on Vue.prototype, register in `src/main.js`

**New layout sub-component:**
- Add to `src/layouts/components/`

**New i18n translations:**
- Add keys to `src/lang/ru.js`, `src/lang/en.js`, `src/lang/kk.js`
- For module-specific translations: add file in `src/lang/mobules/{featureName}/`

**New external app module:**
- Clone into `src/modules/{ModuleName}/` following the `@apps` alias convention
- Register router in `src/store/modules/navigation/mutations.js` `appsRoutes` array
- Module must expose `config/router.js`

## Path Aliases

| Alias | Resolves to |
|-------|-------------|
| `@/` | `src/` |
| `@apps/` | `src/modules/` |
| `lodash$` | `lodash-es` (tree-shakeable) |
| `AutoNumeric` | `node_modules/autonumeric/dist/autoNumeric.min` |

## Special Directories

**`.planning/`:**
- Purpose: AI planning documents (codebase maps, phase plans)
- Generated: By AI tooling
- Committed: Yes

**`public/`:**
- Purpose: Assets copied verbatim to `dist/` root
- Not processed by webpack
- `sound/` — notification audio; `img/` — favicon/icon sets; `manifests/` — PWA manifests

**`.nuxt/` / `dist/`:**
- Purpose: Build output (not present — this is webpack/Vue CLI, not Nuxt despite `.nuxt` mention)
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-04-17*
