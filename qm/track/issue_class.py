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
import qm.xmlutil
import qm.web
import string
import types

########################################################################
# constants
########################################################################

mandatory_field_names = [
    "iid",
    "revision",
    "timestamp",
    "user",
    "state",
    "summary",
    "categories",
    "parents",
    "children",
    ]
"""Names of mandatory issue class fields."""

# The default categories enumeration to use for a new issue class, if
# one is not provided.

# FIXME: These are bogus test values.  Put something better here.

default_categories = [
    "crash",
    "documentation",
    "improvement",
]


# The default set of states to use for a new issue class, if one is
# not provided.  This variable is initialzed in '_initialze_module',
# below. 

default_state_model = None

# The DTD for storing a list of issue classes.

issue_classes_dtd = "-//Software Carpentry//QMTrack Issue Classes V0.1//EN"

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

    class_name = "qm.track.issue_class.IidField"

    def __init__(self, name, default_value="", **properties):
        """Create an IID field."""
        
        # Do base-class initialization, with different defaults.
        properties = properties.copy()
        apply(qm.fields.TextField.__init__,
              (self, name, default_value),
              properties)


    def GetTypeDescription(self):
        return "an issue ID"


    def SetDefaultValue(self, value):
        if value is not "":
            value = self.Validate(value)
        self.default_value = value
        

    def Validate(self, value):
        value = str(value)
        if not qm.label.is_valid(value):
            raise ValueError, \
                  qm.track.error("invalid iid", iid=value) 
        return value



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

    class_name = None
    """The name of this class.

    Subclasses must define this to be a string containing the
    fully-qualified class name."""
    

    property_declarations = (
        qm.fields.PropertyDeclaration(
            name="name",
            description="The name of this trigger instance.",
            default_value=""
            ),
        
        )


    def __init__(self, name, **properties):
        """Create a new trigger instance.

        'name' -- The trigger name.

        'properties' -- Additional trigger properties to set."""

        self.__properties = {}
        # Initialize properties to defaults from property declarations. 
        for declaration in self.property_declarations:
            self.__properties[declaration.name] = \
                declaration.default_value
        # Set properties specified as arguments.
        for property_name, value in properties.items():
            self.SetProperty(property_name, value)
        self.SetProperty("name", name)


    def GetProperty(self, name, default=None):
        """Return the value of the property named 'name'.

        returns -- The value of the property 'name', or 'default' if
        these is no such property."""

        try:
            return self.__properties[str(name)]
        except KeyError:
            return default


    def SetProperty(self, name, value):
        """Set a property value.

        'name' -- The name of the property to set.

        'value' -- The value for the property.  If it is not a string,
        it is converted to one."""

        name = str(name)
        if not qm.label.is_valid(name):
            raise ValueError, name
        self.__properties[name] = str(value)


    def GetName(self):
        """Return the name of this trigger instance."""

        return self.GetProperty("name")


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


    def MakeDomNode(self, document):
        """Construct a DOM element node representing this trigger.

        'document' -- The DOM document in which to create the node."""

        # Construct the main element node.
        element = document.createElement("trigger")
        # Store the Python class name of the trigger's class.
        class_element = qm.xmlutil.create_dom_text_element(
            document, "class", self.class_name)
        element.appendChild(class_element)
        
        # Create an element for each property.
        for name, value in self.__properties.items():
            property_element = qm.xmlutil.create_dom_text_element(
                document, "property", str(value))
            property_element.setAttribute("name", name)
            element.appendChild(property_element)

        return element



########################################################################

