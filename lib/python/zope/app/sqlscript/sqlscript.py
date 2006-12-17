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
"""SQL Script content component implementation

$Id: sqlscript.py 67630 2006-04-27 00:54:03Z jim $
"""
import re
from types import StringTypes

from persistent import Persistent
from persistent.dict import PersistentDict

import zope.component
from zope.interface import implements, classProvides
from zope.interface.common.mapping import IEnumerableMapping
from zope.schema.interfaces import IVocabularyFactory
from zope.rdb import queryForResults
from zope.rdb.interfaces import IZopeDatabaseAdapter

from zope.app.container.contained import Contained
from zope.app.component.vocabulary import UtilityVocabulary
from zope.app.cache.caching import getCacheForObject, getLocationForCache

from zope.app.sqlscript.interfaces import ISQLScript
from zope.app.sqlscript.dtml import SQLDTML


unparmre = re.compile(r'([\000- ]*([^\000- ="]+))')
parmre = re.compile(r'([\000- ]*([^\000- ="]+)=([^\000- ="]+))')
qparmre = re.compile(r'([\000- ]*([^\000- ="]+)="([^"]*)")')


class InvalidParameter(Exception):
    pass

class Arguments(PersistentDict):
    """Hold arguments of SQL Script
    """
    implements(IEnumerableMapping)


class SQLScript(Persistent, Contained):
    implements(ISQLScript)

    def __init__(self, connectionName='', source='', arguments=''):
        self.template = SQLDTML(source)
        self.connectionName = connectionName
        # In our case arguments should be a string that is parsed
        self.arguments = arguments

    def setArguments(self, arguments):
        assert isinstance(arguments, StringTypes), (
               '"arguments" argument of setArguments() must be a string'
               )
        self._arg_string = arguments
        self._arguments = parseArguments(arguments)

    def getArguments(self):
        """See zope.app.sqlscript.interfaces.ISQLScript"""
        return self._arguments

    def getArgumentsString(self):
        return self._arg_string

    # See zope.app.sqlscript.interfaces.ISQLScript
    arguments = property(getArgumentsString, setArguments)

    def setSource(self, source):
        self.template.munge(source)

    def getSource(self):
        return self.template.read_raw()

    # See zope.app.sqlscript.interfaces.ISQLScript
    source = property(getSource, setSource)

    def getTemplate(self):
        """See zope.app.sqlscript.interfaces.ISQLScript"""
        return self.template

    def _setConnectionName(self, name):
        self._connectionName = name
        cache = getCacheForObject(self)
        location = getLocationForCache(self)

        if cache and location:
            cache.invalidate(location)

    def _getConnectionName(self):
        return self._connectionName

    # See zope.app.sqlscript.interfaces.ISQLScript
    connectionName = property(_getConnectionName, _setConnectionName)

    def getConnection(self):
        name = self.connectionName
        connection = zope.component.getUtility(IZopeDatabaseAdapter, name)
        return connection()

    def __call__(self, **kw):
        """See zope.rdb.interfaces"""

        # Try to resolve arguments
        arg_values = {}
        missing = []
        for name in self._arguments.keys():
            name = name.encode('UTF-8')
            try:
                # Try to find argument in keywords
                arg_values[name] = kw[name]
            except KeyError:
                # Okay, the first try failed, so let's try to find the default
                arg = self._arguments[name]
                try:
                    arg_values[name] = arg['default']
                except KeyError:
                    # Now the argument might be optional anyways; let's check
                    try:
                        if not arg['optional']:
                            missing.append(name)
                    except KeyError:
                        missing.append(name)

        try:
            connection = self.getConnection()
        except KeyError:
            raise AttributeError("The database connection '%s' cannot be "
                                 "found." % (self.connectionName))

        query = apply(self.template, (), arg_values)
        cache = getCacheForObject(self)
        location = getLocationForCache(self)
        if cache and location:
            _marker = object()
            result = cache.query(location, {'query': query}, default=_marker)
            if result is not _marker:
                return result
        result = queryForResults(connection, query)
        if cache and location:
            cache.set(result, location, {'query': query})
        return result

def parseArguments(text, result=None):
    """Parse argument string.
    """
    # Make some initializations
    if result is None:
        result  = {}

    __traceback_info__ = text

    # search for the first argument assuming a default value (unquoted) was
    # given
    match_object = parmre.match(text)

    if match_object:
        name    = match_object.group(2)
        value   = {'default': match_object.group(3)}
        length  = len(match_object.group(1))

    else:
        # search for an argument having a quoted default value
        match_object = qparmre.match(text)

        if match_object:
            name    = match_object.group(2)
            value   = {'default': match_object.group(3)}
            length  = len(match_object.group(1))

        else:
            # search for an argument without a default value
            match_object = unparmre.match(text)

            if match_object:
                name    = match_object.group(2)
                value   = {}
                length  = len(match_object.group(1))
            else:
                # We are done parsing
                if not text or not text.strip():
                    return Arguments(result)
                raise InvalidParameter(text)

    # Find type of argument (int, float, string, ...)
    lt = name.find(':')
    if lt > 0:
        if len(name) > lt+1 and name[lt+1] not in ('"', "'", '='):
            value['type'] = name[lt+1:]
            name = name[:lt]
        else:
            raise InvalidParameter(text)

    result[name] = value

    return parseArguments(text[length:], result)


class ConnectionNamesVocabulary(UtilityVocabulary):
    classProvides(IVocabularyFactory)
    interface = IZopeDatabaseAdapter
    nameOnly = True
