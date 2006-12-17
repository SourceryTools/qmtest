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
"""Schema interfaces and exceptions

$Id: interfaces.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = "reStructuredText"

from zope.interface import Interface, Attribute
from zope.schema._bootstrapfields import Container, Iterable
from zope.schema._bootstrapfields import Field, Text, TextLine, Bool, Int

from zope.i18nmessageid import MessageFactory
_ = MessageFactory("zope")

# Import from _bootstrapinterfaces only because other packages will expect
# to find these interfaces here.
from zope.schema._bootstrapinterfaces import StopValidation, ValidationError
from zope.schema._bootstrapinterfaces import IFromUnicode
from zope.schema._bootstrapinterfaces import RequiredMissing, WrongType
from zope.schema._bootstrapinterfaces import ConstraintNotSatisfied
from zope.schema._bootstrapinterfaces import NotAContainer, NotAnIterator
from zope.schema._bootstrapinterfaces import TooSmall, TooBig
from zope.schema._bootstrapinterfaces import TooShort, TooLong
from zope.schema._bootstrapinterfaces import InvalidValue

class WrongContainedType(ValidationError):
    __doc__ = _("""Wrong contained type""")

class NotUnique(ValidationError):
    __doc__ = _("""One or more entries of sequence are not unique.""")

class SchemaNotFullyImplemented(ValidationError):
    __doc__ = _("""Schema not fully implemented""")

class SchemaNotProvided(ValidationError):
    __doc__ = _("""Schema not provided""")

class InvalidURI(ValidationError):
    __doc__ = _("""The specified URI is not valid.""")

class InvalidId(ValidationError):
    __doc__ = _("""The specified id is not valid.""")

class InvalidDottedName(ValidationError):
    __doc__ = _("""The specified dotted name is not valid.""")

class Unbound(Exception):
    __doc__ = _("""The field is not bound.""")

class IField(Interface):
    """Basic Schema Field Interface.

    Fields are used for Interface specifications.  They at least provide
    a title, description and a default value.  You can also
    specify if they are required and/or readonly.

    The Field Interface is also used for validation and specifying
    constraints.

    We want to make it possible for a IField to not only work
    on its value but also on the object this value is bound to.
    This enables a Field implementation to perform validation
    against an object which also marks a certain place.

    Note that many fields need information about the object
    containing a field. For example, when validating a value to be
    set as an object attribute, it may be necessary for the field to
    introspect the object's state. This means that the field needs to
    have access to the object when performing validation::

         bound = field.bind(object)
         bound.validate(value)

    """

    def bind(object):
        """Return a copy of this field which is bound to context.

        The copy of the Field will have the 'context' attribute set
        to 'object'.  This way a Field can implement more complex
        checks involving the object's location/environment.

        Many fields don't need to be bound. Only fields that condition
        validation or properties on an object containing the field
        need to be bound.
        """

    title = TextLine(
        title=_(u"Title"),
        description=_(u"A short summary or label"),
        default=u"",
        required=False,
        )

    description = Text(
        title=_(u"Description"),
        description=_(u"A description of the field"),
        default=u"",
        required=False,
        )

    required = Bool(
        title=_(u"Required"),
        description=(
        _(u"Tells whether a field requires its value to exist.")),
        default=True)

    readonly = Bool(
        title=_(u"Read Only"),
        description=_(u"If true, the field's value cannot be changed."),
        required=False,
        default=False)

    default = Field(
        title=_(u"Default Value"),
        description=_(u"""The field default value may be None or a legal
                        field value""")
        )

    missing_value = Field(
        title=_(u"Missing Value"),
        description=_(u"""If input for this Field is missing, and that's ok,
                          then this is the value to use""")
        )

    order = Int(
        title=_(u"Field Order"),
        description=_(u"""
        The order attribute can be used to determine the order in
        which fields in a schema were defined. If one field is created
        after another (in the same thread), its order will be
        greater.

        (Fields in separate threads could have the same order.)
        """),
        required=True,
        readonly=True,
        )

    def constraint(value):
        u"""Check a customized constraint on the value.

        You can implement this method with your Field to
        require a certain constraint.  This relaxes the need
        to inherit/subclass a Field you to add a simple constraint.
        Returns true if the given value is within the Field's constraint.
        """

    def validate(value):
        u"""Validate that the given value is a valid field value.

        Returns nothing but raises an error if the value is invalid.
        It checks everything specific to a Field and also checks
        with the additional constraint.
        """

    def get(object):
        """Get the value of the field for the given object."""

    def query(object, default=None):
        """Query the value of the field for the given object.

        Return the default if the value hasn't been set.
        """

    def set(object, value):
        """Set the value of the field for the object

        Raises a type error if the field is a read-only field.
        """

class IIterable(IField):
    u"""Fields with a value that can be iterated over.

    The value needs to support iteration; the implementation mechanism
    is not constrained.  (Either `__iter__()` or `__getitem__()` may be
    used.)
    """

class IContainer(IField):
    u"""Fields whose value allows an ``x in value`` check.

    The value needs to support the `in` operator, but is not
    constrained in how it does so (whether it defines `__contains__()`
    or `__getitem__()` is immaterial).
    """

class IOrderable(IField):
    u"""Field requiring its value to be orderable.

    The set of value needs support a complete ordering; the
    implementation mechanism is not constrained.  Either `__cmp__()` or
    'rich comparison' methods may be used.
    """

class ILen(IField):
    u"""A Field requiring its value to have a length.

    The value needs to have a conventional __len__ method.
    """

class IMinMax(IOrderable):
    u"""Field requiring its value to be between min and max.

    This implies that the value needs to support the IOrderable interface.
    """

    min = Field(
        title=_(u"Start of the range"),
        required=False,
        default=None
        )

    max = Field(
        title=_(u"End of the range (excluding the value itself)"),
        required=False,
        default=None
        )


class IMinMaxLen(ILen):
    u"""Field requiring the length of its value to be within a range"""

    min_length = Int(
        title=_(u"Minimum length"),
        description=_(u"""
        Value after whitespace processing cannot have less than
        `min_length` characters (if a string type) or elements (if
        another sequence type). If `min_length` is ``None``, there is
        no minimum.
        """),
        required=False,
        min=0, # needs to be a positive number
        default=0)

    max_length = Int(
        title=_(u"Maximum length"),
        description=_(u"""
        Value after whitespace processing cannot have greater
        or equal than `max_length` characters (if a string type) or
        elements (if another sequence type). If `max_length` is
        ``None``, there is no maximum."""),
        required=False,
        min=0, # needs to be a positive number
        default=None)

class IInterfaceField(IField):
    u"""Fields with a value that is an interface (implementing
    zope.interface.Interface)."""

class IBool(IField):
    u"""Boolean Field."""

    default = Bool(
        title=_(u"Default Value"),
        description=_(u"""The field default value may be None or a legal
                        field value""")
        )

class IBytes(IMinMaxLen, IIterable, IField):
    u"""Field containing a byte string (like the python str).

    The value might be constrained to be with length limits.
    """

class IASCII(IBytes):
    u"""Field containing a 7-bit ASCII string. No characters > DEL
    (chr(127)) are allowed

    The value might be constrained to be with length limits.
    """

class IBytesLine(IBytes):
    u"""Field containing a byte string without newlines."""

class IASCIILine(IASCII):
    u"""Field containing a 7-bit ASCII string without newlines."""

class IText(IMinMaxLen, IIterable, IField):
    u"""Field containing a unicode string."""

class ISourceText(IText):
    u"""Field for source text of object."""

class ITextLine(IText):
    u"""Field containing a unicode string without newlines."""

class IPassword(ITextLine):
    u"Field containing a unicode string without newlines that is a password."

class IInt(IMinMax, IField):
    u"""Field containing an Integer Value."""

    min = Int(
        title=_(u"Start of the range"),
        required=False,
        default=None
        )

    max = Int(
        title=_(u"End of the range (excluding the value itself)"),
        required=False,
        default=None
        )

    default = Int(
        title=_(u"Default Value"),
        description=_(u"""The field default value may be None or a legal
                        field value""")
        )

class IFloat(IMinMax, IField):
    u"""Field containing a Float."""

class IDatetime(IMinMax, IField):
    u"""Field containing a DateTime."""

class IDate(IMinMax, IField):
    u"""Field containing a date."""

class ITimedelta(IMinMax, IField):
    u"""Field containing a timedelta."""

def _is_field(value):
    if not IField.providedBy(value):
        return False
    return True

def _fields(values):
    for value in values:
        if not _is_field(value):
            return False
    return True


class IURI(IBytesLine):
    """A field containing an absolute URI
    """

class IId(IBytesLine):
    """A field containing a unique identifier

    A unique identifier is either an absolute URI or a dotted name.
    If it's a dotted name, it should have a module/package name as a prefix.
    """

class IChoice(IField):
    u"""Field whose value is contained in a predefined set

    Only one, values or vocabulary, may be specified for a given choice.
    """
    vocabulary = Attribute(
        "vocabulary",
        ("IBaseVocabulary to be used, or vocabulary name, or None.\n"
         "\n"
         "If a string, the vocabulary name should be used by an\n"
         "IVocabularyRegistry to locate an appropriate\n"
         "IBaseVocabulary object."))

# Collections:

# Abstract

class ICollection(IMinMaxLen, IIterable, IContainer):
    u"""Abstract interface containing a collection value.

    The Value must be iterable and may have a min_length/max_length.
    """

    value_type = Field(
        title = _("Value Type"),
        description = _(u"Field value items must conform to the given type, "
                        u"expressed via a Field."))

    unique = Bool(
        title = _('Unique Members'),
        description = _('Specifies whether the members of the collection '
                        'must be unique.'),
        default=False)

class ISequence(ICollection):
    u"""Abstract interface specifying that the value is ordered"""

class IUnorderedCollection(ICollection):
    u"""Abstract interface specifying that the value cannot be ordered"""

class IAbstractSet(IUnorderedCollection):
    u"""An unordered collection of unique values."""
    
    unique = Attribute(u"This ICollection interface attribute must be True")

class IAbstractBag(IUnorderedCollection):
    u"""An unordered collection of values, with no limitations on whether
    members are unique"""
    
    unique = Attribute(u"This ICollection interface attribute must be False")

# Concrete

class ITuple(ISequence):
    u"""Field containing a value that implements the API of a conventional 
    Python tuple."""

class IList(ISequence):
    u"""Field containing a value that implements the API of a conventional 
    Python list."""

class ISet(IAbstractSet):
    u"""Field containing a value that implements the API of a conventional 
    Python standard library sets.Set or a Python 2.4+ set."""

class IFrozenSet(IAbstractSet):
    u"""Field containing a value that implements the API of a conventional 
    Python 2.4+ frozenset."""

# (end Collections)

class IObject(IField):
    u"""Field containing an Object value."""

    schema = Attribute("schema",
        _(u"The Interface that defines the Fields comprising the Object."))

class IDict(IMinMaxLen, IIterable, IContainer):
    u"""Field containing a conventional dict.

    The key_type and value_type fields allow specification
    of restrictions for keys and values contained in the dict.
    """

    key_type = Attribute("key_type",
        _(u"""Field keys must conform to the given type, expressed
           via a Field.
        """))

    value_type = Attribute("value_type",
        _(u"""Field values must conform to the given type, expressed
           via a Field.
        """))

class ITerm(Interface):
    """Object representing a single value in a vocabulary."""

    value = Attribute(
        "value", "The value used to represent vocabulary term in a field.")


class ITokenizedTerm(ITerm):
    """Object representing a single value in a tokenized vocabulary.
    """

    # TODO: There should be a more specialized field type for this.
    token = Attribute(
        "token",
        """Token which can be used to represent the value on a stream.

        The value of this attribute must be a non-empty 7-bit string.
        Control characters are not allowed.
        """)

class ITitledTokenizedTerm(ITokenizedTerm):
    """A tokenized term that includes a title."""
    
    title = TextLine(title=_(u"Title"))

class ISource(Interface):
    """A set of values from which to choose

    Sources represent sets of values. They are used to specify the
    source for choice fields.

    Sources can be large (even infinite), in which case, they need to
    be queried to find out what their values are.
    
    """

    def __contains__(value):
        """Return whether the value is available in this source
        """

class ISourceQueriables(Interface):
    """A collection of objects for querying sources
    """

    def getQueriables():
        """Return an iterable of objects that can be queried

        The returned obects should be two-tuples with:

        - A unicode id

          The id must uniquely identify the queriable object within
          the set of queryable objects. Furthermore, in subsequent
          calls, the same id should be used for a given queriable
          object.

        - A queryable object

          This is an object for which there is a view is provided for
          searcing for items.

        """

class IContextSourceBinder(Interface):
    def __call__(context):
        """Return a context-bound instance that implements ISource.
        """
    

class IBaseVocabulary(ISource):
    """Representation of a vocabulary.

    At this most basic level, a vocabulary only need to support a test
    for containment.  This can be implemented either by __contains__()
    or by sequence __getitem__() (the later only being useful for
    vocabularies which are intrinsically ordered).
    """

    def getTerm(value):
        """Return the ITerm object for the term 'value'.

        If 'value' is not a valid term, this method raises LookupError.
        """


class IIterableSource(ISource):
    """Source which supports iteration over allowed values.

    The objects iteration provides must be values from the source.
    """

    def __iter__():
        """Return an iterator which provides the values from the source."""

    def __len__():
        """Return the number of valid values, or sys.maxint."""


# BBB vocabularies are pending deprecation, hopefully in 3.3
class IIterableVocabulary(Interface):
    """Vocabulary which supports iteration over allowed values.

    The objects iteration provides must conform to the ITerm
    interface.
    """

    def __iter__():
        """Return an iterator which provides the terms from the vocabulary."""

    def __len__():
        """Return the number of valid terms, or sys.maxint."""


class IVocabulary(IIterableVocabulary, IBaseVocabulary):
    """Vocabulary which is iterable."""


class IVocabularyTokenized(IVocabulary):
    """Vocabulary that provides support for tokenized representation.

    Terms returned from getTerm() and provided by iteration must
    conform to ITitledTokenizedTerm.
    """

    def getTermByToken(token):
        """Return an ITokenizedTerm for the passed-in token.

        If `token` is not represented in the vocabulary, `LookupError`
        is raised.
        """


class IVocabularyRegistry(Interface):
    """Registry that provides IBaseVocabulary objects for specific fields.
    """

    def get(object, name):
        """Return the vocabulary named 'name' for the content object
        'object'.

        When the vocabulary cannot be found, LookupError is raised.
        """

class IVocabularyFactory(Interface):
    """Can create vocabularies."""

    def __call__(self, context):
        """The context provides a location that the vocabulary can make use
        of."""
