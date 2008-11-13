##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Placeful internationalization of content objects.

$Id: interfaces.py 39752 2005-10-30 20:16:09Z srichter $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface
from zope.i18n.interfaces import ITranslationDomain, IMessageCatalog
from zope.app.container.interfaces import IContainer


class IWriteTranslationDomain(Interface):
    """This interface describes the methods that are necessary for an editable
    Translation Domain to work.

    For a translation domain to be editable its 'messages' have to support
    the following information: id, string, domain, language, date

    Most of the information will be natural, since they are required by the
    translation domain, but especially the date is not a necessary info
    (in fact, it is meta data)
    """

    def getMessage(msgid, langauge):
        """Get the full message of a particular language."""

    def getMessageIds(filter='%'):
        """Get all the message ids of this domain."""

    def getMessages():
        """Get all the messages of this domain."""

    def getAllLanguages():
        """Find all the languages that are available"""

    def getAvailableLanguages():
        """Find all the languages that are available."""

    def addMessage(msgid, msg, language, mod_time=None):
        """Add a message to the translation domain.

        If `mod_time` is ``None``, then the current time should be inserted.
        """

    def updateMessage(msgid, msg, language, mod_time=None):
        """Update a message in the translation domain.

        If `mod_time` is ``None``, then the current time should be inserted.
        """

    def deleteMessage(domain, msgid, language):
        """Delete a messahe in the translation domain."""

    def addLanguage(language):
        """Add Language to Translation Domain"""

    def deleteLanguage(language):
        """Delete a Domain from the Translation Domain."""


class ISyncTranslationDomain(Interface):
    """This interface allows translation domains to be synchronized. The
    following four synchronization states can exist:

    0 - uptodate: The two messages are in sync.
             Default Action: Do nothing.

    1 - new: The message exists on the foreign TS, but is locally unknown.
             Default Action: Add the message to the local catalog.

    2 - older: The local version of the message is older than the one on
             the server.
             Default Action: Update the local message.

    3 - newer: The local version is newer than the foreign version.
             Default Action: Do nothing.

    4 - deleted: The message does not exist in the foreign TS.
             Default Action: Delete local version of message.
    """

    def getMessagesMapping(languages, foreign_messages):
        """Creates a mapping of the passed foreign messages and the local ones.
        Returns a status report in a dictionary with keys of the form
        (msgid, domain, language) and values being a tuple of:

        foreign_mod_date, local_mod_date
        """

    def synchronize(messages_mapping):
        """Update the local message catalogs based on the foreign data.
        """


class ILocalTranslationDomain(ITranslationDomain,
                              IWriteTranslationDomain,
                              ISyncTranslationDomain,
                              IContainer):
    """This is the common and full-features translation domain. Almost all
    translation domain implementations will use this interface.

    An exception to this is the `GlobalMessageCatalog` as it will be read-only.
    """


class ILocalMessageCatalog(IMessageCatalog):
    """If this interfaces is implemented by a message catalog, then we will be
    able to update our messages.

    Note that not all methods here require write access, but they should
    not be required for an `IReadMessageCatalog` and are used for editing
    only. Therefore this is the more suitable interface to put them.
    """

    def getFullMessage(msgid):
        """Get the message data and meta data as a nice dictionary. More
        advanced implementation might choose to return an object with
        the data, but the object should then implement `IEnumerableMapping`.

        An exception is raised if the message id is not found.
        """

    def setMessage(msgid, message, mod_time=None):
        """Set a message to the catalog. If `mod_time` is ``None`` use the
        current time instead as modification time."""

    def deleteMessage(msgid):
        """Delete a message from the catalog."""

    def getMessageIds():
        """Get a list of all the message ids."""

    def getMessages():
        """Get a list of all the messages."""

