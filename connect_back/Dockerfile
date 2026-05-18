FROM python:3.8
ENV PYTHONUNBUFFERED 1
RUN apt update && apt install -y htop supervisor nano mc libreoffice gcc musl-dev libffi-dev binutils libproj-dev ffmpeg gdal-bin
COPY ./chat-handler-bkz.conf /etc/supervisor/conf.d/chat-handler-bkz.conf
COPY ./bkz-django-q.conf /etc/supervisor/conf.d/bkz-django-q.conf
COPY ./bot-delans.conf /etc/supervisor/conf.d/welcome-bot.conf
COPY ./aster.conf /etc/supervisor/conf.d/aster.conf
RUN mkdir /app
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install uwsgi
# RUN pip install git+https://github.com/django-haystack/django-haystack
RUN pip install django-haystack[elasticsearch]
COPY . .
EXPOSE 5001
CMD ["/bin/bash", "/app/start.sh"]
