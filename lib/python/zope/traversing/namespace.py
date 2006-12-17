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
"""URL Namespace Implementations

$Id: namespace.py 68737 2006-06-18 22:49:03Z ctheune $
"""
import re

import zope.component
import zope.interface
from zope.i18n.interfaces import IModifiableUserPreferredLanguages
from zope.component.interfaces import ComponentLookupError
from zope.interface import providedBy, directlyProvides, directlyProvidedBy
from zope.publisher.interfaces.browser import IBrowserSkinType
from zope.publisher.browser import applySkin
from zope.security.proxy import removeSecurityProxy
from zope.traversing.interfaces import ITraversable, IPathAdapter
from zope.traversing.interfaces import TraversalError, IContainmentRoot

class UnexpectedParameters(TraversalError):
    "Unexpected namespace parameters were provided."

class ExcessiveDepth(TraversalError):
    "Too many levels of containment. We don't believe them."

def namespaceLookup(ns, name, object, request=None):
    """Lookup a value from a namespace

    We look up a value using a view or an adapter, depending on
    whether a request is passed.

    Let's start with adapter-based transersal:

      >>> class I(zope.interface.Interface):
      ...     'Test interface'
      >>> class C(object):
      ...     zope.interface.implements(I)

    We'll register a simple testing adapter:

      >>> class Adapter(object):
      ...     def __init__(self, context):
      ...         self.context = context
      ...     def traverse(self, name, remaining):
      ...         return name+'42'

      >>> zope.component.provideAdapter(Adapter, (I,), ITraversable, 'foo')

    Then given an object, we can traverse it with a
    namespace-qualified name:

      >>> namespaceLookup('foo', 'bar', C())
      'bar42'

    If we give an invalid namespace, we'll get a not found error:

      >>> namespaceLookup('fiz', 'bar', C())    # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ...
      TraversalError: (<zope.traversing.namespace.C object at 0x...>, '++fiz++bar')

    We'll get the same thing if we provide a request:

      >>> from zope.publisher.browser import TestRequest
      >>> request = TestRequest()
      >>> namespaceLookup('foo', 'bar', C(), request)    # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ...
      TraversalError: (<zope.traversing.namespace.C object at 0x...>, '++foo++bar')

    We need to provide a view:

      >>> class View(object):
      ...     def __init__(self, context, request):
      ...         pass
      ...     def traverse(self, name, remaining):
      ...         return name+'fromview'
      >>> from zope.traversing.testing import browserView
      >>> browserView(I, 'foo', View, providing=ITraversable)

      >>> namespaceLookup('foo', 'bar', C(), request)
      'barfromview'

    Clean up:

      >>> from zope.testing.cleanup import cleanUp
      >>> cleanUp()
    """
    if request is not None:
        traverser = zope.component.queryMultiAdapter((object, request),
                                                     ITraversable, ns)
    else:
        traverser = zope.component.queryAdapter(object, ITraversable, ns)

    if traverser is None:
        raise TraversalError(object, "++%s++%s" % (ns, name))

    return traverser.traverse(name, ())


namespace_pattern = re.compile('[+][+]([a-zA-Z0-9_]+)[+][+]')

def nsParse(name):
    """Parse a namespace-qualified name into a namespace name and a
    name.  Returns the namespace name and a name.

    A namespace-qualified name is usually of the form ++ns++name, as in:

      >>> nsParse('++acquire++foo')
      ('acquire', 'foo')

    The part inside the +s must be an identifier, so:

      >>> nsParse('++hello world++foo')
      ('', '++hello world++foo')
      >>> nsParse('+++acquire+++foo')
      ('', '+++acquire+++foo')

    But it may also be a @@foo, which implies the view namespace:

      >>> nsParse('@@foo')
      ('view', 'foo')

      >>> nsParse('@@@foo')
      ('view', '@foo')

      >>> nsParse('@foo')
      ('', '@foo')

    """
    ns = ''
    if name.startswith('@@'):
        ns = 'view'
        name = name[2:]
    else:
        match = namespace_pattern.match(name)
        if match:
            prefix, ns = match.group(0, 1)
            name = name[len(prefix):]

    return ns, name

def getResource(site, name, request):
    resource = queryResource(site, name, request)
    if resource is None:
        raise TraversalError(site, name)
    return resource

def queryResource(site, name, request, default=None):
    resource = zope.component.queryAdapter(request, name=name)
    if resource is None:
        return default

    # We need to set the __parent__ and __name__.  We need the unproxied
    # resource to do this.  We still return the proxied resource.
    r = removeSecurityProxy(resource)

    r.__parent__ = site
    r.__name__ = name

    return resource

# ---- namespace processors below ----

class SimpleHandler(object):

    zope.interface.implements(ITraversable)

    def __init__(self, context, request=None):
        """Simple handlers can be used as adapters or views

        They ignore their second constructor arg and store the first
        one in their context attr:

          >>> SimpleHandler(42).context
          42

          >>> SimpleHandler(42, 43).context
          42
        """
        self.context = context

