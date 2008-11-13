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
"""Base implementations of the Publisher objects

Specifically, 'BaseRequest', 'BaseResponse', and 'DefaultPublication' are
specified here.

$Id: base.py 82179 2007-12-07 15:03:15Z ctheune $
"""
from cStringIO import StringIO

from zope.deprecation import deprecated

from zope.interface import implements, providedBy
from zope.interface.common.mapping import IReadMapping, IEnumerableMapping
from zope.exceptions.exceptionformatter import print_exception

from zope.publisher.interfaces import IPublication, IHeld
from zope.publisher.interfaces import NotFound, DebugError, Unauthorized
from zope.publisher.interfaces import IRequest, IResponse, IDebugFlags
from zope.publisher.publish import mapply

_marker = object()

class BaseResponse(object):
    """Base Response Class
    """

    __slots__ = (
        '_result',    # The result of the application call
        '_request',   # The associated request (if any)
        )

    implements(IResponse)

    def __init__(self):
        self._request = None

    def setResult(self, result):
        'See IPublisherResponse'
        self._result = result

    def handleException(self, exc_info):
        'See IPublisherResponse'
        f = StringIO()
        print_exception(
            exc_info[0], exc_info[1], exc_info[2], 100, f)
        self.setResult(f.getvalue())

    def internalError(self):
        'See IPublisherResponse'
        pass

    def reset(self):
        'See IPublisherResponse'
        pass

    def retry(self):
        'See IPublisherResponse'
        return self.__class__()

class RequestDataGetter(object):

    implements(IReadMapping)

    def __init__(self, request):
        self.__get = getattr(request, self._gettrname)

    def __getitem__(self, name):
        return self.__get(name)

    def get(self, name, default=None):
        return self.__get(name, default)

    def __contains__(self, key):
        lookup = self.get(key, self)
        return lookup is not self

    has_key = __contains__

class RequestDataMapper(object):

    implements(IEnumerableMapping)

    def __init__(self, request):
        self.__map = getattr(request, self._mapname)

    def __getitem__(self, name):
        return self.__map[name]

    def get(self, name, default=None):
        return self.__map.get(name, default)

    def __contains__(self, key):
        lookup = self.get(key, self)
        return lookup is not self

    has_key = __contains__

    def keys(self):
        return self.__map.keys()

    def __iter__(self):
        return iter(self.keys())

    def items(self):
        return self.__map.items()

    def values(self):
        return self.__map.values()

    def __len__(self):
        return len(self.__map)

class RequestDataProperty(object):

    def __init__(self, gettr_class):
        self.__gettr_class = gettr_class

    def __get__(self, request, rclass=None):
        if request is not None:
            return self.__gettr_class(request)

    def __set__(*args):
        raise AttributeError('Unassignable attribute')


class RequestEnvironment(RequestDataMapper):
    _mapname = '_environ'


class DebugFlags(object):
    """Debugging flags."""

    implements(IDebugFlags)

    sourceAnnotations = False
    showTAL = False


