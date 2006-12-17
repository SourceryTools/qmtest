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
"""DT_SQLVar Tests

$Id: test_arguments.py 25177 2004-06-02 13:17:31Z jim $
"""

import unittest

from zope.app.sqlscript.sqlscript import Arguments, \
     parseArguments, InvalidParameter

class TestDT_SQLVar(unittest.TestCase):

    def _compareArgumentObjects(self, result, args):
        self.assertEqual(args.items(), result.items())

    def testSimpleParseArgument(self):
        args = parseArguments('arg1')
        result = Arguments({'arg1': {}})
        self._compareArgumentObjects(result, args)

    def testParseArgumentWithType(self):
        args = parseArguments('arg1:int')
        result = Arguments({'arg1': {'type': 'int'}})
        self._compareArgumentObjects(result, args)

    def testParseArgumentWithDefault(self):
        args1 = parseArguments('arg1=value')
        result1 = Arguments({'arg1': {'default': 'value'}})
        self._compareArgumentObjects(result1, args1)

        args2 = parseArguments('arg1="value"')
        result2 = Arguments({'arg1': {'default': 'value'}})
        self._compareArgumentObjects(result2, args2)

    def testParseArgumentWithTypeAndDefault(self):
        args1 = parseArguments('arg1:string=value')
        result1 = Arguments({'arg1': {'default': 'value', 'type': 'string'}})
        self._compareArgumentObjects(result1, args1)

        args2 = parseArguments('arg1:string="value"')
        result2 = Arguments({'arg1': {'default': 'value', 'type': 'string'}})
        self._compareArgumentObjects(result2, args2)

    def testParseMultipleArguments(self):
        args1 = parseArguments('arg1:string=value arg2')
        result1 = Arguments({'arg1': {'default': 'value', 'type': 'string'},
                             'arg2': {}})
        self._compareArgumentObjects(result1, args1)

        args2 = parseArguments('arg1:string=value\narg2')
        result2 = Arguments({'arg1': {'default': 'value', 'type': 'string'},
                             'arg2': {}})
        self._compareArgumentObjects(result2, args2)

    def testParseErrors(self):
        self.assertRaises(InvalidParameter, parseArguments, 'arg1:""')
        self.assertRaises(InvalidParameter, parseArguments, 'arg1 = value')
        self.assertRaises(InvalidParameter, parseArguments, 'arg1="value\' ')
        self.assertRaises(InvalidParameter, parseArguments, 'arg1:=value')


def test_suite():
    return unittest.makeSuite(TestDT_SQLVar)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
