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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Expression engine configuration and registration.

Each expression engine can have its own expression types and base names.

$Id: engine.py 69506 2006-08-15 12:09:32Z ctheune $
"""
__docformat__ = 'restructuredtext'

import sys

from zope import component
from zope.interface import implements
from zope.component.interfaces import ComponentLookupError
from zope.traversing.interfaces import IPathAdapter, ITraversable
from zope.traversing.interfaces import TraversalError
from zope.traversing.adapters import traversePathElement
from zope.security.untrustedpython import rcompile
from zope.security.proxy import ProxyFactory, removeSecurityProxy
from zope.security.untrustedpython.builtins import SafeBuiltins
from zope.i18n import translate

from zope.tales.expressions import PathExpr, StringExpr, NotExpr, DeferExpr
from zope.tales.expressions import SimpleModuleImporter
from zope.tales.pythonexpr import PythonExpr
from zope.tales.tales import ExpressionEngine, Context

from zope.app.i18n import ZopeMessageFactory as _

class InlineCodeError(Exception):
    pass

class ZopeTraverser(object):

    def __init__(self, proxify=None):
        if proxify is None:
            self.proxify = lambda x: x
        else:
            self.proxify = proxify

    def __call__(self, object, path_items, econtext):
        """Traverses a sequence of names, first trying attributes then items.
        """
        request = getattr(econtext, 'request', None)
        path_items = list(path_items)
        path_items.reverse()

        while path_items:
            name = path_items.pop()
            
            # special-case dicts for performance reasons        
            if getattr(object, '__class__', None) == dict:
                object = object[name]
            else:
                object = traversePathElement(object, name, path_items,
                                             request=request)
            object = self.proxify(object)
        return object

zopeTraverser = ZopeTraverser(ProxyFactory)

class ZopePathExpr(PathExpr):

    def __init__(self, name, expr, engine):
        super(ZopePathExpr, self).__init__(name, expr, engine, zopeTraverser)

trustedZopeTraverser = ZopeTraverser()

class TrustedZopePathExpr(PathExpr):

    def __init__(self, name, expr, engine):
        super(TrustedZopePathExpr, self).__init__(name, expr, engine,
                                                  trustedZopeTraverser)


# Create a version of the restricted built-ins that uses a safe
# version of getattr() that wraps values in security proxies where
# appropriate:


class ZopePythonExpr(PythonExpr):

    def __call__(self, econtext):
        __traceback_info__ = self.text
        vars = self._bind_used_names(econtext, SafeBuiltins)
        return eval(self._code, vars)

    def _compile(self, text, filename):
        return rcompile.compile(text, filename, 'eval')


class ZopeContextBase(Context):
    """Base class for both trusted and untrusted evaluation contexts."""

    def translate(self, msgid, domain=None, mapping=None, default=None):
        return translate(msgid, domain, mapping,
                         context=self.request, default=default)

    evaluateInlineCode = False

    def evaluateCode(self, lang, code):
        if not self.evaluateInlineCode:
            raise InlineCodeError(
                  _('Inline Code Evaluation is deactivated, which means that '
                    'you cannot have inline code snippets in your Page '
                    'Template. Activate Inline Code Evaluation and try again.'))

        # TODO This is only needed when self.evaluateInlineCode is true,
        # so should only be needed for zope.app.pythonpage.
        from zope.app.interpreter.interfaces import IInterpreter
        interpreter = component.queryUtility(IInterpreter, lang)
        if interpreter is None:
            error = _('No interpreter named "${lang_name}" was found.',
                      mapping={'lang_name': lang})
            raise InlineCodeError(error)

        globals = self.vars.copy()
        result = interpreter.evaluateRawCode(code, globals)
        # Add possibly new global variables.
        old_names = self.vars.keys()
        for name, value in globals.items():
            if name not in old_names:
                self.setGlobal(name, value)
        return result


class ZopeContext(ZopeContextBase):
    """Evaluation context for untrusted programs."""

    def evaluateMacro(self, expr):
        """evaluateMacro gets security-proxied macro programs when this
        is run with the zopeTraverser, and in other untrusted
        situations. This will cause evaluation to fail in
        zope.tal.talinterpreter, which knows nothing of security proxies. 
        Therefore, this method removes any proxy from the evaluated
        expression.
        
        >>> output = [('version', 'xxx'), ('mode', 'html'), ('other', 'things')]
        >>> def expression(context):
        ...     return ProxyFactory(output)
        ...
        >>> zc = ZopeContext(ExpressionEngine, {})
        >>> out = zc.evaluateMacro(expression)
        >>> type(out)
        <type 'list'>

        The method does some trivial checking to make sure we are getting
        back a macro like we expect: it must be a sequence of sequences, in
        which the first sequence must start with 'version', and the second
        must start with 'mode'.

        >>> del output[0]
        >>> zc.evaluateMacro(expression) # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: ('unexpected result from macro evaluation.', ...)

        >>> del output[:]
        >>> zc.evaluateMacro(expression) # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: ('unexpected result from macro evaluation.', ...)

        >>> output = None
        >>> zc.evaluateMacro(expression) # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: ('unexpected result from macro evaluation.', ...)
        """
        macro = removeSecurityProxy(Context.evaluateMacro(self, expr))
        # we'll do some basic checks that it is the sort of thing we expect
        problem = False
        try:
            problem = macro[0][0] != 'version' or macro[1][0] != 'mode'
        except (TypeError, IndexError):
            problem = True
        if problem:
            raise ValueError('unexpected result from macro evaluation.', macro)
        return macro

    def setContext(self, name, value):
        # Hook to allow subclasses to do things like adding security proxies
        Context.setContext(self, name, ProxyFactory(value))


class TrustedZopeContext(ZopeContextBase):
    """Evaluation context for trusted programs."""


class AdapterNamespaces(object):
    """Simulate tales function namespaces with adapter lookup.

    When we are asked for a namespace, we return an object that
    actually computes an adapter when called:

    To demonstrate this, we need to register an adapter:

      >>> from zope.app.testing.placelesssetup import setUp, tearDown
      >>> setUp()
      >>> from zope.app.testing import ztapi
      >>> def adapter1(ob):
      ...     return 1
      >>> ztapi.provideAdapter(None, IPathAdapter, adapter1, 'a1')

    Now, with this adapter in place, we can try out the namespaces:

      >>> ob = object()
      >>> namespaces = AdapterNamespaces()
      >>> namespace = namespaces['a1']
      >>> namespace(ob)
      1
      >>> namespace = namespaces['a2']
      >>> namespace(ob)
      Traceback (most recent call last):
      ...
      KeyError: 'a2'


    Cleanup:

      >>> tearDown()
    """

    def __init__(self):
        self.namespaces = {}

    def __getitem__(self, name):
        namespace = self.namespaces.get(name)
        if namespace is None:
            def namespace(object):
                try:
                    return component.getAdapter(object, IPathAdapter, name)
                except ComponentLookupError:
                    raise KeyError(name)

            self.namespaces[name] = namespace
        return namespace


class ZopeBaseEngine(ExpressionEngine):

    _create_context = ZopeContext

    def __init__(self):
        ExpressionEngine.__init__(self)
        self.namespaces = AdapterNamespaces()

    def getContext(self, __namespace=None, **namespace):
        if __namespace:
            if namespace:
                namespace.update(__namespace)
            else:
                namespace = __namespace

        context = self._create_context(self, namespace)

        # Put request into context so path traversal can find it
        if 'request' in namespace:
            context.request = namespace['request']

        # Put context into context so path traversal can find it
        if 'context' in namespace:
            context.context = namespace['context']

        return context

class ZopeEngine(ZopeBaseEngine):
    """Untrusted expression engine.

    This engine does not allow modules to be imported; only modules
    already available may be accessed::

      >>> modname = 'zope.app.pagetemplate.tests.trusted'
      >>> engine = _Engine()
      >>> context = engine.getContext(engine.getBaseNames())

      >>> modname in sys.modules
      False
      >>> context.evaluate('modules/' + modname)
      Traceback (most recent call last):
        ...
      KeyError: 'zope.app.pagetemplate.tests.trusted'

    (The use of ``KeyError`` is an unfortunate implementation detail; I
    think this should be a ``TraversalError``.)

    Modules which have already been imported by trusted code are
    available, wrapped in security proxies::

      >>> m = context.evaluate('modules/sys')
      >>> m.__name__
      'sys'
      >>> m._getframe
      Traceback (most recent call last):
        ...
      ForbiddenAttribute: ('_getframe', <module 'sys' (built-in)>)

    The results of Python expressions evaluated by this engine are
    wrapped in security proxies::

      >>> r = context.evaluate('python: {12: object()}.values')
      >>> type(r)
      <type 'zope.security._proxy._Proxy'>
      >>> r = context.evaluate('python: {12: object()}.values()[0].__class__')
      >>> type(r)
      <type 'zope.security._proxy._Proxy'>

    General path expressions provide objects that are wrapped in
    security proxies as well::

      >>> from zope.app.container.sample import SampleContainer
      >>> from zope.app.testing.placelesssetup import setUp, tearDown
      >>> from zope.security.checker import NamesChecker, defineChecker

      >>> class Container(SampleContainer):
      ...     implements(ITraversable)
      ...     def traverse(self, name, further_path):
      ...         return self[name]

      >>> setUp()
      >>> defineChecker(Container, NamesChecker(['traverse']))
      >>> d = engine.getBaseNames()
      >>> foo = Container()
      >>> foo.__name__ = 'foo'
      >>> d['foo'] = ProxyFactory(foo)
      >>> foo['bar'] = bar = Container()
      >>> bar.__name__ = 'bar'
      >>> bar.__parent__ = foo
      >>> bar['baz'] = baz = Container()
      >>> baz.__name__ = 'baz'
      >>> baz.__parent__ = bar
      >>> context = engine.getContext(d)

      >>> o1 = context.evaluate('foo/bar')
      >>> o1.__name__
      'bar'
      >>> type(o1)
      <type 'zope.security._proxy._Proxy'>

      >>> o2 = context.evaluate('foo/bar/baz')
      >>> o2.__name__
      'baz'
      >>> type(o2)
      <type 'zope.security._proxy._Proxy'>
      >>> o3 = o2.__parent__
      >>> type(o3)
      <type 'zope.security._proxy._Proxy'>
      >>> o1 == o3
      True

      >>> o1 is o2
      False

    Note that this engine special-cases dicts during path traversal:
    it traverses only to their items, but not to their attributes
    (e.g. methods on dicts), because of performance reasons:

      >>> d = engine.getBaseNames()
      >>> d['adict'] = {'items': 123}
      >>> d['anotherdict'] = {}
      >>> context = engine.getContext(d)
      >>> context.evaluate('adict/items')
      123
      >>> context.evaluate('anotherdict/keys')
      Traceback (most recent call last):
        ...
      KeyError: 'keys'

      >>> tearDown()

    """

    def getFunctionNamespace(self, namespacename):
        """ Returns the function namespace """
        return ProxyFactory(
            super(ZopeEngine, self).getFunctionNamespace(namespacename))

class TrustedZopeEngine(ZopeBaseEngine):
    """Trusted expression engine.

    This engine allows modules to be imported::

      >>> modname = 'zope.app.pagetemplate.tests.trusted'
      >>> engine = _TrustedEngine()
      >>> context = engine.getContext(engine.getBaseNames())

      >>> modname in sys.modules
      False
      >>> m = context.evaluate('modules/' + modname)
      >>> m.__name__ == modname
      True
      >>> modname in sys.modules
      True

    Since this is trusted code, we can look at whatever is in the
    module, not just __name__ or what's declared in a security
    assertion::

      >>> m.x
      42

    Clean up after ourselves::

      >>> del sys.modules[modname]

    """

    _create_context = TrustedZopeContext


class TraversableModuleImporter(SimpleModuleImporter):

    implements(ITraversable)

    def traverse(self, name, further_path):
        try:
            return self[name]
        except KeyError:
            raise TraversalError(self, name)


def _Engine(engine=None):
    if engine is None:
        engine = ZopeEngine()
    engine = _create_base_engine(engine, ZopePathExpr)
    engine.registerType('python', ZopePythonExpr)

    # Using a proxy around sys.modules allows page templates to use
    # modules for which security declarations have been made, but
    # disallows execution of any import-time code for modules, which
    # should not be allowed to happen during rendering.
    engine.registerBaseName('modules', ProxyFactory(sys.modules))

    return engine

def _TrustedEngine(engine=None):
    if engine is None:
        engine = TrustedZopeEngine()
    engine = _create_base_engine(engine, TrustedZopePathExpr)
    engine.registerType('python', PythonExpr)
    engine.registerBaseName('modules', TraversableModuleImporter())
    return engine

def _create_base_engine(engine, pathtype):
    for pt in pathtype._default_type_names:
        engine.registerType(pt, pathtype)
    engine.registerType('string', StringExpr)
    engine.registerType('not', NotExpr)
    engine.registerType('defer', DeferExpr)
    return engine


Engine = _Engine()
TrustedEngine = _TrustedEngine()


class AppPT(object):

    def pt_getEngine(self):
        return Engine


class TrustedAppPT(object):

    def pt_getEngine(self):
        return TrustedEngine
