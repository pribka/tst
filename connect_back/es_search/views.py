# search/views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.apps import apps

from .utils import universal_search

class SearchPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

@api_view(["GET"])
@authentication_classes([SessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def universal_search_view(request):
    model = request.GET.get("model", "")
    search = request.GET.get("search", "")

    result = universal_search(
        model=model,
        search=search,
    )
    
    if "error" in result:
        return Response(result, status=400)
    
    app_label, model_name = model.split('.')
    model_class = apps.get_model(app_label, model_name)
    serializer_class = model_class.get_serializer_class(action='search')
    
    # Извлекаем ID из результатов поиска (теперь это список словарей)
    if result:
        object_ids = [item['id'] for item in result]
        objects = model_class.objects.filter(pk__in=object_ids)
        # Сортируем объекты в том же порядке, что и ID из поиска
        id_order = {item['id']: i for i, item in enumerate(result)}
        objects = sorted(objects, key=lambda obj: id_order.get(str(obj.pk), 0))
    else:
        objects = model_class.objects.none()
    
    paginator = SearchPagination()
    paginated_objects = paginator.paginate_queryset(objects, request)
    serialized_data = serializer_class(paginated_objects, many=True, context={'request': request}).data
    return paginator.get_paginated_response(serialized_data)
