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
"""Interfaces for experimental support for application database generations

$Id: interfaces.py 29216 2005-02-19 00:08:56Z jim $
"""
__docformat__ = 'restructuredtext'

import zope.interface

class GenerationError(Exception):
    """A database generation is invalid
    """

class GenerationTooHigh(GenerationError):
    """A database generation is higher than an application generation
    """

class GenerationTooLow(GenerationError):
    """A database generation is lower than an application minimum generation
    """

class UnableToEvolve(GenerationError):
    """A database can't evolve to an application minimum generation
    """


class ISchemaManager(zope.interface.Interface):
    """Manage schema evolution for an application."""

    minimum_generation = zope.interface.Attribute(
        "Minimum supported schema generation")

    generation = zope.interface.Attribute(
        "Current schema generation")

    def evolve(context, generation):
        """Evolve a database to the given schema generation.

        The database should be assumed to be at the schema
        generation one less than the given `generation`
        argument. In other words, the `evolve` method is only
        required to make one evolutionary step.

        The `context` argument has a connection attribute,
        providing a database connection to be used to change
        the database.  A `context` argument is passed rather than
        a connection to make it possible to provide additional
        information later, if it becomes necessary.
        """

    def getInfo(generation):
        """Return an information string about the evolution that is used to
        upgrade to the specified generation.

        If no information is available, `None` should be returned.
        """

class IInstallableSchemaManager(ISchemaManager):
    """Manage schema evolution for an application, including installation."""

    def install(context):
        """Perform any initial installation tasks

        The application has never had the application installed
        before.  The schema manager should bring the database to the
        current generation.
        
        """
