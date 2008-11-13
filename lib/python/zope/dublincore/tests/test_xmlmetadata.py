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
"""Test loading of Dublin Core metadata from the XML representation.

$Id: test_xmlmetadata.py 66902 2006-04-12 20:16:30Z philikon $
"""
import unittest

from zope.dublincore import dcterms
from zope.dublincore.xmlmetadata import dumpString, parseString


class XMLDublinCoreLoadingTests(unittest.TestCase):

    # Note: We're not using the 'traditional' namespace prefixes in
    # the tests since we want to make sure we're doing the right thing
    # in the content handler.  Also, we should use something we're not
    # using in zope.dublincore.dcterms.
    _prefix = ("<?xml version='1.0' encoding='utf-8'?>\n"
               "<metadata xmlns:d='%s'\n"
               "          xmlns:t='%s'\n"
               "          xmlns:s='%s'>\n"
               % (dcterms.DC_NS, dcterms.DCTERMS_NS, dcterms.XSI_NS))
    _suffix = "\n</metadata>"

    def parse(self, text):
        return parseString("%s%s%s" % (self._prefix, text, self._suffix))

    def check1(self, text, name, value, generic=None):
        expected = {name: (value,)}
        m = self.parse(text)
        self.assertEqual(m, expected)
        m = self.parse("<wrap>%s</wrap>" % text)
        self.assertEqual(m, expected)
        if generic:
            m = self.parse("<%s>%s</%s>" % (generic, text, generic))
            self.assertEqual(m, expected)
            m = self.parse("<%s><wrap>%s</wrap></%s>"
                           % (generic, text, generic))
            self.assertEqual(m, expected)

    # tests with acceptable input

    def test_empty(self):
        m = parseString("<metadata/>")
        self.assertEqual(m, {})

    # core elements and related refinements

    def test_simple_title(self):
        self.check1("<d:title>Foo</d:title>", "Title", u"Foo")

    def test_two_titles(self):
        m = self.parse("<d:title>Foo</d:title>"
                       "<d:title>Bar</d:title>")
        self.assertEqual(m, {"Title": (u"Foo", u"Bar")})

    def test_alternative_title(self):
        m = self.parse("<d:title>Foo</d:title>"
                       "<t:alternative>Bar</t:alternative>")
        self.assertEqual(m, {"Title": (u"Foo",),
                             "Title.Alternative": (u"Bar",)})

    def test_creator(self):
        self.check1("<d:creator>somebody</d:creator>",
                    "Creator", "somebody")

    def test_subject(self):
        self.check1("<d:subject>something</d:subject>",
                    "Subject", "something")
        self.check1("<d:subject s:type='t:LCSH'>something</d:subject>",
                    "Subject.LCSH", "something")
        self.check1("<d:subject s:type='t:MESH'>something</d:subject>",
                    "Subject.MESH", "something")
        self.check1("<d:subject s:type='t:DDC'>something</d:subject>",
                    "Subject.DDC", "something")
        self.check1("<d:subject s:type='t:LCC'>something</d:subject>",
                    "Subject.LCC", "something")
        self.check1("<d:subject s:type='t:UDC'>something</d:subject>",
                    "Subject.UDC", "something")

    def test_description(self):
        self.check1("<d:description>foo</d:description>",
                    "Description", "foo")
        self.check1("<t:abstract>foo</t:abstract>",
                    "Description.Abstract", "foo", generic="d:description")
        self.check1("<t:tableOfContents>foo</t:tableOfContents>",
                    "Description.Table Of Contents", "foo",
                    generic="d:description")

    def test_publisher(self):
        self.check1("<d:publisher>pub</d:publisher>",
                    "Publisher", "pub")

    def test_contributor(self):
        self.check1("<d:contributor>somebody</d:contributor>",
                    "Contributor", "somebody")

    def test_date(self):
        self.check1("<d:date>2003-08-20</d:date>",
                    "Date", "2003-08-20")
        # refinements used by Zope
        self.check1("<t:created>2003-08-20</t:created>",
                    "Date.Created", "2003-08-20", generic="d:date")
        self.check1("<t:modified>2003-08-20</t:modified>",
                    "Date.Modified", "2003-08-20", generic="d:date")
        # other refinements
        self.check1("<t:accepted>2003-08-20</t:accepted>",
                    "Date.Accepted", "2003-08-20", generic="d:date")
        self.check1("<t:available>2003-08-20</t:available>",
                    "Date.Available", "2003-08-20", generic="d:date")
        self.check1("<t:copyrighted>2003-08-20</t:copyrighted>",
                    "Date.Copyrighted", "2003-08-20", generic="d:date")
        self.check1("<t:issued>2003-08-20</t:issued>",
                    "Date.Issued", "2003-08-20", generic="d:date")
        self.check1("<t:submitted>2003-08-20</t:submitted>",
                    "Date.Submitted", "2003-08-20", generic="d:date")
        self.check1("<t:valid>2003-08-20</t:valid>",
                    "Date.Valid", "2003-08-20", generic="d:date")

    def test_type(self):
        self.check1("<d:type>some type</d:type>",
                    "Type", "some type")
        self.check1("<d:type s:type='t:DCMIType'>Collection</d:type>",
                    "Type.DCMIType", "Collection")

    def test_format(self):
        self.check1("<d:format>some format</d:format>",
                    "Format", "some format")
        self.check1("<d:format s:type='t:IMT'>text/xml</d:format>",
                    "Format.IMT", "text/xml")
        self.check1("<t:extent>1 hour</t:extent>",
                    "Format.Extent", "1 hour", generic="d:format")
        self.check1("<t:medium>70mm IMAX celluloid</t:medium>",
                    "Format.Medium", "70mm IMAX celluloid", generic="d:format")

    def test_identifier(self):
        self.check1("<d:identifier>ident</d:identifier>",
                    "Identifier", "ident")
        self.check1("<t:bibliographicCitation>"
                    "  citation  "
                    "</t:bibliographicCitation>",
                    "Identifier.Bibliographic Citation", "citation",
                    generic="d:identifier")

    def test_source(self):
        self.check1("<d:source>src</d:source>",
                    "Source", "src")
        self.check1("<d:source s:type='t:URI'>http://example.com/</d:source>",
                    "Source.URI", "http://example.com/")

    def test_language(self):
        self.check1("<d:language>Klingon</d:language>",
                    "Language", "Klingon")
        self.check1("<d:language s:type='t:ISO639-2'>abc</d:language>",
                    "Language.ISO639-2", "abc")
        self.check1("<d:language s:type='t:RFC1766'>en</d:language>",
                    "Language.RFC1766", "en")
        self.check1("<d:language s:type='t:RFC3066'>en-GB-oed</d:language>",
                    "Language.RFC3066", "en-GB-oed")

    def test_relation(self):
        self.check1("<d:relation>rel</d:relation>",
                    "Relation", "rel")
        self.check1("<t:isVersionOf>that</t:isVersionOf>",
                    "Relation.Is Version Of", "that", generic="d:relation")
        self.check1("<t:hasVersion>that</t:hasVersion>",
                    "Relation.Has Version", "that", generic="d:relation")
        self.check1("<t:isReplacedBy>that</t:isReplacedBy>",
                    "Relation.Is Replaced By", "that", generic="d:relation")
        self.check1("<t:replaces>that</t:replaces>",
                    "Relation.Replaces", "that", generic="d:relation")
        self.check1("<t:isRequiredBy>that</t:isRequiredBy>",
                    "Relation.Is Required By", "that", generic="d:relation")
        self.check1("<t:requires>that</t:requires>",
                    "Relation.Requires", "that", generic="d:relation")
        self.check1("<t:isPartOf>that</t:isPartOf>",
                    "Relation.Is Part Of", "that", generic="d:relation")
        self.check1("<t:hasPart>that</t:hasPart>",
                    "Relation.Has Part", "that", generic="d:relation")
        self.check1("<t:isReferencedBy>that</t:isReferencedBy>",
                    "Relation.Is Referenced By", "that", generic="d:relation")
        self.check1("<t:references>that</t:references>",
                    "Relation.References", "that", generic="d:relation")
        self.check1("<t:isFormatOf>that</t:isFormatOf>",
                    "Relation.Is Format Of", "that", generic="d:relation")
        self.check1("<t:hasFormat>that</t:hasFormat>",
                    "Relation.Has Format", "that", generic="d:relation")
        self.check1("<t:conformsTo>that</t:conformsTo>",
                    "Relation.Conforms To", "that", generic="d:relation")

    def test_coverage(self):
        self.check1("<d:coverage>how much</d:coverage>",
                    "Coverage", "how much")
        self.check1("<t:spatial>where</t:spatial>",
                    "Coverage.Spatial", "where", generic="d:coverage")
        self.check1("<t:temporal>when</t:temporal>",
                    "Coverage.Temporal", "when", generic="d:coverage")
        self.check1("<t:temporal s:type='t:Period'>"
                    "  name=Period Name; start=1812; end=2112;  "
                    "</t:temporal>",
                    "Coverage.Temporal.Period",
                    "name=Period Name; start=1812; end=2112;",
                    generic="d:coverage")
        self.check1("<t:temporal s:type='t:W3CDTF'>2003-08-20</t:temporal>",
                    "Coverage.Temporal.W3CDTF", "2003-08-20",
                    generic="d:coverage")

    def test_rights(self):
        self.check1("<d:rights>rights</d:rights>",
                    "Rights", "rights")
        self.check1("<t:accessRights>rights</t:accessRights>",
                    "Rights.Access Rights", "rights", generic="d:rights")

    # non-core elements

    def test_audience(self):
        # Audience is the only DCMI element not in the core
        self.check1("<t:audience>people</t:audience>",
                    "Audience", "people")
        self.check1("<t:educationLevel>people</t:educationLevel>",
                    "Audience.Education Level", "people", generic="t:audience")
        self.check1("<t:mediator>people</t:mediator>",
                    "Audience.Mediator", "people", generic="t:audience")

    def test_nested_refinement(self):
        # direct nesting
        self.check1(("<d:title>"
                     "<t:alternative>Foo</t:alternative>"
                     "</d:title>"),
                    "Title.Alternative", u"Foo")
        # nesting with an intermediate element
        self.check1(("<d:title>"
                     "<x><t:alternative>Foo</t:alternative></x>"
                     "</d:title>"),
                    "Title.Alternative", u"Foo")

    # tests with errors in the input

    def test_invalid_nested_refinement(self):
        self.assertRaises(ValueError, self.parse,
                          ("<d:format>"
                           "<t:alternative>Title</t:alternative>"
                           "</d:format>"))
        self.assertRaises(ValueError, self.parse,
                          ("<d:format>"
                           "<x><t:alternative>Title</t:alternative></x>"
                           "</d:format>"))

    def test_invalid_type(self):
        self.assertRaises(ValueError, self.parse,
                          "<d:subject s:type='t:IMT'>x</d:subject>")

    def test_invalid_dcmitype(self):
        self.assertRaises(ValueError, self.parse,
                          "<d:type s:type='t:DCMIType'>flub</d:type>")

class XMLDublinCoreSerializationTests(unittest.TestCase):

    def roundtrip(self, mapping):
        text = dumpString(mapping)
        parsed = parseString(text)
        self.assertEqual(parsed, mapping)

    def test_serialize_empty(self):
        self.roundtrip({})

    def test_single_entry(self):
        self.roundtrip({"Title.Alternative": (u"Foo",)})

    def test_two_titles(self):
        self.roundtrip({"Title": (u"Foo", u"Bar")})


def test_suite():
    suite = unittest.makeSuite(XMLDublinCoreLoadingTests)
    suite.addTest(unittest.makeSuite(XMLDublinCoreSerializationTests))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
