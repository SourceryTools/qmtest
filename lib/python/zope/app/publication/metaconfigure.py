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
""" Directive handler for publication factory

See metadirective.py

$Id: metaconfigure.py 70794 2006-10-19 04:29:42Z baijum $
"""
__docformat__ = 'restructuredtext'

from zope.app.publication.requestpublicationregistry import factoryRegistry

def publisher(_context, name, factory, methods=['*'], mimetypes=['*'],
              priority=0):

    factory = factory()

    for method in methods:
        for mimetype in mimetypes:
            _context.action(
                discriminator = (method, mimetype, priority),
                callable = factoryRegistry.register,
                args = (method, mimetype, name, priority, factory)
                )
