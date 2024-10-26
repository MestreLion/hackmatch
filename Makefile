# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
# -----------------------------------------------------------------------------
# Inspired by https://venthur.de/2021-03-31-python-makefiles.html

# For customizing defaults, such as PYTHON
-include .env

# TODO: add SLUG to avoid hard-coding project name

## PYTHON: System python, used to create the virtual environment
PYTHON   ?= python3
## ENV_DIR: Path to the virtual environment, absolute or relative to current dir
ENV_DIR  ?= venv
## PROF_DIR: Path to profiling dir, where .pstats and .dot files are generated
PROF_DIR ?= profile

# Derived vars:
# path to virtual environment bin dir
venv    := $(ENV_DIR)/bin
# path to virtual environment python executable
python  := $(venv)/python
# path to virtual environment pip executable
pip     := $(venv)/pip
# paths to profiling stats file and dot graph
now      := $(shell date '+%Y%m%d%H%M%S')
pstats   := $(PROF_DIR)/hackmatch_$(now).pstats
dotgraph := $(PROF_DIR)/hackmatch_$(now).dot
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
	$(venv)/twine upload --repository hackmatch -- dist/*

## - profile: Generate and open Dot graph at $PROF_DIR with `cProfile` and `gprof2dot`
profile: $(dotgraph)
$(PROF_DIR)/.gitignore:
	mkdir -p -- $(PROF_DIR)
	echo '*' > $(PROF_DIR)/.gitignore
$(dotgraph): $(venv)/gprof2dot $(venv)/xdot $(PROF_DIR)/.gitignore
	$(python) -m cProfile -o $(pstats) -m hackmatch -q --benchmark
	$(venv)/gprof2dot -f pstats -o $@ -- $(pstats)
	# TODO: test for desktop-registered with xdg-mime and use xdg-open
	$(venv)/xdot $@

## - system-packages: apt-install system pre-dependencies `python3-{tk,dev,venv}`
system-packages:
	# I'm *sure* there's a better way of doing this... my make-fu is weak, PRs welcome!
	$(call is_installed,python3-tk)               || sudo apt install python3-tk
	$(call is_installed,$(notdir $(PYTHON))-dev)  || sudo apt install $(notdir $(PYTHON))-dev
	$(call is_installed,$(notdir $(PYTHON))-venv) || sudo apt install $(notdir $(PYTHON))-venv
define is_installed
	[ -n "$(shell dpkg-query --showformat='$${Version}' --show "${1}" 2>/dev/null || true)" ]
endef

$(venv): pyproject.toml
	$(PYTHON) -m venv $(ENV_DIR)
	$(python) -m pip --disable-pip-version-check install --upgrade pip
	$(pip) install --upgrade setuptools build twine
	$(pip) install --upgrade -e .[dev,extra]
	touch -- $(venv)

.PHONY: default run format check build upload profile system-packages
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

$(venv)/%: | venv
	$(pip) install --upgrade $*
	touch -- $@

.PHONY: venv venv-clean python ipython bash clean clean-all help
