import os
from zope.app.testing import functional

TraversingLayer = functional.ZCMLLayer(
    os.path.join(os.path.split(__file__)[0], 'ftesting.zcml'),
    __name__, 'TraversingLayer', allow_teardown=True)


