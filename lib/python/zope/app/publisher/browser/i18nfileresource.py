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
"""Internationalized file resource.

$Id: i18nfileresource.py 38178 2005-08-30 21:50:19Z mj $
"""
from zope.publisher.interfaces.browser import IBrowserPublisher

from zope.app.publisher.browser.fileresource import FileResource

from zope.i18n.negotiator import negotiator
from zope.i18n.interfaces import II18nAware
from zope.interface import implements


class I18nFileResource(FileResource):

    implements(IBrowserPublisher, II18nAware)

    def __init__(self, data, request, defaultLanguage='en'):
        """Creates an internationalized file resource.  data should be
        a mapping from languages to File or Image objects.
        """
        self._data = data
        self.request = request
        self.defaultLanguage = defaultLanguage


    def chooseContext(self):
        """Choose the appropriate context according to language"""
        langs = self.getAvailableLanguages()
        language = negotiator.getLanguage(langs, self.request)
        try:
            return self._data[language]
        except KeyError:
            return self._data[self.defaultLanguage]


    # for unit tests
    def _testData(self, language):
        file = self._data[language]
        f=open(file.path,'rb')
        data=f.read()
        f.close()
        return data


    ############################################################
    # Implementation methods for interface
    # II18nAware.py

    def getDefaultLanguage(self):
        'See II18nAware'
        return self.defaultLanguage

    def setDefaultLanguage(self, language):
        'See II18nAware'
        if not self._data.has_key(language):
            raise ValueError(
                  'cannot set nonexistent language (%s) as default' % language)
        self.defaultLanguage = language

    def getAvailableLanguages(self):
        'See II18nAware'
        return self._data.keys()

    #
    ############################################################


class I18nFileResourceFactory(object):

    def __init__(self, data, defaultLanguage):
        self.__data = data
        self.__defaultLanguage = defaultLanguage

    def __call__(self, request):
        return I18nFileResource(self.__data, request, self.__defaultLanguage)
