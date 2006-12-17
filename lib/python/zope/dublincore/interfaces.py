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
"""Dublin Core interfaces

$Id: interfaces.py 69636 2006-08-18 10:02:46Z faassen $
"""
__docformat__ = 'restructuredtext'

from zope.annotation.interfaces import IAnnotatable
from zope.interface import Interface
from zope.schema import Text, TextLine, Datetime, Tuple

class IDublinCoreElementItem(Interface):
    """A qualified dublin core element"""

    qualification = TextLine(
        title = u"Qualification",
        description = u"The element qualification"
        )

    value = Text(
        title = u"Value",
        description = u"The element value",
        )

class IGeneralDublinCore(Interface):
    """Dublin-core data access interface

    The Dublin Core, http://dublincore.org/, is a meta data standard
    that specifies a set of standard data elements. It provides
    flexibility of interpretation of these elements by providing for
    element qualifiers that specialize the meaning of specific
    elements. For example, a date element might have a qualifier, like
    "creation" to indicate that the date is a creation date. In
    addition, any element may be repeated. For some elements, like
    subject, and contributor, this is obviously necessary, but for
    other elements, like title and description, allowing repetitions
    is not very useful and adds complexity.

    This interface provides methods for retrieving data in full
    generality, to be compliant with the Dublin Core standard.
    Other interfaces will provide more convenient access methods
    tailored to specific element usage patterns.
    """

    def getQualifiedTitles():
        """Return a sequence of Title IDublinCoreElementItem.
        """

    def getQualifiedCreators():
        """Return a sequence of Creator IDublinCoreElementItem.
        """

    def getQualifiedSubjects():
        """Return a sequence of Subject IDublinCoreElementItem.
        """

    def getQualifiedDescriptions():
        """Return a sequence of Description IDublinCoreElementItem.
        """

    def getQualifiedPublishers():
        """Return a sequence of Publisher IDublinCoreElementItem.
        """

    def getQualifiedContributors():
        """Return a sequence of Contributor IDublinCoreElementItem.
        """

    def getQualifiedDates():
        """Return a sequence of Date IDublinCoreElementItem.
        """

    def getQualifiedTypes():
        """Return a sequence of Type IDublinCoreElementItem.
        """

    def getQualifiedFormats():
        """Return a sequence of Format IDublinCoreElementItem.
        """

    def getQualifiedIdentifiers():
        """Return a sequence of Identifier IDublinCoreElementItem.
        """

    def getQualifiedSources():
        """Return a sequence of Source IDublinCoreElementItem.
        """

    def getQualifiedLanguages():
        """Return a sequence of Language IDublinCoreElementItem.
        """

    def getQualifiedRelations():
        """Return a sequence of Relation IDublinCoreElementItem.
        """

    def getQualifiedCoverages():
        """Return a sequence of Coverage IDublinCoreElementItem.
        """

    def getQualifiedRights():
        """Return a sequence of Rights IDublinCoreElementItem.
        """

