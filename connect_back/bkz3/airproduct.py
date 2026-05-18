import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'django-insecure-z=0fr6uvf5wz)wx)xu^2i@d5s9^8)pn3-a5k&mj1x(e!$w)h!7'

COMPANY_NAME = 'Delans'
SHORT_COMPANY_NAME = 'Delans'

SUPPORT_EMAIL = 'noreply@gos24mailer.kz'

DEBUG = True
#DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'airproduct',
        'USER': 'postgres',
        'PASSWORD': 'Choo2uxe',
        'HOST': 'postgres-13.5',
        'PORT': '5432',
    }
}

ALLOWED_HOSTS = ['crm.delans.ru']
STATIC_ROOT = os.path.join(BASE_DIR, 'media/static/')
STATIC_URL = '/static/'
STATICFILES_DIRS = ['/app/static_admin']

REDIS_HOST = 'redis'
REDIS_PORT = '6379'

CACHES = {
    'default': {
        "BACKEND": "django_redis.cache.RedisCache",
        'LOCATION': 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/1',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

TIME_ZONE = 'Europe/Moscow'

BACKEND_URL = 'https://crm.delans.ru'

FRONTEND_URL = 'https://crm.delans.ru'


SESSION_REDIS = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': 1,
    'prefix': 'session',
    'socket_timeout': 1
}
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_PREFIX = 'session'
SESSION_COOKIE_HTTPONLY = False
BROKER_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/1'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
result_backend = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/1'
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'INCLUDE_SPELLING': True,
        'URL': 'http://172.17.0.1:8983/solr/cotn.delocloud.ru',
        'HAYSTACK_DEFAULT_OPERATOR': 'OR',
        'TIMEOUT': 60 * 5,
    },
}

#HAYSTACK_CONNECTIONS = {
#    'default': {
#        'ENGINE': 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine',
#        'INCLUDE_SPELLING': True,
#        'URL': 'http://elastic:9200',
#        'HAYSTACK_DEFAULT_OPERATOR': 'OR',
#        'TIMEOUT': 60 * 5,
#        'INDEX_NAME': "airprod",
#        'KWARGS':{
        #    'http_auth': ('elastic', 'CDOHNR-ZnnnrkZWz*wuC'),
#            'use_ssl':False,
#            'verify_certs':False,
#        }
#    },
#}
# HAYSTACK_SIGNAL_PROCESSOR = 'celery_haystack.signals.CelerySignalProcessor'
# HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
HAYSTACK_SIGNAL_PROCESSOR = 'common.djangoq_haystack.signal_processor.DjangoQSignalProcessor'
IMPORT_DATA_TOKEN = 'Shsdndfu36sd2yshwys6djwpw836whasharfhysdsh'

DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000000000
DATA_UPLOAD_MAX_MEMORY_SIZE = 100000000000
TOKEN_URV='LKJHGDSLfkhjlg'

# email:


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'bmx.cskz.kz'
EMAIL_HOST_USER = 'noreply@gos24mailer.kz'
EMAIL_HOST_PASSWORD = 'GP2Jg@%3K6v7vxfe'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'noreply@gos24mailer.kz'





