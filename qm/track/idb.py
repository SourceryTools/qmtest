########################################################################
#
# File:   idb.py
# Author: Alex Samuel
# Date:   2000-12-21
#
# Contents:
#   Generic issue database (IDB) code.
#
# Copyright (c) 2000 by CodeSourcery, LLC.  All rights reserved. 
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
# classes
########################################################################

class Trigger:
    """Base class for triggers.

    Triggers are represented by instances of subclasses of this
    class.  Each subclass must override the '__call__()' method to
    perform the trigger action and return an outcome."""

    def __init__(self, name):
        """Create a new trigger instance."""

        self.__name = name


    def GetName(self):
        """Return the name of this trigger instance."""

        return self.__name


    def __call__(self, issue, previous_issue):
        """Invoke the trigger.

        'issue' -- An 'Issue' instance.  For a "get" trigger, the
         issue being retrieved.  For update triggers, the state of the
         issue as it will be or is after the update.

        'previous_issue' -- An 'Issue' instance.  For a "get" trigger,
        'None'.  For update triggers, the state of the issue before
        the update.

        returns -- A 'TriggerOutcome' object.  The result is ignored
        for postupdate triggers."""

        # This function should be overridden by derived classes.
        raise NotImplementedError, "__call__ method must be overridden"



class TriggerOutcome:
    """The outcome of invoking a trigger."""

    def __init__(self, trigger, result, message=None):
        """Create a new outcome instance.

        'trigger' -- The 'Trigger' subclass instance of the trigger
        that created this outcome.

        'result' -- A boolean value indicating the result of the
        trigger.  A false value indicates a veto of the current
        operation (ignored for postupdate triggers).

        'message' -- A string describing the trigger's action or
        decision in structured text."""
        
        self.__trigger_name = trigger.GetName()
        self.__result = result
        self.__message = message


    def GetResult(self):
        """Return the result of this trigger action.

        A false value indicates the operation was vetoed by the
        trigger.""" 

        return self.__result


    def GetMessage(self):
        """Return a message describing the outcome.

        returns -- A string containing structured text, or 'None'."""

        return self.__message


    def GetTriggerName(self):
        """Return the name of the trigger that created this outcome."""
        
        return self.__trigger_name
    



class IdbBase:
    """Base class for IDB implementations."""

    def __init__(self):
        """Create a new IDB connection."""

        self.__triggers = {
            "get" : [],
            "preupdate" : [],
            "postupdate" : []
            }


    def RegisterTrigger(self, type, trigger):
        """Register a trigger.

        'type' -- The type is a string indicating the trigger type.

           * '"get"' triggers are invoked on issue records that are
             retrieved or returned as query results.  

           * '"preupdate"' triggers are invoked before an issue is
             updated.  

           * '"postupdate"' triggers are invoked after an issue is
             updated.  

        'trigger' -- The trigger, a callable object.  The trigger
        takes two arguments, both instances of 'IssueRecord'.

        The same trigger may be registered more than once for each
        type, or for multiple types."""

        trigger_list = self.__GetTriggerListForType(type)
        trigger_list.append(trigger)


    def UnregisterTrigger(self, type, trigger):
        """Unregister a trigger.

        'type' -- If 'None', all instances of 'trigger' are
        unregistered.  Otherwise, only instances matching 'type' are
        unregistered.

        'trigger' -- The trigger to unregister."""

        trigger_list = self.__GetTriggerListForType(type)
        try:
            trigger_list.remove(trigger)
        except ValueError:
            raise ValueError, "trigger was not registered"


    def GetTriggers(self, type):
        """Return a sequence registered triggers of type 'type'."""

        # Copy the list, so callers don't fool around with it.
        return self.__GetTriggerListForType(type)[:]


    # Functions for derived classes.

    def __InvokeGetTriggers(self, issue):

        # Retrieve all the get triggers.
        trigger_list = self.__GetTriggerListForType("get")

        # For each issue, we'll construct a list of trigger
        # outcomes. 
        outcomes = []
        for trigger in trigger_list:
            # Invoke the trigger.  
            outcome = trigger(issue, None)
            outcomes.append(outcome)
            if not outcome.GetResult():
                # The trigger vetoed this issue.  Stop processing the
                # issue.
                return (0, outcomes)

        return (1, outcomes)
            

    def __InvokePreupdateTriggers(self, issue, previous_issue):

        # Retrieve all the get triggers.
        trigger_list = self.__GetTriggerListForType("preupdate")
        outcomes = []

        for trigger in trigger_list:
            # Invoke the trigger.
            outcome = trigger(issue, previous_issue)
            outcomes.append(outcome)
            if not outcome.GetResult():
                # The trigger vetoed the update.  Return immediately
                # without invoking further triggers.
                return (0, outcomes)

        return (1, outcomes)


    def __InvokePostupdateTriggers(self, issue, previous_issue):

        trigger_list = self.__GetTriggerListForType("postupdate")
        outcomes = []

        for trigger in trigger_list:
            # Invoke the trigger.
            outcome = trigger(issue, previous_issue)
            outcomes.append(outcome)

        return outcomes


    # Helper functions.

    def __GetTriggerListForType(self, type):
        """Return the list of triggers of 'type'.

        raises -- 'ValueError' if 'type' is not a valid type."""

        try:
            return self.__triggers[type]
        except KeyError:
            raise ValueError, "invalid trigger type: %s" % type



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
