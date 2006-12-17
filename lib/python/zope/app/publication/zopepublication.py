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
"""Zope publication

$Id: zopepublication.py 69636 2006-08-18 10:02:46Z faassen $
"""
__docformat__ = 'restructuredtext'

import sys
import logging
from new import instancemethod

from ZODB.POSException import ConflictError
import transaction

from zope.event import notify
from zope.security.interfaces import Unauthorized
from zope.interface import implements, providedBy
from zope.publisher.publish import mapply
from zope.publisher.interfaces import Retry, IExceptionSideEffects, IHeld
from zope.publisher.interfaces import IRequest, IPublication
from zope.security.management import newInteraction, endInteraction
from zope.security.checker import ProxyFactory
from zope.security.proxy import removeSecurityProxy
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.location import LocationProxy

from zope.app import zapi
from zope.app.applicationcontrol.applicationcontrol \
     import applicationControllerRoot
from zope.app.error.interfaces import IErrorReportingUtility
from zope.app.exception.interfaces import ISystemErrorView
from zope.app.publication.interfaces import BeforeTraverseEvent
from zope.app.publication.interfaces import EndRequestEvent
from zope.app.publication.publicationtraverse import PublicationTraverse
from zope.app.security.principalregistry import principalRegistry as prin_reg
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.app.security.interfaces import IAuthentication
from zope.app.component.interfaces import ISite

class Cleanup(object):

    implements(IHeld)

    def __init__(self, f):
        self._f = f

    def release(self):
        self._f()
        self._f = None

    def __del__(self):
        if self._f is not None:
            logging.getLogger('SiteError').error(
                "Cleanup without request close")
            self._f()