GLOBAL_FRONT_SETTINGS = {
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
        "vue2ChatComponent",
        "vue2MeetingComponent",
        "BusinessProcesses",
        "Notifications",
        "Dashboard",
        "Products",
        "Orders",
#        "vue2FlowchartsComponent",
        "vue2Files",
        "vue2CommentsComponent",





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
    "order_setting":{
	"always_show_get_paid_button": True,
        "check_stock":False,
"cartPriceEdit": True,
'orderCartEdit':True,'orderExtendMeasures':True,	"check_stock_modal": True,
	"min_product_count":0,
'cartDecimalCount':True,        "cartMinusDelete":False,
        "remnant_control":False,
	"show_create_order_button": True,
	 "calculate_warehouse_tp": False,
	"showCartCatalogButton": True,
"cartCatalogButtonLink": "dashboard",
"calculationButton": True
},    "aside_setting": {
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
        "logo": "https://cotn.delocloud.ru/media/user_c7a2f74d-8057-11ed-9c0d-b9d8a2bff12b/0c1fbc09-a2f1-4e71-9aa8-17a5e6f9a8f6.png",
        "logo_mini":"https://cotn.delocloud.ru/media/user_c7a2f74d-8057-11ed-9c0d-b9d8a2bff12b/0c1fbc09-a2f1-4e71-9aa8-17a5e6f9a8f6.png",
    },
    "theme": {
        "main_color": "#1d65c0",
        #"main_color": "#89c340",
        "aside_color": "eff2f5",
        "blue": "1890ff",
        "tableSize": "small",
    },
'dashboard_settings': {
        'items': [
        'get_started',
        'news',	
        'dashboard_contractors', 
#'completed_task',
# 'created_task',
# 'news',
# 'goods',
]
    },
    "site_setting":{
        "site_name": "Кабинет дилера",
        "pwa": True,
        "ui_key":"ORg4AjUWIQA/Gnt2VVhjQlFaclhJXGFWfVJpTGpQdk5xdV9DaVZUTWY/P1ZhSXxRd0VgWH9ccXBQQmdaUU0=",    
        "icon_16":f"{BACKEND_URL}/media/icon-16x16.png",
        "icon_32":f"{BACKEND_URL}/media/icon-32x32.png",
        "icon_96":f"{BACKEND_URL}/media/icon-96x96.png",
        "icon_192":f"{BACKEND_URL}/media/icon-192x192.png",
        "icon_512":f"{BACKEND_URL}/media/icon-512x512.png",
        "icon_mask_192":f"{BACKEND_URL}/media/icon-mask-192x192.png",
        "icon_mask_512":f"{BACKEND_URL}/media/icon-mask-512x512.png",
    },
    "footer_setting": {
        "active": True,
    },
    "front_page": "dashboard",
    "sounds": {
        "new_message": f"{BACKEND_URL}/media/new_message.mp3",
        "new_notify": f"{BACKEND_URL}/media/new_notify.mp3",
    },
    "product_setting": {
        "product_default_list": "ProductCardShortList", # Дефолтный список товаров
        "product_history": False, #История недавних товаров
    },
}
DEFAULT_CURRENCY_CODE = '643'

IMPORT_1C_DATA_TOKEN = 'osjdfjsldkf'
FRONT_CATEGORIES = {
    'dashboard': (),
    'communication': ('calendar','my_bases', 'team', 'chat', 'meetings', 'tasks', 'groups', 'projects', 'files'),
    'crm': ('contractors','interest', 'interest_kanban')
}

EXPORT_1C_DATA_URL = 'http://10.35.0.131/crm_delance/'
EXPORT_1C_DATA_TOKEN = 'ZWZzb2w6ZWZzb2w='
LOCAL_REMNANT_CONTROL = False
Q_CLUSTER = {
    'retry': 180,
    'timeout': 120,
    'workers': 1,
    'name': 'bkz',
    'redis': {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'db': 1,
    }
}

SHOW_CONTRACT_IN_GOODS_ORDER = False
SHOW_PAY_TYPE_IN_GOODS_ORDER = True
DEFAULT_PRICE_TYPE_CODE = None
GOODS_PRICE_BY_CATALOG = True
SOCKETIO_SYSTEM_CHANNEL = 'system'
TG_BOT_TOKEN = '6378071262:AAEzCHLUrNYGy21NuLAbx7dwawibbPzLsQM'
TG_BOT_NAME = 'deland_info_bot'

