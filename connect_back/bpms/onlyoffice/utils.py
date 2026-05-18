import hashlib
import io
import logging
import uuid
from urllib.parse import quote

import jwt
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.urls import reverse
from rest_framework import exceptions
from rest_framework.test import APIRequestFactory, force_authenticate

from bpms.chat.models import ChatModel
from bpms.comments.models import CommentModel
from common.models import File
from common.utils import check_chat_attachments


logger = logging.getLogger(__name__)

WORD_EXTENSIONS = {
    "doc",
    "docm",
    "docx",
    "dot",
    "dotm",
    "dotx",
    "fodt",
    "odt",
    "rtf",
    "txt",
}
CELL_EXTENSIONS = {
    "csv",
    "fods",
    "ods",
    "xls",
    "xlsb",
    "xlsm",
    "xlsx",
}
SLIDE_EXTENSIONS = {
    "fodp",
    "odp",
    "pot",
    "potm",
    "potx",
    "pps",
    "ppsm",
    "ppsx",
    "ppt",
    "pptm",
    "pptx",
}
PDF_EXTENSIONS = {
    "pdf",
}
SUPPORTED_EXTENSIONS = WORD_EXTENSIONS | CELL_EXTENSIONS | SLIDE_EXTENSIONS | PDF_EXTENSIONS

DOWNLOAD_SALT = "onlyoffice.download"
CALLBACK_SALT = "onlyoffice.callback"
REPORT_SESSION_CACHE_PREFIX = "onlyoffice.report_session"
EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def normalize_extension(value):
    return str(value or "").lower().lstrip(".")


def resolve_editor_language(request):
    lang = getattr(request, "LANGUAGE_CODE", "") or request.headers.get("Accept-Language", "")
    lang = str(lang or "").split(",")[0].split("-")[0].strip().lower()
    if lang in {"ru", "kk", "en"}:
        return lang

    user_lang = str(getattr(request.user, "language", "") or "").strip().lower()
    if user_lang in {"ru", "kk", "en"}:
        return user_lang

    return "ru"


def is_previewable_extension(value):
    return normalize_extension(value) in SUPPORTED_EXTENSIONS


def get_document_type(extension):
    normalized = normalize_extension(extension)
    if normalized in WORD_EXTENSIONS:
        return "word"
    if normalized in CELL_EXTENSIONS:
        return "cell"
    if normalized in SLIDE_EXTENSIONS:
        return "slide"
    if normalized in PDF_EXTENSIONS:
        return "pdf"
    raise exceptions.ValidationError({"detail": "unsupported_file_type"})


def ensure_onlyoffice_is_configured():
    if not settings.ONLYOFFICE_DOCUMENT_SERVER_PUBLIC_URL:
        raise exceptions.ValidationError({"detail": "onlyoffice_document_server_url_is_not_configured"})
    if not settings.ONLYOFFICE_JWT_SECRET:
        raise exceptions.ValidationError({"detail": "onlyoffice_jwt_secret_is_not_configured"})


def _build_public_url(path):
    base_url = (settings.ONLYOFFICE_STORAGE_PUBLIC_URL or settings.BACKEND_URL or "").rstrip("/")
    return f"{base_url}{path}"


def build_download_url(payload):
    token = signing.dumps(payload, salt=DOWNLOAD_SALT)
    return _build_public_url(f"{reverse('onlyoffice:download')}?token={quote(token)}")


def build_callback_url(payload):
    token = signing.dumps(payload, salt=CALLBACK_SALT)
    return _build_public_url(f"{reverse('onlyoffice:callback')}?token={quote(token)}")


def load_download_payload(token):
    return signing.loads(
        token,
        salt=DOWNLOAD_SALT,
        max_age=settings.ONLYOFFICE_DOWNLOAD_TOKEN_TTL,
    )


def load_callback_payload(token):
    return signing.loads(
        token,
        salt=CALLBACK_SALT,
        max_age=settings.ONLYOFFICE_CALLBACK_TOKEN_TTL,
    )


def build_document_key(file, scope_payload):
    version_bits = [
        str(file.pk),
        str(file.updated_at.timestamp() if getattr(file, "updated_at", None) else ""),
        str(file.size or ""),
        str(scope_payload.get("scope", "")),
        str(scope_payload.get("comment_id", "")),
        str(scope_payload.get("chat_uid", "")),
        str(scope_payload.get("message_uid", "")),
        str(scope_payload.get("session_id", "")),
    ]
    return hashlib.sha256("|".join(version_bits).encode("utf-8")).hexdigest()


def _get_report_session_ttl():
    default_ttl = max(int(getattr(settings, "ONLYOFFICE_DOWNLOAD_TOKEN_TTL", 900)), 3600)
    return int(getattr(settings, "ONLYOFFICE_REPORT_SESSION_TTL", default_ttl))


