from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common import models as common_models
from common import utils as common_utils

from . import serializers, utils, models


def get_pvh(request):
    if request.method == 'GET':
        model_name = request.query_params.get('model')
    else:
        model_name = request.data.get('model')
    if not model_name:
        return None
    app_label, model = model_name.lower().split('.')
    content_type = ContentType.objects.get_by_natural_key(app_label, model)
    try:
        pvh = models.PVH.objects.get(is_active=True, content_type=content_type)
    except models.PVH.DoesNotExist:
        return None
    return pvh


class AttrNamesView(APIView):
    def get(self, request, *args, **kwargs):
        pvh = get_pvh(request)
        if pvh:
            return Response(data=pvh.attr_names)
        else:
            return Response()


class PropertyListViewSet(APIView):
    def post(self, request, *args, **kwargs):
        pvh = get_pvh(request)
        condition = request.data.get('condition')
        properties_through = utils.get_pvh_property_through_for_pvh(pvh, condition)
        serializer = serializers.PVHPropertyThroughSerializer(
            properties_through, many=True, context={'view': self, 'request': request}
        )
        data = serializer.data
        return Response(data)


class PlanOfCharacteristicViewSet(ModelViewSet):
    model = common_models.BaseModel
    permission_classes = (IsAuthenticated,)
    def get_serializer_class(self, *args, **kwargs):
        return serializers.PVHSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            obj = self.model.objects.super_get(pk=pk)
        except self.model.DoesNotExist:
            raise NotFound()
        return obj

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = utils.get_pvh_data(instance)
        return Response(data)

    @action(methods=['get'], detail=False, url_path='form_info')
    def get_characteristic(self, request, *args, **kwargs):
        model = common_utils.get_model(request)
        # query_params = request.query_params.dict() TODO фильтрация по атрибутам модели
        # query_params.pop('model', None)
        # characteristics, independent_fields = model.get_model_characteristics_fields(**query_params)
        characteristics, independent_fields = model.get_model_characteristics_fields()

        blocks_choices = common_models.PlanOfCharacteristicBlock.objects.filter(
            characteristics__in=(*characteristics, *independent_fields)
        ).distinct().order_by('sort').values_list('code', 'name')
        blocks = []
        for choice_code, choice_name in blocks_choices:
            block_characteristic = characteristics.filter(block=choice_code).order_by('sort')
            independent_fields_blocks = independent_fields.filter(block=choice_code).order_by('sort')
            editable_part = {
                "name": f"{choice_code}_BLOCK",
                "title": str(choice_name),
                "block_code": str(choice_code),
                "type_for_front": 'form',
                "fields": block_characteristic,
                "independent_fields": independent_fields_blocks,
                "filterInfo": ""
            }
            if block_characteristic.__len__() > 0 or independent_fields_blocks.__len__() > 0:
                blocks.append(editable_part)
        poc_data = serializers.PlanOfCharacteristicBlockSerializer(blocks, many=True).data
        result = {
            #  Пустышки для фронтенда
            "actions": {
                "create": {
                    "path": "/pvh/<id>/"
                },
                "update": {
                    "path": "/pvh/<id>/"
                },
                "retrieve": {
                    "path": "/pvh/<id>/"
                }
            },
            "pageConfig": {
                "headerButtons": []
            },
            "fieldInfo": [
                {
                    "class": "",
                    "name": "name",
                    "title": "Имя",
                    "fieldName": "",
                    "type": "string",
                    "update": False,
                    "rulesConfig": [],
                    "widgetConfig":{
                        "disabled": True,
                        "placeholder": "",
                        "size": "default",
                        "widget": "WidgetString"
                    },
                    "defaultValue": ""
                },
            ],
            "fields": {
                "create": [
                    "name"
                ],
                "update": [
                    "name"
                ],
            },
            # end пустышки для фронтенда

            "title": "Каталогизация",
            "type": "form",
            "pageWidget": "TableForm",
            "navWidget": "NavForm",
            "name": model.get_label() + '_parts',
            "editablePart": poc_data,
        }
        return Response(result, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        utils.set_characteristics_values(request.data, instance)
        data = utils.get_pvh_data(instance)
        return Response(data)