class ZopePublication(PublicationTraverse):
    """Base Zope publication specification."""
    implements(IPublication)

    version_cookie = 'Zope-Version'
    root_name = 'Application'

    def __init__(self, db):
        # db is a ZODB.DB.DB object.
        self.db = db

    def beforeTraversal(self, request):
        # Try to authenticate against the default global registry.
        p = prin_reg.authenticate(request)
        if p is None:
            p = prin_reg.unauthenticatedPrincipal()
            if p is None:
                raise Unauthorized # If there's no default principal

        request.setPrincipal(p)
        newInteraction(request)
        transaction.begin()

    def _maybePlacefullyAuthenticate(self, request, ob):
        if not IUnauthenticatedPrincipal.providedBy(request.principal):
            # We've already got an authenticated user. There's nothing to do.
            # Note that beforeTraversal guarentees that user is not None.
            return

        if not ISite.providedBy(ob):
            # We won't find an authentication utility here, so give up.
            return

        sm = removeSecurityProxy(ob).getSiteManager()

        auth = sm.queryUtility(IAuthentication)
        if auth is None:
            # No auth utility here
            return

        # Try to authenticate against the auth utility
        principal = auth.authenticate(request)
        if principal is None:
            principal = auth.unauthenticatedPrincipal()
            if principal is None:
                # nothing to do here
                return

        request.setPrincipal(principal)

    def callTraversalHooks(self, request, ob):
        # Call __before_publishing_traverse__ hooks
        notify(BeforeTraverseEvent(ob, request))
        # This is also a handy place to try and authenticate.
        self._maybePlacefullyAuthenticate(request, ob)

    def afterTraversal(self, request, ob):
        #recordMetaData(object, request)
        self._maybePlacefullyAuthenticate(request, ob)


    def openedConnection(self, conn):
        # Hook for auto-refresh
        pass

    def getApplication(self, request):
        # If the first name is '++etc++process', then we should
        # get it rather than look in the database!
        stack = request.getTraversalStack()

        if '++etc++process' in stack:
            return applicationControllerRoot

        # Open the database.
        version = request.get(self.version_cookie, '')
        conn = self.db.open(version)

        cleanup = Cleanup(conn.close)
        request.hold(cleanup)  # Close the connection on request.close()

        self.openedConnection(conn)
        #conn.setDebugInfo(getattr(request, 'environ', None), request.other)

        root = conn.root()
        app = root.get(self.root_name, None)

        if app is None:
            raise SystemError("Zope Application Not Found")

        return ProxyFactory(app)

    def callObject(self, request, ob):
        return mapply(ob, request.getPositionalArguments(), request)

    def afterCall(self, request, ob):
        txn = transaction.get()
        self.annotateTransaction(txn, request, ob)

        txn.commit()

    def endRequest(self, request, ob):
        endInteraction()
        notify(EndRequestEvent(ob, request))

    def annotateTransaction(self, txn, request, ob):
        """Set some useful meta-information on the transaction. This
        information is used by the undo framework, for example.

        This method is not part of the `IPublication` interface, since
        it's specific to this particular implementation.
        """
        if request.principal is not None:
            txn.setUser(request.principal.id)

        # Work around methods that are usually used for views
        bare = removeSecurityProxy(ob)
        if isinstance(bare, instancemethod):
            ob = bare.im_self

        # set the location path
        path = None
        locatable = IPhysicallyLocatable(ob, None)
        if locatable is not None:
            # Views are made children of their contexts, but that
            # doesn't necessarily mean that we can fully resolve the
            # path. E.g. the family tree of a resource cannot be
            # resolved completely, as the site manager is a dead end.
            try:
                path = locatable.getPath()
            except (AttributeError, TypeError):
                pass
        if path is not None:
            txn.setExtendedInfo('location', path)

        # set the request type
        iface = IRequest
        for iface in providedBy(request):
            if iface.extends(IRequest):
                break
        iface_dotted = iface.__module__ + '.' + iface.getName()
        txn.setExtendedInfo('request_type', iface_dotted)
        return txn

    def _logErrorWithErrorReportingUtility(self, object, request, exc_info):
        # Record the error with the ErrorReportingUtility
        self.beginErrorHandlingTransaction(request, object,
                                           'error reporting utility')
        try:
            errUtility = zapi.getUtility(IErrorReportingUtility)

            # It is important that an error in errUtility.raising
            # does not propagate outside of here. Otherwise, nothing
            # meaningful will be returned to the user.
            #
            # The error reporting utility should not be doing database
            # stuff, so we shouldn't get a conflict error.
            # Even if we do, it is more important that we log this
            # error, and proceed with the normal course of events.
            # We should probably (somehow!) append to the standard
            # error handling that this error occurred while using
            # the ErrorReportingUtility, and that it will be in
            # the zope log.

            errUtility.raising(exc_info, request)
            transaction.commit()
        except:
            tryToLogException(
                'Error while reporting an error to the Error Reporting utility'
                )
            transaction.abort()

    def handleException(self, object, request, exc_info, retry_allowed=True):
        # This transaction had an exception that reached the publisher.
        # It must definitely be aborted.
        transaction.abort()
        
        # Reraise Retry exceptions for the publisher to deal with.
        if retry_allowed and isinstance(exc_info[1], Retry):
            raise

        # Convert ConflictErrors to Retry exceptions.
        if retry_allowed and isinstance(exc_info[1], ConflictError):
            tryToLogWarning('ZopePublication',
                'Competing writes/reads at %s' %
                request.get('PATH_INFO', '???'),
                exc_info=True)
            raise Retry(exc_info)
        # Are there any reasons why we'd want to let application-level error
        # handling determine whether a retry is allowed or not?
        # Assume not for now.

        # Record the error with the ErrorReportingUtility
        self._logErrorWithErrorReportingUtility(object, request, exc_info)

        response = request.response
        response.reset()
        exception = None
        legacy_exception = not isinstance(exc_info[1], Exception)
        if legacy_exception:
            response.handleException(exc_info)
            if isinstance(exc_info[1], str):
                tryToLogWarning(
                    'Publisher received a legacy string exception: %s.'
                    ' This will be handled by the request.' %
                    exc_info[1])
            else:
                tryToLogWarning(
                    'Publisher received a legacy classic class exception: %s.'
                    ' This will be handled by the request.' %
                    exc_info[1].__class__)
        else:
            # We definitely have an Exception
            # Set the request body, and abort the current transaction.
            self.beginErrorHandlingTransaction(
                request, object, 'application error-handling')
            view = None
            try:
                # We need to get a location, because some template content of
                # the exception view might require one.
                #
                # The object might not have a parent, because it might be a
                # method. If we don't have a `__parent__` attribute but have
                # an im_self or a __self__, use it.
                loc = object
                if not hasattr(object, '__parent__'):
                    loc = removeSecurityProxy(object)
                    # Try to get an object, since we apparently have a method
                    # Note: We are guaranteed that an object has a location,
                    # so just getting the instance the method belongs to is
                    # sufficient.
                    loc = getattr(loc, 'im_self', loc)
                    loc = getattr(loc, '__self__', loc)
                    # Protect the location with a security proxy
                    loc = ProxyFactory(loc)

                # Give the exception instance its location and look up the
                # view.
                exception = LocationProxy(exc_info[1], loc, '')
                name = zapi.queryDefaultViewName(exception, request)
                if name is not None:
                    view = zapi.queryMultiAdapter(
                        (exception, request), name=name)
            except:
                # Problem getting a view for this exception. Log an error.
                tryToLogException(
                    'Exception while getting view on exception')


            if view is not None:
                try:
                    # We use mapply instead of self.callObject here
                    # because we don't want to pass positional
                    # arguments.  The positional arguments were meant
                    # for the published object, not an exception view.
                    body = mapply(view, (), request)
                    response.setResult(body)
                    transaction.commit()
                    if (ISystemErrorView.providedBy(view)
                        and view.isSystemError()):
                        # Got a system error, want to log the error

                        # Lame hack to get around logging missfeature
                        # that is fixed in Python 2.4
                        try:
                            raise exc_info[0], exc_info[1], exc_info[2]
                        except:
                            logging.getLogger('SiteError').exception(
                                str(request.URL),
                                )

                except:
                    # Problem rendering the view for this exception.
                    # Log an error.
                    tryToLogException(
                        'Exception while rendering view on exception')

                    # Record the error with the ErrorReportingUtility
                    self._logErrorWithErrorReportingUtility(
                        object, request, sys.exc_info())

                    view = None

            if view is None:
                # Either the view was not found, or view was set to None
                # because the view couldn't be rendered. In either case,
                # we let the request handle it.
                response.handleException(exc_info)
                transaction.abort()

            # See if there's an IExceptionSideEffects adapter for the
            # exception
            try:
                adapter = IExceptionSideEffects(exception, None)
            except:
                tryToLogException(
                    'Exception while getting IExceptionSideEffects adapter')
                adapter = None

            if adapter is not None:
                self.beginErrorHandlingTransaction(
                    request, object, 'application error-handling side-effect')
                try:
                    # Although request is passed in here, it should be
                    # considered read-only.
                    adapter(object, request, exc_info)
                    transaction.commit()
                except:
                    tryToLogException(
                        'Exception while calling'
                        ' IExceptionSideEffects adapter')
                    transaction.abort()

    def beginErrorHandlingTransaction(self, request, ob, note):
        txn = transaction.begin()
        txn.note(note)
        self.annotateTransaction(txn, request, ob)
        return txn

def tryToLogException(arg1, arg2=None):
    if arg2 is None:
        subsystem = 'SiteError'
        message = arg1
    else:
        subsystem = arg1
        message = arg2
    try:
        logging.getLogger(subsystem).exception(message)
    # Bare except, because we want to swallow any exception raised while
    # logging an exception.
    except:
        pass

def tryToLogWarning(arg1, arg2=None, exc_info=False):
    if arg2 is None:
        subsystem = 'SiteError'
        message = arg1
    else:
        subsystem = arg1
        message = arg2
    try:
        logging.getLogger(subsystem).warn(message, exc_info=exc_info)
    # Bare except, because we want to swallow any exception raised while
    # logging a warning.
    except:
        pass
