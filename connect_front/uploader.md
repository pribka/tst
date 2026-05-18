# Uploader Audit

## Scope

This file captures:

- the backend contract for `/api/v1/common/upload/`
- the related editor upload contract
- all frontend places that call or embed the uploader
- alternative upload paths found on the frontend

## Current State After Refactor

Status as of `2026-04-03`.

This section supersedes the older audit notes below where they describe the pre-refactor uploader behavior.

### Universal frontend uploader

Source:

- `C:\Users\user\Desktop\connect_front\src\utils\upload.js`
- `C:\Users\user\Desktop\connect_front\src\main.js:249`

Behavior:

- all upload entry points should now go through `this.$uploadFile(...)`
- default mode is `auto`
- if file size is `<= 2 MB`, upload goes by the old direct flow
- if file size is `> 2 MB` and URL is one of the local common upload endpoints, file is split into chunks of `2 MB`
- chunk upload is transparent for the user
- external upload URLs stay on direct upload unless mode is explicitly overridden

Supported local chunk-capable endpoints:

- `/common/upload/`
- `/api/v1/common/upload/`
- `/common/upload_for_editor/`
- `/api/v1/common/upload_for_editor/`

Chunk request payload additions:

- `upload_id`
- `chunk_index`
- `total_chunks`
- `original_name`
- `chunked_upload`
- `file_size`

Delivery control on frontend:

- chunks are sent sequentially
- each chunk is retried up to `3` times
- upload progress is aggregated across the whole file
- cancellation still works for integrations that already used cancel tokens

### Backend chunk support

Source:

- `C:\projects\bpms_crm_develop_new\bpms\bpms_common\views.py`

Behavior:

- old direct upload contract is still supported unchanged
- if `upload_id` is absent, backend processes upload exactly as before
- if `upload_id` is present, backend stores chunks in temp storage, validates completeness, assembles the final file, creates the same `File` model record, and returns the usual response format
- non-final chunks return an internal ack response
- final chunk returns the same payload shape that old callers expect
- final response is cached by `upload_id` to safely survive retry of the last chunk

Current response compatibility:

- `/api/v1/common/upload/` still returns array payload compatible with `AppFileSerializer`
- `/api/v1/common/upload_for_editor/` still returns:

```json
{
  "urls": {
    "default": "<file-url>"
  }
}
```

### Current frontend integration points

Shared entry points:

- `C:\Users\user\Desktop\connect_front\src\modules\Upload\index.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileAttach.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileCreate.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\CKEditor\mixins\main.js`

Direct callers migrated to the universal helper:

- `C:\Users\user\Desktop\connect_front\src\views\Profile\Page.vue`
- `C:\Users\user\Desktop\connect_front\src\components\UserSettings\index.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\Directories\Team\components\CreateOrganization.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\Groups\mixins\createdMethods.js`
- `C:\Users\user\Desktop\connect_front\src\modules\Projects\mixins\createdMethods.js`
- `C:\Users\user\Desktop\connect_front\src\modules\Documents\components\CreateDocument\index.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\Gallery\index.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\UIModules\Gallery\index.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\Consolidation\components\UploadReport\index.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\SportsFacilities\components\RepairDrawer.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\SportsFacilities\components\RepairRequest.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2CommentsComponent\CommentInput.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2ChatComponent\components\ChatFooter\mixins\methods.js`

Alternative frontend path still present:

- `https://gos24.kz/api/v2/common/upload/`
  - used in:
  - `C:\Users\user\Desktop\connect_front\src\modules\GOS24\News\NewsForm.vue`
  - `C:\Users\user\Desktop\connect_front\src\modules\GOS24\NewsFinance\NewsFinanceForm.vue`
  - now also routed through `this.$uploadFile(...)`
  - remains on direct upload because this is an external backend

## Backend

### Route registration

- `C:\projects\bpms_crm_develop_new\bkz3\urls.py:61`
  - mounts `bpms.bpms_common.urls` under `api/v1/`
