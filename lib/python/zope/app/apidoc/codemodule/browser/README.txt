====================================
Code Browser Presentation Components
====================================

This document describes the API of the views complementing the varius code
browser documentation components. The views can be found in

  >>> from zope.app.apidoc.codemodule import browser

We will also need the code browser documentation module:

  >>> from zope.component import getUtility
  >>> from zope.app.apidoc.interfaces import IDocumentationModule
  >>> cm = getUtility(IDocumentationModule, 'Code')

The `zope` package is already registered and available with the code module.


Module Details
--------------

The module details are easily created, since we can just use the traversal
process to get a module documentation object:

  >>> from zope.traversing.api import traverse
  >>> details = browser.module.ModuleDetails(None, None)
  >>> details.context = traverse(cm,
  ...     'zope/app/apidoc/codemodule/codemodule')
  >>> from zope.publisher.browser import TestRequest
  >>> details.request = TestRequest()

`getDoc()`
~~~~~~~~~~

Get the doc string of the module formatted in STX or ReST.

  >>> print details.getDoc().strip()
  <p>Code Documentation Module</p>
  <p>This module is able to take a dotted name of any class and display
  documentation for it.</p>

`getEntries(columns=True)`
~~~~~~~~~~~~~~~~~~~~~~~~~~

Return info objects for all modules and classes in this module.

  >>> pprint(details.getEntries(False))
  [{'isclass': True,
    'isfunction': False,
    'isinterface': False,
    'ismodule': False,
    'istextfile': False,
    'iszcmlfile': False,
    'name': 'CodeModule',
    'path': 'zope.app.apidoc.codemodule.class_.CodeModule',
    'url': 'http://127.0.0.1/zope/app/apidoc/codemodule/codemodule/CodeModule'}]

`getBreadCrumbs()`
~~~~~~~~~~~~~~~~~~

Create breadcrumbs for the module path.

We cannot reuse the the system's bread crumbs, since they go all the
way up to the root, but we just want to go to the root module.

  >>> pprint(details.getBreadCrumbs())
  [{'name': u'[top]',
    'url': 'http://127.0.0.1'},
   {'name': u'zope',
    'url': 'http://127.0.0.1/zope'},
   {'name': 'app',
    'url': 'http://127.0.0.1/zope/app'},
   {'name': 'apidoc',
    'url': 'http://127.0.0.1/zope/app/apidoc'},
   {'name': 'codemodule',
    'url': 'http://127.0.0.1/zope/app/apidoc/codemodule'},
   {'name': 'codemodule',
    'url': 'http://127.0.0.1/zope/app/apidoc/codemodule/codemodule'}]


Class Details
-------------

The class details are easily created, since we can just use the traversal
process to get a class documentation object:

  >>> details = browser.class_.ClassDetails()
  >>> details.context = traverse(
  ...     cm, 'zope/app/apidoc/codemodule/codemodule/CodeModule')

  >>> details.request = TestRequest()

Now that we have the details class we can just access the various methods:

`getBases()`
~~~~~~~~~~~~

Get all bases of this class.

  >>> pprint(details.getBases())
  [{'path': 'zope.app.apidoc.codemodule.module.Module',
    'url': 'http://127.0.0.1/zope/app/apidoc/codemodule/module/Module'}]

`getKnownSubclasses()`
~~~~~~~~~~~~~~~~~~~~~~
Get all known subclasses of this class.

  >>> details.getKnownSubclasses()
  []

`_listClasses(classes)`
~~~~~~~~~~~~~~~~~~~~~~~

Prepare a list of classes for presentation.

  >>> import zope.app.apidoc.apidoc
  >>> import zope.app.apidoc.codemodule.codemodule

  >>> pprint(details._listClasses([
  ...       zope.app.apidoc.apidoc.APIDocumentation,
  ...       zope.app.apidoc.codemodule.codemodule.Module]))
  [{'path': 'zope.app.apidoc.apidoc.APIDocumentation',
    'url': 'http://127.0.0.1/zope/app/apidoc/apidoc/APIDocumentation'},
   {'path': 'zope.app.apidoc.codemodule.module.Module',
    'url': 'http://127.0.0.1/zope/app/apidoc/codemodule/module/Module'}]

`getBaseURL()`
~~~~~~~~~~~~~~

Return the URL for the API Documentation Tool.

Note that the following output is a bit different than usual, since
we have not setup all path elements.

  >>> details.getBaseURL()
  'http://127.0.0.1'

