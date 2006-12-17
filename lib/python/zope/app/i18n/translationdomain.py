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
"""This is the standard, placeful Translation Domain for TTW development.

$Id: translationdomain.py 68769 2006-06-20 10:19:22Z hdima $
"""
__docformat__ = 'restructuredtext'

import re
from BTrees.OOBTree import OOBTree

import zope.component
from zope.interface import implements
from zope.i18n import interpolate
from zope.i18n.negotiator import negotiator
from zope.i18n.interfaces import INegotiator, ITranslationDomain
from zope.i18n.simpletranslationdomain import SimpleTranslationDomain

from zope.app.container.btree import BTreeContainer
from zope.app.i18n.interfaces import ILocalTranslationDomain
from zope.app.container.contained import Contained
from zope.app.component import queryNextUtility


class TranslationDomain(BTreeContainer, SimpleTranslationDomain, Contained):
    implements(ILocalTranslationDomain)

    def __init__(self):
        super(TranslationDomain, self).__init__()
        self._catalogs = OOBTree()
        self.domain = '<domain not activated>'

    def _registerMessageCatalog(self, language, catalog_name):
        if language not in self._catalogs.keys():
            self._catalogs[language] = []

        mc = self._catalogs[language]
        mc.append(catalog_name)

    def _unregisterMessageCatalog(self, language, catalog_name):
        self._catalogs[language].remove(catalog_name)

    def __setitem__(self, name, object):
        'See IWriteContainer'
        super(TranslationDomain, self).__setitem__(name, object)
        self._registerMessageCatalog(object.language, name)

    def __delitem__(self, name):
        'See IWriteContainer'
        object = self[name]
        super(TranslationDomain, self).__delitem__(name)
        self._unregisterMessageCatalog(object.language, name)

    def translate(self, msgid, mapping=None, context=None,
                  target_language=None, default=None):
        """See interface `ITranslationDomain`"""
        if target_language is None and context is not None:
            avail_langs = self.getAvailableLanguages()
            # Let's negotiate the language to translate to. :)
            negotiator = zope.component.getUtility(INegotiator, context=self)
            target_language = negotiator.getLanguage(avail_langs, context)

        # Get the translation. Default is the source text itself.
        catalog_names = self._catalogs.get(target_language, [])

        for name in catalog_names:
            catalog = super(TranslationDomain, self).__getitem__(name)
            text = catalog.queryMessage(msgid)
            if text is not None:
                break
        else:
            # If nothing found, delegate to a translation server higher up the
            # tree.
            domain = queryNextUtility(ITranslationDomain, self.domain)
            if domain is not None:
                return domain.translate(msgid, mapping, context,
                                        target_language, default=default)
            if default is None:
                default = unicode(msgid)
            text = default

        # Now we need to do the interpolation
        return interpolate(text, mapping)


    def getMessageIds(self, filter='%'):
        'See `IWriteTranslationDomain`'
        filter = filter.replace('%', '.*')
        filter_re = re.compile(filter)

        msgids = {}
        for language in self.getAvailableLanguages():
            for name in self._catalogs[language]:
                for msgid in self[name].getMessageIds():
                    if filter_re.match(msgid) >= 0:
                        msgids[msgid] = None
        return msgids.keys()

    def getMessages(self):
        'See `IWriteTranslationDomain`'
        messages = []
        languages = self.getAvailableLanguages()
        for language in languages:
            for name in self._catalogs[language]:
                messages += self[name].getMessages()
        return messages


    def getMessage(self, msgid, language):
        'See `IWriteTranslationDomain`'
        for name in self._catalogs.get(language, []):
            try:
                return self[name].getFullMessage(msgid)
            except:
                pass
        return None

    def getAllLanguages(self):
        'See `IWriteTranslationDomain`'
        languages = {}
        for key in self._catalogs.keys():
            languages[key] = None
        return languages.keys()


    def getAvailableLanguages(self):
        'See `IWriteTranslationDomain`'
        return list(self._catalogs.keys())


    def addMessage(self, msgid, msg, language, mod_time=None):
        'See `IWriteTranslationDomain`'
        if not self._catalogs.has_key(language):
            if language not in self.getAllLanguages():
                self.addLanguage(language)

        catalog_name = self._catalogs[language][0]
        catalog = self[catalog_name]
        catalog.setMessage(msgid, msg, mod_time)


    def updateMessage(self, msgid, msg, language, mod_time=None):
        'See `IWriteTranslationDomain`'
        catalog_name = self._catalogs[language][0]
        catalog = self[catalog_name]
        catalog.setMessage(msgid, msg, mod_time)


    def deleteMessage(self, msgid, language):
        'See `IWriteTranslationDomain`'
        catalog_name = self._catalogs[language][0]
        catalog = self[catalog_name]
        catalog.deleteMessage(msgid)


    def addLanguage(self, language):
        'See `IWriteTranslationDomain`'
        catalog = zope.component.createObject(u'zope.app.MessageCatalog',
                                              language)
        self[language] = catalog


    def deleteLanguage(self, language):
        'See `IWriteTranslationDomain`'
        # Delete all catalogs from the data storage
        for name in self._catalogs[language]:
            if self.has_key(name):
                del self[name]
        # Now delete the specifc catalog registry for this language
        del self._catalogs[language]


    def getMessagesMapping(self, languages, foreign_messages):
        'See `ISyncTranslationDomain`'
        mapping = {}
        # Get all relevant local messages
        local_messages = []
        for language in languages:
            for name in self._catalogs.get(language, []):
                local_messages += self[name].getMessages()


        for fmsg in foreign_messages:
            ident = (fmsg['msgid'], fmsg['language'])
            mapping[ident] = (fmsg, self.getMessage(*ident))

        for lmsg in local_messages:
            ident = (lmsg['msgid'], lmsg['language'])
            if ident not in mapping.keys():
                mapping[ident] = (None, lmsg)

        return mapping


    def synchronize(self, messages_mapping):
        'See `ISyncTranslationDomain`'

        for value in messages_mapping.values():
            fmsg = value[0]
            lmsg = value[1]
            if fmsg is None:
                self.deleteMessage(lmsg['msgid'], lmsg['language'])
            elif lmsg is None:
                self.addMessage(fmsg['msgid'],
                                fmsg['msgstr'], fmsg['language'],
                                fmsg['mod_time'])
            elif fmsg['mod_time'] > lmsg['mod_time']:
                self.updateMessage(fmsg['msgid'],
                                   fmsg['msgstr'], fmsg['language'],
                                   fmsg['mod_time'])


