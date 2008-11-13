##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os, sys, unittest

from zope.sequencesort import ssort
from zope.sequencesort.tests.ztestlib import *
from zope.sequencesort.tests.results import *

class TestCase(unittest.TestCase):
    """Test zope.sequencesort.sort()
    """

    def test1(self):
        assert res1==ssort.sort(wordlist)

    def test2(self):
        assert res2==ssort.sort(wordlist, (("key",),), mapping=1)

    def test3(self):
        assert res3==ssort.sort(wordlist, (("key", "cmp"),), mapping=1)

    def test4(self):
        assert res4==ssort.sort(wordlist, (("key", "cmp", "desc"),),
                                mapping=1)

    def test5(self):
        assert res5==ssort.sort(wordlist, (("weight",), ("key",)),
                                mapping=1)

    def test6(self):
        assert res6==ssort.sort(wordlist,
                                (("weight",),
                                 ("key", "nocase", "desc")),
                                mapping=1)

    def test7(self):
        def myCmp(s1, s2):
            return -cmp(s1, s2)

        md = {"myCmp" : myCmp}
        assert res7==ssort.sort(wordlist,
                                (("weight",), ("key", "myCmp", "desc")),
                                md,
                                mapping=1
                                )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
