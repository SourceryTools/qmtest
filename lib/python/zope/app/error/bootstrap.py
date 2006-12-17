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
"""Bootstrap code for error reporting utility.

$Id: bootstrap.py 66293 2006-04-02 10:47:12Z srichter $
"""

import transaction

from zope.app.appsetup.bootstrap import ensureUtility, getInformationFromEvent

from zope.app.error.error import RootErrorReportingUtility
from zope.app.error.interfaces import IErrorReportingUtility

def bootStrapSubscriber(event):
    """Subscriber to the IDataBaseOpenedEvent

    Create utility at that time if not yet present
    """

    db, connection, root, root_folder = getInformationFromEvent(event)

    ensureUtility(root_folder, IErrorReportingUtility, '',
                  RootErrorReportingUtility, copy_to_zlog=False, asObject=True)

    transaction.commit()
    connection.close()
