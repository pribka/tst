import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '__redacted_invalid__'
DID_SALT = '6tpR2jbCv\vy%#1%m:P2)t$?$Qp\i!q-'

DEBUG = False
DEBUG = True
INVITE_REGISTER_ONLY = False
USE_ACCESS_GROUPS = True

DRF_RECAPTCHA_TESTING = True
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        # 'ENGINE': 'django.db.backends.__redacted_invalid__ql_psycopg2',
        # 'NAME': 'bkz3_bolevoi2',
        # 'NAME': 'bkz3_3',
        'NAME': 'bkz_start',
        'USER': '__redacted_invalid__',
        'PASSWORD': '__redacted_invalid__',
        'HOST': '__redacted_invalid__-13.5',
        'PORT': '5432',
    }
}


CSRF_TRUSTED_ORIGINS = [
    '__redacted_invalid__', 'localhost'    ,  'localhost:8000',    'd.centersoft.kz:8080'    ,     'd.centersoft.kz:8000'    ,
    'auth.connect.gos24.kz'
]

ALLOWED_HOSTS = [                'd.centersoft.kz'    ,   'localhost'    ,   'localhost:8000', 'mbpms.gos24.kz', 'bpms.gos24.kz', 'connect.gos24.kz', 'efsol.delocloud.ru']
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_URL = '/static/'
STATICFILES_DIRS = ['/app/static_admin']

REDIS_HOST = '__redacted_invalid__'
REDIS_PORT = '__redacted_invalid__'

CACHES = {
    'default': {
        "BACKEND": "django_redis.cache.RedisCache",
        'LOCATION': 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/4',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

BACKEND_URL = 'https://connect.gos24.kz'

FRONTEND_URL = 'https://connect.gos24.kz'

VOICE_INPUT_RECOGNIZE_URL = 'http://178.91.130.245:5080/recognize'

FIREBASE_SERVICE_ACCOUNT_INFO = {
    'type': 'service_account',
    'project_id': 'connectgos24',
    'private_key_id': '__redacted_invalid__',
    'private_key': """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC2bK4twT9TSI4/
zCgtzEFx2R+WYP3wjxfac8t9j68Z1GH/a1YD3ABSOa/pcAlcwaIOpbdTXt9JlJAg
V++OlfaXy7Opkq5LWNhnNsO3Yi57ifXBwPummPhspv/TPE6aqWO1ejhAqla6/DTr
vxkbU6co+rN9JV0PMBW4ordNf2wOwSY0hTIqctWed57v31Fnv0C8UbTTZ2rpfyQN
uyEif0jhpOrKUAucBx+C7egeti40PwWpr/3UnPSO/7uPiXQ+gO4pM4niMCz1/82J
wQ47SKpbk5V1wLblZ+4xk+t8QI69aBnMxHVMcGF5CD7cYE3ohZyyuPzBkM/OrP1Q
uIjnjq+/AgMBAAECggEAFxisdtOMOnWpuO8WuTGuqYTlaGswS4g6a2iUv3l1IG6Q
179VvRhaHA78tDAAp3NGmtclXlNZLt413zpy9JkNBwv9277b/WMqxuqanfm6y95c
NKND2URt04fTRQHSK+e9XYkzXRCT+YmcA6sGuTx+ogQXvIUCAr3CSkWjspaq7jUU
a2/lN/DwWITUSnFv+eWDyWiZ4mPTVX5XBiw9jPHthByTj/6TDDPv51K34i9HFHmf
1+9UOvYOHuo36jhfKm30awNrVE87KNy2F1ZXO236Vf4aaNQAm+4MFQ9AyMPKUoou
QYublvHlW7Tjv7lGuHxBE7hItAIkZ7A+kttrafp7LQKBgQDe0XJO0ltBB8Kom3mL
z4ctTTxK7v6FiHSzhBs0tauTgp+NOGLC12OP6E6olWXpWaCokMOnPVcxullbsw+0
yNURrFmXG70bH5UuyHh6QoRzhxSw8K3ey8lxNPBcTpFfQowTYMKzkHx9/YhTpPNU
0ucF419DHuJKSmIJhjNwbdFGRQKBgQDRl0wxLM0MBUr5SHs7fN5R4dAQMDlEnIT0
eoeS6nG8rppBTopal6f8Kp+E/R0zGxwb+yEvC1TYcaIbSwb6v8qIlbk/1o1+9efW
TcH/HV3eISqbL2YCaqYX0VOrzyZCNnWCCqPaPrjfn2eP36ob+ILCEPKSVejd2mnT
5tfFu1nwMwKBgQDF8PLHKwB+KNK4zkWP+nBvwilJuD7LiYmC4Fz62ljt1iC/Z9P0
mzuLYChggzfhsQmUNeZZ75hCSPWRDOVrCO6foKiGINJCAjCZOuYsVmMr7lhnR6hu
QENYGltc5T8njQq7PD47HqQ5mL0+8U5pkGJDTNYX3pvQu3uUUm/n9ObwsQKBgQCZ
o0fl8Epq2mJoNBqps9IgweBMTZ1dT0MjF8LUDmnLf05yOwmueOdaMUB4Mzc5ZFEJ
reBYZP0QINRNH4WBQCBOWTrPsg5NGCOXc66WvUc28qcR1P/5G4afhQHJuvL3rIYd
CoGsFTheLLK0w6cmE9h+PAAlBzbJkjbrb5eSSdEXAwKBgAvoiDfVTGsVcbrtJmi2
x3bfhzgT7wQuJHH3ZqIqDW0qaQ1XMXOeNXblZEHdZ4kwjGiJvq5Js58e9Ki8Fh7d
pHH9oAcdlb5ixZ8ygWOWfySozmiA1uT1LeYEbp6zej2UWDnGwXcQkEKiVkq30whX
tMx2R8E1fyzCbdetPpDRWZgZ
-----END PRIVATE KEY-----
""",
    'client_email': 'firebase-adminsdk-fbsvc@connectgos24.iam.gserviceaccount.com',
    'client_id': '101891802225262082763',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': '__redacted_invalid__',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40connectgos24.iam.gserviceaccount.com',
    'universe_domain': 'googleapis.com',
}

SESSION_REDIS = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': 0,
    'prefix': 'session',
    'socket_timeout': 1
}
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_PREFIX = '__redacted_invalid__'
SESSION_COOKIE_HTTPONLY = False
result_backend = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/5'
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine',
        'INCLUDE_SPELLING': True,

        'URL': 'http://invalid-redacted.local',
        'HAYSTACK_DEFAULT_OPERATOR': 'OR',
        'TIMEOUT': 60 * 5,
        'INDEX_NAME': "connect24"
    },
}
# HAYSTACK_SIGNAL_PROCESSOR = 'celery_haystack.signals.CelerySignalProcessor'
HAYSTACK_SIGNAL_PROCESSOR = 'common.djangoq_haystack.signal_processor.DjangoQSignalProcessor'

