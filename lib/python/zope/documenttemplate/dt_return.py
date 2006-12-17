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
"""

$Id: dt_return.py 26737 2004-07-23 22:08:14Z jim $
"""
from zope.documenttemplate.dt_util import parse_params, name_param

class ReturnTag:
    name = 'return'
    expr = None

    def __init__(self, context, args):
        args = parse_params(args, name='', expr='')
        name, expr = name_param(context, args,'var',1)
        self.__name__, self.expr = name, expr

    def render(self, md):
        name = self.__name__
        val = self.expr
        if val is None:
            val = md[name]
        else:
            val = val.eval(md)

        raise DTReturn(val)

    __call__ = render


class DTReturn:
    def __init__(self, v):
        self.v = v
