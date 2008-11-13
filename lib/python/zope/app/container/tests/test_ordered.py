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

$Id: test_ordered.py 71677 2006-12-29 22:07:05Z srichter $
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

def test_all_items_available_at_object_added_event():
    """
    Prepare the setup::

        >>> root = setup.placefulSetUp(site=True)

    Now register an event subscriber to object added events.

        >>> import zope.component
        >>> from zope.app.container import interfaces

        >>> @zope.component.adapter(interfaces.IObjectAddedEvent)
        ... def printContainerKeys(event):
        ...     print event.newParent.keys()

        >>> zope.component.provideHandler(printContainerKeys)

    Now we are adding an object to the container. 

        >>> from zope.app.container.ordered import OrderedContainer
        >>> oc = OrderedContainer()
        >>> oc['foo'] = 'FOO'
        ['foo']

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
