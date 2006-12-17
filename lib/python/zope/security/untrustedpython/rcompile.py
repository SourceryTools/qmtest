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
"""compile() equivalent that produces restricted code.

Only 'eval' is supported at this time.

$Id$
"""

import compiler.pycodegen

import RestrictedPython.RCompile
from RestrictedPython.SelectCompiler import ast, OP_ASSIGN, OP_DELETE, OP_APPLY

def compile(text, filename, mode):
    if not isinstance(text, basestring):
        raise TypeError("Compiled source must be string")
    gen = RExpression(text, str(filename), mode)
    gen.compile()
    return gen.getCode()

class RExpression(RestrictedPython.RCompile.RestrictedCompileMode):

    CodeGeneratorClass = compiler.pycodegen.ExpressionCodeGenerator

    def __init__(self, source, filename, mode = "eval"):
        self.mode = mode
        RestrictedPython.RCompile.RestrictedCompileMode.__init__(
            self, source, filename)
        self.rm = RestrictionMutator()


# The security checks are performed by a set of six functions that
# must be provided by the restricted environment.

_getattr_name = ast.Name("getattr")


class RestrictionMutator:

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.used_names = {}

    def error(self, node, info):
        """Records a security error discovered during compilation."""
        lineno = getattr(node, 'lineno', None)
        if lineno is not None and lineno > 0:
            self.errors.append('Line %d: %s' % (lineno, info))
        else:
            self.errors.append(info)

    def visitGetattr(self, node, walker):
        """Converts attribute access to a function call.

        'foo.bar' becomes 'getattr(foo, "bar")'.

        Also prevents augmented assignment of attributes, which would
        be difficult to support correctly.
        """
        node = walker.defaultVisitNode(node)
        return ast.CallFunc(_getattr_name,
                            [node.expr, ast.Const(node.attrname)])

    def visitExec(self, node, walker):
        self.error(node, "exec statements are not supported")

    def visitPrint(self, node, walker):
        """Make sure prints always have a destination

        If we get a print without a destination, make the default destination
        untrusted_output.
        """
        node = walker.defaultVisitNode(node)
        if node.dest is None:
            node.dest = ast.Name('untrusted_output')
        return node
    visitPrintnl = visitPrint
        
    def visitRaise(self, node, walker):
        self.error(node, "raise statements are not supported")

    def visitTryExcept(self, node, walker):
        self.error(node, "try/except statements are not supported")
                   
