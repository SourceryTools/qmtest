##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Plugin Vocabulary.

This vocabulary provides terms for authentication utility plugins.

$Id: vocabulary.py 73548 2007-03-25 09:05:22Z dobe $
"""
__docformat__ = "reStructuredText"

import zope.dublincore.interfaces
from zope import interface, component, i18n
from zope.schema import vocabulary
from zope.schema.interfaces import IVocabularyFactory

from zope.app.authentication.i18n import ZopeMessageFactory as _

from zope.app.authentication import interfaces

UTILITY_TITLE = _(
    'zope.app.authentication.vocabulary-utility-plugin-title',
    '${name} (a utility)')
CONTAINED_TITLE = _(
    'zope.app.authentication.vocabulary-contained-plugin-title',
    '${name} (in contents)')
MISSING_TITLE = _(
    'zope.app.authentication.vocabulary-missing-plugin-title',
    '${name} (not found; deselecting will remove)')

def _pluginVocabulary(context, interface, attr_name):
    """Vocabulary that provides names of plugins of a specified interface.

    Given an interface, the options should include the unique names of all of
    the plugins that provide the specified interface for the current context--
    which is expected to be a pluggable authentication utility, hereafter
    referred to as a PAU).

    These plugins may be objects contained within the PAU ("contained
    plugins"), or may be utilities registered for the specified
    interface, found in the context of the PAU ("utility plugins").
    Contained plugins mask utility plugins of the same name.

    The vocabulary also includes the current values of the PAU even if they do
    not correspond to a contained or utility plugin.
    """
    terms = {}
    isPAU = interfaces.IPluggableAuthentication.providedBy(context)
    if isPAU:
        for k, v in context.items():
            if interface.providedBy(v):
                dc = zope.dublincore.interfaces.IDCDescriptiveProperties(
                    v, None)
                if dc is not None and dc.title:
                    title = dc.title
                else:
                    title = k
                terms[k] = vocabulary.SimpleTerm(
                    k, k.encode('base64').strip(), i18n.Message(
                        CONTAINED_TITLE, mapping={'name': title}))
    utils = component.getUtilitiesFor(interface, context)
    for nm, util in utils:
        if nm not in terms:
            terms[nm] = vocabulary.SimpleTerm(
                nm, nm.encode('base64').strip(), i18n.Message(
                    UTILITY_TITLE, mapping={'name': nm}))
    if isPAU:
        for nm in set(getattr(context, attr_name)):
            if nm not in terms:
                terms[nm] = vocabulary.SimpleTerm(
                    nm, nm.encode('base64').strip(), i18n.Message(
                        MISSING_TITLE, mapping={'name': nm}))
    return vocabulary.SimpleVocabulary(
        [term for nm, term in sorted(terms.items())])

def authenticatorPlugins(context):
    return _pluginVocabulary(
        context, interfaces.IAuthenticatorPlugin, 'authenticatorPlugins')

interface.alsoProvides(authenticatorPlugins, IVocabularyFactory)

def credentialsPlugins(context):
    return _pluginVocabulary(
        context, interfaces.ICredentialsPlugin, 'credentialsPlugins')

interface.alsoProvides(credentialsPlugins, IVocabularyFactory)