IMPORT_DATA_TOKEN = '__redacted_invalid__'

DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000000000
DATA_UPLOAD_MAX_MEMORY_SIZE = 100000000000
TOKEN_URV = '__redacted_invalid__'

# email:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'bmx.cskz.kz'
# EMAIL_HOST_USER = 'noreply@gos24mailer.kz'
# EMAIL_HOST_PASSWORD = 'GP2Jg@%3K6v7vxfe'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False
# DEFAULT_FROM_EMAIL = 'noreply@gos24mailer.kz'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'connect.smtp.bz'
EMAIL_HOST_USER = 'noreply@gos24.kz'
EMAIL_HOST_PASSWORD = '__redacted_invalid__'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'Платформа Gos24.KZ-Коннект <noreply@gos24.kz>'

GLOBAL_FRONT_SETTINGS = {

    'tg_bot_settings': {'url': 'https://t.me/delocloud_bot/'},

    "locale": {  # Язык
        "default_lang": "ru",
        "lang_list": [
            'ru',
            'en',
            'kk',
        ],
        "fallback_lang": "en",
        "injectTranslate": [
            "vue2TaskComponent",
            "Profiler",
            "Upload",
            "vue2GroupsAndProjectsComponent",
            "vue2ChatComponent",
        ]
    },
    "injectInit": [
        "vue2GroupsAndProjectsComponent",
        "vue2TaskComponent",
        "Team", "vue2ChatComponent",
        "vue2MeetingComponent",
        "BusinessProcesses",
        'vue2CommentsComponent',
        "Notifications",
        "Dashboard",
        "vue2Files"
    ],
    "upload_config": {  # Загрузка файлов
        "max_file_size": 10,
    },
    "widgets": {  # Тут будут мелкие конфиги
        "show": True,
    },
    "table_setting": {
        "theme": "ag-theme-alpine",
    },
    "aside_setting": {
        "active": True,
        "theme": "FlatAside",
        "grouping": True,
        "width": 250,
    },
    "header_setting": {
        "history": False,
        "favorite": False,
        "notification": True,
        "settingNav": True,
        "i18n": False,
        "search": True,
        "widgets": True,
        "product_cart": False,
        "logo": "https://connect.gos24.kz/media/avatars/logo_connect.svg",
        "logo_mini": f"{BACKEND_URL}/media/mini_logo.svg"
    },

    "site_setting": {
        "site_name": "Центрсофт",
        "pwa": True,

        "ui_key": "ORg4AjUWIQA/Gnt2VVhjQlFaclhJXGFWfVJpTGpQdk5xdV9DaVZUTWY/P1ZhSXxRd0VgWH9ccXBQQmdaUU0=",
        "icon_16": f"{BACKEND_URL}/media/icon-16x16.png",
        "icon_32": f"{BACKEND_URL}/media/icon-32x32.png",
        "icon_96": f"{BACKEND_URL}/media/icon-96x96.png",
        "icon_192": f"{BACKEND_URL}/media/icon-192x192.png",
        "icon_512": f"{BACKEND_URL}/media/icon-512x512.png",
        "icon_mask_192": f"{BACKEND_URL}/media/icon-mask-192x192.png",
        "icon_mask_512": f"{BACKEND_URL}/media/icon-mask-512x512.png",
    },

    "footer_setting": {
        "active": True,
    },

    'dashboard_settings': {'items': ['team', 'news', 'created_task']},

    "front_page": "dashboard",
    "sounds": {
        "new_message": f"{BACKEND_URL}/media/new_message.mp3",
        "new_notify": f"{BACKEND_URL}/media/new_notify.mp3",
    },
    "main_settings": {
        "VUE_APP_SENTRY_DSN": "__redacted_invalid__",
        "VUE_APP_SENTRY_AUTH_TOKEN": "__redacted_invalid__",
        "VUE_APP_SENTRY_URL": "__redacted_invalid__",
        "VUE_APP_SENTRY_ORG": "__redacted_invalid__",
        "VUE_APP_SENTRY_PROJECT": "__redacted_invalid__",
        "VUE_APP_TAGMANAGER_ID": "GTM-NQMQZWV",
    },
    "files_setting": {
        "available_views": [
            {
                "name": 'list',
                "icon": 'fi-rr-list'
            },
            {
                "name": 'grid',
                "icon": 'fi-rr-apps'
            }
        ],
        "default_view": "list",
    }
}
DEFAULT_CURRENCY_CODE = '398'
TIME_ZONE = 'Asia/Aqtau'
IMPORT_1C_DATA_TOKEN = '__redacted_invalid__'
EXPORT_1C_DATA_URL = ''
EXPORT_1C_DATA_TOKEN = '__redacted_invalid__'
PRIVATE_OFFICE = ({
                      'name': "Персональная информация",
                      'path': "personal",
                      'icon': "fi-rr-id-badge",
                      'widget': 'Personal'
                  },
                  {
                      'name': "Сменить пароль",
                      'path': "change-password",
                      'icon': "fi-rr-lock",
                      'widget': 'Password'
                  },
                  {
                      'name': "Интерфейс",
                      'path': "interface",
                      'icon': "fi-rr-settings-sliders",
                      'widget': 'Interface'
                  },)

