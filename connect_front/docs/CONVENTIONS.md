# Coding Conventions
> Vue 2 Options API frontend with consistent 4-space indent, ESLint enforced, no Prettier.

**Analysis Date:** 2026-04-17

## Linting & Formatting

- **ESLint** via `.eslintrc.js` — `plugin:vue/essential` + custom rules
- **No Prettier** — no `.prettierrc` present
- 4-space indentation enforced (`indent: ['error', 4]`) — applies to JS; Vue template/script indent rules are **off**
- `eqeqeq: ['error', 'smart']` — strict equality enforced
- `no-console: 'off'` — `console.log` is permitted in development
- `no-debugger: 'error'` in production builds only
- Parser: `babel-eslint`, `ecmaVersion: 2020`

## File Naming

- **Vue components**: PascalCase for multi-word files (`DrawerTemplate.vue`, `NetworkStatus.vue`, `DateField.vue`)
- **Component directories**: PascalCase folder + `index.vue` entry (`ListView/index.vue`, `ModuleWrapper/index.vue`)
- **JS utilities/config**: camelCase (`eventBus.js`, `socketUtils.js`, `dateSettings.js`)
- **Store files**: flat names per role (`actions.js`, `mutations.js`, `state.js`, `getters.js`, `index.js`)
- **Old/deprecated files**: prefixed with `old_` (`old_DateTimeField.vue`)

## Naming Patterns

- **Vuex mutations**: SCREAMING_SNAKE_CASE (`SET_USER`, `CHANGE_USER_ORG`, `SET_ONLINE_USER`)
- **Vuex actions**: camelCase (`skipPassword`, `logout`)
- **Component props**: camelCase (`wConfig`, `maskFormat`, `enterHandler`)
- **Variables and functions**: camelCase (`getSiteName`, `generateDeviceUUID`, `secondsFormat`)
- **CSS classes**: mix of Tailwind utilities (`flex`, `items-center`) and BEM-style custom classes (`date_input_wrapper`, `select_btn`)

## Component Structure (Options API)

Standard Vue 2 Options API order observed throughout:
1. `mixins`
2. `components`
3. `props`
4. `data`
5. `computed` (including `mapState`)
6. `methods`
7. `sockets` (vue-socket.io events)
8. `metaInfo` (vue-meta)

Example from `src/App.vue` and `src/components/Field/DateField.vue`.

## Props Definition

- Props use object form with `type` and `default`:
  ```js
  wConfig: { type: Object, default: () => null },
  currentDate: { type: Boolean, default: false }
  ```
- Functions as defaults use arrow function: `default: () => {}`
- Object/array defaults always use factory function

## Import Organization

No enforced import order. Observed pattern in files:
1. Third-party libs (`vue`, `axios`, `moment`, `lodash`)
2. Store/config (`@/config/axios`, `@/store`)
3. Utilities (`@/utils/...`)
4. Components (`@/components/...`)

**Path alias:** `@/` maps to `src/` (configured in `jsconfig.json` and `vue.config.js`)

## Async Components (Lazy Loading)

Lazy-loaded via arrow function factory:
```js
components: {
    initSwitch: () => import('@/components/initSwitch'),
    OnlyofficePreviewModal: () => import('@/components/OnlyofficePreview/Modal.vue')
}
```

## State Management (Vuex)

- Namespaced modules under `src/store/modules/`
- Each module: `index.js`, `actions.js`, `mutations.js`, `state.js`, `getters.js`
- Actions use `Promise` + `axios` pattern with `.then`/`.catch`:
  ```js
  return new Promise((resolve, reject) => {
      axios.post('/endpoint/').then(({data}) => {
          commit('MUTATION_NAME')
          resolve(data)
      }).catch(error => reject(error))
  })
  ```
- `mapState` via object shorthand in computed properties

## Mixins

Located in `src/mixins/`. Used for cross-cutting concerns:
- `src/mixins/launchQueue.js` — PWA launch queue
- `src/mixins/selectMixins.js` — dropdown positioning via Popper.js
- `src/mixins/appBadge.js` — PWA badge API
- `src/mixins/pageMeta.js` — meta tag handling

## Comments

- Commented-out code blocks are common — dead code left in with `//` or `/* */`
- `console.log` with styled output used for debugging (`%c Socket connected`, `color: #...`)
- No JSDoc observed

## Tailwind CSS

Tailwind utility classes used directly in templates alongside custom LESS/SCSS classes. Config in `tailwind.config.js`.

---

*Convention analysis: 2026-04-17*
