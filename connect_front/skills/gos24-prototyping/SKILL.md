---
name: gos24-prototyping
description: Use this skill whenever the user wants to design, prototype, mock up, or visualize a NEW page, screen, view, widget, drawer, modal, or feature for the Gos24.Connect / delocloud-front project (the bkz.centersoft.kz / d.centersoft.kz / connect.centersoft.kz frontends). Trigger on any of "сделай прототип", "набросай страницу", "покажи как будет выглядеть", "макет", "wireframe", "prototype", "mockup", "набросай UI", or whenever the user describes a screen they want to see before it is built. The skill produces a single self-contained HTML file that visually matches the project's Vue 2 + Ant Design Vue + Tailwind UI system (Open Sans, primary `#4777FF`, 8px radius, custom button types, flaticon icons, 250px sidebar layout). Do NOT use this skill to write production Vue code — it is strictly for visual prototypes that the user reviews before real implementation.
---

# Gos24.Connect — UI prototyping skill

This project is a Vue 2.6 SPA built on **ant-design-vue 1.7** + **TailwindCSS** (postcss7-compat, JIT) + **Less/Sass**. The brand for this skill is the **BKZ tenant** (`https://bkz.centersoft.kz/`) — primary `#4777FF`. The same UI system is shared across the connect/dcstand/bkz tenants (only `--blue` / `--primaryColor` differ).

When the user asks for a prototype of a new page, screen or widget, produce **one self-contained HTML file** under the user's outputs / workspace folder that visually mimics this UI. Always:

1. Start by reading `tokens.css` and `template.html` from this skill folder — they define the design tokens and the page chrome (sidebar + top bar) every prototype needs.
2. Embed `tokens.css` inline in a `<style>` block (do not link to it — the file must be self-contained so it opens in any browser).
3. Reuse the recipes in `components.html` (buttons, cards, tabs, tables, drawers, modals, filter-chips, statuses, forms, empty states) instead of inventing new visual styles.
4. Use **flaticon classes** (`fi-rr-*`) for icons via the CDN already linked in `template.html`. Do NOT use Ant Design's anticons or Material Icons.
5. Localize the prototype to **Russian** by default — that's the language of the product. Switch to KZ/EN only if the user explicitly asks.

## Hard rules — never break these

- **Primary color is `#4777FF`** (the BKZ brand). Never use the blue `#1d65c0` from `var.less` unless the user says "стандарт / connect / dcstand tenant".
- **Body font is Open Sans, base size `0.835rem` (~13.36px), color `#2D2D2D`, page background `#f7f9fc`**. Do not switch to Inter, Roboto, system-ui, or any other font.
- **Active tab indicator is orange `#FF9A01`** (2px underline) — not blue. This is a deliberate accent in the system; honor it.
- **Card / button / input radius is 8px** (`--borderRadius`). Modals use 16px. Dropdowns/popovers use 12px. Pills/chips inside the active filter-row use full pill radius. **Don't use 4px or 12px on buttons.**
- **Buttons are 36px tall** (sm = 28px). Padding `0 15px`. Text 14px. Always render via the `.btn` + variant classes in `tokens.css`.
- **Sidebar is 250px wide, dark `#3E3E4F`, white text on dark, with the active item highlighted in primary blue tint**. Header is 50px tall, light bg `#f7f9fc`. The logo block at the top of the sidebar is white with the Gos24.kz logo.
- **Tables use header bg `#f5f7f7`, 13px font**. Zebra striping is off by default; rows separated by `1px solid #e1e7ec`. Row hover is `#f7f9fc`.
- **Page title is `<h1 class="page_title">` — 18px, weight 400, dark**. Module headers usually have title on the left and action buttons on the right of the same row, with optional inline search input next to the title.
- **Filter chips** (Список, Канбан, Делаю …) — pill buttons, active is filled primary `#4777FF` white, idle is `transparent` dark text. They sit in a row right below the page header.
- **Use Russian copy by default**. Common labels: "Добавить", "Сохранить", "Отмена", "Удалить", "Создать", "Поиск", "Фильтр", "Загрузить ещё", "Нет данных", "Закрыть".
- Do not invent colors outside the tokens. If you need a new accent, pick from the `--c*` scale (`--cBlue #4777FF`, `--cGreen #368225`, `--cOrange #FF9A01`, `--cRed #FF5C5C`, `--cYellow #FADB14`, `--cPurple #722ED1`, `--cMagenta #EB2F96`, `--cCyan #13C2C2`, `--cVolcano #FA541C`, `--cLime #A0D911`, `--cGold #FAAD14`, `--cBrown #521F3B`, `--cGrey #888`).

