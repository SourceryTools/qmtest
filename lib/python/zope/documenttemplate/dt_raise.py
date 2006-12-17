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
'''Raising exceptions

   Errors can be raised from DTML using the 'raise' tag.

   For example::

    <dtml-if expr="condition_that_tests_input">
       <dtml-raise type="Input Error">
           The value you entered is not valid
       </dtml-raise>
    </dtml-if>

$Id: dt_raise.py 38178 2005-08-30 21:50:19Z mj $
'''
from zope.documenttemplate.dt_util \
     import parse_params, name_param, render_blocks

class Raise:
    blockContinuations = ()
    name = 'raise'
    expr = ''

    def __init__(self, context, blocks):
        tname, args, section = blocks[0]
        self.section=section.blocks
        args=parse_params(args, type='', expr='')
        self.__name__, self.expr = name_param(
            context, args, 'raise', 1, attr='type')

    def render(self, md):
        expr = self.expr
        if expr is None:
            t = self.__name__
            if t[-5:] == 'Error' and __builtins__.has_key(t):
                t = __builtins__[t]
        else:
            try:
                t = expr.eval(md)
            except:
                t = 'Invalid Error Type Expression'

        try:
            v = render_blocks(self.section,md)
        except:
            v = 'Invalid Error Value'

        raise t(v)

    __call__ = render
