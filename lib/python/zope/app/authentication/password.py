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

$Id: password.py 67630 2006-04-27 00:54:03Z jim $
"""

import md5
import sha

from zope.interface import implements, classProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.app.component.vocabulary import UtilityVocabulary

from zope.app.authentication.interfaces import IPasswordManager


class PlainTextPasswordManager(object):
    """Plain text password manager.

    >>> from zope.interface.verify import verifyObject

    >>> manager = PlainTextPasswordManager()
    >>> verifyObject(IPasswordManager, manager)
    True

    >>> encoded = manager.encodePassword("password")
    >>> encoded
    'password'
    >>> manager.checkPassword(encoded, "password")
    True
    >>> manager.checkPassword(encoded, "bad")
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

    >>> encoded = manager.encodePassword("password")
    >>> encoded
    '5f4dcc3b5aa765d61d8327deb882cf99'
    >>> manager.checkPassword(encoded, "password")
    True
    >>> manager.checkPassword(encoded, "bad")
    False
    """

    implements(IPasswordManager)

    def encodePassword(self, password):
        return md5.new(password).hexdigest()

class SHA1PasswordManager(PlainTextPasswordManager):
    """SHA1 password manager.

    >>> from zope.interface.verify import verifyObject

    >>> manager = SHA1PasswordManager()
    >>> verifyObject(IPasswordManager, manager)
    True

    >>> encoded = manager.encodePassword("password")
    >>> encoded
    '5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8'
    >>> manager.checkPassword(encoded, "password")
    True
    >>> manager.checkPassword(encoded, "bad")
    False
    """

    implements(IPasswordManager)

    def encodePassword(self, password):
        return sha.new(password).hexdigest()

# Simple registry used by mkzopeinstance script
managers = [
    ("Plain Text", PlainTextPasswordManager()), # default
    ("MD5", MD5PasswordManager()),
    ("SHA1", SHA1PasswordManager()),
]

class PasswordManagerNamesVocabulary(UtilityVocabulary):
    classProvides(IVocabularyFactory)
    interface = IPasswordManager
    nameOnly = True
