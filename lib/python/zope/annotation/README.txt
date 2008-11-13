Annotations
===========

There is more to document about annotations, but we'll just sketch out
a scenario on how to use the annotation factory for now. This is one
of the easiest ways to use annotations -- basically you can see them
as persistent, writable adapters.

First, let's make a persistent object we can create annotations for:

  >>> from zope import interface
  >>> class IFoo(interface.Interface):
  ...     pass
  >>> from zope.annotation.interfaces import IAttributeAnnotatable
  >>> from persistent import Persistent
  >>> class Foo(Persistent):
  ...     interface.implements(IFoo, IAttributeAnnotatable)

We directly say that Foo implements IAttributeAnnotatable here. In
practice this is often done in ZCML, using the `implements`
subdirective of the `content` or `class` directive.

Now let's create an annotation for this:
  
  >>> class IBar(interface.Interface):
  ...     a = interface.Attribute('A')
  ...     b = interface.Attribute('B')
  >>> from zope import component
  >>> class Bar(Persistent):
  ...     interface.implements(IBar)
  ...     component.adapts(IFoo)
  ...     def __init__(self):
  ...         self.a = 1
  ...         self.b = 2

Note that the annotation implementation does not expect any arguments
to its `__init__`. Otherwise it's basically an adapter.

Now, we'll register the annotation as an adapter. To do this we use
the `factory` function provided by `zope.annotation`:

  >>> from zope.annotation import factory
  >>> component.provideAdapter(factory(Bar))

Note that we do not need to specify what the adapter provides or what
it adapts - we already do this on the annotation class itself.

Now let's make an instance of `Foo`, and make an annotation for it.

  >>> foo = Foo()
  >>> bar = IBar(foo)
  >>> bar.a
  1
  >>> bar.b
  2

We'll change `a` and get the annotation again. Our change is still
there:

  >>> bar.a = 3
  >>> IBar(foo).a
  3

Of course it's still different for another instance of `Foo`:

  >>> foo2 = Foo()
  >>> IBar(foo2).a
  1

What if our annotation does not provide what it adapts with
`component.adapts`? It will complain:

  >>> class IQux(interface.Interface):
  ...     pass
  >>> class Qux(Persistent):
  ...     interface.implements(IQux)
  >>> component.provideAdapter(factory(Qux)) # doctest: +ELLIPSIS
  Traceback (most recent call last):
  ...
  TypeError: Missing 'zope.component.adapts' on annotation

It's possible to provide an annotation with an explicit key. (If the
key is not supplied, the key is deduced from the annotation's dotted
name, provided it is a class.)

  >>> class IHoi(interface.Interface):
  ...     pass
  >>> class Hoi(Persistent):
  ...     interface.implements(IHoi)
  ...     component.adapts(IFoo)
  >>> component.provideAdapter(factory(Hoi, 'my.unique.key'))
  >>> isinstance(IHoi(foo), Hoi)
  True


Location
--------

Annotation factories are put into the location hierarchy with their parent
pointing to the annotated object and the name to the dotted name of the
annotation's class (or the name the adapter was registered under):

  >>> foo3 = Foo()
  >>> new_hoi = IHoi(foo3)
  >>> new_hoi.__parent__
  <Foo object at 0x...>
  >>> new_hoi.__name__
  'my.unique.key'
  >>> import zope.location.interfaces
  >>> zope.location.interfaces.ILocation.providedBy(new_hoi)
  True

Please notice, that our Hoi object does not implement ILocation, so a
location proxy will be used. This has to be re-established every time we
retrieve the object

(Guard against former bug: proxy wasn't established when the annotation
existed already.)

  >>> old_hoi = IHoi(foo3)
  >>> old_hoi.__parent__
  <Foo object at 0x...>
  >>> old_hoi.__name__
  'my.unique.key'
  >>> zope.location.interfaces.ILocation.providedBy(old_hoi)
  True
