from weakref import ref

from persistent.interfaces import IPersistent
from persistent.wref import (WeakRef, WeakRefMarker,
                             PersistentWeakKeyDictionary)

class wref(ref):
    def __reduce_ex__(self, proto):
        return _wref_reconstructor, ()

class Dummy(object): pass

def _wref_reconstructor():
    """Return a dead reference on reconstruction"""
    return wref(Dummy())

def getWeakRef(ob):
    """Get either a persistent or non-presistent weakref"""
    if IPersistent.providedBy(ob):
        return WeakRef(ob)
    else:
        return wref(ob)

class FlexibleWeakKeyDictionary(PersistentWeakKeyDictionary):

    def __setitem__(self, key, value):
        self.data[getWeakRef(key)] = value

    def __getitem__(self, key):
        return self.data[getWeakRef(key)]

    def __delitem__(self, key):
        del self.data[getWeakRef(key)]

    def get(self, key, default=None):
        return self.data.get(getWeakRef(key), default)

    def __contains__(self, key):
        return getWeakRef(key) in self.data

    def update(self, adict):
        if isinstance(adict, PersistentWeakKeyDictionary):
            self.data.update(adict.update)
        else:
            for k, v in adict.items():
                self.data[getWeakRef(k)] = v

    def keys(self):
        return [k() for k in self.data.keys()]

    def __len__(self):
        return len(self.data)