class State:
    """A state in a state model.

    See 'StateModel' for more information."""

    def __init__(self, name, description, open=1):
        """Create a new state.

        'name' -- The name of this state.

        'description' -- A description of the significance of this
        state.

        'open' -- If true, this is considered an open state.  If false,
        this is considered a closed state."""
        
        self.__name = name
        self.__description = description
        self.__open = open


    def GetName(self):
        """Return the name of this state."""

        return self.__name


    def GetDescription(self):
        """Return a description of this state."""

        return self.__description


    def IsOpen(self):
        """Return true if this is an open state."""

        return self.__open



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
                 condition=None):
        """Create a new transition.

        'starting_state_name' -- The name of the state from which this
        transition leads.

        'ending_state_name' -- The name of the state to which this
        transition leads.

        'conditions' -- A sequence of 'TransitionCondition' objects.
        All must evaluate to true for the transition to be permitted."""
        
        self.__starting_state_name = starting_state_name
        self.__ending_state_name = ending_state_name
        self.__condition = condition


    def GetStartingStateName(self):
        """Return the name of the transition's starting state."""
        
        return self.__starting_state_name


    def GetEndingStateName(self):
        """Return the name of the transition's ending state."""

        return self.__ending_state_name


    def GetCondition(self):
        """Return the condition on this transition.

        returns -- A 'TransitionCondition' object, or 'None'."""

        return self.__condition



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
            return self.__states[str(state_name)]
        except KeyError:
            raise KeyError, "unknown state %s" % state_name


    def GetStateNames(self):
        """Return a sequence of names of the states in the state model."""

        return self.__states.keys()


    def GetOpenStateNames(self):
        """Return a sequence of names of open states in the state model."""

        open_states = filter(lambda s: s.IsOpen(), self.__states.values())
        return map(lambda s: s.GetName(), open_states)


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

    class_name = "qm.track.issue_class.StateField"

    property_declarations = \
        qm.fields.EnumerationField.property_declarations + [
        qm.fields.PropertyDeclaration(
            name="state_model",
            description="""The set of states available for this field,
            and allowed transitions among them.""",
            default_value=""),

        ]


    def __init__(self, name, **properties):
        """Construct a new field.

        The 'state_model' property must be initialized, to the encoded
        state model for this field (or a 'StateModel' instance).

        'name' -- The name of this field.

        postconditions -- The default value of this field is set to the
        state model's initial state."""

        state_model = properties["state_model"]
        if not isinstance(state_model, StateModel):
            state_model = decode_state_model(state_model)

        # Construct a starting enumeration consisting of the initial
        # state only.  We need the enumeration to be non-empty, and for
        # the default value (which is the initial state) to be a member
        # of it.
        initial_state_name = state_model.GetInitialStateName()
        enumerals = state_model.GetStateNames()
        # Initialize the base class.
        qm.common.purge_keys(
            properties,
            ["name", "initial_state_name", "enumerals", "state_model"])
        apply(qm.fields.EnumerationField.__init__,
              (self, name, initial_state_name, enumerals),
              properties)

        self.SetStateModel(state_model)

        
    def SetStateModel(self, state_model):
        """Set the state model for this field."""

        self.SetProperty("state_model", encode_state_model(state_model))


    def GetStateModel(self):
        """Return the state model for this field."""
        
        return decode_state_model(self.GetProperty("state_model"))


    def GetEnumerals(self):
        return self.GetStateModel().GetStateNames()


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
                transitions_to = map(lambda t: "*%s*" % t, transitions_to)
                transitions_to = string.join(transitions_to, " , ")
            else:
                transitions_to = "None"
            help = help + \
                   "            * *%s*: %s  Transitions to: %s.\n\n" \
                   % (state_name, description, transitions_to)
        # Also mention the state model's initial state.
        help = help + """
        The initial state is *%s*.
            """ % state_model.GetInitialStateName()
        return help


    def FormatValueAsHtml(self, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = self.GetDefaultValue()
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "edit":
            # Use a restricted select control showing only values for
            # reachable states.
            enumerals = self._GetAvailableEnumerals(value)
            # Make sure there are some enumerals.
            if len(enumerals) == 0:
                enumerals = self.GetEnumerals()
            # If the enumeration was changed, 'value' may not be a valid
            # enumeral anymore.
            if value not in enumerals:
                value = self.GetDefaultValue()
            # Construct the control.
            return qm.web.make_select(name, enumerals, value,
                                      str, self.FormEncodeValue)
        else:
            # Use the base-class implementation.
            return qm.fields.EnumerationField.FormatValueAsHtml(
                self, value, style, name)


    def _GetAvailableEnumerals(self, value):
        """Return enumerals corresponding to available states.

        'value' -- The value representing the current state.

        returns -- A list of enumeral values representing states
        reachable from the current state."""
        
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


    def MakePropertyControls(self):
        # Start with controls for base-class properties.
        controls = qm.fields.EnumerationField.MakePropertyControls(self)

        # Enumerals are specified implicitly by the state model.  Don't
        # let the user specify them explicitly.
        controls["enumerals"] = None

        # Construct a control to edit the state model.  Generate the
        # input name which will contain the string-encoded state mode.
        input_name = qm.fields.query_field_property_prefix + "state_model"
        # Get the current encoded state model.
        encoding = encode_state_model(self.GetStateModel())
        # Construct a hidden input for the encoded model, and
        # initialize it with the current value.
        hidden = '<input type="hidden" name="%s" value="%s" />' \
                 % (input_name, encoding)
        # Construct a button that pops up a page for editing the state
        # model.  The page reads the encoded state model out of the
        # hidden input, and puts the encoding of the modified model
        # there afterwards.
        request = qm.web.WebRequest("state-model", input=input_name)
        button = '''
        <input type="button"
               value=" Edit... "
               onclick="window.open('%s', 'popup',
                        'width=540,height=640,resizeable,scrollbars');"
        />''' % request.AsUrl()
        # Use these controls for the 'state_model' property.
        controls["state_model"] = hidden + button

        return controls
    


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

    class_name = "qm.track.issue_class.DiscussionField"

    def __init__(self, text_field):
        """Create a new discussion field.

        'text_field' -- A 'TextField' instance for elements of the
        discussion."""

        # Now construct our base class, the set field.
        apply(qm.fields.SetField.__init__, (self, text_field))


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
            description="The issue's unique identifier.",
            initialize_only="true")
        self.AddField(field)

        # The revision number field.
        field = qm.fields.IntegerField(
            name="revision",
            title="Revision Number",
            description="The cardinality of this revision of the issue.",
            hidden="true",
            read_only="true")
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
            description=
