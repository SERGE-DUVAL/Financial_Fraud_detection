#!/usr/bin/env python
"""Site Django de détection de fraude.

Lancement (depuis ce dossier) :
    python manage.py runserver
puis ouvrir http://127.0.0.1:8000/
"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fraud_api.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
