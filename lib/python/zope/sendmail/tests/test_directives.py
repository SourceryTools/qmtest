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
"""Test the gts ZCML namespace directives.

$Id: test_directives.py 66922 2006-04-12 23:28:07Z jinty $
"""
import os
import shutil
import unittest
import threading
import time

import zope.component
from zope.component.testing import PlacelessSetup
from zope.configuration import xmlconfig
from zope.interface import implements

from zope.sendmail.interfaces import \
     IMailDelivery, IMailer, ISMTPMailer
from zope.sendmail.delivery import QueueProcessorThread
from zope.sendmail import delivery
import zope.sendmail.tests


class MaildirStub(object):

    def __init__(self, path, create=False):
        self.path = path
        self.create = create

    def __iter__(self):
        return iter(())

    def newMessage(self):
        return None

class Mailer(object):
    implements(IMailer)


class DirectivesTest(PlacelessSetup, unittest.TestCase):

    mailbox = os.path.join(os.path.dirname(__file__), 'mailbox')

    def setUp(self):
        super(DirectivesTest, self).setUp()
        self.testMailer = Mailer()

        gsm = zope.component.getGlobalSiteManager()
        gsm.registerUtility(Mailer(), IMailer, "test.smtp")
        gsm.registerUtility(self.testMailer, IMailer, "test.mailer")

        self.context = xmlconfig.file("mail.zcml", zope.sendmail.tests)
        self.orig_maildir = delivery.Maildir
        delivery.Maildir = MaildirStub

    def tearDown(self):
        delivery.Maildir = self.orig_maildir

        # Tear down the mail queue processor thread.
        # Give the other thread a chance to start:
        time.sleep(0.001)
        threads = list(threading.enumerate())
        for thread in threads:
            if isinstance(thread, QueueProcessorThread):
                thread.stop()
                thread.join()

        shutil.rmtree(self.mailbox, True)

    def testQueuedDelivery(self):
        delivery = zope.component.getUtility(IMailDelivery, "Mail")
        self.assertEqual('QueuedMailDelivery', delivery.__class__.__name__)
        self.assertEqual(self.mailbox, delivery.queuePath)

    def testDirectDelivery(self):
        delivery = zope.component.getUtility(IMailDelivery, "Mail2")
        self.assertEqual('DirectMailDelivery', delivery.__class__.__name__)
        self.assert_(self.testMailer is delivery.mailer)

    def testSMTPMailer(self):
        mailer = zope.component.getUtility(IMailer, "smtp")
        self.assert_(ISMTPMailer.providedBy(mailer))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DirectivesTest),
        ))

if __name__ == '__main__':
    unittest.main()
