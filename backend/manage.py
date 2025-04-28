#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
# --- ADD THIS SECTION ---
from dotenv import load_dotenv
# --- END OF ADDED SECTION ---

def main():
    # --- ADD THIS LINE ---
    load_dotenv() # Loads variables from .env into os.environ
    # --- END OF ADDED LINE ---

    """Run administrative tasks."""
    # --- Make sure DJANGO_SETTINGS_MODULE points to the correct path ---
    # Check if your settings file is at backend.settings or backend.backend.settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') # Adjust if needed
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()