"""
WSGI config for AILLA project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

django_application = get_wsgi_application()
application = WhiteNoise(django_application,
                         root=settings.STATIC_ROOT,
                         prefix=settings.STATIC_URL)