## Workflow when prompted "сделай прототип …"

1. Read the user's description and clarify only if a major piece is missing (intended user, key actions, list vs. board vs. form). For small additions to existing screens, don't pause to ask.
2. Pick a layout pattern from the list below.
3. Open `template.html` from this skill folder, copy it as the starting point, and fill in the `<main>` content area only. Keep the sidebar + top bar untouched unless the prototype is for the sidebar/topbar themselves.
4. Save the result to `/Volumes/SamsungSSD/app/delocloud-front/<descriptive-name>.prototype.html` so it lives in the project workspace and the user can `open` it.
5. End the response with one short line and a `computer://` link to the file. Don't summarize what you built — the user can see it.

## Layout patterns

### A. Filterable list page (most common — `/tasks`, `/projects`, `/deals`, `/helpdesk/tickets` …)

```
┌ page_header ──────────────────────────────────────────────────────────┐
│  H1 + inline search ………………………………………… [primary action] [⋮] [📊] [⚙] │
├───────────────────────────────────────────────────────────────────────┤
│  [Filter chip 1] [Filter chip 2] [Filter chip 3] [+ filter]           │
├───────────────────────────────────────────────────────────────────────┤
│  ┌── universal table ──────────────────────────────────────────────┐  │
│  │ # | Название | Проект | Ответственный | Дата | Статус          │  │
│  │ ───────────────────────────────────────────────────────────────  │  │
│  │ rows …                                                          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                  [pagination]         │
└───────────────────────────────────────────────────────────────────────┘
```

Use `.page_filter` + `.universal_table` classes from `components.html`. Empty state: a centered "Нет данных" with a small flaticon glyph above.

### B. Dashboard with widget grid (`/dashboard`)

3-column grid of cards. Each widget = `.widget_card` with a header row (title + ⋮ menu), body, optional footer. Use Tailwind grid (`grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4`) inside `<main>`. The first widget often spans 2 columns when it's a hero/welcome card.

### C. Detail drawer (right side, 720px on desktop)

The detail view of a task / project / deal opens as a right drawer. Use `.drawer` markup from `components.html`. Drawer header: title + close. Drawer footer is sticky, white, with primary action on the right.

### D. Modal form (small/medium)

Modal width 480 / 640 / 800px. Header with title (no border below), body padded `10px 20px`, footer sticky white with action buttons. Border radius 16px. See `.modal` in `components.html`.

### E. Auth screens (login, no-access)

Centered single-column card on `--mBg` background, panel max-width ~440px, white bg, 16px radius, generous padding. Logo on top. Submit button is full-width primary.

### F. Mobile layout

Reuse the same tokens but switch to a single-column scroll. Bottom tab bar instead of side menu (5 tabs). Cards become full-width with rounded corners. See `template.html` `?mobile=1` mode.

## Buttons — always use these variants, no others

| Variant       | When to use                                                      |
|---------------|------------------------------------------------------------------|
| `primary`     | The single most important action on the page (`Сохранить`, `Создать`) |
| `default`     | Secondary action; outlined                                        |
| `flat`        | Toolbar / row action with no destructive intent                   |
| `flat_primary`| Tinted primary action — e.g. "Открыть" in a list card             |
| `flat_danger` | "Удалить" / "Отклонить" inside a flat toolbar                     |
| `orange_flat` | Pending / warning action — e.g. "Назначить", "Отправить на согласование" |
| `green`       | Approved / success action                                         |
| `success`     | Solid green confirm button                                        |
| `ui`          | Round 36×36 icon-only button (settings, more, share)              |
| `ui_ghost`    | Same shape, transparent until hover — used in dense toolbars      |
| `link`        | Inline text-style button (no border/bg)                           |

Icon-only buttons MUST be 36×36 and use `border-radius: 50%`. Pass an icon by class name, e.g. `<button class="btn ui icon"><i class="fi fi-rr-settings"></i></button>`.

## Icons — flaticon `fi-rr-*` set

