=====================
Generic API Doc Views
=====================

Get a browser started:

  >>> from zope.testbrowser.testing import Browser
  >>> browser = Browser()
  >>> browser.addHeader('Authorization', 'Basic mgr:mgrpw')


Not Found View
--------------

The `APIDOC` skin defines a custom not found view, since it fits the look and
feel better and does not have all the O-wrap clutter:

  >>> browser.open('http://localhost/++apidoc++/non-existent/')
  Traceback (most recent call last):
  ...
  HTTPError: HTTP Error 404: Not Found

  >>> from urllib2 import HTTPError
  >>> try:
  ...     browser.open('http://localhost/++apidoc++/non-existent/')
  ... except HTTPError, error:
  ...     pass

  >>> print browser.contents
  <...
  <h1 class="details-header">
    Page Not Found
  </h1>
  <BLANKLINE>
  <p>
    While broken links occur occassionally, they are considered bugs. Please
    report any broken link to
    <a href="mailto:zope-dev@zope.org">zope-dev@zope.org</a>.
  </p>
  ...

