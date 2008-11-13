##############################################################################
#
# Copyright (c) 2002, 2004 Zope Corporation and Contributors.
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
"""Bootstrap code.

This module contains code to bootstrap a Zope3 instance.  For example
it makes sure a root folder exists and creates and configures some
essential utilities.

$Id: bootstrap.py 80044 2007-09-25 20:17:42Z rogerineichen $
"""

import transaction

from zope.app.appsetup.bootstrap import ensureUtility, getInformationFromEvent

from zope.session.interfaces import IClientIdManager, ISessionDataContainer
from zope.session.http import CookieClientIdManager
from zope.session.session import PersistentSessionDataContainer

def bootStrapSubscriber(event):
    """Subscriber to the IDataBaseOpenedEvent

    Create utility at that time if not yet present
    """

    db, connection, root, root_folder = getInformationFromEvent(event)

    ensureUtility(
        root_folder,
        IClientIdManager, 'CookieClientIdManager',
        CookieClientIdManager,
        asObject=True,
        )
    ensureUtility(
        root_folder,
        ISessionDataContainer, 'PersistentSessionDataContainer',
        PersistentSessionDataContainer,
        asObject=True,
        )

    transaction.commit()
    connection.close()
