"""
WSGI config for alumin_event project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""
print("Loading WSGI...")

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumin_event.settings')

try:
    application = get_wsgi_application()
except Exception as e:
    import traceback
    print("WSGI load failed:")
    traceback.print_exc()
    raise