"""The state of this issue in the issue class's state model.

The state reflects the status of this issue within the set of
procedures by which an issue is normally resolved.""",
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
            not_empty_text="true")
        self.AddField(field)

        # The categories field.
        field = qm.fields.EnumerationField(
            name="categories",
            enumerals=categories,
            title="Categories",
            description=
"""The names of categories to which this issue belongs.

A category is a group of issues that share a similar feature, for
instance all bugs in the particular component."""
            )
        field = qm.fields.SetField(field)
        self.AddField(field)

        # The parents field.
        field = IidField(
            name="parents",
            title="Parents",
            description=
"""The issue ID of the issue from which this issue was split, or the
issue IDs of the issues from which this issue was joined.""",
            hidden="true",
            read_only="true")
        field = qm.fields.SetField(field)
        self.AddField(field)

        # The children field.
        field = IidField(
            name="children",
            title="Children",
            description=
"""The issue IDs of issues into which this issue was split, or the issue
ID of the issue which resulted when this issue was joined with other
issues.""",
            hidden="true",
            read_only="true")
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
                  qm.error("field not in class",
                           field_name=name,
                           issue_class_name=self.GetName())

        
    def AddField(self, field):
        """Add a new field to the issue class.

        'field' -- An instance of a subclass of 'Field' which describes
        the field to be added.  The object is copied, and subsequent
        modifications to it will not affect the issue class."""

        name = field.GetName()
        self.__fields_by_name[name] = field
        self.__fields.append(field)


    def RemoveField(self, field):
        """Remove a field from the issue class.

        'field' -- A field currently part of the issue class."""

        name = field.GetName()
        # Make sure this field is in the issue class.
        assert self.__fields_by_name[name] is field
        assert self.__fields.count(field) == 1
        # Remove it.
        del self.__fields_by_name[name]
        self.__fields.remove(field)


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
        
        # Remove any existing trigger with the same name.
        current_trigger = self.GetTrigger(trigger.GetName())
        if current_trigger is not None:
            self.__triggers.remove(current_trigger)
        # Add the trigger.
        self.__triggers.append(trigger)


    def GetTriggers(self):
        """Return a sequence of triggers registered for this class."""

        return self.__triggers


    def GetTrigger(self, name, default=None):
        """Return the trigger.

        returns -- The trigger whose name is 'name', or 'default' if no
        such trigger is registered for this class."""

        for trigger in self.__triggers:
            if trigger.GetName() == name:
                return trigger
        # No luck.
        return default


    def MakeDomNode(self, document):
        """Construct a DOM node describing the issue class.

        'document' -- The DOM document in which to contruct the node.

        returns -- A DOM node for an "issue-class" element."""

        # Create the main element node.
        element = document.createElement("issue-class")
        # Set the name in an attribute.
        element.setAttribute("name", self.GetName())
        # Annotate the title and description.
        title_element = qm.xmlutil.create_dom_text_element(
            document, "title", self.GetTitle())
        element.appendChild(title_element)
        description_element = qm.xmlutil.create_dom_text_element(
            document, "description", self.GetDescription())
        element.appendChild(description_element)

        # Store the fields.
        for field in self.__fields:
            field_element = field.MakeDomNode(document)
            element.appendChild(field_element)

        # Store the triggers.
        for trigger in self.__triggers:
            trigger_element = trigger.MakeDomNode(document)
            element.appendChild(trigger_element)

        return element



