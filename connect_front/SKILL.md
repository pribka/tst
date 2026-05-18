# Project Skill

## Repository structure

- The project is split across multiple Git repositories.
- The main application root is one Git repository.
- The `/src/modules` directory contains modules where each module is its own separate Git repository.
- Before making changes inside `/src/modules`, account for the fact that the target module may belong to a different repository than the main project root.

## Node.js version

- The project works only with the Node.js version specified in `/.nvmrc`.
- Before running project commands or installing dependencies, use the Node.js version from `/.nvmrc`.
- Any new package installation must also be done under that same Node.js version.

## Linting

- The project uses ESLint.
- Follow the rules defined in `/.eslintrc.js`.
- New code and changed code should comply with the existing ESLint configuration.

## UI and styling

- Prefer `tailwindcss` for styling to minimize custom CSS.
- Avoid writing separate CSS rules when the same result can be achieved with Tailwind utility classes.

## Infinite loading

- For infinite scroll and infinite loading behavior, use `vue-infinite-loading`.

## Lazy-loaded components

- In `components`, load components lazily wherever practical via `() => import(...)`.
- Prefer lazy loading especially for non-critical UI blocks, drawers, selects, and profile-related views.

## Shared project components

- Common UI elements such as buttons and other reusable interface pieces are often located in `/src/modules/UIModules`.
- Before creating a new shared UI component, check `/src/modules/UIModules` for an existing implementation.
- The shared notifications module is `/src/modules/Notifications`.
- The shared file selection and attachment module is `/src/modules/vue2Files`.
- When a form or feature needs file picking or file attachment, prefer reusing `/src/modules/vue2Files`.
- The main rich text editor in the project is `/src/modules/CKEditor/index.vue`.
- If a toolbar-less editor variant is needed, use `/src/modules/CKEditor/BalloonEditor.vue`.
- For configurable drawer-based selects, prefer `/src/modules/DrawerSelect/Select.vue`.
- `/src/modules/DrawerSelect/Select.vue` is a universal select component that can accept a request, value/output keys, paginated or non-paginated data, single or multiple selection, and similar configuration.
- For rendering a profile, use `/src/modules/Profiler/Profiler.vue`.
- For organization selection, use `/src/modules/DrawerSelect/OrgSelect.vue`.
- For project selection, use `/src/modules/DrawerSelect/ProjectSelect.vue`.
- For status selection, use `/src/modules/DrawerSelect/StatusSelect.vue`.
- For team selection, use `/src/modules/DrawerSelect/GroupSelect.vue`.
- For user selection, use `/src/modules/DrawerSelect/index.vue`.
- `/src/modules/DrawerSelect/UserMiniSelect.vue` is a smaller user select with limited functionality and is used less often.
- For ticket selection, use `/src/modules/DrawerSelect/TicketSelect.vue`.

## Buttons and icons

- Use `a-button` from Vue Ant Design in its project-customized form.
- In addition to standard button types like `primary` and `default`, use the project-specific button types where appropriate: `green`, `ui`, `ui_ghost`, `flat`, `flat_primary`, `flat_danger`, `orange_flat`.
- `a-button` supports custom icons through the `icon` prop.
- For these icons, use classes from `/src/assets/css/uicons-regular-rounded.css`.
- Pass icon names like `fi-rr-funnel-dollar` into the `icon` prop and also pass the `flaticon` prop so the icon renders correctly.
- Prefer these project icons over the default Vue Ant Design icon set.
- In general, do not use Vue Ant Design icons unless there is a clear reason the project icon set cannot cover the case.

## Date pickers

- For date pickers, place the calendar icon on the left via `iconPosition="left"`.
- For `a-range-picker`, always pass `:mask="{ mask: '00.00.0000', lazy: true, autofix: true }"`.
- The `:mask` prop for `a-range-picker` is mandatory and should be considered a default requirement whenever the component is used.

## Animations

- For animations, always follow the same browser-dependent pattern used in `/src/modules/WorkPlan/Drawer/widgets/DayPulse/index.vue`.
- For all browsers except Safari, use `.webm` animation files from `/src/assets/animate`.
- For Safari, use `.mov` animation files from `/public/animate`.
- Before using any animation, check `this.$store.state.isSafari`.
- `isSafari` is already available in `/src/store/state.js`, so reuse that flag and do not invent a separate browser check in components.
- Use the same loading approach as in `DayPulse`: if `isSafari` is true, assign the animation from `${process.env.BASE_URL}animate/<file>.mov`; otherwise load the `.webm` file via `await import('@/assets/animate/<file>.webm')`.
- Store the resolved animation path in component state and render it in `<video>` through `:src`.
- When adding a new animation, keep Safari and non-Safari sources paired and named consistently.

## Responsive state

- To determine whether the app is in mobile mode, use `this.$store.state.isMobile`.
- `isMobile` is defined in `/src/store/state.js`, so reuse that state key instead of adding custom viewport checks in components.

## Current user

- Information about the current user should be taken from the store key `user`.
- Reuse the user state from `/src/store/modules/user/state.js`.
- Do not introduce duplicate sources for current user data when the store already provides it.

## i18n

- The project supports i18n translations.
- Common and shared translations are located in `/src/lang`.
- Modules inside `/src/modules` usually have their own `lang` folders with module-specific translations.
- When adding translations for a module, prefer placing them in that module's own `lang` folder if the text is module-specific.
- Module translation keys should generally use their own prefixes to avoid collisions and duplicate keys across the project.

## Layouts

- The desktop layout is `/src/layouts/Dashboard.vue`.
- The mobile layout is `/src/layouts/MobileDashboard.vue`.
- When working with layout-level behavior, choose the correct file depending on whether the change belongs to desktop or mobile UI.
- In the mobile version, the footer contains links only to a limited set of modules.
- The shared page for all module links that are not pinned in the mobile footer is `/src/views/Menu/Page.vue`.
- The mobile profile page is `/src/views/Profile/Page.vue`.

## Page-level module entry points

- If a module is rendered as a page, its connection point usually goes through `/src/views/Dashboard`.
- When looking for where a page-level module is mounted or connected, check `/src/views/Dashboard` first.

## Tables

- The main universal table component is `/src/components/TableWidgets/UniversalTable.vue`.
- When implementing table output, prefer reusing `/src/components/TableWidgets/UniversalTable.vue` instead of creating a new table component from scratch.
- Many modules use the shared page filter component `/src/components/PageFilter/index.vue`.
- The shared page filter is connected with the table through `eventBus`, so when the filter changes it updates the related table.
- When implementing a standard filterable table page, prefer reusing `/src/components/PageFilter/index.vue` together with `/src/components/TableWidgets/UniversalTable.vue`.
- Table settings are exposed through `/src/components/TableWidgets/SettingsButton.vue`.
- `/src/components/TableWidgets/SettingsButton.vue` is inserted manually where needed and opens the table settings modal for tasks like hiding columns or changing their order.

## Drawers

- `a-drawer` is used through the project's wrapper component.
- The shared drawer component is `/src/components/DrawerTemplate.vue`.
- When implementing drawers, prefer `/src/components/DrawerTemplate.vue` instead of using raw `a-drawer` directly.
- For mobile versions of menus and action lists, use `/src/components/ActivitySelect/ActivityDrawer.vue` where it fits better than `a-dropdown` or similar desktop-oriented overlays.
- For the current user settings drawer, use `/src/components/UserSettings/index.vue`.
