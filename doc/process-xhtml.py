#! /usr/bin/python

########################################################################
#
# File:   process-xhtml.py
# Author: Alex Samuel
# Date:   2000-10-24
#
# Contents:
#   Processing for XHTML documentation.
#
#   This script is used to generate HTML, suitable for browsing, from
#   XHTML documentation sources.  It performs the following tasks:
#
#     - Any processing that's necessary to make our documentation
#       compatible with XHTML (which isn't fully supported in all
#       browsers).
#
#     - Automatic generation of crosslinks from uses to definitions
#       of terms.
#
# Usage:
#   This script reads XHTML from standard input and writes to standard
#   output.  
#
# Bugs:
#   This script, as currently written, is a bit of a hack, but it
#   should do for a while.
#
# Copyright (c) 2000 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

import re
import string
import sys

terms_filename = ".terms"


def to_camel_caps(str):
    """Converts a string to CamelCaps."""
    # Break STR into words.
    words = string.split(string.strip(str))
    # Capitalize each word.
    words = map(string.capitalize, words)
    # Join the words together, without spaces among them.
    return string.join(words, '')
    

def make_label(term):
    """Returns an HTML label to be used for a term."""
    return 'DEF-%s' % to_camel_caps(term)


# Load terms from the cache file, if it exists.
try:
    terms_file = open(terms_filename, "r")
    terms_text = terms_file.read()
    terms_file.close()
    terms = eval(terms_text)
except:
    terms = {}

# Read input from the specified file.
input_file = sys.argv[1]
input = open(input_file, 'r').read()

# Regular expression for definitions of terms.
term_definition_re = re.compile('<a\s*class="TermDef">([^<]*)</a>')

# Regular expression for uses of terms.
term_use_re = re.compile('<a\s*class="Term">([^<]*)</a>')

# Fix up definitions of terms.
while 1:
    match = term_definition_re.search(input)
    if match == None:
        break

    term = string.strip(match.group(1))
    label = make_label(term)
    # Add the name attribute to the anchor element.
    input = input[ : match.start()] \
            + '<a class="TermDef" name="%s">%s</a>' % (label, term) \
            + input[match.end() : ]
    # Add/update a reference in the terms dictionary.
    ref = '%s#%s' % (input_file, label)
    terms[term] = ref

# Fix up uses of terms.
while 1:
    match = term_use_re.search(input)
    if match == None:
        break

    term = string.strip(match.group(1))
    # Look up the term in the terms dictionary.
    if terms.has_key(term):
        ref = terms[term]
    else:
        # The term is not in our dictionary.  Emit a warning and use a
        # default ref.
        sys.stderr.write('Warning: encountered use of undefined term %s.\n'
                          % term)
        ref = "index.html"
    # Add the ref attribute to the anchor element.
    input = input[ : match.start()] \
            + '<a class="Term" ref="%s">%s</a>' % (ref, term) \
            + input[match.end() : ]

# Write the result to standard output.
print input

# Write out the terms cache file.
terms_file = open(terms_filename, 'w')
terms_file.write(repr(terms))
terms_file.close()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
