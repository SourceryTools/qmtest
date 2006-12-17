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
"""Tests for the unique id utility.

$Id: tests.py 30863 2005-06-20 15:31:55Z jim $
"""
import unittest

def test_multi_databases():
    """
    >>> from ZODB.tests.util import DB
    >>> import transaction
    >>> from BTrees.OOBTree import OOBucket

    >>> databases = {}

    >>> db1 = DB(databases=databases, database_name='1')
    >>> db2 = DB(databases=databases, database_name='2')

    >>> conn1 = db1.open()
    >>> conn1.root()['ob'] = OOBucket()

    >>> conn2 = conn1.get_connection('2')
    >>> conn2.root()['ob'] = OOBucket()

    >>> conn1.root()['ob']._p_oid == conn2.root()['ob']._p_oid
    True

    >>> transaction.commit()

    >>> from zope.app.keyreference.persistent import KeyReferenceToPersistent

    >>> key1 = KeyReferenceToPersistent(conn1.root()['ob'])
    >>> key2 = KeyReferenceToPersistent(conn2.root()['ob'])

    >>> key1 != key2, key2 > key1, hash(key1) != hash(key2)
    (True, True, True)

"""

def test_suite():
    from zope.testing import doctest
    return unittest.TestSuite((
        doctest.DocFileSuite('persistent.txt'),
        doctest.DocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

