# Makefile for Superpool application
#
# File contains common commands utilized by developers during development
# of the Superpool application.
#
# Created by: Eri A.
# Created on: 09:50 2024-06-05
clear_migrations:
	find . -path "**/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "**/migrations/*.pyc"  -delete

make_migrations:
	python manage.py makemigrations

