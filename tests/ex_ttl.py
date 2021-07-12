#!/usr/bin/env python3

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
This is a single-purpose script to compile a set of Turtle ontology files into one.
"""

import sys

import rdflib

g = rdflib.Graph()
for filename in sys.argv[2:]:
    g.parse(filename, format="turtle")
g.serialize(sys.argv[1], format="turtle")
