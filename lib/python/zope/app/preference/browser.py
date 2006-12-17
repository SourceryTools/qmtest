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
"""User Preferences Browser Views

$Id: menu.py 29269 2005-02-23 22:22:48Z srichter $
"""
__docformat__ = 'restructuredtext'

import re
import zope.interface
import zope.schema
from zope.security.proxy import removeSecurityProxy
from zope.i18n import translate
from zope.i18nmessageid import Message

from zope.app import zapi
from zope.app.basicskin.standardmacros import StandardMacros
from zope.app.container.interfaces import IObjectFindFilter
from zope.app.form.browser.editview import EditView
from zope.app.pagetemplate.simpleviewclass import simple
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.tree.browser.cookie import CookieTreeView
from zope.app.i18n import ZopeMessageFactory as _

from zope.app.preference import interfaces


NoneInterface = zope.interface.interface.InterfaceClass('None')

class PreferencesMacros(StandardMacros):
    """Page Template METAL macros for preferences"""
    macro_pages = ('preference_macro_definitions',)


class PreferenceGroupFilter(object):
    """A special filter for """
    zope.interface.implements(IObjectFindFilter)

    def matches(self, obj):
        """Decide whether the object is shown in the tree."""
        if interfaces.IPreferenceCategory.providedBy(obj):
            return True

        if interfaces.IPreferenceGroup.providedBy(obj):
            parent = zapi.getParent(obj)
            if interfaces.IPreferenceCategory.providedBy(parent):
                return True

        return False


class PreferencesTree(CookieTreeView):
    """Preferences Tree using the stateful cookie tree."""

    def tree(self):
        root = zapi.getRoot(self.context)
        filter = PreferenceGroupFilter()
        return self.cookieTree(root, filter)

pref_msg = _("${name} Preferences")

class EditPreferenceGroup(EditView):

    def __init__(self, context, request):
        self.__used_for__ = removeSecurityProxy(context.__schema__)
        self.schema = removeSecurityProxy(context.__schema__)

        if self.schema is None:
            self.schema = NoneInterface 
            zope.interface.alsoProvides(removeSecurityProxy(context),
                                        NoneInterface)

        name = translate(context.__title__, context=request,
                         default=context.__title__)
        self.label = Message(pref_msg, mapping={u'name': name})
        super(EditPreferenceGroup, self).__init__(context, request)
        self.setPrefix(context.__id__)

    def getIntroduction(self):
        text = self.context.__description__ or self.schema.__doc__
        text = translate(text, context=self.request, default=text)

        # Determine common whitespace ...
        cols = len(re.match('^[ ]*', text).group())
        # ... and clean it up.
        text = re.sub('\n[ ]{%i}' %cols, '\n', text).strip()

        if not text:
            return u''

        # Render the description as ReST.
        source = zapi.createObject('zope.source.rest', text)
        renderer = zapi.getMultiAdapter((source, self.request))
        return renderer.render()
