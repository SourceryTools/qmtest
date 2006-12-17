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
"""Meta-Configuration Handlers for "help" namespace.

These handlers process the `registerTopic()` directive of
the "help" ZCML namespace.

$Id: metaconfigure.py 26955 2004-08-09 04:06:35Z pruggera $
"""
__docformat__ = 'restructuredtext'
import os.path
import zope.app.apidoc.bookmodule
from zope.app.onlinehelp.onlinehelptopic import RESTOnlineHelpTopic
from book import book

EMPTYPATH = os.path.join(
    os.path.dirname(zope.app.apidoc.bookmodule.__file__),
    'empty.txt')

def bookchapter(_context, id, title, doc_path=EMPTYPATH,
                parent="", resources=None):
    """Register an book chapter"""

    _context.action(
        discriminator = ('apidoc:bookchapter', parent, id),
        callable = book.registerHelpTopic,
        args = (parent, id, title, doc_path),
        kw = {'resources': resources, 'class_': RESTOnlineHelpTopic},
        order=999999)
