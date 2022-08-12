#!/usr/bin/make -f

# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to title 17 Section 105 of the
# United States Code this software is not subject to copyright
# protection and is in the public domain. NIST assumes no
# responsibility whatsoever for its use by other parties, and makes
# no guarantees, expressed or implied, about its quality,
# reliability, or any other characteristic.
#
# We would appreciate acknowledgement if the software is used.

SHELL := /bin/bash

PYTHON3 ?= $(shell which python3.9 2>/dev/null || which python3.8 2>/dev/null || which python3.7 2>/dev/null || which python3.6 2>/dev/null || which python3)

GSED ?= $(shell which gsed 2>/dev/null || which sed)

all: \
  .venv-pre-commit/var/.pre-commit-built.log \
  README.md

.PHONY: \
  download

README.md: \
  .generated-README.md
	diff \
	  README.md \
	  .generated-README.md \
	  || (echo "UPDATE:Makefile:The generated README.md does not match the Git-tracked README.md.  If the above reported changes look fine, run 'cp .generated-README.md README.md' to get a file ready to commit to Git." >&2 ; exit 1)
	test -r $@ && touch $@

.generated-README.md: \
  README.md.in \
  README.md.sed \
  tests/ex-triangle-inheritance.ttl \
  tests/ex-triangle-1-1.ttl \
  tests/ex-triangle-1-2.ttl \
  tests/ex-triangle-2.ttl \
  tests/kb-test-1.ttl \
  tests/kb-test-2.ttl \
  tests/kb-test-3.ttl \
  tests/kb-test-4.ttl \
  tests/kb-test-5.ttl \
  tests/kb-test-6.ttl \
  tests/kb-triangle-1.ttl \
  tests/kb-triangle-2.ttl \
  tests/kb-triangle-3.ttl \
  tests/kb-triangle-3-super.ttl
	$(GSED) \
	  -f README.md.sed \
	  README.md.in \
	  > $@_
	mv $@_ $@

.lib.done.log:
	$(MAKE) \
	  --directory lib
	touch $@

# This virtual environment is meant to be built once and then persist, even through 'make clean'.
# If a recipe is written to remove this flag file, it should first run `pre-commit uninstall`.
.venv-pre-commit/var/.pre-commit-built.log:
	rm -rf .venv-pre-commit
	test -r .pre-commit-config.yaml \
	  || (echo "ERROR:Makefile:pre-commit is expected to install for this repository, but .pre-commit-config.yaml does not seem to exist." >&2 ; exit 1)
	$(PYTHON3) -m venv \
	  .venv-pre-commit
	source .venv-pre-commit/bin/activate \
	  && pip install \
	    --upgrade \
	    pip \
	    setuptools \
	    wheel
	source .venv-pre-commit/bin/activate \
	  && pip install \
	    pre-commit
	source .venv-pre-commit/bin/activate \
	  && pre-commit install
	mkdir -p \
	  .venv-pre-commit/var
	touch $@

# After running unit tests, see if README.md needs to be regenerated.
check: \
  .venv-pre-commit/var/.pre-commit-built.log \
  .lib.done.log
	$(MAKE) \
	  PYTHON3=$(PYTHON3) \
	  --directory tests \
	  check
	$(MAKE) \
	  README.md

clean:
	@rm -f \
	  .lib.done.log
	@rm -rf \
	  *.egg-info \
	  case_shacl_inheritance_reviewer/__pycache__
	@$(MAKE) \
	  --directory tests \
	  clean

download: \
  .lib.done.log \
  .venv-pre-commit/var/.pre-commit-built.log
	$(MAKE) \
	  PYTHON3=$(PYTHON3) \
	  --directory tests \
	  download
