##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Location copying/pickling support

$Id: pickling.py 66534 2006-04-05 14:09:33Z philikon $
"""
__docformat__ = 'restructuredtext'

import cPickle
import tempfile
import zope.interface
from zope.traversing.interfaces import IContainmentRoot
from zope.traversing.interfaces import ITraverser

from zope.location.interfaces import ILocation
from zope.location.location import Location, inside
from zope.location.traversing import LocationPhysicallyLocatable

def locationCopy(loc):
    r"""Return a copy of an object, and anything in it

    If object in the location refer to objects outside of the
    location, then the copies of the objects in the location refer to
    the same outside objects.

    For example, suppose we have an object (location) hierarchy like this::

           o1
          /  \
        o2    o3
        |     |
        o4    o5

    >>> o1 = Location()
    >>> o1.o2 = Location(); o1.o2.__parent__ = o1
    >>> o1.o3 = Location(); o1.o3.__parent__ = o1
    >>> o1.o2.o4 = Location(); o1.o2.o4.__parent__ = o1.o2
    >>> o1.o3.o5 = Location(); o1.o3.o5.__parent__ = o1.o3

    In addition, o3 has a non-location reference to o4.

    >>> o1.o3.o4 = o1.o2.o4

    When we copy o3, we should get a copy of o3 and o5, with
    references to o1 and o4.

    >>> c3 = locationCopy(o1.o3)
    >>> c3 is o1.o3
    0
    >>> c3.__parent__ is o1
    1
    >>> c3.o5 is o1.o3.o5
    0
    >>> c3.o5.__parent__ is c3
    1
    >>> c3.o4 is o1.o2.o4
    1

    """
    tmp = tempfile.TemporaryFile()
    persistent = CopyPersistent(loc)

    # Pickle the object to a temporary file
    pickler = cPickle.Pickler(tmp, 2)
    pickler.persistent_id = persistent.id
    pickler.dump(loc)

    # Now load it back
    tmp.seek(0)
    unpickler = cPickle.Unpickler(tmp)
    unpickler.persistent_load = persistent.load

    return unpickler.load()


class CopyPersistent(object):
    """Persistence hooks for copying locations

    See `locationCopy` above.

    We get initialized with an initial location:

    >>> o1 = Location()
    >>> persistent = CopyPersistent(o1)

    We provide an `id` function that returns None when given a non-location:

    >>> persistent.id(42)

    Or when given a location that is inside the initial location:

    >>> persistent.id(o1)
    >>> o2 = Location(); o2.__parent__ = o1
    >>> persistent.id(o2)

    But, if we get a location outside the original location, we assign
    it an `id` and return the `id`:

    >>> o3 = Location()
    >>> id3 = persistent.id(o3)
    >>> id3 is None
    0
    >>> o4 = Location()
    >>> id4 = persistent.id(o4)
    >>> id4 is None
    0
    >>> id4 is id3
    0

    If we ask for the `id` of an outside location more than once, we
    always get the same `id` back:

    >> persistent.id(o4) == id4
    1

    We also provide a load function that returns the objects for which
    we were given ids:

    >>> persistent.load(id3) is o3
    1
    >>> persistent.load(id4) is o4
    1

    """

    def __init__(self, location):
        self.location = location
        self.pids_by_id = {}
        self.others_by_pid = {}
        self.load = self.others_by_pid.get

    def id(self, object):
        if ILocation.providedBy(object):
            if not inside(object, self.location):
                if id(object) in self.pids_by_id:
                    return self.pids_by_id[id(object)]
                pid = len(self.others_by_pid)

                # The following is needed to overcome a bug
                # in pickle.py. The pickle checks the boolean value
                # of the id, rather than whether it is None.
                pid += 1

                self.pids_by_id[id(object)] = pid
                self.others_by_pid[pid] = object
                return pid

        return None


class PathPersistent(object):
    """Persistence hooks for pickling locations

    See `locationCopy` above.

    Unlike copy persistent, we use paths for ids of outside locations
    so that we can separate pickling and unpickling in time.  We have
    to compute paths and traverse objects to load paths, but paths can
    be stored for later use, unlike the ids used by `CopyPersistent`.

    We require outside locations that can be adapted to `ITraversable`.
    To simplify the example, we'll use a simple traversable location
    defined in `zope.location.tests`, `TLocation`.

    Normally, general adapters are used to make objects traversable.

    We get initialized with an initial location:

    >>> o1 = Location()
    >>> persistent = PathPersistent(o1)

    We provide an id function that returns None when given a non-location:

    >>> persistent.id(42)

    Or when given a location that is inside the initial location:

    >>> persistent.id(o1)
    >>> o2 = Location(); o2.__parent__ = o1
    >>> persistent.id(o2)

    But, if we get a location outside the original location, we return it's
    path. To compute it's path, it must be rooted:

    >>> from zope.location.tests import TLocation
    >>> root = TLocation()
    >>> zope.interface.directlyProvides(root, IContainmentRoot)
    >>> o3 = TLocation(); o3.__name__ = 'o3'
    >>> o3.__parent__ = root; root.o3 = o3
    >>> persistent.id(o3)
    u'/o3'

    >>> o4 = TLocation(); o4.__name__ = 'o4'
    >>> o4.__parent__ = o3; o3.o4 = o4
    >>> persistent.id(o4)
    u'/o3/o4'


    We also provide a load function that returns objects by traversing
    given paths.  It has to find the root based on the object given to
    the constructor.  Therefore, that object must also be rooted:

    >>> o1.__parent__ = root
    >>> persistent.load(u'/o3') is o3
    1
    >>> persistent.load(u'/o3/o4') is o4
    1

    """

    def __init__(self, location):
        self.location = location

    def id(self, object):
        if ILocation.providedBy(object):
            if not inside(object, self.location):
                return LocationPhysicallyLocatable(object).getPath()

        return None

    def load(self, path):
        if path[:1] != u'/':
            raise ValueError("ZPersistent paths must be absolute", path)
        root = LocationPhysicallyLocatable(self.location).getRoot()
        return ITraverser(root).traverse(path[1:])
