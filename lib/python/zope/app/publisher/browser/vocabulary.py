##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Browser vocabularies

$Id: vocabulary.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.interface import classProvides
from zope.publisher.interfaces.browser import IBrowserSkinType
from zope.schema.interfaces import IVocabularyFactory
from zope.app.component.vocabulary import UtilityVocabulary

class BrowserSkinsVocabulary(UtilityVocabulary):
    classProvides(IVocabularyFactory)
    interface = IBrowserSkinType
