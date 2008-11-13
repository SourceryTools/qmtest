======
README
======

This package provides an error reporting utility which is able to store errors.
Let's create one:

  >>> from zope.error.error import ErrorReportingUtility
  >>> util = ErrorReportingUtility()
  >>> util
  <zope.error.error.ErrorReportingUtility object at ...>
  
  >>> from zope.error.interfaces import IErrorReportingUtility
  >>> IErrorReportingUtility.providedBy(util)
  True
