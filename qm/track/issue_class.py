########################################################################
#
# File:   issue_class.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   Generic implementation of an issue class.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

########################################################################
# imports
########################################################################

import issue
import qm
import qm.fields
import qm.label
import string
import types

########################################################################
# constants
########################################################################

# The default categories enumeration to use for a new issue class, if
# one is not provided.

# FIXME: These are bogus test values.  Put something better here.

default_categories = {
    "crash" : 0,
    "documentation" : 1,
    "improvement": 2,
}


# The default set of states to use for a new issue class, if one is
# not provided.  This variable is initialzed in '_initialze_module',
# below. 

default_state_model = None


########################################################################
# exceptions
########################################################################

class UnreachableStateError(ValueError):
    """Exception indicating an unreachable state in a state model.

    This exception is raised when a state is detected in a state model
    that is not reachable via a sequence of transitions from the state
    model's initial state."""

    pass



class NoSuchTransitionError(RuntimeError):
    """Exception indicating a transition is absent.

    This exception is raised when an attempt is made to retrieve a
    transition from one state to another when no such transition is
    present in the state model."""

    pass



########################################################################
# classes
########################################################################

class IidField(qm.fields.TextField):
    """A field containing the ID of an issue."""

    def __init__(self, name, **attributes):
        """Create an IID field.

        The field has no default value."""
        
        # Do base-class initialization, with different defaults.
        attributes = attributes.copy()
        attributes["default_value"] = None
        apply(qm.fields.TextField.__init__, (self, name), attributes)


    def GetTypeDescription(self):
        return "an issue ID"


    def Validate(self, value):
        value = str(value)
        if not qm.label.is_valid(value):
            raise ValueError, \
                  qm.track.error("invalid iid", iid=value) 
        return value


    def SetDefaultValue(self, value):
        # An issue ID field never has a default value.
        pass



########################################################################

class TriggerResult:
    """The result of invoking a trigger.

    A trigger result is composed of

      * A reference to the 'Trigger' object which generated this result.

      * An outcome, either 'ACCEPT' or 'REJECT'.

      * If the outcome is 'REJECT', an explanatory message.
    """

    ACCEPT = "ACCEPT"
    REJECT = "REJECT"

    def __init__(self, trigger, outcome, message=None):
        """Create a new outcome instance.

        'trigger' -- The 'Trigger' subclass instance of the trigger that
        created this outcome.

        'outcome' -- A value indicating the outcome of the trigger,
        either 'ACCEPT' or 'REJECT'.

        'message' -- A string describing the trigger's action or
        decision in structured text.  The message is used only if
        'outcome' is 'REJECT'."""
        
        assert outcome is TriggerResult.ACCEPT \
               or outcome is TriggerResult.REJECT

        self.__trigger_name = trigger.GetName()
        self.__outcome = outcome
        self.__message = message


    def GetOutcome(self):
        """Return the outcome of this trigger action.

        A false value indicates the operation was vetoed by the
        trigger.""" 

        return self.__outcome


    def GetMessage(self):
        """Return a message describing the outcome.

        returns -- A string containing structured text, or 'None'."""

        return self.__message


    def GetTriggerName(self):
        """Return the name of the trigger that created this outcome."""
        
        return self.__trigger_name



class Trigger:
    """Base class for triggers.

    Triggers are represented by instances of subclasses of this class.
    A trigger subclass may override any or all three of the 'Preupdate',
    'Postupdate', or 'Get' methods.  These methods are called at the
    appropriate times to invoke the trigger.

    The default implementations of these methods are no-ops; the 'Get'
    and 'Preupdate' implementations return an 'ACCEPT' outcome."""

    def __init__(self, name):
        """Create a new trigger instance."""

        self.__name = name


    def GetName(self):
        """Return the name of this trigger instance."""

        return self.__name


    def Preupdate(self, issue, previous_issue):
        """Invoke the trigger before an issue is changed.

        'issue' -- An 'Issue' instance.  The state of the issue as it
        will be after the update.

        'previous_issue' -- An 'Issue' instance.  The state of the issue
        before the update.

        returns -- A 'TriggerResult' object."""

        return TriggerResult(self, TriggerResult.ACCEPT)


    def Postupdate(self, issue, previous_issue):
        """Invoke the trigger after an issue is changed

        'issue' -- An 'Issue' instance.  The state of the issue after
        the update.

        'previous_issue' -- An 'Issue' instance.  The state of the issue
        before the update."""

        pass


    def Get(self, issue):
        """Invoke the trigger.

        'issue' -- An 'Issue' instance representing issue being
        retrieved.

        returns -- A 'TriggerResult' object."""

        return TriggerResult(self, TriggerResult.ACCEPT)



