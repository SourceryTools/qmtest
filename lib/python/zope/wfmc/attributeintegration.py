##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Attribute-based integration components


$Id: attributeintegration.py 30314 2005-05-09 17:07:09Z jim $
"""

from zope.wfmc import interfaces
from zope import interface

class AttributeIntegration:
    """Integration component that uses simple attributes

    Subclasses provide attributes with suffices Participant or Application to
    provide participant and application factories of a given name.
    """

    interface.implements(interfaces.IIntegration)
    
    def createParticipant(self, activity,
                          process_definition_identifier, performer):
        return getattr(self, performer+'Participant')(activity)
        

    def createWorkItem(self, participant,
                       process_definition_identifier, application):
        return getattr(self, application+'WorkItem')(participant)
