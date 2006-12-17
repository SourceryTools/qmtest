##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Lexicon tests

$Id$
"""
import sys
from unittest import TestCase, main, makeSuite

from zope.index.text.lexicon import Lexicon
from zope.index.text.lexicon import Splitter, CaseNormalizer

class StupidPipelineElement(object):
    def __init__(self, fromword, toword):
        self.__fromword = fromword
        self.__toword = toword

    def process(self, seq):
        res = []
        for term in seq:
            if term == self.__fromword:
                res.append(self.__toword)
            else:
                res.append(term)
        return res

class WackyReversePipelineElement(object):
    def __init__(self, revword):
        self.__revword = revword

    def process(self, seq):
        res = []
        for term in seq:
            if term == self.__revword:
                x = list(term)
                x.reverse()
                res.append(''.join(x))
            else:
                res.append(term)
        return res

class StopWordPipelineElement(object):
    def __init__(self, stopdict={}):
        self.__stopdict = stopdict

    def process(self, seq):
        res = []
        for term in seq:
            if self.__stopdict.get(term):
                continue
            else:
                res.append(term)
        return res


class Test(TestCase):
    def testSourceToWordIds(self):
        lexicon = Lexicon(Splitter())
        wids = lexicon.sourceToWordIds('cats and dogs')
        self.assertEqual(wids, [1, 2, 3])

    def testTermToWordIds(self):
        lexicon = Lexicon(Splitter())
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('dogs')
        self.assertEqual(wids, [3])

    def testMissingTermToWordIds(self):
        lexicon = Lexicon(Splitter())
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('boxes')
        self.assertEqual(wids, [0])

    def testOnePipelineElement(self):
        lexicon = Lexicon(Splitter(), StupidPipelineElement('dogs', 'fish'))
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('fish')
        self.assertEqual(wids, [3])

    def testSplitterAdaptorFold(self):
        lexicon = Lexicon(Splitter(), CaseNormalizer())
        wids = lexicon.sourceToWordIds('CATS and dogs')
        wids = lexicon.termToWordIds('cats and dogs')
        self.assertEqual(wids, [1, 2, 3])

    def testSplitterAdaptorNofold(self):
        lexicon = Lexicon(Splitter())
        wids = lexicon.sourceToWordIds('CATS and dogs')
        wids = lexicon.termToWordIds('cats and dogs')
        self.assertEqual(wids, [0, 2, 3])

    def testTwoElementPipeline(self):
        lexicon = Lexicon(Splitter(),
                          StupidPipelineElement('cats', 'fish'),
                          WackyReversePipelineElement('fish'))
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('hsif')
        self.assertEqual(wids, [1])

    def testThreeElementPipeline(self):
        lexicon = Lexicon(Splitter(),
                          StopWordPipelineElement({'and':1}),
                          StupidPipelineElement('dogs', 'fish'),
                          WackyReversePipelineElement('fish'))
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('hsif')
        self.assertEqual(wids, [2])

    def testSplitterLocaleAwareness(self):
        from zope.index.text.htmlsplitter import HTMLWordSplitter
        import locale
        loc = locale.setlocale(locale.LC_ALL) # get current locale
         # set German locale
        try:
            if sys.platform != 'win32':
                locale.setlocale(locale.LC_ALL, 'de_DE.ISO8859-1')
            else:
                locale.setlocale(locale.LC_ALL, 'German_Germany.1252')
        except locale.Error:
            return # This test doesn't work here :-(
        expected = ['m\xfclltonne', 'waschb\xe4r',
                    'beh\xf6rde', '\xfcberflieger']
        words = [" ".join(expected)]
        words = Splitter().process(words)
        self.assertEqual(words, expected)
        words = HTMLWordSplitter().process(words)
        self.assertEqual(words, expected)
        locale.setlocale(locale.LC_ALL, loc) # restore saved locale

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')
