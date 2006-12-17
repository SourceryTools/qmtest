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
"""Class Registry

$Id: __init__.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'

__import_unknown_modules__ = False

# List of modules that should never be imported.
# TODO: List hard-coded for now.
IGNORE_MODULES = ['twisted']

import sys

class ClassRegistry(dict):
    """A simple registry for classes."""

    def getClassesThatImplement(self, iface):
        """Return all class items that implement iface.

        Methods returns a list of 2-tuples of the form (path, class).
        """
        return [(path, klass) for path, klass in self.items()
                if iface.implementedBy(klass)]

    def getSubclassesOf(self, klass):
        """Return all class items that are proper subclasses of klass.

        Methods returns a list of 2-tuples of the form (path, class).
        """
        return [(path, klass2) for path, klass2 in self.items()
                if issubclass(klass2, klass) and klass2 is not klass]


classRegistry = ClassRegistry()

def cleanUp():
    classRegistry.clear()

from zope.testing.cleanup import addCleanUp
addCleanUp(cleanUp)


def safe_import(path, default=None):
    """Import a given path as efficiently as possible and without failure."""
    module = sys.modules.get(path, default)
    for exclude_name in IGNORE_MODULES:
        if path.startswith(exclude_name):
            return default
    if module is default and __import_unknown_modules__:
        try:
            module = __import__(path, {}, {}, ('*',))
        except ImportError:
            return default
        # Some software, we cannot control, might raise all sorts of errors;
        # thus catch all exceptions and return the default.
        except Exception, error:
            return default
    return module
