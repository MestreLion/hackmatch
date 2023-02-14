# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
# -----------------------------------------------------------------------------
# Inspired by https://venthur.de/2021-03-31-python-makefiles.html

# For customizing defaults, such as PYTHON
include .env

## PYTHON: System python, used to create the virtual environment
PYTHON  ?= python3
## ENV_DIR: Path to the virtual environment, absolute or relative to current dir
ENV_DIR ?= venv

# Derived vars:
# path to virtual environment bin dir
venv    := $(ENV_DIR)/bin
# path to virtual environment python executable
python  := $(venv)/python
# path to virtual environment pip executable
pip     := $(venv)/pip

# -----------------------------------------------------------------------------
## - default: format and check
default: format check

## - run: run project
run: venv
	# alternative: exec $(python) -m hackmatch
	exec $(venv)/hackmatch-bot

## - style: apply `black` formatter
format: venv
	$(venv)/black .

## - check: invoke `mypy` static type checker
check: venv
	$(venv)/mypy

## - build: build sdist and wheel packages using PyPA's `build` module
build: venv default
	$(python) -m build

## - upload: upload built packages to PyPI using `twine`
upload: venv build
	$(venv)/twine upload dist/*

$(venv): pyproject.toml
	$(PYTHON) -m venv $(ENV_DIR)
	$(python) -m pip install --upgrade pip
	$(pip) install --upgrade setuptools wheel build twine
	$(pip) install --upgrade -e .[dev,extra]
	touch -- $(venv)

.PHONY: default style check build upload clean clean-all

# -----------------------------------------------------------------------------
## - venv: create a virtual environment in $ENV_DIR, by default `./venv`
venv: $(venv)

## - venv-clean: remove the virtual environment
venv-clean:
	rm -rf $(ENV_DIR)

## - python: run Python interactive interpreter
python: venv
	exec $(python)

## - ipython: run IPython interactive interpreter
ipython: $(venv)/ipython
	exec $(venv)/ipython

## - bash: run bash subshell in the virtual environment
bash: venv
	. $(venv)/activate && exec bash

## - clean: remove build artifacts
clean:
	rm -rf *.egg-info

## - clean-all: remove build artifacts and the virtual environment
clean-all: clean venv-clean

## - help: display this message
help:
	@echo "Available env vars and targets:"
	@sed -n 's/^.*##[ ]//p' Makefile

$(venv)/%: venv
	$(pip) install --upgrade $*
	touch -- $@

.PHONY: venv venv-clean python ipython shell bash help
