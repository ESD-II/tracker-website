"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
# --- ADD THIS SECTION ---
from dotenv import load_dotenv
# --- END OF ADDED SECTION ---

from django.core.wsgi import get_wsgi_application

# --- ADD THIS LINE ---
load_dotenv() # Load .env before accessing settings
# --- END OF ADDED LINE ---

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') # Adjust if needed

application = get_wsgi_application()