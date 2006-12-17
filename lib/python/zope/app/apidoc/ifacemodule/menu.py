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
"""Interface Module Browser Menu (Tree)

$Id: menu.py 39722 2005-10-29 23:25:40Z srichter $
"""
__docformat__ = 'restructuredtext'
from zope.security.proxy import removeSecurityProxy
import re

whitepattern = re.compile('\s{2,}')
def getAllTextOfInterface(iface):
    """Get all searchable text from an interface"""
    iface = removeSecurityProxy(iface)
    text = iface.__doc__ or ''
    for name in iface:
        attr = iface[name]
        text += attr.getName()
        text += attr.getDoc() or ''
    return text


class Menu(object):
    """Menu for the Interface Documentation Module."""

    def findInterfaces(self):
        """Find the interface that match any text in the documentation strings
        or a partial path."""
        name_only = ('name_only' in self.request) and True or False
        search_str = self.request.get('search_str', None)
        results = []

        if search_str is None:
            return results
        for name, iface in self.context.items():
            if (search_str in name or
                (not name_only and search_str in getAllTextOfInterface(iface))):
                results.append(
                    {'name': name,
                     'url': './%s/index.html' %name
                     })
        results.sort(lambda x, y: cmp(x['name'], y['name']))
        return results

    def findAllInterfaces(self):
        """Find all interfaces."""

        results = []

        counter = 0
        for name, iface in self.context.items():
            rtext = getAllTextOfInterface(iface)
            results.append(
                {'name': name,
                 'url': './%s/index.html' %name,
                 'counter': counter,
                 'doc': whitepattern.sub(' ',getAllTextOfInterface(iface))
                 })
            counter += 1

        results.sort(lambda x, y: cmp(x['name'], y['name']))
        return results
