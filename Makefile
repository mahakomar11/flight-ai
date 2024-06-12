SHELL := /bin/bash

PYTHON_PATH := $(shell which python3.11)

VENV_PATH ?= ./.venv
VENV_PYTHON := $(VENV_PATH)/bin/python

DEV_ENV_FILE := .env-dev
DEV_COMPOSE_FILE := docker-compose.dev.yml

SERVICES ?= ./chat ./src ./migrations

ALEMBIC_CONFIG := alembic.ini

############### INSTALL ###############

install-deps:
	@echo -e "Install dependencies for ${SOURCE}\n"
	$(VENV_PYTHON) -m pip install \
		--no-deps -Ur ./${SOURCE}/requirements.txt

install-deps-dev:
	@echo -e "Install development dependencies\n"
	$(VENV_PYTHON) -m pip install \
		-Ur ./requirements-dev.txt

install-deps-tests:
	@echo -e "Install development dependencies\n"
	$(VENV_PYTHON) -m pip install \
		-Ur ./tests/requirements.txt

############### ENV ###############

env-create-empty:
	@echo -e "Create virtual environment\n"
	virtualenv --python=$(PYTHON_PATH) $(VENV_PATH)

	@echo "Activate virtual environment\n"
	@source $(VENV_PATH)/bin/activate

env-create: env-create-empty
	@echo -e "Install dependencies for phoenix"
	SOURCE=chat $(MAKE) -f Makefile install-deps

	@echo -e "Install dev dependencies"
	$(MAKE) -f Makefile install-deps-dev

env-remove:
	rm -rf ${VENV_PATH}

env-update: env-remove env-create

############### BUILD ###############

build-format:
	@echo -e "############### ISORT ###############\n"
	$(VENV_PYTHON) -m isort $(SERVICES) ./tests
	@echo -e "############### BLACK ###############\n"
	$(VENV_PYTHON) -m black --skip-magic-trailing-comma $(SERVICES) ./tests

############### DEBUG #################

dev-compose-up:
	docker-compose --env-file $(DEV_ENV_FILE) -f $(DEV_COMPOSE_FILE) up -d --build

dev-compose-down:
	docker-compose --env-file $(DEV_ENV_FILE) -f $(DEV_COMPOSE_FILE) down

############### CHECK ###############

check-lint:
	echo -e "############### FLAKE ###############\n" ; \
	$(VENV_PYTHON) -m flake8 $(SERVICES) ./tests; \
	FLAKE8_EXIT_CODE=$$? ; \
	\
	echo -e "############### BLACK ###############\n" ; \
	$(VENV_PYTHON) -m black --check --diff $(SERVICES) ./tests; \
	BLACK_EXIT_CODE=$$? ; \
	\
	echo -e "############### ISORT "###############\n ; \
	$(VENV_PYTHON) -m isort --check --diff $(SERVICES) ./tests; \
	ISORT_EXIT_CODE=$$? ; \
	\
	if [ $$FLAKE8_EXIT_CODE != 0 ] || [ $$BLACK_EXIT_CODE != 0 ] || [ $$ISORT_EXIT_CODE != 0 ]; then \
		exit 1 ; \
	else \
		exit 0 ; \
	fi

############### DATABASE ###############
include ${DEV_ENV_FILE}

.db-migrate:
	POSTGRES_NAME=${POSTGRES_NAME} \
	POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	alembic -c ${ALEMBIC_CONFIG} upgrade head

db-migrate:
	@read -p "DANGER! This command will migrate database in ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_NAME} database, print database password to confirm " ans && ans=$${ans} ; \
	if [ $${ans} != ${POSTGRES_PASSWORD} ];	then \
		echo "Aborting" && exit 1 ; \
	fi
	POSTGRES_NAME=${POSTGRES_NAME} \
	POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	alembic -c ${ALEMBIC_CONFIG} upgrade head

.db-downgrade:
	POSTGRES_NAME=${POSTGRES_NAME} \
	POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	alembic -c ${ALEMBIC_CONFIG} downgrade ${DOWNGRADE_TO}

db-downgrade:
	@read -p "DANGER! This command will downgrade database in ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_NAME} database, print database password to confirm " ans && ans=$${ans} ; \
	if [ $${ans} != ${POSTGRES_PASSWORD} ];	then \
		echo "Aborting" && exit 1 ; \
	fi
	DOWNGRADE_TO=-1 $(MAKE) .db-downgrade

db-revision:
	POSTGRES_NAME=${POSTGRES_NAME} \
	POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	alembic -c ${ALEMBIC_CONFIG} revision --autogenerate -m ${NAME}

db-clear:
	@read -p "DANGER! This command will clear all database in ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_NAME} database, print database password to confirm " ans && ans=$${ans} ; \
	if [ $${ans} != ${POSTGRES_PASSWORD} ];	then \
		echo "Aborting" && exit 1 ; \
	fi
	@echo "Clearing database"
	DOWNGRADE_TO=base $(MAKE) .db-downgrade
	$(MAKE) .db-migrate
