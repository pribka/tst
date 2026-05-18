import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + ''
SECRET_KEY = '!!!SECRET!!!'

DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # 'NAME': 'bkz_empty2',
        # 'NAME': 'bkz_empty4',
        # 'NAME': 'bpms_main_new',
        'NAME': 'bpms',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

ALLOWED_HOSTS = ['*']
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_URL = '/static/'

REDIS_HOST = 'localhost'
REDIS_PORT = '6379'

CACHES = {
    'default': {
        "BACKEND": "django_redis.cache.RedisCache",
        'LOCATION': 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/12',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

CSRF_TRUSTED_ORIGINS = {
    'local.bkz3.kz',
    'd2.centersoft.kz',
    'd.centersoft.kz',
}
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://local.bkz3.kz",
    "http://d2.centersoft.kz",
    "http://d.centersoft.kz:8080",
    "http://d.centersoft.kz:8080",
    "http://d.centersoft.kz",
]

BACKEND_URL = 'http://d.centersoft.kz:8080'

FRONTEND_URL = 'http://d.centersoft.kz:8080'

SESSION_REDIS = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': 10,
    'prefix': 'session',
    'socket_timeout': 1
}
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_PREFIX = 'session'
SESSION_COOKIE_DOMAIl = '.centersoft.kz'

BROKER_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/4'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'INCLUDE_SPELLING': True,
        'URL': 'http://127.0.0.1:8983/solr/bkz3.centersoft.kz',
        'HAYSTACK_DEFAULT_OPERATOR': 'OR',
        'TIMEOUT': 60 * 5,
    },
}
#
# HAYSTACK_CONNECTIONS = {
#     'default': {
#         'ENGINE': 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine',
#         'INCLUDE_SPELLING': True,
#         'URL': 'http://127.0.0.1:9200',
#         'HAYSTACK_DEFAULT_OPERATOR': 'OR',
#         'TIMEOUT': 60 * 5,
#         'INDEX_NAME': "haystack"
#     },
# }
#HAYSTACK_SIGNAL_PROCESSOR = 'common.djangoq_haystack.signal_processor.DjangoQSignalProcessor'
IMPORT_DATA_TOKEN = '9ZN#mJpJN2dP7A9EDLVR8}>%+-u8vw~]#+cmd:]tWeKn6w*q1VW-eY}'
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000000000
DATA_UPLOAD_MAX_MEMORY_SIZE = 100000000000
EMAIL_HOST_USER = ''
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# IP-адрес УРВ:
IP_ADDRESS_URV = ''
TOKEN_URV = 'LKJHGDSLfkhjlg'

# URV_SEND_DATA_URL = ''
DOWNLOADER_PATH = None
GLOBAL_FRONT_SETTINGS = {
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
        "vue2GroupsAndProjectsComponent",
        "vue2TaskComponent",
        "vue2ChatComponent",
        "vue2MeetingComponent",
        "BusinessProcesses",
        "Notifications",
        "Dashboard",
        "Products",
        "Orders",
        "vue2FlowchartsComponent",
        "vue2Files",
        "vue2CommentsComponent",


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
        "product_cart": True,
        "logo": f"{BACKEND_URL}/media/new_lg.svg",
        "logo_mini": f"{BACKEND_URL}/media/new_logo_mini_1.svg",
        "favicon": f"{BACKEND_URL}/media/favicon.ico",
    },
    "footer_setting": {
        "active": True,
    },
    "site_setting":{
        "site_name": "BPMS",
        "pwa": True,
        "push_key": "",
        "gant_key": "",
        "ui_key":"",
        "icon_16":f"{BACKEND_URL}/media/icon-16x16.png",
        "icon_32":f"{BACKEND_URL}/media/icon-32x32.png",
        "icon_96":f"{BACKEND_URL}/media/icon-96x96.png",
        "icon_192":f"{BACKEND_URL}/media/icon-192x192.png",
        "icon_512":f"{BACKEND_URL}/media/icon-512x512.png",
        "icon_mask_192":f"{BACKEND_URL}/media/icon-mask-192x192.png",
        "icon_mask_512":f"{BACKEND_URL}/media/icon-mask-512x512.png",
    },
    "order_setting":{
        "cartDecimalCount": True, # Позволяет вводить дробные количества в корзине
        "check_stock": True,
        "cartMinusDelete": False,
        "remnant_control": True,
        "show_create_order_button": True,
        "calculate_warehouse_tp": False,
    },
    "front_page": "dashboard",
    "sounds": {
        "new_message": f"{BACKEND_URL}/media/new_message.mp3",
        "new_notify": f"{BACKEND_URL}/media/new_notify.mp3",
    },
    "main_settings": {
        "VUE_APP_SENTRY_DSN": "https://",
        "VUE_APP_SENTRY_AUTH_TOKEN": "",
        "VUE_APP_SENTRY_URL": "https://",
        "VUE_APP_SENTRY_ORG": "",
        "VUE_APP_SENTRY_PROJECT": "bpms",
        "VUE_APP_TAGMANAGER_ID": "",
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
    },
        "product_setting": {
        "product_default_list": "ProductCardInfoList", # Дефолтный список товаров
        "product_history": False, #История недавних товаров
    },
        "old_cabinet_url": "https://oldkabinte.net",
    "map": {
        "tileToken": "<token>",
        "tileUrl": "https://tile.jawg.io/jawg-sunny/{z}/{x}/{y}{r}.png?access-token=<token>"
    },
    "theme": {
        "main_color": "#1d65c0",
        "aside_color": "eff2f5",
        "blue": "1890ff",
        "tableSize": "small",
    },
    'dashboard_settings': { # Что показать на главной странице
        'items': ['team', 'completed_task', 'created_task', 'news', 'goods']
    }

}

