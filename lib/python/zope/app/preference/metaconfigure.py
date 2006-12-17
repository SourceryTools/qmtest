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
"""This module handles the 'apidoc' namespace directives.

$Id: metaconfigure.py 26889 2004-08-04 04:00:36Z pruggera $
"""
__docformat__ = 'restructuredtext'
from zope.component.zcml import utility

from zope.app.preference.interfaces import IPreferenceGroup
from zope.app.preference.preference import PreferenceGroup


def preferenceGroup(_context, id=None, schema=None,
                    title=u'', description=u'', category=False):
    if id is None:
        id = ''
    group = PreferenceGroup(id, schema, title, description, category)
    utility(_context, IPreferenceGroup, group, name=id)
