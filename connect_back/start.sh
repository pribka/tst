#!/bin/bash
#python manage.py makemigration --noinput
#python manage.py migrate --noinput
#python manage.py makemigrations --noinput
#celery -A bkz3 worker -l warn --logfile celery.log --pidfile celery.pid --detach
#service supervisor start
#supervisorctl start chat-handler-bkz3
#supervisorctl start bkz-django-q
#supervisorctl start welcome-bot
uwsgi --ini /app/project.ini
#python manage.py runserver 0.0.0.0:5001

# Exit with status of process that exited first
exit $?
