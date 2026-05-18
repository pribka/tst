# Upload Loans

## Scope

Этот файл фиксирует по тем же upload-связанным файлам:

- где есть захардкоженные домены или URL
- где upload реализован не через общий паттерн "как у остальных"

Статус на `2026-04-03`.

## Захардкоженные домены и URL

### Внешний абсолютный upload-домен

- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\News\NewsForm.vue:270`
  - `https://gos24.kz/api/v2/common/upload/`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\NewsFinance\NewsFinanceForm.vue:270`
  - `https://gos24.kz/api/v2/common/upload/`

Это единственный найденный рабочий абсолютный upload-домен в проверенной группе файлов.

### Базовый upload через env

- `C:\Users\user\Desktop\connect_front\src\modules\Upload\index.vue:159`
  - `${process.env.VUE_APP_API_URL}/common/upload/`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileAttach.vue:163`
  - `${process.env.VUE_APP_API_URL}/common/upload/`

Это не захардкоженный домен, а env-конфигурация, но место важно как источник базового upload endpoint.

### Локальный upload route

Следующие файлы явно указывают локальный endpoint `/common/upload/`:

- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileCreate.vue:488`
- `C:\Users\user\Desktop\connect_front\src\modules\Directories\Team\components\CreateOrganization.vue:496`
- `C:\Users\user\Desktop\connect_front\src\modules\Groups\mixins\createdMethods.js:62`
- `C:\Users\user\Desktop\connect_front\src\modules\Projects\mixins\createdMethods.js:61`
- `C:\Users\user\Desktop\connect_front\src\modules\Documents\components\CreateDocument\index.vue:225`
- `C:\Users\user\Desktop\connect_front\src\modules\Gallery\index.vue:299`
- `C:\Users\user\Desktop\connect_front\src\modules\UIModules\Gallery\index.vue:298`
- `C:\Users\user\Desktop\connect_front\src\modules\Consolidation\components\UploadReport\index.vue:281`
- `C:\Users\user\Desktop\connect_front\src\modules\SportsFacilities\components\RepairDrawer.vue:343`
- `C:\Users\user\Desktop\connect_front\src\modules\SportsFacilities\components\RepairRequest.vue:143`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2CommentsComponent\CommentInput.vue:429`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2ChatComponent\components\ChatFooter\mixins\methods.js:153`
- `C:\Users\user\Desktop\connect_front\src\views\Profile\Page.vue:529`
- `C:\Users\user\Desktop\connect_front\src\components\UserSettings\index.vue:285`

### Прочие захардкоженные домены в этих же файлах

Не про upload напрямую, но в этом же наборе файлов найдены жёстко заданные `http://`:

- `C:\Users\user\Desktop\connect_front\src\modules\Groups\mixins\createdMethods.js:178`
  - `return \`http://${newUrl}\`;`
- `C:\Users\user\Desktop\connect_front\src\modules\Projects\mixins\createdMethods.js:182`
  - `return \`http://${newUrl}\`;`

### Комментарии с историческими URL

- `C:\Users\user\Desktop\connect_front\src\modules\Upload\index.vue:158`
  - `http://bkz.centersoft.kz/api/v1/common/upload/`

Это комментарий, не рабочий код.

## Кто делает upload не как остальные

## Общий паттерн

Сейчас целевой общий паттерн такой:

- вызов через `this.$uploadFile(...)`
- общая логика chunk/direct спрятана в `src/utils/upload.js`

## Явные выбросы из общего поведения

### GOS24 формы

- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\News\NewsForm.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\NewsFinance\NewsFinanceForm.vue`

Они уже используют `this.$uploadFile(...)`, но отличаются от остальных:

- ходят не в локальный `/common/upload/`, а во внешний `https://gos24.kz/api/v2/common/upload/`
- используют поле файла `file`, а не `upload`
- выставляют `withCredentials: false`
- имеют собственный `customRequest="uploadImage"`
- chunk-flow для них по текущей логике не включается автоматически, потому что это внешний backend

Итог:

- это уже не самодельный XHR-upload
- но это всё ещё отдельная ветка контракта

## Что больше не найдено

В этой группе файлов больше не найдено:

- `new XMLHttpRequest()`
- прямого `this.$http.post('/common/upload/', formData, ...)`
- прямого `request.post('/common/upload/', ...)`

То есть старый самодельный upload вида:

```js
const fd = new FormData()
fd.append('file', file)
const xhr = new XMLHttpRequest()
xhr.open('POST', 'https://gos24.kz/api/v2/common/upload/')
...
xhr.send(fd)
```

в этих файлах больше не используется.

## Текущие обёртки над общим upload helper

Ниже места, где есть свой метод-обёртка, но внутри всё равно вызывается `this.$uploadFile(...)`:

- `C:\Users\user\Desktop\connect_front\src\modules\Upload\index.vue:261`
  - `customUploadRequest(...)`
- `C:\Users\user\Desktop\connect_front\src\modules\Upload\index.vue:275`
  - `uploadImage()`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileCreate.vue:472`
  - `uploadRequest(...)`
- `C:\Users\user\Desktop\connect_front\src\modules\CKEditor\mixins\main.js:23`
  - `UploadAdapter.upload()`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileAttach.vue:308`
  - `handleFileUpload(...)`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\News\NewsForm.vue:266`
  - `uploadImage(...)`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\NewsFinance\NewsFinanceForm.vue:266`
  - `uploadImage(...)`

Это не самодеятельный upload в старом смысле, а разные UI-адаптеры вокруг единого helper.

## Вывод

По текущему срезу главный нестандартный upload-кейс один:

- GOS24 `NewsForm.vue`
- GOS24 `NewsFinanceForm.vue`

Причина:

- внешний абсолютный домен
- отдельный backend-контракт (`file`, не `upload`)
- отдельная политика credentials

Всё остальное из проверенной группы уже приведено к общему upload helper.
