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

$Id: process.py 67734 2006-04-28 19:16:23Z adamg $
"""

import persistent

import zope.cachedescriptors.property

from zope import component, interface

import zope.event

from zope.wfmc import interfaces

def always_true(data):
    return True

class TransitionDefinition(object):

    interface.implements(interfaces.ITransitionDefinition)

    def __init__(self, from_, to, condition=always_true, id=None):
        self.id = id
        self.from_ = from_
        self.to = to
        self.condition = condition

    def __repr__(self):
        return "TransitionDefinition(from=%r, to=%r)" %(self.from_, self.to)


class ProcessDefinition(object):

    interface.implements(interfaces.IProcessDefinition)
    
    TransitionDefinitionFactory = TransitionDefinition

    def __init__(self, id, integration=None):
        self.id = id
        self.integration = integration
        self.activities = {}
        self.transitions = []
        self.applications = {}
        self.participants = {}
        self.parameters = ()

    def __repr__(self):
        return "ProcessDefinition(%r)" % self.id

    def defineActivities(self, **activities):
        self._dirty()
        for id, activity in activities.items():
            activity.id = id
            if activity.__name__ is None:
                activity.__name__ = self.id + '.' + id
            activity.process = self
            self.activities[id] = activity

    def defineTransitions(self, *transitions):
        self._dirty()
        self.transitions.extend(transitions)

        # Compute activity transitions based on transition data:
        activities = self.activities
        for transition in transitions:
            activities[transition.from_].transitionOutgoing(transition)
            activities[transition.to].incoming += (transition, )

    def defineApplications(self, **applications):
        for id, application in applications.items():
            application.id = id
            self.applications[id] = application

    def defineParticipants(self, **participants):
        for id, participant in participants.items():
            participant.id = id
            self.participants[id] = participant

    def defineParameters(self, *parameters):
        self.parameters += parameters

    def _start(self):
        # Return an initial transition

        activities = self.activities

        # Find the start, making sure that there is one and that there
        # aren't any activities with no transitions:
        start = ()
        for aid, activity in activities.items():
            if not activity.incoming:
                start += ((aid, activity), )
                if not activity.outgoing:
                    raise interfaces.InvalidProcessDefinition(
                        "Activity %s has no transitions" %aid)

        if len(start) != 1:
            if start:
                raise interfaces.InvalidProcessDefinition(
                    "Multiple start activities",
                    [id for (id, a) in start]
                    )
            else:
                raise interfaces.InvalidProcessDefinition(
                    "No start activities")

        return self.TransitionDefinitionFactory(None, start[0][0])

    _start = zope.cachedescriptors.property.Lazy(_start)

    def __call__(self, context=None):
        return Process(self, self._start, context)

    def _dirty(self):
        try:
            del self._start
        except AttributeError:
            pass

class ActivityDefinition(object):

    interface.implements(interfaces.IActivityDefinition)

    performer = ''
    process = None

    def __init__(self, __name__=None):
        self.__name__ = __name__
        self.incoming = self.outgoing = ()
        self.transition_outgoing = self.explicit_outgoing = ()
        self.applications = ()
        self.andJoinSetting = self.andSplitSetting = False

    def andSplit(self, setting):
        self.andSplitSetting = setting

    def andJoin(self, setting):
        self.andJoinSetting = setting

    def addApplication(self, application, actual=()):
        app = self.process.applications[application]
        formal = app.parameters
        if len(formal) != len(actual):
            raise TypeError("Wrong number of parameters => "
                            "Actual=%s, Formal=%s for Application %s with id=%s"
                            %(actual, formal, app, app.id))
        self.applications += ((application, formal, tuple(actual)), )

    def definePerformer(self, performer):
        self.performer = performer

    def addOutgoing(self, transition_id):
        self.explicit_outgoing += (transition_id,)
        self.computeOutgoing()

    def transitionOutgoing(self, transition):
        self.transition_outgoing += (transition,)
        self.computeOutgoing()

    def computeOutgoing(self):
        if self.explicit_outgoing:
            transitions = dict([(t.id, t) for t in self.transition_outgoing])
            self.outgoing = ()
            for tid in self.explicit_outgoing:
                transition = transitions.get(tid)
                if transition is not None:
                    self.outgoing += (transition,)
        else:
            self.outgoing = self.transition_outgoing

    def __repr__(self):
        return "<ActivityDefinition %r>" %self.__name__


class Process(persistent.Persistent):

    interface.implements(interfaces.IProcess)

    def __init__(self, definition, start, context=None):
        self.process_definition_identifier = definition.id
        self.startTransition = start
        self.context = context
        self.activities = {}
        self.nextActivityId = 0
        self.workflowRelevantData = WorkflowData()
        self.applicationRelevantData = WorkflowData()

    def definition(self):
        return component.getUtility(
            interfaces.IProcessDefinition,
            self.process_definition_identifier,
            )
    definition = property(definition)

    def start(self, *arguments):
        if self.activities:
            raise TypeError("Already started")

        definition = self.definition
        data = self.workflowRelevantData
        args = arguments
        for parameter in definition.parameters:
            if parameter.input:
                arg, args = args[0], args[1:]
                setattr(data, parameter.__name__, arg)
        if args:
            raise TypeError("Too many arguments. Expected %s. got %s" %
                            (len(definition.parameters), len(arguments)))

        zope.event.notify(ProcessStarted(self))
        self.transition(None, (self.startTransition, ))

    def outputs(self):
        outputs = []
        for parameter in self.definition.parameters:
            if parameter.output:
                outputs.append(
                    getattr(self.workflowRelevantData,
                            parameter.__name__))

        return outputs

    def _finish(self):
        if self.context is not None:
            self.context.processFinished(self, *self.outputs())

        zope.event.notify(ProcessFinished(self))


    def transition(self, activity, transitions):
        if transitions:
            definition = self.definition

            for transition in transitions:
                activity_definition = definition.activities[transition.to]
                next = None
                if activity_definition.andJoinSetting:
                    # If it's an and-join, we want only one.
                    for i, a in self.activities.items():
                        if a.activity_definition_identifier == transition.to:
                            # we already have the activity -- use it
                            next = a
                            break

                if next is None:
                    next = Activity(self, activity_definition)
                    self.nextActivityId += 1
                    next.id = self.nextActivityId

                zope.event.notify(Transition(activity, next))
                self.activities[next.id] = next
                next.start(transition)

        if activity is not None:
            del self.activities[activity.id]
            if not self.activities:
                self._finish()

        self._p_changed = True

    def __repr__(self):
        return "Process(%r)" % self.process_definition_identifier

class WorkflowData(persistent.Persistent):
    """Container for workflow-relevant and application-relevant data
    """

class ProcessStarted:
    interface.implements(interfaces.IProcessStarted)

    def __init__(self, process):
        self.process = process

    def __repr__(self):
        return "ProcessStarted(%r)" % self.process

class ProcessFinished:
    interface.implements(interfaces.IProcessFinished)

    def __init__(self, process):
        self.process = process

    def __repr__(self):
        return "ProcessFinished(%r)" % self.process


class Activity(persistent.Persistent):

    interface.implements(interfaces.IActivity)

    def __init__(self, process, definition):
        self.process = process
        self.activity_definition_identifier = definition.id

        integration = process.definition.integration

        workitems = {}
        if definition.applications:

            participant = integration.createParticipant(
                self,
                process.process_definition_identifier,
                definition.performer,
                )

            i = 0
            for application, formal, actual in definition.applications:
                workitem = integration.createWorkItem(
                    participant,
                    process.process_definition_identifier,
                    application,
                    )
                i += 1
                workitem.id = i
                workitems[i] = workitem, application, formal, actual

        self.workitems = workitems

    def definition(self):
        return self.process.definition.activities[
            self.activity_definition_identifier]
    definition = property(definition)

    incoming = ()
    def start(self, transition):
        # Start the activity, if we've had enough incoming transitions

        definition = self.definition

        if definition.andJoinSetting:
            if transition in self.incoming:
                raise interfaces.ProcessError(
                    "Repeated incoming %s with id='%s' "
                    "while waiting for and completion"
                    %(transition, transition.id))
            self.incoming += (transition, )

            if len(self.incoming) < len(definition.incoming):
                return # not enough incoming yet

        zope.event.notify(ActivityStarted(self))

        if self.workitems:
            for workitem, app, formal, actual in self.workitems.values():
                args = []
                for parameter, name in zip(formal, actual):
                    if parameter.input:
                        args.append(
                            getattr(self.process.workflowRelevantData, name))
                workitem.start(*args)
        else:
            # Since we don't have any work items, we're done
            self.finish()

    def workItemFinished(self, work_item, *results):
        unused, app, formal, actual = self.workitems.pop(work_item.id)
        self._p_changed = True
        res = results
        for parameter, name in zip(formal, actual):
            if parameter.output:
                v = res[0]
                res = res[1:]
                setattr(self.process.workflowRelevantData, name, v)

        if res:
            raise TypeError("Too many results")

        zope.event.notify(WorkItemFinished(
            work_item, app, actual, results))

        if not self.workitems:
            self.finish()

    def finish(self):
        zope.event.notify(ActivityFinished(self))

        definition = self.definition

        transitions = []
        for transition in definition.outgoing:
            if transition.condition(self.process.workflowRelevantData):
                transitions.append(transition)
                if not definition.andSplitSetting:
                    break # xor split, want first one

        self.process.transition(self, transitions)

    def __repr__(self):
        return "Activity(%r)" % (
            self.process.process_definition_identifier + '.' +
            self.activity_definition_identifier
            )

class WorkItemFinished:

    def __init__(self, workitem, application, parameters, results):
        self.workitem =  workitem
        self.application = application
        self.parameters = parameters
        self.results = results

    def __repr__(self):
        return "WorkItemFinished(%r)" % self.application

class Transition:

    def __init__(self, from_, to):
        self.from_ = from_
        self.to = to

    def __repr__(self):
        return "Transition(%r, %r)" % (self.from_, self.to)

class ActivityFinished:

    def __init__(self, activity):
        self.activity = activity

    def __repr__(self):
        return "ActivityFinished(%r)" % self.activity

class ActivityStarted:

    def __init__(self, activity):
        self.activity = activity

    def __repr__(self):
        return "ActivityStarted(%r)" % self.activity

class Parameter(object):

    interface.implements(interfaces.IParameterDefinition)

    input = output = False

    def __init__(self, name):
        self.__name__ = name

class OutputParameter(Parameter):

    output = True

class InputParameter(Parameter):

    input = True

class InputOutputParameter(InputParameter, OutputParameter):

    pass

class Application:

    interface.implements(interfaces.IApplicationDefinition)

    def __init__(self, *parameters):
        self.parameters = parameters

    def defineParameters(self, *parameters):
        self.parameters += parameters

    def __repr__(self):
        input = u', '.join([param.__name__ for param in self.parameters
                           if param.input == True])
        output = u', '.join([param.__name__ for param in self.parameters
                           if param.output == True])
        return "<Application %r: (%s) --> (%s)>" %(self.__name__, input, output)


class Participant:

    interface.implements(interfaces.IParticipantDefinition)

    def __init__(self, name=None):
        self.__name__ = name

    def __repr__(self):
        return "Participant(%r)" %self.__name__