`getInterfaces()`
~~~~~~~~~~~~~~~~~

Get all implemented interfaces (as paths) of this class.

  >>> pprint(details.getInterfaces())
  [{'path': 'zope.app.apidoc.interfaces.IDocumentationModule',
    'url': 'zope.app.apidoc.interfaces.IDocumentationModule'},
   {'path': 'zope.location.interfaces.ILocation',
    'url': 'zope.location.interfaces.ILocation'},
   {'path': 'zope.app.apidoc.codemodule.interfaces.IModuleDocumentation',
    'url': 'zope.app.apidoc.codemodule.interfaces.IModuleDocumentation'},
   {'path': 'zope.app.container.interfaces.IReadContainer',
    'url': 'zope.app.container.interfaces.IReadContainer'}]

`getAttributes()`
~~~~~~~~~~~~~~~~~

Get all attributes of this class.

  >>> pprint(details.getAttributes()[1])
  {'interface': {'path': 'zope.app.apidoc.interfaces.IDocumentationModule',
                 'url': 'zope.app.apidoc.interfaces.IDocumentationModule'},
   'name': 'title',
   'read_perm': None,
   'type': 'Message',
   'type_link': 'zope/i18nmessageid/message/Message',
   'value': "u'Code Browser'",
   'write_perm': None}

`getMethods()`
~~~~~~~~~~~~~~
Get all methods of this class.

  >>> pprint(details.getMethods()[-2:])
  [{'doc': u'<p>Setup module and class tree.</p>\n',
    'interface': None,
    'name': 'setup',
    'read_perm': None,
    'signature': '()',
    'write_perm': None},
   {'doc': u'',
    'interface': {'path': 'zope.interface.common.mapping.IEnumerableMapping',
                  'url': 'zope.interface.common.mapping.IEnumerableMapping'},
    'name': 'values',
    'read_perm': None,
    'signature': '()',
    'write_perm': None}]

`getDoc()`
~~~~~~~~~~

Get the doc string of the class STX formatted.

  >>> print details.getDoc()[:-1]
  <p>Represent the code browser documentation root</p>


Function Details
----------------

This is the same deal as before, use the path to generate the function
documentation component:

  >>> details = browser.function.FunctionDetails()
  >>> details.context = traverse(cm,
  ...     'zope/app/apidoc/codemodule/browser/tests/foo')
  >>> details.request = TestRequest()

Here are the methods:

`getDocString()`
~~~~~~~~~~~~~~~~

Get the doc string of the function in a rendered format.

  >>> details.getDocString()
  u'<p>This is the foo function.</p>\n'

`getAttributes()`
~~~~~~~~~~~~~~~~~

Get all attributes of this function.

  >>> attr = details.getAttributes()[0]
  >>> pprint(attr)
  {'name': 'deprecated',
   'type': 'bool',
   'type_link': '__builtin__/bool',
   'value': 'True'}

`getBaseURL()`
~~~~~~~~~~~~~~

Return the URL for the API Documentation Tool.

Note that the following output is a bit different than usual, since
we have not setup all path elements.

  >>> details.getBaseURL()
  'http://127.0.0.1'


Text File Details
-----------------

This is the same deal as before, use the path to generate the text file
documentation component:

  >>> details = browser.text.TextFileDetails()
  >>> details.context = traverse(cm,
  ...     'zope/app/apidoc/codemodule/README.txt')
  >>> details.request = TestRequest()

Here are the methods:

`renderedContent()`
~~~~~~~~~~~~~~~~~~~

Render the file content to HTML.

  >>> print details.renderedContent()[:48]
  <h1 class="title">Code Documentation Module</h1>


ZCML File and Directive Details
-------------------------------

The ZCML file details are a bit different, since there is no view class for
ZCML files, just a template. The template then uses the directive details to
provide all the view content:

  >>> details = browser.zcml.DirectiveDetails()
  >>> zcml = traverse(cm,
  ...     'zope/app/apidoc/codemodule/configure.zcml')
  >>> details.context = zcml.rootElement
  >>> details.request = TestRequest()
  >>> details.__parent__ = details.context

Here are the methods for the directive details:

`fullTagName()`
~~~~~~~~~~~~~~~

Return the name of the directive, including prefix, if applicable.

  >>> details.fullTagName()
  u'configure'

`line()`
~~~~~~~~

Return the line (as a string) at which this directive starts.

  >>> details.line()
  '1'

`highlight()`
~~~~~~~~~~~~~

