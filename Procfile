web: gunicorn TrivIFTA.TrivIFTA.wsgi
worker: celery -A TrivIFTA.TrivIFTA worker --loglevel=info -c 3
beat: celery -A TrivIFTA.TrivIFTA beat --loglevel=info