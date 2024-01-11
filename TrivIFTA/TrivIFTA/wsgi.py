"""
WSGI config for TrivIFTA project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings
BASE_DIR = settings.BASE_DIR

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TrivIFTA.settings")

application = get_wsgi_application()
application = WhiteNoise(application, root=settings.STATICFILES_DIRS[0])