- `C:\projects\bpms_crm_develop_new\bpms\bpms_common\urls.py:22`
  - `common/upload_for_editor/`
- `C:\projects\bpms_crm_develop_new\bpms\bpms_common\urls.py:23`
  - `common/upload/`

Effective routes:

- `/api/v1/common/upload/`
- `/api/v1/common/upload_for_editor/`

### Contract: `/api/v1/common/upload/`

Sources:

- `C:\projects\bpms_crm_develop_new\bpms\bpms_common\views.py:519`
- `C:\projects\bpms_crm_develop_new\common\serializers.py:586`
- `C:\projects\bpms_crm_develop_new\common\models.py:971`

Behavior:

- Method: `POST`
- Auth: `JWTAuthentication`, `BasicAuthentication`, `CsrfExemptSessionAuthentication`
- Permission: `IsAuthenticated`
- Body: `multipart/form-data`
- File field: `upload`
- Multiple files are supported via `request.FILES.getlist('upload')`
- Optional flag: `is_confined`
  - backend checks only that the key exists in `request.POST`

Response:

- JSON array
- each item is serialized by `AppFileSerializer`

`AppFileSerializer` fields:

- `id`
- `name`
- `content_type`
- `extension`
- `path`
- `size`
- `is_image`
- `is_video`
- `is_audio`
- `file_type`
- `is_dynamic`
- `description`
- `obj_type`

Notes:

- `path` comes from `instance.author_url`
- most frontend callers expect an array and immediately use `data[0]`

### Contract: `/api/v1/common/upload_for_editor/`

Source:

- `C:\projects\bpms_crm_develop_new\bpms\bpms_common\views.py:489`

Behavior:

- Method: `POST`
- Auth: same auth classes
- Permission: `IsAuthenticated`
- File field: `upload`
- only the first file is used
- backend validates that the file is an image via `PIL.Image.open`
- non-image upload raises `ValidationError('not_image')`

Response shape:

```json
{
  "urls": {
    "default": "<file-url>"
  }
}
```

This is a separate editor-specific contract.

## Frontend

### Effective frontend contract for `/common/upload/`

Common pattern across the app:

- create `FormData`
- append the file under `upload`
- `POST` to `/common/upload/`
- send `multipart/form-data`
- expect an array response
- consume `data[0]`

Only one place sends `is_confined`:

- `C:\Users\user\Desktop\connect_front\src\modules\Consolidation\components\UploadReport\index.vue:281`

### Direct call sites of `/common/upload/`

- `C:\Users\user\Desktop\connect_front\src\views\Profile\Page.vue:530`
  - profile avatar after crop
- `C:\Users\user\Desktop\connect_front\src\components\UserSettings\index.vue:286`
  - avatar upload from user settings
- `C:\Users\user\Desktop\connect_front\src\modules\Directories\Team\components\CreateOrganization.vue:497`
  - organization logo
- `C:\Users\user\Desktop\connect_front\src\modules\Groups\mixins\createdMethods.js:63`
  - group logo
- `C:\Users\user\Desktop\connect_front\src\modules\Projects\mixins\createdMethods.js:62`
  - project logo
- `C:\Users\user\Desktop\connect_front\src\modules\Documents\components\CreateDocument\index.vue:225`
  - document file
- `C:\Users\user\Desktop\connect_front\src\modules\Gallery\index.vue:299`
  - gallery files
- `C:\Users\user\Desktop\connect_front\src\modules\UIModules\Gallery\index.vue:298`
  - UI gallery files
- `C:\Users\user\Desktop\connect_front\src\modules\Consolidation\components\UploadReport\index.vue:282`
  - consolidation report upload
- `C:\Users\user\Desktop\connect_front\src\modules\SportsFacilities\components\RepairDrawer.vue:343`
  - repair drawer attachments
- `C:\Users\user\Desktop\connect_front\src\modules\SportsFacilities\components\RepairRequest.vue:143`
  - repair request attachments
- `C:\Users\user\Desktop\connect_front\src\modules\vue2CommentsComponent\CommentInput.vue:429`
  - comment attachments
