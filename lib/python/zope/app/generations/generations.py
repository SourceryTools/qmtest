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
"""Experimental support for application database generations

$Id: generations.py 68759 2006-06-19 17:51:24Z ctheune $
"""
__docformat__ = 'restructuredtext'

import sys

from interfaces import GenerationTooHigh, GenerationTooLow, UnableToEvolve
from interfaces import ISchemaManager, IInstallableSchemaManager
import logging
import os
import zope.interface
import transaction

generations_key = 'zope.app.generations'

class SchemaManager(object):
    """Schema manager

       Schema managers implement `IInstallableSchemaManager` using
       scripts provided as module methods.  You create a schema
       manager by providing mimumum and maximum generations and a
       package providing modules named ``evolveN``, where ``N`` is a
       generation number.  Each module provides a function, `evolve`
       that evolves a database from the previous generation.

       For the sake of the example, we'll use the demo package defined
       in here. See the modules there for simple examples of evolution
       scripts.

       So, if we'll create a SchemaManager:

         >>> manager = SchemaManager(1, 3, 'zope.app.generations.demo')

       and we'll create a test database and context:

         >>> from ZODB.tests.util import DB
         >>> db = DB()
         >>> context = Context()
         >>> context.connection = db.open()

       Then we'll evolve the database from generation 1 to 3:

         >>> manager.evolve(context, 2)
         >>> manager.evolve(context, 3)
         >>> transaction.commit()

       The demo evolvers simply record their data in a root key:

         >>> from zope.app.generations.demo import key
         >>> conn = db.open()
         >>> conn.root()[key]
         (2, 3)

       You can get the information for each evolver by specifying the
       destination generation of the evolver as argument to the `getInfo()`
       method:

         >>> manager.getInfo(1)
         'Evolver 1'
         >>> manager.getInfo(2)
         'Evolver 2'
         >>> manager.getInfo(3) is None
         True

       If a package provides an install script, then it will be called
       when the manager's intall method is called:

         >>> conn.sync()
         >>> del conn.root()[key]
         >>> transaction.commit()
         >>> conn.root().get(key)

         >>> manager.install(context)
         >>> transaction.commit()
         >>> conn.sync()
         >>> conn.root()[key]
         ('installed',)

       If there is not install script, the manager will do nothing on
       an install:

         >>> manager = SchemaManager(1, 3, 'zope.app.generations.demo2')
         >>> manager.install(context)

       We handle ImportErrors within the script specially, so they get promoted:

         >>> manager = SchemaManager(1, 3, 'zope.app.generations.demo3')
         >>> manager.install(context)
         Traceback (most recent call last):
         ImportError: No module named nonexistingmodule

       We'd better clean up:

         >>> context.connection.close()
         >>> conn.close()
         >>> db.close()


       """

    zope.interface.implements(IInstallableSchemaManager)

    def __init__(self, minimum_generation=0, generation=0, package_name=None):
        if generation < minimum_generation:
            raise ValueError("generation is less than minimum_generation",
                             generation, minimum_generation)
        if minimum_generation < 0:
            raise ValueError("generations must be non-negative",
                             minimum_generation)

        if generation and not package_name:
            raise ValueError("A package name must be supplied if the"
                             " generation is non-zero")

        self.minimum_generation = minimum_generation
        self.generation = generation
        self.package_name = package_name

    def evolve(self, context, generation):
        """Evolve a database to reflect software/schema changes
        """
        name = "%s.evolve%d" % (self.package_name, generation)

        evolver = __import__(name, {}, {}, ['*'])

        evolver.evolve(context)

    def install(self, context):
        """Evolve a database to reflect software/schema changes
        """
        name = "%s.install" % self.package_name

        try:
            evolver = __import__(name, {}, {}, ['*'])
        except ImportError, m:
            if str(m) not in ('No module named %s' % name,
                              'No module named install'):
                # This was an import error *within* the module, so we re-raise.
                raise
        else:
            evolver.evolve(context)

    def getInfo(self, generation):
        """Get the information from the evolver function's doc string."""
        evolver = __import__(
            "%s.evolve%d" % (self.package_name, generation),
            {}, {}, ['*'])
        return evolver.evolve.__doc__



class Context(object):
    pass

def findManagers():
    # Hook to let Chris use this for Zope 2
    import zope.app
    return zope.app.zapi.getUtilitiesFor(ISchemaManager)

def PersistentDict():
    # Another hook to let Chris use this for Zope 2
    import persistent.dict
    return persistent.dict.PersistentDict()

EVOLVE, EVOLVENOT, EVOLVEMINIMUM = 0, 1, 2

