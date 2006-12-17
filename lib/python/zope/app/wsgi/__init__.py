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
"""A WSGI Application wrapper for zope

$Id: __init__.py 69639 2006-08-18 10:19:40Z philikon $
"""
import os
import sys
import ZConfig
import logging

from zope.event import notify
from zope.interface import implements
from zope.publisher.publish import publish
from zope.publisher.interfaces.http import IHeaderOutput

from zope.app.appsetup import appsetup
from zope.app.publication.httpfactory import HTTPPublicationRequestFactory
from zope.app.wsgi import interfaces


class WSGIPublisherApplication(object):
    """A WSGI application implementation for the zope publisher

    Instances of this class can be used as a WSGI application object.

    The class relies on a properly initialized request factory.
    """
    implements(interfaces.IWSGIApplication)

    def __init__(self, db=None, factory=HTTPPublicationRequestFactory):
        self.requestFactory = None

        if db is not None:
            self.requestFactory = factory(db)

    def __call__(self, environ, start_response):
        """See zope.app.wsgi.interfaces.IWSGIApplication"""
        request = self.requestFactory(environ['wsgi.input'], environ)

        # Let's support post-mortem debugging
        handle_errors = environ.get('wsgi.handleErrors', True)

        request = publish(request, handle_errors=handle_errors)
        response = request.response

        # Start the WSGI server response
        start_response(response.getStatusString(), response.getHeaders())

        # Return the result body iterable.
        return response.consumeBodyIter()


class PMDBWSGIPublisherApplication(WSGIPublisherApplication):

    def __call__(self, environ, start_response):
        environ['wsgi.handleErrors'] = False

        # Call the application to handle the request and write a response
        try:
            app =  super(PMDBWSGIPublisherApplication, self)
            return app.__call__(environ, start_response)
        except Exception, error:
            import sys, pdb
            print "%s:" % sys.exc_info()[0]
            print sys.exc_info()[1]
            #import zope.security.management
            #zope.security.management.restoreInteraction()
            try:
                pdb.post_mortem(sys.exc_info()[2])
                raise
            finally:
                pass #zope.security.management.endInteraction()



def getWSGIApplication(configfile, schemafile=None,
                       features=(),
                       requestFactory=HTTPPublicationRequestFactory):
    # Load the configuration schema
    if schemafile is None:
        schemafile = os.path.join(
            os.path.dirname(appsetup.__file__), 'schema.xml')

    # Let's support both, an opened file and path
    if isinstance(schemafile, basestring):
        schema = ZConfig.loadSchema(schemafile)
    else:
        schema = ZConfig.loadSchemaFile(schemafile)

    # Load the configuration file
    # Let's support both, an opened file and path
    try:
        if isinstance(configfile, basestring):
            options, handlers = ZConfig.loadConfig(schema, configfile)
        else:
            options, handlers = ZConfig.loadConfigFile(schema, configfile)
    except ZConfig.ConfigurationError, msg:
        sys.stderr.write("Error: %s\n" % str(msg))
        sys.exit(2)

    # Insert all specified Python paths
    if options.path:
        sys.path[:0] = [os.path.abspath(p) for p in options.path]

    # Setup the event log
    options.eventlog()

    # Insert the devmode feature, if turned on
    if options.devmode:
        features += ('devmode',)
        logging.warning("Developer mode is enabled: this is a security risk "
            "and should NOT be enabled on production servers. Developer mode "
            "can be turned off in etc/zope.conf")

    # Configure the application
    appsetup.config(options.site_definition, features=features)

    # Connect to and open the database
    db = appsetup.multi_database(options.databases)[0][0]

    # Send out an event that the database has been opened
    notify(appsetup.interfaces.DatabaseOpened(db))

    # Create the WSGI application
    return WSGIPublisherApplication(db, requestFactory)
