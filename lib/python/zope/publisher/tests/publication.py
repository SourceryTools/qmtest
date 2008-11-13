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
"""Publication test

$Id: publication.py 38357 2005-09-07 20:14:34Z srichter $
"""

from zope.publisher.interfaces import IPublication
from zope.interface import implements

class TestPublication(object):

    implements(IPublication)

    def afterCall(self, request, ob):
        '''See interface IPublication'''
        self._afterCall = getattr(self, '_afterCall', 0) + 1

    def endRequest(self, request, ob):
        '''See interface IPublication'''
        self._endRequest = getattr(self, '_endRequest', 0) + 1

    def traverseName(self, request, ob, name, check_auth=1):
        '''See interface IPublication'''
        return getattr(ob, name, "%s value" % name)

    def afterTraversal(self, request, ob):
        '''See interface IPublication'''
        self._afterTraversal = getattr(self, '_afterTraversal', 0) + 1

    def beforeTraversal(self, request):
        '''See interface IPublication'''
        self._beforeTraversal = getattr(self, '_beforeTraversal', 0) + 1

    def callObject(self, request, ob):
        '''See interface IPublication'''
        return ob(request)

    def getApplication(self, request):
        '''See interface IPublication'''
        return app

    def handleException(self, object, request, exc_info, retry_allowed=1):
        '''See interface IPublication'''
        try:
            request.response.setResult("%s: %s" % (exc_info[:2]))
        finally:
            exc_info = 0


    def callTraversalHooks(self, request, ob):
        '''See interface IPublication'''
        self._callTraversalHooks = getattr(self, '_callTraversalHooks', 0) + 1


class App(object):

    def __init__(self, name):
        self.name = name

    def index_html(self, request):
        return self

app = App('')
app.ZopeCorp = App('ZopeCorp')
app.ZopeCorp.Engineering = App('Engineering')
