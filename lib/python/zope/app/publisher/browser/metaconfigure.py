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
"""Browser configuration code

$Id: metaconfigure.py 67630 2006-04-27 00:54:03Z jim $
"""
import warnings
from zope.component.interfaces import IDefaultViewName
from zope.component.interface import provideInterface
from zope.component.zcml import handler
from zope.configuration.exceptions import ConfigurationError
from zope.interface import directlyProvides
from zope.interface.interface import InterfaceClass
from zope.publisher.interfaces.browser import IBrowserRequest, IDefaultSkin
from zope.publisher.interfaces.browser import IBrowserSkinType

from zope.app import zapi, layers, skins

# referred to through ZCML
from zope.app.publisher.browser.resourcemeta import resource
from zope.app.publisher.browser.resourcemeta import resourceDirectory
from zope.app.publisher.browser.i18nresourcemeta import I18nResource
from zope.app.publisher.browser.viewmeta import view

# BBB 2006/02/18, to be removed after 12 months
import zope.deprecation
zope.deprecation.__show__.off()
from zope.publisher.interfaces.browser import ILayer
zope.deprecation.__show__.on()

# BBB 2006/02/18, to be removed after 12 months
def layer(_context, name=None, interface=None, base=IBrowserRequest,
          bbb_aware=False):
    """Provides a new layer.

    First, let's ignore the warnigns:

    >>> showwarning = warnings.showwarning
    >>> warnings.showwarning = lambda *a, **k: None

    >>> class Info(object):
    ...     file = u'doctest'
    ...     line = 1
    ... 
    >>> class Context(object):
    ...     info = Info()
    ...     def __init__(self): self.actions = []
    ...     def action(self, **kw): self.actions.append(kw)

    Possibility 1: The Old Way
    --------------------------

    >>> context = Context()
    >>> layer(context, u'layer1')
    >>> iface = context.actions[0]['args'][1]
    >>> iface.getName()
    'layer1'
    >>> ILayer.providedBy(iface)
    True
    >>> import sys
    >>> hasattr(sys.modules['zope.app.layers'], 'layer1')
    True

    >>> del sys.modules['zope.app.layers'].layer1

    Possibility 2: Providing a custom base interface
    ------------------------------------------------
    
    >>> class BaseLayer(IBrowserRequest):
    ...     pass
    >>> context = Context()
    >>> layer(context, u'layer1', base=BaseLayer)
    >>> iface = context.actions[0]['args'][1]
    >>> iface.getName()
    'layer1'
    >>> iface.__bases__
    (<InterfaceClass zope.app.publisher.browser.metaconfigure.BaseLayer>,)
    >>> hasattr(sys.modules['zope.app.layers'], 'layer1')
    True

    >>> del sys.modules['zope.app.layers'].layer1

    Possibility 3: Define a Layer just through an Interface
    -------------------------------------------------------

    >>> class layer1(IBrowserRequest):
    ...     pass
    >>> context = Context()
    >>> layer(context, interface=layer1)
    >>> context.actions[0]['args'][1] is layer1
    True
    >>> hasattr(sys.modules['zope.app.layers'], 'layer1')
    False

    Possibility 4: Use an Interface and a Name
    ------------------------------------------

    >>> context = Context()
    >>> layer(context, name='layer1', interface=layer1)
    >>> context.actions[0]['args'][1] is layer1
    True
    >>> hasattr(sys.modules['zope.app.layers'], 'layer1')
    True
    >>> import pprint
    >>> pprint.pprint([action['discriminator'] for action in context.actions])
    [('interface', 'zope.app.publisher.browser.metaconfigure.layer1'),
     ('layer', 'layer1')]

    Here are some disallowed configurations.

    >>> context = Context()
    >>> layer(context, 'foo,bar')
    Traceback (most recent call last):
    ...
    TypeError: Commas are not allowed in layer names.
    >>> layer(context)
    Traceback (most recent call last):
    ...
    ConfigurationError: You must specify the 'name' or 'interface' attribute.
    >>> layer(context, base=BaseLayer)
    Traceback (most recent call last):
    ...
    ConfigurationError: You must specify the 'name' or 'interface' attribute.

    >>> layer(context, interface=layer1, base=BaseLayer)
    Traceback (most recent call last):
    ...
    ConfigurationError: You cannot specify the 'interface' and 'base' together.

    Enabling the warnings again:

    >>> warnings.showwarning = showwarning
    """
    if name is not None and ',' in name:
        raise TypeError("Commas are not allowed in layer names.")
    if name is None and interface is None: 
        raise ConfigurationError(
            "You must specify the 'name' or 'interface' attribute.")
    if interface and not interface.extends(IBrowserRequest):
        raise ConfigurationError(
            "The layer interface must extend `IBrowserRequest`.")
    if base is not IBrowserRequest and not base.extends(IBrowserRequest):
        raise ConfigurationError(
            "The base interface must extend `IBrowserRequest`.")
    if interface is not None and base is not IBrowserRequest:
        raise ConfigurationError(
            "You cannot specify the 'interface' and 'base' together.")

    if interface is None:
        if not bbb_aware:
            warnings.warn_explicit(
                'Creating layers via ZCML has been deprecated.  The '
                'browser:layer directive will be removed in Zope 3.5.  Layers '
                'are now interfaces extending zope.publisher.interfaces.browser'
                '.IBrowserRequest. They do not need further registration.',
                DeprecationWarning, _context.info.file, _context.info.line)
        interface = InterfaceClass(str(name), (base, ),
                                   __doc__='Layer: %s' %str(name),
                                   __module__='zope.app.layers')
        # Add the layer to the layers module.
        # Note: We have to do this immediately, so that directives using the
        # InterfaceField can find the layer.
        layers.set(name, interface)
        path = 'zope.app.layers.'+name
    else:
        if not bbb_aware:
            warnings.warn_explicit(
                'Layer interfaces do not require registration anymore.  The '
                'browser:layer directive will be removed in Zope 3.5.',
                DeprecationWarning, _context.info.file, _context.info.line)
        path = interface.__module__ + '.' + interface.getName()

        # If a name was specified, make this layer available under this name.
        # Note that the layer will be still available under its path, since it
        # is an adapter, and the `LayerField` can resolve paths as well.
        if name is None:
            name = path
        else:
            # Make the interface available in the `zope.app.layers` module, so
            # that other directives can find the interface under the name
            # before the CA is setup.
            layers.set(name, interface)

    # Register the layer interface as an interface
    _context.action(
        discriminator = ('interface', path),
        callable = provideInterface,
        args = (path, interface),
        kw = {'info': _context.info}
        )

    directlyProvides(interface, ILayer)

    # Register the layer interface as a layer
    _context.action(
        discriminator = ('layer', name),
        callable = provideInterface,
        args = (name, interface, ILayer, _context.info)
        )