########################################################################
# functions
########################################################################

def encode_state_model(state_model):
    """Encode a state model as a string.

    'state_model' -- A 'StateModel' instance.

    returns -- A string encoding the state model.

    The encoding scheme is as follows:

      <encoding>    ::= <states> "|" <initial-state-name> "|" <transitions>
      <states>      ::= <state> ";" <state> ";" ...
      <state>       ::= <name> "," <description> "," <is-open>
      <is-open>     ::= "0" | "1"
      <transitions> ::= <transition> ";" <transition> ";" ...
      <transition>  ::= <start-state-name> "," <end-state-name> "," <condition>

    The values of <description> and <condition> are URL-escaped (see
    'qm.web.javascript_escape').

    Use 'decode_state_model' to reverse this encoding."""

    # Construct a list of all states.
    states = state_model._StateModel__states.values()
    # Encoded states go in a semicolon-separated list.
    states = string.join(map(encode_state, states), ";")
      
    # Obtain the initial state name.
    initial_state_name = state_model.GetInitialStateName()

    # Construct a flat list of all transitions.
    transitions = reduce(lambda l, m: l + m.values(),
                         state_model._StateModel__transitions.values(),
                         [])
    # Encoded transitions go in a semicolon-separated list.
    transitions = string.join(map(encode_transition, transitions), ";")

    # Join the three segments with pipes.
    return string.join([states, initial_state_name, transitions], "|")


def encode_state(state):
    """Encode a state.

    'state' -- A 'State' instance.

    returns -- A string encoding the state.

    See 'encode_state_model' for a description of the encoding scheme."""

    result = state.GetName() + "," \
             + qm.web.javascript_escape(state.GetDescription()) + "," \
             + str(state.IsOpen())
    return result


def encode_transition(transition):
    """Encode a transition.

    'transition' -- A 'Transition' instance.

    returns -- A string encoding the transition.

    See 'encode_state_model' for a description of the encoding scheme."""

    # Encode the start and end states.
    result = transition.GetStartingStateName() + "," \
             + transition.GetEndingStateName() + ","
    # Now encode the condition.
    condition = transition.GetCondition()
    if condition is not None:
        result = result + qm.web.javascript_escape(condition.GetExpression())
    else:
        # No condition; leave it blank.
        pass
    return result


def decode_state_model(encoding):
    """Decode a state model.

    'encoding' -- A string-encoded state model.

    returns -- A 'StateModel' instance.

    See 'encode_state_model' for a description of the encoding scheme."""

    # Split into three major parts.
    states, initial_state_name, transitions = string.split(encoding, "|")
    # Split and decode the list of states.
    states = map(decode_state, string.split(states, ";"))
    # Split and decode the list of transitions.
    transitions = map(decode_transition, string.split(transitions, ";"))
    # Construct the state model.
    return StateModel(states, initial_state_name, transitions)


def decode_state(encoding):
    """Decode a state.

    'encoding' -- A string-encoded state.

    returns -- A 'State' instance.

    See 'encode_state_model' for a description of the encoding scheme."""

    name, description, is_open = string.split(encoding, ",")
    return State(name, qm.web.javascript_unescape(description), int(is_open))


def decode_transition(encoding):
    """Decode a transition.

    'encoding' -- A string-encoded transition.

    returns -- A 'Transition' instance.

    See 'encode_state_model' for a description of the encoding scheme."""

    start, end, condition = string.split(encoding, ",")
    condition = string.strip(qm.web.javascript_unescape(condition))
    # Decode the condition.
    if condition == "":
        # An empty string signifies no condition.
        condition = None
    else:
        condition = TransitionCondition(
            "", qm.web.javascript_unescape(condition))
    return Transition(start, end, condition)
    

