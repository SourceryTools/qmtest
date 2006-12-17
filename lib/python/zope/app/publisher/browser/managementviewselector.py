##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Selecting first available and allowed management view

$Id: managementviewselector.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.interface import implements
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.browser import BrowserView
from zope.app.publisher.browser.menu import getFirstMenuItem

class ManagementViewSelector(BrowserView):
    """View that selects the first available management view.

    Support 'zmi_views' actions like: 'javascript:alert("hello")', 
    '../view_on_parent.html' or '++rollover++'.
    """
    implements(IBrowserPublisher)

    def browserDefault(self, request):
        return self, ()

    def __call__(self):
        item = getFirstMenuItem('zmi_views', self.context, self.request)

        if item:
            redirect_url = item['action']
            if not (redirect_url.startswith('../') or \
                    redirect_url.lower().startswith('javascript:') or \
                    redirect_url.lower().startswith('++')):
                self.request.response.redirect(redirect_url)
                return u''

        self.request.response.redirect('.') # Redirect to content/
        return u''