It is possible to highlight a directive by passing the `line` variable as a
request variable. If the value of `line` matches the output of `line()`, this
method returns 'highlight' and otherwise ''. 'highlight' is a CSS class that
places a colored box around the directive.

  >>> details.highlight()
  ''

  >>> details.request = TestRequest(line='1')
  >>> details.highlight()
  'highlight'

`url()`
~~~~~~~

Returns the URL of the directive docuemntation in the ZCML documentation
module.

  >>> details.url()
  u'http://127.0.0.1/../ZCML/ALL/configure/index.html'

The result is a bit strange, since the ZCML Documentation module is the
containment root.

`objectURL(value, field, rootURL)`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method converts the string value of the field to an object and then
crafts a documentation URL for it:

  >>> from zope.configuration.fields import GlobalObject
  >>> field = GlobalObject()

  >>> details.objectURL('.interfaces.IZCMLFile', field, '')
  '/../Interface/zope.app.apidoc.codemodule.interfaces.IZCMLFile/index.html'

  >>> details.objectURL('.zcml.ZCMLFile', field, '')
  '/zope/app/apidoc/codemodule/zcml/ZCMLFile/index.html'

`attributes()`
~~~~~~~~~~~~~~

Returns a list of info dictionaries representing all the attributes in the
directive. If the directive is the root directive, all namespace declarations
will be listed too.

  >>> pprint(details.attributes())
  [{'name': 'xmlns',
    'url': None,
    'value': u'http://namespaces.zope.org/zope',
    'values': []},
   {'name': u'xmlns:apidoc',
    'url': None,
    'value': u'http://namespaces.zope.org/apidoc',
    'values': []},
   {'name': u'xmlns:browser',
    'url': None,
    'value': u'http://namespaces.zope.org/browser',
    'values': []}]

  >>> details.context = details.context.subs[0]
  >>> pprint(details.attributes())
  [{'name': u'class',
    'url':
        'http://127.0.0.1/zope/app/apidoc/codemodule/module/Module/index.html',
    'value': u'.module.Module',
    'values': []}]

`hasSubDirectives()`
~~~~~~~~~~~~~~~~~~~~

Returns `True`, if the directive has subdirectives; otherwise `False` is
returned.

  >>> details.hasSubDirectives()
  True

`getElements()`
~~~~~~~~~~~~~~~

Returns a list of all sub-directives:

  >>> details.getElements()
  [<Directive (u'http://namespaces.zope.org/zope', u'allow')>]


The Introspector
----------------

There are several tools that are used to support the introspector.

  >>> from zope.app.apidoc.codemodule.browser import introspector

`getTypeLink(type)`
~~~~~~~~~~~~~~~~~~~

This little helper function returns the path to the type class:

  >>> from zope.app.apidoc.apidoc import APIDocumentation
  >>> introspector.getTypeLink(APIDocumentation)
  'zope/app/apidoc/apidoc/APIDocumentation'

  >>> introspector.getTypeLink(dict)
  '__builtin__/dict'

  >>> introspector.getTypeLink(type(None)) is None
  True

`++annootations++` Namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This namespace is used to traverse into the annotations of an object.

  >>> import zope.interface
  >>> from zope.annotation.interfaces import IAttributeAnnotatable

  >>> class Sample(object):
  ...    zope.interface.implements(IAttributeAnnotatable)

  >>> sample = Sample()
  >>> sample.__annotations__ = {'zope.my.namespace': 'Hello there!'}

  >>> ns = introspector.annotationsNamespace(sample)
  >>> ns.traverse('zope.my.namespace', None)
  'Hello there!'

  >>> ns.traverse('zope.my.unknown', None)
  Traceback (most recent call last):
  ...
  KeyError: 'zope.my.unknown'

Mapping `++items++` namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This namespace allows us to traverse the items of any mapping:

  >>> ns = introspector.mappingItemsNamespace({'mykey': 'myvalue'})
  >>> ns.traverse('mykey', None)
  'myvalue'

  >>> ns.traverse('unknown', None)
  Traceback (most recent call last):
  ...
  KeyError: 'unknown'


Sequence `++items++` namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This namespace allows us to traverse the items of any sequence:

  >>> ns = introspector.sequenceItemsNamespace(['value1', 'value2'])
  >>> ns.traverse('0', None)
  'value1'

  >>> ns.traverse('2', None)
  Traceback (most recent call last):
  ...
  IndexError: list index out of range

  >>> ns.traverse('text', None)
  Traceback (most recent call last):
  ...
  ValueError: invalid literal for int(): text

