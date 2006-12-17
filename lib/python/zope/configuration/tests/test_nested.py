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
r"""Creating nested directives

When using ZCML, you sometimes nest ZCML directives. This is typically
done either to:

- Avoid repetative input.  Information shared among multiple
  directives is provided in a surrounding directive.

- Put together information that is too complex or structured to express
  with a single set of directive parameters.

Grouping directives are used to handle both of these cases.  See the
documentation in ``../zopeconfigure.py``. This file describes the
implementation of the zope ``configure`` directive, which groups
directives that use a common package or internationalization domain.
The documentation in ``../zopeconfigure.py`` provides background for
the documentation here.  You should also have read the documentation
in ``test_simple.py``, which documents how to create simple
directives.

This file shows you how to handle the second case above. In this case,
we have grouping directives that are meant to collaborate with
specific contained directives.  To do this, you have the grouping
directives declare a more specific (or alternate) interface to
``IConfigurationContext``. Directives designed to work with those
grouping directives are registered for the new interface.

Let's look at example. Suppose we wanted to be able to define schema
using ZCML.  We'd use a grouping directive to specify schemas and
contained directives to specify fields within the schema.  We'll use a
schema registry to hold the defined schemas.

A schema has a name, an id, some documentation, and some fields.
We'll provide the name and the id as parameters. We'll define fields
as subdirectives and documentation as text contained in the schema
directive.  The schema directive uses the schema, ``ISchemaInfo`` for
it's parameters.

We also define the schema, ISchema, that specifies an attribute that
nested field directives will use to store the fields they define.

The class, ``Schema``, provides the handler for the schema directive. (If
you haven't read the documentation in ``zopeconfigure.py``, you need
to do so now.)  The constructor saves its arguments as attributes
and initializes its ``fields`` attribute.

The ``after`` method of the ``Schema`` class creates a schema and
computes an action to register the schema in the schema registry.  The
discriminator prevents two schema directives from registering the same
schema.

It's important to note that when we call the ``action`` method on
``self``, rather than on ``self.context``.  This is because, in a
grouping directive handler, the handler instance is itself a context.
When we call the ``action`` method, the method stores additional meta
data associated with the context it was called on. This meta data
includes an include path, used when resolving conflicting actions,
and an object that contains information about the XML source used
to invole the directive. If we called the action method on
``self.context``, the wrong meta data would be associated with the
configuration action.

The file ``schema.zcml`` contains the meta-configuration directive
that defines the schema directive.

To define fields, we'll create directives to define the fields.
Let's start with a ``text`` field.  ``ITextField`` defines the schema for
text field parameters. It extends ``IFieldInfo``, which defines data
common to all fields.  We also define a simple handler method,
textField, that takes a context and keyword arguments. (For
information on writing simple directives, see ``test_simple.py``.)
We've abstracted most of the logic into the function ``field``.

The ``field`` function computes a field instance using the
constructor, and the keyword arguments passed to it.  It also uses the
context information object to get the text content of the directive,
which it uses for the field description.

After computing the field instance, it gets the ``Schema`` instance,
which is the context of the context passed to the function. The
function checks to see if there is already a field with that name. If
there is, it raises an error. Otherwise, it saves the field. 

We also define an ``IIntInfo`` schema and ``intField`` handler
function to support defining integer fields. 

We register the ``text`` and ``int`` directives in ``schema.zcml``.
These are like the simple directive definition we saw in
``test_simple.py`` with an important exception.  We provide a
``usedIn`` parameter to say that these directives can *only* ne used
in a ``ISchema`` context. In other words, these can only be used
inside of ``schema`` directives.

The ``schema.zcml`` file also contains some sample ``schema``
directives.  We can execute the file:

>>> from zope.configuration import tests
>>> context = xmlconfig.file("schema.zcml", tests)

And verify that the schema registery has the schemas we expect:

>>> from pprint import PrettyPrinter
>>> pprint=PrettyPrinter(width=70).pprint
>>> pprint(list(schema_registry))
['zope.configuration.tests.test_nested.I1',
 'zope.configuration.tests.test_nested.I2']

>>> def sorted(x):
...     r = list(x)
...     r.sort()
...     return r

>>> i1 = schema_registry['zope.configuration.tests.test_nested.I1']
>>> sorted(i1)
['a', 'b']
>>> i1['a'].__class__.__name__
'Text'
>>> i1['a'].description.strip()
u'A\n\n          Blah blah'
>>> i1['a'].min_length
1
>>> i1['b'].__class__.__name__
'Int'
>>> i1['b'].description.strip()
u'B\n\n          Not feeling very creative'
>>> i1['b'].min
1
>>> i1['b'].max
10

>>> i2 = schema_registry['zope.configuration.tests.test_nested.I2']
>>> sorted(i2)
['x', 'y']


Now let's look at some error situations. For example, let's see what
happens if we use a field directive outside of a schema dorective.
(Note that we used the context we created above, so we don't have to
redefine our directives:

>>> try:
...    v = xmlconfig.string(
...      '<text xmlns="http://sample.namespaces.zope.org/schema" name="x" />',
...      context)
... except xmlconfig.ZopeXMLConfigurationError, v:
...   pass
>>> print v
File "<string>", line 1.0
    ConfigurationError: The directive """ \
        """(u'http://sample.namespaces.zope.org/schema', u'text') """ \
        """cannot be used in this context

Let's see what happens if we declare duplicate fields:

>>> try:
...    v = xmlconfig.string(
...      '''
...      <schema name="I3" id="zope.configuration.tests.test_nested.I3"
...              xmlns="http://sample.namespaces.zope.org/schema">
...        <text name="x" />
...        <text name="x" />
...      </schema>
...      ''',
...      context)
... except xmlconfig.ZopeXMLConfigurationError, v:
...   pass
>>> print v
File "<string>", line 5.7-5.24
    ValueError: ('Duplicate field', 'x')

$Id: test_nested.py 25177 2004-06-02 13:17:31Z jim $
"""

