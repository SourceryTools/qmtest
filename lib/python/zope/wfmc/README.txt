Workflow-Management Coalition Workflow Engine
=============================================

This package provides an implementation of a Workflow-Management
Coalition (WFMC) workflow engine.  The engine is provided as a
collection of workflow process components.  Workflow processes can be
defined in Python or via the XML Process-Definition Language, XPDL.

In this document, we'll look at Python-defined process definitions:

    >>> from zope.wfmc import process
    >>> pd = process.ProcessDefinition('sample')

The argument to the process is a process id.

A process has a number of parts.  Let's look at a sample review
process::

                              -----------
                           -->| Publish |
  ----------   ---------- /   -----------
  | Author |-->| Review |-    ----------
  ----------   ---------- \-->| Reject |
                              ----------

Here we have a single start activity and 2 end activities.  We could
have modeled this with a single end activity, but that is not
required.  A single start activity *is* required. A process definition
has a set of activities, with transitions between them.  Let's define
the activities for our process definition:

    >>> pd.defineActivities(
    ...     author  = process.ActivityDefinition(),
    ...     review  = process.ActivityDefinition(),
    ...     publish = process.ActivityDefinition(),
    ...     reject  = process.ActivityDefinition(),
    ...     )

We supply activities as keyword arguments. The argument names provide
activity ids that we'll use when defining transitions:

    >>> pd.defineTransitions(
    ...     process.TransitionDefinition('author', 'review'),
    ...     process.TransitionDefinition('review', 'publish'),
    ...     process.TransitionDefinition('review', 'reject'),
    ...     )

Each transition is constructed with an identifier for a starting
activity, and an identifier for an ending activity.

Before we can use a workflow definition, we have to register it as a
utility. This is necessary so that process instances can find their
definitions.  In addition, the utility name must match the process id:

    >>> import zope.component
    >>> zope.component.provideUtility(pd, name=pd.id)

Now, with this definition, we can execute our workflow.  We haven't
defined any work yet, but we can see the workflow execute.  We'll see
the workflow executing by registering a subscriber that logs workflow
events:

    >>> def log_workflow(event):
    ...     print event

    >>> import zope.event
    >>> zope.event.subscribers.append(log_workflow)

To use the workflow definition, we need to create an instance:

    >>> proc = pd()

Now, if we start the workflow:

    >>> proc.start()
    ProcessStarted(Process('sample'))
    Transition(None, Activity('sample.author'))
    ActivityStarted(Activity('sample.author'))
    ActivityFinished(Activity('sample.author'))
    Transition(Activity('sample.author'), Activity('sample.review'))
    ActivityStarted(Activity('sample.review'))
    ActivityFinished(Activity('sample.review'))
    Transition(Activity('sample.review'), Activity('sample.publish'))
    ActivityStarted(Activity('sample.publish'))
    ActivityFinished(Activity('sample.publish'))
    ProcessFinished(Process('sample'))

we see that we transition immediately into the author activity, then
into review and publish.  Normally, we'd need to do some work in each
activity, and transitions would continue only after work had been
done, however, in this case, we didn't define any work, so each
activity completed immediately.

Note that we didn't transition into the rejected activity.  By
default, when an activity is completed, the first transition for which
its condition evaluates to `True` is used.  By default, transitions
have boolean conditions [1]_ that evaluate to `True`, so the transition
to `publish` is used because it was defined before the transition to
`reject`.  What we want is to transition to `publish` if a reviewer
approves the content for publication, but to `reject` if the reviewer
rejects the content for publication.  We can use a condition for this:

    >>> pd = process.ProcessDefinition('sample')
    >>> zope.component.provideUtility(pd, name=pd.id)

    >>> pd.defineActivities(
    ...     author = process.ActivityDefinition(),
    ...     review = process.ActivityDefinition(),
    ...     publish = process.ActivityDefinition(),
    ...     reject = process.ActivityDefinition(),
    ...     )
    >>> pd.defineTransitions(
    ...     process.TransitionDefinition('author', 'review'),
    ...     process.TransitionDefinition(
    ...         'review', 'publish', condition=lambda data: data.publish),
    ...     process.TransitionDefinition('review', 'reject'),
    ...     )

We redefined the workflow process, specifying a condition for the
transition to `publish`.  Boolean conditions are just callable objects that
take a data object and return a boolean value.  The data object is
called "workflow-relevant data".  A process instance has a data object
containing this data.  In the example, above, the condition simply
returned the value of the `publish` attribute. How does this attribute
get set? It needs to be set by the review activity. To do that, we
need to arrange for the activity to set the data.  This brings us to
applications.

