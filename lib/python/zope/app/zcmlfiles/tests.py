import unittest
from zope.testing.doctestunit import DocTestSuite

def test_include():
    """
    >>> from zope.configuration import xmlconfig, config
    >>> context = config.ConfigurationMachine()
    >>> xmlconfig.registerCommonDirectives(context)
    >>> import zope.app.zcmlfiles

    >>> import warnings
    >>> showwarning = warnings.showwarning
    >>> warnings.showwarning = lambda *a, **k: None

    >>> xmlconfig.include(context, package=zope.app.zcmlfiles)

    >>> xmlconfig.include(context, 'configure.zcml', zope.app.zcmlfiles)
    >>> xmlconfig.include(context, 'ftesting.zcml', zope.app.zcmlfiles)
    >>> xmlconfig.include(context, 'menus.zcml', zope.app.zcmlfiles)
    >>> xmlconfig.include(context, 'meta.zcml', zope.app.zcmlfiles)
    >>> xmlconfig.include(context,
    ...     'file_not_exists.zcml', zope.app.zcmlfiles) #doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    IOError: ...

    >>> warnings.showwarning = showwarning
    """

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