class acquire(SimpleHandler):
    """Traversal adapter for the acquire namespace
    """

    def traverse(self, name, remaining):
        """Acquire a name

        Let's set up some example data:

          >>> class testcontent(object):
          ...     zope.interface.implements(ITraversable)
          ...     def traverse(self, name, remaining):
          ...         v = getattr(self, name, None)
          ...         if v is None:
          ...             raise TraversalError(self, name)
          ...         return v
          ...     def __repr__(self):
          ...         return 'splat'

          >>> ob = testcontent()
          >>> ob.a = 1
          >>> ob.__parent__ = testcontent()
          >>> ob.__parent__.b = 2
          >>> ob.__parent__.__parent__ = testcontent()
          >>> ob.__parent__.__parent__.c = 3

        And acquire some names:

          >>> adapter = acquire(ob)

          >>> adapter.traverse('a', ())
          1

          >>> adapter.traverse('b', ())
          2

          >>> adapter.traverse('c', ())
          3

          >>> adapter.traverse('d', ())
          Traceback (most recent call last):
          ...
          TraversalError: (splat, 'd')
        """
        i = 0
        ob = self.context
        while i < 200:
            i += 1
            traversable = ITraversable(ob, None)
            if traversable is not None:
                try:
                    # ??? what do we do if the path gets bigger?
                    path = []
                    next = traversable.traverse(name, path)
                    if path:
                        continue
                except TraversalError:
                    pass

                else:
                    return next

            ob = getattr(ob, '__parent__', None)
            if ob is None:
                raise TraversalError(self.context, name)

        raise ExcessiveDepth(self.context, name)

class attr(SimpleHandler):

    def traverse(self, name, ignored):
        """Attribute traversal adapter

        This adapter just provides traversal to attributes:

          >>> ob = {'x': 1}
          >>> adapter = attr(ob)
          >>> adapter.traverse('keys', ())()
          ['x']

        """
        return getattr(self.context, name)

class item(SimpleHandler):

    def traverse(self, name, ignored):
        """Item traversal adapter

           This adapter just provides traversal to items:

              >>> ob = {'x': 42}
              >>> adapter = item(ob)
              >>> adapter.traverse('x', ())
              42
           """
        return self.context[name]

class etc(SimpleHandler):

    def traverse(self, name, ignored):
        # TODO:
        # This is here now to allow us to get site managers from a
        # separate namespace from the content. We add and etc
        # namespace to allow us to handle misc objects.  We'll apply
        # YAGNI for now and hard code this. We'll want something more
        # general later. We were thinking of just calling "get"
        # methods, but this is probably too magic. In particular, we
        # will treat returned objects as sub-objects wrt security and
        # not all get methods may satisfy this assumption. It might be
        # best to introduce some sort of etc registry.

        ob = self.context

        # TODO: lift dependency on zope.app
        if (name in ('process', 'ApplicationController')
            and IContainmentRoot.providedBy(ob)):
            # import the application controller here to avoid circular
            # import problems
            from zope.app.applicationcontrol.applicationcontrol \
                 import applicationController
            return applicationController

        if name not in ('site',):
            raise TraversalError(ob, name)

        method_name = "getSiteManager"
        method = getattr(ob, method_name, None)
        if method is None:
            raise TraversalError(ob, name)

        try:
            return method()
        except ComponentLookupError:
            raise TraversalError(ob, name)


class view(object):

    zope.interface.implements(ITraversable)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def traverse(self, name, ignored):
        view = zope.component.queryMultiAdapter((self.context, self.request),
                                                name=name)
        if view is None:
            raise TraversalError(self.context, name)

        return view

class resource(view):

    def traverse(self, name, ignored):
        # The context is important here, since it becomes the parent of the
        # resource, which is needed to generate the absolute URL.
        return getResource(self.context, name, self.request)

class lang(view):

    def traverse(self, name, ignored):
        self.request.shiftNameToApplication()
        languages = IModifiableUserPreferredLanguages(self.request)
        languages.setPreferredLanguages([name])
        return self.context

class skin(view):

    def traverse(self, name, ignored):
        self.request.shiftNameToApplication()
        try:
            skin = zope.component.getUtility(IBrowserSkinType, name)
        except ComponentLookupError:
            raise TraversalError("++skin++%s" % name)
        applySkin(self.request, skin)
        return self.context

class vh(view):

    def traverse(self, name, ignored):

        request = self.request

        traversal_stack = request.getTraversalStack()
        app_names = []

        if name:
            try:
                proto, host, port = name.split(":")
            except ValueError:
                raise ValueError("Vhost directive should have the form "
                                 "++vh++protocol:host:port")

            request.setApplicationServer(host, proto, port)

        if '++' in traversal_stack:
            segment = traversal_stack.pop()
            while segment != '++':
                app_names.append(segment)
                segment = traversal_stack.pop()
            request.setTraversalStack(traversal_stack)
        else:
            raise ValueError(
                "Must have a path element '++' after a virtual host "
                "directive.")

        request.setVirtualHostRoot(app_names)

        return self.context


