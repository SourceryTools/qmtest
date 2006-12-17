##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Renderer configuration code

$Id: metaconfigure.py 69358 2006-08-05 17:54:32Z flox $
"""
# BBB 2006/02/24, to be removed after 12 months

import warnings
from zope.component.zcml import handler
from zope.configuration.fields import GlobalInterface, GlobalObject
from zope.interface import Interface

class IRendererDirective(Interface):
    """
    *BBB: DEPRECATED*

    The 'renderer' directive has been deprecated and will be
    removed in Zope 3.5.  Use the 'view' directive instead.

    Example::

      <browser:view
          name=""
          for="some.interface"
          class="some.class"
          permission="zope.Public"
          />

    Register a renderer for a particular output interface, such as
    IBrowserView.
    """

    sourceType = GlobalInterface(
        title=u"Source Type Interface",
        description=u"Specifies an interface for of a particular source type.",
        required=True)

    for_ = GlobalInterface(
        title=u"Interface of the output type",
        description=u"Specifies the interface of the output type (i.e. "
                    u"browser) for which this view is being registered.",
        required=True)

    factory = GlobalObject(
        title=u"Factory",
        description=u"Specifies the factory that is used to create the "
                    u"view on the source.",
        required=True)

# TODO: Does not seem to be tested
def renderer(_context, sourceType, for_, factory):
    def dottify(obj):
        try:
            return obj.__module__ + '.' + obj.__name__
        except AttributeError:
            return '...'
    warnings.warn_explicit(
        "The 'renderer' directive has been deprecated and will be "
        "removed in Zope 3.5.  Use the 'view' directive instead:\n"
        '  <browser:view\n'
        '      name=""\n'
        '      for="%s"\n'
        '      class="%s"\n'
        '      permission="zope.Public"\n'
        '      />' % (dottify(sourceType), dottify(factory)),
        DeprecationWarning, _context.info.file, _context.info.line)

    _context.action(
        discriminator = ('view', sourceType, u'', for_, 'default'),
        callable = handler,
        args = ('provideAdapter',
                (sourceType,), for_, u'', factory, 'default')
        )
