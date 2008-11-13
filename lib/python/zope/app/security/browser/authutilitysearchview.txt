===========================================
The Query View for Authentication Utilities
===========================================

A regular authentication service will not provide the `ISourceQueriables`
interface, but it is a queriable itself, since it provides the simple
`getPrincipals(name)` method:

  >>> class Principal:
  ...     def __init__(self, id):
  ...         self.id = id

  >>> class MyAuthUtility:
  ...     data = {'jim': Principal(42), 'don': Principal(0),
  ...             'stephan': Principal(1)}
  ...
  ...     def getPrincipals(self, name):
  ...         return [principal
  ...                 for id, principal in self.data.items()
  ...                 if name in id]

Now that we have our queriable, we create the view for it:

  >>> from zope.app.security.browser.auth import AuthUtilitySearchView
  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()
  >>> view = AuthUtilitySearchView(MyAuthUtility(), request)

This allows us to render a search form.

  >>> print view.render('test') # doctest: +NORMALIZE_WHITESPACE
  <h4>principals.zcml</h4>
  <div class="row">
  <div class="label">
  Search String
  </div>
  <div class="field">
  <input type="text" name="test.searchstring" />
  </div>
  </div>
  <div class="row">
  <div class="field">
  <input type="submit" name="test.search" value="Search" />
  </div>
  </div>

If we ask for results:

  >>> view.results('test')

We don't get any, since we did not provide any. But if we give input:

  >>> request.form['test.searchstring'] = 'n'

we still don't get any:

  >>> view.results('test')

because we did not press the button. So let's press the button:

  >>> request.form['test.search'] = 'Search'

so that we now get results (!):

  >>> ids = list(view.results('test'))
  >>> ids.sort()
  >>> ids
  [0, 1]
