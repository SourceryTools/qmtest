import os
from zope.app.testing.functional import ZCMLLayer

AppContainerLayer = ZCMLLayer(
    os.path.join(os.path.split(__file__)[0], 'ftesting.zcml'),
    __name__, 'AppContainerLayer', allow_teardown=True)

