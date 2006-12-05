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
#   This script reads XHTML from a single files specified on the
#   command line, and writes processed XHTML to standard output. 
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

import pickle
import re
import string
import sys

# Terms are caches across invocations in this file, allowing
# inter-file cross references. 
terms_filename = '.terms'

# Terms are recognized for these classes of the XHTML <span> element.
terms_classes = [
    'Term',
    'Class',
    'API'
    ]

# The same class name with 'Def' appended is taken recognized as the
# definition of a term.  So, for instance, 'TermDef' is the class for
# terminology definitions, and 'Term' for corresponding uses.
terms_def_classes = map(lambda klass: klass + 'Def', terms_classes)


def to_camel_caps(str):
    """Converts a string to CamelCaps."""
    # Break STR into words.
    words = string.split(string.strip(str))
    # Capitalize each word.
    words = map(string.capitalize, words)
    # Join the words together, without spaces among them.
    return string.join(words, '')
    

def make_label(klass, term):
    """Returns an HTML label to be used for a term."""
    return '%s-%s' % (klass, to_camel_caps(term))


def clean_up_term(term):
    """Clean up whitespace and such to canonicalize a term."""
    return string.strip(re.sub('\s+', ' ', term))


# Load terms from the cache file, if it exists.
try:
    terms_file = open(terms_filename, "r")
    terms = pickle.load(terms_file)
    terms_file.close()
except:
    terms = {}

# Read input from the specified file.
input_file = sys.argv[1]
input = open(input_file, 'r').read()
input_file = re.sub('\.xhtml', '.html', input_file)

# Regular expression for definitions of terms.
term_definition_re = re.compile('<span\s*class="(?P<class>%s)">'
                                % string.join(terms_def_classes, '|')
                                + '(?P<term>[^<]*)</a>')

# Regular expression for uses of terms.
term_use_re = re.compile('<span\s*class="(?P<class>%s)">'
                         % string.join(terms_classes, '|')
                         + '(?P<term>[^<]*)</span>')

# Fix up definitions of terms.
while 1:
    match = term_definition_re.search(input)
    if match == None:
        break

    klass = match.group('class')
    term = clean_up_term(match.group('term'))
    label = make_label(klass, term)
    # Add the name attribute to the anchor element.
    input = input[ : match.start()] \
            + '<a class="%s" name="%s">%s</a>' % (klass, label, term) \
            + input[match.end() : ]
    # Add/update a reference in the terms dictionary.
    ref = '%s#%s' % (input_file, label)
    klass = klass[ : -3]
    if not terms.has_key(klass):
        terms[klass] = {}
    klass_dict = terms[klass]
    klass_dict[term] = ref

# Fix up uses of terms.
while 1:
    match = term_use_re.search(input)
    if match == None:
        break

    klass = match.group('class')
    term = clean_up_term(match.group('term'))
    # Look up the term in the terms dictionary.
    if not terms.has_key(klass):
        terms[klass] = {}
    klass_dict = terms[klass]
    if klass_dict.has_key(term):
        ref = klass_dict[term]
    # If the term ends with 's', naively assume its a pluralized form
    # and try to find the singluar.
    elif term[-1] == 's' and klass_dict.has_key(term[ : -1]):
        ref = klass_dict[term[ : -1]]
    else:
        # The term is not in our dictionary.  Emit a warning and use a
        # default ref.
        sys.stderr.write('Warning: encountered use of undefined term %s.\n'
                          % term)
        ref = None
    # Add the ref attribute to the anchor element.
    if ref == None:
        href_text = ''
    else:
        href_text = ' href="%s"' % ref
    input = input[ : match.start()] \
            + '<a class="%s"%s>%s</a>' % (klass, href_text, term) \
            + input[match.end() : ]

# Write the result to standard output.
print input

# Write out the terms cache file.
terms_file = open(terms_filename, 'w')
pickle.dump(terms, terms_file)
terms_file.close()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