DEFAULT_CURRENCY_CODE = '643'

IMPORT_1C_DATA_TOKEN = '@@@TOKEN@@@'
TIME_ZONE = 'Europe/Moscow'

EXPORT_1C_DATA_URL = 'https://base433.gos24.kz/Uvsb3Z7ksh/'
# EXPORT_1C_DATA_URL = 'https://promsiteh-as.esit.info:5443/1s.UTCRM_Promsytex.v8.3_test/'
EXPORT_1C_DATA_TOKEN = 'LKJHGDSLfkhjlg'
FRONT_CATEGORIES = {
    'front_page': (),
    'communication': (
    'meetings',
    'chat',
    'tasks',
    'groups',
    'projects',
    'business_processes',
    'flowchart',
    'files',
    'helpdesk'),
    'crm': (
        'logistic',
        'goods',
        'orders',
        'interest',
        'interest_kanban',
    ),
    'test_page': ('edition',),
}

HZ = {
    'front_page': (),
    'crm': (

        'goods',
        'orders',
        'interest',
        'interest_kanban',
        'logistic',
        'logistic_monitor',
    ),

    'communication': (
        'meetings',
        'chat',
        'tasks',
        'groups',
        'projects'
    ),

}

LOCAL_REMNANT_CONTROL = True

SUPPORT_EMAIL = 'HelpDesk@prst.ru'
COMPANY_NAME = 'ООО "Промситех"'

Q_CLUSTER = {
    'retry': 180,
    'timeout': 120,
    'workers': 1,
    'name': 'bkz',
    'redis': {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'db': 7,
    }
}

SHOW_CONTRACT_IN_GOODS_ORDER = False
SHOW_PAY_TYPE_IN_GOODS_ORDER = False
SOCKETIO_SYSTEM_CHANNEL = ''
TG_BOT_TOKEN ='5617467066:AAHoQGi8KEoSxiX8Y6l3uystxXAE-6UskmU'
MOBILE_GLOBAL_FRONT_SETTINGS=''
TG_BOT_NAME =''
BITRIX_TOKEN ='59/ki23ug8rmnphdm5w'
BITRIX_OUTER_TOKEN = 'tz5dimhb59c3xarmlf3yww5toykai5it'

MOBILE_APP_GLOBAL_FRONT_SETTINGS = {
    "injectModules": {
        "notifications": True,
    },
    "injectComponents": [
        "TaskDetail",
    ],
}
MOBILE_APP_PRIVATE_OFFICE = (
    {
        "icon": "fi-rr-id-badge",
        "name": "Персональная информация",
        "path": "personal",
        "widget": "Personal",
    }
)
