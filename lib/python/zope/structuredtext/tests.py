##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
$Id: tests.py 41188 2006-01-08 09:27:48Z philikon $
"""

import sys
import os
import unittest
import StringIO

from zope.structuredtext import stng
from zope.structuredtext.document import Document, DocumentWithImages
from zope.structuredtext.html import HTML, HTMLWithImages

package_dir = os.path.dirname(stng.__file__)
regressions = os.path.join(package_dir, 'regressions')

files = ['index.stx','Acquisition.stx','ExtensionClass.stx',
        'MultiMapping.stx','examples.stx','Links.stx','examples1.stx',
        'table.stx','InnerLinks.stx']

def readFile(dirname,fname):
    myfile = open(os.path.join(dirname, fname), "r")
    lines = myfile.readlines()
    myfile.close()
    return ''.join(lines)

class StngTests(unittest.TestCase):

    def testDocumentClass(self):
        # testing Document
        # *cough* *cough* this can't be enough...
        for f in files:
            doc = Document()
            raw_text = readFile(regressions, f)
            text = stng.structurize(raw_text)
            self.assert_(doc(text))

    def testRegressionsTests(self):
        # HTML regression test
        for f in files:
            raw_text = readFile(regressions, f)
            doc = stng.structurize(raw_text)
            doc = Document()(doc)
            html = HTML()(doc)

            reg_fname = f.replace('.stx','.ref')
            reg_html  = readFile(regressions , reg_fname)

            self.assertEqual(reg_html.strip(), html.strip())

class BasicTests(unittest.TestCase):

    def _test(self, stxtxt, expected):
        doc = stng.structurize(stxtxt)
        doc = DocumentWithImages()(doc)
        output = HTMLWithImages()(doc, level=1)
        if not expected in output:
            print "Text:     ", stxtxt.encode('utf-8')
            print "Converted:", output.encode('utf-8')
            print "Expected: ", expected.encode('utf-8')
            self.fail("'%s' not in result" % expected)        

    def testUnderline(self):
        self._test("xx _this is html_ xx",
                   "xx <u>this is html</u> xx")

    def testUnderline1(self):
        self._test("xx _this is html_",
                   "<u>this is html</u>")

    def testEmphasis(self):
        self._test("xx *this is html* xx",
                   "xx <em>this is html</em> xx")

    def testStrong(self):
        self._test("xx **this is html** xx",
                   "xx <strong>this is html</strong> xx")

    def testUnderlineThroughoutTags(self):
        self._test('<a href="index_html">index_html</a>',
                   '<a href="index_html">index_html</a>')

    def testUnderscoresInLiteral1(self):
        self._test("def __init__(self)",
                   "def __init__(self)")

    def testUnderscoresInLiteral2(self):
        self._test("this is '__a_literal__' eh",
                   "<code>__a_literal__</code>")

    def testUnderlinesWithoutWithspaces(self):
        self._test("Zopes structured_text is sometimes a night_mare",
                   "Zopes structured_text is sometimes a night_mare")

    def testAsterisksInLiteral(self):
        self._test("this is a '*literal*' eh",
        "<code>*literal*</code>")

    def testDoubleAsterisksInLiteral(self):
        self._test("this is a '**literal**' eh",
        "<code>**literal**</code>")

    def testLinkInLiteral(self):
        self._test("this is a '\"literal\":http://www.zope.org/.' eh",
        '<code>"literal":http://www.zope.org/.</code>')

    def testLink(self):
        self._test('"foo":http://www.zope.org/foo/bar',
                   '<p><a href="http://www.zope.org/foo/bar">foo</a></p>')

        self._test('"foo":http://www.zope.org/foo/bar/%20x',
                   '<p><a href="http://www.zope.org/foo/bar/%20x">foo</a></p>')

        self._test('"foo":http://www.zope.org/foo/bar?arg1=1&arg2=2',
                   '<p><a href="http://www.zope.org/foo/bar?arg1=1&arg2=2">foo</a></p>')

        self._test('"foo bar":http://www.zope.org/foo/bar',
                   '<p><a href="http://www.zope.org/foo/bar">foo bar</a></p>')

        self._test('"[link goes here]":http://www.zope.org/foo/bar',
                   '<p><a href="http://www.zope.org/foo/bar">[link goes here]</a></p>')

        self._test('"[Dad\'s car]":http://www.zope.org/foo/bar',
                   '<p><a href="http://www.zope.org/foo/bar">[Dad\'s car]</a></p>')

     
    def testImgLink(self):
        self._test('"foo":img:http://www.zope.org/bar.gif',
                   '<img src="http://www.zope.org/bar.gif" alt="foo" />')

        self._test('"foo":img:http://www.zope.org:8080/bar.gif',
                   '<img src="http://www.zope.org:8080/bar.gif" alt="foo" />')

        self._test('"foo":img:http://www.zope.org:8080/foo/bar?arg=1',
                   '<img src="http://www.zope.org:8080/foo/bar?arg=1" alt="foo" />')

        self._test('"foo":img:http://www.zope.org:8080/foo/b%20ar?arg=1',
                   '<img src="http://www.zope.org:8080/foo/b%20ar?arg=1" alt="foo" />')

        self._test('"foo bar":img:http://www.zope.org:8080/foo/bar',
                   '<img src="http://www.zope.org:8080/foo/bar" alt="foo bar" />')

        self._test('"[link goes here]":img:http://www.zope.org:8080/foo/bar',
                   '<img src="http://www.zope.org:8080/foo/bar" alt="[link goes here]" />')

        self._test('"[Dad\'s new car]":img:http://www.zope.org:8080/foo/bar',
                   '<img src="http://www.zope.org:8080/foo/bar" alt="[Dad\'s new car]" />')

    def TODOtestUnicodeContent(self):
        # This fails because ST uses the default locale to get "letters"
        # whereas it should use \w+ and re.U if the string is Unicode.
        #self._test(u"h\xe9 **y\xe9** xx",
        #           u"h\xe9 <strong>y\xe9</strong> xx")
        pass


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StngTests))
    suite.addTest(unittest.makeSuite(BasicTests))
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
