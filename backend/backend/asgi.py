# backend/asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') # Adjust 'backend.settings' if needed

application = get_asgi_application()


## backend/asgi.py (TEMPORARY TEST)
#import os
#import django
#from django.core.asgi import get_asgi_application

#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
#django.setup()

## Only include the basic Django ASGI app for HTTP
#application = get_asgi_application()

#print("ASGI Application Instantiated (HTTP ONLY TEST) - Daphne is ready.")