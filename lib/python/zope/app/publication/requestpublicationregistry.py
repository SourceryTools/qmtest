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
"""A registry for Request-Publication factories.

$Id: publicationfactories.py 38841 2005-10-07 04:34:09Z andreasjung $
"""
__docformat__ = 'restructuredtext'

import sets
from zope.interface import implements
from zope.app.publication.interfaces import IRequestPublicationRegistry
from zope.configuration.exceptions import ConfigurationError

class RequestPublicationRegistry(object):
    """The registry implements a three stage lookup for registred factories
    that have to deal with requests::

      {method > { mimetype -> [{'priority' : some_int,
                                 'factory' :  factory,
                                 'name' : some_name }, ...
                                ]
                  },
      }

    The `priority` is used to define a lookup-order when multiple factories
    are registered for the same method and mime-type.
    """
    implements(IRequestPublicationRegistry)

    def __init__(self):
        self._d = {}   # method -> { mimetype -> {factories_data}}

    def register(self, method, mimetype, name, priority, factory):
        """Register a factory for method+mimetype """

        # initialize the two-level deep nested datastructure if necessary
        if not self._d.has_key(method):
            self._d[method] = {}
        if not self._d[method].has_key(mimetype):
            self._d[method][mimetype] = []
        l = self._d[method][mimetype]

        # Check if there is already a registered publisher factory (check by
        # name).  If yes then it will be removed and replaced by a new
        # publisher.
        for pos, d in enumerate(l):
            if d['name'] == name:
                del l[pos]
                break
        # add the publisher factory + additional informations
        l.append({'name' : name, 'factory' : factory, 'priority' : priority})

        # order by descending priority
        l.sort(lambda x,y: -cmp(x['priority'], y['priority']))

        # check if the priorities are unique
        priorities = [item['priority'] for item in l]
        if len(sets.Set(priorities)) != len(l):
            raise ConfigurationError('All registered publishers for a given '
                                     'method+mimetype must have distinct '
                                     'priorities. Please check your ZCML '
                                     'configuration')


    def getFactoriesFor(self, method, mimetype):

        if ';' in mimetype:
            # `mimetype` might be something like 'text/xml; charset=utf8'. In
            # this case we are only interested in the first part.
            mimetype = mimetype.split(';')[0]

        try:
            return self._d[method][mimetype.strip()]
        except KeyError:
            return None


    def lookup(self, method, mimetype, environment):
        """Lookup a factory for a given method+mimetype and a environment."""

        for m,mt in ((method, mimetype), (method, '*'), ('*', '*')):
            factory_lst = self.getFactoriesFor(m, mt)
            if factory_lst:
                break
        else:
            raise ConfigurationError('No registered publisher found '
                                     'for (%s/%s)' % (method, mimetype))

        # now iterate over all factory candidates and let them introspect
        # the request environment to figure out if they can handle the
        # request
        for d in factory_lst:
            factory = d['factory']
            if factory.canHandle(environment):
                return factory

        # Actually we should never get here unless of improper
        # configuration (no default handler for method=* and mimetype=*)
        return None


factoryRegistry = RequestPublicationRegistry()

from zope.testing import cleanup
cleanup.addCleanUp(lambda : factoryRegistry.__init__())
