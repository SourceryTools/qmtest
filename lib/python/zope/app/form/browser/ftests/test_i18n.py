##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Test form i18n

$Id: test_i18n.py 69217 2006-07-20 03:56:26Z baijum $
"""
import unittest
from zope.testing import doctest
from persistent import Persistent
from zope.interface import Interface, implements
from zope.schema import TextLine, Text, Int, List
from zope.i18nmessageid import MessageFactory
from zope.app.testing.functional import FunctionalDocFileSuite

_ = MessageFactory('formtest')

__docformat__ = "reStructuredText"

class IFieldContent(Interface):

    title = TextLine(
        title=_(u"Title"),
        description=_(u"A short description of the event."),
        default=u"",
        required=True
        )

    description = Text(
        title=_(u"Description"),
        description=_(u"A long description of the event."),
        default=u"",
        required=False
        )

    somenumber = Int(
        title=_(u"Some number"),
        default=0,
        required=False
        )

    somelist = List(
        title=_(u"Some List"),
        value_type=TextLine(title=_(u"Some item")),
        default=[],
        required=False
        )

class FieldContent(Persistent):
    implements(IFieldContent)

def test_suite():
    return unittest.TestSuite([
        FunctionalDocFileSuite('i18n.txt', package='zope.app.form.browser',
                               optionflags=doctest.ELLIPSIS)
        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
