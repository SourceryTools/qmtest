===============
Browser Widgets
===============

.. contents::

This directory contains widgets: views on bound schema fields.  Many of these
are straightforward.  For instance, see the `TextWidget` in textwidgets.py,
which is a subclass of BrowserWidget in widget.py.  It is registered as an
`IBrowserRequest` view of an `ITextLine` schema field, providing the
`IInputWidget` interface::

  <view
      type="zope.publisher.interfaces.browser.IBrowserRequest"
      for="zope.schema.interfaces.ITextLine"
      provides="zope.app.form.interfaces.IInputWidget"
      factory=".TextWidget"
      permission="zope.Public"
      />

The widget then receives the field and the request as arguments to the factory
(i.e., the `TextWidget` class).

Some widgets in Zope 3 extend this pattern.  This extension is configurable:
simply do not load the zope/app/form/browser/configure.zcml file if you do not
wish to participate in the extension.  The widget registration is extended for
`Choice` fields and for the `collection` fields.

Default Choice Field Widget Registration and Lookup
===================================================

As described above, all field widgets are obtained by looking up a browser
`IInputWidget` or `IDisplayWidget` view for the field object.  For `Choice`
fields, the default registered widget defers all of its behavior to the result
of another lookup: a browser widget view for the field *and* the Choice field's
vocabulary.  

This allows registration of Choice widgets that differ on the basis of the
vocabulary type.  For example, a widget for a vocabulary of images might have
a significantly different user interface than a widget for a vocabulary of
words.  A dynamic vocabulary might implement `IIterableVocabulary` if its
contents are below a certain length, but not implement the marker "iterable"
interface if the number of possible values is above the threshhold.

This also means that choice widget factories are called with with an additional
argument.  Rather than being called with the field and the request as
arguments, choice widgets receive the field, vocabulary, and request as
arguments.

Some `Choice` widgets may also need to provide a query interface,
particularly if the vocabulary is too big to iterate over.  The vocabulary
may provide a query which implements an interface appropriate for that
vocabulary.  You then can register a query view -- a view registered for the
query interface and the field interface -- that implements
`zope.app.forms.browser.interfaces.IVocabularyQueryView`.

Default Collection Field Widget Registration and Lookup
=======================================================

The default configured lookup for collection fields -- List, Tuple, and Set, for
instance -- begins with the usual lookup for a browser widget view for the
field object.  This widget defers its display to the result of another lookup:
a browser widget view registered for the field and the field's `value_type`
(the type of the contained values).  This allows registrations for collection
widgets that differ on the basis of the members -- a widget for entering a list
of text strings might differ significantly from a widget for entering a list of
dates...or even a list of choices, as discussed below.

This registration pattern has three implications that should be highlighted. 

* First, collection fields that do not specify a `value_type` probably cannot
  have a reasonable widget.

* Second, collection widgets that wish to be the default widget for a
  collection with any `value_type` should be registered for the collection
  field and a generic value_type: the `IField` interface.  Do  not register the
  generic widget for the collection field only or you will break the lookup
  behavior as described here.

* Third, like choice widget factories, sequence widget factories (classes or
  functions) take three arguments.  Typical sequence widgets receive the
  field, the `value_type`, and the request as arguments.

Collections of Choices
----------------------

If a collection field's `value_type` is a `Choice` field, the second widget
again defers its behavior, this time to a third lookup based on the collection
field and the choice's vocabulary.  This means that a widget for a list of
large image choices can be different than a widget for a list of small image
choices (with a different vocabulary interface), different from a widget for a
list of keyword choices, and different from a set of keyword choices.

Some advanced applications may wish to do a further lookup on the basis of the
unique attribute of the collection field--perhaps looking up a named view with
a "unique" or "lenient" token depending on the field's value, but this is not
enabled in the default Zope 3 configuration.

Registering Widgets for a New Collection Field Type
---------------------------------------------------

Because of this lookup pattern, basic widget registrations for new field types
must follow a recipe.  For example, a developer may introduce a new Bag field
type for simple shopping cart functionality and wishes to add widgets for it
within the default Zope 3 collection widget registration.  The bag widgets
should be registered something like this. 

The only hard requirement is that the developer must register the bag + choice
widget: the widget is just the factory for the third dispatch as described
above, so the developer can use the already implemented widgets listed below::

  <view
      type="zope.publisher.interfaces.browser.IBrowserRequest"
      for="zope.schema.interfaces.IBag
           zope.schema.interfaces.IChoice"
      provides="zope.app.form.interfaces.IDisplayWidget"
      factory=".ChoiceCollectionDisplayWidget"
      permission="zope.Public"
      />

  <view
      type="zope.publisher.interfaces.browser.IBrowserRequest"
      for="zope.schema.interfaces.IBag
           zope.schema.interfaces.IChoice"
      provides="zope.app.form.interfaces.IInputWidget"
      factory=".ChoiceCollectionInputWidget"
      permission="zope.Public"
      />

Beyond this, the developer may also have a generic bag widget she wishes to
register.  This might look something like this, assuming there's a
`BagSequenceWidget` available in this package::

  <view
      type="zope.publisher.interfaces.browser.IBrowserRequest"
      for="zope.schema.interfaces.IBag
           zope.schema.interfaces.IField"
      provides="zope.app.form.interfaces.IInputWidget"
      factory=".BagSequenceWidget"
      permission="zope.Public"
      />

Then any widgets for the bag and a vocabulary would be registered according to
this general pattern, in which `IIterableVocabulary` would be the interface of
any appropriate vocabulary and `BagWidget` is some appropriate widget::

  <view
      type="zope.publisher.interfaces.browser.IBrowserRequest"
      for="zope.schema.interfaces.IBag
           zope.schema.interfaces.IIterableVocabulary"
      provides="zope.app.form.interfaces.IInputWidget"
      factory=".BagWidget"
      permission="zope.Public"
      />
