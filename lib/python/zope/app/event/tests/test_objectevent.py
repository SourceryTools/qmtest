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
"""Object Event Tests

$Id: test_objectevent.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
import zope.component.event
from zope.testing import doctest

from zope.app.container.contained import Contained, ObjectRemovedEvent
from zope.app.container.interfaces import IContained, IObjectRemovedEvent
from zope.app.container.sample import SampleContainer
from zope.app.testing.placelesssetup import setUp, tearDown
from zope.app.testing import ztapi

class TestObjectEventNotifications(unittest.TestCase):

    def setUp(self):
        self.callbackTriggered = False
        setUp()

    def tearDown(self):
        tearDown()

    def testNotify(self):
        events = []

        def record(*args):
            events.append(args)

        ztapi.subscribe([IContained, IObjectRemovedEvent], None, record)

        item = Contained()
        event = ObjectRemovedEvent(item)
        zope.component.event.objectEventNotify(event)
        self.assertEqual([(item, event)], events)

    def testNotifyNobody(self):
        # Check that notify won't raise an exception in absence of
        # of subscribers.
        events = []
        item = Contained()
        evt = ObjectRemovedEvent(item)
        zope.component.event.objectEventNotify(evt)
        self.assertEqual([], events)

    def testVeto(self):
        zope.component.provideHandler(zope.component.event.objectEventNotify)
        container = SampleContainer()
        item = Contained()

        # This will fire an event.
        container['Fred'] = item

        class Veto(Exception):
            pass
        
        def callback(item, event):
            self.callbackTriggered = True
            self.assertEqual(item, event.object)
            raise Veto

        ztapi.subscribe([IContained, IObjectRemovedEvent], None, callback)

        # del container['Fred'] will fire an ObjectRemovedEvent event.
        self.assertRaises(Veto, container.__delitem__, 'Fred')
        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestObjectEventNotifications),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
