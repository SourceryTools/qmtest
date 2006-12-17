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
"""Terms view for Principal Source

$Id: principalterms.py 38178 2005-08-30 21:50:19Z mj $
"""
__docformat__ = "reStructuredText"

from zope.interface import implements
from zope.publisher.interfaces.browser import IBrowserRequest

from zope.app import zapi
from zope.app.form.browser.interfaces import ITerms
from zope.app.security.interfaces import IPrincipalSource

class Term(object):

    def __init__(self, token, title):
        self.token = token
        self.title = title


class PrincipalTerms(object):
    implements(ITerms)
    __used_for__ = IPrincipalSource, IBrowserRequest

    def __init__(self, context, request):
        self.context = context

    def getTerm(self, principal_id):
        if principal_id not in self.context:
            raise LookupError(principal_id)

        auth = zapi.principals()
        principal = auth.getPrincipal(principal_id)

        if principal is None:
            raise LookupError(principal_id)

        return Term(principal_id.encode('base64').strip().replace('=', '_'),
                    principal.title)

    def getValue(self, token):
        return token.replace('_', '=').decode('base64')
