##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
r'''How to conditionalize specific directives

There is a "condition" attribute in the
"http://namespaces.zope.org/zcml" namespace which is honored on all
elements in ZCML.  The value of the attribute is an expression
which is used to determine if that element and its descendents are
used.  If the condition is true, processing continues normally,
otherwise that element and its descendents are ignored.

Currently the expression is always of the form "have featurename", and it
checks for the presence of a <meta:provides feature="featurename" />.

Our demonstration uses a trivial registry; each registration consists
of a simple id inserted in the global `registry` in this module.  We
can checked that a registration was made by checking whether the id is
present in `registry`.

We start by loading the example ZCML file, *conditions.zcml*::

  >>> import zope.configuration.tests
  >>> import zope.configuration.xmlconfig

  >>> context = zope.configuration.xmlconfig.file("conditions.zcml",
  ...                                             zope.configuration.tests)

To show that our sample directive works, we see that the unqualified
registration was successful::

  >>> "unqualified.registration" in registry
  True

When the expression specified with ``zcml:condition`` evaluates to
true, the element it is attached to and all contained elements (not
otherwise conditioned) should be processed normally::

  >>> "direct.true.condition" in registry
  True
  >>> "nested.true.condition" in registry
  True

However, when the expression evaluates to false, the conditioned
element and all contained elements should be ignored::

  >>> "direct.false.condition" in registry
  False
  >>> "nested.false.condition" in registry
  False

Conditions on container elements affect the conditions in nested
elements in a reasonable way.  If an "outer" condition is true, nested
conditions are processed normally::

  >>> "true.condition.nested.in.true" in registry
  True
  >>> "false.condition.nested.in.true" in registry
  False

If the outer condition is false, inner conditions are not even
evaluated, and the nested elements are ignored::

  >>> "true.condition.nested.in.false" in registry
  False
  >>> "false.condition.nested.in.false" in registry
  False

Now we need to clean up after ourselves::

  >>> del registry[:]

'''
__docformat__ = "reStructuredText"

import zope.interface
import zope.schema
import zope.testing.doctest


class IRegister(zope.interface.Interface):
    """Trivial sample registry."""

    id = zope.schema.Id(
        title=u"Identifier",
        description=u"Some identifier that can be checked.",
        required=True,
        )

registry = []

def register(context, id):
    context.action(discriminator=('Register', id),
                   callable=registry.append,
                   args=(id,)
                   )

def test_suite():
    return zope.testing.doctest.DocTestSuite()
