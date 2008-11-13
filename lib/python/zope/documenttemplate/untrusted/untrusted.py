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
"""Untrusted document template support

$Id: untrusted.py 26826 2004-07-29 04:57:37Z jim $
"""

from zope.security.checker import ProxyFactory
from zope.documenttemplate.dt_html import HTML
from zope.documenttemplate.dt_util import InstanceDict, TemplateDict
from zope.security.untrustedpython.rcompile import compile
from zope.security.untrustedpython.builtins import SafeBuiltins
from zope.security.checker import NamesChecker

class UntrustedInstanceDict(InstanceDict):

    def __getitem__(self, key):
        return ProxyFactory(InstanceDict.__getitem__(self, key))

class UntrustedTemplateDict(TemplateDict):

    __builtins__ = SafeBuiltins

    __Security_checker__ = NamesChecker([
        'math', 'random', 'range', 'pow', 'test', 'getattr', 'attr', 'hasattr',
        'render', 'namespace', 'reorder',
        'None', 'abs', 'chr', 'divmod', 'float', 'hash', 'hex', 'int',
        'len', 'max', 'min', 'oct', 'ord', 'round', 'str',
        ])

    def _push_instance(self, inst):
        self._push(UntrustedInstanceDict(inst, self))

    def _proxied(self):
        return ProxyFactory(self)

    def __repr__(self):
        return '<an UntrustedTemplateDict>'
    

class UntrustedHTML(HTML):
    __name__ = 'UntrustedHTML'

    TemplateDict = UntrustedTemplateDict

    def compile_python_expresssion(self, src):
        return compile(src, getattr(self, '__name__', '<string>'), 'eval')
    
    def __call__(self, client=None, mapping={}, **kw):
        if kw:
            kw = dict([(k, ProxyFactory(v)) for (k, v) in kw.items()])
        
        return HTML.__call__(self,
                             ProxyFactory(client),
                             ProxyFactory(mapping),
                             **kw)
