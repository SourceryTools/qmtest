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
"""Module representation for code browser

$Id: __init__.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'
import os
import types

import zope
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.location.interfaces import ILocation
from zope.location import LocationProxy

from zope.app.apidoc.classregistry import safe_import
from zope.app.apidoc.utilities import ReadContainerBase
from interfaces import IModuleDocumentation

from zope.app.apidoc.codemodule.class_ import Class
from zope.app.apidoc.codemodule.function import Function
from zope.app.apidoc.codemodule.text import TextFile
from zope.app.apidoc.codemodule.zcml import ZCMLFile

# Ignore these files, since they are not necessary or cannot be imported
# correctly.
IGNORE_FILES = ('tests', 'tests.py', 'ftests', 'ftests.py', 'CVS', 'gadfly',
                'setup.py', 'introspection.py', 'Mount.py')

class Module(ReadContainerBase):
    """This class represents a Python module."""
    implements(ILocation, IModuleDocumentation)

    def __init__(self, parent, name, module, setup=True):
        """Initialize object."""
        self.__parent__ = parent
        self.__name__ = name
        self._module = module
        self._children = {}
        if setup:
            self.__setup()

    def __setup(self):
        """Setup the module sub-tree."""
        # Detect packages
        if hasattr(self._module, '__file__') and \
               (self._module.__file__.endswith('__init__.py') or
                self._module.__file__.endswith('__init__.pyc')or
                self._module.__file__.endswith('__init__.pyo')):
            for dir in self._module.__path__:
                for file in os.listdir(dir):
                    if file in IGNORE_FILES or file in self._children:
                        continue
                    path = os.path.join(dir, file)

                    if (os.path.isdir(path) and
                        '__init__.py' in os.listdir(path)):
                        fullname = self._module.__name__ + '.' + file
                        module = safe_import(fullname)
                        if module is not None:
                            self._children[file] = Module(self, file, module)

                    elif os.path.isfile(path) and file.endswith('.py') and \
                             not file.startswith('__init__'):
                        name = file[:-3]
                        fullname = self._module.__name__ + '.' + name
                        module = safe_import(fullname)
                        if module is not None:
                            self._children[name] = Module(self, name, module)

                    elif os.path.isfile(path) and file.endswith('.zcml'):
                        self._children[file] = ZCMLFile(path, self._module,
                                                        self, file)

                    elif os.path.isfile(path) and file.endswith('.txt'):
                        self._children[file] = TextFile(path, file, self)

        # Setup classes in module, if any are available.
        zope.deprecation.__show__.off()
        for name in self._module.__dict__.keys():
            attr = getattr(self._module, name)
            # We do not want to register duplicates or instances
            if hasattr(attr, '__module__') and \
                   attr.__module__ == self._module.__name__:

                if not hasattr(attr, '__name__') or \
                       attr.__name__ != name:
                    continue

                if isinstance(attr, (types.ClassType, types.TypeType)):
                    self._children[name] = Class(self, name, attr)

                if isinstance(attr, InterfaceClass):
                    self._children[name] = LocationProxy(attr, self, name)

                elif type(attr) is types.FunctionType:
                    self._children[name] = Function(self, name, attr)

        zope.deprecation.__show__.on()


    def getDocString(self):
        """See IModule."""
        return self._module.__doc__

    def getFileName(self):
        """See IModule."""
        return self._module.__file__

    def getPath(self):
        """See IModule."""
        return self._module.__name__

    def get(self, key, default=None):
        """See zope.app.container.interfaces.IReadContainer."""
        obj = self._children.get(key, default)
        if obj is not default:
            return obj

        # We are actually able to find much more than we promise
        if self.getPath():
            path = self.getPath() + '.' + key
        else:
            path = key
        obj = safe_import(path)

        if obj is not None:
            return Module(self, key, obj)

        # Maybe it is a simple attribute of the module
        if obj is None:
            obj = getattr(self._module, key, default)
            if obj is not default:
                obj = LocationProxy(obj, self, key)

        return obj

    def items(self):
        """See zope.app.container.interfaces.IReadContainer."""
        # Only publicize public objects, even though we do keep track of
        # private ones
        return [(name, value)
                for name, value in self._children.items()
                if not name.startswith('_')]
