##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test the Dublib Core Structured Value support functions.

$Id: test_dcsv.py 66902 2006-04-12 20:16:30Z philikon $
"""
import unittest

from zope.testing.doctestunit import DocTestSuite
from zope.dublincore.dcsv import encode, decode


# TODO still need tests for errors, and createMapping()


def test_decode_empty():
    """
    >>> decode('')
    []
    >>> decode('   ')
    []
    """

def test_decode_simple_value():
    """
    >>> decode('v')
    [('', 'v')]
    >>> decode(' v ')
    [('', 'v')]
    >>> decode('v;')
    [('', 'v')]
    >>> decode(' v ; ')
    [('', 'v')]
    """

def test_decode_simple_escaped_value():
    # Make the docstring a raw string to avoid having escapes
    # interpreted twice; each test within the docstring will be parsed
    # again!
    r"""
    >>> decode(r'\v')
    [('', 'v')]
    >>> decode(r'\;')
    [('', ';')]
    >>> decode(r'\;;')
    [('', ';')]
    >>> decode(r'\= ')
    [('', '=')]
    >>> decode(r'\= ; ')
    [('', '=')]

    >>> decode(r'\\\=\; ; ')
    [('', '\\=;')]
    >>> decode(r'\\\=\;')
    [('', '\\=;')]
    >>> decode(r'\\\=\; = ; ')
    [('\\=;', '')]
    >>> decode(r'\;\;\;;')
    [('', ';;;')]
    """

def test_decode_trailing_backslash():
    r"""
    >>> decode('\\')
    [('', '\\')]
    >>> decode('v\\')
    [('', 'v\\')]

    These are tricky, but for different reasons:

    >>> decode(r'v\ ')
    [('', 'v\\')]
    >>> decode(r'v\ ; ')
    [('', 'v')]
    """

def test_decode_simple_list():
    """
    >>> decode('a;b;c')
    [('', 'a'), ('', 'b'), ('', 'c')]
    >>> decode('a;b;c;')
    [('', 'a'), ('', 'b'), ('', 'c')]
    """

def test_decode_simple_escaped_list():
    r"""
    >>> decode(r'\a;\b;\c')
    [('', 'a'), ('', 'b'), ('', 'c')]
    >>> decode(r' \a ; \b ; \c ; ')
    [('', 'a'), ('', 'b'), ('', 'c')]

    >>> decode(r'\;;b;c')
    [('', ';'), ('', 'b'), ('', 'c')]
    >>> decode(r' \=;b;c;')
    [('', '='), ('', 'b'), ('', 'c')]
    """

def test_decode_empty_values():
    # weird case; hard to know the intent of the specification
    """
    >>> decode('=')
    [('', '')]
    >>> decode(';')
    [('', '')]
    >>> decode('  ;  ')
    [('', '')]
    >>> decode(';;')
    [('', ''), ('', '')]
    >>> decode('  ;  ;  ')
    [('', ''), ('', '')]
    >>> decode('=;')
    [('', '')]
    >>> decode(' = ;  ')
    [('', '')]
    >>> decode('=;=;')
    [('', ''), ('', '')]
    >>> decode(' = ; = ;  ')
    [('', ''), ('', '')]
    >>> decode(' = ; = ; = ')
    [('', ''), ('', ''), ('', '')]
    """

def test_decode_labeled_values():
    """
    >>> decode('a=b')
    [('a', 'b')]
    >>> decode('a=b;')
    [('a', 'b')]
    >>> decode('a=b;c=d')
    [('a', 'b'), ('c', 'd')]

    Not really sure about this one yet; assuming that the space in 'd ;'
    is supposed to be removed until we have information that says
    otherwise:

    >>> decode('a =b; c=  d ;')
    [('a', 'b'), ('c', 'd')]
    """

def test_decode_mixed_values():
    """
    >>> decode('a;b=c')
    [('', 'a'), ('b', 'c')]
    >>> decode('a=b;c')
    [('a', 'b'), ('', 'c')]
    >>> decode('a;b=c;  ')
    [('', 'a'), ('b', 'c')]
    >>> decode('a=b;c ; ')
    [('a', 'b'), ('', 'c')]

    >>> decode('a;b;c;d=e;f;g;')
    [('', 'a'), ('', 'b'), ('', 'c'), ('d', 'e'), ('', 'f'), ('', 'g')]
    >>> decode('a=b;c=d;e;f=g')
    [('a', 'b'), ('c', 'd'), ('', 'e'), ('f', 'g')]
    """

def test_decode_duplicate_labels():
    """
    >>> decode('a=b;a=c; a=d')
    [('a', 'b'), ('a', 'c'), ('a', 'd')]
    """

def test_encode_empty_list():
    """
    >>> encode([])
    ''
    """

def test_encode_single_item():
    """
    >>> encode([''])
    ';'
    >>> encode([('', '')])
    ';'
    >>> encode(['a'])
    'a;'
    >>> encode([('', 'a')])
    'a;'
    >>> encode([('a','')])
    'a=;'
    >>> encode([('a', 'b')])
    'a=b;'

    The label from a pair can be any non-true value:

    >>> encode([(None, '')])
    ';'
    >>> encode([(None, 'a')])
    'a;'
    >>> encode([(0, 'a')])
    'a;'
    >>> encode([((), 'a')])
    'a;'

    This may be a mis-feature, but seems harmless since no one in
    their right mind would use it intentionally (except maybe with
    None).
    """

def test_encode_single_value_needing_escapes():
    r"""
    >>> encode(['='])
    '\\=;'
    >>> encode([';'])
    '\\;;'
    >>> encode(['\\'])
    '\\\\;'
    >>> encode([r'\\'])
    '\\\\\\\\;'
    """

def test_encode_labeled_value_needing_escapes():
    r"""
    Escaping needed in the labels:

    >>> encode([('\\', '')])
    '\\\\=;'
    >>> encode([('\\', 'a')])
    '\\\\=a;'
    >>> encode([('=', '')])
    '\\==;'
    >>> encode([(';', 'a')])
    '\\;=a;'

    Escaping needed in the values:

    >>> encode([('a', '\\')])
    'a=\\\\;'
    >>> encode([('a', '=')])
    'a=\\=;'
    >>> encode([('a', ';')])
    'a=\\;;'

    Escaping needed in both:

    >>> encode([('\\', '\\')])
    '\\\\=\\\\;'
    >>> encode([('=', '=')])
    '\\==\\=;'
    >>> encode([(';', ';')])
    '\\;=\\;;'
    """

def test_encode_simple_list():
    """
    >>> encode(['a', 'b', 'c'])
    'a; b; c;'
    >>> encode(['', '', ''])
    '; ; ;'
    >>> encode(['a b', 'c d'])
    'a b; c d;'
    """

def test_encode_labeled_values():
    # Single items were tested above; these all demonstrate with more
    # than one item.
    """
    >>> encode([('a', ''), ('b', '')])
    'a=; b=;'
    >>> encode([('a', 'b'), ('c', 'd')])
    'a=b; c=d;'
    """

def test_encode_mixed_items():
    """
    >>> encode(['a', ('b', 'c')])
    'a; b=c;'
    >>> encode([('', 'a'), ('b', 'c')])
    'a; b=c;'
    >>> encode([('b', 'c'), 'a'])
    'b=c; a;'
    >>> encode([('b', 'c'), ('', 'a')])
    'b=c; a;'
    """

def test_encode_error_non_strings():
    """
    >>> encode([(42, '')])
    Traceback (most recent call last):
    ...
    TypeError: labels must be strings; found 42
    >>> encode([('', 42)])
    Traceback (most recent call last):
    ...
    TypeError: values must be strings; found 42
    >>> encode([('label', 42)])
    Traceback (most recent call last):
    ...
    TypeError: values must be strings; found 42
    """

def test_encode_error_outer_whitespace():
    """
    >>> encode([' a'])
    Traceback (most recent call last):
    ...
    ValueError: values may not include leading or trailing spaces: ' a'
    >>> encode(['a '])
    Traceback (most recent call last):
    ...
    ValueError: values may not include leading or trailing spaces: 'a '
    >>> encode([('', 'a ')])
    Traceback (most recent call last):
    ...
    ValueError: values may not include leading or trailing spaces: 'a '
    >>> encode([('label', 'a ')])
    Traceback (most recent call last):
    ...
    ValueError: values may not include leading or trailing spaces: 'a '
    """


def test_suite():
    return DocTestSuite()

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")
