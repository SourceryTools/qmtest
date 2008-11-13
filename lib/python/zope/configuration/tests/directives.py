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
"""Test directives

$Id: directives.py 26559 2004-07-15 21:22:32Z srichter $
"""
from zope.interface import Interface, implements
from zope.schema import Text, BytesLine
from zope.configuration.config import GroupingContextDecorator
from zope.configuration.interfaces import IConfigurationContext
from zope.configuration.fields import GlobalObject


class F(object):
    def __repr__(self):
        return 'f'
    def __call__(self, *a, **k):
        pass

f = F()

class ISimple(Interface):

    a = Text()
    b = Text(required=False)
    c = BytesLine()

def simple(context, a=None, c=None, b=u"xxx"):
    return [(('simple', a, b, c), f, (a, b, c))]

def newsimple(context, a, c, b=u"xxx"):
    context.action(('newsimple', a, b, c), f, (a, b, c))


class IPackaged(Interface):

    package = GlobalObject()

class IPackagedContext(IPackaged, IConfigurationContext):
    pass

class Packaged(GroupingContextDecorator):

    implements(IPackagedContext)


class IFactory(Interface):

    factory = GlobalObject()

def factory(context, factory):
    context.action(('factory', 1,2), factory)

class Complex(object):

    def __init__(self, context, a, c, b=u"xxx"):
        self.a, self.b, self.c = a, b, c
        context.action("Complex.__init__")

    def factory(self, context, factory):
        return [(('Complex.factory', 1,2), factory, (self.a, ))]

    def factory2(self, context, factory):
        return [(('Complex.factory', 1,2), factory, (self.a, ))]

    def __call__(self):
        return [(('Complex', 1,2), f, (self.b, self.c))]


class Ik(Interface):
    for_ = BytesLine()
    class_ = BytesLine()
    x = BytesLine()
    
def k(context, for_, class_, x):
    context.action(('k', for_), f, (for_, class_, x))

def kkw(context, for_, class_, x, **kw):
    context.action(('k', for_), f, (for_, class_, x, kw))
