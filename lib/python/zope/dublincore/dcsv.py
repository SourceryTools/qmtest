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
"""Functions for working with Dublin Core Structured Values (DCSV) scheme.

DCSV is specified in 'DCMI DCSV: A syntax for writing a list of
labelled values in a text string', at:

http://dublincore.org/documents/dcmi-dcsv/

$Id: dcsv.py 26734 2004-07-23 21:55:49Z pruggera $
"""
__docformat__ = 'restructuredtext'

import re

__all__ = "encode", "decode"

try:
    basestring
except NameError:
    # define basestring in Python 2.2.x:
    try:
        unicode
    except NameError:
        basestring = str
    else:
        basestring = str, unicode


def encode(items):
    L = []
    for item in items:
        if isinstance(item, basestring):
            L.append(_encode_string(item, "values") + ";")
        else:
            k, v = item
            if not isinstance(v, basestring):
                raise TypeError("values must be strings; found %r" % v)
            v = _encode_string(v, "values")
            if k:
                if not isinstance(k, basestring):
                    raise TypeError("labels must be strings; found %r" % k)
                k = _encode_string(k, "labels")
                s = "%s=%s;" % (k, v)
            else:
                s = v + ";"
            L.append(s)
    return " ".join(L)

def _encode_string(s, what):
    if s.strip() != s:
        raise ValueError("%s may not include leading or trailing spaces: %r"
                         % (what, s))
    return s.replace("\\", r"\\").replace(";", r"\;").replace("=", r"\=")


def decode(text):
    items = []
    text = text.strip()
    while text:
        m = _find_interesting(text)
        if m:
            prefix, char = m.group(1, 2)
            prefix = _decode_string(prefix).rstrip()
            if char == ";":
                items.append(('', prefix))
                text = text[m.end():].lstrip()
                continue
            else: # char == "="
                text = text[m.end():].lstrip()
            # else we have a label
            m = _find_value(text)
            if m:
                value = m.group(1)
                text = text[m.end():].lstrip()
            else:
                value = text
                text = ''
            items.append((prefix, _decode_string(value)))
        else:
            items.append(('', _decode_string(text)))
            break
    return items

_prefix = r"((?:[^;\\=]|\\.)*)"
_find_interesting = re.compile(_prefix + "([;=])").match
_find_value = re.compile(_prefix + ";").match

def _decode_string(s):
    if "\\" not in s:
        return s.rstrip()
    r = ""
    while s:
        c1 = s[0]
        if c1 == "\\":
            c2 = s[1:2]
            if not c2:
                return r + c1
            r += c2
            s = s[2:]
        else:
            r += c1
            s = s[1:]
    return r.rstrip()


def createMapping(items, allow_duplicates=False):
    mapping = {}
    for item in items:
        if isinstance(item, basestring):
            raise ValueError("can't create mapping with unlabelled data")
        k, v = item
        if not isinstance(k, basestring):
            raise TypeError("labels must be strings; found %r" % k)
        if not isinstance(v, basestring):
            raise TypeError("values must be strings; found %r" % v)
        if k in mapping:
            if allow_duplicates:
                mapping[k].append(v)
            else:
                raise ValueError("labels may not have more than one value")
        else:
            if allow_duplicates:
                mapping[k] = [v]
            else:
                mapping[k] = v
    return mapping
