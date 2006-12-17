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
"""Workflow-integration interfaces

$Id: interfaces.py 40506 2005-12-02 20:35:44Z mgedmin $
"""
__docformat__ = "reStructuredText"

from zope import interface

class IIntegration(interface.Interface):
    """Integration of a workflow definition with an application environment

    ``IIntegration`` objects provide methods for integrating workflow
    process definition with an application environment.
    """


    def createParticipant(activity, process_definition_identifier, performer):
        """Create a participant for an activity

        The process id and especially the performer (id) are used to
        select an appropriate participant type.
        """

    def createWorkItem(participant,
                       process_definition_identifier, application):
        """Create a work item for the given participant

        The process id and especially the application (id) are used to
        select an appropriate work-item type.
        """

class IProcessDefinition(interface.Interface):
    """Process definition

    A process definition defines a particular workflow and define the control
    and flow of the work. You can think of them as the workflow blueprint.
    """

    id = interface.Attribute("Process-definition identifier")

    __name__ = interface.Attribute("Name")

    description = interface.Attribute("Description")

    integration = interface.Attribute(
        """Environment-integration component

        The integration component is used to hook up a process
        definition with an application environment.

        This is an ``IIntegration``.
        """
        )

    participants = interface.Attribute(
        """Process participants

        This is a mapping from participant id to participant definition
        """
        )

    activities = interface.Attribute(
        """Process activities

        This is a mapping from activity id to activity definition
        """
        )

    applications = interface.Attribute(
        """Process applications

        This is a mapping from application id to participant definitions
        """
        )

    def defineActivities(**activities):
        """Add activity definitions to the collection of defined activities

        Activity definitions are supplied as keyword arguments.  The
        keywords provide activity identifiers.  The values are
        IActivityDefinition objects.

        """

    def defineTransitions(*transitions):
        """Add transition definitions

        The transitions are ITransition objects.
        """

    def defineParticipants(**participants):
        """Declare participants

        The participants are provided as keyword arguments.
        Participant identifiers are supplied as the keywords and the
        definitions are supplied as values.  The definitions are
        IParticipantDefinition objects.
        """

    def defineApplications(**applications):
        """Declare applications

        The applications are provided as keyword arguments.
        Application identifiers are supplied as the keywords and the
        definitions are supplied as values.  The definitions are
        IApplicationDefinition objects.
        """

    def defineParameters(*parameters):
        """Declate process parameters

        Input parameters are set as workflow-relevant data.  Output
        parameters are passed from workflow-relevant data to the
        processFinished method of process-instances process contexts.

        """

class IActivityDefinition(interface.Interface):
    """Activity definition
    """

    id = interface.Attribute("Activity identifier")

    def addApplication(id, *parameters):
        """Declare that the activity uses the identified activity

        The application identifier must match an application declared
        for the process.

        Parameter definitions can be given as positional arguments.
        The parameter definition directions must match those given in
        the application definition.
        """

    def definePerformer(performer):
        """Set the activity performer

        The argument must be the identifier of a participant defined
        for the enclosing process.
        """

    def setAndSplit(setting):
        """Provide an and-split setting

        If the setting is true, then the activity will use an "and" split.
        """

    def setAndJoin(setting):
        """Provide an and-join setting

        If the setting is true, then the activity will use an "and" join.
        """

class ITransitionDefinition(interface.Interface):
    """Transition definition
    """

class IProcess(interface.Interface):
    """Process instance
    """

    definition = interface.Attribute("Process definition")

    workflowRelevantData = interface.Attribute(
        """Workflow-relevant data

        Object with attributes containing data used in conditions and
        to pass data as parameters between applications
        """
        )

    applicationRelevantData = interface.Attribute(
        """Application-relevant data

        Object with attributes containing data used to pass data as
        shared data for applications

        """
        )

class IProcessContext(interface.Interface):
    """Object that can receive process results.
    """

    def processFinished(process, *results):
        """Receive notification of process completion, with results
        """

class IActivity(interface.Interface):
    """Activity instance
    """

    id = interface.Attribute(
        """Activity identifier

        This identifier is set by the process instance

        """)

    definition = interface.Attribute("Activity definition")

    def workItemFinished(work_item, *results):
        """Notify the activity that the work item has been completed.
        """

class IApplicationDefinition(interface.Interface):
    """Application definition
    """

    __name__ = interface.Attribute("Name")

    description = interface.Attribute("Description")

    parameters = interface.Attribute(
        "A sequence of parameter definitions")

class IParameterDefinition(interface.Interface):
    """Parameter definition
    """

    name = interface.Attribute("Parameter name")

    input = interface.Attribute("Is this an input parameter?")

    output = interface.Attribute("Is this an output parameter?")

class IParticipantDefinition(interface.Interface):
    """Participant definition
    """

class IParticipant(interface.Interface):
    """Workflow participant
    """

    __name__ = interface.Attribute("Name")

    description = interface.Attribute("Description")

class IWorkItem(interface.Interface):
    """Work items
    """

    id = interface.Attribute(
        """Item identifier

        This identifier is set by the activity instance

        """)

    def start(*arguments):
        """Start the work
        """


class InvalidProcessDefinition(Exception):
    """A process definition isn't valid in some way.
    """

class ProcessError(Exception):
    """An error occurred in execution of a process.
    """

class IProcessStarted(interface.Interface):
    """A process has begun executing
    """

    process = interface.Attribute("The process")

class IProcessFinished(interface.Interface):
    """A process has finished executing
    """

    process = interface.Attribute("The process")
