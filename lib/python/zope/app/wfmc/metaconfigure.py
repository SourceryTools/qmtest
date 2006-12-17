##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""ZCML directives for loading XPDL workflow definitions.

$Id: $
"""
__docformat__ = "reStructuredText"

import zope.interface
import zope.schema
import zope.configuration.fields
import zope.wfmc.interfaces
from zope import wfmc
from zope.wfmc import xpdl
from zope.component.zcml import utility

class IdefineXpdl(zope.interface.Interface):

    file = zope.configuration.fields.Path(
        title=u"File Name",
        description=u"The name of the xpdl file to read.",
        )

    process = zope.schema.TextLine(
        title=u"Process Name",
        description=u"The name of the process to read.",
        )

    id = zope.schema.Id(
        title=u"ID",
        description=(u"The identifier to use for the process.  "
                     u"Defaults to the process name."),
        )

    integration = zope.configuration.fields.GlobalObject(
        title=u"Integration component",
        description=(u"Python name of the integration object.  This"
                      " must identify an object in a module using the"
                      " full dotted name."),
        )

def defineXpdl(_context, file, process, id, integration):
    package = xpdl.read(open(file))
    definition = package[process]
    definition.id = id

    if not zope.wfmc.interfaces.IIntegration.providedBy(integration):
        raise TypeError("Not an IIntegration", integration)
    
    definition.integration = integration

    utility(_context, wfmc.interfaces.IProcessDefinition, definition, name=id)
