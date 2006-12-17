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
"""Translation Domain Views

$Id: __init__.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'

from zope.i18n.interfaces import ITranslationDomain

class BaseView(object):

    __used_for__ = ITranslationDomain

    def getAllLanguages(self):
        """Get all available languages from the Translation Domain."""
        return self.context.getAllLanguages()
