import persistent.interfaces
import zope.interface

class IAbstractValue(persistent.interfaces.IPersistent):
    """A persistent value with the conflict resolution.

    The values are expected to be homogeneous.
    """

    value = zope.interface.Attribute('The initial value')

    def __nonzero__():
        """Return Boolean cast of the value as True or False."""
