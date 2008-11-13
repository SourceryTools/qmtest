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
"""Contained Tests

$Id: test_contained.py 37532 2005-07-28 16:26:49Z jim $
"""
import unittest
import gc
from ZODB.DemoStorage import DemoStorage
from ZODB.DB import DB
import transaction
from persistent import Persistent

import zope.interface
from zope.testing import doctest

from zope.app.container.contained import ContainedProxy
from zope.app.testing import placelesssetup

class MyOb(Persistent):
    pass

def test_basic_proxy_attribute_management_and_picklability():
    """Contained-object proxy

    This is a picklable proxy that can be put around objects that
    don't implement IContained.

    >>> l = [1, 2, 3]
    >>> p = ContainedProxy(l)
    >>> p.__parent__ = 'Dad'
    >>> p.__name__ = 'p'
    >>> p
    [1, 2, 3]
    >>> p.__parent__
    'Dad'
    >>> p.__name__
    'p'

    >>> import pickle
    >>> p2 = pickle.loads(pickle.dumps(p))
    >>> p2
    [1, 2, 3]
    >>> p2.__parent__
    'Dad'
    >>> p2.__name__
    'p'
    """

def test_basic_persistent_w_non_persistent_proxied():
    """
    >>> p = ContainedProxy([1])
    >>> p.__parent__ = 2
    >>> p.__name__ = 'test'
    >>> db = DB(DemoStorage('test_storage'))
    >>> c = db.open()
    >>> c.root()['p'] = p
    >>> transaction.commit()

    >>> c2 = db.open()
    >>> p2 = c2.root()['p']
    >>> p2
    [1]
    >>> p2.__parent__
    2
    >>> p2.__name__
    'test'

    >>> p2._p_changed
    0
    >>> p2._p_deactivate()
    >>> p2._p_changed
    >>> p2.__name__
    'test'

    >>> db.close()
    """

def test_declarations_on_ContainedProxy():
    r"""

    It is possible to make declarations on ContainedProxy objects.

      >>> class I1(zope.interface.Interface):
      ...     pass
      >>> class C(object):
      ...     zope.interface.implements(I1)

      >>> c = C()
      >>> p = ContainedProxy(c)

    ContainedProxy provides no interfaces on it's own:

      >>> tuple(zope.interface.providedBy(ContainedProxy))
      ()

    It implements IContained and IPersistent:

      >>> tuple(zope.interface.implementedBy(ContainedProxy))
      (<InterfaceClass zope.app.container.interfaces.IContained>,
       <InterfaceClass persistent.interfaces.IPersistent>)

    A proxied object has IContainer, in addition to what the unproxied
    object has:

      >>> tuple(zope.interface.providedBy(p))
      (<InterfaceClass zope.app.container.tests.test_contained.I1>,
       <InterfaceClass zope.app.container.interfaces.IContained>,
       <InterfaceClass persistent.interfaces.IPersistent>)

      >>> class I2(zope.interface.Interface):
      ...     pass
      >>> zope.interface.directlyProvides(c, I2)
      >>> tuple(zope.interface.providedBy(p))
      (<InterfaceClass zope.app.container.tests.test_contained.I2>,
       <InterfaceClass zope.app.container.tests.test_contained.I1>,
       <InterfaceClass zope.app.container.interfaces.IContained>,
       <InterfaceClass persistent.interfaces.IPersistent>)

    We can declare interfaces through the proxy:

      >>> class I3(zope.interface.Interface):
      ...     pass
      >>> zope.interface.directlyProvides(p, I3)
      >>> tuple(zope.interface.providedBy(p))
      (<InterfaceClass zope.app.container.tests.test_contained.I3>,
       <InterfaceClass zope.app.container.tests.test_contained.I1>,
       <InterfaceClass zope.app.container.interfaces.IContained>,
       <InterfaceClass persistent.interfaces.IPersistent>)

    """

