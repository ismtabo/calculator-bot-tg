DOCKER_USER                       ?= ismtabo
DOCKER_PASSWORD                   ?=
DOCKER_REGISTRY                   ?=
DOCKER_ORG                        ?= $(DOCKER_USER)
DOCKER_PROJECT                    ?= dle-rae-bot-tg
DOCKER_API_VERSION                ?=
DOCKER_IMAGE                      ?= $(if $(DOCKER_REGISTRY),$(DOCKER_REGISTRY)/$(DOCKER_ORG)/$(DOCKER_PROJECT),$(DOCKER_ORG)/$(DOCKER_PROJECT))
DOCKER_SERVICES                   ?= tgbot

USER_UID                          ?= $(shell id -u)
USER_GID                          ?= $(shell id -g)
HOST_UID_GID                      ?=

PRODUCT_VERSION                   ?=
PRODUCT_REVISION                  ?=
BUILD_VERSION                     ?= $(PRODUCT_VERSION)-$(PRODUCT_REVISION)
LDFLAGS_OPTIMIZATION              ?= -w -s
LDFLAGS                           ?= $(LDFLAGS_OPTIMIZATION)

DOCKER_COMPOSE_PROJECT            := $(shell echo '$(DOCKER_PROJECT)' | sed -e 's/[^a-z0-9]//g')
DOCKER_COMPOSE_ENV                := HOST_UID_GID='$(USER_UID):$(USER_GID)'
DOCKER_COMPOSE                    := $(DOCKER_COMPOSE_ENV) docker-compose -p '$(DOCKER_COMPOSE_PROJECT)'

PIPENV_VENV_IN_PROJECT_FOLDER     ?= 1
PIPENV_VENV_IN_PROJECT_FOLDER_ENV := PIPENV_VENV_IN_PROJECT_FOLDER=$(PIPENV_VENV_IN_PROJECT_FOLDER)
PIPENV_IGNORE_VIRTUALENVS         ?= 0
PIPENV_IGNORE_VIRTUALENVS_ENV     := PIPENV_IGNORE_VIRTUALENVS=$(PIPENV_IGNORE_VIRTUALENVS)
PIPENV_VERBOSITY                  ?= -1
PIPENV_VERBOSITY_ENV              := PIPENV_VERBOSITY=$(PIPENV_VERBOSITY)
PIPENV_ENV					      ?= $(PIPENV_VENV_IN_PROJECT_FOLDER_ENV) $(PIPENV_IGNORE_VIRTUALENVS_ENV) $(PIPENV_VERBOSITY_ENV) PIPENV_COLORBLIND=1
PIPENV						      ?= $(PIPENV_ENV) pipenv
DEVELENV_SERVICE			      := $(DOCKER_SERVICES[0])

# Get the environment and import the settings.
# If the make target is pipeline-xxx, the environment is obtained from the target.
ifeq ($(patsubst pipeline-%,%,$(MAKECMDGOALS)),$(MAKECMDGOALS))
	ENVIRONMENT ?= pull
else
	override ENVIRONMENT := $(patsubst pipeline-%,%,$(MAKECMDGOALS))
endif

# Include envfile settings
ifeq (,$(wildcard ./.env))
else
	include .env
	export $(shell sed 's/=.*//' .env)
endif

# Shell settings
SHELL := bash
.ONESHELL:

define help
Usage: make <command>
Commands:
  help:              Show this help information
  clean:             Clean the project (remove build directory, clean golang packages and tidy go.mod file)
  install-lock:      Lock Pipenv dependencies into requirements for later use of pip to install them.
  install-pip:       Install application dependencies using pip.
  install:           Install application dependencies using Pipenv.
  build-test:        Pass linter, unit tests and coverage reports (in build/cover)
  build:			 Build application. Orchestrates: build-test
  login:             Docker login to publish and promote docker images
  package:           Create the docker image
  publish:           Publish the docker image in the docker repository
  deploy:            Deploy the application with ansible.
  run:               Launch the application
  pipeline-pull:     Launch pipeline to handle a pull request
  pipeline-dev:      Launch pipeline to handle the merge of a pull request
  pipeline:          Launch the pipeline for the selected environment
  ci-pipeline:       Start up a development environment to launch a pipeline. When the pipeline is completed, the development environment is shut down
  develenv-up:       Launch the development environment with a docker-compose of the service
  develenv-sh:       Access to a shell of the develenv service.
  develenv-down:     Stop the development environment
endef
export help

check-%:
	@if [ -z '${${*}}' ]; then echo 'Environment variable $* not set' && exit 1; fi

.PHONY: help
help:
	@echo "$$help"

.PHONY: clean
clean:
	$(info) 'Cleaning the project'
	rm -rf .venv/

