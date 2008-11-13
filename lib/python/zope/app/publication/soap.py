##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""
SOAP Publication Handler. Note that there is no *standard* SOAP
implementation that is currently appropriate for the Zope3 core.

The current architecture allows external packages to register a
utility for zope.app.publication.interfaces.SOAPRequestFactory
in order to implement SOAP support. If no utility is registered
for this interface, SOAP requests are handled as if they were
browser requests.

$Id: soap.py 70826 2006-10-20 03:41:16Z baijum $
"""

from zope.app.publication.http import BaseHTTPPublication

# Don't need any special handling for SOAP
SOAPPublication = BaseHTTPPublication

class SOAPPublicationFactory(object):

    def __init__(self, db):
        self.__pub = SOAPPublication(db)

    def __call__(self):
        return self.__pub
