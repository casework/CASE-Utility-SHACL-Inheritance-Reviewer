#!/usr/bin/python

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

"""
This script was written to run unit tests in the pytest framework.
"""

import glob
import logging
import os
import typing

import pytest
import rdflib.plugins.sparql

_logger = logging.getLogger(os.path.basename(__file__))

NS_EX = rdflib.Namespace("http://example.org/ontology/example/")
NS_SH = rdflib.SH
NS_SHIR = rdflib.Namespace("http://example.org/ontology/shacl-inheritance-review/")


def load_and_check_graph(
    basename: str,
    required_conformance: bool,
    conformance_mismatch_expectation: typing.Optional[str] = None,
) -> rdflib.Graph:
    graph = rdflib.Graph()
    graph_filepath = os.path.join(os.path.dirname(__file__), basename)
    graph.parse(graph_filepath, format="turtle")
    conforms = None
    for triple in graph.triples((None, NS_SH.conforms, None)):
        assert conforms is None, "Found second result."
        conforms = triple[2].toPython()

    if conformance_mismatch_expectation is None:
        assert conforms == required_conformance
    else:
        try:
            assert conforms == required_conformance
            raise ValueError("XPASS - Was expecting failure.")
        except AssertionError:
            pytest.xfail(conformance_mismatch_expectation)
    return graph


def load_ontology_graph(basename: str) -> rdflib.Graph:
    graph = rdflib.Graph()
    graph_filepath = os.path.join(os.path.dirname(__file__), basename)
    graph.parse(graph_filepath, format="turtle")
    return graph


def test_coverage():
    # Ground truth:
    # * There is an expected set of IRIs of error classes emitted by the reports.
    expected = {
        str(NS_SHIR["PropertyShapeComponentBroadenedError-class"]),
        str(NS_SHIR["PropertyShapeComponentBroadenedError-datatype"]),
        str(NS_SHIR["PropertyShapeComponentBroadenedError-maxCount"]),
        str(NS_SHIR["PropertyShapeComponentBroadenedError-minCount"]),
        str(NS_SHIR["PropertyShapeComponentBroadenedError-path"]),
        str(NS_SHIR["PropertyShapeComponentDroppedError-class"]),
        str(NS_SHIR["PropertyShapeComponentDroppedError-datatype"]),
        str(NS_SHIR["PropertyShapeComponentDroppedError-maxCount"]),
        str(NS_SHIR["PropertyShapeComponentDroppedError-minCount"]),
    }
    computed = set()

    graph = rdflib.Graph()
    srcdir = os.path.dirname(__file__)

    # Load XFAIL reports.
    for inheritance_ttl in sorted(
        glob.glob(os.path.join(srcdir, "XFAIL_*_inheritance.ttl"))
    ):
        _logger.debug("inheritance_ttl = %r.", inheritance_ttl)
        basename = os.path.basename(inheritance_ttl)
        tmp_graph = load_and_check_graph(basename, False)
        graph += tmp_graph

    query = rdflib.plugins.sparql.prepareQuery(
        """\
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX shir: <http://example.org/ontology/shacl-inheritance-review/>

SELECT ?nClass
WHERE {
  ?nReport
    a shir:InheritanceValidationReport ;
    sh:result/a ?nClass ;
    .
}
"""
    )
    for result in graph.query(query):
        n_class = result[0]
        computed.add(str(n_class))

    try:
        assert expected == computed
    except AssertionError:
        if computed - expected != set():
            raise
        if expected - computed == {
            str(NS_SHIR["PropertyShapeComponentBroadenedError-datatype"])
        }:
            pytest.xfail(
                "At this time, the broadened-on-datatype test has not been specified."
            )
    raise ValueError(
        "XPASS - Since original writing, the broadened-on-datatype test has been specified and should be reviewed for the test_coverage function."
    )


