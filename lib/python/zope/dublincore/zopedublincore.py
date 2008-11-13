##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Zope's Dublin Core Implementation

$Id: zopedublincore.py 66902 2006-04-12 20:16:30Z philikon $
"""
__docformat__ = 'restructuredtext'

from datetime import datetime

from zope.interface import implements
from zope.datetime import parseDatetimetz
from zope.dublincore.interfaces import IZopeDublinCore

class SimpleProperty(object):

    def __init__(self, name):
        self.__name__ = name

class ScalarProperty(SimpleProperty):

    def __get__(self, inst, klass):
        if inst is None:
            return self
        data = inst._mapping.get(self.__name__, ())
        if data:
            return data[0]
        else:
            return u''

    def __set__(self, inst, value):
        if not isinstance(value, unicode):
            raise TypeError("Element must be unicode")
        dict = inst._mapping
        __name__ = self.__name__
        inst._changed()
        dict[__name__] = (value, ) + dict.get(__name__, ())[1:]

def _scalar_get(inst, name):
    data = inst._mapping.get(name, ())
    if data:
        return data[0]
    else:
        return u''

class DateProperty(ScalarProperty):

    def __get__(self, inst, klass):
        if inst is None:
            return self
        data = inst._mapping.get(self.__name__, ())
        if data:
            return parseDatetimetz(data[0])
        else:
            return None

    def __set__(self, inst, value):
        if not isinstance(value, datetime):
            raise TypeError("Element must be %s", datetime)

        value = unicode(value.isoformat('T'), 'ascii')

        super(DateProperty, self).__set__(inst, value)


class SequenceProperty(SimpleProperty):

    def __get__(self, inst, klass):
        if inst is None:
            return self

        return inst._mapping.get(self.__name__, ())

    def __set__(self, inst, value):
        value = tuple(value)
        for v in value:
            if not isinstance(v, unicode):
                raise TypeError("Elements must be unicode")
        inst._changed()
        inst._mapping[self.__name__] = value

class ZopeDublinCore(object):
    """Zope Dublin Core Mixin

    Subclasses should define either `_changed()` or `_p_changed`.

    Just mix with `Persistence` to get a persistent version.
    """

    implements(IZopeDublinCore)

    def __init__(self, mapping=None):
        if mapping is None:
            mapping = {}
        self._mapping = mapping

    def _changed(self):
        self._p_changed = True

    title = ScalarProperty(u'Title')

    def Title(self):
        "See `IZopeDublinCore`"
        return self.title

    creators = SequenceProperty(u'Creator')

    def Creator(self):
        "See `IZopeDublinCore`"
        return self.creators

    subjects = SequenceProperty(u'Subject')

    def Subject(self):
        "See `IZopeDublinCore`"
        return self.subjects

    description = ScalarProperty(u'Description')

    def Description(self):
        "See `IZopeDublinCore`"
        return self.description

    publisher = ScalarProperty(u'Publisher')

    def Publisher(self):
        "See IZopeDublinCore"
        return self.publisher

    contributors = SequenceProperty(u'Contributor')

    def Contributors(self):
        "See `IZopeDublinCore`"
        return self.contributors

    def Date(self):
        "See IZopeDublinCore"
        return _scalar_get(self, u'Date')

    created = DateProperty(u'Date.Created')

    def CreationDate(self):
        "See `IZopeDublinCore`"
        return _scalar_get(self, u'Date.Created')

    effective = DateProperty(u'Date.Effective')

    def EffectiveDate(self):
        "See `IZopeDublinCore`"
        return _scalar_get(self, u'Date.Effective')

    expires = DateProperty(u'Date.Expires')

    def ExpirationDate(self):
        "See `IZopeDublinCore`"
        return _scalar_get(self, u'Date.Expires')

    modified = DateProperty(u'Date.Modified')

    def ModificationDate(self):
        "See `IZopeDublinCore`"
        return _scalar_get(self, u'Date.Modified')

    type = ScalarProperty(u'Type')

    def Type(self):
        "See `IZopeDublinCore`"
        return self.type

    format = ScalarProperty(u'Format')

    def Format(self):
        "See `IZopeDublinCore`"
        return self.format

    identifier = ScalarProperty(u'Identifier')

    def Identifier(self):
        "See `IZopeDublinCore`"
        return self.identifier

    language = ScalarProperty(u'Language')

    def Language(self):
        "See `IZopeDublinCore`"
        return self.language

    rights = ScalarProperty(u'Rights')

    def Rights(self):
        "See `IZopeDublinCore`"
        return self.rights

    def setQualifiedTitles(self, qualified_titles):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Title', qualified_titles)

    def setQualifiedCreators(self, qualified_creators):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Creator', qualified_creators)

    def setQualifiedSubjects(self, qualified_subjects):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Subject', qualified_subjects)

    def setQualifiedDescriptions(self, qualified_descriptions):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Description', qualified_descriptions)

    def setQualifiedPublishers(self, qualified_publishers):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Publisher', qualified_publishers)

    def setQualifiedContributors(self, qualified_contributors):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Contributor', qualified_contributors)

    def setQualifiedDates(self, qualified_dates):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Date', qualified_dates)

    def setQualifiedTypes(self, qualified_types):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Type', qualified_types)

    def setQualifiedFormats(self, qualified_formats):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Format', qualified_formats)

    def setQualifiedIdentifiers(self, qualified_identifiers):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Identifier', qualified_identifiers)

    def setQualifiedSources(self, qualified_sources):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Source', qualified_sources)

    def setQualifiedLanguages(self, qualified_languages):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Language', qualified_languages)

    def setQualifiedRelations(self, qualified_relations):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Relation', qualified_relations)

    def setQualifiedCoverages(self, qualified_coverages):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Coverage', qualified_coverages)

    def setQualifiedRights(self, qualified_rights):
        "See `IWritableDublinCore`"
        return _set_qualified(self, u'Rights', qualified_rights)

    def getQualifiedTitles(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Title')

    def getQualifiedCreators(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Creator')

    def getQualifiedSubjects(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Subject')

    def getQualifiedDescriptions(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Description')

    def getQualifiedPublishers(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Publisher')

    def getQualifiedContributors(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Contributor')

    def getQualifiedDates(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Date')

    def getQualifiedTypes(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Type')

    def getQualifiedFormats(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Format')

    def getQualifiedIdentifiers(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Identifier')

    def getQualifiedSources(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Source')

    def getQualifiedLanguages(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Language')

    def getQualifiedRelations(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Relation')

    def getQualifiedCoverages(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Coverage')

    def getQualifiedRights(self):
        "See `IStandardDublinCore`"
        return _get_qualified(self, u'Rights')


def _set_qualified(self, name, qvalue):
    data = {}
    dict = self._mapping

    for qualification, value in qvalue:
        data[qualification] = data.get(qualification, ()) + (value, )

    self._changed()
    for qualification, values in data.iteritems():
        qname = qualification and (name + '.' + qualification) or name
        dict[qname] = values

def _get_qualified(self, name):
    result = []
    for aname, avalue in self._mapping.iteritems():

        if aname == name:
            qualification = u''
            for value in avalue:
                result.append((qualification, value))

        elif aname.startswith(name):
            qualification = aname[len(name)+1:]
            for value in avalue:
                result.append((qualification, value))

    return tuple(result)


__doc__ = ZopeDublinCore.__doc__ + __doc__
