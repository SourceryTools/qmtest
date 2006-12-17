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
"""Basic File interfaces.

$Id: interfaces.py 39064 2005-10-11 18:40:10Z philikon $
"""
__docformat__ = 'restructuredtext'

from zope.schema import BytesLine, Bytes
from zope.interface import Interface
from zope.app.i18n import ZopeMessageFactory as _


# BBB: To go away in 3.3
from zope.app.publication.interfaces import IFileContent
from zope.deprecation import deprecated
deprecated('IFileContent',
           '`IFileContent` has moved `zope.app.publication.interfaces`. '
           'This will go away in 3.3.')


class IFile(Interface):

    contentType = BytesLine(
        title = _(u'Content Type'),
        description=_(u'The content type identifies the type of data.'),
        default='',
        required=False,
        missing_value=''
        )

    data = Bytes(
        title=_(u'Data'),
        description=_(u'The actual content of the object.'),
        default='',
        missing_value='',
        required=False,
        )

    def getSize():
        """Return the byte-size of the data of the object."""

class IImage(IFile):
    """This interface defines an Image that can be displayed.
    """

    def getImageSize():
        """Return a tuple (x, y) that describes the dimensions of
        the object.
        """