class adapter(SimpleHandler):

    def traverse(self, name, ignored):
        """Adapter traversal adapter

        This adapter provides traversal to named adapters registered
        to provide IPathAdapter.

        To demonstrate this, we need to register some adapters:

          >>> def adapter1(ob):
          ...     return 1
          >>> def adapter2(ob):
          ...     return 2
          >>> zope.component.provideAdapter(
          ...     adapter1, (None,), IPathAdapter, 'a1')
          >>> zope.component.provideAdapter(
          ...     adapter2, (None,), IPathAdapter, 'a2')

        Now, with these adapters in place, we can use the traversal adapter:

          >>> ob = object()
          >>> adapter = adapter(ob)
          >>> adapter.traverse('a1', ())
          1
          >>> adapter.traverse('a2', ())
          2
          >>> try:
          ...     adapter.traverse('bob', ())
          ... except TraversalError:
          ...     print 'no adapter'
          no adapter

        Clean up:
        
          >>> from zope.testing.cleanup import cleanUp
          >>> cleanUp()
        """
        try:
            return zope.component.getAdapter(self.context, IPathAdapter, name)
        except ComponentLookupError:
            raise TraversalError(self.context, name)


class debug(view):

    def traverse(self, name, ignored):
        """Debug traversal adapter

        This adapter allows debugging flags to be set in the request.
        See IDebugFlags.

        Setup for demonstration:

            >>> from zope.publisher.browser import TestRequest
            >>> request = TestRequest()
            >>> ob = object()
            >>> adapter = debug(ob, request)

        in debug mode, ++debug++source enables source annotations

            >>> request.debug.sourceAnnotations
            False
            >>> adapter.traverse('source', ()) is ob
            True
            >>> request.debug.sourceAnnotations
            True

        ++debug++tal enables TAL markup in output

            >>> request.debug.showTAL
            False
            >>> adapter.traverse('tal', ()) is ob
            True
            >>> request.debug.showTAL
            True

        ++debug++errors enables tracebacks (by switching to debug skin)

            >>> from zope.publisher.interfaces.browser import IBrowserRequest

            >>> class Debug(IBrowserRequest):
            ...     pass
            >>> directlyProvides(Debug, IBrowserSkinType)
            >>> zope.component.provideUtility(
            ...     Debug, IBrowserSkinType, name='Debug')

            >>> Debug.providedBy(request)
            False
            >>> adapter.traverse('errors', ()) is ob
            True
            >>> Debug.providedBy(request)
            True

        You can specify several flags separated by commas

            >>> adapter.traverse('source,tal', ()) is ob
            True

        Unknown flag names cause exceptions

            >>> try:
            ...     adapter.traverse('badflag', ())
            ... except ValueError:
            ...     print 'unknown debugging flag'
            unknown debugging flag

        """
        if __debug__:
            request = self.request
            for flag in name.split(','):
                if flag == 'source':
                    request.debug.sourceAnnotations = True
                elif flag == 'tal':
                    request.debug.showTAL = True
                elif flag == 'errors':
                    # TODO: I am not sure this is the best solution.  What
                    # if we want to enable tracebacks when also trying to
                    # debug a different skin?
                    skin = zope.component.getUtility(IBrowserSkinType, 'Debug')
                    directlyProvides(request, providedBy(request)+skin)
                else:
                    raise ValueError("Unknown debug flag: %s" % flag)
            return self.context
        else:
            raise ValueError("Debug flags only allowed in debug mode")

    if not __debug__:
        # If not in debug mode, we should get an error:
        traverse.__doc__ = """Disabled debug traversal adapter

        This adapter allows debugging flags to be set in the request,
        but it is disabled because Python was run with -O.

        Setup for demonstration:

            >>> from zope.publisher.browser import TestRequest
            >>> request = TestRequest()
            >>> ob = object()
            >>> adapter = debug(ob, request)

        in debug mode, ++debug++source enables source annotations

            >>> request.debug.sourceAnnotations
            False
            >>> adapter.traverse('source', ()) is ob
            Traceback (most recent call last):
            ...
            ValueError: Debug flags only allowed in debug mode

        ++debug++tal enables TAL markup in output

            >>> request.debug.showTAL
            False
            >>> adapter.traverse('tal', ()) is ob
            Traceback (most recent call last):
            ...
            ValueError: Debug flags only allowed in debug mode

        ++debug++errors enables tracebacks (by switching to debug skin)

            >>> Debug.providedBy(request)
            False
            >>> adapter.traverse('errors', ()) is ob
            Traceback (most recent call last):
            ...
            ValueError: Debug flags only allowed in debug mode

        You can specify several flags separated by commas

            >>> adapter.traverse('source,tal', ()) is ob
            Traceback (most recent call last):
            ...
            ValueError: Debug flags only allowed in debug mode
        """
