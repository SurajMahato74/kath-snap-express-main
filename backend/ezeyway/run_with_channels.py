#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
    
    # For WebSocket support, use daphne instead of runserver
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        # Install daphne if not installed: pip install daphne
        execute_from_command_line(['manage.py', 'runserver', '--noreload'])
    else:
        execute_from_command_line(sys.argv)