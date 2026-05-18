# Planner Research

## 1. Old Planner Overview

- Legacy Planner lives in the old Vue 2 logistics module and is centered around a dedicated `taskPlanner` Vuex module.
- Root page composition in the old implementation:
  - `PlannerToolbar`
  - `OrdersQueue`
  - `PerformerColumn`
- Main orchestration happens in the page component:
  - initialize store data
  - keep current drag source
  - dispatch assign / move / unassign actions
- Column rendering is utility-driven:
  - slot generation
  - overlap layout calculation
  - preferred range highlighting
  - card height calculation
- The old Planner is tightly bound to logistics orders and delivery tasks, so we should reuse the mechanics, not the domain logic.

## 2. Frontend Integration Points

### Existing reusable pieces

- Performer selection can reuse [`src/components/UserSelect/index.vue`](/c:/Users/user/Desktop/connect_front/src/components/UserSelect/index.vue).
- Hover popups can reuse globally registered Ant Design `popover` / `tooltip`.
- Current "My Day" data layer already exists in [`src/modules/WorkPlan/store/actions.js`](/c:/Users/user/Desktop/connect_front/src/modules/WorkPlan/store/actions.js).
- Current app already has query-based drawers for details:
  - `task`
  - `event`
  - `requestView`

### Existing creation entry points

- Task create:
  - `eventBus.$emit('add_task_modal', payload)`
  - receiver: [`src/modules/vue2TaskComponent/components/EditModal/index.vue`](/c:/Users/user/Desktop/connect_front/src/modules/vue2TaskComponent/components/EditModal/index.vue)
  - supports injected form data through `formInject`
- Event create:
  - `eventBus.$emit('open_event_form', startDate, endDate, event, relatedObject, uKey, nameFocus, projectId)`
  - receiver: [`src/modules/Calendar/components/AddEvent.vue`](/c:/Users/user/Desktop/connect_front/src/modules/Calendar/components/AddEvent.vue)
  - supports start/end prefill
- Helpdesk request create:
  - `eventBus.$emit('helpdesc_add_tickets', payload?)`
  - receiver: [`src/modules/HelpDesk/components/Tickets/ModalForm.vue`](/c:/Users/user/Desktop/connect_front/src/modules/HelpDesk/components/Tickets/ModalForm.vue)
  - Planner uses the standard HelpDesk ticket form instead of a separate lightweight request form
  - current Planner prefill:
    - `specialist`
    - `receipt_date`
    - `dead_line`
  - contractor and contact person are selected inside the standard HelpDesk form with its native dependency rules

### Navigation integration

- Top-level menu is built in [`src/store/modules/navigation/mutations.js`](/c:/Users/user/Desktop/connect_front/src/store/modules/navigation/mutations.js).
- It combines:
  - backend `/app_info/routes/`
  - static frontend-added routes
- Since Planner is a frontend module, it can be injected as a static route.
- Because it is not backed by route metadata from backend, it must be skipped in [`src/utils/routerUtils.js`](/c:/Users/user/Desktop/connect_front/src/utils/routerUtils.js) `initRouteInfo`.

## 3. Backend Integration Points

### Tasks

- Endpoint:
  - `GET /tasks/task/my_day/`
  - `PATCH /tasks/task/{id}/`
  - `POST /tasks/task/`
- Serializer fields relevant for planning:
  - `operator`
  - `date_start_plan`
  - `dead_line`
  - `cooperators`
  - `visors`

### Events

- Endpoint:
  - `GET /calendars/events/my_day/`
  - `GET /calendars/events/{id}/`
  - `PATCH /calendars/events/{id}/`
  - `POST /calendars/events/`
- Serializer fields relevant for planning:
  - `start_at`
  - `end_at`
  - `all_day`
  - `members`

### Helpdesk Requests

- Planner scope maps "obraschenie" to helpdesk requests, not workflow approvals.
- Endpoint:
  - `GET /help_desk/tickets/my_day/`
  - `POST /help_desk/tickets/for_client/create/`
  - `PATCH /help_desk/tickets/{id}/`
- Serializer fields relevant for planning:
  - `specialist`
  - `dead_line`
  - `start_date`
  - `end_date`

## 4. Time Fields / Ranges Per Entity

- `task`
  - start: `date_start_plan`
  - end: `dead_line`
  - performer: `operator`
- `event`
  - start: `start_at`
  - end: `end_at`
  - performer mapping on board: selected `members`
  - all-day events should stay in queue, not in timed slots
- `request`
  - start: `start_date`
  - end: `end_date`
  - deadline fallback: `dead_line`
  - performer: `specialist`

## 5. Queue Solution

- Reuse current "My Day" data from `WorkPlan`.
- Build a Planner normalization layer on top of:
  - tasks
  - events
  - helpdesk tickets
- Put into the left queue items that are not schedulable into a timed board immediately:
  - no performer
  - missing start/end time range
  - all-day event
- Queue cards should remain draggable to a board slot.

## 6. Slots / Scales Solution

