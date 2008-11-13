##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Helper base class that picks principal ids

$Id: idpicker.py 73548 2007-03-25 09:05:22Z dobe $
"""
__docformat__ = 'restructuredtext'

import re
from zope.exceptions.interfaces import UserError
from zope.app.container.contained import NameChooser
from zope.app.authentication.i18n import ZopeMessageFactory as _

ok = re.compile('[!-~]+$').match
class IdPicker(NameChooser):
    """Helper base class that picks principal ids.

    Add numbers to ids given by users to make them unique.

    The Id picker is a variation on the name chooser that picks numeric
    ids when no name is given.

      >>> from zope.app.authentication.idpicker import IdPicker
      >>> IdPicker({}).chooseName('', None)
      u'1'

      >>> IdPicker({'1': 1}).chooseName('', None)
      u'2'

      >>> IdPicker({'2': 1}).chooseName('', None)
      u'1'

      >>> IdPicker({'1': 1}).chooseName('bob', None)
      u'bob'

      >>> IdPicker({'bob': 1}).chooseName('bob', None)
      u'bob1'

    """
    def chooseName(self, name, object):
        i = 0
        name = unicode(name)
        orig = name
        while (not name) or (name in self.context):
            i += 1
            name = orig+str(i)

        self.checkName(name, object)
        return name

    def checkName(self, name, object):
        """Limit ids

        Ids can only contain printable, non-space, 7-bit ASCII strings:

        >>> from zope.app.authentication.idpicker import IdPicker
        >>> IdPicker({}).checkName(u'1', None)
        True

        >>> IdPicker({}).checkName(u'bob', None)
        True

        >>> IdPicker({}).checkName(u'bob\xfa', None)
        ... # doctest: +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        UserError: Ids must contain only printable
        7-bit non-space ASCII characters

        >>> IdPicker({}).checkName(u'big bob', None)
        ... # doctest: +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        UserError: Ids must contain only printable
        7-bit non-space ASCII characters

        Ids also can't be over 100 characters long:

        >>> IdPicker({}).checkName(u'x' * 100, None)
        True

        >>> IdPicker({}).checkName(u'x' * 101, None)
        Traceback (most recent call last):
        ...
        UserError: Ids can't be more than 100 characters long.

        """
        NameChooser.checkName(self, name, object)
        if not ok(name):
            raise UserError(
                _("Ids must contain only printable 7-bit non-space"
                  " ASCII characters")
                )
        if len(name) > 100:
            raise UserError(
                _("Ids can't be more than 100 characters long.")
                )
        return True
