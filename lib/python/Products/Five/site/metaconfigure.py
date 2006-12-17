##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Five-specific directive handlers

These directives are specific to Five and have no equivalents in Zope 3.

$Id: fiveconfigure.py 18581 2005-10-14 16:54:25Z regebro $
"""
from zope.interface import classImplements, classImplementsOnly, implementedBy
from zope.interface.interface import InterfaceClass
from zope.configuration.exceptions import ConfigurationError
from zope.component.zcml import adapter
from zope.app.component.interfaces import IPossibleSite

from Products.Five.site.localsite import FiveSite

import logging, warnings

LOG = logging.getLogger('Five')

_localsite_monkies = []
def classSiteHook(class_, site_class):
    if class_ in _localsite_monkies:
        LOG.warn("Class %s already has a site hook" % class_)        
    else:
        _localsite_monkies.append(class_)
    setattr(class_, 'getSiteManager', site_class.getSiteManager.im_func)
    setattr(class_, 'setSiteManager', site_class.setSiteManager.im_func)
    

def installSiteHook(_context, class_, site_class=None):
    warnings.warn_explicit("The five:localsite directive is deprecated and "
                           "will be removed in Zope 2.12. \n"
                           "See Five/doc/localsite.txt .",
                           DeprecationWarning, 
                           _context.info.file, _context.info.line)
    if site_class is not None:
        _context.action(
            discriminator = (class_,),
            callable = classSiteHook,
            args=(class_, site_class)
            )
    if not IPossibleSite.implementedBy(class_):
        _context.action(
            discriminator = (class_, IPossibleSite),
            callable = classImplements,
            args=(class_, IPossibleSite)
            )

# clean up code

def uninstallSiteHooks():
    for class_ in _localsite_monkies:
        _localsite_monkies.remove(class_)
        delattr(class_, 'getSiteManager')
        delattr(class_, 'setSiteManager')
        classImplementsOnly(class_, implementedBy(class_)-IPossibleSite)

from zope.testing.cleanup import addCleanUp
addCleanUp(uninstallSiteHooks)
del addCleanUp
