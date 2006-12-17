##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Code to initialize the application server

$Id: appsetup.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import ZODB.interfaces
import zope.interface
import zope.component
import zope.app.component.hooks
from zope.security.interfaces import IParticipation
from zope.security.management import system_user
from zope.app.appsetup import interfaces

class SystemConfigurationParticipation(object):
    zope.interface.implements(IParticipation)

    principal = system_user
    interaction = None


_configured = False
def config(file, features=(), execute=True):
    r"""Execute the ZCML configuration file.

    This procedure defines the global site setup. Optionally you can also
    provide a list of features that are inserted in the configuration context
    before the execution is started.

    Let's create a trivial sample ZCML file.

      >>> import tempfile
      >>> fn = tempfile.mktemp('.zcml')
      >>> zcml = open(fn, 'w')
      >>> zcml.write('''
      ... <configure xmlns:meta="http://namespaces.zope.org/meta"
      ...            xmlns:zcml="http://namespaces.zope.org/zcml">
      ...   <meta:provides feature="myFeature" />
      ...   <configure zcml:condition="have myFeature2">
      ...     <meta:provides feature="myFeature4" />
      ...   </configure>
      ... </configure>
      ... ''')
      >>> zcml.close()

    We can now pass the file into the `config()` function:

      # End an old interaction first
      >>> from zope.security.management import endInteraction
      >>> endInteraction()

      >>> context = config(fn, features=('myFeature2', 'myFeature3'))
      >>> context.hasFeature('myFeature')
      True
      >>> context.hasFeature('myFeature2')
      True
      >>> context.hasFeature('myFeature3')
      True
      >>> context.hasFeature('myFeature4')
      True

    Further, we should have access to the configuration file name and context
    now:

      >>> getConfigSource() is fn
      True
      >>> getConfigContext() is context
      True

    Let's now clean up by removing the temporary file:

      >>> import os
      >>> os.remove(fn)

    """
    global _configured
    global __config_source
    __config_source = file

    if _configured:
        return

    from zope.configuration import xmlconfig, config

    # Set user to system_user, so we can do anything we want
    from zope.security.management import newInteraction
    newInteraction(SystemConfigurationParticipation())

    # Hook up custom component architecture calls
    zope.app.component.hooks.setHooks()

    # Load server-independent site config
    context = config.ConfigurationMachine()
    xmlconfig.registerCommonDirectives(context)
    for feature in features:
        context.provideFeature(feature)
    context = xmlconfig.file(file, context=context, execute=execute)

    # Reset user
    from zope.security.management import endInteraction
    endInteraction()

    _configured = execute

    global __config_context
    __config_context = context

    return context


def database(db):
    """Load ZODB database from Python module or FileStorage file"""
    if type(db) is str:
        # Database name
        if db.endswith('.py'):
            # Python source, exec it
            globals = {}
            execfile(db, globals)
            if 'DB' in globals:
                db = globals['DB']
            else:
                storage = globals['Storage']
                from ZODB.DB import DB
                db = DB(storage, cache_size=4000)
        elif db.endswith(".fs"):
            from ZODB.FileStorage import FileStorage
            from ZODB.DB import DB
            storage = FileStorage(db)
            db = DB(storage, cache_size=4000)

    # The following will fail unless the application has been configured.
    from zope.event import notify
    notify(interfaces.DatabaseOpened(db))

    return db


def multi_database(database_factories):
    """Set up a multi-database from an iterable of database factories

    Return a sequence of databases, and a mapping of from database name to
    database.

    >>> class DB:
    ...     def __init__(self, number):
    ...         self.number = number
    ...     def __repr__(self):
    ...         return "DB(%s)" % self.number

    >>> class Factory:
    ...     def __init__(self, name, number):
    ...         self.name = name
    ...         self.number = number
    ...     def open(self):
    ...         return DB(self.number)

    >>> s, m = multi_database(
    ...           [Factory(None, 3), Factory('y', 2), Factory('x', 1)])

    >>> list(s)
    [DB(3), DB(2), DB(1)]

    >>> [d.database_name for d in s]
    ['', 'y', 'x']

    >>> [d.databases is m for d in s]
    [True, True, True]

    >>> items = m.items()
    >>> items.sort()
    >>> items
    [('', DB(3)), ('x', DB(1)), ('y', DB(2))]

    Each of the databases is registered as an IDatabase utility:

    >>> from zope import component
    >>> [(component.getUtility(ZODB.interfaces.IDatabase, name) is m[name])
    ...  for name in m]
    [True, True, True]

    """
    databases = {}
    result = []
    for factory in database_factories:
        name = factory.name or ''
        if name in databases:
            raise ValueError("Duplicate database name: %r" % name)
        db = factory.open()
        db.databases = databases
        db.database_name = name
        databases[name] = db
        # Grrr bug in ZODB. Database doesn't declare that it implements
        # IDatabase.
        if not ZODB.interfaces.IDatabase.providedBy(db):
            zope.interface.directlyProvides(db, ZODB.interfaces.IDatabase)
        zope.component.provideUtility(db, ZODB.interfaces.IDatabase, name)
        result.append(db)

    return result, databases


__config_context = None
def getConfigContext():
    return __config_context

__config_source = None
def getConfigSource():
    return __config_source

def reset():
    global _configured
    _configured = False

    global __config_source
    __config_source = None

    global __config_context
    __config_context = None

from zope.testing.cleanup import addCleanUp
addCleanUp(reset)
del addCleanUp
