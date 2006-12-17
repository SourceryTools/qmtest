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
"""ZCML configuration directives for configuring the default zope:
namespace in TALES.

$Id: metaconfigure.py 26955 2004-08-09 04:06:35Z pruggera $
"""
__docformat__ = 'restructuredtext'

from zope.app.pagetemplate.engine import Engine, _Engine
from zope.app.pagetemplate.engine import TrustedEngine, _TrustedEngine
from zope.testing.cleanup import addCleanUp
from zope.interface import Interface
from zope.configuration.fields import GlobalObject
from zope.schema import TextLine

class IExpressionTypeDirective(Interface):
    """Register a new TALES expression type"""

    name = TextLine(
        title=u"Name",
        description=u"""Name of the expression. This will also be used
        as the prefix in actual TALES expressions.""",
        required=True
        )

    handler = GlobalObject(
        title=u"Handler",
        description=u"""Handler is class that implements
        zope.tales.interfaces.ITALESExpression.""",
        required=True
        )

def expressiontype(_context, name, handler):
    _context.action(
        discriminator = ("tales:expressiontype", name),
        callable = registerType,
        args = (name, handler)
        )

def registerType(name, handler):
    Engine.registerType(name, handler)
    TrustedEngine.registerType(name, handler)


def clear():
    Engine.__init__()
    _Engine(Engine)
    TrustedEngine.__init__()
    _TrustedEngine(TrustedEngine)

addCleanUp(clear)
