import persistent
import zope.interface

from zope.minmax import interfaces

class AbstractValue(persistent.Persistent):

    zope.interface.implements(interfaces.IAbstractValue)

    def __init__(self, value=None):
        self.value = value

    def __getstate__(self):
        return self.value

    def __setstate__(self, value):
        self.value = value

    def __nonzero__(self):
        return bool(self.value)

    def _p_resolveConflict(self, old, commited, new):
        raise NotImplementedError()

class Maximum(AbstractValue):
    def _p_resolveConflict(self, old, commited, new):
        # including old does not seem logical but it's open to discussion
        return max(commited, new)

class Minimum(AbstractValue):
    def _p_resolveConflict(self, old, commited, new):
        # including old does not seem logical but it's open to discussion
        return min(commited, new)
