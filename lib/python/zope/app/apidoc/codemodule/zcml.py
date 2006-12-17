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
"""ZCML File Representation

$Id$
"""
__docformat__ = "reStructuredText"
import copy
from xml.sax import make_parser
from xml.sax.xmlreader import InputSource
from xml.sax.handler import feature_namespaces

from zope.cachedescriptors.property import Lazy
from zope.configuration import xmlconfig, config
from zope.interface import implements, directlyProvides

import zope.app.appsetup.appsetup

from interfaces import IDirective, IRootDirective, IZCMLFile


class MyConfigHandler(xmlconfig.ConfigurationHandler, object):
    """Special configuration handler to generate an XML tree."""

    def __init__(self, context):
        super(MyConfigHandler, self).__init__(context)
        self.rootElement = self.currentElement = None
        self.prefixes = {}

    def startPrefixMapping(self, prefix, uri):
        self.prefixes[uri] = prefix

    def evaluateCondition(self, expression):
        # We always want to process/show all ZCML directives.
        return True

    def startElementNS(self, name, qname, attrs):
        # The last stack item is parent of the stack item that we are about to
        # create
        stackitem = self.context.stack[-1]
        super(MyConfigHandler, self).startElementNS(name, qname, attrs)

        # Get the parser info from the correct context
        info = self.context.stack[-1].context.info

        # complex stack items behave a bit different than the other ones, so
        # we need to handle it separately
        if isinstance(stackitem, config.ComplexStackItem):
            schema = stackitem.meta.get(name[1])[0]
        else:
            schema = stackitem.context.factory(stackitem.context, name).schema

        # Now we have all the necessary information to create the directive
        element = Directive(name, schema, attrs, stackitem.context, info,
                            self.prefixes)
        # Now we place the directive into the XML directive tree.
        if self.rootElement is None:
            self.rootElement = element
        else:
            self.currentElement.subs.append(element)

        element.__parent__ = self.currentElement
        self.currentElement = element


    def endElementNS(self, name, qname):
        super(MyConfigHandler, self).endElementNS(name, qname)
        self.currentElement = self.currentElement.__parent__


class Directive(object):
    """Representation of a ZCML directive."""
    implements(IDirective)

    def __init__(self, name, schema, attrs, context, info, prefixes):
        self.name = name
        self.schema = schema
        self.attrs = attrs
        self.context = context
        self.info = info
        self.__parent__ = None
        self.subs = []
        self.prefixes = prefixes

    def __repr__(self):
        return '<Directive %s>' %str(self.name)


class ZCMLFile(object):
    """Representation of an entire ZCML file."""
    implements(IZCMLFile)

    def __init__(self, filename, package, parent=None, name=None):
        # Retrieve the directive registry
        self.filename = filename
        self.package = package
        self.__parent__ = parent
        self.__name__ = name

    def rootElement(self):
        # Get the context that was originally generated during startup and
        # create a new context using its registrations
        real_context = zope.app.appsetup.appsetup.getConfigContext()
        context = config.ConfigurationMachine()
        context._registry = copy.copy(real_context._registry)
        context._features = copy.copy(real_context._features)
        context.package = self.package

        # Shut up i18n domain complaints
        context.i18n_domain = 'zope'

        # Since we want to use a custom configuration handler, we need to
        # instantiate the parser object ourselves
        parser = make_parser()
        handler = MyConfigHandler(context)
        parser.setContentHandler(handler)
        parser.setFeature(feature_namespaces, True)

        # Now open the file
        file = open(self.filename)
        src = InputSource(getattr(file, 'name', '<string>'))
        src.setByteStream(file)

        # and parse it
        parser.parse(src)

        # Finally we retrieve the root element, have it provide a special root
        # directive interface and give it a location, so that we can do local
        # lookups.
        root = handler.rootElement
        directlyProvides(root, IRootDirective)
        root.__parent__ = self
        return root

    rootElement = Lazy(rootElement)
