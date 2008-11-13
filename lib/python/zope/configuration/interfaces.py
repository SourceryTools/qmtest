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
"""Zope Configuration (ZCML) interfaces

$Id: interfaces.py 37552 2005-07-29 17:16:15Z anguenot $
"""
from zope.interface import Interface
from zope.schema import BytesLine
from zope.schema.interfaces import ValidationError

class InvalidToken(ValidationError):
    """Invaid token in list."""

class IConfigurationContext(Interface):
    """Configuration Context

    The configuration context manages information about the state of
    the configuration system, such as the package containing the
    configuration file. More importantly, it provides methods for
    importing objects and opening files relative to the package.
    """

    package = BytesLine(
        title=u"The current package name",
        description=u"""\
          This is the name of the package containing the configuration
          file being executed. If the configuration file was not
          included by package, then this is None.
          """,
        required=False,
        )

    def resolve(dottedname):
        """Resolve a dotted name to an object

        A dotted name is constructed by concatenating a dotted module
        name with a global name within the module using a dot.  For
        example, the object named "spam" in the foo.bar module has a
        dotted name of foo.bar.spam.  If the current package is a
        prefix of a dotted name, then the package name can be relaced
        with a leading dot, So, for example, if the configuration file
        is in the foo package, then the dotted name foo.bar.spam can
        be shortened to .bar.spam.

        If the current package is multiple levels deep, multiple
        leading dots can be used to refer to higher-level modules.
        For example, if the current package is x.y.z, the dotted
        object name ..foo refers to x.y.foo.
        """

    def path(filename):
        """Compute a full file name for the given file

        If the filename is relative to the package, then the returned
        name will include the package path, otherwise, the original
        file name is returned.
        """

    def checkDuplicate(filename):
        """Check for duplicate imports of the same file.

        Raises an exception if this file had been processed before.  This
        is better than an unlimited number of conflict errors.
        """

    def action(self, discriminator, callable, args=(), kw={}, order=0):
        """Record a configuration action

        The job of most directives is to compute actions for later
        processing.  The action method is used to record those
        actions.  The discriminator is used to to find actions that
        conflict. Actions conflict if they have the same
        discriminator. The exception to this is the special case of
        the discriminator with the value None. An actions with a
        discriminator of None never conflicts with other actions. This
        is possible to add an order argument to crudely control the
        order of execution
        """

    def provideFeature(name):
        """Record that a named feature is available in this context."""

    def hasFeature(name):
        """Check whether a named feature is available in this context."""


class IGroupingContext(Interface):

    def before():
        """Do something before processing nested directives
        """

    def after():
        """Do something after processing nested directives
        """
