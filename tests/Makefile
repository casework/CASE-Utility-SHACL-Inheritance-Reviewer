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

top_srcdir := $(shell cd .. ; pwd)

rdf_toolkit_jar := $(top_srcdir)/lib/rdf-toolkit.jar

# These files are needed for the top README.
all: \
  ex-triangle-inheritance.ttl \
  kb-test-1.ttl \
  kb-test-2.ttl \
  kb-test-3.ttl \
  kb-test-4.ttl \
  kb-test-5.ttl \
  kb-test-6.ttl \
  kb-test-7.ttl \
  kb-test-8.ttl

.PHONY: \
  check-cli-xfails \
  check-pytest \
  download

.PRECIOUS: \
  %_inheritance.ttl

# rdf-toolkit.jar is used to normalize generated Turtle content, to reduce on noise in the Git history.
%_inheritance.ttl: \
  %_ontology.ttl \
  $(top_srcdir)/.lib.done.log \
  $(top_srcdir)/case_shacl_inheritance_reviewer/__init__.py \
  .venv.done.log
	source venv/bin/activate \
	  && case_shacl_inheritance_reviewer \
	    __$@ \
	    $<
	java -jar $(rdf_toolkit_jar) \
	  --infer-base-iri \
	  --inline-blank-nodes \
	  --source __$@ \
	  --source-format turtle \
	  --target _$@ \
	  --target-format turtle
	rm __$@
	mv _$@ $@

$(top_srcdir)/.lib.done.log:
	@echo "ERROR:tests/Makefile:Please run 'make check' from the top source directory before running 'make check' under the tests directory." >&2
	exit 1

.venv.done.log: \
  $(top_srcdir)/setup.cfg \
  $(top_srcdir)/setup.py \
  requirements.txt
	rm -rf venv
	$(PYTHON3) -m venv \
	  venv
	source venv/bin/activate \
	  && pip install \
	    --upgrade \
	    pip \
	    setuptools
	source venv/bin/activate \
	  && pip install \
	    --editable \
	      $(top_srcdir)
	source venv/bin/activate \
	  && pip install \
	    --requirement requirements.txt
	touch $@

# This CLI test confirms an output file existing causes the execution to halt.
.xfail-out_graph.done.log: \
  $(top_srcdir)/case_shacl_inheritance_reviewer/__init__.py \
  .venv.done.log
	rm -f .xpass-out_graph.log
	( \
	  source venv/bin/activate \
	    && case_shacl_inheritance_reviewer \
	      Makefile \
	      kb-test-1.ttl \
	      && touch .xpass-out_graph.log \
	) || true
	test ! -r .xpass-out_graph.log
	touch $@

# This CLI test confirms the 'strict' flag and a discovered shape broadening error causes the execution to halt.
.xfail-strict.done.log: \
  $(top_srcdir)/case_shacl_inheritance_reviewer/__init__.py \
  .venv.done.log \
  ex-triangle.ttl
	rm -f \
	  .xfail-strict.ttl \
	  .xpass-strict.log
	( \
	  source venv/bin/activate \
	    && case_shacl_inheritance_reviewer \
	      --strict \
	      .xfail-strict.ttl \
	      ex-triangle.ttl \
	      && touch .xpass-strict.log \
	) || true
	test -r .xfail-strict.ttl
	test ! -r .xpass-strict.log
	touch $@

check: \
  check-mypy \
  check-cli-xfails \
  check-pytest

# These two targets are made only if the program fails under expected conditions.
check-cli-xfails: \
  .xfail-out_graph.done.log \
  .xfail-strict.done.log

check-mypy: \
  .venv.done.log
	source venv/bin/activate \
	  && mypy \
	    --exclude venv \
	    --strict \
	    $(top_srcdir)/case_shacl_inheritance_reviewer \
	    .

check-pytest: \
  PASS_class_inheritance.ttl \
  PASS_datatype_inheritance.ttl \
  PASS_maxCount_inheritance.ttl \
  PASS_minCount_inheritance.ttl \
  PASS_path_inheritance.ttl \
  PASS_subprop_inheritance.ttl \
  XFAIL_class_inheritance.ttl \
  XFAIL_maxCount_inheritance.ttl \
  XFAIL_minCount_inheritance.ttl \
  XFAIL_path_inheritance.ttl \
  XFAIL_subprop_inheritance.ttl \
  ex-triangle-inheritance.ttl \
  kb-test-1.ttl \
  kb-test-2.ttl \
  kb-test-3.ttl \
  kb-test-4.ttl \
  kb-test-5.ttl \
  kb-test-6.ttl \
  kb-test-7.ttl \
  kb-test-8.ttl
	source venv/bin/activate \
	  && pytest \
	    --log-level=DEBUG \
	    --verbose \
	    --verbose

clean:
	@rm -rf \
	  .pytest_cache \
	  __pycache__
	@rm -f \
	  .*.done.log \
	  .xfail* \
	  .xpass* \
	  _*
	@rm -rf \
	  venv

download: \
  .venv.done.log

