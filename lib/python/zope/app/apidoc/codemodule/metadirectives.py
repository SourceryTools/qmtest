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
"""``apidoc`` ZCML namespace directive interfaces

$Id: metadirectives.py 26613 2004-07-18 21:50:40Z srichter $
"""
__docformat__ = 'restructuredtext'
import zope.interface
import zope.schema

class IRootModule(zope.interface.Interface):
    """Declares a new root module to be available for the class documentation
    module."""

    module = zope.schema.TextLine(
        title=u"Root Module Name",
        description=u"This is the Python path of the new root module.",
        required=True
        )

class IModuleImport(zope.interface.Interface):
    """Set a flag whether new modules can be imported to the class registry or
       not."""

    allow = zope.schema.Bool(
        title=u"Allow Importing Modules",
        description=u"When set to true, new modules will be imported by path.",
        required=True,
        default=False
        )
