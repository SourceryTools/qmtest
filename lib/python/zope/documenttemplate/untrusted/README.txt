Untrusted Document Templates
============================

Untrusted document templates implement an untrusted interpreter for
the DTML language. Untrusted templates protect any data they're given.

  >>> from zope.documenttemplate.untrusted import UntrustedHTML

Consider a sample class, which allows access to attributes f1, f2, and name:

  >>> from zope.security.checker import NamesChecker
  >>> class C(object):
  ...     def __init__(self, name, **kw):
  ...         self.name = name
  ...         self.__dict__.update(kw)
  ...     def f1(self):
  ...         return 'f1 called'
  ...     def f2(self):
  ...         return 'f2 called'
  ...     __Security_checker__ = NamesChecker(['f1', 'f2', 'name'])

We can get at alowed data just fine:

  >>> UntrustedHTML('<dtml-var f1> <dtml-var name>')(C('bob'))
  'f1 called bob'

But we'll get an error if we try to access an attribute we're not
alowed to get:

  >>> UntrustedHTML('<dtml-var x>')(C('bob', x=1))
  Traceback (most recent call last):
  ...
  KeyError: 'x'

If we create data inside the template, we'll be allowed to manipulate
it:

  >>> UntrustedHTML('''
  ... <dtml-let data="[]">
  ...    <dtml-call expr="data.append(1)"><dtml-var data>
  ... </dtml-let>
  ... ''')()
  '\n   [1]\n'

but any attributes we get from data we create are proxied, and
this protected:

  >>> UntrustedHTML('''
  ... <dtml-let data="[]">
  ...    <dtml-with data><dtml-with __class__><dtml-var __dict__>
  ...    </dtml-with></dtml-with>
  ... </dtml-let>
  ... ''')()
  Traceback (most recent call last):
  ...
  KeyError: '__dict__'

  >>> UntrustedHTML('''
  ... <dtml-let data="[]">
  ...    <dtml-var expr="data.__class__.__dict__">
  ... </dtml-let>
  ... ''')()
  Traceback (most recent call last):
  ...
  ForbiddenAttribute: ('__dict__', <type 'list'>)

  >>> UntrustedHTML('''<dtml-var expr="'foo'.__class__.__dict__">''')()
  Traceback (most recent call last):
  ...
  ForbiddenAttribute: ('__dict__', <type 'str'>)

Access is provided to a number of utility functions provided by the
template dict, but not to hidden functions:

  >>> UntrustedHTML('''<dtml-var expr="_.abs(-1)">''')()
  '1'

But not to privare attributes:

  >>> UntrustedHTML('''<dtml-var expr="_._pop()">''')()
  Traceback (most recent call last):
  ...
  ForbiddenAttribute: ('_pop', <an UntrustedTemplateDict>)
  
