============
Vocabularies
============

The vocabulary module provides vocabularies for the authenticator plugins and
the credentials plugins.

The options should include the unique names of all of the plugins that provide
the appropriate interface (interfaces.ICredentialsPlugin or
interfaces.IAuthentiatorPlugin, respectively) for the current context-- which
is expected to be a pluggable authentication utility, hereafter referred to as
a PAU.

These names may be for objects contained within the PAU ("contained
plugins"), or may be utilities registered for the specified interface,
found in the context of the PAU ("utility plugins").  Contained
plugins mask utility plugins of the same name.  They also may be names
currently selected in the PAU that do not actually have a
corresponding plugin at this time.

Here is a short example of how the vocabulary should work.  Let's say we're
working with authentication plugins.  We'll create some faux
authentication plugins, and register some of them as utilities and put
others in a faux PAU.

    >>> from zope.app.authentication import interfaces
    >>> from zope import interface, component
    >>> class DemoPlugin(object):
    ...     interface.implements(interfaces.IAuthenticatorPlugin)
    ...     def __init__(self, name):
    ...         self.name = name
    ...
    >>> utility_plugins = dict(
    ...     (i, DemoPlugin(u'Plugin %d' % i)) for i in range(4))
    >>> contained_plugins = dict(
    ...     (i, DemoPlugin(u'Plugin %d' % i)) for i in range(1, 5))
    >>> sorted(utility_plugins.keys())
    [0, 1, 2, 3]
    >>> for p in utility_plugins.values():
    ...     component.provideUtility(p, name=p.name)
    ...
    >>> sorted(contained_plugins.keys()) # 1 will mask utility plugin 1
    [1, 2, 3, 4]
    >>> class DemoAuth(dict):
    ...     interface.implements(interfaces.IPluggableAuthentication)
    ...     def __init__(self, *args, **kwargs):
    ...         super(DemoAuth, self).__init__(*args, **kwargs)
    ...         self.authenticatorPlugins = (u'Plugin 3', u'Plugin X')
    ...         self.credentialsPlugins = (u'Plugin 4', u'Plugin X')
    ...
    >>> auth = DemoAuth((p.name, p) for p in contained_plugins.values())

    >>> @component.adapter(interface.Interface)
    ... @interface.implementer(component.IComponentLookup)
    ... def getSiteManager(context):
    ...     return component.getGlobalSiteManager()
    ...
    >>> component.provideAdapter(getSiteManager)

We are now ready to create a vocabulary that we can use.  The context is
our faux authentication utility, `auth`.

    >>> from zope.app.authentication import vocabulary
    >>> vocab = vocabulary.authenticatorPlugins(auth)

Iterating over the vocabulary results in all of the terms, in a relatively
arbitrary order of their names.  (This vocabulary should typically use a
widget that sorts values on the basis of localized collation order of the
term titles.)

    >>> [term.value for term in vocab] # doctest: +NORMALIZE_WHITESPACE
    [u'Plugin 0', u'Plugin 1', u'Plugin 2', u'Plugin 3', u'Plugin 4',
     u'Plugin X']

Similarly, we can use `in` to test for the presence of values in the
vocabulary.

    >>> ['Plugin %s' % i in vocab for i in range(-1, 6)]
    [False, True, True, True, True, True, False]
    >>> 'Plugin X' in vocab
    True

The length reports the expected value.

    >>> len(vocab)
    6

One can get a term for a given value using `getTerm()`; its token, in
turn, should also return the same effective term from `getTermByToken`.

    >>> values = ['Plugin 0', 'Plugin 1', 'Plugin 2', 'Plugin 3', 'Plugin 4',
    ...           'Plugin X']
    >>> for val in values:
    ...     term = vocab.getTerm(val)
    ...     assert term.value == val
    ...     term2 = vocab.getTermByToken(term.token)
    ...     assert term2.token == term.token
    ...     assert term2.value == val
    ...

The terms have titles, which are message ids that show the plugin title or id
and whether the plugin is a utility or just contained in the auth utility.
We'll give one of the plugins a dublin core title just to show the
functionality.

    >>> import zope.dublincore.interfaces
    >>> class ISpecial(interface.Interface):
    ...     pass
    ...
    >>> interface.directlyProvides(contained_plugins[1], ISpecial)
    >>> class DemoDCAdapter(object):
    ...     interface.implements(
    ...         zope.dublincore.interfaces.IDCDescriptiveProperties)
    ...     component.adapts(ISpecial)
    ...     def __init__(self, context):
    ...         pass
    ...     title = u'Special Title'
    ...
    >>> component.provideAdapter(DemoDCAdapter)

We need to regenerate the vocabulary, since it calculates all of its data at
once.

    >>> vocab = vocabulary.authenticatorPlugins(auth)

Now we'll check the titles.  We'll have to translate them to see what we
expect.

    >>> from zope import i18n
    >>> import pprint
    >>> pprint.pprint([i18n.translate(term.title) for term in vocab])
    [u'Plugin 0 (a utility)',
     u'Special Title (in contents)',
     u'Plugin 2 (in contents)',
     u'Plugin 3 (in contents)',
     u'Plugin 4 (in contents)',
     u'Plugin X (not found; deselecting will remove)']

credentialsPlugins
------------------

For completeness, we'll do the same review of the credentialsPlugins.

    >>> class DemoPlugin(object):
    ...     interface.implements(interfaces.ICredentialsPlugin)
    ...     def __init__(self, name):
    ...         self.name = name
    ...
    >>> utility_plugins = dict(
    ...     (i, DemoPlugin(u'Plugin %d' % i)) for i in range(4))
    >>> contained_plugins = dict(
    ...     (i, DemoPlugin(u'Plugin %d' % i)) for i in range(1, 5))
    >>> for p in utility_plugins.values():
    ...     component.provideUtility(p, name=p.name)
    ...
    >>> auth = DemoAuth((p.name, p) for p in contained_plugins.values())
    >>> vocab = vocabulary.credentialsPlugins(auth)

Iterating over the vocabulary results in all of the terms, in a relatively
arbitrary order of their names.  (This vocabulary should typically use a
widget that sorts values on the basis of localized collation order of the term
titles.) Similarly, we can use `in` to test for the presence of values in the
vocabulary. The length reports the expected value.

    >>> [term.value for term in vocab] # doctest: +NORMALIZE_WHITESPACE
    [u'Plugin 0', u'Plugin 1', u'Plugin 2', u'Plugin 3', u'Plugin 4',
     u'Plugin X']
    >>> ['Plugin %s' % i in vocab for i in range(-1, 6)]
    [False, True, True, True, True, True, False]
    >>> 'Plugin X' in vocab
    True
    >>> len(vocab)
    6

One can get a term for a given value using `getTerm()`; its token, in
turn, should also return the same effective term from `getTermByToken`.

    >>> values = ['Plugin 0', 'Plugin 1', 'Plugin 2', 'Plugin 3', 'Plugin 4',
    ...           'Plugin X']
    >>> for val in values:
    ...     term = vocab.getTerm(val)
    ...     assert term.value == val
    ...     term2 = vocab.getTermByToken(term.token)
    ...     assert term2.token == term.token
    ...     assert term2.value == val
    ...

The terms have titles, which are message ids that show the plugin title or id
and whether the plugin is a utility or just contained in the auth utility.
We'll give one of the plugins a dublin core title just to show the
functionality. We need to regenerate the vocabulary, since it calculates all
of its data at once. Then we'll check the titles.  We'll have to translate
them to see what we expect.

    >>> interface.directlyProvides(contained_plugins[1], ISpecial)
    >>> vocab = vocabulary.credentialsPlugins(auth)
    >>> pprint.pprint([i18n.translate(term.title) for term in vocab])
    [u'Plugin 0 (a utility)',
     u'Special Title (in contents)',
     u'Plugin 2 (in contents)',
     u'Plugin 3 (in contents)',
     u'Plugin 4 (in contents)',
     u'Plugin X (not found; deselecting will remove)']
