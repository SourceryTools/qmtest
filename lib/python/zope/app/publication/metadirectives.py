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
"""Directive schema, for publication factory

This module provides the schema for the new zcml directive,
that let the developer associate a publication factory to a given
request, based on its method and mimetype.

Each directive also has a name and a sortkey.

The sortkey helps when several directives can handle a request:
they are sorted by this key and the highest one is taken.

$Id: metadirectives.py 39571 2005-10-24 10:56:11Z tziade $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface
from zope.configuration.fields import GlobalObject, Tokens
from zope.schema import TextLine, Int

class IRequestPublicationDirective(Interface):
    """Link a request type to a request and publication factory"""

    name = TextLine(
        title=u'Name',
        description=u'The name of the publication factory.')

    factory = GlobalObject(
        title=u'Factory',
        description=u'The request-publication factory')

    methods = Tokens(
        title=u'Methods',
        description=(u'A list of HTTP method names. If the method is a "*", '
                     u'then all methods will match. Example: "GET POST"'),
        value_type=TextLine(),
        required=False)

    mimetypes = Tokens(
        title=u'Mime Types',
        description=(u'A list of content/mime types of the request. If the '
                     u'type is a "*" then all types will be matched. '
                     u'Example: "text/html text/xml"'),
        value_type=TextLine(),
        required=False)

    priority = Int(
        title=u'Priority',
        description=(u'A priority key used to concurrent'
                     ' publication factories.'),
        required=False)
