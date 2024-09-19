# Makefile for Superpool application
#
# File contains common commands utilized by developers during development
# of the Superpool application.
#
# Created by: Eri A.
# Created on: 09:50 2024-06-05

.PHONY: help clear_migrations migrations clear_pycache run_server show_migrations shell test

help:
	@echo "Superpool Makefile"
	@echo "=================="
	@echo "clear_migrations: 				Delete all migrations files"
	@echo "migrations: 				Create new migrations files"
	@echo "clear_pycache: 					Delete all python cache files"
	@echo "run_server: 						Run the development server"
	@echo "show_migrations: 				Show all migrations"
	@echo "shell: 							Run the Django shell"

clear_migrations:
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc"  -delete

migrations:
	python superpool/api/manage.py make_migrations
	python superpool/api/manage.py migrate

clear_pycache:
	find . -path "*/*.pyc" -delete
	find . -path "*/__pycache__" -delete

run_server:
	python superpool/api/manage.py runserver

show_migrations:
	python superpool/api/manage.py showmigrations

shell:
	python superpool/api/manage.py shell

mypy:
	mypy --config-file superpool/mypy.ini .

test:
	python superpool/api/manage.py test