ex-triangle.ttl: \
  $(top_srcdir)/.lib.done.log \
  .venv.done.log \
  ex-triangle-1-1.ttl \
  ex-triangle-1-2.ttl \
  ex-triangle-2.ttl \
  ex_ttl.py
	source venv/bin/activate \
	  && python ex_ttl.py \
	    __$@ \
	    ex-triangle-1-1.ttl \
	    ex-triangle-1-2.ttl \
	    ex-triangle-2.ttl
	java -jar $(rdf_toolkit_jar) \
	  --infer-base-iri \
	  --inline-blank-nodes \
	  --source __$@ \
	  --source-format turtle \
	  --target _$@ \
	  --target-format turtle
	rm __$@
	mv _$@ $@

ex-triangle-inheritance.ttl: \
  $(top_srcdir)/.lib.done.log \
  $(top_srcdir)/case_shacl_inheritance_reviewer/__init__.py \
  ex-triangle.ttl
	source venv/bin/activate \
	  && case_shacl_inheritance_reviewer \
	    __$@ \
	    ex-triangle.ttl
	java -jar $(rdf_toolkit_jar) \
	  --infer-base-iri \
	  --inline-blank-nodes \
	  --source __$@ \
	  --source-format turtle \
	  --target _$@ \
	  --target-format turtle
	rm __$@
	mv _$@ $@

kb-test-1.ttl: \
  .venv.done.log \
  ex-triangle-1-2.ttl \
  kb-triangle-1.ttl
	source venv/bin/activate \
	  && pyshacl \
	    --data-file-format turtle \
	    --format turtle \
	    --output _$@ \
	    --shacl ex-triangle-1-2.ttl \
	    --shacl-file-format turtle \
	    kb-triangle-1.ttl
	mv _$@ $@

kb-test-2.ttl: \
  .venv.done.log \
  ex-triangle-1-2.ttl \
  kb-triangle-2.ttl
	source venv/bin/activate \
	  && pyshacl \
	    --data-file-format turtle \
	    --format turtle \
	    --output _$@ \
	    --shacl ex-triangle-1-2.ttl \
	    --shacl-file-format turtle \
	    kb-triangle-2.ttl \
	    || true    #xfail
	mv _$@ $@

kb-test-3.ttl: \
  .venv.done.log \
  ex-triangle-2.ttl \
  kb-triangle-3.ttl
	source venv/bin/activate \
	  && pyshacl \
	    --data-file-format turtle \
	    --format turtle \
	    --output _$@ \
	    --shacl ex-triangle-2.ttl \
	    --shacl-file-format turtle \
	    kb-triangle-3.ttl
	mv _$@ $@

kb-test-4.ttl: \
  .venv.done.log \
  ex-triangle.ttl \
  kb-triangle-3.ttl
	source venv/bin/activate \
	  && pyshacl \
	    --data-file-format turtle \
	    --format turtle \
	    --output _$@ \
	    --shacl ex-triangle.ttl \
	    --shacl-file-format turtle \
	    kb-triangle-3.ttl
	mv _$@ $@

kb-test-5.ttl: \
  .venv.done.log \
  ex-triangle.ttl \
  kb-triangle-3-super.ttl
	source venv/bin/activate \
	  && pyshacl \
	    --data-file-format turtle \
	    --format turtle \
	    --output _$@ \
	    --shacl ex-triangle.ttl \
	    --shacl-file-format turtle \
	    kb-triangle-3-super.ttl \
	    || true    #xfail
	mv _$@ $@

kb-test-6.ttl: \
  .venv.done.log \
  ex-triangle.ttl \
  kb-triangle-3.ttl
	source venv/bin/activate \
	  && pyshacl \
	    --data-file-format turtle \
	    --format turtle \
	    --ont-file-format turtle \
	    --ont-graph ex-triangle.ttl \
	    --output _$@ \
	    --shacl ex-triangle.ttl \
	    --shacl-file-format turtle \
	    kb-triangle-3.ttl \
	    || true    #xfail
	mv _$@ $@

kb-test-7.ttl: \
  .venv.done.log \
  ex-triangle.ttl \
  kb-triangle-3.ttl
	source venv/bin/activate \
	  && pyshacl \
	    --advanced \
	    --data-file-format turtle \
	    --format turtle \
	    --inference both \
	    --iterate-rules \
	    --metashacl \
	    --ont-file-format turtle \
	    --ont-graph ex-triangle.ttl \
	    --output _$@ \
	    --shacl ex-triangle.ttl \
	    --shacl-file-format turtle \
	    kb-triangle-3.ttl \
	    || true    #xfail
	mv _$@ $@

# Normalize at least this file due to sort order not being guaranteed.
kb-test-8.ttl: \
  .venv.done.log \
  ex-constraint-repetition.ttl \
  kb-triangle-4.ttl
	source venv/bin/activate \
	  && pyshacl \
	    --data-file-format turtle \
	    --format turtle \
	    --ont-file-format turtle \
	    --ont-graph ex-constraint-repetition.ttl \
	    --output __$@ \
	    --shacl ex-constraint-repetition.ttl \
	    --shacl-file-format turtle \
	    kb-triangle-4.ttl \
	    || true    #xfail
	java -jar $(rdf_toolkit_jar) \
	  --infer-base-iri \
	  --inline-blank-nodes \
	  --source __$@ \
	  --source-format turtle \
	  --target _$@ \
	  --target-format turtle
	rm __$@
	mv _$@ $@
