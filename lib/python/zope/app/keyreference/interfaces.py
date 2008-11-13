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
"""Key-reference interfaces

$Id: interfaces.py 67630 2006-04-27 00:54:03Z jim $
"""
import zope.interface
from zope.schema import DottedName
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('zope')


class NotYet(Exception):
    """Can't compute a key reference for an object

    It might be possible to compute one later
    (e.g. at the end of the transaction).
    """

class IKeyReference(zope.interface.Interface):
    """A reference to an object (similar to a weak reference).

    The references are compared by their hashes.
    """

    key_type_id = DottedName(title=_('Key Type Id'),
        description=_('Key references should sort first '
            'on their key type and second on any type-specific '
            'information.')
        )

    def __call__():
        """Get the object this reference is linking to.
        """

    def __hash__():
        """Get a unique identifier of the referenced object.
        """

    def __cmp__(ref):
        """Compare the reference to another reference.
        """