- `1 hour` mode:
  - performer columns
  - 60-minute clickable slots
  - vertical time scale
  - absolute-positioned cards by exact time
- `2 hours` mode:
  - same timed board
  - 120-minute clickable slots
- `day` mode:
  - overview mode where the day is the display unit
  - cards grouped inside a day cell per performer
- `week` mode:
  - overview mode for 7 days
  - if one performer is selected, days are shown in a 7-column grid
  - if multiple performers are selected, each performer gets a compact day stack
- `2 weeks` mode:
  - 14-day overview for one performer
- Overlaps:
  - assign simple lanes inside a performer column
  - shrink card width inside overlap groups
- Use a full-day 24h timed canvas for exact planning views.

## 7. Two-Week Mode Solution

- Scope: one performer only.
- If multiple performers are selected, two-week mode should ask the user to narrow to one performer.
- In two-week mode, board switches from a timed performer-column view to a day-by-day focus board for 14 days.
- Cards are grouped by day and sorted by start time.

## 8. Reassignment Solution

- Provide a dedicated "Peredat drugomu" modal from a card.
- Modal fields:
  - performer
  - start datetime
  - end datetime
- Update adapters:
  - task -> `operator`, `date_start_plan`, `dead_line`
  - request -> `specialist`, `start_date`, `end_date`, `dead_line`
  - event -> fetch detail, replace current displayed member with target performer, patch `members`, `start_at`, `end_at`

## 9. Decision Log

- Decision: scope Planner to `task`, `request`, `event`.
  - Reason: this is the explicit scope from the current TZ.
- Decision: build Planner on top of existing `WorkPlan` store actions instead of creating a second network layer.
  - Reason: current `my_day` endpoints and update hooks already exist and are battle-tested.
- Decision: inject Planner as a static frontend route.
  - Reason: backend route metadata is not required for the page itself, and this avoids backend dependency for MVP.
- Decision: use the standard HelpDesk ticket create form for Planner request creation.
  - Reason: it already contains contractor, contact person, specialist, category, and date-range logic, so Planner only needs to prefill performer and slot range.
- Decision: extend event create modal with optional injected members payload.
  - Reason: slot-based event creation should prefill the selected performer when the existing drawer can accept it safely.
- Decision: use performer-centric filters in the reused data layer.
  - Reason: board columns must represent executors/specialists, not every related user.
- Decision: agreed product changes override the initial Planner TZ in several UX areas.
  - Agreed changes:
    - performer selection now goes through reusable saved teams instead of a direct flat multi-user picker in the toolbar;
    - toolbar slot-size switch is `30 min / 1 hour / 2 hours`;
    - hover popover on cards is removed, key details stay in the card itself;
    - long-horizon loading is handled through per-column day scrolling and lazy loading instead of a dedicated mandatory "2 weeks" focus button;
    - transfer modal uses a performer/slot matrix with contiguous multi-slot selection and infinite day loading.
  - Result: `tz.md` and `tz_codex.md` were updated to reflect the agreed scope.

## 10. Execution Log

### Task 1. Transfer modal slots

- Scope of this iteration:
  - fix false occupied slots for the current performer in the transfer modal
  - show time directly inside each transfer slot cell
  - keep multi-slot selection sequential only, with explicit checkbox UI
- Code changes:
  - strengthened performer resolution in the modal against raw entity fields:
    - `task -> raw.operator`
    - `request -> raw.specialist`
    - `event -> raw.members`
  - transfer cells now render:
    - checkbox
    - slot time inside the cell
    - compact occupied-item label when the slot is busy
  - busy transfer cells remain orange, selectable, and still support only contiguous selection
- Files touched for task 1:
  - [`src/modules/Planner/Page.vue`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/Page.vue)
  - [`src/modules/Planner/page.scss`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/page.scss)
  - [`src/modules/Planner/utils.js`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/utils.js)
- Status:
  - implemented in code
  - requires browser verification against live modal data for the current user

### Task 2. Transfer modal entity type

- Scope of this iteration:
  - keep the entity type stable inside the transfer modal
  - avoid falling back from `task` to helpdesk `request` logic on submit
- Code changes:
  - transfer modal state now stores its own `entityType`
  - submit passes explicit `entityType` into `applyTransfer`
  - transfer adapter dispatch now uses a single resolved type with `else if` routing:
    - `task -> /tasks/task/{id}/`
    - `request -> /help_desk/tickets/{id}/`
    - `event -> /calendars/events/{id}/`
  - unknown type now stops the transfer instead of silently hitting a wrong branch
- Files touched for task 2:
  - [`src/modules/Planner/Page.vue`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/Page.vue)
- Status:
  - implemented in code
  - requires browser verification with a real task transfer from the modal

### Task 3. Drag to slot start

- Scope of this iteration:
  - make drag-and-drop in timed planner always start exactly from the beginning of the target slot
- Code changes:
  - introduced a dedicated planner slot-start helper for timed board moves
  - slot picker creation and timed drag-drop now use the same slot-start calculation
  - removed the extra generic rounding step from timed drag-drop so the start point stays bound to the planner slot itself
