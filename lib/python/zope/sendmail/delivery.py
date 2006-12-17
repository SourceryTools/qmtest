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
"""Mail Delivery utility implementation

This module contains various implementations of `MailDeliverys`.

$Id: delivery.py 67263 2006-04-21 22:04:21Z philikon $
"""
__docformat__ = 'restructuredtext'

import rfc822
import threading
import logging
import atexit
import time
from os import unlink, getpid
from cStringIO import StringIO
from random import randrange
from time import strftime
from socket import gethostname

from zope.interface import implements
from zope.sendmail.interfaces import IDirectMailDelivery, IQueuedMailDelivery
from zope.sendmail.maildir import Maildir
from transaction.interfaces import IDataManager
import transaction


class MailDataManager(object):
    implements(IDataManager)

    def __init__(self, callable, args=(), onAbort=None):
        self.callable = callable
        self.args = args
        self.onAbort = onAbort
        # Use the default thread transaction manager.
        self.transaction_manager = transaction.manager

    def commit(self, transaction):
        pass

    def abort(self, transaction):
         if self.onAbort:
            self.onAbort()

    def sortKey(self):
        return id(self)

    # No subtransaction support.
    def abort_sub(self, transaction):
        pass

    commit_sub = abort_sub

    def beforeCompletion(self, transaction):
        pass

    afterCompletion = beforeCompletion

    def tpc_begin(self, transaction, subtransaction=False):
        assert not subtransaction

    def tpc_vote(self, transaction):
        pass

    def tpc_finish(self, transaction):
        self.callable(*self.args)

    tpc_abort = abort


class AbstractMailDelivery(object):

    def newMessageId(self):
        """Generates a new message ID according to RFC 2822 rules"""
        randmax = 0x7fffffff
        left_part = '%s.%d.%d' % (strftime('%Y%m%d%H%M%S'),
                                  getpid(),
                                  randrange(0, randmax))
        return "%s@%s" % (left_part, gethostname())

    def send(self, fromaddr, toaddrs, message):
        parser = rfc822.Message(StringIO(message))
        messageid = parser.getheader('Message-Id')
        if messageid:
            if not messageid.startswith('<') or not messageid.endswith('>'):
                raise ValueError('Malformed Message-Id header')
            messageid = messageid[1:-1]
        else:
            messageid = self.newMessageId()
            message = 'Message-Id: <%s>\n%s' % (messageid, message)
        transaction.get().join(
            self.createDataManager(fromaddr, toaddrs, message))
        return messageid


class DirectMailDelivery(AbstractMailDelivery):
    __doc__ = IDirectMailDelivery.__doc__

    implements(IDirectMailDelivery)

    def __init__(self, mailer):
        self.mailer = mailer

    def createDataManager(self, fromaddr, toaddrs, message):
        return MailDataManager(self.mailer.send,
                               args=(fromaddr, toaddrs, message))


class QueuedMailDelivery(AbstractMailDelivery):
    __doc__ = IQueuedMailDelivery.__doc__

    implements(IQueuedMailDelivery)

    def __init__(self, queuePath):
        self._queuePath = queuePath

    queuePath = property(lambda self: self._queuePath)

    def createDataManager(self, fromaddr, toaddrs, message):
        maildir = Maildir(self.queuePath, True)
        msg = maildir.newMessage()
        msg.write('X-Zope-From: %s\n' % fromaddr)
        msg.write('X-Zope-To: %s\n' % ", ".join(toaddrs))
        msg.write(message)
        return MailDataManager(msg.commit, onAbort=msg.abort)


class QueueProcessorThread(threading.Thread):
    """This thread is started at configuration time from the
    `mail:queuedDelivery` directive handler.
    """

    log = logging.getLogger("QueueProcessorThread")
    __stopped = False

    def __init__(self):
        threading.Thread.__init__(self)

    def setMaildir(self, maildir):
        """Set the maildir.

        This method is used just to provide a `maildir` stubs ."""
        self.maildir = maildir

    def setQueuePath(self, path):
        self.maildir = Maildir(path, True)

    def setMailer(self, mailer):
        self.mailer = mailer

    def _parseMessage(self, message):
        """Extract fromaddr and toaddrs from the first two lines of
        the `message`.

        Returns a fromaddr string, a toaddrs tuple and the message
        string.
        """

        fromaddr = ""
        toaddrs = ()
        rest = ""

        try:
            first, second, rest = message.split('\n', 2)
        except ValueError:
            return fromaddr, toaddrs, message

        if first.startswith("X-Zope-From: "):
            i = len("X-Zope-From: ")
            fromaddr = first[i:]

        if second.startswith("X-Zope-To: "):
            i = len("X-Zope-To: ")
            toaddrs = tuple(second[i:].split(", "))

        return fromaddr, toaddrs, rest

    def run(self, forever=True):
        atexit.register(self.stop)
        while not self.__stopped:
            for filename in self.maildir:
                fromaddr = ''
                toaddrs = ()
                try:
                    file = open(filename)
                    message = file.read()
                    file.close()
                    fromaddr, toaddrs, message = self._parseMessage(message)
                    self.mailer.send(fromaddr, toaddrs, message)
                    unlink(filename)
                    # TODO: maybe log the Message-Id of the message sent
                    self.log.info("Mail from %s to %s sent.",
                                  fromaddr, ", ".join(toaddrs))
                    # Blanket except because we don't want
                    # this thread to ever die
                except:
                    if fromaddr != '' or toaddrs != ():
                        self.log.error(
                            "Error while sending mail from %s to %s.",
                            fromaddr, ", ".join(toaddrs), exc_info=True)
                    else:
                        self.log.error(
                            "Error while sending mail : %s ",
                            filename, exc_info=True)
            else:
                if forever:
                    time.sleep(3)

            # A testing plug
            if not forever:
                break

    def stop(self):
        self.__stopped = True