def trigger_from_dom_node(node):
    """Construct a trigger from a DOM node.

    'node' -- A DOM element node, with tag "trigger".

    returns -- A 'Trigger' object."""

    assert node.tagName == "trigger"

    # Get the Python class for the field.
    trigger_class_name = qm.xmlutil.get_child_text(node, "class")
    # Load the class.
    trigger_class = qm.common.load_class(trigger_class_name)

    # Construct a map of properties.
    properties = {}
    for property_node in node.getElementsByTagName("property"):
        property_name = property_node.getAttribute("name")
        property_value = qm.xmlutil.get_dom_text(property_node)
        properties[property_name] = property_value

    # Instantiate the trigger.
    trigger = apply(trigger_class, (), properties)
    # All done.
    return trigger


def from_dom_node(node, attachment_store):
    """Construct an issue class from a DOM node.

    'node' -- A DOM element node, with tag "issue-class".

    'attachment_store' -- The attachment store in which to presume
    attachments are located.

    returns -- An 'IssueClass' element."""

    assert node.tagName == "issue-class"

    # Get the main properties for the issue class.
    name = node.getAttribute("name")
    title = qm.xmlutil.get_child_text(node, "title")
    description = qm.xmlutil.get_child_text(node, "description")
    
    # Get field descriptors.
    fields = []
    fields_by_name = {}
    for field_node in qm.xmlutil.get_children(node, "field"):
        field = qm.fields.from_dom_node(field_node, attachment_store)
        fields.append(field)
        fields_by_name[field.GetName()] = field

    # Get triggers.
    triggers = []
    for trigger_node in qm.xmlutil.get_children(node, "trigger"):
        trigger = trigger_from_dom_node(trigger_node)
        triggers.append(trigger)

    # Construct the issue class.
    issue_class = IssueClass(name, title, description)
    issue_class._IssueClass__fields = fields
    issue_class._IssueClass__fields_by_name = fields_by_name
    issue_class._IssueClass__triggers = triggers
    return issue_class


def load(path, attachment_store):
    """Load issue classes from 'path'.

    'attachment_store' -- The attachment store in which to presume
    attachments are located.

    returns -- A map from issue class named to 'IssueClass' objects."""

    document = qm.xmlutil.load_xml_file(path)
    issue_classes = {}
    for node in \
        qm.xmlutil.get_children(document.documentElement, "issue-class"):
        issue_class = from_dom_node(node, attachment_store)
        issue_classes[issue_class.GetName()] = issue_class
    return issue_classes


def save(path, issue_classes):
    """Save issue classes to the file at 'path'.

    'issue_classes' -- A sequence of 'IssueClass' objects."""

    # Create an XML document.
    document = qm.xmlutil.create_dom_document(
        public_id=issue_classes_dtd,
        dtd_file_name="issue-classes.dtd",
        document_element_tag="issue-classes"
        )
    # Create issue class elements.
    for issue_class in issue_classes:
        issue_class_node = issue_class.MakeDomNode(document)
        document.documentElement.appendChild(issue_class_node)
    # Write it.
    qm.xmlutil.write_dom_document(document, open(path, "w"))
    

########################################################################
# initialization
########################################################################

def _initialize_module():
    global default_state_model

    states = [
        State(name="submitted",
              description=
"""The issue has been submitted, but has not been verified.""",
              open=1
              ),

        State(name="active",
              description=
"""The issue has been verified, and is scheduled for resolution.""",
              open=1
              ),

        State(name="unreproducible",
              description=
"""The issue could not be reproduced.""",
              open=0
              ),

        State(name="will_not_fix",
              description=
"""The issue has been verified, but there are no plans to resolve it.""",
              open=0
              ),

        State(name="resolved",
              description=
"""The issue has been resolved.""",
              open=1,
              ),

        State(name="tested",
              description=
"""The resolution of the issue has been tested and verified.""",
              open=1
              ),

        State(name="closed",
              description=
"""The issue is no longer under consideration.""",
              open=0
              ),
        ]

    condition = TransitionCondition("must have categories",
                                    "len(categories) > 0")

    transitions = [
        Transition("submitted", "active", condition),
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
