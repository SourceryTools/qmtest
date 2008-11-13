##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Interfaces test fixtures

$Id: classes.py 71798 2007-01-08 13:16:22Z yuppie $
"""
from zope.interface import Interface

class One(object):
    'A class'

class Two(object):
    'Another class'

class IOne(Interface):
    """This is a Zope 3 interface.
    """

class ITwo(Interface):
    """This is another Zope 3 interface.
    """
