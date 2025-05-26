#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import oracledb

try:
    oracledb.init_oracle_client()
    print("Inicio modo thick")
except Exception as e:
    print("error: {e}")  

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'modulo_citas.settings')
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
