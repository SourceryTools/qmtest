##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Test folders

$Id: folder.py 67728 2006-04-28 17:57:47Z regebro $
"""
from OFS.Folder import Folder
from OFS.interfaces import IFolder
from zope.interface import implements

class NoVerifyPasteFolder(Folder):
    """Folder that does not perform paste verification.
    Used by test_events
    """
    def _verifyObjectPaste(self, object, validate_src=1):
        pass

def manage_addNoVerifyPasteFolder(container, id, title=''):
    container._setObject(id, NoVerifyPasteFolder())
    folder = container[id]
    folder.id = id
    folder.title = title

class FiveTraversableFolder(Folder):
    """Folder that is five-traversable
    """
    implements(IFolder)

def manage_addFiveTraversableFolder(container, id, title=''):
    container._setObject(id, FiveTraversableFolder())
    folder = container[id]
    folder.id = id
    folder.title = title
