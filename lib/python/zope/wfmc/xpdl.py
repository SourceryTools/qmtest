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
"""XPDL reader for process definitions

$Id: xpdl.py 67734 2006-04-28 19:16:23Z adamg $
"""

import sys
import xml.sax
import xml.sax.xmlreader
import xml.sax.handler

import zope.wfmc.process

xpdlns = "http://www.wfmc.org/2002/XPDL1.0"


class HandlerError(Exception):

    def __init__(self, orig, tag, locator):
        self.orig = orig
        self.tag = tag
        self.xml = locator.getSystemId()
        self.line = locator.getLineNumber()

    def __repr__(self):
        return ('%r\nFile "%s", line %s. in %s'
                % (self.orig, self.xml, self.line, self.tag))

    def __str__(self):
        return ('%s\nFile "%s", line %s. in %s'
                % (self.orig, self.xml, self.line, self.tag))


class Package(dict):

    def __init__(self):
        self.applications = {}
        self.participants = {}
    
    def defineApplications(self, **applications):
        for id, application in applications.items():
            application.id = id
            self.applications[id] = application

    def defineParticipants(self, **participants):
        for id, participant in participants.items():
            participant.id = id
            self.participants[id] = participant


class XPDLHandler(xml.sax.handler.ContentHandler):

    start_handlers = {}
    end_handlers = {}
    text = u''
    
    ProcessDefinitionFactory = zope.wfmc.process.ProcessDefinition
    ParticipantFactory = zope.wfmc.process.Participant
    ApplicationFactory = zope.wfmc.process.Application
    ActivityDefinitionFactory = zope.wfmc.process.ActivityDefinition
    TransitionDefinitionFactory = zope.wfmc.process.TransitionDefinition

    def __init__(self, package):
        self.package = package
        self.stack = []

    def startElementNS(self, name, qname, attrs):
        handler = self.start_handlers.get(name)
        if handler:
            try:
                result = handler(self, attrs)
            except:
                raise HandlerError(sys.exc_info()[1], name[1], self.locator
                    ), None, sys.exc_info()[2]
        else:
            result = None

        if result is None:
            # Just dup the top of the stack
            result = self.stack[-1]
            
        self.stack.append(result)
        self.text = u''

    def endElementNS(self, name, qname):
        last = self.stack.pop()
        handler = self.end_handlers.get(name)
        if handler:
            try:
                handler(self, last)
            except:
                raise HandlerError(sys.exc_info()[1], name[1], self.locator
                    ), None, sys.exc_info()[2]

        self.text = u''

    def characters(self, text):
        self.text += text

    def setDocumentLocator(self, locator):
        self.locator = locator

    ######################################################################
    # Application handlers

    # Pointless container elements that we want to "ignore" by having them
    # dup their containers:
    def Package(self, attrs):
        package = self.package
        package.id = attrs[(None, 'Id')]
        package.__name__ = attrs.get((None, 'Name'))
        return package
    start_handlers[(xpdlns, 'Package')] = Package

    def WorkflowProcess(self, attrs):
        id = attrs[(None, 'Id')]
        process = self.ProcessDefinitionFactory(id)
        process.__name__ = attrs.get((None, 'Name'))

        # Copy package data:
        process.defineApplications(**self.package.applications)
        process.defineParticipants(**self.package.participants)

        self.package[id] = process
        return process
    start_handlers[(xpdlns, 'WorkflowProcess')] = WorkflowProcess

    paramter_types = {
        'IN': zope.wfmc.process.InputParameter,
        'OUT': zope.wfmc.process.OutputParameter,
        'INOUT': zope.wfmc.process.InputOutputParameter,
        }
        
    
    def FormalParameter(self, attrs):
        mode = attrs.get((None, 'Mode'), 'IN')
        id = attrs[(None, 'Id')]
        self.stack[-1].defineParameters(*[self.paramter_types[mode](id)])
    start_handlers[(xpdlns, 'FormalParameter')] = FormalParameter
    
    def Participant(self, attrs):
        id = attrs[(None, 'Id')]
        name = attrs.get((None, 'Name'))
        participant = self.ParticipantFactory(name)
        self.stack[-1].defineParticipants(**{str(id): participant})
    start_handlers[(xpdlns, 'Participant')] = Participant

    def Application(self, attrs):
        id = attrs[(None, 'Id')]
        name = attrs.get((None, 'Name'))
        app = self.ApplicationFactory()
        app.id = id
        if name:
            app.__name__ = name
        return app
    start_handlers[(xpdlns, 'Application')] = Application
    
    def application(self, app):
        self.stack[-1].defineApplications(**{str(app.id): app})
    end_handlers[(xpdlns, 'Application')] = application

    def description(self, ignored):
        if self.stack[-1] is not None:
            self.stack[-1].description = self.text
    end_handlers[(xpdlns, 'Description')] = description

    ######################################################################
    # Activity definitions

    def ActivitySet(self, attrs):
        raise NotImplementedError("ActivitySet")
    end_handlers[(xpdlns, 'ActivitySet')] = ActivitySet

    def Activity(self, attrs):
        id = attrs[(None, 'Id')]
        name = attrs.get((None, 'Name'))
        activity = self.ActivityDefinitionFactory(name)
        activity.id = id
        self.stack[-1].defineActivities(**{str(id): activity})
        return activity
    start_handlers[(xpdlns, 'Activity')] = Activity

    def Tool(self, attrs):
        return Tool(attrs[(None, 'Id')])
    start_handlers[(xpdlns, 'Tool')] = Tool

    def tool(self, tool):
        self.stack[-1].addApplication(tool.id, tool.parameters)
    end_handlers[(xpdlns, 'Tool')] = tool

    def actualparameter(self, ignored):
        self.stack[-1].parameters += (self.text, )
    end_handlers[(xpdlns, 'ActualParameter')] = actualparameter

    def performer(self, ignored):
        self.stack[-1].definePerformer(self.text.strip())
    end_handlers[(xpdlns, 'Performer')] = performer

    def Join(self, attrs):
        Type = attrs.get((None, 'Type'))
        if Type == u'AND':
            self.stack[-1].andJoin(True)
    start_handlers[(xpdlns, 'Join')] = Join

    def Split(self, attrs):
        Type = attrs.get((None, 'Type'))
        if Type == u'AND':
            self.stack[-1].andSplit(True)
    start_handlers[(xpdlns, 'Split')] = Split

    def TransitionRef(self, attrs):
        Id = attrs.get((None, 'Id'))
        self.stack[-1].addOutgoing(Id)
    start_handlers[(xpdlns, 'TransitionRef')] = TransitionRef
        

    # Activity definitions
    ######################################################################

    def Transition(self, attrs):
        id = attrs[(None, 'Id')]
        name = attrs.get((None, 'Name'))
        from_ = attrs.get((None, 'From'))
        to = attrs.get((None, 'To'))
        transition = self.TransitionDefinitionFactory(from_, to)
        transition.id = id
        return transition
    start_handlers[(xpdlns, 'Transition')] = Transition
    
    def transition(self, transition):
        self.stack[-1].defineTransitions(transition)
    end_handlers[(xpdlns, 'Transition')] = transition
    
    def condition(self, ignored):
        assert isinstance(self.stack[-1],
                          self.TransitionDefinitionFactory)

        text = self.text
        self.stack[-1].condition = TextCondition("(%s)" % text)
    end_handlers[(xpdlns, 'Condition')] = condition


class Tool:

    def __init__(self, id):
        self.id = id

    parameters = ()
  
class TextCondition:

    def __init__(self, source):
        self.source = source

        # make sure that we can compile the source
        compile(source, '<string>', 'eval')

    def __getstate__(self):
        return {'source': self.source}

    def __call__(self, data):
        # We *depend* on being able to use the data's dict.
        # TODO This needs to be part of the contract.
        try:
            compiled = self._v_compiled
        except AttributeError:
            self._v_compiled = compile(self.source, '<string>', 'eval')
            compiled = self._v_compiled

        return eval(compiled, {'__builtins__': None}, data.__dict__)
    

def read(file):
    src = xml.sax.xmlreader.InputSource(getattr(file, 'name', '<string>'))
    src.setByteStream(file)
    parser = xml.sax.make_parser()
    package = Package()
    parser.setContentHandler(XPDLHandler(package))
    parser.setFeature(xml.sax.handler.feature_namespaces, True)
    parser.parse(src)
    return package
    
