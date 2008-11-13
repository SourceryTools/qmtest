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
"""Generic two-dimensional array type (in context of security)

$Id: securitymap.py 80458 2007-10-02 03:27:54Z srichter $
"""

import zope.deferredimport

zope.deferredimport.deprecated(
    "It has moved to zope.securitypolicy.securitymap. This reference will be "
    "removed at some point after 2008-09-26.",
    SecurityMap = \
        'zope.securitypolicy.securitymap:SecurityMap',
    PersistentSecurityMap = \
        'zope.securitypolicy.securitymap:PersistentSecurityMap',
    AnnotationSecurityMap = \
        'zope.securitypolicy.securitymap:AnnotationSecurityMap',
    )
