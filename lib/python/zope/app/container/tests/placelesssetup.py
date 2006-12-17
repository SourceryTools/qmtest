##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Unit test logic for setting up and tearing down basic infrastructure

$Id: placelesssetup.py 29143 2005-02-14 22:43:16Z srichter $
"""
from zope.app.testing import ztapi
from zope.app.container.interfaces import IWriteContainer, INameChooser
from zope.app.container.contained import NameChooser

class PlacelessSetup(object):

    def setUp(self):
        ztapi.provideAdapter(IWriteContainer, INameChooser, NameChooser)
