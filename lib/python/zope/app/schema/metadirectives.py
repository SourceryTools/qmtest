##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Renderer configuration code

$Id: metadirectives.py 69358 2006-08-05 17:54:32Z flox $
"""
from zope.configuration.fields import GlobalObject
from zope.interface import Interface
from zope.schema import TextLine

# BBB 2006/02/24, to be removed after 12 months
class IVocabularyDirective(Interface):
    '''
    *BBB: DEPRECATED*

    The 'vocabulary' directive has been deprecated and will be
    removed in Zope 3.5.  Use the 'utility' directive instead to
    register the class as a named utility:

    Example::

      <utility
          provides="zope.schema.interfaces.IVocabularyFactory"
          component="zope.app.gary.paths.Favorites"
          name="garys-favorite-path-references"
          />

    **Previous documentation**

    Define a named vocabulary.

    This associates a vocabulary name in the global vocabulary registry with a
    factory.  Each name may only be defined once.

    Additional keyword arguments may be passed to the factory by adding
    additional attributes beyond those listed here.  This can be useful when
    using vocabularies which implement various kinds of filtering.

    Example::

       <vocabulary
           name="garys-favorite-path-references"
           factory="zope.app.gary.paths.Favorites" />
    '''

    name = TextLine(
        title=u"Name",
        description=u'Provides a title for the source type. The name of the ' \
                    u'vocabulary; this can be used as the value for the ' \
                    u'"vocabulary" argument to the Choice field ' \
                    u'constructor to cause this vocabulary to be used.',
        required=True)

    factory = GlobalObject(
        title=u"Factory",
        description=u"Factory that returns an instance of the named " \
                    u"vocabulary when called with the context object as " \
                    u"the only argument.  This should be a dotted-name " \
                    u"that refers to a Python object.",
        required=True)


# Arbitrary keys and values are allowed to be passed to the vocabulary source.
IVocabularyDirective.setTaggedValue('keyword_arguments', True)