class IWritableGeneralDublinCore(Interface):
    """Provide write access to dublin core data

    This interface augments `IStandardDublinCore` with methods for
    writing elements.
    """

    def setQualifiedTitles(qualified_titles):
        """Set the qualified Title elements.

        The argument must be a sequence of `IDublinCoreElementItem`.
        """

    def setQualifiedCreators(qualified_creators):
        """Set the qualified Creator elements.

        The argument must be a sequence of Creator `IDublinCoreElementItem`.
        """

    def setQualifiedSubjects(qualified_subjects):
        """Set the qualified Subjects elements.

        The argument must be a sequence of Subject `IDublinCoreElementItem`.
        """

    def setQualifiedDescriptions(qualified_descriptions):
        """Set the qualified Descriptions elements.

        The argument must be a sequence of Description `IDublinCoreElementItem`.
        """

    def setQualifiedPublishers(qualified_publishers):
        """Set the qualified Publishers elements.

        The argument must be a sequence of Publisher `IDublinCoreElementItem`.
        """

    def setQualifiedContributors(qualified_contributors):
        """Set the qualified Contributors elements.

        The argument must be a sequence of Contributor `IDublinCoreElementItem`.
        """

    def setQualifiedDates(qualified_dates):
        """Set the qualified Dates elements.

        The argument must be a sequence of Date `IDublinCoreElementItem`.
        """

    def setQualifiedTypes(qualified_types):
        """Set the qualified Types elements.

        The argument must be a sequence of Type `IDublinCoreElementItem`.
        """

    def setQualifiedFormats(qualified_formats):
        """Set the qualified Formats elements.

        The argument must be a sequence of Format `IDublinCoreElementItem`.
        """

    def setQualifiedIdentifiers(qualified_identifiers):
        """Set the qualified Identifiers elements.

        The argument must be a sequence of Identifier `IDublinCoreElementItem`.
        """

    def setQualifiedSources(qualified_sources):
        """Set the qualified Sources elements.

        The argument must be a sequence of Source `IDublinCoreElementItem`.
        """

    def setQualifiedLanguages(qualified_languages):
        """Set the qualified Languages elements.

        The argument must be a sequence of Language `IDublinCoreElementItem`.
        """

    def setQualifiedRelations(qualified_relations):
        """Set the qualified Relations elements.

        The argument must be a sequence of Relation `IDublinCoreElementItem`.
        """

    def setQualifiedCoverages(qualified_coverages):
        """Set the qualified Coverages elements.

        The argument must be a sequence of Coverage `IDublinCoreElementItem`.
        """

    def setQualifiedRights(qualified_rights):
        """Set the qualified Rights elements.

        The argument must be a sequence of Rights `IDublinCoreElementItem`.
        """

class IDCDescriptiveProperties(Interface):
    """Basic descriptive meta-data properties
    """

    title = TextLine(
        title = u'Title',
        description =
        u"The first unqualified Dublin Core 'Title' element value."
        )

    description = Text(
        title = u'Description',
        description =
        u"The first unqualified Dublin Core 'Description' element value.",
        )

class IDCTimes(Interface):
    """Time properties
    """

    created = Datetime(
        title = u'Creation Date',
        description =
        u"The date and time that an object is created. "
        u"\nThis is normally set automatically."
        )

    modified = Datetime(
        title = u'Modification Date',
        description =
        u"The date and time that the object was last modified in a\n"
        u"meaningful way."
        )

class IDCPublishing(Interface):
    """Publishing properties
    """

    effective = Datetime(
        title = u'Effective Date',
        description =
        u"The date and time that an object should be published. "
        )


    expires = Datetime(
        title = u'Expiration Date',
        description =
        u"The date and time that the object should become unpublished."
        )

class IDCExtended(Interface):
    """Extended properties

    This is a mized bag of properties we want but that we probably haven't
    quite figured out yet.
    """


    creators = Tuple(
        title = u'Creators',
        description = u"The unqualified Dublin Core 'Creator' element values",
        value_type = TextLine(),
        )

    subjects = Tuple(
        title = u'Subjects',
        description = u"The unqualified Dublin Core 'Subject' element values",
        value_type = TextLine(),
        )

    publisher = Text(
        title = u'Publisher',
        description =
        u"The first unqualified Dublin Core 'Publisher' element value.",
        )

    contributors = Tuple(
        title = u'Contributors',
        description =
        u"The unqualified Dublin Core 'Contributor' element values",
        value_type = TextLine(),
        )

