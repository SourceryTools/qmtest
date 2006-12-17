##############################################################################
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""File-system representation interfaces

The interfaces defined here are used for file-system and
file-system-like representations of objects, such as file-system
synchronization, FTP, PUT, and WebDAV.

There are three issues we need to deal with:

  File system representation

    Every object is either a directory or a file.

  Properties

    There are two kinds of proprties:

    - Data properties

      Data properties are handled directly by the object implementation.

    - Meta-data properties

      Meta data properties are handled via annotations.

  Completeness

    We must have a complete lossless data representation for file-system
    synchronization. This is achieved through serialization of:

    - All annotations (not just properties, and

    - Extra data.

  Strategies for common access mechanisms:

    FTP

      - For getting directory info (statish) information:

        - Use Zope DublinCore to get modification times

        - Show as readable if we can access a read method.

        - Show as writable if we can access a write method.

    FTP and WebDAV

      - Treat as a directory if there is an adapter to `IReadDirectory`.
        Treat as a file otherwise.

      - For creating objects:

        - Directories:

          Look for an `IDirectoryFactory` adapter.

        - Files

          First lookj for a `IFileFactory` adapter with a name that is
          the same as the extention (e.g. ".pt").

          Then look for an unnamed `IFileFactory` adapter.


    File-system synchronization

      Because this must be lossless, we will use class-based adapters
      for this, but we want to make it as easy as possible to use other
      adapters as well.

      For reading, there must be a class adapter to `IReadSync`.  We will
      then apply rules similar to those above.

$Id: interfaces.py 26746 2004-07-24 04:15:42Z pruggera $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface
from zope.app.container.interfaces import IReadContainer, IWriteContainer

class IReadFile(Interface):
    """Provide read access to file data
    """

    def read():
        """Return the file data
        """

    def size():
        """Return the data length
        """

class IWriteFile(Interface):

    def write(data):
        """Update the file data
        """

# TODO: We will add ILargeReadFile and ILargeWriteFile to efficiently
# handle large data.

class IReadDirectory(IReadContainer):
    """Objects that should be treated as directories for reading
    """

class IWriteDirectory(IWriteContainer):
    """Objects that should be treated as directories for writing
    """

class IDirectoryFactory(Interface):

    def __call__(name):
        """Create a directory

        where a directory is an object with adapters to IReadDirectory
        and IWriteDirectory.

        """

class IFileFactory(Interface):

    def __call__(name, content_type, data):
        """Create a file

        where a file is an object with adapters to `IReadFile`
        and `IWriteFile`.

        The file `name`, content `type`, and `data` are provided to help
        create the object.
        """

# TODO: we will add additional interfaces for WebDAV and File-system
# synchronization.
