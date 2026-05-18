# Testing Patterns
> Testing infrastructure is configured but no test files exist — the project has zero actual tests.

**Analysis Date:** 2026-04-17

## Test Framework

**Runner:** Jest 29.5.0
- Config: `jest.config.js` (root)
- Preset: `@vue/cli-plugin-unit-jest`

**Component testing:**
- `@vue/test-utils` ^1.1.3 (Vue Test Utils v1 for Vue 2)
- `@testing-library/vue` ^5.9.0
- `@vue/vue2-jest` ^27.0.0-alpha.2 (transform `.vue` files)

**Transpilation:**
- `babel-jest` ^27.5.1
- Config: `babel.config.js` with `@vue/cli-plugin-babel/preset`

## Run Commands

```bash
npm run test:unit    # Run all unit tests (vue-cli-service test:unit)
```

No watch-mode or coverage commands are defined in `package.json` scripts.

## Test File Organization

**No test files found.** Search across entire `src/` for `*.test.*`, `*.spec.*`, and `__tests__/` directories returned zero results.

## Current State

The project has:
- Full Jest + Vue Test Utils installation
- `jest.config.js` configured with `@vue/cli-plugin-unit-jest` preset
- `test:unit` npm script wired up
- **Zero test files written**

There is no test coverage of any kind. No unit tests, no component tests, no integration tests.

## What Should Be Tested (High Priority Gaps)

Given the codebase, the following are highest-risk untested areas:

- **Vuex store modules** (`src/store/modules/`) — business logic in actions and mutations
- **Utility functions** (`src/utils/utils.js`, `src/utils/dateSettings.js`, etc.) — pure functions suitable for unit testing
- **Field components** (`src/components/Field/`) — form input behavior and validation
- **Auth/token flow** (`src/config/axios.js`, `src/config/TokenService.js`) — 401/403 retry logic
- **Router guards** (`src/config/router.js`) — navigation permission checks

## How to Add Tests

Place test files co-located or in a `__tests__/` subdirectory. Jest will pick up `*.spec.js` and `*.test.js` patterns per the `@vue/cli-plugin-unit-jest` preset defaults.

Example unit test for a utility:
```js
// src/utils/utils.spec.js
import { secondsFormat } from './utils'

describe('secondsFormat', () => {
    it('returns "0 секунд" for falsy input', () => {
        expect(secondsFormat(0)).toBe('0 секунд')
    })
})
```

Example component test using Vue Test Utils:
```js
// src/components/Field/DateField.spec.js
import { shallowMount } from '@vue/test-utils'
import DateField from './DateField.vue'

describe('DateField', () => {
    it('renders with default props', () => {
        const wrapper = shallowMount(DateField, {
            propsData: { wConfig: { disabled: false } }
        })
        expect(wrapper.exists()).toBe(true)
    })
})
```

---

*Testing analysis: 2026-04-17*