class ICMFDublinCore(Interface):
    """This interface duplicates the CMF dublin core interface.
    """

    def Title():
        """Return the resource title.

        The first unqualified Dublin Core `Title` element value is
        returned as a unicode string if an unqualified element is
        defined, otherwise, an empty unicode string is returned.
        """

    def Creator():
        """Return the resource creators.

        Return the full name(s) of the author(s) of the content
        object.

        The unqualified Dublin Core `Creator` element values are
        returned as a sequence of unicode strings.
        """

    def Subject():
        """Return the resource subjects.

        The unqualified Dublin Core `Subject` element values are
        returned as a sequence of unicode strings.
        """

    def Description():
        """Return the resource description

        Return a natural language description of this object.

        The first unqualified Dublin Core `Description` element value is
        returned as a unicode string if an unqualified element is
        defined, otherwise, an empty unicode string is returned.
        """

    def Publisher():
        """Dublin Core element - resource publisher

        Return full formal name of the entity or person responsible
        for publishing the resource.

        The first unqualified Dublin Core `Publisher` element value is
        returned as a unicode string if an unqualified element is
        defined, otherwise, an empty unicode string is returned.
        """

    def Contributors():
        """Return the resource contributors

        Return any additional collaborators.

        The unqualified Dublin Core `Contributor` element values are
        returned as a sequence of unicode strings.
        """

    def Date():
        """Return the default date

        The first unqualified Dublin Core `Date` element value is
        returned as a unicode string if an unqualified element is
        defined, otherwise, an empty unicode string is returned. The
        string is formatted  'YYYY-MM-DD H24:MN:SS TZ'.
        """

    def CreationDate():
        """Return the creation date.

        The value of the first Dublin Core `Date` element qualified by
        'creation' is returned as a unicode string if a qualified
        element is defined, otherwise, an empty unicode string is
        returned. The string is formatted  'YYYY-MM-DD H24:MN:SS TZ'.
        """

    def EffectiveDate():
        """Return the effective date

        The value of the first Dublin Core `Date` element qualified by
        'effective' is returned as a unicode string if a qualified
        element is defined, otherwise, an empty unicode string is
        returned. The string is formatted  'YYYY-MM-DD H24:MN:SS TZ'.
        """

    def ExpirationDate():
        """Date resource expires.

        The value of the first Dublin Core `Date` element qualified by
        'expiration' is returned as a unicode string if a qualified
        element is defined, otherwise, an empty unicode string is
        returned. The string is formatted  'YYYY-MM-DD H24:MN:SS TZ'.
        """

    def ModificationDate():
        """Date resource last modified.

        The value of the first Dublin Core `Date` element qualified by
        'modification' is returned as a unicode string if a qualified
        element is defined, otherwise, an empty unicode string is
        returned. The string is formatted  'YYYY-MM-DD H24:MN:SS TZ'.
        """

    def Type():
        """Return the resource type

        Return a human-readable type name for the resource.

        The first unqualified Dublin Core `Type` element value is
        returned as a unicode string if an unqualified element is
        defined, otherwise, an empty unicode string is returned.
        """

    def Format():
        """Return the resource format.

        Return the resource's MIME type (e.g., 'text/html',
        'image/png', etc.).

        The first unqualified Dublin Core `Format` element value is
        returned as a unicode string if an unqualified element is
        defined, otherwise, an empty unicode string is returned.
        """

    def Identifier():
        """Return the URL of the resource.

        This value is computed. It is included in the output of
        qualifiedIdentifiers with the qualification 'url'.
        """

    def Language():
        """Return the resource language.

        Return the RFC language code (e.g., 'en-US', 'pt-BR')
        for the resource.

        The first unqualified Dublin Core `Language` element value is
        returned as a unicode string if an unqualified element is
        defined, otherwise, an empty unicode string is returned.
        """

    def Rights():
        """Return the resource rights.

        Return a string describing the intellectual property status,
        if any, of the resource.  for the resource.

        The first unqualified Dublin Core `Rights` element value is
        returned as a unicode string if an unqualified element is
        defined, otherwise, an empty unicode string is returned.
        """

class IZopeDublinCore(
    IGeneralDublinCore,
    ICMFDublinCore,
    IDCDescriptiveProperties,
    IDCTimes,
    IDCPublishing,
    IDCExtended,
    ):
    """Zope Dublin Core properties"""

class IWriteZopeDublinCore(
    IZopeDublinCore,
    IWritableGeneralDublinCore,
    ):
    """Zope Dublin Core properties with generate update support"""


class IZopeDublinCoreAnnotatable(IAnnotatable):
    """Objects that can be annotated with Zope Dublin-Core meta data

    This is a marker interface that indicates the intent to have
    Zope Dublin-Core meta data associated with an object.
    """
