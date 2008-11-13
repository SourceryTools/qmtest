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
"""Virtual File System interfaces for the publisher.

$Id: ftp.py 25177 2004-06-02 13:17:31Z jim $
"""
from zope.component.interfaces import IPresentation
from zope.component.interfaces import IView

from zope.publisher.interfaces.ftp import IFTPPublisher

class IFTPPresentation(IPresentation):
    """FTP presentations"""


class IFTPView(IFTPPresentation, IView):
    "FTP View"


class IFTPDirectoryPublisher(IFTPPublisher, IFTPView):

    def type(name):
        """Return the file type at the given name

        The return valie is 'd', for a directory, 'f', for a file, and
        None if there is no file at the path.
        """

    def names(filter=None):
        """Return a sequence of the names in a directory

        If the filter is not None, include only those names for which
        the filter returns a true value.
        """

    def ls(filter=None):
        """Return a sequence of information objects

        Return item info objects (see lsinfo) for the files in a directory.

        If the filter is not None, include only those names for which
        the filter returns a true value.
        """
        return list(tuple(str, str))

    def readfile(name, outstream, start=0, end=None):
        """Outputs the file at name to a stream.

        Data are copied starting from start. If end is not None,
        data are copied up to end.

        """

    def lsinfo(name):
        """Return information for a unix-style ls listing for the path

        Data are returned as a dictionary containing the following keys:

        type

           The path type, either 'd' or 'f'.

        owner_name

           Defaults to "na". Must not include spaces.

        owner_readable

           defaults to True

        owner_writable

           defaults to True

        owner_executable

           defaults to True for directories and false otherwise.

        group_name

           Defaults to "na". Must not include spaces.

        group_readable

           defaults to True

        group_writable

           defaults to True

        group_executable

           defaults to True for directories and false otherwise.

        other_readable

           defaults to False

        other_writable

           defaults to False

        other_executable

           defaults to True for directories and false otherwise.

        mtime

           Optional time, as a datetime.

        nlinks

           The number of links. Defaults to 1.

        size

           The file size.  Defaults to 0.

        name

           The file name.
        """

    def mtime(name):
        """Return the modification time for the file

        Return None if it is unknown.
        """

    def size(name):
        """Return the size of the file at path
        """

    def mkdir(name):
        """Create a directory.
        """

    def remove(name):
        """Remove a file. Same as unlink.
        """

    def rmdir(name):
        """Remove a directory.
        """

    def rename(old, new):
        """Rename a file or directory.
        """

    def writefile(name, instream, start=None, end=None, append=False):
        """Write data to a file.

        If start or end is not None, then only part of the file is
        written. The remainder of the file is unchanged.
        If start or end are specified, they must ne non-negative.

        If end is None, then the file is truncated after the data are
        written.  If end is not None, parts of the file after end, if
        any, are unchanged.  If end is not None and there isn't enough
        data in instream to fill out the file, then the missing data
        are undefined.

        If neither start nor end are specified, then the file contents
        are overwritten.

        If start is specified and the file doesn't exist or is shorter
        than start, the file will contain undefined data before start.

        If append is true, start and end are ignored.
        """

    def writable(name):
        """Return boolean indicating whether a file at path is writable

        Note that a true value should be returned if the file doesn't
        exist but it's directory is writable.

        """