- `C:\Users\user\Desktop\connect_front\src\modules\vue2ChatComponent\components\ChatFooter\mixins\methods.js:155`
  - chat attachments
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileAttach.vue:311`
  - shared attach component
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileCreate.vue:490`
  - shared file queue uploader
- `C:\Users\user\Desktop\connect_front\src\modules\Upload\index.vue:271`
  - cropper mode inside shared Upload component

## Shared uploader components

### `src/modules/Upload/index.vue`

Sources:

- `C:\Users\user\Desktop\connect_front\src\modules\Upload\index.vue:155`
- `C:\Users\user\Desktop\connect_front\src\modules\Upload\index.vue:23`
- `C:\Users\user\Desktop\connect_front\src\modules\Upload\index.vue:271`

Behavior:

- exposes prop `action`
- default is `${process.env.VUE_APP_API_URL}/common/upload/`
- normal mode uses Ant `a-upload` and really passes `:action="action"`
- cropper mode bypasses that and posts directly to `/common/upload/`

`<Upload` consumers:

- `C:\Users\user\Desktop\connect_front\src\modules\BusinessProcesses\components\CreateDrawer\index.vue:72`
- `C:\Users\user\Desktop\connect_front\src\modules\BusinessProcesses\components\ViewDrawer\index.vue:237`
- `C:\Users\user\Desktop\connect_front\src\modules\Groups\CreateModal.vue:67`
- `C:\Users\user\Desktop\connect_front\src\modules\Groups\MainPage\modules\Galery.vue:106`
- `C:\Users\user\Desktop\connect_front\src\modules\Projects\CreateModal.vue:146`
- `C:\Users\user\Desktop\connect_front\src\modules\Projects\ProjectCreate.vue:22`
- `C:\Users\user\Desktop\connect_front\src\modules\Projects\MainPage\modules\Galery.vue:106`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2TaskComponent\components\TaskShowDrawer\TabWidgets\Delivery\ProductModal.vue:76`
- `C:\Users\user\Desktop\connect_front\src\modules\Orders\views\CreateOrder\widgets\fields\Upload.vue:2`
- `C:\Users\user\Desktop\connect_front\src\modules\Orders\views\returnOrder\widgets\fields\Upload.vue:2`
- `C:\Users\user\Desktop\connect_front\src\modules\Orders\components\OrdersList\ProductModal.vue:76`

Finding:

- no frontend usage was found that overrides this uploader's `action` prop
- in practice these consumers stay on the default `${VUE_APP_API_URL}/common/upload/`

### `src/modules/vue2Files/components/FileAttach.vue`

Sources:

- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileAttach.vue:160`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileAttach.vue:311`

Behavior:

- exposes prop `action`
- default is `${process.env.VUE_APP_API_URL}/common/upload/`
- actual upload call is hardcoded to `this.$http.post('/common/upload/', ...)`

Important mismatch:

- the `action` prop exists
- but the real request does not use it

`<FileAttach` consumers:

- `C:\Users\user\Desktop\connect_front\src\modules\Calendar\components\AddEvent.vue:165`
- `C:\Users\user\Desktop\connect_front\src\modules\AccountingReports\components\Drawers\FinancePlanChange\Rationale.vue:57`
- `C:\Users\user\Desktop\connect_front\src\modules\AccountingReports\components\Drawers\ChangeCalculation\Rationale.vue:53`
- `C:\Users\user\Desktop\connect_front\src\modules\InvestProject\components\AddProject.vue:502`
- `C:\Users\user\Desktop\connect_front\src\modules\RequestApprovals\ViewDrawer\AdvanceReport\index.vue:201`
- `C:\Users\user\Desktop\connect_front\src\modules\RequestApprovals\AddDrawer\index.vue:258`
- `C:\Users\user\Desktop\connect_front\src\modules\Consolidation\components\CreateConsolidation\index.vue:217`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2CommentsComponent\CommentInput.vue:113`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2CommentsComponent\CommentInput.vue:216`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2TaskComponent\components\EditModal\index.vue:263`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2TaskComponent\components\EditDrawer\FormParts\AttachFiles.vue:18`
- `C:\Users\user\Desktop\connect_front\src\modules\Groups\MainPage\PagesSwitch\News.vue:134`
- `C:\Users\user\Desktop\connect_front\src\modules\Projects\MainPage\PagesSwitch\News.vue:134`
- `C:\Users\user\Desktop\connect_front\src\modules\HelpDesk\components\Tickets\TicketDrawer\components\ChatList\Footer.vue:3`
- `C:\Users\user\Desktop\connect_front\src\modules\HelpDesk\components\Request\RequestDrawerV2\components\ChatList\Footer.vue:3`
- `C:\Users\user\Desktop\connect_front\src\modules\HelpDesk\components\Request\RequestDrawer\components\ChatList\Footer.vue:3`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileCreate.vue:39`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileCreate.vue:56`

### `src/modules/vue2Files/components/FileCreate.vue`

Source:

- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\FileCreate.vue:490`

