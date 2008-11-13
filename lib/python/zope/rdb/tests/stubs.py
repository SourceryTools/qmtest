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
"""Stubs for Zope RDB unit tests.

$Id: stubs.py 37757 2005-08-06 12:34:43Z hdima $
"""

class ConnectionStub(object):

    def __init__(self):
        self._called={}

    def cursor(self):
        return CursorStub()

    def answer(self):
        return 42

    def commit(self, *ignored):
        v = self._called.setdefault('commit',0)
        v+=1
        self._called['commit']=v

    def rollback(self, *ignored):
        v = self._called.setdefault('rollback',0)
        v+=1
        self._called['rollback']=v

class CursorStub(object):

    def execute(*args, **kw):
        pass

class TypeInfoStub(object):
    paramstyle = 'pyformat'
    threadsafety = 0
    encoding = 'utf-8'

    def setEncoding(self, encoding):
        self.encoding = encoding

    def getEncoding(self):
        return self.encoding

    def getConverter(self, type):
        return lambda x: x
