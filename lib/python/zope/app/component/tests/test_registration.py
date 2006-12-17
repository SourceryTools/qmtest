##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Registration Tests

$Id$
"""
__docformat__ = "reStructuredText"

import os
import unittest
import warnings

from ZODB.DB import DB
import ZODB.FileStorage
from ZODB.DemoStorage import DemoStorage
import transaction
import persistent

import zope.component.globalregistry
import zope.component.testing as placelesssetup
from zope.testing import doctest
from zope.app.testing import setup
import zope.app.container.contained
from zope import interface

import zope.app.component.site


# test class for testing data conversion
class IFoo(interface.Interface):
    pass
class Foo(persistent.Persistent, zope.app.container.contained.Contained):
    interface.implements(IFoo)
    name = ''
    def __init__(self, name=''):
        self.name = name

    def __repr__(self):
        return 'Foo(%r)' % self.name

def setUpOld(test):
    placelesssetup.setUp(test)
    setup.setUpAnnotations()
    setup.setUpDependable()
    setup.setUpTraversal()
    test.globs['showwarning'] = warnings.showwarning
    warnings.showwarning = lambda *a, **k: None

def tearDown(test):
    warnings.showwarning = test.globs['showwarning']
    placelesssetup.tearDown(test)

def setUp(test):
    placelesssetup.setUp(test)
    test.globs['showwarning'] = warnings.showwarning
    warnings.showwarning = lambda *a, **k: None

def oldfs():
    return FileStorage(
        os.path.join(os.path.dirname(__file__), 'gen3.fs'),
        read_only=True,
        )

# Work around a bug in ZODB
# XXX fix ZODB
class FileStorage(ZODB.FileStorage.FileStorage):
    
    def new_oid(self):
        self._lock_acquire()
        try:
            last = self._oid
            d = ord(last[-1])
            if d < 255:  # fast path for the usual case
                last = last[:-1] + chr(d+1)
            else:        # there's a carry out of the last byte
                last_as_long, = _structunpack(">Q", last)
                last = _structpack(">Q", last_as_long + 1)
            self._oid = last
            return last
        finally:
             self._lock_release()
 

def test_old_databases_backward_compat():
    """

Let's open an old database and get the 3 site managers in it:

    >>> fs = oldfs()
    >>> demo = DemoStorage(base=fs)
    >>> db = DB(demo)
    >>> tm = transaction.TransactionManager()
    >>> root = db.open(transaction_manager=tm).root()
    >>> _ = tm.begin()
    
    >>> sm1 = root['Application'].getSiteManager()
    >>> [sm2] = sm1.subs
    >>> [sm3] = sm2.subs

We can look up utilities as we expect:

    >>> sm1.getUtility(IFoo, '1') is sm1['default']['1']
    True

    >>> sm3.getUtility(IFoo, '3') is sm3['default']['3']
    True

    >>> sm2.getUtility(IFoo, '2') is sm2['default']['2']
    True

    >>> sm1.getUtility(IFoo, '2') is sm1['default']['2']
    True

    >>> sm1.getUtility(IFoo, '3') is sm1['default']['3']
    True

    >>> sm2.getUtility(IFoo, '3') is sm2['default']['3']
    True

    >>> sm2.getUtility(IFoo, '4') is sm2['default']['4']
    True

    >>> sm3.getUtility(IFoo, '4') is sm3['default']['4']
    True

    >>> sm3.getUtility(IFoo, '5') is sm3['default']['5']
    True

and we get registration info:

    >>> sorted([r.name for r in sm2.registeredUtilities()])
    [u'2', u'3', u'4']

We don't have any adapter or subscriber information, because it wasn't
previously supported to register those:

    >>> len(list(sm2.registeredAdapters()))
    0
    >>> len(list(sm2.registeredSubscriptionAdapters()))
    0
    >>> len(list(sm2.registeredHandlers()))
    0

