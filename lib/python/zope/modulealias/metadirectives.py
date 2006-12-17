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
"""'zope:modulealias' directive interface

$Id$
"""
from zope.configuration.fields import PythonIdentifier
from zope.interface import Interface

class IModuleAliasDirective(Interface):
    """ *BBB: DEPRECATED*

    The 'modulealias' directive has been deprecated and will be
    removed in Zope 3.5. Manipulate 'sys.modules' manually instead.

    Define a new module alias
    """
    module = PythonIdentifier()
    alias = PythonIdentifier()
