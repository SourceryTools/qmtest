#! /usr/bin/python

########################################################################
#
# File:   generate_expectations.py
# Author: Mark Mitchell
# Date:   01/04/2002
#
# Contents:
#   Script to automatically generate QMTest expectations.
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import dircache
import os
import os.path
import string

########################################################################
# Functions
########################################################################

def find_xfails(xfails, dirname, names):
    """Look for expected failures in 'dirname'.

    'xfails' -- The list of files that contain expected failures.

    'dirname' -- A string giving the path to the directory.

    'names' -- A sequence of strings giving the names of files in the
    directory.

    Add all files that are expected to fail to 'xfails'."""
    
    # Look through each of the files in the directory.
    for name in names:
        # Skip files that do not end in .C.
        if os.path.splitext(name)[1] != '.C':
            continue
        # Compute the complete path to the file.
        path = os.path.join(dirname, name)
        # Open the file.
        f = open(os.path.join(dirname, name))
        # Look for an XFAIL marker.
        if string.find(f.read(), "XFAIL") != -1:
            xfails.append(path)


def generate_failure_result(path):
    """Generate XML indicating that the test given by 'path' failed.

    'path' -- A string giving the path to a test."""

    # Split path into all of its components.
    components = []
    while path:
        (path, tail) = os.path.split(path)
        components.insert(0, tail)

    # The first component should be ".".
    assert components[0] == '.'
    # Remove it.
    components = components[1:]
    
    # All components but the last are of the form "g++.<name>".
    # Change that into "name".
    for x in range(len(components) - 1):
        assert components[x][:4] == "g++."
        components[x] = components[x][4:]

    # The last component shoud end in ".C".
    assert components[-1][-2:] == ".C"
    components[-1] = components[-1][:-2]

    test_name = string.join(components, ".")

    xml = ('<result id="%s" kind="test">\n'
           '  <outcome>FAIL</outcome>\n'
           '</result>') % test_name

    print xml

    
    
########################################################################
# Main Program
########################################################################

# There are no expected failures yet.
xfails = []

# Walk all directories looking for .C files with XFAIL markers.
os.path.walk(".", find_xfails, xfails)

# Generate the header.
print '''<?xml version='1.0' encoding='ISO-8859-1'?>
<!DOCTYPE results PUBLIC "-//Software Carpentry//QMTest Result
V0.3//EN" "http://www.software-carpentry.com/qm/xml/result.dtd">
<results>'''

# Generate results for all of the expected failures.
map(generate_failure_result, xfails)

print "</results>"
