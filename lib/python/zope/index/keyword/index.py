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
"""Keyword index

$Id$
"""
from persistent import Persistent

from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree, OOSet, difference 
from BTrees.IIBTree import IISet, union, intersection
from BTrees.Length import Length

from types import StringTypes
from zope.index.interfaces import IInjection, IStatistics
from zope.index.keyword.interfaces import IKeywordQuerying
from zope.interface import implements

class KeywordIndex(Persistent):
    """ A case-insensitive keyword index """

    normalize = True
    implements(IInjection, IStatistics, IKeywordQuerying)

    def __init__(self):
        self.clear()

    def clear(self):
        """Initialize forward and reverse mappings."""

        # The forward index maps index keywords to a sequence of docids
        self._fwd_index = OOBTree()

        # The reverse index maps a docid to its keywords
        # TODO: Using a vocabulary might be the better choice to store
        # keywords since it would allow use to use integers instead of strings
        self._rev_index = IOBTree()
        self._num_docs = Length(0)

    def documentCount(self):
        """Return the number of documents in the index."""
        return self._num_docs()

    def wordCount(self):
        """Return the number of indexed words"""
        return len(self._fwd_index)

    def has_doc(self, docid):
        return bool(self._rev_index.has_key(docid))

    def index_doc(self, docid, seq):
        if isinstance(seq, StringTypes):
            raise TypeError('seq argument must be a list/tuple of strings')
    
        if not seq:
            return

        if self.normalize:
            seq = [w.lower() for w in seq]

        old_kw = self._rev_index.get(docid, None)
        new_kw = OOSet(seq)

        if old_kw is None:
            self._insert_forward(docid, new_kw)
            self._insert_reverse(docid, new_kw)
            self._num_docs.change(1)
        else:

            # determine added and removed keywords
            kw_added = difference(new_kw, old_kw)
            kw_removed = difference(old_kw, new_kw)

            # removed keywords are removed from the forward index
            for word in kw_removed:
                self._fwd_index[word].remove(docid)
            
            # now update reverse and forward indexes
            self._insert_forward(docid, kw_added)
            self._insert_reverse(docid, new_kw)
        
    def unindex_doc(self, docid):
        idx  = self._fwd_index

        try:
            for word in self._rev_index[docid]:
                idx[word].remove(docid)
                if not idx[word]:
                    del idx[word] 
        except KeyError:
            return
        
        try:
            del self._rev_index[docid]
        except KeyError:
            pass

        self._num_docs.change(-1)

    def _insert_forward(self, docid, words):
        """insert a sequence of words into the forward index """

        idx = self._fwd_index
        has_key = idx.has_key
        for word in words:
            if not has_key(word):
                idx[word] = IISet()
            idx[word].insert(docid)

    def _insert_reverse(self, docid, words):
        """ add words to forward index """

        if words:
            self._rev_index[docid] = words

    def search(self, query, operator='and'):
        """Execute a search given by 'query'."""
        if isinstance(query, StringTypes):
            query = [query]

        if self.normalize:
            query = [w.lower() for w in query]

        f = {'and' : intersection, 'or' : union}[operator]
    
        rs = None
        for word in query:
            docids = self._fwd_index.get(word, IISet())
            rs = f(rs, docids)
            
        if rs:
            return rs
        else:
            return IISet()

class CaseSensitiveKeywordIndex(KeywordIndex):
    """ A case-sensitive keyword index """
    normalize = False        
