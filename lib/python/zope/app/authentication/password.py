##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Password managers

$Id: password.py 74706 2007-04-24 16:15:34Z hdima $
"""
__docformat__ = 'restructuredtext'

import md5
import sha
from random import randint
from codecs import getencoder

from zope.interface import implements, classProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.app.component.vocabulary import UtilityVocabulary

from zope.app.authentication.interfaces import IPasswordManager


_encoder = getencoder("utf-8")


class PlainTextPasswordManager(object):
    """Plain text password manager.

    >>> from zope.interface.verify import verifyObject

    >>> manager = PlainTextPasswordManager()
    >>> verifyObject(IPasswordManager, manager)
    True

    >>> password = u"right \N{CYRILLIC CAPITAL LETTER A}"
    >>> encoded = manager.encodePassword(password)
    >>> encoded
    u'right \u0410'
    >>> manager.checkPassword(encoded, password)
    True
    >>> manager.checkPassword(encoded, password + u"wrong")
    False
    """

    implements(IPasswordManager)

    def encodePassword(self, password):
        return password

    def checkPassword(self, storedPassword, password):
        return storedPassword == self.encodePassword(password)


class MD5PasswordManager(PlainTextPasswordManager):
    """MD5 password manager.

    >>> from zope.interface.verify import verifyObject

    >>> manager = MD5PasswordManager()
    >>> verifyObject(IPasswordManager, manager)
    True

    >>> password = u"right \N{CYRILLIC CAPITAL LETTER A}"
    >>> encoded = manager.encodePassword(password, salt="")
    >>> encoded
    '86dddccec45db4599f1ac00018e54139'
    >>> manager.checkPassword(encoded, password)
    True
    >>> manager.checkPassword(encoded, password + u"wrong")
    False

    >>> encoded = manager.encodePassword(password)
    >>> encoded[-32:]
    '86dddccec45db4599f1ac00018e54139'
    >>> manager.checkPassword(encoded, password)
    True
    >>> manager.checkPassword(encoded, password + u"wrong")
    False

    >>> manager.encodePassword(password) != manager.encodePassword(password)
    True
    """

    implements(IPasswordManager)

    def encodePassword(self, password, salt=None):
        if salt is None:
            salt = "%08x" % randint(0, 0xffffffff)
        return salt + md5.new(_encoder(password)[0]).hexdigest()

    def checkPassword(self, storedPassword, password):
        salt = storedPassword[:-32]
        return storedPassword == self.encodePassword(password, salt)


class SHA1PasswordManager(PlainTextPasswordManager):
    """SHA1 password manager.

    >>> from zope.interface.verify import verifyObject

    >>> manager = SHA1PasswordManager()
    >>> verifyObject(IPasswordManager, manager)
    True

    >>> password = u"right \N{CYRILLIC CAPITAL LETTER A}"
    >>> encoded = manager.encodePassword(password, salt="")
    >>> encoded
    '04b4eec7154c5f3a2ec6d2956fb80b80dc737402'
    >>> manager.checkPassword(encoded, password)
    True
    >>> manager.checkPassword(encoded, password + u"wrong")
    False

    >>> encoded = manager.encodePassword(password)
    >>> encoded[-40:]
    '04b4eec7154c5f3a2ec6d2956fb80b80dc737402'
    >>> manager.checkPassword(encoded, password)
    True
    >>> manager.checkPassword(encoded, password + u"wrong")
    False

    >>> manager.encodePassword(password) != manager.encodePassword(password)
    True
    """

    implements(IPasswordManager)

    def encodePassword(self, password, salt=None):
        if salt is None:
            salt = "%08x" % randint(0, 0xffffffff)
        return salt + sha.new(_encoder(password)[0]).hexdigest()

    def checkPassword(self, storedPassword, password):
        salt = storedPassword[:-40]
        return storedPassword == self.encodePassword(password, salt)


# Simple registry used by mkzopeinstance script
managers = [
    ("Plain Text", PlainTextPasswordManager()), # default
    ("MD5", MD5PasswordManager()),
    ("SHA1", SHA1PasswordManager()),
]


class PasswordManagerNamesVocabulary(UtilityVocabulary):
    """Vocabulary of password managers."""

    classProvides(IVocabularyFactory)
    interface = IPasswordManager
    nameOnly = True
