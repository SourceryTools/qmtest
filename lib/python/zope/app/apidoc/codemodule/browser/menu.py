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
"""Code Module Menu

$Id: browser.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'
from zope.component import getUtility
from zope.traversing.api import traverse
from zope.traversing.browser import absoluteURL

from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.classregistry import classRegistry

class Menu(object):
    """Menu for the Class Documentation Module.

    The menu allows for looking for classes by partial names. See
    `findClasses()` for the simple search implementation.
    """

    def findClasses(self):
        """Find the classes that match a partial path.

        Examples::
          >>> from zope.component import getUtility
          >>> from zope.app.apidoc.codemodule.class_ import Class
          >>> from zope.app.apidoc.interfaces import IDocumentationModule

          >>> cm = getUtility(IDocumentationModule, 'Code')
          >>> mod = cm['zope']['app']['apidoc']['codemodule']['browser']

          Setup a couple of classes and register them.

          >>> class Foo(object):
          ...     pass
          >>> mod._children['Foo'] = Class(mod, 'Foo', Foo)
          >>> class Foo2(object):
          ...     pass
          >>> mod._children['Foo2'] = Class(mod, 'Foo2', Foo2)
          >>> class Blah(object):
          ...     pass
          >>> mod._children['Blah'] = Class(mod, 'Blah', Blah)

          Setup the view.

          >>> from zope.app.apidoc.codemodule.browser.menu import Menu
          >>> from zope.publisher.browser import TestRequest
          >>> menu = Menu()
          >>> menu.context = None

          Testing the method with various inputs.

          >>> menu.request = TestRequest(form={'path': 'Foo'})
          >>> info = menu.findClasses()

          >>> pprint(info)
          [{'path': 'zope.app.apidoc.codemodule.browser.Foo',
            'url': 'http://127.0.0.1/zope/app/apidoc/codemodule/browser/Foo/'},
           {'path': 'zope.app.apidoc.codemodule.browser.Foo2',
            'url': 'http://127.0.0.1/zope/app/apidoc/codemodule/browser/Foo2/'}]

          >>> menu.request = TestRequest(form={'path': 'o2'})
          >>> info = menu.findClasses()
          >>> pprint(info)
          [{'path': 'zope.app.apidoc.codemodule.browser.Foo2',
            'url': 'http://127.0.0.1/zope/app/apidoc/codemodule/browser/Foo2/'}]


          >>> menu.request = TestRequest(form={'path': 'Blah'})
          >>> info = menu.findClasses()
          >>> pprint(info)
          [{'path': 'zope.app.apidoc.codemodule.browser.Blah',
            'url': 'http://127.0.0.1/zope/app/apidoc/codemodule/browser/Blah/'}]

        """
        path = self.request.get('path', None)
        if path is None:
            return []
        classModule = getUtility(IDocumentationModule, "Code")
        results = []
        for p in classRegistry.keys():
            if p.find(path) >= 0:
                klass = traverse(classModule, p.replace('.', '/'))
                results.append(
                    {'path': p,
                     'url': absoluteURL(klass, self.request) + '/'
                     })
        results.sort(lambda x, y: cmp(x['path'], y['path']))
        return results

    def findAllClasses(self):

        """Find all classes

        Examples::
          >>> from zope.component import getUtility
          >>> from zope.app.apidoc.codemodule.class_ import Class
          >>> from zope.app.apidoc.interfaces import IDocumentationModule


          >>> cm = getUtility(IDocumentationModule, 'Code')
          >>> mod = cm['zope']['app']['apidoc']['codemodule']['browser']

          Setup a couple of classes and register them.

          >>> class Foo(object):
          ...     pass
          >>> mod._children['Foo'] = Class(mod, 'Foo', Foo)
          >>> class Foo2(object):
          ...     pass
          >>> mod._children['Foo2'] = Class(mod, 'Foo2', Foo2)
          >>> class Blah(object):
          ...     pass
          >>> mod._children['Blah'] = Class(mod, 'Blah', Blah)

          Setup the view.

          >>> from zope.app.apidoc.codemodule.browser.menu import Menu
          >>> from zope.publisher.browser import TestRequest
          >>> menu = Menu()
          >>> menu.context = None

          Testing the method with various inputs.

          >>> menu.request = TestRequest(form={'path': 'Foo'})
          >>> info = menu.findAllClasses()

          >>> len(info) > 3
          True
        """
        classModule = getUtility(IDocumentationModule, "Code")
        classModule.setup() # run setup if not yet done
        results = []
        counter = 0
        for p in classRegistry.keys():
            klass = traverse(classModule, p.replace('.', '/'))
            results.append(
                {'path': p,
                 'url': absoluteURL(klass, self.request),
                 'counter': counter
                 })
            counter += 1

        results.sort(lambda x, y: cmp(x['path'], y['path']))
        return results