def setDomainOnActivation(domain, event):
    """Set the permission id upon registration activation.

    Let's see how this notifier can be used. First we need to create an event
    using the permission instance and a registration stub:

    >>> class Registration:
    ...     def __init__(self, obj, name):
    ...         self.component = obj
    ...         self.name = name

    >>> domain1 = TranslationDomain()
    >>> domain1.domain
    '<domain not activated>'

    >>> import zope.component.interfaces
    >>> event = zope.component.interfaces.Registered(
    ...     Registration(domain1, 'domain1'))

    Now we pass the event into this function, and the id of the domain should
    be set to 'domain1'.

    >>> setDomainOnActivation(domain1, event)
    >>> domain1.domain
    'domain1'
    """
    domain.domain = event.object.name


def unsetDomainOnDeactivation(domain, event):
    """Unset the permission id up registration deactivation.

    Let's see how this notifier can be used. First we need to create an event
    using the permission instance and a registration stub:

    >>> class Registration:
    ...     def __init__(self, obj, name):
    ...         self.component = obj
    ...         self.name = name

    >>> domain1 = TranslationDomain()
    >>> domain1.domain = 'domain1'

    >>> import zope.component.interfaces
    >>> event = zope.component.interfaces.Unregistered(
    ...     Registration(domain1, 'domain1'))

    Now we pass the event into this function, and the id of the role should be
    set to '<domain not activated>'.

    >>> unsetDomainOnDeactivation(domain1, event)
    >>> domain1.domain
    '<domain not activated>'
    """
    domain.domain = '<domain not activated>'