Process definitions are meant to be used with different
applications. For this reason, process definitions don't include
application logic.  What they do include is a specifications of the
applications to be invoked and the flow of work-flow-relevant data to
and from the application.  Now, we can define our applications:

    >>> pd.defineApplications(
    ...     author = process.Application(),
    ...     review = process.Application(
    ...         process.OutputParameter('publish')),
    ...     publish = process.Application(),
    ...     reject = process.Application(),
    ...     )

We used the same names for the applications that we used for our
activities. This isn't required, but is a common practice.  Note that
the `review` application includes a specification of an output
parameter.  Now that we've defined our applications, we need to modify
our activities to use them:

    >>> pd.activities['author'].addApplication('author')
    >>> pd.activities['review'].addApplication('review', ['publish'])
    >>> pd.activities['publish'].addApplication('publish')
    >>> pd.activities['reject'].addApplication('reject')

An activity can use many applications, so we call `addApplication`.
In the application definition for the 'review' application, we
provided the name of a workflow-relevent data variable corresponding
to the output parameter defined for the application.  When using an
application in an activity, a workflow-relevent data variable name
must be provided for each of the parameters in the identified
applications's signature.  When an application is used in an activity,
workflow-relevent data are passed for each of the input parameters and
are set by each of the output parameters. In this example, the output
parameter, will be used to add a `publish` attribute to the workflow
relevant data.

Participants
------------

We've declared some applications, and we've wired them up to
activities, but we still haven't specified any application code. Before
we can specify application code, we need to consider who will be
performing the application.  Workflow applications are normally
executed by people, or other external actors.  As with applications,
process definitions allow participants in the workflow to be declared
and identified with activities.  We declare participants much as we
declare applications, except without parameters:

    >>> pd.defineParticipants(
    ...     author   = process.Participant(),
    ...     reviewer = process.Participant(),
    ...     )

In this case, we happened to reuse an activity name for one, but
not both of the participants.  Having defined these participants, we
can associate them with activities:

    >>> pd.activities['author'].definePerformer('author')
    >>> pd.activities['review'].definePerformer('reviewer')

Application Integration
-----------------------

To use a process definition to control application logic, we need to
associate it with an "integration" object.

When a process needs to get a participant, it calls createParticipant
on its integration attribute, passing the process id and the
performer id. If an activity doesn't have a
performer, then the procedure above is used with an empty performer id.

Similarly, when a process needs a work item, it calls createWorkItem
on its integration attribute, passing the process id and the
application id.

Work items provide a `start` method, which is used to start the work
and pass input arguments.  It is the responsibility of the work item,
at some later time, to call the `workItemFinished` method on the
activity, to notify the activity that the work item was
completed. Output parameters are passed to the `workItemFinished`
method.

A simple way to create integration objects is with
`zope.wfmc.attributeintegration.AttributeIntegration`.

    >>> from zope.wfmc.attributeintegration import AttributeIntegration
    >>> integration = AttributeIntegration()
    >>> pd.integration = integration

We'll start by defining a simple Participant class:

    >>> import zope.interface
    >>> from zope.wfmc import interfaces

    >>> class Participant(object):
    ...     zope.component.adapts(interfaces.IActivity)
    ...     zope.interface.implements(interfaces.IParticipant)
    ...
    ...     def __init__(self, activity):
    ...         self.activity = activity

We set attributes on the integration for each participant:

    >>> integration.authorParticipant   = Participant
    >>> integration.reviewerParticipant = Participant

We also define an attribute for participants for activities that don't
have performers:

    >>> integration.Participant = Participant

Now we'll define our work-items. First we'll define some classes:

    >>> work_list = []

    >>> class ApplicationBase:
    ...     zope.component.adapts(interfaces.IParticipant)
    ...     zope.interface.implements(interfaces.IWorkItem)
    ...
    ...     def __init__(self, participant):
    ...         self.participant = participant
    ...         work_list.append(self)
    ...
    ...     def start(self):
    ...         pass
    ...
    ...     def finish(self):
    ...         self.participant.activity.workItemFinished(self)

    >>> class Review(ApplicationBase):
    ...     def finish(self, publish):
    ...         self.participant.activity.workItemFinished(self, publish)

    >>> class Publish(ApplicationBase):
    ...     def start(self):
    ...         print "Published"
    ...         self.finish()

    >>> class Reject(ApplicationBase):
    ...     def start(self):
    ...         print "Rejected"
    ...         self.finish()

