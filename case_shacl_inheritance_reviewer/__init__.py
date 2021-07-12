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

__version__ = "0.1.0"

import argparse
import logging
import os

import rdflib.plugins.sparql
import rdflib.util

_logger = logging.getLogger(os.path.basename(__file__))

NS_RDF = rdflib.RDF
NS_RDFS = rdflib.RDFS
NS_SH = rdflib.SH
NS_SHIR = rdflib.Namespace("http://example.org/ontology/shacl-inheritance-review/")

class ConformanceError(Exception):
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Exit in an error state if any inheritance errors are reported (i.e. if conforms==False).  (The error report in out_graph will still be intact.)")
    parser.add_argument("--verbose", action="store_true", help="Augment debug log messages with timestamps.")
    parser.add_argument("out_graph", help="Output file.  Required to not exist.")  # Requirement is to prevent accidental overwrite of inputs.
    parser.add_argument("in_graph", nargs="+")
    args = parser.parse_args()

    if os.path.exists(args.out_graph):
        raise ValueError("File found where output graph was going to be written.  Please ensure first positional argument is a currently non-existent output file.")

    logging_kwargs = dict()
    logging_kwargs["level"] = logging.DEBUG if args.debug else logging.INFO
    logging_kwargs["format"] = "%(asctime)s:" + logging.BASIC_FORMAT if args.verbose else logging.BASIC_FORMAT
    logging.basicConfig(**logging_kwargs)

    # Initialize output graph, and add carrying-documentation triple denoting what an InheritanceValidationReport is.
    out_graph = rdflib.Graph()
    out_graph.namespace_manager.bind("sh", NS_SH)
    out_graph.namespace_manager.bind("shir", NS_SHIR)

    # Add anchoring report node.
    n_report = rdflib.BNode()
    out_graph.add((
      n_report,
      NS_RDF.type,
      NS_SHIR.InheritanceValidationReport
    ))

    # Initialize and load input graph.
    in_graph = rdflib.Graph()
    for in_graph_filepath in args.in_graph:
        _logger.debug("Loading graph in %r...", in_graph_filepath)
        in_graph.parse(in_graph_filepath, format=rdflib.util.guess_format(in_graph_filepath))
        _logger.debug("Loaded.")
    nsdict = {k:v for (k,v) in in_graph.namespace_manager.namespaces()}

    for prefix in nsdict:
        out_graph.namespace_manager.bind(prefix, nsdict[prefix])

    # Members: Triples, fit for argument to rdflib.Graph.triples().
    triple_patterns_to_link = set()

    # Explain known "sub-shape" issues.
    # Key: String of IRI of SHIR error class.
    # Value: Tuple.
    #   0: Error message.
    #   1: SPARQL query to find all applicable instances for error message.
    error_class_iri_to_message_and_query = dict()

    message_string = "Subclass (sh:focusNode) is missing property shape (sh:sourceShape) from superclass, according to property in source's sh:path (sh:resultPath)."
    query_string = """\
SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath
WHERE {
  ?nSuperclassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    sh:property ?nSuperclassPropertyShape ;
    .

  ?nClassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    rdfs:subClassOf+ ?nSuperclassNodeShape ;
    .

  ?nSuperclassPropertyShape
    sh:path ?nSuperclassPropertyShapePath ;
    .

  FILTER NOT EXISTS {
    ?nClassNodeShape
      sh:property/sh:path ?nClassPropertyShapePath ;
      .
    ?nClassPropertyShapePath
      rdfs:subPropertyOf* ?nSuperclassPropertyShapePath ;
      .
  }
}
"""
    error_class_iri_to_message_and_query[str(NS_SHIR["PropertyShapeDroppedError"])] = (message_string, query_string)

    message_string = "Subclass (sh:focusNode) has property shape (sh:value) of ancestor class (rdfs:seeAlso) that has sh:path to superproperty of ancestor class's property shape (sh:sourceShape)."
    query_string = """\
SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath
WHERE {
  ?nSuperclassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    sh:property ?nSuperclassPropertyShape ;
    .

  ?nSuperclassPropertyShape
    sh:path ?nSuperclassPropertyShapePath ;
    .

  ?nClassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    rdfs:subClassOf+ ?nSuperclassNodeShape ;
    sh:property ?nClassPropertyShape ;
    .

  ?nClassPropertyShape
    sh:path ?nClassPropertyShapePath ;
    .

  ?nSuperclassPropertyShapePath
    rdfs:subPropertyOf+ ?nClassPropertyShapePath ;
    .
}
"""
    error_class_iri_to_message_and_query[str(NS_SHIR["PropertyShapeComponentBroadenedError-path"])] = (message_string, query_string)

    message_string = "Subclass (sh:focusNode) has property shape (sh:value) corresponding with an ancestor class's (rdfs:seeAlso) property shape (sh:sourceShape).  However, the sh:class references on the two property shapes are inverted - the subclass shape's sh:class is a superclass of the ancestor class property shape's sh:class."
    query_string = """\
SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath
WHERE {
  ?nSuperclassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    sh:property ?nSuperclassPropertyShape ;
    .

  ?nSuperclassPropertyShape
    sh:class ?nSuperclassPropertyShapeClass ;
    sh:path ?nSuperclassPropertyShapePath ;
    .

  ?nClassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    rdfs:subClassOf+ ?nSuperclassNodeShape ;
    sh:property ?nClassPropertyShape ;
    .

  ?nClassPropertyShape
    sh:class ?nClassPropertyShapeClass ;
    sh:path ?nClassPropertyShapePath ;
    .

  ?nClassPropertyShapePath
    rdfs:subPropertyOf* ?nSuperclassPropertyShapePath ;
    .

  ?nSuperclassPropertyShapeClass
    rdfs:subClassOf+ ?nClassPropertyShapeClass ;
    .
}
"""
    error_class_iri_to_message_and_query[str(NS_SHIR["PropertyShapeComponentBroadenedError-class"])] = (message_string, query_string)

    message_string = "Subclass (sh:focusNode) has property shape (sh:value) corresponding with an ancestor class's (rdfs:seeAlso) property shape (sh:sourceShape).  But, the subclass's property shape is missing its sh:class."
    query_string = """\
SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath
WHERE {
  ?nSuperclassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    sh:property ?nSuperclassPropertyShape ;
    .

  ?nSuperclassPropertyShape
    sh:class ?nSuperclassPropertyShapeClass  ;
    sh:path ?nSuperclassPropertyShapePath ;
    .

  ?nClassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    rdfs:subClassOf+ ?nSuperclassNodeShape ;
    sh:property ?nClassPropertyShape ;
    .

  ?nClassPropertyShape
    sh:path ?nClassPropertyShapePath ;
    .

  ?nClassPropertyShapePath
    rdfs:subPropertyOf* ?nSuperclassPropertyShapePath ;
    .

  FILTER NOT EXISTS {
    ?nClassPropertyShape
      sh:class ?nClassPropertyShapeClass ;
      .
  }
}
"""
    error_class_iri_to_message_and_query[str(NS_SHIR["PropertyShapeComponentDroppedError-class"])] = (message_string, query_string)

    message_string = "Subclass (sh:focusNode) has property shape (sh:value) from ancestor class (rdfs:seeAlso), but according to ancestor property shape (sh:sourceShape) dropped its sh:datatype."
    query_string = """\
SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath
WHERE {
  ?nSuperclassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    sh:property ?nSuperclassPropertyShape ;
    .

  ?nSuperclassPropertyShape
    sh:datatype ?nSuperclassPropertyShapeDatatype ;
    sh:path ?nSuperclassPropertyShapePath ;
    .

  ?nClassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    rdfs:subClassOf+ ?nSuperclassNodeShape ;
    sh:property ?nClassPropertyShape ;
    .

  ?nClassPropertyShape
    sh:path ?nClassPropertyShapePath ;
    .

  ?nClassPropertyShapePath
    rdfs:subPropertyOf* ?nSuperclassPropertyShapePath ;
    .

  FILTER NOT EXISTS {
    ?nClassPropertyShape
      sh:datatype ?nClassPropertyShapeDatatype ;
      .
  }
}
"""
    error_class_iri_to_message_and_query[str(NS_SHIR["PropertyShapeComponentDroppedError-datatype"])] = (message_string, query_string)

    message_string = "Subclass (sh:focusNode) has property shape (sh:value) from ancestor class (rdfs:seeAlso), but according to ancestor property shape (sh:sourceShape) dropped its maxCount."
    query_string = """\
SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath
WHERE {
  ?nSuperclassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    sh:property ?nSuperclassPropertyShape ;
    .

  ?nSuperclassPropertyShape
    sh:maxCount ?lSuperclassPropertyShapeMaxCount ;
    sh:path ?nSuperclassPropertyShapePath ;
    .

  ?nClassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    rdfs:subClassOf+ ?nSuperclassNodeShape ;
    sh:property ?nClassPropertyShape ;
    .

  ?nClassPropertyShape
    sh:path ?nClassPropertyShapePath ;
    .

  ?nClassPropertyShapePath
    rdfs:subPropertyOf* ?nSuperclassPropertyShapePath ;
    .

  FILTER NOT EXISTS {
    ?nClassPropertyShape
      sh:maxCount ?lClassPropertyShapeMaxCount ;
      .
  }
}
"""
    error_class_iri_to_message_and_query[str(NS_SHIR["PropertyShapeComponentDroppedError-maxCount"])] = (message_string, query_string)

    message_string = "Subclass (sh:focusNode) has property shape (sh:value) from ancestor class (rdfs:seeAlso), but according to ancestor property shape (sh:sourceShape) has a lower sh:minCount." ;
    query_string = """\
SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath
WHERE {
  ?nSuperclassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    sh:property ?nSuperclassPropertyShape ;
    .

  ?nSuperclassPropertyShape
    sh:maxCount ?lSuperclassPropertyShapeMaxCount ;
    sh:path ?nSuperclassPropertyShapePath ;
    .

  ?nClassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    rdfs:subClassOf+ ?nSuperclassNodeShape ;
    sh:property ?nClassPropertyShape ;
    .

  ?nClassPropertyShape
    sh:maxCount ?lClassPropertyShapeMaxCount ;
    sh:path ?nClassPropertyShapePath ;
    .

  ?nClassPropertyShapePath
    rdfs:subPropertyOf* ?nSuperclassPropertyShapePath ;
    .

  FILTER (?lClassPropertyShapeMaxCount > ?lSuperclassPropertyShapeMaxCount)
}
"""
    error_class_iri_to_message_and_query[str(NS_SHIR["PropertyShapeComponentBroadenedError-maxCount"])] = (message_string, query_string)

    message_string = "Subclass (sh:focusNode) has property shape (sh:value) from ancestor class (rdfs:seeAlso), but according to ancestor's property shape (sh:sourceShape) dropped its sh:minCount."
    query_string = """\
SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath
WHERE {
  ?nSuperclassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    sh:property ?nSuperclassPropertyShape ;
    .

  ?nSuperclassPropertyShape
    sh:minCount ?lSuperclassPropertyShapeMinCount ;
    sh:path ?nSuperclassPropertyShapePath ;
    .

  ?nClassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    rdfs:subClassOf+ ?nSuperclassNodeShape ;
    sh:property ?nClassPropertyShape ;
    .

  ?nClassPropertyShape
    sh:path ?nClassPropertyShapePath ;
    .

  ?nClassPropertyShapePath
    rdfs:subPropertyOf* ?nSuperclassPropertyShapePath ;
    .

  FILTER NOT EXISTS {
    ?nClassPropertyShape
      sh:minCount ?lClassPropertyShapeMinCount ;
      .
  }
}
"""
    error_class_iri_to_message_and_query[str(NS_SHIR["PropertyShapeComponentDroppedError-minCount"])] = (message_string, query_string)

    message_string = "Subclass (sh:focusNode) has property shape (sh:value) from ancestor class (rdfs:seeAlso), but according to ancestor's property shape (sh:sourceShape) has a lower sh:minCount."
    query_string = """\
SELECT ?nClassNodeShape ?nClassPropertyShape ?nClassPropertyShapePath ?nSuperclassNodeShape ?nSuperclassPropertyShape ?nSuperclassPropertyShapePath
WHERE {
  ?nSuperclassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    sh:property ?nSuperclassPropertyShape ;
    .

  ?nSuperclassPropertyShape
    sh:minCount ?lSuperclassPropertyShapeMinCount ;
    sh:path ?nSuperclassPropertyShapePath ;
    .

  ?nClassNodeShape
    a owl:Class ;
    a sh:NodeShape ;
    rdfs:subClassOf+ ?nSuperclassNodeShape ;
    sh:property ?nClassPropertyShape ;
    .

  ?nClassPropertyShape
    sh:minCount ?lClassPropertyShapeMinCount ;
    sh:path ?nClassPropertyShapePath ;
    .

  ?nClassPropertyShapePath
    rdfs:subPropertyOf* ?nSuperclassPropertyShapePath ;
    .

  FILTER (?lClassPropertyShapeMinCount < ?lSuperclassPropertyShapeMinCount)
}
"""
    error_class_iri_to_message_and_query[str(NS_SHIR["PropertyShapeComponentBroadenedError-minCount"])] = (message_string, query_string)

    for error_class_iri in sorted(error_class_iri_to_message_and_query.keys()):
        _logger.debug("error_class_iri = %r.", error_class_iri)
        (
          message_string,
          query_string
        ) = error_class_iri_to_message_and_query[error_class_iri]

        _logger.debug("Compiling query...")
        query_object = rdflib.plugins.sparql.prepareQuery(query_string, initNs=nsdict)
        _logger.debug("Compiled.")

        reported_first_result = False
        _logger.debug("Running query...")
        for result in in_graph.query(query_object):
            if not reported_first_result:
                _logger.debug("Query now yielding results.")
                reported_first_result = True
            (
              n_class_node_shape,
              n_class_property_shape,
              n_class_property_shape_path,
              n_superclass_node_shape,
              n_superclass_property_shape,
              n_superclass_property_shape_path
            ) = result
            if not n_class_property_shape is None:
                triple_patterns_to_link.add((
                  n_class_node_shape,
                  None,
                  n_class_property_shape
                ))
            triple_patterns_to_link.add((
              n_superclass_node_shape,
              None,
              n_superclass_property_shape
            ))

            n_inheritance_validation_result = rdflib.BNode()
            out_graph.add((
              n_report,
              NS_SH.result,
              n_inheritance_validation_result
            ))
            out_graph.add((
              n_inheritance_validation_result,
              NS_RDF.type,
              rdflib.URIRef(error_class_iri)
            ))
            out_graph.add((
              n_inheritance_validation_result,
              NS_SH.focusNode,
              n_class_node_shape
            ))
            out_graph.add((
              n_inheritance_validation_result,
              NS_SH.resultPath,
              n_superclass_property_shape_path
            ))
            if not n_class_property_shape is None:
                out_graph.add((
                  n_inheritance_validation_result,
                  NS_SH.value,
                  n_class_property_shape
                ))
            out_graph.add((
              n_inheritance_validation_result,
              NS_SH.sourceShape,
              n_superclass_property_shape
            ))
            out_graph.add((
              n_inheritance_validation_result,
              NS_SH.resultMessage,
              rdflib.Literal(message_string)
            ))
            out_graph.add((
              n_inheritance_validation_result,
              NS_SH.resultSeverity,
              NS_SH.Violation
            ))
            out_graph.add((
              n_inheritance_validation_result,
              NS_RDFS.seeAlso,
              n_superclass_node_shape
            ))

    _logger.debug("error_class_iris reviewed.")

    for triple_pattern in triple_patterns_to_link:
        for triple in in_graph.triples(triple_pattern):
            out_graph.add(triple)
        # Pick up all triples of pattern's Object, presumed to be a sh:PropertyNode.
        for triple in in_graph.triples((triple_pattern[2], None, None)):
            out_graph.add(triple)

    results_tally = len([x for x in out_graph.triples((None, NS_SH.result, None))])
    # Report (extended) conformance.
    out_graph.add((
      n_report,
      NS_SH.conforms,
      rdflib.Literal(results_tally == 0)
    ))
    
    out_graph.serialize(args.out_graph, rdflib.util.guess_format(args.out_graph))

    if results_tally != 0:
        count_message = "Encountered at least one shir:ShapeBroadenedError. (%d encountered.)" % results_tally
        if args.strict:
            raise ConformanceError(count_message)
        else:
            _logger.warning(count_message)

if __name__ == "__main__":
    main()
