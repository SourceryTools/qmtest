##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Zope 3 API Documentation

$Id: disabled.py 70020 2006-09-07 09:08:16Z flox $
"""
__docformat__ = 'restructuredtext'

from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.utilities import ReadContainerBase

class APIDocStub(object):
    """A stub to use as display context when APIDoc is disabled.
    """

class apidocNamespace(object):
    """Used to traverse to an API Documentation."""

    def __init__(self, ob, request=None):
        self.request = request
        self.context = ob

    def traverse(self, name, ignore):
        return APIDocStub()
