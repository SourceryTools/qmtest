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
"""Interface Documentation Module

The interface documentation module retrieves its information from the
site manager. Therefore, currently there are no unregsitered interfaces
listed in the documentation. This might be good, since unregistered interfaces
are usually private and not of interest to a general developer.

$Id: __init__.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'
import os.path

from zope.interface import implements

import zope.app.apidoc.bookmodule
from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.onlinehelp.onlinehelp import OnlineHelp


class IBookModule(IDocumentationModule):
    """Interface API Documentation Module

    This is a marker interface, so that we can write adapters for objects
    implementing this interface.
    """

class BookModule(OnlineHelp):
    """Represent a book compiled from various `README.txt` and other `*.txt`
    documentation files.
    """

    implements(IBookModule)

    # See zope.app.apidoc.interfaces.IDocumentationModule
    title = _('Book')

    # See zope.app.apidoc.interfaces.IDocumentationModule
    description = _("""
    This is a developer's book compiled from all existing documentation
    files. It is not meant to be a complete or cohesive work, but each chapter
    in itself is a little story. Think about it like a collection of fairy
    tales.
    """)


# Global Book Instance
path = os.path.join(os.path.dirname(zope.app.apidoc.bookmodule.__file__),
                    'intro.txt')
book = BookModule(_('Book'), path)

def _clear():
    global book
    book.__init__(book.title, book.path)

from zope.testing import cleanup
cleanup.addCleanUp(_clear)
