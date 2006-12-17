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
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Text Index Tests

$Id$
"""
from unittest import TestCase, TestSuite, main, makeSuite

from zope.index.text.lexicon import Lexicon, Splitter
from zope.index.text.cosineindex import CosineIndex
from zope.index.text.okapiindex import OkapiIndex

# Subclasses must set a class variable IndexFactory to the appropriate
# index object constructor.

class IndexTest(TestCase):

    def setUp(self):
        self.lexicon = Lexicon(Splitter())
        self.index = self.IndexFactory(self.lexicon)


    def _test_index_document_assertions(self, DOCID=1):
        self.assertEqual(self.index.documentCount(), 1)
        self.assertEqual(self.index.wordCount(), 5)
        self.assertEqual(self.lexicon.wordCount(), 5)
        self.assert_(self.index.has_doc(DOCID))
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._docweight), 1)
        self.assertEqual(len(self.index._wordinfo), 5)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index.get_words(DOCID)), 5)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.wordCount())
        for map in self.index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_index_document(self, DOCID=1):
        doc = "simple document contains five words"
        self.assert_(not self.index.has_doc(DOCID))
        self.index.index_doc(DOCID, doc)
        self._test_index_document_assertions(DOCID)

    def test_unindex_document_absent_docid(self):
        self.test_index_document(1)
        self.index.unindex_doc(2)
        self._test_index_document_assertions(1)

    def test_clear(self):
        self.test_index_document(1)
        self.index.clear()
        self._test_unindex_document_assertions()

    def _test_unindex_document_assertions(self):
        self.assertEqual(len(self.index._docweight), 0)
        self.assertEqual(len(self.index._wordinfo), 0)
        self.assertEqual(len(self.index._docwords), 0)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.wordCount())

    def test_unindex_document(self):
        DOCID = 1
        self.test_index_document(DOCID)
        self.index.unindex_doc(DOCID)
        self._test_unindex_document_assertions()
        

    def test_index_two_documents(self):
        self.test_index_document()
        doc = "another document just four"
        DOCID = 2
        self.index.index_doc(DOCID, doc)
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._docweight), 2)
        self.assertEqual(len(self.index._wordinfo), 8)
        self.assertEqual(len(self.index._docwords), 2)
        self.assertEqual(len(self.index.get_words(DOCID)), 4)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.wordCount())
        wids = self.lexicon.termToWordIds("document")
        self.assertEqual(len(wids), 1)
        document_wid = wids[0]
        for wid, map in self.index._wordinfo.items():
            if wid == document_wid:
                self.assertEqual(len(map), 2)
                self.assert_(map.has_key(1))
                self.assert_(map.has_key(DOCID))
            else:
                self.assertEqual(len(map), 1)

    def test_index_two_unindex_one(self):
        # index two documents, unindex one, and test the results
        self.test_index_two_documents()
        self.index.unindex_doc(1)
        DOCID = 2
        self.assertEqual(len(self.index._docweight), 1)
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._wordinfo), 4)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index.get_words(DOCID)), 4)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.wordCount())
        for map in self.index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_index_duplicated_words(self, DOCID=1):
        doc = "very simple repeat repeat repeat document test"
        self.index.index_doc(DOCID, doc)
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._wordinfo), 5)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index.get_words(DOCID)), 7)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.wordCount())
        wids = self.lexicon.termToWordIds("repeat")
        self.assertEqual(len(wids), 1)
        repititive_wid = wids[0]
        for wid, map in self.index._wordinfo.items():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_simple_query_oneresult(self):
        self.index.index_doc(1, 'not the same document')
        results = self.index.search("document")
        self.assertEqual(list(results.keys()), [1])

    def test_simple_query_noresults(self):
        self.index.index_doc(1, 'not the same document')
        results = self.index.search("frobnicate")
        self.assertEqual(list(results.keys()), [])

    def test_query_oneresult(self):
        self.index.index_doc(1, 'not the same document')
        self.index.index_doc(2, 'something about something else')
        results = self.index.search("document")
        self.assertEqual(list(results.keys()), [1])

    def test_search_phrase(self):
        self.index.index_doc(1, "the quick brown fox jumps over the lazy dog")
        self.index.index_doc(2, "the quick fox jumps lazy over the brown dog")
        results = self.index.search_phrase("quick brown fox")
        self.assertEqual(list(results.keys()), [1])

    def test_search_glob(self):
        self.index.index_doc(1, "how now brown cow")
        self.index.index_doc(2, "hough nough browne cough")
        self.index.index_doc(3, "bar brawl")
        results = self.index.search_glob("bro*")
        self.assertEqual(list(results.keys()), [1, 2])
        results = self.index.search_glob("b*")
        self.assertEqual(list(results.keys()), [1, 2, 3])

class CosineIndexTest(IndexTest):
    IndexFactory = CosineIndex

class OkapiIndexTest(IndexTest):
    IndexFactory = OkapiIndex

def test_suite():
    return TestSuite((makeSuite(CosineIndexTest),
                      makeSuite(OkapiIndexTest),
                    ))

if __name__=='__main__':
    main(defaultTest='test_suite')
