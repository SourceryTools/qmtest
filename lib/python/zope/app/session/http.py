##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Session implementation using cookies

$Id: http.py 80054 2007-09-25 21:28:40Z rogerineichen $
"""

import zope.deferredimport

zope.deferredimport.deprecated(
    "It has moved to zope.session.http  This reference will be gone sometimes.",
    ICookieClientIdManager = 'zope.session.http:ICookieClientIdManager',
    MissingClientIdException = 'zope.session.http:MissingClientIdException',
    notifyVirtualHostChanged = 'zope.session.http:notifyVirtualHostChanged',
    CookieClientIdManager = 'zope.session.http:CookieClientIdManager',
    digestEncode = 'zope.session.http:digestEncode',
    cookieSafeTrans = 'zope.session.http:cookieSafeTrans',
    )
