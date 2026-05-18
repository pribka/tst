from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.db.models import Avg

from django_q.tasks import async_task

from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import BaseModel

from . import models, serializers
from .utils import update_vote_cache_for_instance


class VoteView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_rated_object(self, request, *args, **kwargs):
        # Получаем ID оцениваемого объекта
        obj_pk = self.kwargs.get('pk')
        if obj_pk is None:
            raise drf_exceptions.ValidationError('Неверный ID')

        # Пробуем получить сам объект оценки
        try:
            obj = BaseModel.objects.super_get(obj_pk)
        except Exception:
            raise drf_exceptions.ValidationError(
                'Не удалось получить объект оценки')

        # Проверяем права пользователя на доступ к объекту
        if not obj.get_detail_permission(request):
            raise drf_exceptions.ValidationError(
                'Не достаточно прав для этой операции')

        return obj

    def get(self, request, *args, **kwargs):

        # Получаем объект оценки
        obj = self.get_rated_object(request)

        # Запрашиваем и оценки для объекта
        result = update_vote_cache_for_instance(obj)

        # Запрашиваем и возвращаем предыдущую оценку пользователя для объекта
        vote_obj = models.UserVotesModel.objects.filter(
                author=request.user.profile,
                related_object=obj).first()

        result['my_vote'] = vote_obj.vote if vote_obj else None
        return Response(result,
                        status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        # Получаем объект оценки
        obj = self.get_rated_object(request)

        # Получаем поставленную оценку из запроса
        # Она должна быть True или False
        vote = request.data.get('vote')
        if vote is None or not isinstance(vote, bool):
            raise drf_exceptions.ValidationError('Неправильная оценка')

        # Запрашиваем предыдущую оценку пользователя для объекта
        vote_obj = models.UserVotesModel.objects.filter(
                author=request.user.profile,
                related_object=obj).first()

        # Если её ещё нет, создаем и обновляем данные об оценках в кэше
        if not vote_obj:
            vote_obj = models.UserVotesModel.objects.create(
                related_object=obj,
                vote=vote
            )
            async_task(update_vote_cache_for_instance, obj)
            return Response({'vote': vote_obj.vote},
                            status=status.HTTP_201_CREATED)

        # Если оценка существует, проверяем совпадает ли новая оценка со старой
        # Если совпадает, удаляем оценку из БД (отменяем предыдущую оценку)
        # Если не совпадает, изменяем оценку на новую и обновляем кэш
        if vote_obj.vote == vote:
            vote_obj.delete()
            async_task(update_vote_cache_for_instance, obj)
            return Response({'vote': None},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            vote_obj.vote = vote
            vote_obj.save()
            async_task(update_vote_cache_for_instance, obj)
            return Response({'vote': vote},
                            status=status.HTTP_200_OK)


class UserRatingView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        data = request.data
        related_object_id = data.get('related_object')
        if not related_object_id:
            raise drf_exceptions.ValidationError('related object required')
        try:
            related_object = BaseModel.objects.super_get(pk=related_object_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('related object not found')
        if not hasattr(related_object, 'update_rating_permission'):
            raise drf_exceptions.ValidationError('Объект нельзя оценить')
        if not related_object.update_rating_permission(request):
            raise drf_exceptions.PermissionDenied()
        user = request.user.profile
        data = request.data
        context = {'request': request, 'view': self}
        with transaction.atomic():
            try:
                user_rating = models.UserRatingModel.objects.get(author=user, related_object_id=related_object.pk)
            except ObjectDoesNotExist:
                serializer = serializers.RatingWriteSerializer(
                    data=data,
                    context=context,
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            else:
                serializer = serializers.RatingWriteSerializer(
                    instance=user_rating,
                    data=data,
                    context=context,
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return Response('ok')

    def get(self, request, *args, **kwargs):
        related_object_id = request.query_params.get('related_object')
        if not related_object_id:
            raise drf_exceptions.ValidationError('related object required')
        try:
            related_object = BaseModel.objects.super_get(pk=related_object_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('related object not found')
        if not related_object.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        instance = models.UserRatingModel.objects.filter(related_object=related_object).order_by('-created_at',).first()
        if not instance:
            return Response()
        else:
            serializer = serializers.RatingReadSerializer(instance, context={'request': request, 'view': self})
        return Response(serializer.data)