We haven't modified anything yet.  We can see this in a number of
ways.  If we look at the internal data structured used, we can see
that they are weird:

    >>> sm2._utility_registrations.__class__.__name__
    '_OldUtilityRegistrations'

    >>> sm2._adapter_registrations.__class__.__name__
    '_OldAdapterRegistrations'

    >>> sm2._subscription_registrations.__class__.__name__
    '_OldSubscriberRegistrations'

    >>> sm2._handler_registrations.__class__.__name__
    '_OldSubscriberRegistrations'

and the registries have a _registrations attribute, which is a sign
that they haven't been converted yet:

    >>> hasattr(sm2.utilities, '_registrations')
    True

    >>> hasattr(sm2.adapters, '_registrations')
    True

We'll commit the transaction and make sure the database hasn't
grown. (This relies on a buglet in DemoStorage length computation.)

    >>> tm.commit()
    >>> len(demo) == len(fs)
    True

Of course, we can register new utilities:

    >>> _ = tm.begin()
    >>> sm1.registerUtility(Foo('one'), IFoo, '1')
    >>> sm2.registerUtility(Foo('two'), IFoo, '2')
    >>> tm.commit()

We should then be able to look up the newly registered utilities.
Let's try to do so in a separate connection:

    >>> tm2 = transaction.TransactionManager()
    >>> root2 = db.open(transaction_manager=tm2).root()
    >>> _ = tm2.begin()
    
    >>> sm1 = root2['Application'].getSiteManager()
    >>> [sm2] = sm1.subs
    >>> [sm3] = sm2.subs

    >>> sm1.getUtility(IFoo, '1').name
    'one'

    >>> sm2.getUtility(IFoo, '2').name
    'two'

    >>> sm1.getUtility(IFoo, '2') is sm1['default']['2']
    True

    >>> sm1.getUtility(IFoo, '3') is sm1['default']['3']
    True

    >>> sm2.getUtility(IFoo, '3') is sm2['default']['3']
    True

    >>> sm2.getUtility(IFoo, '4') is sm2['default']['4']
    True

    >>> sm3.getUtility(IFoo, '4') is sm3['default']['4']
    True

    >>> sm3.getUtility(IFoo, '5') is sm3['default']['5']
    True

    >>> sorted([r.name for r in sm2.registeredUtilities()])
    [u'2', u'3', u'4']


Because we registered utilities, the corresponding data structures
have been updated:

    >>> sm2._utility_registrations.__class__.__name__
    'PersistentMapping'

    >>> hasattr(sm2.utilities, '_registrations')
    False

But other data structures haven't been effected:

    >>> sm2._adapter_registrations.__class__.__name__
    '_OldAdapterRegistrations'

    >>> hasattr(sm2.adapters, '_registrations')
    True

Nor, of course, have the data structures for sites that we haven't
changed:

    >>> sm3._utility_registrations.__class__.__name__
    '_OldUtilityRegistrations'

    >>> hasattr(sm3.utilities, '_registrations')
    True

The _evolve_to_generation_4 method actually converts the remaining
data structures. It also evolves all of it's subsites:

    >>> sm1._evolve_to_generation_4()
    >>> tm2.commit()

and we see that all of the data structures have been converted:

    >>> sm1._utility_registrations.__class__.__name__
    'PersistentMapping'
    >>> sm1._adapter_registrations.__class__.__name__
    'PersistentMapping'
    >>> sm1._subscription_registrations.__class__.__name__
    'PersistentList'
    >>> sm1._handler_registrations.__class__.__name__
    'PersistentList'
    >>> hasattr(sm1.utilities, '_registrations')
    False
    >>> hasattr(sm1.adapters, '_registrations')
    False

    >>> sm2._utility_registrations.__class__.__name__
    'PersistentMapping'
    >>> sm2._adapter_registrations.__class__.__name__
    'PersistentMapping'
    >>> sm2._subscription_registrations.__class__.__name__
    'PersistentList'
    >>> sm2._handler_registrations.__class__.__name__
    'PersistentList'
    >>> hasattr(sm2.utilities, '_registrations')
    False
    >>> hasattr(sm2.adapters, '_registrations')
    False

    >>> sm3._utility_registrations.__class__.__name__
    'PersistentMapping'
    >>> sm3._adapter_registrations.__class__.__name__
    'PersistentMapping'
    >>> sm3._subscription_registrations.__class__.__name__
    'PersistentList'
    >>> sm3._handler_registrations.__class__.__name__
    'PersistentList'
    >>> hasattr(sm3.utilities, '_registrations')
    False
    >>> hasattr(sm3.adapters, '_registrations')
    False

