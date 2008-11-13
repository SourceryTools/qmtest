from unittest import TestCase, defaultTestLoader

class Test(TestCase):
    def test_succeed(self):
        # always succeeding
        pass

def test_suite():
    return defaultTestLoader.loadTestsFromTestCase(Test)
