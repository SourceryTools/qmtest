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
"""SQL Script Views

$Id: sqlscript.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.rdb.interfaces import DatabaseException
from zope.traversing.browser import absoluteURL
from zope.app.form.browser.submit import Update
from zope.app.sqlscript.interfaces import ISQLScript

class SQLScriptTest(object):
    """Test the SQL inside the SQL Script
    """

    __used_for__ = ISQLScript

    error = None

    def getArguments(self):
        form = self.request.form
        arguments = {}

        for argname, argvalue in self.context.getArguments().items():
            value = form.get(argname)
            if value is None:
                value = argvalue.get('default')
            if value is not None:
                arguments[argname.encode('UTF-8')] = value
        return arguments

    def getTestResults(self):
        try:
            return self.context(**self.getArguments())
        except (DatabaseException, AttributeError, Exception), error:
            self.error = error
            return []

    def getFormattedError(self):
        error = str(self.error)
        return error

    def getRenderedSQL(self):
        return self.context.getTemplate()(**self.getArguments())

class SQLScriptAdd(object):
    """Provide interface to add SQL Script
    """

    def update(self):
        """Set the Update variable for Add and Test
        >>> from zope.publisher.browser import TestRequest

        >>> rqst = TestRequest()
        >>> class Base(object):
        ...     def __init__(self, request):
        ...         self.request = request
        ...     def update(self):
        ...         self.updated = True

        >>> class V(SQLScriptAdd, Base):
        ...     pass

        >>> dc = V(rqst)
        >>> dc.update()
        >>> dc.updated
        True
        >>> 'UPDATE_SUBMIT' in rqst
        False
        >>> d = {'add_test': True}
        >>> rqst1 = TestRequest(form = d)
        >>> dc1 = V(rqst1)
        >>> dc1.update()
        >>> 'UPDATE_SUBMIT' in rqst1
        True
        """
        if 'add_test' in self.request:
            self.request.form[Update] = ''

        return super(SQLScriptAdd, self).update()

    def nextURL(self):
        """
        >>> from zope.publisher.browser import TestRequest
        >>> from zope.app.testing.placelesssetup import setUp, tearDown
        >>> setUp()
        >>> rqst = TestRequest()
        >>> class Base(object):
        ...     def __init__(self, request):
        ...         self.request = request
        ...         self.context = self
        ...         self.contentName = 'new srcipt'
        ...     def __getitem__(self, key):
        ...         return None
        ...     def nextURL(self):
        ...         return "www.zeomega.com"

        >>> class V(SQLScriptAdd, Base):
        ...     pass
        >>> 
        >>> rqst = TestRequest()
        >>> dc = V(rqst)
        >>> dc.nextURL()
        'www.zeomega.com'
        >>> d = {'add_test': True}
        >>> rqst1 = TestRequest(form = d)
        >>> dc1 = V(rqst1)
        >>> dc1.nextURL()
        'http://127.0.0.1/test.html'
        """
        if 'add_test' in self.request:
            name = self.context.contentName
            container = self.context.context
            obj = container[name]
            url = absoluteURL(obj, self.request)
            url = '%s/test.html' % url
            return url
        else:
            return super(SQLScriptAdd, self).nextURL()

class SQLScriptEdit(object):
    """Provide interface to Edit and Test  SQL Script
    """

    def update(self):
        """Set the Update variable for Change and Test
        >>> from zope.publisher.browser import TestRequest

        >>> rqst = TestRequest()
        >>> class Base(object):
        ...     def __init__(self, request):
        ...         self.request = request
        ...         self.errors  = ('no errors')
        ...     def update(self):
        ...         self.updated = True
        ...         return "update returned"

        >>> class V(SQLScriptEdit, Base):
        ...     pass

        >>> dc = V(rqst)
        >>> dc.update()
        'update returned'
        >>> dc.updated
        True
        >>> 'UPDATE_SUBMIT' in rqst
        False
        >>>

        >>> d = {'change_test': True}
        >>> rqst1 = TestRequest(form = d)
        >>> dc1 = V(rqst1)
        >>> dc1.errors = ()
        >>> dc1.update()
        'update returned'
        >>> 'UPDATE_SUBMIT' in rqst1
        True
        >>> dc1.updated
        True
        >>> rqst1.response.getHeader('location')
        'test.html'
        >>> rqst1.response.getStatus()
        302

        >>> d = {'change_test': True}
        >>> rqst2 = TestRequest(form = d)
        >>> dc2 = V(rqst2)
        >>> dc2.errors = ('errorname', 1234)
        >>> dc2.update()
        'update returned'
        >>> 'UPDATE_SUBMIT' in rqst2
        True
        >>> rqst2.response.getHeader('location')

        >>> rqst2.response.getStatus()
        599
        """
        if 'change_test' in self.request:
            self.request.form[Update] = ''
            super(SQLScriptEdit, self).update()
            if not self.errors:
                url = 'test.html'
                self.request.response.redirect(url)
        return super(SQLScriptEdit, self).update()
