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
"""Session implementation

$Id: session.py 80054 2007-09-25 21:28:40Z rogerineichen $
"""

import zope.deferredimport

zope.deferredimport.deprecated(
    "It has moved to zope.session.session  This reference will be gone sometimes.",
    SessionData = 'zope.session.session:SessionData',
    SessionPkgData = 'zope.session.session:SessionPkgData',
    Session = 'zope.session.session:Session',
    RAMSessionDataContainer = 'zope.session.session:RAMSessionDataContainer',
    PersistentSessionDataContainer = 'zope.session.session:PersistentSessionDataContainer',
    ClientId = 'zope.session.session:ClientId',
    digestEncode = 'zope.session.session:digestEncode',
    cookieSafeTrans = 'zope.session.session:cookieSafeTrans',
    )
