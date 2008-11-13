##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Processes

$Id: integration.py 30314 2005-05-09 17:07:09Z jim $
"""

from zope import component, interface
from zope.wfmc import interfaces

interface.moduleProvides(interfaces.IIntegration)
    
def createParticipant(activity, process_definition_identifier, performer):
    participant = component.queryAdapter(
        activity, interfaces.IParticipant,
        process_definition_identifier + '.' + performer)

    if participant is None:
        participant = component.getAdapter(
            activity, interfaces.IParticipant, '.' + performer)

    return participant

def createWorkItem(participant,
                   process_definition_identifier, application):

    workitem = component.queryAdapter(
        participant, interfaces.IWorkItem,
        process_definition_identifier + '.' + application)
    if workitem is None:
        workitem = component.getAdapter(
            participant, interfaces.IWorkItem, '.' + application)

    return workitem
