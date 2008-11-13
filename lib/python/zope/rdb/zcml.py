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
"""'rdb' ZCML Namespace Directives

$Id: zcml.py 66862 2006-04-11 18:00:42Z philikon $
"""
import zope.component
from zope.configuration.fields import GlobalObject
from zope.interface import Interface
from zope.schema import TextLine
from zope.rdb.interfaces import IZopeDatabaseAdapter

class IProvideConnectionDirective(Interface):
    """This directive creates a globale connection to an RDBMS."""

    name = TextLine(
        title=u"Name",
        description=u"This is the name the connection will be known as.",
        required=True)

    component = GlobalObject(
        title=u"Component",
        description=u"Specifies the component that provides the connection. "
                     "This component handles one particular RDBMS.",
        required=True)

    dsn = TextLine(
        title=u"DSN",
        description=u"The DSN contains all the connection information. The"\
                    u"syntax looks as follows: \n" \
                    u"dbi://username:password@host:port/dbname;param1=value...",
        default=u"dbi://localhost/testdb",
        required=True)

def connectionhandler(_context, name, component, dsn):
    connection = component(dsn)
    _context.action(
            discriminator = ('provideConnection', name),
            callable = provideConnection,
            args = (name, connection) )
    
def provideConnection(name, connection):
    """ Registers a database connection
    
    Uses the global site manager for registering the connection
    """
    gsm = zope.component.getGlobalSiteManager()
    gsm.registerUtility(connection, IZopeDatabaseAdapter, name)