and then we'll hook them up with the integration object:

    >>> integration.authorWorkItem  = ApplicationBase
    >>> integration.reviewWorkItem  = Review
    >>> integration.publishWorkItem = Publish
    >>> integration.rejectWorkItem  = Reject

Using workflow processes
------------------------

To use a process definition, instantiate it and call its start method
to start execution:

    >>> proc = pd()
    >>> proc.start()
    ... # doctest: +NORMALIZE_WHITESPACE
    ProcessStarted(Process('sample'))
    Transition(None, Activity('sample.author'))
    ActivityStarted(Activity('sample.author'))

We transition into the author activity and wait for work to get done.
To move forward, we need to get at the authoring work item, so we can
finish it.  Our work items add themselves to a work list, so we can
get the item from the list.

    >>> item = work_list.pop()

Now we can finish the work item, by calling its finish method:

    >>> item.finish()
    WorkItemFinished('author')
    ActivityFinished(Activity('sample.author'))
    Transition(Activity('sample.author'), Activity('sample.review'))
    ActivityStarted(Activity('sample.review'))

We see that we transitioned to the review activity.  Note that the
`finish` method isn't a part of the workflow APIs.  It was defined by
our sample classes. Other applications could use different mechanisms.

Now, we'll finish the review process by calling the review work item's
`finish`. We'll pass `False`, indicating that the content should not
be published:

    >>> work_list.pop().finish(False)
    WorkItemFinished('review')
    ActivityFinished(Activity('sample.review'))
    Transition(Activity('sample.review'), Activity('sample.reject'))
    ActivityStarted(Activity('sample.reject'))
    Rejected
    WorkItemFinished('reject')
    ActivityFinished(Activity('sample.reject'))
    ProcessFinished(Process('sample'))

Ordering output transitions
---------------------------

Normally, outgoing transitions are ordered in the order of transition
definition and all transitions from a given activity are used.

If transitions are defined in an inconvenient order, then the workflow
might not work as expected.  For example, let's modify the above
process by switching the order of definition of some of the
transitions.  We'll reuse our integration object from the previous
example by passing it to the definition constructor:

    >>> pd = process.ProcessDefinition('sample', integration)
    >>> zope.component.provideUtility(pd, name=pd.id)

    >>> pd.defineActivities(
    ...     author = process.ActivityDefinition(),
    ...     review = process.ActivityDefinition(),
    ...     publish = process.ActivityDefinition(),
    ...     reject = process.ActivityDefinition(),
    ...     )
    >>> pd.defineTransitions(
    ...     process.TransitionDefinition('author', 'review'),
    ...     process.TransitionDefinition('review', 'reject'),
    ...     process.TransitionDefinition(
    ...         'review', 'publish', condition=lambda data: data.publish),
    ...     )

    >>> pd.defineApplications(
    ...     author = process.Application(),
    ...     review = process.Application(
    ...         process.OutputParameter('publish')),
    ...     publish = process.Application(),
    ...     reject = process.Application(),
    ...     )

    >>> pd.activities['author'].addApplication('author')
    >>> pd.activities['review'].addApplication('review', ['publish'])
    >>> pd.activities['publish'].addApplication('publish')
    >>> pd.activities['reject'].addApplication('reject')

    >>> pd.defineParticipants(
    ...     author   = process.Participant(),
    ...     reviewer = process.Participant(),
    ...     )

    >>> pd.activities['author'].definePerformer('author')
    >>> pd.activities['review'].definePerformer('reviewer')

and run our process:

    >>> proc = pd()
    >>> proc.start()
    ... # doctest: +NORMALIZE_WHITESPACE
    ProcessStarted(Process('sample'))
    Transition(None, Activity('sample.author'))
    ActivityStarted(Activity('sample.author'))

    >>> work_list.pop().finish()
    WorkItemFinished('author')
    ActivityFinished(Activity('sample.author'))
    Transition(Activity('sample.author'), Activity('sample.review'))
    ActivityStarted(Activity('sample.review'))

This time, we'll say that we should publish:

    >>> work_list.pop().finish(True)
    WorkItemFinished('review')
    ActivityFinished(Activity('sample.review'))
    Transition(Activity('sample.review'), Activity('sample.reject'))
    ActivityStarted(Activity('sample.reject'))
    Rejected
    WorkItemFinished('reject')
    ActivityFinished(Activity('sample.reject'))
    ProcessFinished(Process('sample'))