def evolve(db, how=EVOLVE):
    """Evolve a database

    We evolve a database using registered application schema managers.
    Here's an example (silly) schema manager:

      >>> from zope.app.generations.interfaces import ISchemaManager
      >>> class FauxApp(object):
      ...     zope.interface.implements(ISchemaManager)
      ...
      ...     erron = None # Raise an error is asked to evolve to this
      ...
      ...     def __init__(self, name, minimum_generation, generation):
      ...         self.name, self.generation = name, generation
      ...         self.minimum_generation = minimum_generation
      ...
      ...     def evolve(self, context, generation):
      ...         if generation == self.erron:
      ...             raise ValueError(generation)
      ...
      ...         context.connection.root()[self.name] = generation

    We also need to set up the component system, since we'll be
    registering utilities:

      >>> from zope.app.testing.placelesssetup import setUp, tearDown
      >>> setUp()

    Now, we'll create and register some handlers:

      >>> from zope.app.testing import ztapi
      >>> app1 = FauxApp('app1', 0, 1)
      >>> ztapi.provideUtility(ISchemaManager, app1, name='app1')
      >>> app2 = FauxApp('app2', 5, 11)
      >>> ztapi.provideUtility(ISchemaManager, app2, name='app2')

    If we create a new database, and evolve it, we'll simply update
    the generation data:

      >>> from ZODB.tests.util import DB
      >>> db = DB()
      >>> conn = db.open()
      >>> root = conn.root()
      >>> evolve(db)
      >>> conn.sync()
      >>> root[generations_key]['app1']
      1
      >>> root[generations_key]['app2']
      11

    But nothing will have been done to the database:

      >>> root.get('app1')
      >>> root.get('app2')

    Now if we increase the generation of one of the apps:

      >>> app1.generation += 1
      >>> evolve(db)

    We'll see that the generation data has updated:

      >>> conn.sync()
      >>> root[generations_key]['app1']
      2
      >>> root[generations_key]['app2']
      11

    And that the database was updated for that application:

      >>> root.get('app1')
      2
      >>> root.get('app2')

    If there is an error updating a particular generation, but the
    generation is greater than the minimum generation, then we won't
    get an error from evolve, but we will get a log message.

      >>> from zope.testing import loggingsupport
      >>> handler = loggingsupport.InstalledHandler('zope.app.generations')

      >>> app1.erron = 4
      >>> app1.generation = 7
      >>> evolve(db)

      >>> print handler
      zope.app.generations ERROR
        Failed to evolve database to generation 4 for app1

    The database will have been updated for previous generations:

      >>> conn.sync()
      >>> root[generations_key]['app1']
      3
      >>> root.get('app1')
      3

    If we set the minimum generation for app1 to something greater than 3:

      >>> app1.minimum_generation = 5

    Then we'll get an error if we try to evolve, since we can't get
    past 3 and 3 is less than 5:

      >>> evolve(db)
      Traceback (most recent call last):
      ...
      UnableToEvolve: (4, u'app1', 7)

    We'll also get a log entry:

      >>> print handler
      zope.app.generations ERROR
        Failed to evolve database to generation 4 for app1
      zope.app.generations ERROR
        Failed to evolve database to generation 4 for app1

    So far, we've used evolve in its default policy, in which we evolve
    as far as we can up to the current generation.  There are two
    other policies:

    EVOLVENOT -- Don't evolve, but make sure that the application is
      at the minimum generation

    EVOLVEMINIMUM -- Evolve only to the minimum generation

    Let's change unset erron for app1 so we don't get an error when we
    try to evolve.

      >>> app1.erron = None

    Now, we'll call evolve with EVOLVENOT:

      >>> evolve(db, EVOLVENOT)
      Traceback (most recent call last):
      ...
      GenerationTooLow: (3, u'app1', 5)

    We got an error because we aren't at the minimum generation for
    app1.  The database generation for app1 is still 3 because we
    didn't do any evolution:

      >>> conn.sync()
      >>> root[generations_key]['app1']
      3
      >>> root.get('app1')
      3

    Now, if we use EVOLVEMINIMUM instead, we'll evolve to the minimum
    generation:

      >>> evolve(db, EVOLVEMINIMUM)
      >>> conn.sync()
      >>> root[generations_key]['app1']
      5
      >>> root.get('app1')
      5

    If we happen to install an app that has a generation that is less
    that the database generation, we'll get an error, because there is
    no way to get the database to a generation that the app
    understands:

      >>> app1.generation = 2
      >>> app1.minimum_generation = 0
      >>> evolve(db)
      Traceback (most recent call last):
      ...
      GenerationTooHigh: (5, u'app1', 2)

    We'd better clean up:

      >>> handler.uninstall()
      >>> conn.close()
      >>> db.close()
      >>> tearDown()

    """
    conn = db.open()
    try:
        context = Context()
        context.connection = conn
        root = conn.root()
        generations = root.get(generations_key)
        if generations is None:
            generations = root[generations_key] = PersistentDict()
            transaction.commit()

        for key, manager in findManagers():
            generation = generations.get(key)

            if generation == manager.generation:
                continue

            if generation is None:
                # This is a new database, so no old data

                if IInstallableSchemaManager.providedBy(manager):
                    try:
                        manager.install(context)
                    except:
                        transaction.abort()
                        logging.getLogger('zope.app.generations').exception(
                            "Failed to install %s",
                            key)
                        raise
                        
                generations[key] = manager.generation
                transaction.commit()
                continue

            if generation > manager.generation:
                raise GenerationTooHigh(generation, key, manager.generation)

            if generation < manager.minimum_generation:
                if how == EVOLVENOT:
                    raise GenerationTooLow(
                        generation, key, manager.minimum_generation)
            else:
                if how != EVOLVE:
                    continue

            if how == EVOLVEMINIMUM:
                target = manager.minimum_generation
            else:
                target = manager.generation

            while generation < target:
                generation += 1
                try:
                    transaction.begin()
                    manager.evolve(context, generation)
                    generations[key] = generation
                    transaction.commit()
                except:
                    # An unguarded handler is intended here
                    transaction.abort()
                    logging.getLogger('zope.app.generations').exception(
                        "Failed to evolve database to generation %d for %s",
                        generation, key)

                    if generation < manager.minimum_generation:
                        raise UnableToEvolve(generation, key,
                                             manager.generation)
                    break
    finally:
        conn.close()



def evolveSubscriber(event):
    evolve(event.database, EVOLVE)

def evolveNotSubscriber(event):
    evolve(event.database, EVOLVENOT)

def evolveMinimumSubscriber(event):
    evolve(event.database, EVOLVEMINIMUM)

