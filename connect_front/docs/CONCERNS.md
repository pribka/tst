# Concerns

> Vue 2 (EOL) frontend with several active security risks and zero test coverage; overall health is moderate but bounded by framework obsolescence.

## Critical

### `eval()` in table formula evaluation
- **Issue:** Server-supplied formula strings are executed via `eval()` in two places
- **Files:** `src/store/modules/table/actions.js` lines 159, 178
- **Impact:** Remote code execution if formula data is ever attacker-controlled or if backend is compromised; also blocks CSP headers
- **Fix:** Replace with a safe math expression parser (e.g., `mathjs`, `expr-eval`)

### `v-html` on unescaped server data
- **Issue:** Raw HTML from API is rendered directly into the DOM without sanitization
- **Files:** `src/components/TableWidgets/Widgets/ClientSpecialistsCommentRow.vue` line 6, `src/components/TableWidgets/Widgets/DescriptionRow.vue` line 4
- **Impact:** Stored XSS if any user-controlled content reaches these fields
- **Fix:** Sanitize with DOMPurify before binding, or replace with a text renderer

### Vue 2 reached end-of-life (Dec 2023)
- **Issue:** `"vue": "^2.6.14"` and `@vue/cli-service ~4.5.13` — no further security patches from upstream
- **Files:** `package.json`
- **Impact:** Any future CVEs in Vue 2 core or vue-cli will not be fixed
- **Fix:** Plan migration to Vue 3; this is a multi-quarter effort given the scope

## High Priority

### Zero test coverage
- **Issue:** No `.spec.js` or `.test.js` files exist anywhere in the project; `test:unit` script is configured but unused
- **Files:** `package.json` (`test:unit` script), no test files found
- **Impact:** Regressions go undetected; large components like `UniversalTable.vue` (1270 lines) have no safety net
- **Fix:** Start with critical store actions and utility functions; set a coverage threshold

### Swallowed exceptions in utilities
- **Issue:** 14+ files use empty `catch (e) {}` blocks, silently discarding errors
- **Files:** `src/config/i18n-setup.js`, `src/utils/visibilityManager.js`, `src/utils/notySyncChannel.js`, `src/plugins/versionWatch.js`, `src/config/registerServiceWorker.js`, `src/config/service-worker.js`, and others
- **Impact:** Failures in BroadcastChannel, IndexedDB, and service worker logic are invisible in production
- **Fix:** At minimum log to Sentry (already integrated); remove blanket suppression

### Hardcoded production URLs in source
- **Issue:** Specific customer hostnames and download links committed to source
- **Files:**
  - `src/components/RemoteAccess.vue` line 126: `https://connect.gos24.kz/media/desktop/connect_gos24_desktop.exe`
  - `src/layouts/components/Header/UserNav.vue` line 214: `https://bpms.gos24.kz/ru`
- **Impact:** Multi-tenant deployments require code changes; URLs cannot be reconfigured without a rebuild
- **Fix:** Move to env vars (`VUE_APP_*`) or server-provided configuration

### 137 `console.log` calls across 78 files
- **Issue:** Debug logging left in production code throughout the codebase
- **Impact:** Sensitive data (user objects, tokens, error details) may leak in browser console
- **Fix:** Remove or gate behind `process.env.NODE_ENV !== 'production'`; configure ESLint `no-console` rule

### `axios` pinned at `^0.21.4` (obsolete major version)
- **Issue:** Axios 0.x is significantly behind current 1.x; known issues and breaking behavior differ
- **Files:** `package.json`
- **Impact:** Missing security fixes and modern interceptor behaviors available in 1.x
- **Fix:** Upgrade to `axios ^1.x`; review interceptors in `src/config/axios.js`, `src/config/axiosClear.js`, `src/config/axiosPush.js`

### Node version mismatch
- **Issue:** `.nvmrc` specifies Node 16.20.2 but runtime is Node 18.18.2; Node 16 is EOL
- **Files:** `.nvmrc`
- **Impact:** CI/CD may behave differently from development; `dev4gb` script targets 4GB limit suggesting build memory pressure
- **Fix:** Update `.nvmrc` to Node 18 LTS or 20 LTS

## Low Priority / Tech Debt

### Massively oversized components
- **Issue:** Several components exceed maintainable size limits
- **Files:**
  - `src/components/TableWidgets/UniversalTable.vue` — 1270 lines
  - `src/components/PageFilter/Desktop.vue` — 802 lines
  - `src/components/DrawerTemplate.vue` — 787 lines
  - `src/views/Profile/Page.vue` — 776 lines
- **Fix:** Extract sub-components and composables incrementally

### Typo in directory name `lang/mobules/`
- **Issue:** `src/lang/mobules/` should be `modules/`; propagated across all i18n imports
- **Files:** `src/lang/mobules/` (entire directory), `src/lang/ru.js`, `src/lang/kk.js`
- **Impact:** Cosmetic but causes confusion; hard to rename without touching many imports

### Trial/watermarked Gantt library
- **Issue:** `@dhx/trial-gantt ^9.0.4` is a trial build with restrictions
- **Files:** `package.json`
- **Impact:** May display trial watermark in production; licensing risk
- **Fix:** Evaluate purchasing DHTMLX license or migrating to an open-source alternative

### Pinned legacy packages
- **Issue:** `swiper` is pinned to `5.2.0` (current major is 11) and `lightgallery.js` to `1.1.3` (deprecated in favor of `lightgallery`)
- **Files:** `package.json`
- **Impact:** No security updates; `vue-awesome-swiper@4` depends on old Swiper 5 API
- **Fix:** Upgrade Swiper to v11 with `swiper/vue` and replace `lightgallery.js` with `lightgallery`

### `main.js` is a 402-line global registration monolith
- **Issue:** All plugins, directives, global components, and app config are registered in a single file
- **Files:** `src/main.js` (62 imports)
- **Fix:** Split into feature-specific plugin files; use Vue's `app.use()` pattern per module

### App modules loaded from external Git group
- **Issue:** `src/modules/` only contains a README pointing to `https://gitlab.buhni.kz/bkz/frontend/appcomponents`; actual modules are not in this repo
- **Files:** `src/modules/README.md`
- **Impact:** New developers cannot build without access to separate private repositories; onboarding is broken without documentation
- **Fix:** Add git submodules or document the setup steps in a proper README

### TODO comments not tracked
- **Issue:** Unfollowed TODOs exist in store and utility code
- **Files:**
  - `src/store/modules/table/actions.js` line 248
  - `src/utils/routerUtils.js` line 55
- **Fix:** Convert to tracked issues; add ESLint rule to flag new TODOs

---

*Concerns audit: 2026-04-17*