def _report_session_cache_key(session_id):
    return f"{REPORT_SESSION_CACHE_PREFIX}:{session_id}"


def _normalize_report_file_name(report_name):
    base_name = str(report_name or "").strip() or "Report"
    safe_name = base_name.replace("/", "_").replace("\\", "_")
    if safe_name.lower().endswith(".xlsx"):
        return safe_name
    return f"{safe_name}.xlsx"


def _resolve_report_model_class(model_name):
    normalized_name = str(model_name or "").strip().lower()
    if not normalized_name:
        return None

    report_model_paths = getattr(settings, "REPORTS_UNIVERSAL_MODELS", []) or []
    for model_path in report_model_paths:
        try:
            model_class = apps.get_model(model_path)
        except LookupError:
            continue

        if model_class.__name__.lower() == normalized_name:
            return model_class
    return None


def _normalize_report_payload(payload):
    if not isinstance(payload, dict):
        raise exceptions.ValidationError({"detail": "report_payload_must_be_object"})

    normalized_payload = dict(payload)
    normalized_payload["results"] = "xls"
    normalized_payload["html"] = False
    return normalized_payload


def create_report_session(user, model_name, report_payload):
    model_class = _resolve_report_model_class(model_name)
    if model_class is None:
        raise exceptions.ValidationError({"detail": "invalid_report_model_name"})

    normalized_payload = _normalize_report_payload(report_payload)
    session_id = uuid.uuid4().hex
    session_payload = {
        "user_id": str(user.pk),
        "model_name": model_class.__name__,
        "report_payload": normalized_payload,
        "file_name": _normalize_report_file_name(normalized_payload.get("report_name")),
    }

    cache.set(_report_session_cache_key(session_id), session_payload, timeout=_get_report_session_ttl())
    return {
        "session_id": session_id,
        "file_name": session_payload["file_name"],
    }


def _get_report_session(session_id):
    if not session_id:
        return None
    return cache.get(_report_session_cache_key(session_id))


def refresh_report_session(user, session_id):
    session_payload = _get_report_session(session_id)
    if not session_payload:
        raise exceptions.NotFound()

    if str(session_payload.get("user_id")) != str(user.pk):
        raise exceptions.PermissionDenied()

    model_class = _resolve_report_model_class(session_payload.get("model_name"))
    if model_class is None:
        raise exceptions.ValidationError({"detail": "invalid_report_model_name"})

    normalized_payload = _normalize_report_payload(session_payload.get("report_payload") or {})
    refreshed_session_id = uuid.uuid4().hex
    refreshed_payload = {
        "user_id": str(user.pk),
        "model_name": model_class.__name__,
        "report_payload": normalized_payload,
        "file_name": _normalize_report_file_name(normalized_payload.get("report_name")),
    }

    cache.set(_report_session_cache_key(refreshed_session_id), refreshed_payload, timeout=_get_report_session_ttl())
    return {
        "session_id": refreshed_session_id,
        "file_name": refreshed_payload["file_name"],
    }


def _build_comment_source_url(comment, file):
    if settings.DOWNLOADER_PATH is None:
        return file.absolute_url
    parent_path = quote(f"?obj={comment.pk}&id={file.pk}&target=attachments")
    return f"{settings.BACKEND_URL}{settings.DOWNLOADER_PATH}/?path={parent_path}"


def _build_chat_source_url(chat_uid, message_uid, file):
    if settings.DOWNLOADER_PATH is None:
        return file.absolute_url
    parent_path = quote(
        f"?chat_uid={chat_uid}&message_uid={message_uid}&id={file.pk}&target=chat_attachments"
    )
    return f"{settings.BACKEND_URL}{settings.DOWNLOADER_PATH}/?path={parent_path}"


def _has_comment_access(request, comment):
    related_object = comment.related_object
    if related_object is None:
        return False
    original_object = related_object.original_object
    queryset = CommentModel.objects.filter(pk=comment.pk, is_active=True)
    try:
        queryset = original_object.filter_comment_qs(request.user.profile, queryset)
    except AttributeError:
        try:
            return original_object.get_detail_permission(request)
        except AttributeError:
            return False

    return queryset.exists()


def resolve_scope_payload(request):
    scope = request.query_params.get("scope", "")
    if scope == "file":
        return _resolve_generic_file_scope(request)
    if scope == "comment_attachment":
        return _resolve_comment_attachment_scope(request)
    if scope == "chat_attachment":
        return _resolve_chat_attachment_scope(request)
    if scope == "report_session":
        return _resolve_report_session_scope(request)
    raise exceptions.ValidationError({"detail": "unsupported_scope"})


