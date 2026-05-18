# Upload Tasks

Статус на `2026-04-03`.

Ниже оформлены две отдельные задачи по итогам текущего аудита upload-механики.

## Задача 1. Привести ограничения на upload к согласованной политике

### Контекст

В проекте уже внедрён единый upload helper с поддержкой chunk upload, и часть старых жёстких ограничений на `10 MB` уже снята. Но вокруг upload всё ещё остаётся несколько разных типов ограничений:

- ограничения по размеру файла
- ограничения по количеству файлов
- ограничения по типам файлов
- ограничения по минимальным размерам изображения

Сейчас эти ограничения заданы не централизованно, а распределены по разным компонентам и экранам.

### Что уже сделано

- Для основных upload-потоков внедрён единый механизм через `src/utils/upload.js`.
- Старые жёсткие client-side ограничения на `10 MB` уже сняты в следующих местах:
  - `src/views/Profile/Page.vue`
  - `src/components/UserSettings/index.vue`
  - `src/modules/Upload/index.vue`
  - `src/modules/Groups/mixins/createdMethods.js`
  - `src/modules/Projects/mixins/createdMethods.js`
  - `src/modules/Directories/Team/components/CreateOrganization.vue`
  - `src/modules/vue2CommentsComponent/CommentInput.vue`
  - `src/modules/vue2ChatComponent/components/ChatFooter/mixins/methods.js`

### Что найдено сейчас

#### 1. Ограничения по размеру файла

- В `src/modules/vue2Files/components/FileAttach.vue` есть проп `maxMBSize` со значением по умолчанию `1`.
- Там же реальная проверка лимита строится через `this.maxMBSize * (1024 ** 2)`.
- Во многих местах этот лимит переопределён в `50 MB`:
  - `src/modules/AccountingReports/components/Drawers/ChangeCalculation/Rationale.vue`
  - `src/modules/AccountingReports/components/Drawers/FinancePlanChange/Rationale.vue`
  - `src/modules/Consolidation/components/CreateConsolidation/index.vue`
  - `src/modules/HelpDesk/components/Request/RequestDrawer/components/ChatList/Footer.vue`
  - `src/modules/HelpDesk/components/Request/RequestDrawerV2/components/ChatList/Footer.vue`
  - `src/modules/HelpDesk/components/Tickets/TicketDrawer/components/ChatList/Footer.vue`
  - `src/modules/InvestProject/components/AddProject.vue`
  - `src/modules/RequestApprovals/AddDrawer/index.vue`
  - `src/modules/RequestApprovals/ViewDrawer/AdvanceReport/index.vue`
  - `src/modules/vue2CommentsComponent/CommentInput.vue`
  - `src/modules/vue2TaskComponent/components/EditDrawer/FormParts/AttachFiles.vue`
  - `src/modules/vue2TaskComponent/components/EditModal/index.vue`

#### 2. Ограничения по количеству файлов

- В `src/modules/vue2Files/components/FileAttach.vue` есть `maxFileCount` со значением по умолчанию `5`.
- В `src/modules/Upload/index.vue` есть `limit` со значением по умолчанию `5`.
- В чате есть отдельное ограничение не на размер, а на количество: максимум `10` файлов в сообщении:
  - `src/modules/vue2ChatComponent/components/ChatFooter/mixins/methods.js`

#### 3. Ограничения по типам файлов

- Только изображения для avatar/cropper-потоков:
  - `src/components/UserSettings/index.vue`
  - `src/views/Profile/Page.vue`
  - `src/modules/Directories/Team/components/CreateOrganization.vue`
  - `src/modules/Upload/index.vue`
- Только документы определённых форматов:
  - `src/modules/Documents/components/CreateDocument/index.vue`
- Только изображения для галереи:
  - `src/modules/Gallery/index.vue`
  - `src/modules/UIModules/Gallery/index.vue`
- Ограниченный набор типов для чата:
  - `src/modules/vue2ChatComponent/components/ChatFooter/index.vue`
- Только PDF в одном из экранов расчётов:
  - `src/modules/AccountingReports/components/Drawers/ChangeCalculation/index.vue`

#### 4. Ограничения по изображению как таковому

- В avatar/cropper-потоках остаются проверки минимальных размеров изображения через `checkImageWidthHeight(...)`:
  - `src/views/Profile/Page.vue`
  - `src/components/UserSettings/index.vue`
  - `src/modules/Upload/index.vue`
  - `src/modules/Groups/mixins/createdMethods.js`
  - `src/modules/Projects/mixins/createdMethods.js`
  - `src/modules/Directories/Team/components/CreateOrganization.vue`
