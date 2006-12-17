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
"""Test the OrderedContainer.

$Id: test_ordered.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite
from zope.component.eventtesting import getEvents, clearEvents
from zope.app.testing import placelesssetup, setup

def test_order_events():
    """
    Prepare the setup::

        >>> root = setup.placefulSetUp(site=True)

    Prepare some objects::

        >>> from zope.app.container.ordered import OrderedContainer
        >>> oc = OrderedContainer()
        >>> oc['foo'] = 'bar'
        >>> oc['baz'] = 'quux'
        >>> oc['zork'] = 'grue'
        >>> oc.keys()
        ['foo', 'baz', 'zork']

    Now change the order::

        >>> clearEvents()
        >>> oc.updateOrder(['baz', 'foo', 'zork'])
        >>> oc.keys()
        ['baz', 'foo', 'zork']

    Check what events have been sent::

        >>> events = getEvents()
        >>> [event.__class__.__name__ for event in events]
        ['ContainerModifiedEvent']

    This is in fact a specialized modification event::

        >>> from zope.lifecycleevent.interfaces import IObjectModifiedEvent
        >>> IObjectModifiedEvent.providedBy(events[0])
        True

    Finally, tear down::

        >>> setup.placefulTearDown()
    """

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(DocTestSuite("zope.app.container.ordered",
                               setUp=placelesssetup.setUp,
                               tearDown=placelesssetup.tearDown))
    suite.addTest(DocTestSuite())
    return suite

if __name__ == '__main__':
    unittest.main()