LOCAL_REMNANT_CONTROL = True
AXES_ENABLED = False

Q_CLUSTER = {
    'retry': 180,
    'timeout': 120,
    'workers': 12,
    'name': 'bkz',
    'django_redis': '__redacted_invalid__',
}
MOBILE_GLOBAL_FRONT_SETTINGS = {
    "locale": {
        "default_lang": "ru",
        "lang_list": [
            'ru',
            'en',
            'kk',
        ],
        "fallback_lang": "en",
        "injectTranslate": [
            "vue2TaskComponent",
            "Profiler",
            "Upload",
            "vue2GroupsAndProjectsComponent",
            "vue2ChatComponent",
        ]
    },
    "injectInit": [
        'Team', "vue2TaskComponent",
        "Notifications",
        "vue2GroupsAndProjectsComponent",
        "vue2ChatComponent",
        "vue2MeetingComponent",

        'vue2CommentsComponent',
        "Products",
        "Orders",
    ],
    "upload_config": {
        "max_file_size": 10,
    },
    "widgets": {
        "show": True,
    },
    "table_setting": {
        "theme": "ag-theme-alpine",
    },
    "aside_setting": {
        "active": True,
        "theme": "FlatAside",
        "grouping": True,
        "width": 250,
    },
    "header_setting": {
        "history": False,
        "favorite": False,
        "notification": True,
        "settingNav": True,
        "i18n": False,
        "search": True,
        "widgets": True,
        "product_cart": False,
        "logo": "https://connect.gos24.kz/media/avatars/logo_connect.svg",
        "logo_mini": f"{BACKEND_URL}/media/mini_logo.svg"
    },
    "footer_setting": {
        "active": True,
    },
    "order_setting": {
        "check_stock": False,
        "cartMinusDelete": False,
        "remnant_control": False,
    },
    "front_page": "tasks",
    "sounds": {
        "new_message": f"{BACKEND_URL}/media/new_message.mp3",
        "new_notify": f"{BACKEND_URL}/media/new_notify.mp3",
    }
}