# BBB 2006/02/18, to be removed after 12 months
def skin(_context, name=None, interface=None, layers=None):
    """Provides a new skin.

    First, let's ignore the warnigns:
    >>> showwarning = warnings.showwarning
    >>> warnings.showwarning = lambda *a, **k: None

    >>> import pprint
    >>> class Info(object):
    ...     file = u'doctest'
    ...     line = 1
    ... 
    >>> class Context(object):
    ...     info = Info()
    ...     def __init__(self): self.actions = []
    ...     def action(self, **kw): self.actions.append(kw)

    >>> class Layer1(ILayer): pass
    >>> class Layer2(ILayer): pass

    Possibility 1: The Old Way
    --------------------------
    
    >>> context = Context()
    >>> skin(context, u'skin1', layers=[Layer1, Layer2])
    >>> iface = context.actions[3]['args'][1]
    >>> iface.getName()
    'skin1'
    >>> pprint.pprint(iface.__bases__)
    (<InterfaceClass zope.app.publisher.browser.metaconfigure.Layer1>,
     <InterfaceClass zope.app.publisher.browser.metaconfigure.Layer2>)
    >>> import sys
    >>> hasattr(sys.modules['zope.app.skins'], 'skin1')
    True

    >>> del sys.modules['zope.app.skins'].skin1

    Possibility 2: Just specify an interface
    ----------------------------------------

    >>> class skin1(Layer1, Layer2):
    ...     pass

    >>> context = Context()
    >>> skin(context, interface=skin1)
    >>> context.actions[0]['args'][1] is skin1
    True

    Possibility 3: Specify an interface and a Name
    ----------------------------------------------

    >>> context = Context()
    >>> skin(context, name='skin1', interface=skin1)
    >>> context.actions[0]['args'][1] is skin1
    True
    >>> import pprint
    >>> pprint.pprint([action['discriminator'] for action in context.actions])
    [('skin', 'skin1'),
     ('interface', 'zope.app.publisher.browser.metaconfigure.skin1'),
     ('skin', 'zope.app.publisher.browser.metaconfigure.skin1')]

    Here are some disallowed configurations.

    >>> context = Context()
    >>> skin(context)
    Traceback (most recent call last):
    ...
    ConfigurationError: You must specify the 'name' or 'interface' attribute.
    >>> skin(context, layers=[Layer1])
    Traceback (most recent call last):
    ...
    ConfigurationError: You must specify the 'name' or 'interface' attribute.

    Enabling the warnings again:
    >>> warnings.showwarning = showwarning
    """
    if name is None and interface is None: 
        raise ConfigurationError(
            "You must specify the 'name' or 'interface' attribute.")

    if name is not None and layers is not None:
        warnings.warn_explicit(
            'Creating skins via ZCML has been deprecated.  The browser:skin '
            'directive will be removed in Zope 3.5.  Skins are now interfaces '
            'extending zope.publisher.interfaces.browser.IBrowserRequest. '
            'They are registered using the \'interface\' directive.',
            DeprecationWarning, _context.info.file, _context.info.line)
        interface = InterfaceClass(str(name), layers,
                                   __doc__='Skin: %s' %str(name),
                                   __module__='zope.app.skins')

        # Add the layer to the skins module.
        # Note: We have to do this immediately, so that directives using the
        # InterfaceField can find the layer.
        skins.set(name, interface)
        path = 'zope.app.skins'+name

        # Register the layers
        for layer in layers:
            _context.action(
                discriminator = None,
                callable = provideInterface,
                args = (layer.getName(), layer, ILayer, _context.info)
            )    

    else:
        path = interface.__module__ + '.' + interface.getName()
        warnings.warn_explicit(
            'The browser:skin directive has been deprecated and will be '
            'removed in Zope 3.5.  Skins are now simply registered using '
            'the \'interface\' directive:\n'
            '  <interface\n'
            '      interface="%s"\n'
            '      type="zope.publisher.interfaces.browser.IBrowserSkinType"\n'
            '      name="%s"\n'
            '      />' % (path, name),
            DeprecationWarning, _context.info.file, _context.info.line)

        # Register the skin interface as a skin using the passed name.
        if name is not None:
            _context.action(
                discriminator = ('skin', name),
                callable = provideInterface,
                args = (name, interface, IBrowserSkinType, _context.info)
                )
        
        name = path

    # Register the skin interface as an interface
    _context.action(
        discriminator = ('interface', path),
        callable = provideInterface,
        args = (path, interface),
        kw = {'info': _context.info}
        )

    # Register the skin interface as a skin
    _context.action(
        discriminator = ('skin', name),
        callable = provideInterface,
        args = (name, interface, IBrowserSkinType, _context.info)
        )

def setDefaultSkin(name, info=''):
    """Set the default skin.

    >>> from zope.interface import directlyProvides
    >>> from zope.app.testing import ztapi

    >>> class Skin1: pass
    >>> directlyProvides(Skin1, IBrowserSkinType)

    >>> ztapi.provideUtility(IBrowserSkinType, Skin1, 'Skin1')
    >>> setDefaultSkin('Skin1')
    >>> adapters = zapi.getSiteManager().adapters

	Lookup the default skin for a request that has the 

    >>> adapters.lookup((IBrowserRequest,), IDefaultSkin, '') is Skin1
    True
    """
    skin = zapi.getUtility(IBrowserSkinType, name)
    handler('registerAdapter',
            skin, (IBrowserRequest,), IDefaultSkin, '', info),

def defaultSkin(_context, name):

    _context.action(
        discriminator = 'defaultSkin',
        callable = setDefaultSkin,
        args = (name, _context.info)
        )

def defaultView(_context, name, for_=None, layer=IBrowserRequest):

    _context.action(
        discriminator = ('defaultViewName', for_, layer, name),
        callable = handler,
        args = ('registerAdapter',
                name, (for_, layer), IDefaultViewName, '', _context.info)
        )

    if for_ is not None:
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = ('', for_)
            )
