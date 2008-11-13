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
"""Define view component for event utility control.

$Id: __init__.py 79929 2007-09-24 21:59:36Z rogerineichen $
"""
from zope.publisher.browser import BrowserView

from zope.app import zapi
from zope.error.interfaces import IErrorReportingUtility
from zope.error.interfaces import ILocalErrorReportingUtility


class EditErrorLog(object):
    __used_for__ = ILocalErrorReportingUtility

    def updateProperties(self, keep_entries, copy_to_zlog=None,
                         ignored_exceptions=None):
        errorLog = self.context
        if copy_to_zlog is None:
            copy_to_zlog = 0
        errorLog.setProperties(keep_entries, copy_to_zlog, ignored_exceptions)
        return self.request.response.redirect('@@configure.html')


class ErrorRedirect(BrowserView):

    def action(self):
        # Some locations (eg ++etc++process) throw a TypeError exception when
        # finding their absoluteurl, if this happens catch the error and
        # redirect the browser to the site root "/@@errorRedirect.html"
        # to handle redirection to the site error logger instead
        try:
            err = zapi.getUtility(IErrorReportingUtility)
            url = zapi.absoluteURL(err, self.request)
        except TypeError:
            url = self.request.getApplicationURL() + "/@@errorRedirect.html"
        else:
            url = url + "/@@SelectedManagementView.html"

        self.request.response.redirect(url)