def test_basic_persistent_w_persistent_proxied():
    """

    Here, we'll verify that shared references work and
    that updates to both the proxies and the proxied objects
    are made correctly.

            ----------------------
            |                    |
          parent                other
            |                 /
           ob  <--------------

    Here we have an object, parent, that contains ob.  There is another
    object, other, that has a non-container reference to ob.

    >>> parent = MyOb()
    >>> parent.ob = ContainedProxy(MyOb())
    >>> parent.ob.__parent__ = parent
    >>> parent.ob.__name__ = 'test'
    >>> other = MyOb()
    >>> other.ob = parent.ob

    We can change ob through either parent or other

    >>> parent.ob.x = 1
    >>> other.ob.y = 2

    Now we'll save the data:

    >>> db = DB(DemoStorage('test_storage'))
    >>> c1 = db.open()
    >>> c1.root()['parent'] = parent
    >>> c1.root()['other'] = other
    >>> transaction.commit()

    We'll open a second connection and verify that we have the data we
    expect:

    >>> c2 = db.open()
    >>> p2 = c2.root()['parent']
    >>> p2.ob.__parent__ is p2
    1
    >>> p2.ob.x
    1
    >>> p2.ob.y
    2
    >>> o2 = c2.root()['other']
    >>> o2.ob is p2.ob
    1
    >>> o2.ob is p2.ob
    1
    >>> o2.ob.__name__
    'test'

    Now we'll change things around a bit. We'll move things around
    a bit. We'll also add an attribute to ob

    >>> o2.ob.__name__ = 'test 2'
    >>> o2.ob.__parent__ = o2
    >>> o2.ob.z = 3

    >>> p2.ob.__parent__ is p2
    0
    >>> p2.ob.__parent__ is o2
    1

    And save the changes:

    >>> transaction.commit()

    Now we'll reopen the first connection and verify that we can see
    the changes:

    >>> c1.close()
    >>> c1 = db.open()
    >>> p2 = c1.root()['parent']
    >>> p2.ob.__name__
    'test 2'
    >>> p2.ob.z
    3
    >>> p2.ob.__parent__ is c1.root()['other']
    1

    >>> db.close()
    """

def test_proxy_cache_interaction():
    """Test to make sure the proxy properly interacts with the object cache

    Persistent objects are their own weak refs.  Thier deallocators
    need to notify their connection's cache that their object is being
    deallocated, so that it is removed from the cache.

    >>> from ZODB.tests.util import DB
    >>> db = DB()
    >>> db.setCacheSize(5)
    >>> conn = db.open()
    >>> conn.root()['p'] = ContainedProxy(None)

    We need to create some filler objects to push our proxy out of the cache:

    >>> for i in range(10):
    ...     conn.root()[i] = MyOb()

    >>> transaction.commit()

    Let's get the oid of our proxy:

    >>> oid = conn.root()['p']._p_oid

    Now, we'll access the filler object's:

    >>> x = [getattr(conn.root()[i], 'x', 0) for i in range(10)]

    We've also accessed the root object. If we garbage-collect the
    cache:

    >>> conn._cache.incrgc()

    Then the root object will still be active, because it was accessed
    recently:

    >>> conn.root()._p_changed
    0

    And the proxy will be in the cache, because it's refernced from
    the root object:

    >>> conn._cache.get(oid) is not None
    True

    But it's a ghost:

    >>> conn.root()['p']._p_changed

    If we deactivate the root object:

    >>> conn.root()._p_deactivate()

    Then we'll release the last reference to the proxy and it should
    no longer be in the cache. To be sure, we'll call gc:

    >>> x = gc.collect()
    >>> conn._cache.get(oid) is not None
    False

    """

def test_ContainedProxy_instances_have_no_instance_dictionaries():
    """Make sure that proxies don't introduce extra instance dictionaries

    >>> from zope.app.container.contained import ContainedProxy
    >>> class C:
    ...     pass

    >>> c = C()
    >>> c.x = 1
    >>> c.__dict__
    {'x': 1}

    >>> p = ContainedProxy(c)
    >>> p.__dict__
    {'x': 1}
    >>> p.y = 3
    >>> p.__dict__
    {'y': 3, 'x': 1}
    >>> c.__dict__
    {'y': 3, 'x': 1}

    >>> p.__dict__ is c.__dict__
    True
    
    """

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite('zope.app.container.contained',
                             setUp=placelesssetup.setUp,
                             tearDown=placelesssetup.tearDown),
        doctest.DocTestSuite(optionflags=doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__': unittest.main()