and that lookups still work as expected:


    >>> sm1.getUtility(IFoo, '1').name
    'one'

    >>> sm2.getUtility(IFoo, '2').name
    'two'

    >>> sm1.getUtility(IFoo, '2') is sm1['default']['2']
    True

    >>> sm1.getUtility(IFoo, '3') is sm1['default']['3']
    True

    >>> sm2.getUtility(IFoo, '3') is sm2['default']['3']
    True

    >>> sm2.getUtility(IFoo, '4') is sm2['default']['4']
    True

    >>> sm3.getUtility(IFoo, '4') is sm3['default']['4']
    True

    >>> sm3.getUtility(IFoo, '5') is sm3['default']['5']
    True

getAllUtilitiesRegisteredFor should work too: :)

    >>> all = list(sm3.getAllUtilitiesRegisteredFor(IFoo))
    >>> all.remove(sm1['default']['1'])
    >>> all.remove(sm1['default']['2'])
    >>> all.remove(sm1['default']['3'])
    >>> all.remove(sm2['default']['2'])
    >>> all.remove(sm2['default']['3'])
    >>> all.remove(sm2['default']['4'])
    >>> all.remove(sm3['default']['3'])
    >>> all.remove(sm3['default']['4'])
    >>> all.remove(sm3['default']['5'])
    >>> len(all)
    2

Cleanup:

    >>> db.close()

"""


class GlobalRegistry:
    pass

base = zope.component.globalregistry.GlobalAdapterRegistry(
    GlobalRegistry, 'adapters')
GlobalRegistry.adapters = base
def clear_base():
    base.__init__(GlobalRegistry, 'adapters')
    
    
def test_deghostification_of_persistent_adapter_registries():
    """

Note that this test duplicates one from zope.component.tests.
We should be able to get rid of this one when we get rid of
__setstate__ implementation we have in back35.
    
We want to make sure that we see updates corrextly.

    >>> import ZODB.tests.util
    >>> db = ZODB.tests.util.DB()
    >>> tm1 = transaction.TransactionManager()
    >>> c1 = db.open(transaction_manager=tm1)
    >>> r1 = zope.app.component.site._LocalAdapterRegistry((base,))
    >>> r2 = zope.app.component.site._LocalAdapterRegistry((r1,))
    >>> c1.root()[1] = r1
    >>> c1.root()[2] = r2
    >>> tm1.commit()
    >>> r1._p_deactivate()
    >>> r2._p_deactivate()

    >>> tm2 = transaction.TransactionManager()
    >>> c2 = db.open(transaction_manager=tm2)
    >>> r1 = c2.root()[1]
    >>> r2 = c2.root()[2]

    >>> r1.lookup((), IFoo, '')

    >>> base.register((), IFoo, '', Foo(''))
    >>> r1.lookup((), IFoo, '')
    Foo('')

    >>> r2.lookup((), IFoo, '1')

    >>> r1.register((), IFoo, '1', Foo('1'))

    >>> r2.lookup((), IFoo, '1')
    Foo('1')

    >>> r1.lookup((), IFoo, '2')
    >>> r2.lookup((), IFoo, '2')

    >>> base.register((), IFoo, '2', Foo('2'))
    
    >>> r1.lookup((), IFoo, '2')
    Foo('2')

    >>> r2.lookup((), IFoo, '2')
    Foo('2')

Cleanup:

    >>> db.close()
    >>> clear_base()

    """


def test_suite():
    suite = unittest.TestSuite((
        doctest.DocFileSuite('deprecated35_statusproperty.txt',
                             'deprecated35_registration.txt',
                             setUp=setUpOld, tearDown=tearDown),
        doctest.DocTestSuite(setUp=setUp, tearDown=tearDown)
        ))
    return suite


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