.PHONY: install-lock
install-lock: Pipfile
	$(PIPENV) lock -r requirements.txt

.PHONY: install-pip
install-pip: install-lock
	pip install -r

.PHONY: install
install: Pipfile
	$(PIPENV) install

.PHONY: build-test
build-test: install
	# Linter
	$(info) 'Passing linter'
	$(PIPENV) run lint
	# Unit tests and coverage
	$(info) 'Passing unit tests and coverage'
	mkdir -p build/cover/cover_html
	$(PIPENV) run test-cov
	$(PIPENV) run report-html -d build/cover/cover_html
	$(PIPENV) run report-xml -o build/cover/cover.xml


.PHONY: build
build: build-test

.PHONY: package
package:
	$(info) 'Creating the docker image $(DOCKER_IMAGE):$(BUILD_VERSION)'
	docker build \
		--build-arg PRODUCT_VERSION='$(PRODUCT_VERSION)' \
		--build-arg PRODUCT_REVISION='$(PRODUCT_REVISION)' \
		-t '$(DOCKER_IMAGE):$(BUILD_VERSION)' .

.PHONY: login
login: check-DOCKER_PASSWORD
	$(info) 'Docker login with user $(DOCKER_USER) in $(DOCKER_REGISTRY)'
	echo $(DOCKER_PASSWORD) | docker login --username '$(DOCKER_USER)' --password-stdin '$(DOCKER_REGISTRY)'

.PHONY: publish
publish: login
	@for version in $(BUILD_VERSION) $(PRODUCT_VERSION) latest; do
		$(info) "Publishing the docker image: $(DOCKER_IMAGE):$$version"
		docker tag '$(DOCKER_IMAGE):$(BUILD_VERSION)' "$(DOCKER_IMAGE):$$version"
		docker push "$(DOCKER_IMAGE):$$version"
	done

.PHONY: deploy
deploy:
	$(info) 'Deploying the service $(DOCKER_PROJECT):$(BUILD_VERSION) in environment $(ENVIRONMENT)'

.PHONY: run
run:
	$(info) 'Launching the service'
	$(PIPENV) run python -m dle_rae_bot

.PHONY: pipeline-pull
pipeline-pull: build test-acceptance
	$(info) 'Completed successfully pipeline-pull'

.PHONY: pipeline-dev
pipeline-dev: build test-acceptance
	$(info) 'Completed successfully pipeline-dev'

.PHONY: pipeline
pipeline: pipeline-$(ENVIRONMENT)

.PHONY: ci-pipeline
ci-pipeline: check-PRODUCT_VERSION check-PRODUCT_REVISION
	$(info) 'Launching the CI pipeline for environment: $(ENVIRONMENT) and version: $(BUILD_VERSION)'
	function shutdown {
		rm -rf build/
		docker cp $$($(DOCKER_COMPOSE) -f docker-compose.yml ps -q develenv):/src/build . || true
		@for service in $(DOCKER_SERVICES); do \
			servicename="$(DOCKER_COMPOSE_PROJECT)"_"$$service"_"1"
			docker logs $$servicename > build/acceptance/logs/$$servicename.log
		done
		$(DOCKER_COMPOSE) -f docker-compose.yml down --remove-orphans
	}
	trap 'shutdown' EXIT

	# Export variables for creating the docker image for admin service with docker-compose
	export DOCKER_IMAGE='$(DOCKER_IMAGE):$(BUILD_VERSION)' \
		PRODUCT_VERSION='$(PRODUCT_VERSION)' \
		PRODUCT_REVISION='$(PRODUCT_REVISION)' \
		HOST_UID_GID='$(HOST_UID_GID)'

	# Start up the development environment disabling the default port mapping in the host
	# and using the target "build" because mounting a volume could fail if the docker engine
	# is remote. This is done by excluding docker-compose.override.yml
	$(DOCKER_COMPOSE) -f docker-compose.yml up --build -d

	# In CI, disable TTY in docker-compose with option -T
	$(DOCKER_COMPOSE) -f docker-compose.yml exec -T develenv make pipeline-$(ENVIRONMENT)

.PHONY: develenv-up
develenv-up:
	$(info) 'Launching the development environment: $(PRODUCT_VERSION)-$(PRODUCT_REVISION)'
	$(DOCKER_COMPOSE) up --build -d

.PHONY: develenv-sh
develenv-sh:
	$(DOCKER_COMPOSE) exec $(DEVELENV_SERVICE) bash

.PHONY: develenv-down
develenv-down:
	$(info) 'Shutting down the development environment'
	$(DOCKER_COMPOSE) down --remove-orphans --volumes

# Functions
info := @printf '\033[32;01m%s\033[0m\n'
get_packages := $$(go list ./... | grep -v test/acceptance)