But we went to the reject activity anyway. Why? Because transitions
are tested in order. Because the transition to the reject activity was
tested first and had no condition, we followed it without checking the
condition for the transition to the publish activity.  We can fix this
by specifying outgoing transitions on the reviewer activity directly.
To do this, we'll also need to specify ids in our transitions.  Let's
redefine the process:


    >>> pd = process.ProcessDefinition('sample', integration)
    >>> zope.component.provideUtility(pd, name=pd.id)

    >>> pd.defineActivities(
    ...     author = process.ActivityDefinition(),
    ...     review = process.ActivityDefinition(),
    ...     publish = process.ActivityDefinition(),
    ...     reject = process.ActivityDefinition(),
    ...     )
    >>> pd.defineTransitions(
    ...     process.TransitionDefinition('author', 'review'),
    ...     process.TransitionDefinition('review', 'reject', id='reject'),
    ...     process.TransitionDefinition(
    ...         'review', 'publish', id='publish',
    ...         condition=lambda data: data.publish),
    ...     )

    >>> pd.defineApplications(
    ...     author = process.Application(),
    ...     review = process.Application(
    ...         process.OutputParameter('publish')),
    ...     publish = process.Application(),
    ...     reject = process.Application(),
    ...     )

    >>> pd.activities['author'].addApplication('author')
    >>> pd.activities['review'].addApplication('review', ['publish'])
    >>> pd.activities['publish'].addApplication('publish')
    >>> pd.activities['reject'].addApplication('reject')

    >>> pd.defineParticipants(
    ...     author   = process.Participant(),
    ...     reviewer = process.Participant(),
    ...     )

    >>> pd.activities['author'].definePerformer('author')
    >>> pd.activities['review'].definePerformer('reviewer')

    >>> pd.activities['review'].addOutgoing('publish')
    >>> pd.activities['review'].addOutgoing('reject')

Now, when we run the process, we'll go to the publish activity as
expected:


    >>> proc = pd()
    >>> proc.start()
    ... # doctest: +NORMALIZE_WHITESPACE
    ProcessStarted(Process('sample'))
    Transition(None, Activity('sample.author'))
    ActivityStarted(Activity('sample.author'))

    >>> work_list.pop().finish()
    WorkItemFinished('author')
    ActivityFinished(Activity('sample.author'))
    Transition(Activity('sample.author'), Activity('sample.review'))
    ActivityStarted(Activity('sample.review'))

    >>> work_list.pop().finish(True)
    WorkItemFinished('review')
    ActivityFinished(Activity('sample.review'))
    Transition(Activity('sample.review'), Activity('sample.publish'))
    ActivityStarted(Activity('sample.publish'))
    Published
    WorkItemFinished('publish')
    ActivityFinished(Activity('sample.publish'))
    ProcessFinished(Process('sample'))


Complex Flows
-------------

Lets look at a more complex example.  In this example, we'll extend
the process to work with multiple reviewers.  We'll also make the
work-list handling a bit more sophisticated.  We'll also introduce
some new concepts:

- splits and joins

- process arguments

Consider the publication
process shown below::


  Author:      Tech          Tech          Editorial
               Reviewer 1:   Reviewer 2:   Reviewer:
  ===========  ===========   ===========   ==============
                                                           ---------
       ----------------------------------------------------| Start |
      /                                                    ---------
      |
      V
  -----------
  | Prepare |<------------------------------\
  -----------                                \
      |        ------------                   \
      |        | Tech     |--------------- \   \
      |------->| Review 1 |                 V   |
      |        ------------  ----------    -------------
       \                     | Tech   |    | Editorial |   ----------
         ------------------->| Review |--->| Review    |-->| Reject |
                             | 2      |    -------------   ----------
                             ----------      |      |
  -----------                               /        \
  | Prepare |                              /          \--------\
  | Final   |<----------------------------/                    |
  -----------                                                  |
     ^   |                                 ----------          V
     |    \------------------------------->| Review |      -----------
      \                                    | Final  |----->| Publish |
       ------------------------------------|        |      -----------
                                           ----------

Here we've arranged the process diagram into columns, with the
activities for each participant. We have four participants, the
author, two technical reviewers, and an editorial reviewer.  The
author prepares a draft.  The author sends the draft to *both*
technical reviewers for review.  When the technical reviews have
completed, the editorial review does an initial editorial
review. Based on the technical reviews, the editor may choose to:

- Reject the document

- Publish the document as is

- Request technical changes (based on the technical reviewers'
  comments), or

- Request editorial changes.