SOCKETIO_SYSTEM_CHANNEL = 'system'
DOWNLOADER_PATH = None
TG_BOT_TOKEN = '__redacted_invalid__'
TG_BOT_NAME = 'delocloudmesmelo_bot'
MOBILE_FRONT_CATEGORIES = {
    'tasks': {'show_footer_menu': True},
    'sprints': {'show_footer_menu': False},
    'chat': {'show_footer_menu': True},
    'meetings': {'show_footer_menu': True},
    'groups': {'show_footer_menu': True},
    'projects': {'show_footer_menu': False},
    'calendar': {'show_footer_menu': True},
    "team": {"show_footer_menu": False},
    "interest": {"show_footer_menu": False},
    "files": {"show_footer_menu": False}
}

FRONT_CATEGORIES = {'dashboard': (),
                    'communication': ('meetings', 'chat', 'tasks', 'groups', 'projects', 'files', 'calendar', 'team'),
                    'crm': ('interest',)}

CORS_ALLOWED_ORIGINS = ['https://bpms.gos24.kz', 'https://mbpms.gos24.kz', 'https://connect.gos24.kz']
SHOW_CONTRACT_IN_GOODS_ORDER = False
SHOW_PAY_TYPE_IN_GOODS_ORDER = False
GET_PROJECTS_AND_GROUPS_FROM_OTHER_BASE = False

TOKEN_FOR_IMPORT_PROJECTS = '__redacted_invalid__'
DOWNLOADER_PATH = '/download_file'

FILTER_BY_ORGANIZATIONS = True

INITIAL_ORGANIZATION = '3a6c8612-87fa-11ec-9552-0242ac110006'
INVITE_REGISTER_ONLY = False
COMPANY_NAME = 'GOS24.CONNECT'
SHORT_COMPANY_NAME = 'GOS24.CONNECT'
TARIFFS_URL = "https://gos24.kz/tariffplans"
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.__redacted_invalid__ql_psycopg2',
        'NAME': 'bpms',
        'USER': '__redacted_invalid__',
        'PASSWORD': '__redacted_invalid__',
        'HOST': '__redacted_invalid__',
        'PORT': '5433',
    }
}

INITIAL_ORGANIZATION = '3a6c8612-87fa-11ec-9552-0242ac110006'
import os
import osgeo
from pathlib import Path

osgeo_path = Path(osgeo.__file__).parent

GDAL_LIBRARY_PATH = str(osgeo_path / "gdal.dll")
GEOS_LIBRARY_PATH = str(osgeo_path / "geos_c.dll")  # она там тоже есть, обычно

# Эти переменные на всякий случай
os.environ.setdefault("GDAL_DATA", str(osgeo_path / "data" / "gdal"))
os.environ.setdefault("PROJ_LIB", str(osgeo_path / "data" / "proj"))

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": "http://invalid-redacted.local"
    }
}

# DEFAULT_DSL_NAMESPACE = 'delocloud'
#TG_BOT_TOKEN = '8238977097:AAFzyuhVCFsvU7bR8obegZOFWXtUbn7brHE'
VOICE_INPUT_RECOGNIZE_URL = 'http://10.100.0.39:5080/recognize'

# Local front/back integration overrides.
BACKEND_URL = 'http://d.centersoft.kz:8000'
FRONTEND_URL = 'http://d.centersoft.kz:8080'
ALLOWED_HOSTS = list(set(ALLOWED_HOSTS + ['d.centersoft.kz', '__redacted_invalid__', 'localhost']))
CSRF_TRUSTED_ORIGINS = [
    'd.centersoft.kz',
    'd.centersoft.kz:8000',
    'd.centersoft.kz:8080',
    '__redacted_invalid__',
    '__redacted_invalid__:8000',
    'localhost',
    'localhost:8000',
]
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOWED_ORIGINS = [
    'http://d.centersoft.kz:8080',
    'http://d.centersoft.kz:8000',
    'http://__redacted_invalid__:8080',
    'http://__redacted_invalid__:8000',
]
