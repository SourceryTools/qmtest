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
"""Test message catalog

$Id: testmessagecatalog.py 40011 2005-11-09 21:30:39Z jim $
"""

from zope import component, interface
import zope.i18n.interfaces
from zope.i18n.translationdomain import TranslationDomain

class TestMessageCatalog:
    interface.implements(zope.i18n.interfaces.IGlobalMessageCatalog)

    language = 'test'

    def __init__(self, domain):
        self.domain = domain

    def queryMessage(self, msgid, default=None):
        default = getattr(msgid, 'default', default)
        if default != None and default != msgid:
            msg = u"%s (%s)" % (msgid, default)
        else:
            msg = msgid
            
        return u'[[%s][%s]]' % (self.domain, msg)

    getMessage = queryMessage

    def getIdentifier(self):
        return 'test'

    def reload(self):
        pass

@interface.implementer(zope.i18n.interfaces.ITranslationDomain)
def TestMessageFallbackDomain(domain_id=u''):
    domain = TranslationDomain(domain_id)
    domain.addCatalog(TestMessageCatalog(domain_id))
    return domain

interface.directlyProvides(
    TestMessageFallbackDomain,
    zope.i18n.interfaces.IFallbackTranslationDomainFactory,
    )
