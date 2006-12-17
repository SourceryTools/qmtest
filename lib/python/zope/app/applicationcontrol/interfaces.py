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
"""Application Control Interface

$Id: interfaces.py 29278 2005-02-24 10:01:05Z hdima $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface

class IApplicationControl(Interface):
    """The application control instance is usually generated upon startup and
    can therefore record the startup time."""

    def getStartTime():
        """Return time the application started in seconds since the epoch."""


class IRuntimeInfo(Interface):
    """Runtime Information Adapter for Application Control"""

    def getPreferredEncoding():
        """Return the encoding used for text data, according
           to user system preferences"""

    def getFileSystemEncoding():
        """Return the name of the encoding used to convert
           Unicode filenames into system file names"""

    def getZopeVersion():
        """Return a string containing the descriptive version of the
           current zope installation"""

    def getPythonVersion():
        """Return an unicode string containing verbose description
           of the python interpreter"""

    def getPythonPath():
        """Return a tuple containing an unicode strings containing
           the lookup paths of the python interpreter"""

    def getSystemPlatform():
        """Return an unicode string containing the system platform name
        """

    def getCommandLine():
        """Return the command line string Zope was invoked with"""

    def getProcessId():
        """Return the process id number currently serving the request"""

    def getUptime():
        """Return the Zope server uptime in seconds"""


class IZopeVersion(Interface):
    """ Zope version """

    def getZopeVersion():
        """Return a string containing the Zope version (possibly including
           SVN information)"""


class IServerControl(Interface):
    """Defines methods for shutting down and restarting the server.

    This utility also keeps a registry of things to call when shutting down
    zope. You can register using this interface or the zcml on the global
    ServerController instance.
    """

    def shutdown(time=0):
        """Shutdown the server.

        The `time` should be greater-equal 0.

        If the `time` is 0, then we do a hard shutdown, i.e. closing
        all sockets without waiting for tasks to complete.

        If the `time` is not 0, then we will give the tasks `time` seconds to
        finish before shutting down.
        """

    def restart(time=0):
        """Restart the server.

        The `time` should be greater-equal 0.

        If the `time` is 0, then we do a hard shutdown, i.e. closing
        all sockets without waiting for tasks to complete.

        If the `time` is not 0, then we will give the tasks `time` seconds to
        finish before shutting down.
        """