def _test_inheritance_xfail_from_inlined_ground_truth(
    ontology_basename: str, inheritance_basename: str
):
    ontology_graph = load_ontology_graph(ontology_basename)
    inheritance_graph = load_and_check_graph(inheritance_basename, False)
    expected = set()
    computed = set()

    expected_query = rdflib.plugins.sparql.prepareQuery(
        """\
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX shir: <http://example.org/ontology/shacl-inheritance-review/>

SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath ?nErrorClass
WHERE {
  ?nClassNodeShape
    a sh:NodeShape ;
    shir:shouldTriggerBroadeningError ?nExpectedError ;
    .

  ?nExpectedError
    a ?nErrorClass ;
    sh:resultPath ?nSuperclassPropertyShapePath ;
    sh:sourceShape ?nSuperclassPropertyShape ;
    rdfs:seeAlso ?nSuperclassNodeShape ;
    .
  OPTIONAL {
    ?nExpectedError
      sh:value ?nClassPropertyShape ;
      .
    ?nClassPropertyShape
      sh:path ?nClassPropertyShapePath
  }
}
"""
    )
    for result in ontology_graph.query(expected_query):
        (
            n_class_node_shape,
            n_class_property_shape,
            n_class_property_shape_path,
            n_superclass_node_shape,
            n_superclass_property_shape,
            n_superclass_property_shape_path,
            n_error_class,
        ) = result
        expected.add(
            (
                n_error_class.toPython(),
                n_class_node_shape.toPython(),
                n_superclass_node_shape.toPython(),
                n_superclass_property_shape_path.toPython(),
            )
        )

    computed_query = rdflib.plugins.sparql.prepareQuery(
        """\
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX shir: <http://example.org/ontology/shacl-inheritance-review/>

SELECT ?nClassNodeShape ?nSuperclassNodeShape ?nSuperclassPropertyShapePath ?nErrorClass
WHERE {
  ?nReport
    a shir:InheritanceValidationReport ;
    sh:result ?nResult ;
    .

  ?nResult
    a ?nErrorClass ;
    rdfs:seeAlso ?nSuperclassNodeShape ;
    sh:focusNode ?nClassNodeShape ;
    sh:resultPath ?nSuperclassPropertyShapePath ;
    sh:sourceShape ?nSuperclassPropertyShape ;
    .

  ?nSuperclassPropertyShape
    sh:path ?nSuperclassPropertyShapePath ;
    .
}
"""
    )
    for result in inheritance_graph.query(computed_query):
        (
            n_class_node_shape,
            n_superclass_node_shape,
            n_superclass_property_shape_path,
            n_error_class,
        ) = result
        computed.add(
            (
                n_error_class.toPython(),
                n_class_node_shape.toPython(),
                n_superclass_node_shape.toPython(),
                n_superclass_property_shape_path.toPython(),
            )
        )
    assert expected == computed


def test_kb_test_1():
    g = load_and_check_graph("kb-test-1.ttl", True)
    assert isinstance(g, rdflib.Graph)


def test_kb_test_2():
    g = load_and_check_graph("kb-test-2.ttl", False)
    assert isinstance(g, rdflib.Graph)


def test_kb_test_3():
    g = load_and_check_graph("kb-test-3.ttl", True)
    assert isinstance(g, rdflib.Graph)


def test_kb_test_4():
    g = load_and_check_graph(
        "kb-test-4.ttl",
        False,
        "When this was written, pyshacl was known to disagree with test developer's subclass--shape expectations from combined shapes+ontology file.",
    )
    assert isinstance(g, rdflib.Graph)


def test_kb_test_5():
    g = load_and_check_graph("kb-test-5.ttl", False)
    assert isinstance(g, rdflib.Graph)


def test_kb_test_6():
    g = load_and_check_graph("kb-test-6.ttl", False)
    assert isinstance(g, rdflib.Graph)


def test_kb_test_7():
    g = load_and_check_graph(
        "kb-test-7.ttl",
        False,
        "When this was written, pyshacl was known to not report ontology-level errors before reporting instance data-level errors.",
    )
    assert isinstance(g, rdflib.Graph)
    raise NotImplementedError(
        "Test lacking exemplar for reporting ontology-level error."
    )


def test_pass_class():
    g = load_and_check_graph("PASS_class_inheritance.ttl", True)
    assert isinstance(g, rdflib.Graph)


def test_pass_datatype():
    g = load_and_check_graph("PASS_datatype_inheritance.ttl", True)
    assert isinstance(g, rdflib.Graph)


def test_pass_maxCount():
    g = load_and_check_graph("PASS_maxCount_inheritance.ttl", True)
    assert isinstance(g, rdflib.Graph)


def test_pass_minCount():
    g = load_and_check_graph("PASS_minCount_inheritance.ttl", True)
    assert isinstance(g, rdflib.Graph)


def test_pass_path():
    g = load_and_check_graph("PASS_path_inheritance.ttl", True)
    assert isinstance(g, rdflib.Graph)


def test_pass_subprop():
    g = load_and_check_graph("PASS_path_inheritance.ttl", True)
    assert isinstance(g, rdflib.Graph)


def test_xfail_class_inheritance():
    _test_inheritance_xfail_from_inlined_ground_truth(
        "XFAIL_class_ontology.ttl", "XFAIL_class_inheritance.ttl"
    )


def test_xfail_datatype_inheritance():
    _test_inheritance_xfail_from_inlined_ground_truth(
        "XFAIL_datatype_ontology.ttl", "XFAIL_datatype_inheritance.ttl"
    )


def test_xfail_maxCount_inheritance():
    _test_inheritance_xfail_from_inlined_ground_truth(
        "XFAIL_maxCount_ontology.ttl", "XFAIL_maxCount_inheritance.ttl"
    )


def test_xfail_minCount_inheritance():
    _test_inheritance_xfail_from_inlined_ground_truth(
        "XFAIL_minCount_ontology.ttl", "XFAIL_minCount_inheritance.ttl"
    )


def test_xfail_path_inheritance():
    _test_inheritance_xfail_from_inlined_ground_truth(
        "XFAIL_path_ontology.ttl", "XFAIL_path_inheritance.ttl"
    )


def test_xfail_subprop_inheritance():
    _test_inheritance_xfail_from_inlined_ground_truth(
        "XFAIL_subprop_ontology.ttl", "XFAIL_subprop_inheritance.ttl"
    )


def test_ex_triangle_inheritance():
    g = load_and_check_graph("ex-triangle-inheritance.ttl", False)
    assert isinstance(g, rdflib.Graph)
