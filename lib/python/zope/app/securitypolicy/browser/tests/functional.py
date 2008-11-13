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
"""Functional test case support

$Id: functional.py 29143 2005-02-14 22:43:16Z srichter $
"""

from zope import interface
from zope.app.testing import functional

class ManagerSetup:
    interface.implements(functional.IManagerSetup)

    def setUpManager(self):
        functional.HTTPCaller()(grant_request, handle_errors=False)

grant_request = (r"""
POST /@@grant.html HTTP/1.1
Authorization: Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3
Content-Length: 5796
Content-Type: application/x-www-form-urlencoded

field.principal=em9wZS5tZ3I_"""
"""&field.principal.displayed=y"""
"""&GRANT_SUBMIT=Change"""
"""&field.em9wZS5tZ3I_.role.zope.Manager=allow"""
"""&field.em9wZS5tZ3I_.role.zope.Manager-empty-marker=1""")