########################################################################

class State:
    """A state in a state model.

    See 'StateModel' for more information."""

    def __init__(self, name, description):
        """Create a new state.

        'name' -- The name of this state.

        'description' -- A description of the significance of this
        state."""
        
        self.__name = name
        self.__description = description


    def GetName(self):
        """Return the name of this state."""

        return self.__name


    def GetDescription(self):
        """Return a description of this state."""

        return self.__description


class TransitionCondition:
    """A condition attached to a transition in a state model.

    A condition represents a restriction under the circumstances in
    which a particular transition can be taken.  See 'Transition'.

    The condition is represented by a Python expression, which must
    evaluate to true (in the appropriate naming context) for the
    transition to be taken.  The condition also includes a descriptie
    name, which is used to make the meaning of the transition easier to
    identify to users."""

    def __init__(self, name, expression):
        """Create a new transition condition.

        'name' -- A descriptive name for this condition.

        'expression' -- The text of the Python expression of this
        condition."""
        
        self.__name = name
        self.__expression = expression


    def GetName(self):
        """Return a descriptive name for this condition."""

        return self.__name


    def GetExpression(self):
        """Return the text of the Python expression of this condition."""

        return self.__expression
    


class Transition:
    """A transition in a state model.

    A transition indicates that the state to advance directly from a
    specific starting state to a specific ending state in the state
    model.  Zero or more conditions may be specified for the transition;
    all such conditions must evaluate to true for the transition to be
    permitted.

    See 'StateModel'."""

    def __init__(self,
                 starting_state_name,
                 ending_state_name,
                 conditions=[]):
        """Create a new transition.

        'starting_state_name' -- The name of the state from which this
        transition leads.

        'ending_state_name' -- The name of the state to which this
        transition leads.

        'conditions' -- A sequence of 'TransitionCondition' objects.
        All must evaluate to true for the transition to be permitted."""
        
        self.__starting_state_name = starting_state_name
        self.__ending_state_name = ending_state_name
        self.__conditions = conditions


    def GetStartingStateName(self):
        """Return the name of the transition's starting state."""
        
        return self.__starting_state_name


    def GetEndingStateName(self):
        """Return the name of the transition's ending state."""

        return self.__ending_state_name


    def GetConditions(self):
        """Return conditions on this transition.

        returns -- A (possibly empty) sequence of
        'TransitionCondition' objects."""

        return self.__conditions



