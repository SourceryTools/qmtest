##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Object that takes care of annotating the dublin core creator field.

$Id: creatorannotator.py 66902 2006-04-12 20:16:30Z philikon $
"""
__docformat__ = 'restructuredtext'

from zope.dublincore.interfaces import IZopeDublinCore
from zope.security.management import queryInteraction
from zope.security.proxy import removeSecurityProxy

def CreatorAnnotator(event):
    """Update Dublin-Core creator property"""
    dc = IZopeDublinCore(event.object, None)
    # Principals that can create object do not necessarily have
    # 'zope.app.dublincore.change' permission. See issue 373.
    dc = removeSecurityProxy(dc)
    if dc is None:
        return

    # Try to find a principal for that one. If there
    # is no principal then we don't touch the list
    # of creators.
    interaction = queryInteraction()
    if interaction is not None:
        for participation in interaction.participations:
            principalid = participation.principal.id
            if not principalid in dc.creators:
                dc.creators = dc.creators + (unicode(principalid), )