import unittest
from zope.testing.doctestunit import DocTestSuite
from zope import interface, schema
from zope.configuration import config, xmlconfig, fields


schema_registry = {}

class ISchemaInfo(interface.Interface):
    """Parameter schema for the schema directive
    """

    name = schema.TextLine(
        title=u"The schema name",
        description=u"This is a descriptive name for the schema."
        )

    id = schema.Id(
        title=u"The unique id for the schema"
        )

class ISchema(interface.Interface):
    """Interface that distinguishes the schema directive
    """

    fields = interface.Attribute("Dictionary of field definitions"
        )
    
class Schema(config.GroupingContextDecorator):
    """Handle schema directives
    """

    interface.implements(config.IConfigurationContext, ISchema)

    def __init__(self, context, name, id):
        self.context, self.name, self.id = context, name, id
        self.fields = {}

    def after(self):
        schema = interface.Interface.__class__(
            self.name,
            (interface.Interface, ),
            self.fields
            )
        schema.__doc__ = self.info.text.strip()
        self.action(
            discriminator=('schema', self.id),
            callable=schema_registry.__setitem__,
            args=(self.id, schema),
            )
        

class IFieldInfo(interface.Interface):

    name = schema.BytesLine(
        title=u"The field name"
        )

    title = schema.TextLine(
        title=u"Title",
        description=u"A short summary or label",
        default=u"",
        required=False,
        )

    required = fields.Bool(
        title=u"Required",
        description=u"Determines whether a value is required.",
        default=True)

    readonly = fields.Bool(
        title=u"Read Only",
        description=u"Can the value be modified?",
        required=False,
        default=False)

class ITextInfo(IFieldInfo):

    min_length = schema.Int(
        title=u"Minimum length",
        description=u"Value after whitespace processing cannot have less than "
                    u"min_length characters. If min_length is None, there is "
                    u"no minimum.",
        required=False,
        min=0, # needs to be a positive number
        default=0)

    max_length = schema.Int(
        title=u"Maximum length",
        description=u"Value after whitespace processing cannot have greater "
                    u"or equal than max_length characters. If max_length is "
                    u"None, there is no maximum.",
        required=False,
        min=0, # needs to be a positive number
        default=None)

def field(context, constructor, name, **kw):

    # Compute the field
    field = constructor(description=context.info.text.strip(), **kw)

    # Save it in the schema's field dictionary
    schema = context.context
    if name in schema.fields:
        raise ValueError("Duplicate field", name)
    schema.fields[name] = field

    
def textField(context, **kw):
    field(context, schema.Text, **kw)

class IIntInfo(IFieldInfo):

    min = schema.Int(
        title=u"Start of the range",
        required=False,
        default=None
        )

    max = schema.Int(
        title=u"End of the range (excluding the value itself)",
        required=False,
        default=None
        )
    
def intField(context, **kw):
    field(context, schema.Int, **kw)
    

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__': unittest.main()
