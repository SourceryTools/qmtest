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
"""Test objects and interfaces.

$Id: views.py 26559 2004-07-15 21:22:32Z srichter $
"""

from zope.interface import Interface, implements
from zope.publisher.browser import BrowserView

class IC(Interface): pass

class V1(BrowserView): pass

class VZMI(V1): pass

class R1(object):
    def __init__(self, request): self.request = request

class RZMI(R1):
    pass
