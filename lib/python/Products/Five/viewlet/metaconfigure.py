import os
from zope.configuration.exceptions import ConfigurationError
from zope.viewlet import interfaces
from zope.interface import Interface, classImplements
from zope.component import zcml
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.publisher.interfaces.browser import IBrowserView
from zope.app.publisher.browser import viewmeta

from Products.Five.security import getSecurityInfo, protectClass, protectName
from Products.Five.viewlet import viewlet
from Products.Five.viewlet import manager


from Globals import InitializeClass as initializeClass

def viewletManagerDirective(
    _context, name, permission,
    for_=Interface, layer=IDefaultBrowserLayer, view=IBrowserView,
    provides=interfaces.IViewletManager, class_=None, template=None,
    allowed_interface=None, allowed_attributes=None):

    # If class is not given we use the basic viewlet manager.
    if class_ is None:
        class_ = manager.ViewletManagerBase

    # Iterate over permissions
    if allowed_attributes is None:
        allowed_attributes = ['render', 'update']
    if allowed_interface is not None:
        for interface in allowed_interface:
            allowed_attributes.extend(interface.names())

    # Make sure that the template exists and that all low-level API methods
    # have the right permission.
    if template:
        template = os.path.abspath(str(_context.path(template)))
        if not os.path.isfile(template):
            raise ConfigurationError("No such file", template)
        allowed_attributes.append('__getitem__')

        # Create a new class based on the template and class.
        new_class = manager.ViewletManager(
            name, provides, template=template, bases=(class_, ))
    else:
        # Create a new class based on the class.
        new_class = manager.ViewletManager(name, provides, bases=(class_, ))

    # Register interfaces
    viewmeta._handle_for(_context, for_)
    zcml.interface(_context, view)

    # register a viewlet manager
    _context.action(
        discriminator = ('viewletManager', for_, layer, view, name),
        callable = zcml.handler,
        args = ('registerAdapter',
                new_class, (for_, layer, view), provides, name,
                _context.info),)
    _context.action(
        discriminator = ('five:protectClass', new_class),
        callable = protectClass,
        args = (new_class, permission)
        )
    if allowed_attributes:
        for attr in allowed_attributes:
            _context.action(
                discriminator = ('five:protectName', new_class, attr),
                callable = protectName,
                args = (new_class, attr, permission)
                )
    _context.action(
        discriminator = ('five:initialize:class', new_class),
        callable = initializeClass,
        args = (new_class,)
        )


def viewletDirective(
    _context, name, permission,
    for_=Interface, layer=IDefaultBrowserLayer, view=IBrowserView,
    manager=interfaces.IViewletManager, class_=None, template=None,
    attribute='render', allowed_interface=None, allowed_attributes=None,
    **kwargs):

    # Either the class or template must be specified.
    if not (class_ or template):
        raise ConfigurationError("Must specify a class or template")

    # Make sure that all the non-default attribute specifications are correct.
    if attribute != 'render':
        if template:
            raise ConfigurationError(
                "Attribute and template cannot be used together.")

        # Note: The previous logic forbids this condition to evere occur.
        if not class_:
            raise ConfigurationError(
                "A class must be provided if attribute is used")

    # Iterate over permissions
    if allowed_attributes is None:
        allowed_attributes = ['render', 'update']
    if allowed_interface is not None:
        for interface in allowed_interface:
            allowed_attributes.extend(interface.names())

    # Make sure that the template exists and that all low-level API methods
    # have the right permission.
    if template:
        template = os.path.abspath(str(_context.path(template)))
        if not os.path.isfile(template):
            raise ConfigurationError("No such file", template)
        allowed_attributes.append('__getitem__')

    # Make sure the has the right form, if specified.
    if class_:
        if attribute != 'render':
            if not hasattr(class_, attribute):
                raise ConfigurationError(
                    "The provided class doesn't have the specified attribute "
                    )
        if template:
            # Create a new class for the viewlet template and class.
            new_class = viewlet.SimpleViewletClass(
                template, bases=(class_, ), attributes=kwargs)
        else:
            if not hasattr(class_, 'browserDefault'):
                cdict = {'browserDefault':
                         lambda self, request: (getattr(self, attribute), ())}
            else:
                cdict = {}

            cdict['__name__'] = name
            cdict['__page_attribute__'] = attribute
            cdict.update(kwargs)
            new_class = type(class_.__name__,
                             (class_, viewlet.SimpleAttributeViewlet), cdict)

        if hasattr(class_, '__implements__'):
            classImplements(new_class, IBrowserPublisher)

    else:
        # Create a new class for the viewlet template alone.
        new_class = viewlet.SimpleViewletClass(template, name=name,
                                               attributes=kwargs)

    # Register the interfaces.
    viewmeta._handle_for(_context, for_)
    zcml.interface(_context, view)

    # register viewlet
    _context.action(
        discriminator = ('viewlet', for_, layer, view, manager, name),
        callable = zcml.handler,
        args = ('registerAdapter',
                new_class, (for_, layer, view, manager),
                interfaces.IViewlet, name, _context.info),)

    _context.action(
        discriminator = ('five:protectClass', new_class),
        callable = protectClass,
        args = (new_class, permission)
        )
    if allowed_attributes:
        for attr in allowed_attributes:
            _context.action(
                discriminator = ('five:protectName', new_class, attr),
                callable = protectName,
                args = (new_class, attr, permission)
                )
    _context.action(
        discriminator = ('five:initialize:class', new_class),
        callable = initializeClass,
        args = (new_class,)
        )
