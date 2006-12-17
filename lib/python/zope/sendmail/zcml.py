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
"""'mail' ZCML Namespaces Schemas

$Id: zcml.py 67263 2006-04-21 22:04:21Z philikon $
"""
__docformat__ = 'restructuredtext'

from zope.component import queryUtility
from zope.component.zcml import handler, proxify, PublicPermission
from zope.configuration.fields import Path
from zope.configuration.exceptions import ConfigurationError
from zope.interface import Interface
from zope.schema import TextLine, ASCII, BytesLine, Int
from zope.security.checker import InterfaceChecker, CheckerPublic
from zope.security.zcml import Permission

from zope.sendmail.delivery import QueuedMailDelivery, DirectMailDelivery
from zope.sendmail.delivery import QueueProcessorThread
from zope.sendmail.interfaces import IMailer, IMailDelivery
from zope.sendmail.mailer import SMTPMailer

def _assertPermission(permission, interfaces, component):
    if permission is not None:
        if permission == PublicPermission:
            permission = CheckerPublic
        checker = InterfaceChecker(interfaces, permission)

    return proxify(component, checker)

class IDeliveryDirective(Interface):
    """This abstract directive describes a generic mail delivery utility
    registration."""

    name = TextLine(
        title=u"Name",
        description=u'Specifies the Delivery name of the mail utility. '\
                    u'The default is "Mail".',
        default=u"Mail",
        required=False)

    permission = Permission(
        title=u"Permission",
        description=u"Defines the permission needed to use this service.",
        required=True)

    mailer = TextLine(
        title=u"Mailer",
        description=u"Defines the mailer to be used for sending mail.",
        required=True)


class IQueuedDeliveryDirective(IDeliveryDirective):
    """This directive creates and registers a global queued mail utility. It
    should be only called once during startup."""

    queuePath = Path(
        title=u"Queue Path",
        description=u"Defines the path for the queue directory.",
        required=True)

def queuedDelivery(_context, permission, queuePath, mailer, name="Mail"):

    def createQueuedDelivery():
        delivery = QueuedMailDelivery(queuePath)
        delivery = _assertPermission(permission, IMailDelivery, delivery)

        handler('registerUtility', delivery, IMailDelivery, name)

        mailerObject = queryUtility(IMailer, mailer)
        if mailerObject is None:
            raise ConfigurationError("Mailer %r is not defined" %mailer)

        thread = QueueProcessorThread()
        thread.setMailer(mailerObject)
        thread.setQueuePath(queuePath)
        thread.start()

    _context.action(
            discriminator = ('delivery', name),
            callable = createQueuedDelivery,
            args = () )

class IDirectDeliveryDirective(IDeliveryDirective):
    """This directive creates and registers a global direct mail utility. It
    should be only called once during startup."""

def directDelivery(_context, permission, mailer, name="Mail"):

    def createDirectDelivery():
        mailerObject = queryUtility(IMailer, mailer)
        if mailerObject is None:
            raise ConfigurationError("Mailer %r is not defined" %mailer)

        delivery = DirectMailDelivery(mailerObject)
        delivery = _assertPermission(permission, IMailDelivery, delivery)

        handler('registerUtility', delivery, IMailDelivery, name)

    _context.action(
            discriminator = ('utility', IMailDelivery, name),
            callable = createDirectDelivery,
            args = () )

class IMailerDirective(Interface):
    """A generic directive registering a mailer for the mail utility."""

    name = TextLine(
        title=u"Name",
        description=u"Name of the Mailer.",
        required=True)


class ISMTPMailerDirective(IMailerDirective):
    """Registers a new SMTP mailer."""

    hostname = BytesLine(
        title=u"Hostname",
        description=u"Hostname of the SMTP host.",
        default="localhost",
        required=False)

    port = Int(
        title=u"Port",
        description=u"Port of the SMTP server.",
        default=25,
        required=False)

    username = TextLine(
        title=u"Username",
        description=u"A username for SMTP AUTH.",
        required=False)

    password = TextLine(
        title=u"Password",
        description=u"A password for SMTP AUTH.",
        required=False)

def smtpMailer(_context, name, hostname="localhost", port="25",
               username=None, password=None):
    _context.action(
        discriminator = ('utility', IMailer, name),
        callable = handler,
        args = ('registerUtility',
                SMTPMailer(hostname, port, username, password), IMailer, name)
        )
