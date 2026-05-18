import redis
from bkz3 import settings

# Подключение к Redis для работы с SocketIO-сервером
socketio_redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                             db=settings.SESSION_REDIS.get('db'), decode_responses=True)