If technical changes are required, the work flows back to the
"Prepare" activity.  If editorial changes are necessary, then work
flows to the "Prepare Final" activity.  When the author has made the
editorial changes, work flows to "Review Final".  The editor may
request additional changes, in which case, work flows back to "Prepare
Final", otherwise, the work flows to "Publish".

This example illustrates different kinds of "joins" and "splits".  The
term "join" refers to the way incoming transitions to an activity are
handled. There are two kinds of joins: "and" and "xor".  With an "and"
join, the activity waits for each of the incoming transitions.  In
this example, the inputs to the "Editorial Review" activity form an
"and" join.  Editorial review waits until each of the technical
reviews are completed.  The rest of the joins in this example are
"xor" joins.  The activity starts on any transition into the activity.

The term "split" refers to way outgoing transitions from an activity
are handled.  Normally, exactly one transition out of an activity is
used. This is called an "xor" split.  With an "and" split, all
transitions with boolean conditions that evaluate to `True` are used.
In this example, the "Prepare" activity has an "and" split.  Work
flows simultaneously to the two technical review activities.  The rest
of the splits in this example are "xor" splits.

Lets create our new workflow process. We'll reuse our existing
integration object:

    >>> Publication = process.ProcessDefinition('Publication')
    >>> Publication.integration = integration
    >>> zope.component.provideUtility(Publication, name=Publication.id)

    >>> Publication.defineActivities(
    ...     start   = process.ActivityDefinition("Start"),
    ...     prepare = process.ActivityDefinition("Prepare"),
    ...     tech1   = process.ActivityDefinition("Technical Review 1"),
    ...     tech2   = process.ActivityDefinition("Technical Review 2"),
    ...     review  = process.ActivityDefinition("Editorial Review"),
    ...     final   = process.ActivityDefinition("Final Preparation"),
    ...     rfinal  = process.ActivityDefinition("Review Final"),
    ...     publish = process.ActivityDefinition("Publish"),
    ...     reject  = process.ActivityDefinition("Reject"),
    ...     )

Here, we've passed strings to the activity definitions providing
names. Names must be either unicode or ASCII strings.

We define our transitions:

    >>> Publication.defineTransitions(
    ...     process.TransitionDefinition('start', 'prepare'),
    ...     process.TransitionDefinition('prepare', 'tech1'),
    ...     process.TransitionDefinition('prepare', 'tech2'),
    ...     process.TransitionDefinition('tech1', 'review'),
    ...     process.TransitionDefinition('tech2', 'review'),
    ...
    ...     process.TransitionDefinition(
    ...         'review', 'reject',
    ...         condition=lambda data: not data.publish
    ...         ),
    ...     process.TransitionDefinition(
    ...         'review', 'prepare',
    ...         condition=lambda data: data.tech_changes
    ...         ),
    ...     process.TransitionDefinition(
    ...         'review', 'final',
    ...         condition=lambda data: data.ed_changes
    ...         ),
    ...     process.TransitionDefinition('review', 'publish'),
    ...
    ...     process.TransitionDefinition('final', 'rfinal'),
    ...     process.TransitionDefinition(
    ...         'rfinal', 'final',
    ...         condition=lambda data: data.ed_changes
    ...         ),
    ...     process.TransitionDefinition('rfinal', 'publish'),
    ...     )

We specify our "and" split and join:

    >>> Publication.activities['prepare'].andSplit(True)
    >>> Publication.activities['review'].andJoin(True)

