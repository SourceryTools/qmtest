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
"""Code Documentation Module

This module is able to take a dotted name of any class and display
documentation for it.

$Id: __init__.py 29269 2005-02-23 22:22:48Z srichter $
"""
__docformat__ = 'restructuredtext'

import zope.component
from zope.interface import implements

from zope.app.i18n import ZopeMessageFactory as _
from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.classregistry import safe_import
from zope.app.apidoc.codemodule.interfaces import IAPIDocRootModule
from zope.app.apidoc.codemodule.module import Module


class CodeModule(Module):
    """Represent the code browser documentation root"""
    implements(IDocumentationModule)

    # See zope.app.apidoc.interfaces.IDocumentationModule
    title = _('Code Browser')

    # See zope.app.apidoc.interfaces.IDocumentationModule
    description = _("""
    This module allows you to get an overview of the modules and classes
    defined in the Zope 3 framework and its supporting packages. There are
    two methods to navigate through the modules to find the classes you are
    interested in.

    The first method is to type in some part of the Python path of the class
    and the module will look in the class registry for matches. The menu will
    then return with a list of these matches.

    The second method is to click on the "Browse Zope Source" link. In the
    main window, you will see a directory listing with the root Zope 3
    modules. You can click on the module names to discover their content. If a
    class is found, it is represented as a bold entry in the list.

    The documentation contents of a class provides you with an incredible
    amount of information. Not only does it tell you about its base classes,
    implemented interfaces, attributes and methods, but it also lists the
    interface that requires a method or attribute to be implemented and the
    permissions required to access it.
    """)
    def __init__(self):
        """Initialize object."""
        super(CodeModule, self).__init__(None, '', None, False)
        self.__isSetup = False

    def setup(self):
        """Setup module and class tree."""
        if self.__isSetup:
            return
        for name, mod in zope.component.getUtilitiesFor(IAPIDocRootModule):
            module = safe_import(mod)
            if module is not None:
                self._children[name] = Module(self, name, module)
        self.__isSetup = True

    def getDocString(self):
        """See Module class."""
        return _('Zope 3 root.')

    def getFileName(self):
        """See Module class."""
        return ''

    def getPath(self):
        """See Module class."""
        return ''

    def get(self, key, default=None):
        """See zope.app.container.interfaces.IReadContainer."""
        self.setup()
        return super(CodeModule, self).get(key, default)

    def items(self):
        """See zope.app.container.interfaces.IReadContainer."""
        self.setup()
        return super(CodeModule, self).items()
