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
"""Bootstrap code for principal annotation utility.

$Id: bootstrap.py 28023 2004-10-12 18:11:29Z anguenot $
"""

import transaction

from zope.app.appsetup.bootstrap import ensureUtility, getInformationFromEvent

from zope.app.principalannotation import PrincipalAnnotationUtility
from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility

def bootStrapSubscriber(event):
    """Subscriber to the IDataBaseOpenedEvent

    Create utility at that time if not yet present
    """

    db, connection, root, root_folder = getInformationFromEvent(event)

    ensureUtility(root_folder, IPrincipalAnnotationUtility,
                  'PrincipalAnnotation', PrincipalAnnotationUtility,
                  asObject=True)

    transaction.commit()
    connection.close()
