# bkz3

## Добавить пакет для Windows
pip install python-magic-bin

## Обновление файлов локализации (генерация файлов django.po):

    django-admin makemessages -i venv -i media -a

## Компиляция файлов локализации (django.mo):
    django-admin compilemessages

## fix error django.core.exceptions.ImproperlyConfigured: Could not find the GDAL library (tried "gdal302", "gdal301", "gdal300", "gdal204", "gdal203", "gdal202", "gdal201", "gdal20"). Is GDAL installed? If it is, try setting GDAL_LIBRARY_PATH in your settings.
import os, sys
if os.name == 'nt':
    VENV_BASE = os.environ['VIRTUAL_ENV']
    os.environ['PATH'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo') + ';' + os.environ['PATH']
    os.environ['PROJ_LIB'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo\\data\\proj') + ';' + os.environ['PATH']

## Развертывание
### Конфиг демона qcluster через supervisor

    [program:bkz-django-q]
    command = /path/to/venv/bin/python manage.py qcluster
    user = username
    autostart = true
    autorestart = true
    stdout_logfile = /path/to/logs/django-q.log
    redirect_stderr = true
    directory = /path/to/project/
    numprocs = 1
    startsecs = 10
    stopwaitsecs = 30
    killasgroup = true

### Обновление схемы solr
В корне проекта лежит schema.xml.
Необходимо скопировать этот файл в каталог с ядром solr проекта (примерное расположение):

    cp /path/to/project/schema.xml /path/to/solr/multicore/core_name/conf/schema.xml
 
И перезапустить ядро solr проекта с помощью http-запроса:

    curl "http://127.0.0.1:8983/solr/admin/cores?action=RELOAD&core=core_name&wt=json" 

После обновления схемы необходимо под окружением проекта обновить индексы:

    source /path/to/venv/bin/activate
    path/to/project/python manage.py update_index --remove

Это может занять некоторое время.

### Обновление индекса в ElasticSearch
#### Созание индекса
1. Создаём новый индекс в ElasticSearch:

        python manage.py elastic --create_index [index_name]

    [index_name] - имя нового индекса. Если имени нет, будет создан индекс с INDEX_NAME 
    из HAYSTACK_CONNECTIONS['default']

2. Прописываем имя созданного индекса в HAYSTACK_CONNECTIONS['default'] под ключом 'INDEX_NAME', 
если вы этого еще не сделали.
3. Обновляем данные в новом индексе:
    
        python manage.py update_index --remove

#### Обновление структуры индекса
Настройки Elasticsearch индекса находятся в файле bkz3/elastic_index.py.
Чтобы обновить структуру индекса в ElasticSearch, необходимо выполнить две команды:

    python manage.py elastic --rebuild_index
    python manage.py update_index --remove

Внимание!!! Не использовать python manage.py rebuild_index.
Потому что тогда индекс создается с настройками по умолчанию.
А нам нужные настройки из файла bkz3/elastic_index.py, поэтому используем только 
python manage.py elastic --rebuild_index.

#### Все команды для управления индексами
- Проверить кластер:

        python manage.py elastic --check
    
- Просмотреть список индексов кластера:

        python manage.py elastic --list_index

- Создать индекс с именем [index_name]:

        python manage.py elastic --create_index [index_name]
    
    Здесь и далее, если не указан параметр [index_name], то его значение берется из 'INDEX_NAME' 
    в HAYSTACK_CONNECTION['default']
    
- Просмотреть деталку индекса:

        python manage.py elastic --detail_index [index_name]
    
- Удалить текущий индекс:

        python manage.py elastic --delete_index [index_name]
    
- Пересоздать индекс (выполняются сначала --delete_index, затем --create_index):
    
        python manage.py elastic --rebuild_index [index_name]
    
- Проверить размер индекса
curl -X GET "http://127.0.0.1:9200/_cat/indices/bkz?v&h=index,store.size,docs.count"
    
### Конфиг демона для сохранения данных о чате в БД (supervisor)

    [program:bkz-chat-handler]
    command = path/to/venv/bin/python chat_handler.py
    user = username
    autostart = true
    autorestart = true
    stdout_logfile = /path/to/logs/chat-handler.log
    redirect_stderr = true
    directory = /path/to/project/
    numprocs = 1
    startsecs = 10
    stopwaitsecs = 30
    killasgroup = true


## GIS
### Установка
1. Установить библиотеки:

        sudo apt-get install binutils libproj-dev gdal-bin

2. Установить расширение postgis:

        sudo apt install postgresql-14-postgis

    У вас номер версии может отличаться.
3. В конфиге подключения к БД  поменять бэкенд:

        'ENGINE': 'django.contrib.gis.db.backends.postgis',

4. Теперь можно выполнять миграции. Если миграция выдает ошибку "Установка дополнения может быть только от суперюзера",
необходимо вручную установить дополнение в БД:

    1. Зайти в psql:
    
            sudo -u postgres psql
        
        Имя пользователя postgres у вас может отличаться.
        
    2. Выбрать текущую базу данных:
        
            \с <db_name>
        
        где <db_name> - это база данных проекта
    
    3. Установить дополнение postgis:
        
            create extension postgis;
    4. Запустить миграции

### Изменение границ
Если изменились границы районов/областей, добавились новые или т. п., необходимо сделать следующее:
1. Скачать файл .geojson с сайта https://osm-boundaries.com/map изменившейся области. 
В файле должна быть область и все ее районы. Для удобства изменить расширение на json.
2. Заменить файл области на новый в каталоге common/catalogs/osm_regions/
3. Подготовить файл с помощью команды:
       
       python manage.py --prepare_admin_areas file_name.json
       
4. Открыть файл, и для всех границ прописать name_ru. Проверить, что name_kk корректный.
5. Удалить записи в бд с областью и ее районами через админку.
6. Загрузить обновленную область с районами в базу данных с помощью команды
    
        python manage.py --load_admin_areas file_name.json
        
    С ключом all вместо имени файла загрузятся все файлы.
7. Переназначить области и районы геометкам. 
    
    Для обращений:
    
        python manage.py risk_assessment --rebuild_location_points
        
На проде или стенде необходимо будет выполнить пункты с 5 по 7.
    