We define our participants and applications:

    >>> Publication.defineParticipants(
    ...     author   = process.Participant("Author"),
    ...     tech1    = process.Participant("Technical Reviewer 1"),
    ...     tech2    = process.Participant("Technical Reviewer 2"),
    ...     reviewer = process.Participant("Editorial Reviewer"),
    ...     )

    >>> Publication.defineApplications(
    ...     prepare = process.Application(),
    ...     tech_review = process.Application(
    ...         process.OutputParameter('publish'),
    ...         process.OutputParameter('tech_changes'),
    ...         ),
    ...     ed_review = process.Application(
    ...         process.InputParameter('publish1'),
    ...         process.InputParameter('tech_changes1'),
    ...         process.InputParameter('publish2'),
    ...         process.InputParameter('tech_changes2'),
    ...         process.OutputParameter('publish'),
    ...         process.OutputParameter('tech_changes'),
    ...         process.OutputParameter('ed_changes'),
    ...         ),
    ...     publish = process.Application(),
    ...     reject = process.Application(),
    ...     final = process.Application(),
    ...     rfinal = process.Application(
    ...         process.OutputParameter('ed_changes'),
    ...         ),
    ...     )

    >>> Publication.activities['prepare'].definePerformer('author')
    >>> Publication.activities['prepare'].addApplication('prepare')

    >>> Publication.activities['tech1'].definePerformer('tech1')
    >>> Publication.activities['tech1'].addApplication(
    ...     'tech_review', ['publish1', 'tech_changes1'])

    >>> Publication.activities['tech2'].definePerformer('tech2')
    >>> Publication.activities['tech2'].addApplication(
    ...     'tech_review', ['publish2', 'tech_changes2'])

    >>> Publication.activities['review'].definePerformer('reviewer')
    >>> Publication.activities['review'].addApplication(
    ...     'ed_review',
    ...     ['publish1', 'tech_changes1', 'publish2', 'tech_changes2',
    ...      'publish', 'tech_changes', 'ed_changes'],
    ...     )

    >>> Publication.activities['final'].definePerformer('author')
    >>> Publication.activities['final'].addApplication('final')

    >>> Publication.activities['rfinal'].definePerformer('reviewer')
    >>> Publication.activities['rfinal'].addApplication(
    ...     'rfinal', ['ed_changes'],
    ...     )

    >>> Publication.activities['publish'].addApplication('publish')
    >>> Publication.activities['reject'].addApplication('reject')

We want to be able to specify an author when we start the process.
We'd also like to be told the final disposition of the process.  To
accomplish this, we'll define parameters for our process:

    >>> Publication.defineParameters(
    ...     process.InputParameter('author'),
    ...     process.OutputParameter('publish'),
    ...     )

Now that we've defined the process, we need to provide participant and
application components.  Let's start with our participants.  Rather
than sharing a single work list, we'll give each user their own
work list.  We'll also create preexisting participants and return
them. Finally, we'll create multiple authors and use the selected one:


    >>> class User:
    ...     def __init__(self):
    ...         self.work_list = []

    >>> authors = {'bob': User(), 'ted': User(), 'sally': User()}

    >>> reviewer = User()
    >>> tech1 = User()
    >>> tech2 = User()

    >>> class Author(Participant):
    ...     def __init__(self, activity):
    ...         Participant.__init__(self, activity)
    ...         author_name = activity.process.workflowRelevantData.author
    ...         self.user = authors[author_name]

In this example, we need to define a separate attribute for each participant:

    >>> integration.authorParticipant = Author

When the process is created, the author name will be passed in and
assigned to the workflow-relevant data.  Our author class uses this
information to select the named user.

    >>> class Reviewer(Participant):
    ...     user = reviewer
    >>> integration.reviewerParticipant = Reviewer

    >>> class Tech1(Participant):
    ...     user = tech1
    >>> integration.tech1Participant = Tech1

    >>> class Tech2(Participant):
    ...     user = tech2
    >>> integration.tech2Participant = Tech2

We'll use our orginal participation class for activities without
performers:

    >>> integration.Participant = Participant

Now we'll create our applications. Let's start with our author:

    >>> class ApplicationBase(object):
    ...     zope.component.adapts(interfaces.IParticipant)
    ...     zope.interface.implements(interfaces.IWorkItem)
    ...
    ...     def __init__(self, participant):
    ...         self.participant = participant
    ...         self.activity = participant.activity
    ...         participant.user.work_list.append(self)
    ...
    ...     def start(self):
    ...         pass
    ...
    ...     def finish(self):
    ...         self.participant.activity.workItemFinished(self)

    >>> class Prepare(ApplicationBase):
    ...
    ...     def summary(self):
    ...         process = self.activity.process
    ...         doc = getattr(process.applicationRelevantData, 'doc', '')
    ...         if doc:
    ...             print 'Previous draft:'
    ...             print doc
    ...             print 'Changed we need to make:'
    ...             for change in process.workflowRelevantData.tech_changes:
    ...                 print change
    ...         else:
    ...             print 'Please write the initial draft'
    ...
    ...     def finish(self, doc):
    ...         self.activity.process.applicationRelevantData.doc = doc
    ...         super(Prepare, self).finish()

    >>> integration.prepareWorkItem = Prepare

Since we used the prepare application for revisions as well as initial
preparation, we provide a summary method to show us what we have to do.