- Files touched for task 3:
  - [`src/modules/Planner/Page.vue`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/Page.vue)
  - [`src/modules/Planner/page.scss`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/page.scss)
- Status:
  - implemented in code
  - requires browser verification by dragging an item between timed slots

### Task 4. Resize card across slots

- Scope of this iteration:
  - make timed planner cards resizable across multiple slots
- Code changes:
  - fixed resize listener lifecycle so `mousemove` / `mouseup` work with component context
  - added explicit listener attach/detach helpers for resize mode
  - resize start now prevents default browser selection behavior
  - existing bottom resize handle remains the entry point for stretching the card downward by slot step
- Files touched for task 4:
  - [`src/modules/Planner/Page.vue`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/Page.vue)
  - [`src/modules/Planner/page.scss`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/page.scss)
- Status:
  - implemented in code
  - requires browser verification by stretching a timed card downward

### Task 5. Async column loading without planner freeze

- Scope of this iteration:
  - stop blocking the whole planner during data loading
  - load only the scrolled column when extending days
  - keep modal loading non-blocking
  - widen planner columns again
- Code changes:
  - planner base data is now fetched locally in parallel instead of relying on blocking page-wide workplan loading
  - existing planner content stays on screen while a new base range is loading
  - timed and overview columns now load additional days only for the scrolled performer
  - each column has its own loading state and loader
  - transfer modal no longer wraps the whole schedule in a blocking spinner; loading is shown as an inline indicator
  - planner columns were widened again for better readability
  - async request guards were added to avoid stale responses overriding a newer planner state
- Files touched for task 5:
  - [`src/modules/Planner/Page.vue`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/Page.vue)
  - [`src/modules/Planner/page.scss`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/page.scss)
- Status:
  - implemented in code
  - requires browser verification for:
    - no planner freeze on base refresh
    - loader only on the scrolled column
    - modal remains clickable while slots are loading

### Task 6. Compact toolbar and performer teams

- Scope of this iteration:
  - compress the planner toolbar into a single top row
  - replace direct performer picking with reusable saved teams
  - allow activating up to two teams at once
- Code changes:
  - toolbar is now built around:
    - title
    - date picker
    - slot size switch: `30 min / 1 hour / 2 hours`
    - team chooser
  - added team model with local persistence:
    - create team
    - name team
    - edit team members via existing user drawer
    - activate/deactivate team
    - activate up to two teams at the same time
    - delete team
  - active performers are now resolved as a merged unique user list from selected teams
  - legacy direct selected-users storage is migrated into a first default team when possible
- Files touched for task 6:
  - [`src/modules/Planner/Page.vue`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/Page.vue)
  - [`src/modules/Planner/page.scss`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/page.scss)
- Status:
  - implemented in code
  - requires browser verification for:
    - team creation/edit/delete
    - selecting exactly two teams
    - correct merged performer set in planner after team switch

### Task 7. Team selection UX

- Scope of this iteration:
  - separate single-team selection from additive multi-team selection
  - keep team controls visible only on hover
  - remove the hard limit on the number of simultaneously visible teams
- Code changes:
  - each team chip now has an explicit checkbox for additive inclusion into the planner view
  - clicking the team name now switches planner view to that team only and clears the other active teams
  - edit/delete controls are no longer shown for selected teams by default and appear only on hover
  - additive team selection no longer stops at two active teams
- Files touched for task 7:
  - [`src/modules/Planner/Page.vue`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/Page.vue)
  - [`src/modules/Planner/page.scss`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/page.scss)
- Status:
  - implemented in code
  - requires browser verification for:
    - checkbox multi-select
    - single-team switch by clicking the chip body
    - hover-only visibility of team controls

### Task 8. Immediate render after create

- Scope of this iteration:
  - make newly created planner entities appear immediately without waiting for a full planner reload
- Code changes:
  - planner now listens to create-success events for:
    - task created from planner slot
    - event created from planner slot
    - helpdesk ticket created from planner slot
  - created entities are normalized and merged directly into local planner items
  - task create flow now uses `create_handler: planner` to receive a planner-specific created event
  - helpdesk ticket create flow now marks planner origin and emits a dedicated `PLANNER_TICKET_CREATED` event after success
  - request normalization now falls back to `receipt_date` when `start_date` is absent
- Files touched for task 8:
  - [`src/modules/Planner/Page.vue`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/Page.vue)
  - [`src/modules/Planner/utils.js`](/c:/Users/user/Desktop/connect_front/src/modules/Planner/utils.js)
  - [`src/modules/HelpDesk/components/Tickets/ModalForm.vue`](/c:/Users/user/Desktop/connect_front/src/modules/HelpDesk/components/Tickets/ModalForm.vue)
- Status:
  - implemented in code
  - requires browser verification for:
    - task created from planner slot appears immediately
    - event created from planner slot appears immediately
    - helpdesk ticket created from planner slot appears immediately
