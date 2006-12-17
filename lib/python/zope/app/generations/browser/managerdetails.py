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
"""Manager Details View

$Id$
"""
__docformat__ = "reStructuredText"
from zope.app import zapi
from zope.app.generations.interfaces import ISchemaManager
from zope.app.renderer.rest import ReStructuredTextToHTMLRenderer

class ManagerDetails(object):
    r"""Show Details of a particular Schema Manager's Evolvers

    This method needs to use the component architecture, so
    we'll set it up:
    
      >>> from zope.app.testing.placelesssetup import setUp, tearDown
      >>> setUp()
    
    We need to define some schema managers.  We'll define just one:
    
      >>> from zope.app.generations.generations import SchemaManager
      >>> from zope.app.testing import ztapi
      >>> app1 = SchemaManager(0, 3, 'zope.app.generations.demo')
      >>> ztapi.provideUtility(ISchemaManager, app1, 'foo.app1')

    Now let's create the view:

      >>> from zope.publisher.browser import TestRequest
      >>> details = ManagerDetails()
      >>> details.context = None
      >>> details.request = TestRequest(environ={'id': 'foo.app1'})

    Let's now see that the view gets the ID correctly from the request:

      >>> details.id
      'foo.app1'

    Now check that we get all the info from the evolvers:

      >>> info = details.getEvolvers()
      >>> import pprint
      >>> pp = pprint.PrettyPrinter(width=76)
      >>> pp.pprint(info)
      [{'info': u'<p>Evolver 1</p>\n', 'to': 1, 'from': 0},
       {'info': u'<p>Evolver 2</p>\n', 'to': 2, 'from': 1},
       {'info': '', 'to': 3, 'from': 2}]

    We'd better clean up:

      >>> tearDown()
    """

    id = property(lambda self: self.request['id'])

    def getEvolvers(self):
        id = self.id
        manager = zapi.getUtility(ISchemaManager, id)

        evolvers = []

        for gen in range(manager.minimum_generation, manager.generation):

            info = manager.getInfo(gen+1)
            if info is None:
                info = ''
            else:
                # XXX: the renderer *expects* unicode as input encoding (ajung)
                renderer = ReStructuredTextToHTMLRenderer(
                    unicode(info), self.request)
                info = renderer.render()
                
            evolvers.append({'from': gen, 'to': gen+1, 'info': info})

        return evolvers
