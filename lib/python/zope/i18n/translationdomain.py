##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Global Translation Service for providing I18n to file-based code.

$Id: translationdomain.py 68769 2006-06-20 10:19:22Z hdima $
"""
from zope.component import getUtility
from zope.i18nmessageid import Message
from zope.i18n import interpolate
from zope.i18n.simpletranslationdomain import SimpleTranslationDomain
from zope.i18n.interfaces import ITranslationDomain, INegotiator

# The configuration should specify a list of fallback languages for the
# site.  If a particular catalog for a negotiated language is not available,
# then the zcml specified order should be tried.  If that fails, then as a
# last resort the languages in the following list are tried.  If these fail
# too, then the msgid is returned.
#
# Note that these fallbacks are used only to find a catalog.  If a particular
# message in a catalog is not translated, tough luck, you get the msgid.
LANGUAGE_FALLBACKS = ['en']


class TranslationDomain(SimpleTranslationDomain):

    def __init__(self, domain, fallbacks=None):
        self.domain = domain
        # _catalogs maps (language, domain) to IMessageCatalog instances
        self._catalogs = {}
        # _data maps IMessageCatalog.getIdentifier() to IMessageCatalog
        self._data = {}
        # What languages to fallback to, if there is no catalog for the
        # requested language (no fallback on individual messages)
        if fallbacks is None:
            fallbacks = LANGUAGE_FALLBACKS
        self._fallbacks = fallbacks

    def _registerMessageCatalog(self, language, catalog_name):
        key = language
        mc = self._catalogs.setdefault(key, [])
        mc.append(catalog_name)

    def addCatalog(self, catalog):
        self._data[catalog.getIdentifier()] = catalog
        self._registerMessageCatalog(catalog.language,
                                     catalog.getIdentifier())

    def setLanguageFallbacks(self, fallbacks=None):
        if fallbacks is None:
            fallbacks = LANGUAGE_FALLBACKS
        self._fallbacks = fallbacks

    def translate(self, msgid, mapping=None, context=None,
                  target_language=None, default=None):
        """See zope.i18n.interfaces.ITranslationDomain"""

        # if the msgid is empty, let's save a lot of calculations and return
        # an empty string.
        if msgid == u'':
            return u''

        if target_language is None and context is not None:
            langs = self._catalogs.keys()
            # invoke local or global unnamed 'INegotiator' utilities
            negotiator = getUtility(INegotiator)
            # try to determine target language from negotiator utility
            target_language = negotiator.getLanguage(langs, context)

        # MessageID attributes override arguments
        if isinstance(msgid, Message):
            if msgid.domain != self.domain:
                util = getUtility(ITranslationDomain, msgid.domain)
            mapping = msgid.mapping
            default = msgid.default

        if default is None:
            default = unicode(msgid)

        # Get the translation. Use the specified fallbacks if this fails
        catalog_names = self._catalogs.get(target_language)
        if catalog_names is None:
            for language in self._fallbacks:
                catalog_names = self._catalogs.get(language)
                if catalog_names is not None:
                    break

        text = default
        if catalog_names:
            if len(catalog_names) == 1:
                # this is a slight optimization for the case when there is a
                # single catalog. More importantly, it is extremely helpful
                # when testing and the test language is used, because it
                # allows the test language to get the default. 
                text = self._data[catalog_names[0]].queryMessage(
                    msgid, default)
            else:
                for name in catalog_names:
                    catalog = self._data[name]
                    s = catalog.queryMessage(msgid)
                    if s is not None:
                        text = s
                        break

        # Now we need to do the interpolation
        if text and mapping:
            text = interpolate(text, mapping)
        return text

    def getCatalogsInfo(self):
        return self._catalogs

    def reloadCatalogs(self, catalogNames):
        for catalogName in catalogNames:
            self._data[catalogName].reload()
