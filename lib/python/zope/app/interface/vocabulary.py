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
"""Vocabulary that provides a list of all interfaces its context provides.

$Id: vocabulary.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.interface import classProvides, providedBy
from zope.security.proxy import removeSecurityProxy
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm 
from zope.schema.interfaces import IVocabularyFactory
from zope.component.interface import interfaceToName


class ObjectInterfacesVocabulary(SimpleVocabulary):
    """A vocabulary that provides a list of all interfaces that its context
    provides.

    Here a quick demonstration:

    >>> from zope.interface import Interface, implements
    >>> class I1(Interface):
    ...     pass
    >>> class I2(Interface):
    ...     pass
    >>> class I3(I2):
    ...     pass

    >>> class Object(object):
    ...     implements(I3, I1)

    >>> vocab = ObjectInterfacesVocabulary(Object())
    >>> import pprint
    >>> names = [term.token for term in vocab]
    >>> names.sort()
    >>> pprint.pprint(names)
    ['zope.app.interface.vocabulary.I1',
     'zope.app.interface.vocabulary.I2',
     'zope.app.interface.vocabulary.I3',
     'zope.interface.Interface']
    """
    classProvides(IVocabularyFactory)

    def __init__(self, context):
        # Remove the security proxy so the values from the vocabulary
        # are the actual interfaces and not proxies.
        component = removeSecurityProxy(context)
        interfaces = providedBy(component).flattened()
        terms = [SimpleTerm(interface, interfaceToName(context, interface))
                 for interface in interfaces]
        super(ObjectInterfacesVocabulary, self).__init__(terms)