Here we get the document created by the author passed in as an
argument to the finish method.  In a more realistic implementation,
the author task would create the document at the start of the task and
provide a user interface for the user to edit it.  We store the
document as application-relevant data, since we'll want reviewers to
be able to access it, but we don't need it directly for workflow
control.

    >>> class TechReview(ApplicationBase):
    ...
    ...     def getDoc(self):
    ...         return self.activity.process.applicationRelevantData.doc
    ...
    ...     def finish(self, decision, changes):
    ...         self.activity.workItemFinished(self, decision, changes)

    >>> integration.tech_reviewWorkItem = TechReview

Here, we provided a method to access the original document.

    >>> class Review(TechReview):
    ...
    ...     def start(self, publish1, changes1, publish2, changes2):
    ...         if not (publish1 and publish2):
    ...             # Reject if either tech reviewer rejects
    ...             self.activity.workItemFinished(
    ...                 self, False, changes1 + changes2, ())
    ...
    ...         if changes1 or changes2:
    ...             # we won't do anything if there are tech changes
    ...             self.activity.workItemFinished(
    ...                 self, True, changes1 + changes2, ())
    ...
    ...     def finish(self, ed_changes):
    ...         self.activity.workItemFinished(self, True, (), ed_changes)

    >>> integration.ed_reviewWorkItem = Review

In this implementation, we decided to reject outright if either
technical editor recommended rejection and to send work back to
preparation if there are any technical changes. We also subclassed
`TechEdit` to get the `getDoc` method.

We'll reuse the `publish` and `reject` application from the previous
example.

    >>> class Final(ApplicationBase):
    ...
    ...     def summary(self):
    ...         process = self.activity.process
    ...         doc = getattr(process.applicationRelevantData, 'doc', '')
    ...         print 'Previous draft:'
    ...         print self.activity.process.applicationRelevantData.doc
    ...         print 'Changed we need to make:'
    ...         for change in process.workflowRelevantData.ed_changes:
    ...            print change
    ...
    ...     def finish(self, doc):
    ...         self.activity.process.applicationRelevantData.doc = doc
    ...         super(Final, self).finish()

    >>> integration.finalWorkItem = Final

In our this application, we simply update the document to reflect
changes.

    >>> class ReviewFinal(TechReview):
    ...
    ...     def finish(self, ed_changes):
    ...         self.activity.workItemFinished(self, ed_changes)

    >>> integration.rfinalWorkItem = ReviewFinal

Our process now returns data.  When we create a process, we need to
supply an object that it can call back to:

    >>> class PublicationContext:
    ...     zope.interface.implements(interfaces.IProcessContext)
    ...
    ...     def processFinished(self, process, decision):
    ...         self.decision = decision

Now, let's try out our process:

    >>> context = PublicationContext()
    >>> proc = Publication(context)
    >>> proc.start('bob')
    ProcessStarted(Process('Publication'))
    Transition(None, Activity('Publication.start'))
    ActivityStarted(Activity('Publication.start'))
    ActivityFinished(Activity('Publication.start'))
    Transition(Activity('Publication.start'), Activity('Publication.prepare'))
    ActivityStarted(Activity('Publication.prepare'))

We should have added an item to bob's work list. Let's get it and
finish it, submitting a document:

    >>> item = authors['bob'].work_list.pop()
    >>> item.finish("I give my pledge, as an American\n"
    ...             "to save, and faithfully to defend from waste\n"
    ...             "the natural resources of my Country.")
    WorkItemFinished('prepare')
    ActivityFinished(Activity('Publication.prepare'))
    Transition(Activity('Publication.prepare'), Activity('Publication.tech1'))
    ActivityStarted(Activity('Publication.tech1'))
    Transition(Activity('Publication.prepare'), Activity('Publication.tech2'))
    ActivityStarted(Activity('Publication.tech2'))

Notice that we transitioned to *two* activities, `tech1` and
`tech2`.  This is because the prepare activity has an "and" split.
Now we'll do a tech review.  Let's see what tech1 has:

    >>> item = tech1.work_list.pop()
    >>> print item.getDoc()
    I give my pledge, as an American
    to save, and faithfully to defend from waste
    the natural resources of my Country.

Let's tell the author to change "American" to "Earthling":

    >>> item.finish(True, ['Change "American" to "Earthling"'])
    WorkItemFinished('tech_review')
    ActivityFinished(Activity('Publication.tech1'))
    Transition(Activity('Publication.tech1'), Activity('Publication.review'))

Here we transitioned to the editorial review activity, but we didn't
start it. This is because the editorial review activity has an "and"
join, meaning that it won't start until both transitions have
occurred.

