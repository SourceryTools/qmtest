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
"""This module tests the regular persistent Translation Domain.

$Id: test_translationdomain.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest

from zope.component.interfaces import IFactory
from zope.component.factory import Factory
from zope.i18n.interfaces import ITranslationDomain
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.tests.test_itranslationdomain import TestITranslationDomain
from zope.i18n.translationdomain \
     import TranslationDomain as GlobalTranslationDomain
from zope.interface import implements, classImplements
from zope.interface.verify import verifyObject
from zope.testing.doctestunit import DocTestSuite
from zope.annotation.interfaces import IAttributeAnnotatable

from zope.app import zapi
from zope.app.i18n.interfaces import ISyncTranslationDomain
from zope.app.i18n.messagecatalog import MessageCatalog
from zope.app.i18n.translationdomain import TranslationDomain
from zope.app.component.testing import PlacefulSetup
from zope.app.testing import setup, ztapi


class Environment(object):

    implements(IUserPreferredLanguages)

    def __init__(self, langs=()):
        self.langs = langs

    def getPreferredLanguages(self):
        return self.langs


class TestILocalTranslationDomain(object):

    def _getTranslationDomain(self):
        """This should be overwritten by every clas that inherits this test.

           We expect the TranslationDomain to contain exactly 2 languages:
           de and en
        """

    def setUp(self):
        self._domain = self._getTranslationDomain()

    def testInterface(self):
        verifyObject(ITranslationDomain, self._domain)

    def _getLanguages(self, domain):
        languages = domain.getAllLanguages()
        languages.sort()
        return languages

    def testGetAddDeleteLanguage(self):
        domain = self._domain
        langs = self._getLanguages(domain)
        domain.addLanguage('es')
        self.assertEqual(self._getLanguages(domain), langs+['es'])
        domain.addLanguage('fr')
        self.assertEqual(self._getLanguages(domain), langs+['es', 'fr'])
        self.assertEqual(domain.getAvailableLanguages(),
                         langs+['es', 'fr'])
        domain.deleteLanguage('es')
        self.assertEqual(self._getLanguages(domain), langs+['fr'])
        domain.deleteLanguage('fr')
        self.assertEqual(self._getLanguages(domain), langs)

    def testAddUpdateDeleteMessage(self):
        domain = self._domain
        self.assertEqual(domain.translate('greeting2', target_language='de'),
                         'greeting2')
        self.assertEqual(domain.translate(
            'greeting2', target_language='de', default=42), 42)
        domain.addMessage('greeting2', 'Hallo!', 'de')
        self.assertEqual(domain.translate('greeting2', target_language='de'),
                         'Hallo!')
        domain.updateMessage('greeting2', 'Hallo Ihr da!', 'de')
        self.assertEqual(domain.translate('greeting2', target_language='de'),
                         'Hallo Ihr da!')
        domain.deleteMessage('greeting2', 'de')
        self.assertEqual(domain.translate('greeting2', target_language='de'),
                         'greeting2')


# A test mixing -- don't add this to the suite
class TestISyncTranslationDomain(object):

    foreign_messages = [
        # Message that is not locally available
        {'domain': 'default', 'language': 'en', 'msgid': 'test',
         'msgstr': 'Test', 'mod_time': 0},
        # This message is newer than the local one.
        {'domain': 'default', 'language': 'de', 'msgid': 'short_greeting',
         'msgstr': 'Hallo.', 'mod_time': 20},
        # This message is older than the local one.
        {'domain': 'default', 'language': 'en', 'msgid': 'short_greeting',
         'msgstr': 'Hello', 'mod_time': 0},
        # This message is up-to-date.
        {'domain': 'default', 'language': 'en', 'msgid': 'greeting',
         'msgstr': 'Hello $name, how are you?', 'mod_time': 0}]


    local_messages = [
        # This message is older than the foreign one.
        {'domain': 'default', 'language': 'de', 'msgid': 'short_greeting',
         'msgstr': 'Hallo!', 'mod_time': 10},
        # This message is newer than the foreign one.
        {'domain': 'default', 'language': 'en', 'msgid': 'short_greeting',
         'msgstr': 'Hello!', 'mod_time': 10},
        # This message is up-to-date.
        {'domain': 'default', 'language': 'en', 'msgid': 'greeting',
         'msgstr': 'Hello $name, how are you?', 'mod_time': 0},
        # This message is only available locally.
        {'domain': 'default', 'language': 'de', 'msgid': 'greeting',
         'msgstr': 'Hallo $name, wie geht es Dir?', 'mod_time': 0},
        ]


    # This should be overwritten by every clas that inherits this test
    def _getTranslationDomain(self):
        pass


    def setUp(self):
        self._domain = self._getTranslationDomain()

    def testInterface(self):
        verifyObject(ISyncTranslationDomain, self._domain)

    def testGetMessagesMapping(self):
        mapping = self._domain.getMessagesMapping(['de', 'en'],
                                                  self.foreign_messages)
        self.assertEqual(mapping[('test', 'en')],
                         (self.foreign_messages[0], None))
        self.assertEqual(mapping[('short_greeting', 'de')],
                         (self.foreign_messages[1], self.local_messages[0]))
        self.assertEqual(mapping[('short_greeting', 'en')],
                         (self.foreign_messages[2], self.local_messages[1]))
        self.assertEqual(mapping[('greeting', 'en')],
                         (self.foreign_messages[3], self.local_messages[2]))
        self.assertEqual(mapping[('greeting', 'de')],
                         (None, self.local_messages[3]))


    def testSynchronize(self):
        domain = self._domain
        mapping = domain.getMessagesMapping(['de', 'en'], self.foreign_messages)
        domain.synchronize(mapping)

        self.assertEqual(domain.getMessage('test', 'en'),
                         self.foreign_messages[0])
        self.assertEqual(domain.getMessage('short_greeting', 'de'),
                         self.foreign_messages[1])
        self.assertEqual(domain.getMessage('short_greeting', 'en'),
                         self.local_messages[1])
        self.assertEqual(domain.getMessage('greeting', 'en'),
                         self.local_messages[2])
        self.assertEqual(domain.getMessage('greeting', 'en'),
                         self.foreign_messages[3])
        self.assertEqual(domain.getMessage('greeting', 'de'),
                         None)

                            
class TestTranslationDomain(TestITranslationDomain,
                            TestISyncTranslationDomain,
                            TestILocalTranslationDomain,
                            PlacefulSetup,
                            unittest.TestCase):


    def setUp(self):
        classImplements(TranslationDomain, IAttributeAnnotatable)
        self.sm = PlacefulSetup.setUp(self, site=True)
        TestITranslationDomain.setUp(self)

        setup.addUtility(self.sm, 'default', ITranslationDomain, self._domain)
        
        ztapi.provideUtility(IFactory, Factory(MessageCatalog),
                             'zope.app.MessageCatalog')


    def _getTranslationDomain(self):
        domain = TranslationDomain()
        domain.domain = 'default'

        en_catalog = MessageCatalog('en', 'default')
        de_catalog = MessageCatalog('de', 'default')
        # Populate the catalogs with translations of a message id
        en_catalog.setMessage('short_greeting', 'Hello!', 10)
        de_catalog.setMessage('short_greeting', 'Hallo!', 10)
        # And another message id with interpolation placeholders
        en_catalog.setMessage('greeting', 'Hello $name, how are you?', 0)
        de_catalog.setMessage('greeting', 'Hallo $name, wie geht es Dir?', 0)

        domain['en-1'] = en_catalog
        domain['de-1'] = de_catalog

        return domain

    def testParameterNames(self):
        # Test that the second argument is called `msgid'
        self.assertEqual(
            self._domain.translate('short_greeting', target_language='en'),
            'Hello!')


class TestTranslationDomainInAction(unittest.TestCase):

    def setUp(self):
        setup.placefulSetUp()
        self.rootFolder = setup.buildSampleFolderTree()
        sm = zapi.getGlobalSiteManager()
        de_catalog = MessageCatalog('de', 'default')
        de_catalog.setMessage('short_greeting', 'Hallo!', 10)

        # Create global translation domain and add the catalog.
        domain = GlobalTranslationDomain('default')
        domain.addCatalog(de_catalog)
        sm.provideUtility(ITranslationDomain, domain, 'default')

        # Create Domain in root folder
        mgr = setup.createSiteManager(self.rootFolder)
        self.trans = setup.addDomain(mgr, Translation, TranslationDomain())

        # Create Domain in folder1
        mgr = setup.createSiteManager(zapi.traverse(self.rootFolder, 'folder1'))
        td = TranslationDomain()
        td.domain = 'default'
        de_catalog = MessageCatalog('de', 'default')
        de_catalog.setMessage('short_greeting', 'Hallo Welt!', 10)
        td['de-default-1'] = de_catalog
        self.trans1 = setup.addDomain(mgr, Translation, ts)

    def tearDown(self):
        setup.placefulTearDown()
        

    def test_translate(self):
        self.assertEqual(
            self.trans.translate('short_greeting', 'default',
                                 target_language='de'),
            'Hallo!')
        self.assertEqual(
            self.trans1.translate('short_greeting', 'default',
                                  target_language='de'),
            'Hallo Welt!')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestTranslationDomain),
        DocTestSuite('zope.app.i18n.translationdomain'),
        #unittest.makeSuite(TestTranslationDomainInAction),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