class StateModel:
    """A model representing the configuration of a finite state machine.

    The state model is composed of a set of states, and a set of
    transitions connecting them.  Each state is identified by a unique
    name.  Each transition is identified by the names of the two states
    it connects; transitions are directed."""

    # The '__states' attribute is a map from state names to 'State'
    # objects.

    # The '__transitions' attribute is a map of maps.  A key in the
    # outer map specifies the starting state of the transition.  The
    # corresponding value is a map from the ending state of the
    # transition to the corresponding 'Transition' object.


    def __init__(self, states, initial_state_name, transitions=[]):
        """Create a new state model.

        'states' -- A sequence of 'State' objects.  Must contain at
        least one item.

        'initial_state_name' -- The name of the state model's initial
        state.  There must be a state by this name in 'states'.

        'transitions' -- A sequence of 'Transition' objects."""
        
        # Construct the states map.
        self.__states = {}
        for state in states:
            self.AddState(state)
        # Set the initial state.
        self.SetInitialStateName(initial_state_name)
        # Construct the transitions maps.
        self.__transitions = {}
        for transition in transitions:
            self.AddTransition(transition)


    def SetInitialStateName(self, initial_state_name):
        """Set the initial state.

        'initial_state_name' -- The name of the new initial state.

        raises -- 'ValueError' if 'initial_state_name' is not the name
        of a state in this state model."""

        # Make sure there is a state by this name.
        try:
            self.GetState(initial_state_name)
        except KeyError:
            # The specified initial state isn't in this model.
            raise ValueError, \
                  "unknown initial state %s" % initial_state_name
        # Store it.
        self.__initial_state_name = initial_state_name


    def GetInitialStateName(self):
        """Return the name of the initial state."""

        return self.__initial_state_name
    

    def GetState(self, state_name):
        """Return the 'State' object for the state named 'state_name'.

        raises -- 'KeyError' if there is no state named 'state_name' in
        the state model."""

        try:
            return self.__states[state_name]
        except KeyError:
            raise KeyError, "unknown state %s" % state_name


    def GetStateNames(self):
        """Return a sequence of names of the states in the state model."""

        return self.__states.keys()


    def AddState(self, state):
        """Add a state to the state model.

        'state' -- A 'State' object.

        raises -- 'ValueError' if there is already a state by the same
        name."""

        # Make sure there isn't already a state with that name.
        state_name = state.GetName()
        if self.__states.has_key(state_name):
            raise ValueError, \
                  "there is already a state named %s" % state_name
        # Add it.
        self.__states[state_name] = state


    def GetTransition(self, starting_state_name, ending_state_name):
        """Find a 'Transition' object.

        'starting_state_name' -- The name of the starting state for the
        requested transition.

        'ending_state_name' -- The name of the ending state for the
        requested transition.

        returns -- The corresponding 'Transition' object.

        raises -- 'NoSuchTransitionError' if there is no transition in
        the state model from 'starting_state_name' to
        'ending_state_name'."""

        try:
            ending_state_map = self.__transitions[starting_state_name]
            return ending_state_map[ending_state_name]
        except KeyError:
            raise NoSuchTransitionError, \
                  "from %s to %s" % (starting_state_name, ending_state_name)


    def GetAvailableEndingStateNames(self, starting_state_name):
        """Return the names of reachable states.

        returns -- A sequence of names of states reachable by a single
        transition from the state named 'starting_state_name'."""

        try:
            ending_state_map = self.__transitions[starting_state_name]
        except KeyError:
            # No transitions from this state.
            return []
        else:
            return ending_state_map.keys()


    def AddTransition(self, transition):
        """Add a transition to the state model.

        'transition' -- A 'Transition' object.

        raises -- 'ValueError' if the starting or ending state of the
        transition is not a state in the state model."""

        starting_state_name = transition.GetStartingStateName()
        # Make sure the starting state is a state in the state model.
        try:
            self.GetState(starting_state_name)
        except KeyError:
            raise ValueError, \
                  "starting state %s is not in model" % starting_state_name
        ending_state_name = transition.GetEndingStateName()
        # Make sure the ending state is a state in the state model.
        try:
            self.GetState(ending_state_name)
        except KeyError:
            raise ValueError, \
                  "ending state %s is not in model" % ending_state_name

        # Add it.
        try:
            ending_state_map = self.__transitions[starting_state_name]
        except KeyError:
            ending_state_map = {}
            self.__transitions[starting_state_name] = ending_state_map
        ending_state_map[ending_state_name] = transition


    def Validate(self):
        """Check the validity of the state model.

        raises -- 'UnreachableStateError' if a state cannot be reached
        from the intial state via a sequence of transitions."""

        states = self.__states.values()

        # Make sure all states are reachable from the initial state by
        # walking all transitions, starting from the initial state.

        # Mark all states as unvisited.
        for state in states:
            state.__reachable = 0
        # Walk transitions and mark states recursively, starting with
        # the initial state.
        self.__MarkStateReachable(self.GetInitialStateName())
        try:
            # Look for states that have not been marked.
            for state in states:
                if not state.__reachable:
                    raise UnreachableStateError, \
                          "state %s is not reachable from the initial state" \
                          % state.GetName()
        finally:
            # In any case, clean up our mark attribute.
            for state in states:
                del state.__reachable


    def __MarkStateReachable(self, state_name):
        """Mark the state named 'state_name' as reachable, and walk."""

        state = self.GetState(state_name)
        if not state.__reachable:
            # Mark it.
            state.__reachable = 1
            # Mark states reachable via a transition.
            map(self.__MarkStateReachable,
                self.GetAvailableEndingStateNames(state_name))
        else:
            # Stop right her if we've already marked this state.
            pass
        


