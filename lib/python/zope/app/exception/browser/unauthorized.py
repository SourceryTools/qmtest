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
"""Unauthorized Exception View Class

$Id: unauthorized.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.publisher.browser import BrowserPage
from zope.formlib import namedtemplate

from zope.app import zapi
from zope.app.pagetemplate import ViewPageTemplateFile

class Unauthorized(BrowserPage):

    def __call__(self):
        # Set the error status to 403 (Forbidden) in the case when we don't
        # challenge the user
        self.request.response.setStatus(403)
        principal = self.request.principal
        auth = zapi.principals()
        auth.unauthorized(principal.id, self.request)
        if self.request.response.getStatus() not in (302, 303):
            return self.template()

    template = namedtemplate.NamedTemplate('default')

default_template = namedtemplate.NamedTemplateImplementation(
    ViewPageTemplateFile('unauthorized.pt'), Unauthorized)