Now we'll do the other technical review:

    >>> item = tech2.work_list.pop()
    >>> item.finish(True, ['Change "Country" to "planet"'])
    WorkItemFinished('tech_review')
    ActivityFinished(Activity('Publication.tech2'))
    Transition(Activity('Publication.tech2'), Activity('Publication.review'))
    ActivityStarted(Activity('Publication.review'))
    WorkItemFinished('ed_review')
    ActivityFinished(Activity('Publication.review'))
    Transition(Activity('Publication.review'), Activity('Publication.prepare'))
    ActivityStarted(Activity('Publication.prepare'))

Now when we transitioned to the editorial review activity, we started
it, because each of the input transitions had happened.  Our editorial
review application automatically sent the work back to preparation,
because there were technical comments.  Let's address the comments:

    >>> item = authors['bob'].work_list.pop()
    >>> item.summary()
    Previous draft:
    I give my pledge, as an American
    to save, and faithfully to defend from waste
    the natural resources of my Country.
    Changed we need to make:
    Change "American" to "Earthling"
    Change "Country" to "planet"

    >>> item.finish("I give my pledge, as an Earthling\n"
    ...             "to save, and faithfully to defend from waste\n"
    ...             "the natural resources of my planet.")
    WorkItemFinished('prepare')
    ActivityFinished(Activity('Publication.prepare'))
    Transition(Activity('Publication.prepare'), Activity('Publication.tech1'))
    ActivityStarted(Activity('Publication.tech1'))
    Transition(Activity('Publication.prepare'), Activity('Publication.tech2'))
    ActivityStarted(Activity('Publication.tech2'))

As before, after completing the initial edits, we start the technical
review activities again.  We'll review it again. This time, we have no
comments, because the author applied our requested changes:

    >>> item = tech1.work_list.pop()
    >>> item.finish(True, [])
    WorkItemFinished('tech_review')
    ActivityFinished(Activity('Publication.tech1'))
    Transition(Activity('Publication.tech1'), Activity('Publication.review'))

    >>> item = tech2.work_list.pop()
    >>> item.finish(True, [])
    WorkItemFinished('tech_review')
    ActivityFinished(Activity('Publication.tech2'))
    Transition(Activity('Publication.tech2'), Activity('Publication.review'))
    ActivityStarted(Activity('Publication.review'))

This time, we are left in the technical review activity because there
weren't any technical changes. We're ready to do our editorial review.
We'll request an editorial change:

    >>> item = reviewer.work_list.pop()
    >>> print item.getDoc()
    I give my pledge, as an Earthling
    to save, and faithfully to defend from waste
    the natural resources of my planet.

    >>> item.finish(['change "an" to "a"'])
    WorkItemFinished('ed_review')
    ActivityFinished(Activity('Publication.review'))
    Transition(Activity('Publication.review'), Activity('Publication.final'))
    ActivityStarted(Activity('Publication.final'))

Because we requested editorial changes, we transitioned to the final
editing activity, so that the author can make the changes:

    >>> item = authors['bob'].work_list.pop()
    >>> item.summary()
    Previous draft:
    I give my pledge, as an Earthling
    to save, and faithfully to defend from waste
    the natural resources of my planet.
    Changed we need to make:
    change "an" to "a"

    >>> item.finish("I give my pledge, as a Earthling\n"
    ...             "to save, and faithfully to defend from waste\n"
    ...             "the natural resources of my planet.")
    WorkItemFinished('final')
    ActivityFinished(Activity('Publication.final'))
    Transition(Activity('Publication.final'), Activity('Publication.rfinal'))
    ActivityStarted(Activity('Publication.rfinal'))

We transition to the activity for reviewing the final edits.  We
review the document and approve it for publication:

    >>> item = reviewer.work_list.pop()
    >>> print item.getDoc()
    I give my pledge, as a Earthling
    to save, and faithfully to defend from waste
    the natural resources of my planet.

    >>> item.finish([])
    WorkItemFinished('rfinal')
    ActivityFinished(Activity('Publication.rfinal'))
    Transition(Activity('Publication.rfinal'), Activity('Publication.publish'))
    ActivityStarted(Activity('Publication.publish'))
    Published
    WorkItemFinished('publish')
    ActivityFinished(Activity('Publication.publish'))
    ProcessFinished(Process('Publication'))

At this point, the rest of the process finished automatically.  In
addition, the decision was recorded in the process context object:

    >>> context.decision
    True

Coming Soon
------------

- XPDL support

- Timeouts/exceptions

- "otherwise" conditions


.. [1] There are other kinds of conditions, namely "otherwise" and
       "exception" conditions.
