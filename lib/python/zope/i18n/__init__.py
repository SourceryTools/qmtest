##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""i18n support.

$Id: __init__.py 68769 2006-06-20 10:19:22Z hdima $
"""
import re

from zope.i18nmessageid import MessageFactory, Message
from zope.i18n.interfaces import ITranslationDomain
from zope.i18n.interfaces import IFallbackTranslationDomainFactory
from zope.component import queryUtility


# Set up regular expressions for finding interpolation variables in text.
# NAME_RE must exactly match the expression of the same name in the
# zope.tal.taldefs module:
NAME_RE = r"[a-zA-Z][-a-zA-Z0-9_]*"

_interp_regex = re.compile(r'(?<!\$)(\$(?:(%(n)s)|{(%(n)s)}))'
    % ({'n': NAME_RE}))

def translate(msgid, domain=None, mapping=None, context=None,
               target_language=None, default=None):
    """Translate text.

    First setup some test components:

    >>> from zope import component, interface
    >>> import zope.i18n.interfaces

    >>> class TestDomain:
    ...     interface.implements(zope.i18n.interfaces.ITranslationDomain)
    ...
    ...     def __init__(self, **catalog):
    ...         self.catalog = catalog
    ...
    ...     def translate(self, text, *_, **__):
    ...         return self.catalog[text]

    Normally, the translation system will use a domain utility:

    >>> component.provideUtility(TestDomain(eek=u'ook'), name='my.domain')
    >>> translate(u'eek', 'my.domain')
    u'ook'

    Normally, if no domain is given, or if there is no domain utility
    for the given domain, then the text isn't translated:

    >>> translate(u'eek')
    u'eek'

    Moreover the text will be converted to unicode:

    >>> translate('eek', 'your.domain')
    u'eek'

    A fallback domain factory can be provided. This is normally used
    for testing:

    >>> def fallback(domain=u''):
    ...     return TestDomain(eek=u'test-from-' + domain)
    >>> interface.directlyProvides(
    ...     fallback,
    ...     zope.i18n.interfaces.IFallbackTranslationDomainFactory,
    ...     )

    >>> component.provideUtility(fallback)

    >>> translate(u'eek')
    u'test-from-'

    >>> translate(u'eek', 'your.domain')
    u'test-from-your.domain'
    """

    if isinstance(msgid, Message):
        domain = msgid.domain
        default = msgid.default
        mapping = msgid.mapping

    if default is None:
        default = unicode(msgid)

    if domain:
        util = queryUtility(ITranslationDomain, domain)
        if util is None:
            util = queryUtility(IFallbackTranslationDomainFactory)
            if util is not None:
                util = util(domain)
    else:
        util = queryUtility(IFallbackTranslationDomainFactory)
        if util is not None:
            util = util()

    if util is None:
        return interpolate(default, mapping)

    return util.translate(msgid, mapping, context, target_language, default)

def interpolate(text, mapping=None):
    """Insert the data passed from mapping into the text.

    First setup a test mapping:

    >>> mapping = {"name": "Zope", "version": 3}

    In the text we can use substitution slots like $varname or ${varname}:

    >>> interpolate(u"This is $name version ${version}.", mapping)
    u'This is Zope version 3.'

    Interpolation variables can be used more than once in the text:

    >>> interpolate(u"This is $name version ${version}. ${name} $version!",
    ...             mapping)
    u'This is Zope version 3. Zope 3!'

    In case if the variable wasn't found in the mapping or '$$' form
    was used no substitution will happens:

    >>> interpolate(u"This is $name $version. $unknown $$name $${version}.",
    ...             mapping)
    u'This is Zope 3. $unknown $$name $${version}.'

    >>> interpolate(u"This is ${name}")
    u'This is ${name}'
    """

    def replace(match):
        whole, param1, param2 = match.groups()
        return unicode(mapping.get(param1 or param2, whole))

    if not text or not mapping:
        return text

    return _interp_regex.sub(replace, text)
