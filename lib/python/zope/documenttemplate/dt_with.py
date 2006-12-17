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
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Nested namespace access

   The 'with' tag is used to introduce nested namespaces.

   The text enclosed in the with tag is rendered using information
   from the given variable or expression.

   For example, if the variable 'person' is bound to an object that
   has attributes 'name' and 'age', then a 'with' tag like the
   following can be used to access these attributes::

     <dtml-with person>
       <dtml-var name>,
       <dtml-var age>
     </dtml-with>

   Eather a 'name' or an 'expr' attribute may be used to specify data.
   A 'mapping' attribute may be used to indicate that the given data
   should be treated as mapping object, rather than as an object with
   named attributes.

$Id: dt_with.py 26826 2004-07-29 04:57:37Z jim $
"""

from zope.documenttemplate.dt_util import parse_params, name_param
from zope.documenttemplate.dt_util import render_blocks

from types import StringTypes, TupleType


class With:
    blockContinuations = ()
    name = 'with'
    mapping = None
    only = 0

    def __init__(self, context, blocks):
        tname, args, section = blocks[0]
        args = parse_params(args, name='', expr='', mapping=1, only=1)
        name, expr = name_param(context, args, 'with', 1)
        if expr is None:
            expr = name
        else:
            expr = expr.eval
        self.__name__, self.expr = name, expr
        self.section=section.blocks
        if args.has_key('mapping') and args['mapping']:
            self.mapping = 1
        if args.has_key('only') and args['only']:
            self.only = 1

    def render(self, md):
        expr = self.expr
        if isinstance(expr, StringTypes):
            v = md[expr]
        else:
            v = expr(md)

        if self.only:
            _md = md
            md = md.__class__()
            if hasattr(_md, 'validate'):
                md.validate = _md.validate

        if self.mapping:
            md._push(v)
        else:
            if isinstance(v, TupleType) and len(v) == 1:
                v = v[0]
            md._push_instance(v)

        try:
            return render_blocks(self.section, md)
        finally:
            md._pop(1)

    __call__ = render
