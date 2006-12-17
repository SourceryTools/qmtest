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
"""UI for browsing database schema managers

$Id: managers.py 39064 2005-10-11 18:40:10Z philikon $
"""
__docformat__ = 'restructuredtext'

import transaction

from zope.app import zapi
from zope.app.generations.interfaces import ISchemaManager
from zope.app.generations.generations import generations_key, Context
from zope.app.i18n import ZopeMessageFactory as _

request_key_format = "evolve-app-%s"

class Managers(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _getdb(self):
        # TODO: There needs to be a better api for this
        return self.request.publication.db

    def evolve(self):
        """Perform a requested evolution

           This method needs to use the component architecture, so
           we'll set it up:

             >>> from zope.app.testing.placelesssetup import setUp, tearDown
             >>> setUp()

           We also need a test request:

             >>> from zope.publisher.browser import TestRequest
             >>> request = TestRequest()

           We also need to give it a publication with a database:

             >>> class Publication(object):
             ...     pass

             >>> request.setPublication(Publication())
             >>> from ZODB.tests.util import DB
             >>> db = DB()
             >>> request.publication.db = db

           We need to define some schema managers.  We'll define two
           using the demo package:

             >>> from zope.app.generations.generations import SchemaManager
             >>> from zope.app.testing import ztapi
             >>> app1 = SchemaManager(0, 1, 'zope.app.generations.demo')
             >>> ztapi.provideUtility(ISchemaManager, app1, 'foo.app1')
             >>> app2 = SchemaManager(0, 0, 'zope.app.generations.demo')
             >>> ztapi.provideUtility(ISchemaManager, app2, 'foo.app2')

           And we need to record some data for them in the database.

             >>> from zope.app.generations.generations import evolve
             >>> evolve(db)

           This sets up the data and actually evolves app1:

             >>> conn = db.open()
             >>> conn.root()[generations_key]['foo.app1']
             1
             >>> conn.root()[generations_key]['foo.app2']
             0

           To evolve a data base schema, the user clicks on a submit
           button. If they click on the button for add1, a item will
           be added to the request, which we simulate:

             >>> request.form['evolve-app-foo.app1'] = 'evolve'

           We'll also increase the generation of app1:

             >>> app1.generation = 2

           Now we can create our view:

             >>> view = Managers(None, request)

           Now, if we call its `evolve` method, it should see that the
           app1 evolve button was pressed and evolve app1 to the next
           generation.

             >>> status = view.evolve()
             >>> conn.sync()
             >>> conn.root()[generations_key]['foo.app1']
             2

           The demo evolver just writes the generation to a database key:

             >>> from zope.app.generations.demo import key
             >>> conn.root()[key]
             ('installed', 'installed', 2)

           Note that, because the demo package has an install script,
           we have entries for that script.
             
           Which the returned status should indicate:

             >>> status['app']
             u'foo.app1'
             >>> status['to']
             2

           Now, given that the database is at the maximum generation
           for app1, we can't evolve it further.  Calling evolve again
           won't evolve anything:

             >>> status = view.evolve()
             >>> conn.sync()
             >>> conn.root()[generations_key]['foo.app1']
             2
             >>> conn.root()[key]
             ('installed', 'installed', 2)
             
           as the status will indicate by returning a 'to' generation
           of 0:

             >>> status['app']
             u'foo.app1'
             >>> status['to']
             0

           If the request doesn't have the key:

             >>> request.form.clear()

           Then calling evolve does nothing:

             >>> view.evolve()
             >>> conn.sync()
             >>> conn.root()[generations_key]['foo.app1']
             2
             >>> conn.root()[key]
             ('installed', 'installed', 2)

           We'd better clean upp:

             >>> db.close()
             >>> tearDown()
           """

        self.managers = managers = dict(
            zapi.getUtilitiesFor(ISchemaManager))
        db = self._getdb()
        conn = db.open()
        try:
            generations = conn.root().get(generations_key, ())
            request = self.request
            for key in generations:
                generation = generations[key]
                rkey = request_key_format % key
                if rkey in request:
                    manager = managers[key]
                    if generation >= manager.generation:
                        return {'app': key, 'to': 0}
                    context = Context()
                    context.connection = conn
                    generation += 1
                    manager.evolve(context, generation)
                    generations[key] = generation
                    transaction.commit()
                    return {'app': key, 'to': generation}

            return None
        finally:
            transaction.abort()
            conn.close()

    def applications(self):
        """Get information about database-generation status

           This method needs to use the component architecture, so
           we'll set it up:

             >>> from zope.app.testing.placelesssetup import setUp, tearDown
             >>> setUp()

           We also need a test request:

             >>> from zope.publisher.browser import TestRequest
             >>> request = TestRequest()

           We also need to give it a publication with a database:

             >>> class Publication(object):
             ...     pass

             >>> request.setPublication(Publication())
             >>> from ZODB.tests.util import DB
             >>> db = DB()
             >>> request.publication.db = db

           We need to define some schema managers.  We'll define two
           using the demo package:

             >>> from zope.app.generations.generations import SchemaManager
             >>> from zope.app.testing import ztapi
             >>> app1 = SchemaManager(0, 1, 'zope.app.generations.demo')
             >>> ztapi.provideUtility(ISchemaManager, app1, 'foo.app1')
             >>> app2 = SchemaManager(0, 0, 'zope.app.generations.demo')
             >>> ztapi.provideUtility(ISchemaManager, app2, 'foo.app2')

           And we need to record some data for them in the database.

             >>> from zope.app.generations.generations import evolve
             >>> evolve(db)

           This sets up the data and actually evolves app1:

             >>> conn = db.open()
             >>> conn.root()[generations_key]['foo.app1']
             1
             >>> conn.root()[generations_key]['foo.app2']
             0

           Now, let's increment app1's generation:

             >>> app1.generation += 1

           so we can evolve it.

           Now we can create our view:

             >>> view = Managers(None, request)

           We call its applications method to get data about
           application generations. We are required to call evolve
           first:

             >>> view.evolve()
             >>> data = list(view.applications())
             >>> data.sort(lambda d1, d2: cmp(d1['id'], d2['id']))

             >>> for info in data:
             ...     print info['id']
             ...     print info['min'], info['max'], info['generation']
             ...     print 'evolve?', info['evolve'] or None
             foo.app1
             0 2 1
             evolve? evolve-app-foo.app1
             foo.app2
             0 0 0
             evolve? None

           We'd better clean up:

             >>> db.close()
             >>> tearDown()

        """
        result = []

        db = self._getdb()
        conn = db.open()
        try:
            managers = self.managers
            generations = conn.root().get(generations_key, ())
            for key in generations:
                generation = generations[key]
                manager = managers.get(key)
                if manager is None:
                    continue

                result.append({
                    'id': key,
                    'min': manager.minimum_generation,
                    'max': manager.generation,
                    'generation': generation,
                    'evolve': (generation < manager.generation
                               and request_key_format % key
                               or ''
                               ),
                    })

            return result
        finally:
            conn.close()