GOODS_PRICE_BY_CATALOG = True 
DEFAULT_PRICE_TYPE_CODE = None
DOWNLOADER_PATH = None
MOBILE_GLOBAL_FRONT_SETTINGS = {
	"locale": {
        "default_lang": "ru",
        "lang_list": [
            "ru",
            "en",
            "kk"
        ],
        "fallback_lang": "en",
        "injectTranslate": [
            "vue2TaskComponent",
            "Profiler",
            "Upload",
            "vue2GroupsAndProjectsComponent",
            "vue2ChatComponent"
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
        "LogisticMonitor"
    ],
    "upload_config": {
        "max_file_size": 10
    },
    "widgets": {
        "show": True
    },
    "table_setting": {
        "theme": "ag-theme-alpine"
    },
    "order_setting": {
        "check_stock": False,
        "cartPriceEdit": True,
        "orderCartEdit": True,
        "cartMinusDelete": False,
        "remnant_control": False,
        "cartDecimalCount": True,
        "calculationButton": True,
        "check_stock_modal": True,
        "min_product_count": 0,
        "orderExtendMeasures": True,
        "cartCatalogButtonLink": "dashboard",
        "showCartCatalogButton": True,
        "calculate_warehouse_tp": False,
        "show_create_order_button": True,
        "always_show_get_paid_button": True
    },
    "aside_setting": {
        "active": True,
        "theme": "FlatAside",
        "grouping": True,
        "width": 250
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
        "logo": "https://cotn.delocloud.ru/media/user_c7a2f74d-8057-11ed-9c0d-b9d8a2bff12b/0c1fbc09-a2f1-4e71-9aa8-17a5e6f9a8f6.png",
        "logo_mini": "https://cotn.delocloud.ru/media/user_c7a2f74d-8057-11ed-9c0d-b9d8a2bff12b/0c1fbc09-a2f1-4e71-9aa8-17a5e6f9a8f6.png"
    },
    "theme": {
        "main_color": "#1d65c0",
        "aside_color": "eff2f5",
        "blue": "1890ff",
        "tableSize": "small"
    },
    "dashboard_settings": {
        "items": [
            "contractors",
            "goods"
        ]
    },
    "site_setting": {
        "site_name": "Кабинет дилера",
        "pwa": True,
        "ui_key": "ORg4AjUWIQA/Gnt2VVhjQlFaclhJXGFWfVJpTGpQdk5xdV9DaVZUTWY/P1ZhSXxRd0VgWH9ccXBQQmdaUU0=",
        "icon_16": "https://cotn.delocloud.ru/media/icon-16x16.png",
        "icon_32": "https://cotn.delocloud.ru/media/icon-32x32.png",
        "icon_96": "https://cotn.delocloud.ru/media/icon-96x96.png",
        "icon_192": "https://cotn.delocloud.ru/media/icon-192x192.png",
        "icon_512": "https://cotn.delocloud.ru/media/icon-512x512.png",
        "icon_mask_192": "https://cotn.delocloud.ru/media/icon-mask-192x192.png",
        "icon_mask_512": "https://cotn.delocloud.ru/media/icon-mask-512x512.png"
    },
    "footer_setting": {
        "active": True
    },
    "front_page": "orders",
    "sounds": {
        "new_message": "https://cotn.delocloud.ru/media/new_message.mp3",
        "new_notify": "https://cotn.delocloud.ru/media/new_notify.mp3"
    },
    "product_setting": {
        "product_default_list": "ProductCardShortList",
        "product_history": False
    },
    "map": {
        "tileUrl": "https://tile.jawg.io/jawg-sunny/{z}/{x}/{y}{r}.png",
        "tileToken": "hNDwFPXSQQAieYAl4otxT60FDtqY7fE1Kaf37y9IX73edcJ7FMAvY5iCbIgU3GJh",
        "serviceUrl": "https://router.project-osrm.org/route/v1"
    }
}
ORDER_DELIVERY = 'COTN'



PRODUCT_LIST_INFO = [   {
                "type": 'ProductCardShortList',
                "icon": 'fi-rr-list',
                "title": 'Короткий список',
            },]
ORDER_WITHOUT_1C =          False



ORDER_FORM_SETTINGS = {
    "showContractor": True,
    "showContractorMember": False,
    "showContract": False,
}

MOBILE_APP_GLOBAL_FRONT_SETTINGS = {
    "injectModules": {
        "notifications": False,
    },
    "injectComponents": [
        "TaskDetail",
    ],
    "checkLocation": True,
}

MOBILE_APP_FRONT_CATEGORIES = {
  'home', 'logistic'
}
DIRECT_ORDER_FILES=True

ONLY_DEFAULT_WAREHOUSE_IN_LIST = True
TG_BOT_TOKEN = '5617467066:AAHoQGi8KEoSxiX8Y6l3uystxXAE-6UskmU'