- В `src/modules/Upload/index.vue` также заданы `minWidth` и `minHeight`.

#### 5. Отдельный кейс GOS24

- В `src/modules/GOS24/News/NewsForm.vue` и `src/modules/GOS24/NewsFinance/NewsFinanceForm.vue` остаётся отдельный лимит `5 MB` на изображение.
- Там же остаётся ограничение по MIME-типам: `jpeg/png/webp/gif`.

### Что требуется обсудить

- Нужен ли вообще общий лимит по размеру файла на фронте, если уже есть chunk upload.
- Если лимит нужен, то где он должен быть определён:
  - централизованно в одном месте
  - через конфиг
  - через пропсы отдельных компонентов
- Нужно ли сохранять дефолт `1 MB` в `src/modules/vue2Files/components/FileAttach.vue`.
- Нужно ли сохранять лимит `10` файлов в сообщении в чате.
- Являются ли ограничения по `accept` и по минимальным размерам изображений частью бизнес-логики или это временные технические фильтры.
- Нужно ли сохранять отдельный лимит `5 MB` в GOS24.

### Что неприемлемо

- Когда одинаковый upload-сценарий на разных экранах имеет разные лимиты без явной причины.
- Когда размерные ограничения зашиты в компонентах и не видны как часть общей политики.
- Когда пользователь может загрузить файл в одном месте, но не может в другом, хотя backend-контракт один и тот же.
- Когда ограничения продолжают жить как разрозненные hardcode-проверки по всему фронту.

### Целевой результат задачи

- Согласовать единую политику ограничений для upload.
- Явно отделить:
  - бизнес-ограничения
  - UX-ограничения
  - технические ограничения
- Убрать случайные и исторические лимиты.
- Оставить только те ограничения, которые осознанно приняты командой.

## Задача 2. Убрать кастомные upload-ветки с жёстко прописанными доменами

### Контекст

В проекте уже внедрён общий upload helper и большинство экранов приведены к единому паттерну `this.$uploadFile(...)`. Но остаётся отдельная ветка upload-логики, которая ходит во внешний домен и живёт по собственному контракту.

### Что уже сделано

- Старый самописный upload через `XMLHttpRequest` уже убран.
- Эти формы уже переведены на `this.$uploadFile(...)`.
- То есть проблема сейчас не в старом XHR, а в том, что контракт и endpoint всё ещё особые.

### Что найдено сейчас

Кастомный upload с жёстко прописанным внешним доменом найден в двух файлах:

- `src/modules/GOS24/News/NewsForm.vue`
- `src/modules/GOS24/NewsFinance/NewsFinanceForm.vue`

Что именно в них отличается от общего паттерна:

- Используется собственный `customRequest="uploadImage"`.
- Жёстко прописан внешний URL:
  - `https://gos24.kz/api/v2/common/upload/`
- Используется поле файла `file`, а не `upload`.
- Явно задано `withCredentials: false`.
- Отдельно задан front-side лимит `5 MB`.
- Отдельно задан список допустимых MIME-типов.

### Что требуется обсудить

- Должен ли внешний GOS24 upload остаться отдельной веткой вообще.
- Если должен остаться:
  - нужно ли вынести домен в конфиг
  - нужно ли вынести контракт в отдельный адаптер
  - нужно ли явно задокументировать, что это исключение из общего upload-правила
- Если не должен остаться:
  - можно ли перевести его на тот же backend-контракт, что и остальной фронт
  - можно ли убрать жёсткий внешний домен из компонентного кода

### Что неприемлемо

- Жёстко прописанный внешний домен прямо внутри UI-компонента.
- Отдельный upload-контракт без явного статуса исключения.
- Ситуация, когда внешний upload выглядит как обычный, но по факту не наследует общую политику chunk/direct/config.
- Скрытые отличия по полям запроса и credential policy, которые не отражены в конфигурации.

### Целевой результат задачи

- Либо перевести GOS24 upload на ту же общую модель, что и остальные upload-потоки.
- Либо оформить его как явное исключение:
  - с вынесенным URL в конфиг
  - с отдельным адаптером
  - с документированным контрактом
  - без жёсткого домена в компоненте

## Рекомендуемый порядок обсуждения

1. Сначала договориться по общей политике ограничений.
2. Затем решить, является ли GOS24 допустимым исключением.
3. После этого уже вычищать оставшиеся лимиты и hardcode-домены кодом.
