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
"""Module Aliases Package

modulealiases package allows you to make module alias declarations via zcml,
e.g.::

  <modulealias
      module="some.existing.package"
      alias="some.nonexistent.package" />

$Id: metaconfigure.py 69355 2006-08-05 15:29:41Z flox $
"""
__docformat__ = 'restructuredtext'
import sys
import types
import warnings

class ModuleAliasException(Exception):
    pass

def define_module_alias(_context, module, alias):
    warnings.warn_explicit(
        "The 'modulealias' directive has been deprecated and will be "
        "removed in Zope 3.5.  Manipulate sys.modules manually instead.",
        DeprecationWarning, _context.info.file, _context.info.line)    
    _context.action(
        discriminator = None,
        callable = alias_module,
        args = (module, alias, _context),
        )

def alias_module(module, alias, context):
    """ define a module alias by munging sys.modules """
    module_ob = context.resolve(module)
    alias_ob = sys.modules.get(alias)
    if not isinstance(module_ob, types.ModuleType):
        raise ModuleAliasException(
            '"module" %s does not resolve to a module' % module)

    if alias_ob is not None and alias_ob is not module_ob: 
        raise ModuleAliasException(
            '"alias" module %s already exists in sys.modules' % alias)
    
    sys.modules[alias] = module_ob
