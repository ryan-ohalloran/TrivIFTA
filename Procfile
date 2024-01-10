web: gunicorn trivifta.wsgi
worker: celery -A TrivIFTA worker --loglevel=info -c 3
beat: celery -A TrivIFTA beat --loglevel=info