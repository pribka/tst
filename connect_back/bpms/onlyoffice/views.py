import logging

from django.http import FileResponse
from django.utils.cache import patch_cache_control
from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import utils

logger = logging.getLogger(__name__)


class OnlyofficeConfigView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        resolved_scope = utils.resolve_scope_payload(request)
        return Response(utils.build_editor_payload(request, resolved_scope))


class OnlyofficeReportSessionView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        model_name = request.data.get("model_name") or request.data.get("model")
        report_payload = request.data.get("report_payload") or request.data.get("payload")

        session_info = utils.create_report_session(
            user=request.user,
            model_name=model_name,
            report_payload=report_payload,
        )
        return Response(session_info)


class OnlyofficeReportSessionRefreshView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        session_id = request.data.get("session_id")
        if not session_id:
            raise exceptions.ValidationError({"detail": "session_id_is_required"})

        session_info = utils.refresh_report_session(
            user=request.user,
            session_id=session_id,
        )
        return Response(session_info)


class OnlyofficeDownloadView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        token = request.query_params.get("token", "")
        if not token:
            raise exceptions.NotFound()
        try:
            payload = utils.load_download_payload(token)
            stream_payload = utils.resolve_download_stream(payload)
        except Exception as exc:
            logger.warning("ONLYOFFICE download rejected: %s", exc)
            raise exceptions.NotFound()

        response = FileResponse(
            stream_payload["file_obj"],
            as_attachment=False,
            filename=stream_payload["file_name"],
            content_type=stream_payload["content_type"] or "application/octet-stream",
        )
        patch_cache_control(response, private=True, no_cache=True, no_store=True, must_revalidate=True)
        return response


class OnlyofficeCallbackView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        token = request.query_params.get("token", "")
        if not token:
            return Response({"error": 1}, status=400)
        try:
            payload = utils.load_callback_payload(token)
        except Exception as exc:
            logger.warning("ONLYOFFICE callback rejected: %s", exc)
            return Response({"error": 1}, status=403)

        logger.info(
            "ONLYOFFICE callback received",
            extra={
                "onlyoffice_scope": payload.get("scope"),
                "onlyoffice_status": request.data.get("status"),
                "onlyoffice_key": request.data.get("key"),
            },
        )
        return Response({"error": 0})