def _resolve_generic_file_scope(request):
    file_id = request.query_params.get("file_id")
    if not file_id:
        raise exceptions.ValidationError({"detail": "file_id_is_required"})
    try:
        file = File.objects.select_related("mime_type").get(pk=file_id, is_active=True)
    except (File.DoesNotExist, ObjectDoesNotExist):
        raise exceptions.NotFound()
    if not file.get_detail_permission(request):
        raise exceptions.PermissionDenied()
    return {
        "scope": "file",
        "file": file,
        "download_payload": {
            "scope": "file",
            "file_id": str(file.pk),
        },
        "callback_payload": {
            "scope": "file",
            "file_id": str(file.pk),
        },
        "source_url": file.author_url,
    }


def _resolve_comment_attachment_scope(request):
    comment_id = request.query_params.get("comment_id")
    file_id = request.query_params.get("file_id")
    if not comment_id or not file_id:
        raise exceptions.ValidationError({"detail": "comment_id_and_file_id_are_required"})
    try:
        comment = CommentModel.objects.select_related("related_object").get(pk=comment_id, is_active=True)
    except (CommentModel.DoesNotExist, ObjectDoesNotExist):
        raise exceptions.NotFound()
    if not _has_comment_access(request, comment):
        raise exceptions.PermissionDenied()
    try:
        file = comment.attachments.select_related("mime_type").get(pk=file_id, is_active=True)
    except (File.DoesNotExist, ObjectDoesNotExist):
        raise exceptions.NotFound()
    return {
        "scope": "comment_attachment",
        "file": file,
        "comment": comment,
        "download_payload": {
            "scope": "comment_attachment",
            "comment_id": str(comment.pk),
            "file_id": str(file.pk),
        },
        "callback_payload": {
            "scope": "comment_attachment",
            "comment_id": str(comment.pk),
            "file_id": str(file.pk),
        },
        "source_url": _build_comment_source_url(comment, file),
    }


def _resolve_chat_attachment_scope(request):
    if not check_chat_attachments(request):
        raise exceptions.NotFound('check_chat_attachments')
    chat_uid = request.query_params.get("chat_uid")
    message_uid = request.query_params.get("message_uid")
    file_id = request.query_params.get("file_id")

    if not chat_uid or not message_uid or not file_id:
        raise exceptions.ValidationError({"detail": "chat_uid_message_uid_and_file_id_are_required"})
    # try:
    #     chat = ChatModel.objects.get(chat_uid=chat_uid, is_active=True)
    # except (ChatModel.DoesNotExist, ObjectDoesNotExist):
    #     raise exceptions.NotFound()
    # try:
    #     message = chat.messages.get(message_uid=message_uid, is_active=True)
    # except ObjectDoesNotExist:
    #     raise exceptions.NotFound()
    # try:
    #     file = message.attachments.select_related("mime_type").get(pk=file_id, is_active=True)
    # except (File.DoesNotExist, ObjectDoesNotExist):
    #     raise exceptions.NotFound()
    try:
        file = File.objects.get(pk=file_id)
    except (ValidationError, ObjectDoesNotExist):
        raise exceptions.NotFound('file not found')
    return {
        "scope": "chat_attachment",
        "file": file,
        # "chat": chat,
        # "message": message,
        "download_payload": {
            "scope": "chat_attachment",
            # "chat_uid": str(chat.chat_uid),
            # "message_uid": str(message.message_uid),
            "chat_uid": chat_uid,
            "message_uid": message_uid,
            "file_id": str(file.pk),
        },
        "callback_payload": {
            "scope": "chat_attachment",
            # "chat_uid": str(chat.chat_uid),
            # "message_uid": str(message.message_uid),
            "chat_uid": chat_uid,
            "message_uid": message_uid,
            "file_id": str(file.pk),
        },
        # "source_url": _build_chat_source_url(message, file),
        "source_url": _build_chat_source_url(chat_uid, message_uid, file),
    }


def _resolve_report_session_scope(request):
    session_id = request.query_params.get("session_id")
    if not session_id:
        raise exceptions.ValidationError({"detail": "session_id_is_required"})

    session_payload = _get_report_session(session_id)
    if not session_payload:
        raise exceptions.NotFound()

    if str(session_payload.get("user_id")) != str(request.user.pk):
        raise exceptions.PermissionDenied()

    file_name = _normalize_report_file_name(session_payload.get("file_name"))
    virtual_file = type(
        "OnlyofficeReportVirtualFile",
        (object,),
        {
            "pk": f"report-session:{session_id}",
            "updated_at": None,
            "size": 0,
            "extension": "xlsx",
            "full_name": file_name,
            "mime_type_id": EXCEL_CONTENT_TYPE,
        },
    )()

    return {
        "scope": "report_session",
        "file": virtual_file,
        "download_payload": {
            "scope": "report_session",
            "session_id": session_id,
        },
        "callback_payload": {
            "scope": "report_session",
            "session_id": session_id,
        },
        "source_url": "",
    }


