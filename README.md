# SHACL Reviewer Utility

This project was developed for the [CASE community](https://caseontology.org/) to review the state of it's and [UCO](https://unifiedcyberontology.org)'s [SHACL](https://www.w3.org/TR/shacl/) implementation, particularly around the appropriateness of shapes applied to subclasses.

A deeper description of this project is in the [background](#Background) section on this page.


## Disclaimer

Participation by NIST in the creation of the documentation of mentioned software is not intended to imply a recommendation or endorsement by the National Institute of Standards and Technology, nor is it intended to imply that any specific software is necessarily the best available for the purpose.


## Installation

1. Clone this repository.
2. (Optional) Create and activate a virtual environment.
3. Run `pip install .` (or the name of the cloned directory instead of `.`).

Installation is demonstrated in the `.venv.done.log` Makefile target of the [`tests/`](tests/) directory.  The `--editable` flag is a development convenience and not necessary for operational usage.


## Usage


### `case_shacl_inheritance_reviewer`

To review `sh:PropertyShape` inheritance of an ontology using SHACL, run this command:

```bash
case_shacl_inheritance_reviewer review.ttl ontology.ttl [ontology-2.ttl ...]
```

Note that:
* The output file is the first argument.
* The ontology can be passed as a monolithic file or as multiple files.

For usage in CI workflows that wish to halt on any subclass-property-shape ontology errors being encountered, the `--strict` flag should be used.


## Development status

This repository follows [CASE community guidance on describing development status](https://caseontology.org/resources/software.html#development_status), by adherence to noted support requirements.

The status of this repository is:

4 - Beta


## Versioning

This project follows [SEMVER 2.0.0](https://semver.org/) where versions are declared.


## Ontology versions supported

Though this is a CASE repository, it is not a CASE data producer, or even CASE data consumer.  Its role in the CASE and UCO infrastructure is an ontology review tool.  Hence, this repository will not report a "Supported version" of CASE or UCO.  As a historic note, it was developed to support the release of UCO 0.7.0 and CASE 0.5.0.


## Repository locations

This repository is available at the following locations:
* [https://github.com/casework/CASE-Utility-SHACL-Inheritance-Reviewer](https://github.com/casework/CASE-Utility-SHACL-Inheritance-Reviewer)
* [https://github.com/usnistgov/CASE-Utilities-Python](https://github.com/usnistgov/CASE-Utility-SHACL-Inheritance-Reviewer) (a mirror)

Releases and issue tracking will be handled at the [casework location](https://github.com/casework/CASE-Utility-SHACL-Inheritance-Reviewer).


## Make targets

Some `make` targets are defined for this repository:
* `check` - Run unit tests.
* `clean` - Remove test build files, but not downloaded files.
* `download` - Download files sufficiently to run the unit tests offline.  Note if you do need to work offline, be aware touching the `setup.cfg` file in the project root directory, or `tests/requirements.txt`, will trigger a virtual environment rebuild.

Note that as with CASE and UCO community practices, a Java jar file will be downloaded to normalize generated test Turtle content.  This file will be downloaded as part of the `check` and `download` targets.


## Background

SHACL, [at the time of this writing](https://www.w3.org/TR/2017/REC-shacl-20170720/), exhibits a behavior that might be unexpected from ontologists or data modelers used to working with class hierarchies.  A typical use case of SHACL node-shape (`sh:NodeShape`) definitions is to apply them to OWL Class (`owl:Class`) definitions.  For instance, we might have a class for a triangle, with a point and method to relate triangles and points:

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Triangle
  a owl:Class ;
  .

ex:Point
  a owl:Class ;
  .

ex:hasPoint
  a owl:ObjectProperty ;
  rdfs:domain ex:Triangle ;
  rdfs:range ex:Point ;
  .
```

We further might want to specify that any instance of a `ex:Triangle` should have exactly three points.  The SHACL mechanism to specify this is a `sh:PropertyShape` constraint:

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

ex:Triangle
  a sh:NodeShape ;
  sh:property ex:PropertyShape-1 ;
  sh:targetClass ex:Triangle ;
  .

ex:PropertyShape-1
  a sh:PropertyShape ;
  sh:path ex:hasPoint ;
  sh:class ex:Point ;
  sh:minCount 3 ;
  sh:maxCount 3 ;
  .
```

(While it looks like the same specificaion can be made with `owl:Restriction` or `sh:PropertyShape`, their semantics differ significantly.  Discussion of semantic differences is left as out of scope of this repository.)

The above two graphs can have their triples combined together without issue, and can even validate an instance of a triangle.  This example file, [`kb-triangle-1.ttl`](tests/kb-triangle-1.ttl), contains a sample triangle.

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix kb: <http://example.org/kb/> .

kb:point-1 a ex:Point .
kb:point-2 a ex:Point .
kb:point-3 a ex:Point .

kb:triangle-1
  a ex:Triangle ;
  ex:hasPoint kb:point-1 ;
  ex:hasPoint kb:point-2 ;
  ex:hasPoint kb:point-3 ;
  .
```

`pyshacl` will validate it against the combined example ontology.  The file [`kb-test-1.ttl`](tests/kb-test-1.ttl) is generated with this command (see the [Makefile](tests/Makefile) for the full build chain and longer flag names).

```bash
pyshacl \
  -df turtle \
  -f turtle \
  -sf turtle \
  -o kb-test-1.ttl \
  -s ex-triangle-1-2.ttl \
  kb-triangle-1.ttl
```

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

[] a sh:ValidationReport ;
    sh:conforms true .

```

Another example file, [`kb-triangle-2.ttl`](tests/kb-triangle-2.ttl), contains a sample invalid triangle, missing a third point:

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix kb: <http://example.org/kb/> .

kb:point-4 a ex:Point .
kb:point-5 a ex:Point .

kb:triangle-2
  a ex:Triangle ;
  ex:hasPoint kb:point-4 ;
  ex:hasPoint kb:point-5 ;
  .
```

```bash
pyshacl \
  -df turtle \
  -f turtle \
  -sf turtle \
  -o kb-test-1.ttl \
  -s ex-triangle-1-2.ttl \
  kb-triangle-2.ttl
```

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

[] a sh:ValidationReport ;
    sh:conforms false ;
    sh:result [ a sh:ValidationResult ;
            sh:focusNode <http://example.org/kb/triangle-2> ;
            sh:resultMessage "Less than 3 values on kb:triangle-2->ex:hasPoint" ;
            sh:resultPath ex:hasPoint ;
            sh:resultSeverity sh:Violation ;
            sh:sourceConstraintComponent sh:MinCountConstraintComponent ;
            sh:sourceShape ex:PropertyShape-1 ] .

```

What might not be clear to modelers is that SHACL `sh:PropertyShape`s can appear to not be inherited with OWL or RDFS subclassing.  This potential confusion has been found to be an indirect result of a distinction some SHACL implementations may make between "Shape graphs" and "Ontology graphs".  This documentation is based on experiences of the CASE and UCO communities with the `pyshacl` implementation.


### Confusion demonstration

To demonstrate, say the above triangle ontology sees adoption by a plotting system, and the plotting system implements a feature that handles "Squishing" a triangle into a line by making two of its vertices into the same coordinate-set.  Say also their use case involves a memory-"slimming" feature and converts those two coordinate-sets into the same `ex:Point`.  Say---as a last point of contrivance---that a developer was not looking at the original `ex:Triangle` specification when they decided to add [`ex-triangle-2.ttl`](tests/ex-triangle-2.ttl) to their ontology:

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

ex:Triangle-but-1-dimensional
  a
    sh:NodeShape ,
    owl:Class
    ;
  rdfs:subClassOf ex:Triangle ;
  sh:property ex:PropertyShape-2 ;
  sh:targetClass ex:Triangle-but-1-dimensional ;
  .

ex:PropertyShape-2
  a sh:PropertyShape ;
  sh:path ex:hasPoint ;
  sh:class ex:Point ;
  sh:minCount 2 ;
  sh:maxCount 2 ;
  .
```

A modeler with the last few example-blocks fresh in their memory will spot the flaw immediately.  `ex:Triangle-but-1-dimensional` is also a `ex:Triangle`, explicitly so by the included statement `ex:Triangle-but-1-dimensional rdfs:subClassOf ex:Triangle .`, and thus must have exactly three `ex:Point`s.  However, a curious behavior occurs when evaluating this file, [`kb-triangle-3.ttl`](tests/kb-triangle-3.ttl).

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix kb: <http://example.org/kb/> .

kb:point-6 a ex:Point .
kb:point-7 a ex:Point .

kb:triangle-3
  a ex:Triangle-but-1-dimensional ;
  ex:hasPoint kb:point-6 ;
  ex:hasPoint kb:point-7 ;
  .
```

To the developer using only the new ontology file, SHACL validation appears to function.

```bash
pyshacl \
  -df turtle \
  -f turtle \
  -sf turtle \
  -o kb-test-3.ttl \
  -s ex-triangle-2.ttl \
  kb-triangle-3.ttl
```

The contents of [`kb-test-3.ttl`](tests/kb-test-3.ttl) are:

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

[] a sh:ValidationReport ;
    sh:conforms true .

```

But confusion arises when incorporating the superclass definition and `sh:PropertyShape`: `pyshacl` reports the instance is still valid, as shown in ([`kb-test-4.ttl`](tests/kb-test-4.ttl)).

```bash
pyshacl \
  -df turtle \
  -f turtle \
  -sf turtle \
  -o kb-test-4.ttl \
  -s ex-triangle.ttl \
  kb-triangle-3.ttl
```

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

[] a sh:ValidationReport ;
    sh:conforms true .

```

(That example, and further examples, use a combined ontology file [`ex-triangle.ttl`](tests/ex-triangle.ttl) to avoid any possible effects from partial ontology data.)

Adding a "Reminder" triple that explicitly adds the superclass `ex:Triangle` induces `pyshacl` to report non-conformance with the `ex:Triangle` shape.  The following command inspects [`kb-triangle-3-super.ttl`](tests/kb-triangle-3-super.ttl).

```bash
pyshacl \
  -df turtle \
  -f turtle \
  -sf turtle \
  -o kb-test-5.ttl \
  -s ex-triangle.ttl \
  kb-triangle-3-super.ttl
```

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

[] a sh:ValidationReport ;
    sh:conforms false ;
    sh:result [ a sh:ValidationResult ;
            sh:focusNode <http://example.org/kb/triangle-3> ;
            sh:resultMessage "Less than 3 values on kb:triangle-3->ex:hasPoint" ;
            sh:resultPath ex:hasPoint ;
            sh:resultSeverity sh:Violation ;
            sh:sourceConstraintComponent sh:MinCountConstraintComponent ;
            sh:sourceShape ex:PropertyShape-1 ] .

```

There is a point of potential confusion to the end `pyshacl` user, on whether that "Reminder" triple needs to be added to their data graph.  According to [this Issue comment](https://github.com/RDFLib/pySHACL/issues/14#issue-396214221), such subclass information should not be necessary in the data graph, but it would be considered "ontological information".  It is not currently clear to the CASE or UCO communities why such ontological information is not recognized in the SHACL shapes graph when present, especially whether this is a `pyshacl`-level issue or a SHACL specification-level issue.


### Usage resolution

When a SHACL shapes graph is also used to store ontology information (such as subclass relationships), `pyshacl` is capable of using that graph to make class hierarchy inferences, but *not* when treating the graph as a shapes graph.  The ontology must be passed as both the `--shacl` argument (`-s`) to be treated as a shapes graph, and the `--ont-graph` argument (`-e`) to be treated as the ontology graph:

```bash
pyshacl \
  -df turtle \
  -ef turtle \
  -f turtle \
  -sf turtle \
  -o kb-test-6.ttl \
  -s ex-triangle.ttl \
  -e ex-triangle.ttl \
  kb-triangle-3.ttl
```

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

[] a sh:ValidationReport ;
    sh:conforms false ;
    sh:result [ a sh:ValidationResult ;
            sh:focusNode <http://example.org/kb/triangle-3> ;
            sh:resultMessage "Less than 3 values on kb:triangle-3->ex:hasPoint" ;
            sh:resultPath ex:hasPoint ;
            sh:resultSeverity sh:Violation ;
            sh:sourceConstraintComponent sh:MinCountConstraintComponent ;
            sh:sourceShape ex:PropertyShape-1 ] .

```

### Inspection of property shapes and subclasses

The outstanding concern the present repository addresses is a quality control matter at the ontology level.  The above dual-flag treatment catches an ontology error at the time of instance data validation.  An ontology shipping and waiting to find this in instance data is analagous to finding a bug from an application run-time error rather than a compile-time error.

No applications of flags to `pyshacl` were found to be able to detect that the definition of `ex:Triangle-but-1-dimensional` is unsatisfiable in light of its subclass relationships and cross-purposed `sh:PropertyShape`s.  (The recipe for [`kb-test-7.ttl`](tests/kb-test-7.ttl) attempts to exercise all flags from the `pyshacl` help menu.  No ontology-level error is reported.)  It is unclear whether the SHACL specification provides a mechanism to detect this.

The solution the CASE and UCO communities are taking to address this issue is inspecting how all `sh:PropertyShape`s on a class relate to `sh:PropertyShape`s on all superclasses.  This project affirms that shapes of subclasses do not *expand* the set of accepted data patterns beyond superclass constraints.

(This project was originally written to support a solution that the CASE and UCO communities previously believed was necessary, based on the misunderstanding of whether `sh:PropertyShape`s would be implicitly applied to subclasses.  Believing they *weren't*, UCO initially prepared a framework to propagate `sh:PropertyShape` copies to all subclasses, inspiring this project as an automated review system.  Gratefully, the copying is now understood and demonstrated to not be necessary.  However, the other `sh:PropertyShape` subclass-superclass interaction review has proven worth retaining.)

To demonstrate that the above triangle inconsistency is detected, the following shell transcript reports the inconsistencies similar to how a `sh:ValidationReport` would do so for instance data.

```bash
case_shacl_inheritance_reviewer \
  ex-triangle-inheritance.ttl \
  ex-triangle.ttl
```

```turtle
@prefix ex: <http://example.org/ontology/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix shir: <http://example.org/ontology/shacl-inheritance-review/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:PropertyShape-1
	a sh:PropertyShape ;
	sh:class ex:Point ;
	sh:maxCount "3"^^xsd:integer ;
	sh:minCount "3"^^xsd:integer ;
	sh:path ex:hasPoint ;
	.

ex:PropertyShape-2
	a sh:PropertyShape ;
	sh:class ex:Point ;
	sh:maxCount "2"^^xsd:integer ;
	sh:minCount "2"^^xsd:integer ;
	sh:path ex:hasPoint ;
	.

ex:Triangle
	sh:property ex:PropertyShape-1 ;
	.

ex:Triangle-but-1-dimensional
	sh:property ex:PropertyShape-2 ;
	.

[]
	a shir:InheritanceValidationReport ;
	sh:conforms "false"^^xsd:boolean ;
	sh:result [
		a shir:PropertyShapeComponentBroadenedError-minCount ;
		rdfs:seeAlso ex:Triangle ;
		sh:focusNode ex:Triangle-but-1-dimensional ;
		sh:resultMessage "Subclass (sh:focusNode) has property shape (sh:value) from ancestor class (rdfs:seeAlso), but according to ancestor's property shape (sh:sourceShape) has a lower sh:minCount." ;
		sh:resultPath ex:hasPoint ;
		sh:resultSeverity sh:Violation ;
		sh:sourceShape ex:PropertyShape-1 ;
		sh:value ex:PropertyShape-2 ;
	] ;
	.

```

A taxonomy of error types has been developed and is stored in this repository at [`shacl-inheritance-review.ttl`](ontology/shacl-inheritance-review.ttl).  This ontology file is intended to spur discussion in the broader SHACL community, and to assist with implementation of the unit tests.  It is not currently intended to be a durable artifact, nor an attempt to claim the ontological prefix `shir:`.

Code design and tests are further documented in the [`tests/`](tests/#Testing) directory.