The project uses **Flaticon UIcons (regular rounded)**. Common choices: `fi-rr-search`, `fi-rr-plus`, `fi-rr-pencil`, `fi-rr-trash`, `fi-rr-settings`, `fi-rr-filter`, `fi-rr-cross`, `fi-rr-cross-small`, `fi-rr-angle-down`, `fi-rr-angle-right`, `fi-rr-arrow-right`, `fi-rr-bell`, `fi-rr-user`, `fi-rr-users`, `fi-rr-folder`, `fi-rr-document`, `fi-rr-calendar`, `fi-rr-clock`, `fi-rr-check`, `fi-rr-info`, `fi-rr-comment`, `fi-rr-paperclip`, `fi-rr-share`, `fi-rr-eye`, `fi-rr-eye-crossed`, `fi-rr-file`, `fi-rr-grid`, `fi-rr-list`, `fi-rr-menu-burger`, `fi-rr-sign-out-alt`, `fi-rr-bookmark`, `fi-rr-flag`. The CDN link is already in `template.html`.

If a glyph really doesn't exist in the rounded set, fall back to inline SVG — don't pull in another icon library.

## Status colors and label tones

Use the "functional" tones that already exist in `var.less`:

- success label  → bg `#E6EFE3`, text `#368225`, border `#A8C985`
- primary label  → bg `#E8EDFA`, text `#4777FF`
- danger label   → bg `#FFEDED`, text `#FF5C5C`
- warning label  → bg `#FEF8EB`, text `#FF9A01`
- neutral label  → bg `#F0F1F6`, text `#888888`

Render them as `<span class="label success|primary|danger|warning|neutral">…</span>` from `tokens.css`.

## Forms

- Field label above input, label color `#2D2D2D`, weight 400, font-size 13px, line-height 26px (matches Ant `.ant-form-item-label`).
- Input height 32px (Ant default `lg` would be 38px, but the project mostly uses default size). Border `1px solid #e1e7ec`, radius 8px, focus border primary, focus shadow `0 0 0 2px rgba(71,119,255,0.15)`.
- Required field marker is a red `*` AFTER the label text (project overrides Ant's default before-position).
- Date picker: calendar icon on the LEFT (`iconPosition="left"`), placeholder format `ДД.ММ.ГГГГ`.
- Selects open as drawers on mobile — for prototype, just use a normal styled select.
- Group related fields in a `.form_section` block; sections are separated by 16px gap, no horizontal divider.

## Tables (UniversalTable look)

- Header row: bg `#f5f7f7`, 13px, weight 600, color `#2D2D2D`, padding `8px 12px`.
- Body row: padding `10px 12px`, border-bottom `1px solid #e1e7ec`, font 13px.
- Hover row: bg `#f7f9fc`.
- Selected row: bg `rgba(29,101,192,0.2)` (this carries the legacy AG-grid token for selected ranges).
- Cells with status use the label tones above.
- The settings cog ⚙ in the top-right of the page (next to the primary action) opens column settings — show it but don't make it functional in prototypes.

## Drawers (DrawerTemplate look)

- Slides in from the right.
- Width 720px on desktop, 100% on mobile.
- Header: title left (truncated), action group right (share, more, close), bg white, padding `12px 20px`, border-bottom `1px solid #e8e8e8`.
- Body: padding `15px 20px`, scrolls.
- Footer: sticky, white bg, padding `10px 20px`, border-top `1px solid #e8e8e8`, primary action on the LEFT (project convention — Ant defaults to right but this codebase aligns left).

## i18n note for prototypes

Even though the running app uses `vue-i18n`, the prototype is HTML — just hard-code Russian strings. If the user mentions multi-language, add an inline language switcher (RU/KZ/EN) in the top bar that visually toggles between three pre-rendered string sets via CSS classes — no JS needed unless asked.

## Files in this skill

- `SKILL.md` — this file.
- `tokens.css` — paste this inline into every prototype.
- `template.html` — boilerplate page chrome (sidebar + top bar + main slot). Copy and fill `<main>`.
- `components.html` — copy-paste recipes for buttons, tabs, filter chips, tables, cards, drawers, modals, forms, statuses, empty states.
- `icons.md` — curated icon list for common UI roles.
- `examples/` — full prototype examples to mimic (`tasks-list.html`, `task-drawer.html`, `dashboard.html`).

## Anti-patterns — do not do these in a prototype

- Don't import Bootstrap, Material UI, or any other component library.
- Don't use shadows heavier than `0 8px 16px rgba(0,0,0,0.08)` — the system is mostly flat.
- Don't use rounded-full on buttons (only icon buttons and chips).
- Don't put the primary action on the RIGHT of a drawer footer — it goes on the left.
- Don't write CSS that the user will obviously want to delete because it doesn't match Tailwind utilities. If a Tailwind class works, use the Tailwind class.
- Don't add fake content that hints at production data (real names, real org-IDs). Use generic placeholders ("Иван Петров", "ООО Пример", "Проект А").
