from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .cron import send_tariff_ending_notifications, send_tariff_started_notifications


# Create your views here.

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_tariff_ending_notifications_view(request):
    """
    Запуск отправки уведомлений об окончании срока действия тарифа.
    Доступен только администраторам.
    """
    # Проверяем, что пользователь является администратором
    if not request.user.is_superuser:
        return Response(
            {'error': 'Доступ разрешен только администраторам'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Получаем параметр лимита из запроса (по умолчанию 100)
        instance_count = request.data.get('instance_count', 100)
        
        # Запускаем отправку уведомлений
        tasks_count = send_tariff_ending_notifications(instance_count)
        
        return Response({
            'success': True,
            'message': f'Запущено задач отправки уведомлений: {tasks_count}'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Ошибка при отправке уведомлений: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_tariff_started_notifications_view(request):
    """
    Запуск отправки уведомлений о начале тарифа.
    Доступен только администраторам.
    """
    # Проверяем, что пользователь является администратором
    if not request.user.is_superuser:
        return Response(
            {'error': 'Доступ разрешен только администраторам'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Получаем параметр лимита из запроса (по умолчанию 100)
        instance_count = request.data.get('instance_count', 100)
        
        # Запускаем отправку уведомлений
        tasks_count = send_tariff_started_notifications(instance_count)
        
        return Response({
            'success': True,
            'message': f'Запущено задач отправки уведомлений о начале тарифа: {tasks_count}',
            'tasks_count': tasks_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Ошибка при отправке уведомлений: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
