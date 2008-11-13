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
"""Tests for the talgettext utility.

$Id: test_talgettext.py 30452 2005-05-20 05:13:10Z fdrake $
"""
import sys
import unittest
from StringIO import StringIO

from zope.tal.htmltalparser import HTMLTALParser
from zope.tal.talgettext import POTALInterpreter
from zope.tal.talgettext import POEngine
from zope.tal.tests import utils

class test_POEngine(unittest.TestCase):
    """Test the PO engine functionality, which simply adds items to a catalog
    as .translate is called
    """

    def test_translate(self):
        test_keys = ['foo', 'bar', 'blarf', 'washington']

        engine = POEngine()
        engine.file = 'foo.pt'
        for key in test_keys:
            engine.translate(key, 'domain')

        for key in test_keys:
            self.failIf(key not in engine.catalog['domain'],
                        "POEngine catalog does not properly store message ids"
                        )

    def test_dynamic_msgids(self):
        sample_source = """
            <p i18n:translate="">
              Some
              <span tal:replace="string:strange">dynamic</span>
              text.
            </p>
            <p i18n:translate="">
              A <a tal:attributes="href path:dynamic">link</a>.
            </p>
        """
        p = HTMLTALParser()
        p.parseString(sample_source)
        program, macros = p.getCode()
        engine = POEngine()
        engine.file = 'sample_source'
        POTALInterpreter(program, macros, engine, stream=StringIO(),
                         metal=False)()
        msgids = []
        for domain in engine.catalog.values():
            msgids += domain.keys()
        msgids.sort()
        self.assertEquals(msgids,
            ['A <a href="${DYNAMIC_CONTENT}">link</a>.',
            'Some ${DYNAMIC_CONTENT} text.'])


def test_suite():
    suite = unittest.makeSuite(test_POEngine)
    return suite

if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
