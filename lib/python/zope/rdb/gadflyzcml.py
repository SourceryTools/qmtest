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
"""'gadflyRoot' Directive Handler

$Id: metaconfigure.py 25177 2004-06-02 13:17:31Z jim $
"""
from zope.configuration.fields import Path
from zope.interface import Interface

from zope.rdb.gadflyda import setGadflyRoot 

class IGadflyRoot(Interface):
    """This directive creates a globale connection to an RDBMS."""

    path = Path(
        title=u"Path of Gadfly Root",
        description=u"Specifies the path of the gadfly root relative to the"
                    u"packge.",
        required=True)


def gadflyRootHandler(_context, path):
    _context.action(
            discriminator = ('gadflyRoot',),
            callable = setGadflyRoot,
            args = (path,) )