class StateField(qm.fields.EnumerationField):
    """A field representing a state in a state model.

    The value of this field is the name of a state in the state model.
    The default value of this field is the name of the state model's
    initial state.

    The integrity of the state model is not enforced in this class.  See
    'triggers.state.Trigger'."""

    def __init__(self, name, state_model, **attributes):
        """Construct a new field.

        'name' -- The name of this field.

        'state_model' -- A 'StateModel' instance describing the
        available states and transitions of this field.

        postconditions -- The default value of this field is set to the
        state model's initial state."""

        self.__state_model = state_model
        # Construct a starting enumeration consisting of the initial
        # state only.  We need the enumeration to be non-empty, and for
        # the default value (which is the initial state) to be a member
        # of it.
        initial_state_name = state_model.GetInitialStateName()
        enumeration = { initial_state_name: 0 }
        # Initialize the base class.
        apply(qm.fields.EnumerationField.__init__,
              (self, name, enumeration, initial_state_name),
              attributes)
        # Keep a counter with which to assign enumeral values to
        # states. 
        self.__next_enum_value = 1
        # Construct the rest of the enumeration for the other states.
        self.UpdateEnumeration()

        
    def GetStateModel(self):
        """Return the state model for this field."""
        
        return self.__state_model


    def UpdateEnumeration(self):
        """Update the enumeration to reflect the state model.

        This method must be called if states are added to the state
        model, to update the corresponding enumeration of states.

        preconditions -- There are no enumeral names in this field's
        enumeration that are not the names of states in the state
        model.  That is, no states have been removed from the state
        model (though states may have been added)."""
        
        # Make sure the state model looks OK.
        self.__state_model.Validate()
        # Extract the names of states in the state model.
        states_in_model = self.__state_model.GetStateNames()
        # Extract the names of states from the enumeration.
        enumeration = self.GetEnumeration()
        states_in_enum = enumeration.keys()

        # Make sure the states in the enumeration are a subset of the
        # states in the state model, i.e. that no states were removed
        # from the state model.
        for state in states_in_enum:
            assert state in states_in_model
        # Add any state to the enum that isn't there yet.
        for state in states_in_model:
            if state not in states_in_enum:
                value = self.__next_enum_value
                enumeration[state] = value
                self.__next_enum_value = value + 1
        # Replace the old enumeration with the new.
        self._EnumerationField__enumeration = enumeration


    def GetHelp(self):
        state_model = self.GetStateModel()
        # First some boilerplate.
        help = """
        You may change the value of this field only in accordance to
        state model.  The states in the state model, and the allowed
        transitions from each state, are listed below.\n\n"""
        # Construct a list of states in the state model.
        for state_name in state_model.GetStateNames():
            # For each state, print its name, description, and available
            # ending states from transitions.
            state = state_model.GetState(state_name)
            description = string.strip(state.GetDescription())
            transitions_to = state_model.GetAvailableEndingStateNames(
                state_name)
            if len(transitions_to) > 0:
                transitions_to = map(lambda t: '"%s"' % t, transitions_to)
                transitions_to = string.join(transitions_to, " , ")
            else:
                transitions_to = "None"
            help = help + \
                   '            * "%s": %s  Transitions to: %s.\n\n' \
                   % (state_name, description, transitions_to)
        # Also mention the state model's initial state.
        help = help + '''
        The initial state is "%s".
            ''' % state_model.GetInitialStateName()
        return help


    def _EnumerationField__GetAvailableEnumerals(self, value):
        # We override this method to show users only those states that
        # are accessible from the current one (plus, of course, the
        # current state itself).

        # Start with all enumerals, i.e. all the states in the state
        # model. 
        enumerals = self.GetEnumerals()
        # Get the names of states accessible via a transition from the
        # current state.
        available = \
            self.GetStateModel().GetAvailableEndingStateNames(str(value))
        # A filter function which returns true if its argument is the
        # name of the current state or the name of a state accessible
        # via a transition from the current state.
        def filter_function(en, value=value, av=available):
            return en == value or str(en) in av
        # Return only matching enumerals.
        return filter(filter_function, enumerals)



########################################################################