def resolve_download_file(payload):
    scope = payload.get("scope")
    file_id = payload.get("file_id")
    if scope == "file":
        return File.objects.select_related("mime_type").get(pk=file_id, is_active=True)
    if scope == "comment_attachment":
        comment_id = payload.get("comment_id")
        comment = CommentModel.objects.get(pk=comment_id, is_active=True)
        return comment.attachments.select_related("mime_type").get(pk=file_id, is_active=True)
    if scope == "chat_attachment":
        chat_uid = payload.get("chat_uid")
        message_uid = payload.get("message_uid")
        chat = ChatModel.objects.get(chat_uid=chat_uid, is_active=True)
        message = chat.messages.get(message_uid=message_uid, is_active=True)
        return message.attachments.select_related("mime_type").get(pk=file_id, is_active=True)
    raise File.DoesNotExist()


def _resolve_report_session_download_stream(payload):
    session_id = payload.get("session_id")
    session_payload = _get_report_session(session_id)
    if not session_payload:
        raise File.DoesNotExist()

    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(pk=session_payload.get("user_id"), is_active=True)
    except UserModel.DoesNotExist:
        raise File.DoesNotExist()

    model_class = _resolve_report_model_class(session_payload.get("model_name"))
    if model_class is None:
        raise File.DoesNotExist()

    report_payload = _normalize_report_payload(session_payload.get("report_payload") or {})
    basename = f"{model_class._meta.app_label}__{model_class.__name__}"
    model_url_part = model_class.__name__.lower()

    internal_request = APIRequestFactory().post(
        f"/api/v1/reports/{model_url_part}/list_post/",
        report_payload,
        format="json",
    )
    force_authenticate(internal_request, user=user)

    from reports.views import UniversalModelViewSet

    internal_view = UniversalModelViewSet.as_view({"post": "list_post"}, basename=basename)
    response = internal_view(internal_request)

    if hasattr(response, "render") and callable(response.render):
        response.render()

    response_status = int(getattr(response, "status_code", 200))
    if response_status >= 400:
        logger.warning("ONLYOFFICE report session download failed: status=%s", response_status)
        raise File.DoesNotExist()

    content = getattr(response, "content", b"")
    if not content:
        raise File.DoesNotExist()

    return {
        "file_obj": io.BytesIO(content),
        "file_name": _normalize_report_file_name(session_payload.get("file_name")),
        "content_type": response.get("Content-Type", EXCEL_CONTENT_TYPE),
    }


def resolve_download_stream(payload):
    scope = payload.get("scope")
    if scope == "report_session":
        return _resolve_report_session_download_stream(payload)

    file = resolve_download_file(payload)
    return {
        "file_obj": file.upload.open("rb"),
        "file_name": file.full_name,
        "content_type": file.mime_type_id or "application/octet-stream",
    }


def build_editor_payload(request, resolved_scope):
    ensure_onlyoffice_is_configured()
    file = resolved_scope["file"]
    extension = normalize_extension(file.extension)
    if not is_previewable_extension(extension):
        raise exceptions.ValidationError({"detail": "unsupported_file_type"})

    document_url = build_download_url(resolved_scope["download_payload"])
    callback_url = build_callback_url(resolved_scope["callback_payload"])
    config = {
        "documentType": get_document_type(extension),
        "type": "desktop",
        "document": {
            "title": file.full_name,
            "url": document_url,
            "fileType": extension,
            "key": build_document_key(file, resolved_scope["download_payload"]),
            "permissions": {
                "edit": False,
                "download": True,
                "print": True,
                "copy": True,
                "comment": False,
            },
        },
        "editorConfig": {
            "mode": "view",
            "lang": resolve_editor_language(request),
            "callbackUrl": callback_url,
            "user": {
                "id": str(request.user.pk),
                "name": request.user.get_full_name() or request.user.username or request.user.email or "User",
            },
            "customization": {
                "compactHeader": True,
                "toolbarHideFileName": False,
            },
        },
    }
    token = jwt.encode(config, settings.ONLYOFFICE_JWT_SECRET, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    config["token"] = token
    return {
        "document_server_url": settings.ONLYOFFICE_DOCUMENT_SERVER_PUBLIC_URL.rstrip("/"),
        "config": config,
        "file_name": file.full_name,
        "download_url": document_url,
    }
