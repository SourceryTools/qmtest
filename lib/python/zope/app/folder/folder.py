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
"""The standard Zope Folder.

$Id: folder.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from BTrees.OOBTree import OOBTree
from interfaces import IFolder, IRootFolder
from persistent import Persistent
from zope.app.container.contained import Contained, setitem, uncontained
from zope.app.component.interfaces import ISite
from zope.app.component.site import SiteManagerContainer
from zope.exceptions import DuplicationError
from zope.interface import implements, directlyProvides

class Folder(Persistent, SiteManagerContainer, Contained):
    """The standard Zope Folder implementation."""

    implements(IFolder)

    def __init__(self):
        self.data = OOBTree()

    def keys(self):
        """Return a sequence-like object containing the names
           associated with the objects that appear in the folder
        """
        return self.data.keys()

    def __iter__(self):
        return iter(self.data.keys())

    def values(self):
        """Return a sequence-like object containing the objects that
           appear in the folder.
        """
        return self.data.values()

    def items(self):
        """Return a sequence-like object containing tuples of the form
           (name, object) for the objects that appear in the folder.
        """
        return self.data.items()

    def __getitem__(self, name):
        """Return the named object, or raise ``KeyError`` if the object
           is not found.
        """
        return self.data[name]

    def get(self, name, default=None):
        """Return the named object, or the value of the `default`
           argument if the object is not found.
        """
        return self.data.get(name, default)

    def __contains__(self, name):
        """Return true if the named object appears in the folder."""
        return self.data.has_key(name)

    def __len__(self):
        """Return the number of objects in the folder."""
        return len(self.data)

    def __setitem__(self, name, object):
        """Add the given object to the folder under the given name."""

        if not (isinstance(name, str) or isinstance(name, unicode)):
            raise TypeError("Name must be a string rather than a %s" %
                            name.__class__.__name__)
        try:
            unicode(name)
        except UnicodeError:
            raise TypeError("Non-unicode names must be 7-bit-ascii only")
        if not name:
            raise TypeError("Name must not be empty")

        if name in self.data:
            raise DuplicationError("name, %s, is already in use" % name)

        setitem(self, self.data.__setitem__, name, object)

    def __delitem__(self, name):
        """Delete the named object from the folder. Raises a KeyError
           if the object is not found."""
        uncontained(self.data[name], self, name)
        del self.data[name]

def rootFolder():
    f = Folder()
    directlyProvides(f, IRootFolder)
    return f

class FolderSublocations(object):
    """Get the sublocations of a folder

    The subobjects of a folder include it's contents and it's site manager if
    it is a site.

      >>> folder = Folder()
      >>> folder['ob1'] = Contained()
      >>> folder['ob2'] = Contained()
      >>> folder['ob3'] = Contained()
      >>> subs = list(FolderSublocations(folder).sublocations())
      >>> subs.remove(folder['ob1'])
      >>> subs.remove(folder['ob2'])
      >>> subs.remove(folder['ob3'])
      >>> subs
      []

      >>> sm = Contained()
      >>> from zope.component.interfaces import IComponentLookup
      >>> directlyProvides(sm, IComponentLookup)
      >>> folder.setSiteManager(sm)
      >>> directlyProvides(folder, ISite)
      >>> subs = list(FolderSublocations(folder).sublocations())
      >>> subs.remove(folder['ob1'])
      >>> subs.remove(folder['ob2'])
      >>> subs.remove(folder['ob3'])
      >>> subs.remove(sm)
      >>> subs
      []
    """

    def __init__(self, folder):
        self.folder = folder

    def sublocations(self):
        folder = self.folder
        for key in folder:
            yield folder[key]

        if ISite.providedBy(folder):
            yield folder.getSiteManager()
