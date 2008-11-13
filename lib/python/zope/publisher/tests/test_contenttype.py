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
"""Tests of the contenttype helpers.

"""
__docformat__ = "reStructuredText"

import re
import unittest

from zope.publisher import contenttype


class ParseOrderedTestCase(unittest.TestCase):

    empty_params = []

    def setUp(self):
        self.parse = contenttype.parseOrdered

    def oneParam(self, name, value):
        return [(name, value)]

    def test_without_params(self):
        self.assertEqual(self.parse("text/plain"),
                         ("text", "plain", self.empty_params))
        self.assertEqual(self.parse("TEXT/PLAIN"),
                         ("text", "plain", self.empty_params))
        self.assertEqual(self.parse("TeXt / PlaIN"),
                         ("text", "plain", self.empty_params))
        self.assertEqual(self.parse("text / vnd.wap.wml"),
                         ("text", "vnd.wap.wml", self.empty_params))

    def test_with_empty_params(self):
        self.assertEqual(self.parse("text/plain ; "),
                         ("text", "plain", self.empty_params))
        self.assertEqual(self.parse("TEXT/PLAIN ;   "),
                         ("text", "plain", self.empty_params))
        self.assertEqual(self.parse("TeXt / PlaIN ; "),
                         ("text", "plain", self.empty_params))

    def test_bad_tokens(self):
        self.assertRaises(ValueError,
                          self.parse, "text stuff/plain")
        self.assertRaises(ValueError,
                          self.parse, "text/plain stuff")
        self.assertRaises(ValueError,
                          self.parse, "text/plain;some stuff=foo")
        self.assertRaises(ValueError,
                          self.parse, "text/plain;a=b;c d=e")

    def test_missing_parts(self):
        self.assertRaises(ValueError,
                          self.parse, "text ; params")
        self.assertRaises(ValueError,
                          self.parse, "text/ ; params")
        self.assertRaises(ValueError,
                          self.parse, "/plain ; params")
        self.assertRaises(ValueError,
                          self.parse, "text/plain ; params")
        self.assertRaises(ValueError,
                          self.parse, "text/plain ; params=")
        self.assertRaises(ValueError,
                          self.parse, "text/plain ; =params")
        self.assertRaises(ValueError,
                          self.parse, "text/plain ; a=b; params")
        self.assertRaises(ValueError,
                          self.parse, "text/plain ; a=b; params=")
        self.assertRaises(ValueError,
                          self.parse, "text/plain ; a=b; =params")

    def test_single_parameter(self):
        self.assertEqual(self.parse("text/plain;charset=UTF-8"),
                         ("text", "plain", self.oneParam("charset", "UTF-8")))
        self.assertEqual(self.parse("text/plain ;\tcharset = UTF-8"),
                         ("text", "plain", self.oneParam("charset", "UTF-8")))
        # quoted-string parameter values
        self.assertEqual(self.parse('text/plain;charset="UTF-8"'),
                         ("text", "plain", self.oneParam("charset", "UTF-8")))
        self.assertEqual(self.parse('text/plain ;\tcharset = "UTF-8"'),
                         ("text", "plain", self.oneParam("charset", "UTF-8")))

    def test_multiple_parameters(self):
        self.assertEqual(
            self.parse("text/plain;charset=utf-8;format=flowed"),
            ("text", "plain", [("charset", "utf-8"), ("format", "flowed")]))
        self.assertEqual(
            self.parse('text/plain;charset=utf-8;format="flowed"'),
            ("text", "plain", [("charset", "utf-8"), ("format", "flowed")]))

    def test_quoted_strings(self):
        p = self.oneParam("c", " This [] has <> ? other () chars\t")
        self.assertEqual(
            self.parse('a/b;c= " This [] has <> ? other () chars\t" '),
            ("a", "b", p))
        self.assertEqual(
            self.parse('a/b;c=""'),
            ("a", "b", self.oneParam("c", "")))
        self.assertEqual(
            self.parse(r'a/b;c="\\\""'),
            ("a", "b", self.oneParam("c", r'\"')))

class ParseTestCase(ParseOrderedTestCase):

    empty_params = {}

    def setUp(self):
        self.parse = contenttype.parse

    def oneParam(self, name, value):
        return {name: value}

    def test_multiple_parameters(self):
        self.assertEqual(
            self.parse("text/plain;charset=utf-8;format=flowed"),
            ("text", "plain", {"charset": "utf-8", "format": "flowed"}))
        self.assertEqual(
            self.parse('text/plain;charset=utf-8;format="flowed"'),
            ("text", "plain", {"charset": "utf-8", "format": "flowed"}))


class JoinTestCase(unittest.TestCase):

    def test_without_params(self):
        self.assertEqual(contenttype.join(("text", "plain", [])),
                         "text/plain")
        self.assertEqual(contenttype.join(("text", "plain", {})),
                         "text/plain")

    def test_single_token_param(self):
        self.assertEqual(
            contenttype.join(("text", "plain", [("charset", "UTF-8")])),
            "text/plain;charset=UTF-8")
        self.assertEqual(
            contenttype.join(("text", "plain", {"charset": "UTF-8"})),
            "text/plain;charset=UTF-8")

    def test_multi_params_list_maintains_order(self):
        # multiple parameters given as a list maintain order:
        self.assertEqual(
            contenttype.join(("text", "plain",
                              [("charset", "UTF-8"), ("format", "flowed")])),
            "text/plain;charset=UTF-8;format=flowed")
        self.assertEqual(
            contenttype.join(("text", "plain",
                              [("format", "flowed"), ("charset", "UTF-8")])),
            "text/plain;format=flowed;charset=UTF-8")

    def test_multi_params_dict_sorted_order(self):
        # multiple parameters given as a dict are sorted by param name:
        self.assertEqual(
            contenttype.join(("text", "plain",
                              {"charset": "UTF-8", "format": "flowed"})),
            "text/plain;charset=UTF-8;format=flowed")

    def test_params_list_quoted(self):
        # parameter values are quoted automatically:
        self.assertEqual(contenttype.join(("a", "b", [("c", "")])),
                         'a/b;c=""')
        self.assertEqual(contenttype.join(("a", "b", [("c", "ab cd")])),
                         'a/b;c="ab cd"')
        self.assertEqual(contenttype.join(("a", "b", [("c", " \t")])),
                         'a/b;c=" \t"')
        self.assertEqual(contenttype.join(("a", "b", [("c", '"')])),
                         r'a/b;c="\""')
        self.assertEqual(contenttype.join(("a", "b", [("c", "\n")])),
                         'a/b;c="\\\n"')

    def test_params_dict_quoted(self):
        # parameter values are quoted automatically:
        self.assertEqual(contenttype.join(("a", "b", {"c": ""})),
                         'a/b;c=""')
        self.assertEqual(contenttype.join(("a", "b", {"c": "ab cd"})),
                         'a/b;c="ab cd"')
        self.assertEqual(contenttype.join(("a", "b", {"c": " \t"})),
                         'a/b;c=" \t"')
        self.assertEqual(contenttype.join(("a", "b", {"c": '"'})),
                         r'a/b;c="\""')
        self.assertEqual(contenttype.join(("a", "b", {"c": "\n"})),
                         'a/b;c="\\\n"')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ParseOrderedTestCase))
    suite.addTest(unittest.makeSuite(ParseTestCase))
    suite.addTest(unittest.makeSuite(JoinTestCase))
    return suite