class BaseRequest(object):
    """Represents a publishing request.

    This object provides access to request data. Request data may
    vary depending on the protocol used.

    Request objects are created by the object publisher and will be
    passed to published objects through the argument name, REQUEST.

    The request object is a mapping object that represents a
    collection of variable to value mappings.
    """

    implements(IRequest)

    __slots__ = (
        '__provides__',      # Allow request to directly provide interfaces
        '_held',             # Objects held until the request is closed
        '_traversed_names',  # The names that have been traversed
        '_last_obj_traversed', # Object that was traversed last
        '_traversal_stack',  # Names to be traversed, in reverse order
        '_environ',          # The request environment variables
        '_response',         # The response
        '_args',             # positional arguments
        '_body_instream',    # input stream
        '_body',             # The request body as a string
        '_publication',      # publication object
        '_principal',        # request principal, set by publication
        'interaction',       # interaction, set by interaction
        'debug',             # debug flags
        'annotations',       # per-package annotations
        )

    environment = RequestDataProperty(RequestEnvironment)

    def __init__(self, body_instream, environ, response=None,
                 positional=None):
        self._traversal_stack = []
        self._last_obj_traversed = None
        self._traversed_names = []
        self._environ = environ

        self._args = positional or ()

        if response is None:
            self._response = self._createResponse()
        else:
            self._response = response

        self._response._request = self

        self._body_instream = body_instream
        self._held = ()
        self._principal = None
        self.debug = DebugFlags()
        self.interaction = None
        self.annotations = {}

    def setPrincipal(self, principal):
        self._principal = principal

    principal = property(lambda self: self._principal)

    def _getPublication(self):
        'See IPublisherRequest'
        return getattr(self, '_publication', None)

    publication = property(_getPublication)

    def processInputs(self):
        'See IPublisherRequest'
        # Nothing to do here

    def retry(self):
        'See IPublisherRequest'
        raise TypeError('Retry is not supported')

    def setPublication(self, pub):
        'See IPublisherRequest'
        self._publication = pub

    def supportsRetry(self):
        'See IPublisherRequest'
        return 0

    def traverse(self, obj):
        'See IPublisherRequest'

        publication = self.publication

        traversal_stack = self._traversal_stack
        traversed_names = self._traversed_names

        prev_object = None
        while True:

            self._last_obj_traversed = obj

            if obj is not prev_object:
                # Invoke hooks (but not more than once).
                publication.callTraversalHooks(self, obj)

            if not traversal_stack:
                # Finished traversal.
                break

            prev_object = obj

            # Traverse to the next step.
            entry_name = traversal_stack.pop()
            traversed_names.append(entry_name)
            obj = publication.traverseName(self, obj, entry_name)

        return obj

    def close(self):
        'See IPublicationRequest'

        for held in self._held:
            if IHeld.providedBy(held):
                held.release()

        self._held = None
        self._body_instream = None
        self._publication = None

    def getPositionalArguments(self):
        'See IPublicationRequest'
        return self._args

    def _getResponse(self):
        return self._response

    response = property(_getResponse)

    def getTraversalStack(self):
        'See IPublicationRequest'
        return list(self._traversal_stack) # Return a copy

    def hold(self, object):
        'See IPublicationRequest'
        self._held = self._held + (object,)

    def setTraversalStack(self, stack):
        'See IPublicationRequest'
        self._traversal_stack[:] = list(stack)

    def _getBodyStream(self):
        'See zope.publisher.interfaces.IApplicationRequest'
        return self._body_instream

    bodyStream = property(_getBodyStream)

    def __len__(self):
        'See Interface.Common.Mapping.IEnumerableMapping'
        return len(self.keys())

    def items(self):
        'See Interface.Common.Mapping.IEnumerableMapping'
        result = []
        get = self.get
        for k in self.keys():
            result.append((k, get(k)))
        return result

    def keys(self):
        'See Interface.Common.Mapping.IEnumerableMapping'
        return self._environ.keys()

    def __iter__(self):
        return iter(self.keys())

    def values(self):
        'See Interface.Common.Mapping.IEnumerableMapping'
        result = []
        get = self.get
        for k in self.keys():
            result.append(get(k))
        return result

    def __getitem__(self, key):
        'See Interface.Common.Mapping.IReadMapping'
        result = self.get(key, _marker)
        if result is _marker:
            raise KeyError(key)
        else:
            return result

    def get(self, key, default=None):
        'See Interface.Common.Mapping.IReadMapping'
        result = self._environ.get(key, _marker)
        if result is not _marker:
            return result

        return default

    def __contains__(self, key):
        'See Interface.Common.Mapping.IReadMapping'
        lookup = self.get(key, self)
        return lookup is not self

    has_key = __contains__

    def _createResponse(self):
        # Should be overridden by subclasses
        return BaseResponse()

    def __nonzero__(self):
        # This is here to avoid calling __len__ for boolean tests
        return 1

    def __str__(self):
        L1 = self.items()
        L1.sort()
        return "\n".join(map(lambda item: "%s:\t%s" % item, L1))

    def _setupPath_helper(self, attr):
        path = self.get(attr, "/")
        if path.endswith('/'):
            # Remove trailing backslash, so that we will not get an empty
            # last entry when splitting the path.
            path = path[:-1]
            self._endswithslash = True
        else:
            self._endswithslash = False

        clean = []
        for item in path.split('/'):
            if not item or item == '.':
                continue
            elif item == '..':
                try:
                    del clean[-1]
                except IndexError:
                    raise NotFound('..')
            else: clean.append(item)

        clean.reverse()
        self.setTraversalStack(clean)

        self._path_suffix = None

class TestRequest(BaseRequest):

    __slots__ = ('_presentation_type', )

    def __init__(self, path, body_instream=None, environ=None):

        if environ is None:
            environ = {}

        environ['PATH_INFO'] = path
        if body_instream is None:
            body_instream = StringIO('')

        super(TestRequest, self).__init__(body_instream, environ)

class DefaultPublication(object):
    """A stub publication.

    This works just like Zope2's ZPublisher. It rejects any name
    starting with an underscore and any objects (specifically: method)
    that doesn't have a docstring.
    """
    implements(IPublication)

    require_docstrings = True

    def __init__(self, app):
        self.app = app

    def beforeTraversal(self, request):
        # Lop off leading and trailing empty names
        stack = request.getTraversalStack()
        while stack and not stack[-1]:
            stack.pop() # toss a trailing empty name
        while stack and not stack[0]:
            stack.pop(0) # toss a leading empty name
        request.setTraversalStack(stack)

    def getApplication(self, request):
        return self.app

    def callTraversalHooks(self, request, ob):
        pass

    def traverseName(self, request, ob, name, check_auth=1):
        if name.startswith('_'):
            raise Unauthorized(name)
        if hasattr(ob, name):
            subob = getattr(ob, name)
        else:
            try:
                subob = ob[name]
            except (KeyError, IndexError,
                    TypeError, AttributeError):
                raise NotFound(ob, name, request)
        if self.require_docstrings and not getattr(subob, '__doc__', None):
            raise DebugError(subob, 'Missing or empty doc string')
        return subob

    def getDefaultTraversal(self, request, ob):
        return ob, ()

    def afterTraversal(self, request, ob):
        pass

    def callObject(self, request, ob):
        return mapply(ob, request.getPositionalArguments(), request)

    def afterCall(self, request, ob):
        pass

    def endRequest(self, request, ob):
        pass

    def handleException(self, object, request, exc_info, retry_allowed=1):
        # Let the response handle it as best it can.
        request.response.reset()
        request.response.handleException(exc_info)


class TestPublication(DefaultPublication):

    def traverseName(self, request, ob, name, check_auth=1):
        if hasattr(ob, name):
            subob = getattr(ob, name)
        else:
            try:
                subob = ob[name]
            except (KeyError, IndexError,
                    TypeError, AttributeError):
                raise NotFound(ob, name, request)
        return subob