Behavior:

- uses Ant `customRequest`
- posts to `/common/upload/`
- supports upload progress
- supports cancel via `axios.CancelToken`

`<FileCreate` consumers:

- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\Files.vue:136`
- `C:\Users\user\Desktop\connect_front\src\modules\vue2Files\components\ViewTypes\FileGrid.vue:18`
  - currently commented out

## Alternative upload paths found on the frontend

### 1. CKEditor default path: `/api/v1/common/upload_for_editor/`

Sources:

- `C:\Users\user\Desktop\connect_front\src\modules\CKEditor\mixins\mixins.js:23`
- `C:\Users\user\Desktop\connect_front\src\modules\CKEditor\mixins\mixins.js:71`
- `C:\Users\user\Desktop\connect_front\src\modules\CKEditor\mixins\main.js:59`
- `C:\Users\user\Desktop\connect_front\src\modules\CKEditor\mixins\main.js:82`
- `C:\Users\user\Desktop\connect_front\src\modules\CKEditor\DocumentEditor.vue:129`

Frontend contract:

- default `uploadUrl = "/api/v1/common/upload_for_editor/"`
- default field name is `upload`
- CKEditor expects editor-style response with `urls.default`

### 2. GOS24 override: `https://gos24.kz/api/v2/common/upload/`

Sources:

- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\mixins\mixins.js:5`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\mixins\mixins.js:6`

Frontend contract:

- `uploadUrl: 'https://gos24.kz/api/v2/common/upload/'`
- `uploadFieldKey: 'file'`

This means GOS24 does not use local `/api/v1/common/upload_for_editor/`.
It uploads to an external API and changes the field name from `upload` to `file`.

Consumers of this override:

- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\Articles\ArticleForm.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\Knowledgebase\KnowledgebaseForm.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\News\NewsForm.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\NewsFinance\NewsFinanceForm.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\Official\OfficialForm.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\Question\QuestionForm.vue`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\Webinar\WebinarForm.vue`

### 3. Direct XHR upload in GOS24 forms

Sources:

- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\News\NewsForm.vue:271`
- `C:\Users\user\Desktop\connect_front\src\modules\GOS24\NewsFinance\NewsFinanceForm.vue:271`

Behavior:

- builds `FormData`
- appends file under `file`
- posts to `https://gos24.kz/api/v2/common/upload/`
- then tries to read the uploaded URL from `url`, `default`, `location`, or `path`

## Summary

For the common uploader area, three distinct flows were found:

- main app upload: `/api/v1/common/upload/`
- editor-only upload: `/api/v1/common/upload_for_editor/`
- external GOS24 upload: `https://gos24.kz/api/v2/common/upload/`

Key findings:

- backend `/common/upload/` returns an array of `AppFileSerializer`
- almost all frontend consumers of `/common/upload/` assume `data[0]`
- `is_confined` is only used in consolidation report upload
- `FileAttach.vue` exposes `action` but does not actually use it
- `Upload/index.vue` uses `action` only in normal mode; cropper mode is still hardcoded to `/common/upload/`