class DiscussionField(qm.fields.SetField):
    """A field for incremental text discussion of an issue.

    This field is a set of text fields.  The normal controls for
    manipulating a set are not shown, though.  Instead, the controls for
    a text field are shown, and any text entered is added as a new item
    in the discussion.

    A 'qm.track.triggers.discussion.DiscussionTrigger' must be used with
    this field.  This trigger, among other things, prepends a line to
    each discussion element listing the user name and timestamp for the
    element."""

    def __init__(self, name, **attributes):
        # Create the contained field, which is a text field.  Pass
        # extra attributes to it.
        contained_field = apply(qm.fields.TextField, (name, ), attributes)
        # Now construct our base class, the set field.
        apply(qm.fields.SetField.__init__, (self, contained_field))


    def Validate(self, value):
        # Normally, the value of a set field is a list, but we allow
        # strings here too.  'DiscussionTrigger' will take the string
        # and append it to the previous value of the field.
        if type(value) is types.StringType:
            return value
        else:
            return qm.fields.SetField.Validate(self, value)


    def FormatValueAsHtml(self, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = []
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        contained = self.GetContainedField()

        # For read-only display styles, show a history of the
        # conversation.  
        if style in ["full", "brief"]:
            # Use a table to achieve the indentation we want.
            result = '''
            <table border="0" cellpadding="4" cellspacing="4" columns="2">
             <tbody>
            '''
            # Display the discussion elements in reverse order, with the
            # most recent one first.
            value = value[:]
            value.reverse()
            # Show each element.
            for message in value:
                # The first line shows the user and timestamp; format it
                # specially. 
                head, body = string.split(message, "\n", 1)
                result = result + '''
                <tr>
                 <td colspan="2"><i>%s</i></td>
                </tr>
                <tr>
                 <td>&nbsp;</td>
                 <td>%s</td>
                </tr>
                ''' % (qm.web.escape(head),
                       contained.FormatValueAsHtml(body, style))
            result = result + '''
             </tbody>
            </table>
            '''
            return result
            
        # For editing styles, show the controls for the contained text
        # field, not for the set.
        elif style in ["new", "edit"]:
            return contained.FormatValueAsHtml("", style, name)

        # Everything else as a set.
        else:
            return qm.fields.SetField.FormatValueAsHtml(self, value,
                                                        style, name)


    def ParseFormValue(self, value):
        # Since we show editing controls for the contained field, we
        # need to parse the submitted value accordingly.
        contained = self.GetContainedField()
        return contained.ParseFormValue(value)


    def GetHelp(self):
        return """
        A discussion field.  This field contains an ongoing discussion
        of the issue.  You may add additional comments to the field, and
        view the record of previous comments.
        """



########################################################################

class IssueClass:
    """Generic in-memory implementation of an issue class."""

    def __init__(self,
                 name,
                 title=None,
                 description="",
                 categories=default_categories,
                 state_model=None):
        """Create a new issue class.

        'name' -- The name of this issue class.

        'title' -- A user-friendly name.  If 'None', the value of 'name'
        is used.

        'description' -- A description of the issue class.

        'categories' -- The enumeral to use for the "categories" field.

        'state_model' -- A 'StateModel' instance to use for the "states"
        field.

        The issue class initially includes mandatory fields.  The iid
        and revision fields, in that order, are gauranteed to be the
        first two fields added, and as returned by 'GetFields()'."""

        self.__name = name
        if title is None:
            self.__title = name
        else:
            self.__title = title
        self.__description = description
        self.__triggers = []
        if state_model is None:
            state_model = default_state_model
        # Maintain both a list of fields and a mapping from field
        # names to fields.  The list is to preserve the order of the
        # fields; the mapping is for fast lookups by field name.
        self.__fields = []
        self.__fields_by_name = {}

        # Create mandatory fields.
        
        # The issue id field.
        field = IidField(
            name="iid",
            title="Issue ID",
            description="A label that uniquely identifies the issue.",
            initialize_only="true")
        # We do not want the iid to have a default value. It
        # always must be specified.
        field.UnsetDefaultValue()
        self.AddField(field)

        # The revision number field.
        field = qm.fields.IntegerField(
            name="revision",
            title="Revision Number",
            description="The cardinality of this revision of the issue.",
            hidden="true")
        self.AddField(field)

        # The revision timestamp field.
        field = qm.fields.TimeField(
            name="timestamp",
            title="Modification Time",
            description="The time when this revision was created.",
            read_only="true")
        self.AddField(field)

        # The user id field.
        field = qm.fields.UidField(
            name="user",
            title="Modifying User",
            description="The ID of the user who created this revision.",
            read_only="true")
        self.AddField(field)

        # The state field.
        field = StateField(
            name="state",
            title="State",
            state_model=state_model,
            description="""
            The state of this issue in the issue class's state model.
            The state reflects the status of this issue within the set of
            procedures by which an issue is normally resolved.
            """,
            initialize_to_default="true")
        self.AddField(field)

        import triggers.state
        trigger = triggers.state.Trigger("state")
        self.RegisterTrigger(trigger)

        # The summary field.
        field = qm.fields.TextField(
            name="summary",
            title="Summary",
            description="A brief description of this issue.",
            nonempty="true")
        self.AddField(field)

        # The categories field.
        field = qm.fields.EnumerationField(
            name="categories",
            enumeration=categories,
            title="Categories",
            description="""
            The names of categories to which this issue belongs.  A
            category is a group of issues that share a similar feature,
            for instance all bugs in the particular component.
            """)
        field = qm.fields.SetField(field)
        self.AddField(field)

        # The parents field.
        field = IidField(
            name="parents",
            title="Parents",
            description="""
            The issue ID of the issue from which this issue was split,
            or the issue IDs of the issues from which this issue was
            joined.
            """,
            hidden="true")
        field = qm.fields.SetField(field)
        self.AddField(field)

        # The children field.
        field = IidField(
            name="children",
            title="Children",
            description="""
            The issue IDs of issues into which this issue was split, or
            the issue ID of the issue which resulted when this issue was
            joined with other issues.
            """,
            hidden="true")
        field = qm.fields.SetField(field)
        self.AddField(field)


    def GetName(self):
        """Return the name of this class."""

        return self.__name


    def GetTitle(self):
        """Return the user-friendly title of this class."""

        return self.__title


    def GetDescription(self):
        """Return a description of this issue class."""

        return self.__description


    def GetFields(self):
        """Return the fields in this class.

        returns -- A sequence of fields.  The order of the fields is
        the order in which they were added to the class."""

        return self.__fields


    def HasField(self, name):
        """Return true if there is a field named 'name'."""

        return self.__fields_by_name.has_key(name)


    def GetField(self, name):
        """Return the field named by 'name'.

        raises -- 'KeyError' if 'name' is not the name of a field of
        this issue class."""

        try:
            return self.__fields_by_name[name]
        except KeyError:
            raise KeyError, \
                  qm.track.error("field not in class",
                                 field_name=name,
                                 issue_class_name=self.GetName())

        
    def AddField(self, field):
        """Add a new field to the issue class.

        'field' -- An instance of a subclass of 'Field' which describes
        the field to be added.  The object is copied, and subsequent
        modifications to it will not affect the issue class.

        'default_value' -- The value to assign for this field to
        existing issues of the issue class.  If 'None', there is no
        default, and each newly-created issue must assign this field.
        Otherwise, must be a valid field value."""

        name = field.GetName()
        self.__fields_by_name[name] = field
        self.__fields.append(field)


    def DiagnosticPrint(self, file):
        """Print a debugging summary to 'file'."""

        file.write("IssueClass %s\n" % self.GetName())
        for field in self.__fields:
            name = field.GetName()
            file.write("  -- %s: %s, default = %s\n"
                       % (name, field.__class__.__name__,
                          repr(self.__default_values[name])))
        file.write("\n")


    def RegisterTrigger(self, trigger):
        """Add 'trigger' to the list of triggers for this class.

        'trigger' -- An instance of a 'Trigger' subclass."""
        
        self.__triggers.append(trigger)


    def GetTriggers(self):
        """Return a sequence of triggers registered for this class."""

        return self.__triggers



########################################################################
# initialization
########################################################################

def _initialize_module():
    global default_state_model

    states = [
        State(name="submitted",
              description="""
              The issue has been submitted, but has not been verified.
              """
              ),

        State(name="active",
              description="""
              The issue has been verified, and is scheduled for
              resolution.
              """
              ),

        State(name="unreproducible",
              description="""
              The issue could not be reproduced.
              """
              ),

        State(name="will_not_fix",
              description="""
              The issue has been verified, but there are no plans to
              resolve it.
              """
              ),

        State(name="resolved",
              description="""
              The issue has been resolved.
              """
              ),

        State(name="tested",
              description="""
              The resolution of the issue has been tested and verified.
              """
              ),

        State(name="closed",
              description="""
              The issue is no longer under consideration.
              """
              ),
        ]

    condition = TransitionCondition("must have categories",
                                    "len(categories) > 0")

    transitions = [
        Transition("submitted", "active", [ condition ]),
        Transition("submitted", "unreproducible"),
        Transition("submitted", "will_not_fix"),
        Transition("active", "submitted"),
        Transition("active", "resolved"),
        Transition("resolved", "active"),
        Transition("resolved", "tested"),
        Transition("tested", "resolved"),
        Transition("tested", "closed"),
        Transition("unreproducible", "submitted"),
        Transition("unreproducible", "closed"),
        Transition("will_not_fix", "submitted"),
        Transition("will_not_fix", "closed"),
        ]

    default_state_model = StateModel(states, "submitted", transitions)


_initialize_module()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