Introspector View
~~~~~~~~~~~~~~~~~

The main contents of the introspector view comes from the introspector view
class. In the following section we are going to demonstrate the methods used
to collect the data. First we need to create an object though; let's use a
root folder:

  >>> rootFolder
  <zope.app.folder.folder.Folder object at ...>

Now we instantiate the view

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()
  >>> inspect = introspector.Introspector(rootFolder, request)

so that we can start looking at the methods. First we should note that the
class documentation view is directly available:

  >>> inspect.klassView
  <zope.app.apidoc.codemodule.browser.tests.Details object at ...>
  >>> inspect.klassView.context
  <zope.app.apidoc.codemodule.class_.Class object at ...>

You can get the parent of the inspected object, which is ``None`` for the root
folder:

  >>> inspect.parent() is None
  True

You can also get the base URL of the request:

  >>> inspect.getBaseURL()
  'http://127.0.0.1'

Next you can get a list of all directly provided interfaces:

  >>> ifaces = inspect.getDirectlyProvidedInterfaces()
  >>> ifaces.sort()
  >>> ifaces
  ['zope.app.component.interfaces.ISite',
   'zope.app.folder.interfaces.IRootFolder']

The ``getProvidedInterfaces()`` and ``getBases()`` method simply forwards its
request to the class documentation view. Thus the next method is
``getAttributes()``, which collects all sorts of useful information about the
object's attributes:

  >>> pprint(list(inspect.getAttributes()))
  [{'interface': None,
    'name': 'data',
    'read_perm': None,
    'type': 'OOBTree',
    'type_link': 'BTrees/_OOBTree/OOBTree',
    'value': '<BTrees._OOBTree.OOBTree object at ...>',
    'value_linkable': True,
    'write_perm': None}]

Of course, the methods are listed as well:

  >>> pprint(list(inspect.getMethods()))
    [...
     {'doc': u'',
      'interface': 'zope.app.component.interfaces.IPossibleSite',
      'name': 'getSiteManager',
      'read_perm': None,
      'signature': '()',
      'write_perm': None},
     ...
     {'doc': u'<p>Return a sequence-like...',
      'interface': 'zope.interface.common.mapping.IEnumerableMapping',
      'name': 'keys',
      'read_perm': None,
      'signature': '()',
      'write_perm': None},
     {'doc': u'',
      'interface': 'zope.app.component.interfaces.IPossibleSite',
      'name': 'setSiteManager',
      'read_perm': None,
      'signature': '(sm)',
      'write_perm': None},
     ...]

The final methods deal with inspecting the objects data further. For exmaple,
if we inspect a sequence,

  >>> from persistent.list import PersistentList
  >>> list = PersistentList(['one', 'two'])

  >>> from zope.interface.common.sequence import IExtendedReadSequence
  >>> zope.interface.directlyProvides(list, IExtendedReadSequence)

  >>> inspect2 = introspector.Introspector(list, request)

we can first determine whether it really is a sequence

  >>> inspect2.isSequence()
  True

and then get the sequence items:

  >>> pprint(inspect2.getSequenceItems())
  [{'index': 0,
    'value': "'one'",
    'value_type': 'str',
    'value_type_link': '__builtin__/str'},
   {'index': 1,
    'value': "'two'",
    'value_type': 'str',
    'value_type_link': '__builtin__/str'}]

Similar functionality exists for a mapping. But we first have to add an item:

  >>> rootFolder['list'] = list

Now let's have a look:

  >>> inspect.isMapping()
  True

  >>> pprint(inspect.getMappingItems())
  [{'key': u'list',
    'key_string': "u'list'",
    'value': "['one', 'two']",
    'value_type': 'ContainedProxy',
    'value_type_link': 'zope/app/container/contained/ContainedProxy'}]

The final two methods doeal with the introspection of the annotations. If an
object is annotatable,

  >>> inspect.isAnnotatable()
  True

then we can get an annotation mapping:

  >>> rootFolder.__annotations__ = {'my.list': list}

  >>> pprint(inspect.getAnnotationsInfo())
  [{'key': 'my.list',
    'key_string': "'my.list'",
    'value': "['one', 'two']",
    'value_type': 'PersistentList',
    'value_type_link': 'persistent/list/PersistentList'}]

And that's it. Fur some browser-based demonstration see ``introspector.txt``.
