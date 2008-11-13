##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""MIME Content-Type parsing helper functions.

This supports parsing RFC 1341 Content-Type values, including
quoted-string values as defined in RFC 822.

"""
__docformat__ = "reStructuredText"

import re


# TODO: This still needs to support comments in structured fields as
# specified in RFC 2822.


def parse(string):
    major, minor, params = parseOrdered(string)
    d = {}
    for (name, value) in params:
        d[name] = value
    return major, minor, d

def parseOrdered(string):
    if ";" in string:
        type, params = string.split(";", 1)
        params = _parse_params(params)
    else:
        type = string
        params = []
    if "/" not in type:
        raise ValueError("content type missing major/minor parts: %r" % type)
    type = type.strip()

    major, minor = type.lower().split("/", 1)
    return _check_token(major.strip()), _check_token(minor.strip()), params

def _parse_params(string):
    result = []
    string = string.strip()
    while string:
        if not "=" in string:
            raise ValueError("parameter values are not optional")
        name, rest = string.split("=", 1)
        name = _check_token(name.strip().lower())
        rest = rest.strip()

        # rest is: value *[";" parameter]

        if rest[:1] == '"':
            # quoted-string, defined in RFC 822.
            m = _quoted_string_match(rest)
            if m is None:
                raise ValueError("invalid quoted-string in %r" % rest)
            value = m.group()
            rest = rest[m.end():].strip()
            #import pdb; pdb.set_trace()
            if rest[:1] not in ("", ";"):
                raise ValueError(
                    "invalid token following quoted-string: %r" % rest)
            rest = rest[1:]
            value = _unescape(value)

        elif ";" in rest:
            value, rest = rest.split(";")
            value = _check_token(value.strip())

        else:
            value = _check_token(rest.strip())
            rest = ""

        result.append((name, value))
        string = rest.strip()
    return result


def _quoted_string_match(string):
    # This support RFC 822 quoted-string values.
    global _quoted_string_match
    _quoted_string_match = re.compile(
        '"(?:\\\\.|[^"\n\r\\\\])*"', re.DOTALL).match
    return _quoted_string_match(string)

def _check_token(string):
    if _token_match(string) is None:
        raise ValueError('"%s" is not a valid token' % string)
    return string

def _token_match(string):
    global _token_match
    _token_match = re.compile("[^][ \t\n\r()<>@,;:\"/?=\\\\]+$").match
    return _token_match(string)

def _unescape(string):
    assert string[0] == '"'
    assert string[-1] == '"'
    string = string[1:-1]
    if "\\" in string:
        string = re.sub(r"\\(.)", r"\1", string)
    return string


def join((major, minor, params)):
    pstr = ""
    try:
        params.items
    except AttributeError:
        pass
    else:
        params = params.items()
        # ensure a predictable order:
        params.sort()
    for name, value in params:
        pstr += ";%s=%s" % (name, _escape(value))
    return "%s/%s%s" % (major, minor, pstr)

def _escape(string):
    try:
        return _check_token(string)
    except ValueError:
        # '\\' must be first
        for c in '\\"\n\r':
            string = string.replace(c, "\\" + c)
        return '"%s"' % string
