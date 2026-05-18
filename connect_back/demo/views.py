from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .utils import create_demo_data, delete_demo_data


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_demo_data_view(request):
    """
    Эндпойнт для создания демо-данных для текущего пользователя.
    
    POST /demo/create/
    """
    try:
        profile_id = request.user.profile.id
        result = create_demo_data(profile_id)
        
        return Response({
            'success': True,
            'message': 'Демо-данные успешно созданы',
            'data': {
                'users': len(result.get('users', {})),
                'workgroups': len(result.get('workgroups', {})),
                'sprints': len(result.get('sprints', {})),
                'tasks': len(result.get('tasks', {})),
                'execution_times': len(result.get('execution_times', {})),
                'calendars': len(result.get('calendars', {})),
                'calendar_events': len(result.get('calendar_events', {})),
                'objectives': len(result.get('objectives', {})),
                'key_results': len(result.get('key_results', {})),
            }
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Ошибка при создании демо-данных: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_demo_data_view(request):
    """
    Эндпойнт для удаления всех демо-данных.
    
    POST /demo/delete/
    """
    try:
        profile_id = request.user.profile.id
        result = delete_demo_data(profile_id)
        
        return Response({
            'success': True,
            'message': 'Демо-данные успешно удалены',
            'data': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Ошибка при удалении демо-данных: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
