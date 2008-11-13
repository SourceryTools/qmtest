##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Browser utilities for API documentation.

$Id: utilities.py 70020 2006-09-07 09:08:16Z flox $
"""
__docformat__ = 'restructuredtext'

from zope.i18nmessageid import ZopeMessageFactory as _
from zope.traversing.api import getName, getParent
from zope.traversing.browser import absoluteURL
from zope.app.apidoc.interfaces import IDocumentationModule


class CodeBreadCrumbs(object):
    """View that provides breadcrumbs for code objects"""

    def __call__(self):
        """Create breadcrumbs for a module or an object in a module or package.

        We cannot reuse the system's bread crumbs, since they go all the
        way up to the root, but we just want to go to the root module.
        """
        obj = self.context
        crumbs = []
        while not IDocumentationModule.providedBy(obj):
            crumbs.append(
                {'name': getName(obj),
                 'url': absoluteURL(obj, self.request)}
                )
            obj = getParent(obj)

        crumbs.append(
            {'name': _('[top]'),
             'url': absoluteURL(obj, self.request)}
            )
        crumbs.reverse()
        return crumbs
