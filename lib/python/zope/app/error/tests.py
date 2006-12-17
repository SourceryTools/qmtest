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
"""Error Reporting Utility Tests

$Id: tests.py 41724 2006-02-21 13:27:44Z hdima $
"""
import sys
import unittest

from zope.exceptions.exceptionformatter import format_exception
from zope.publisher.tests.httprequest import TestRequest
from zope.app.testing.placelesssetup import PlacelessSetup

from zope.app.error.error import ErrorReportingUtility, getFormattedException

class Error(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

def getAnErrorInfo(value=""):
    try:
        raise Error(value)
    except:
        return sys.exc_info()

class ErrorReportingUtilityTests(PlacelessSetup, unittest.TestCase):

    def test_checkForEmpryLog(self):
        # Test Check Empty Log
        errUtility = ErrorReportingUtility()
        getProp = errUtility.getLogEntries()
        self.failIf(getProp)

    def test_checkProperties(self):
        # Test Properties test
        errUtility = ErrorReportingUtility()
        setProp = {
            'keep_entries':10,
            'copy_to_zlog':1,
            'ignored_exceptions':()
            }
        errUtility.setProperties(**setProp)
        getProp = errUtility.getProperties()
        self.assertEqual(setProp, getProp)

    def test_ErrorLog(self):
        # Test for Logging Error.  Create one error and check whether its
        # logged or not.
        errUtility = ErrorReportingUtility()
        exc_info = getAnErrorInfo()
        errUtility.raising(exc_info)
        getErrLog = errUtility.getLogEntries()
        self.assertEquals(1, len(getErrLog))

        tb_text = ''.join(format_exception(as_html=0, *exc_info))

        err_id = getErrLog[0]['id']
        self.assertEquals(tb_text,
                          errUtility.getLogEntryById(err_id)['tb_text'])

    def test_ErrorLog_unicode(self):
        # Emulate a unicode url, it gets encoded to utf-8 before it's passed
        # to the request. Also add some unicode field to the request's
        # environment and make the principal's title unicode.
        request = TestRequest(environ={'PATH_INFO': '/\xd1\x82',
                                       'SOME_UNICODE': u'\u0441'})
        class PrincipalStub(object):
            id = u'\u0441'
            title = u'\u0441'
            description = u'\u0441'
        request.setPrincipal(PrincipalStub())

        errUtility = ErrorReportingUtility()
        exc_info = getAnErrorInfo(u"Error (\u0441)")
        errUtility.raising(exc_info, request=request)
        getErrLog = errUtility.getLogEntries()
        self.assertEquals(1, len(getErrLog))

        tb_text = ''.join(format_exception(as_html=0, *exc_info))

        err_id = getErrLog[0]['id']
        self.assertEquals(tb_text,
                          errUtility.getLogEntryById(err_id)['tb_text'])

        username = getErrLog[0]['username']
        self.assertEquals(username, u'unauthenticated, \u0441, \u0441, \u0441')

    def test_ErrorLog_nonascii(self):
        # Emulate a unicode url, it gets encoded to utf-8 before it's passed
        # to the request. Also add some unicode field to the request's
        # environment and make the principal's title unicode.
        request = TestRequest(environ={'PATH_INFO': '/\xd1\x82',
                                       'SOME_NONASCII': '\xe1'})
        class PrincipalStub(object):
            id = '\xe1'
            title = '\xe1'
            description = '\xe1'
        request.setPrincipal(PrincipalStub())

        errUtility = ErrorReportingUtility()
        exc_info = getAnErrorInfo("Error (\xe1)")
        errUtility.raising(exc_info, request=request)
        getErrLog = errUtility.getLogEntries()
        self.assertEquals(1, len(getErrLog))

        tb_text = getFormattedException(exc_info)

        err_id = getErrLog[0]['id']
        self.assertEquals(tb_text,
                          errUtility.getLogEntryById(err_id)['tb_text'])

        username = getErrLog[0]['username']
        self.assertEquals(username, r"unauthenticated, \xe1, \xe1, \xe1")


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ErrorReportingUtilityTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
