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
# imports
########################################################################

import cPickle
import rexec
import qm
import issue
import issue_class
import os
import qm.fields
import string
import types

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

    # Subclasses of 'IdbBase' should be added to 'get_idb_class',
    # below, so that they can be referred to by name in the persistent
    # configuration.


    def __init__(self, path, create_idb):
        """Create a new IDB connection."""

        self.path = path
        # If this is a new IDB, create the directory to contain it.
        if create_idb:
            if not os.path.isdir(path):
                if os.path.exists(path):
                    raise ValueError, \
                          'IDB path %s alread exists' % path
                else:
                    os.mkdir(path)
            attachment_path = self.__GetAttachmentPath("")
            os.mkdir(attachment_path)
        # Initialize trigger lists.
        self.__triggers = {
            "get" : [],
            "preupdate" : [],
            "postupdate" : []
            }

        if create_idb:
            # Start numbering attachments from zero
            self.__next_attachment_index = 0
        else:
            # Read the index of the next attachment from a file.
            path = self.__GetAttachmentPath("next")
            index_file = open(path, "r")
            self.__next_attachment_index = int(index_file.read())
            index_file.close()
            

    def Close(self):
        """Shut down the IDB connection."""

        # Write out the next attachment index.
        path = self.__GetAttachmentPath("next")
        index_file = open(path, "w")
        index_file.write("%d\n" % self.__next_attachment_index)
        index_file.close()


    def GetNewAttachmentLocation(self):
        """Return a location for the data for a new attachment."""

        location = "%06d.bin" % self.__next_attachment_index
        self.__next_attachment_index = self.__next_attachment_index + 1
        return location


    def SetAttachmentData(self, location, data):
        """Set the data for the attachment at 'location' to 'data'."""

        # Find the file system path to the attachment data.
        path = self.__GetAttachmentPath(location)
        # Write the data.
        attachment_file = open(path, "w")
        attachment_file.write(data)
        attachment_file.close()


    def GetAttachmentData(self, location):
        """Return the data for the attachment at 'location'."""

        # Find the file system path to the attachment data.
        path = self.__GetAttachmentPath(location)
        # Read the data.
        attachment_file = open(path, "r")
        data = attachment_file.read()
        attachment_file.close()
        return data


    def GetAttachmentSize(self, location):
        """Return the size in bytes of the attachment at 'location'."""

        # Find the file system path to the attachment data.
        path = self.__GetAttachmentPath(location)
        # Use 'stat' to return the file size.
        return os.stat(path)[6]


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


    def GetIssues(self):
        """Return a list of all the issues.

        *This method is deprecated and should not be used.*"""

        
        # This function should be overridden by derived classes.
        raise NotImplementedError, "GetIssues method must be overridden"

    
    def Query(self, query_str, issue_class_name):
        """Query on the database.
        
        query_str -- The string with the python expression to be evaluated
        on each issue to determine if the issue matches.
        
        issue_class_name -- The name of the class of which you wish to
        query issues.  Only issues of that class will be queried.  
        
        returns -- This function returns a list of issues that match a
        query.

        raises -- Any error that can be raised by the 'rexec' function."""

        self.results = [ ]
        for issue in self.GetIssues():
            query_env = rexec.RExec()
            # Import string operations so that they may be used in
            # a query.
            query_env.r_exec("import string");
            c = issue.GetClass()

            # We should only do the query if the issue is of the correct
            # class.
            if c.GetName() == issue_class_name:
                # Set up the execution environment for the expression.
                for field in c.GetFields():
                    field_name = field.GetName()
                    # Set each field to be its current value in the issue.
                    field_value = issue.GetField(field_name)
                    query_env.r_exec("%s = %s"
                                     % (field_name, repr(field_value)))
                    # We have to check to see if this class is an
                    # enumeration.  If it is, grab the mapping and use
                    # that.  Alternately, it might be a set of
                    # enumerations, in which case we need to fish
                    # into the set to get the mapping of each thing
                    # that could be in the set.
                    enum_type = qm.fields.EnumerationField
                    enum = None
                    if not isinstance(field, enum_type):
                        try:
                            contained = field.GetContainedField()
                            if isinstance(contained, enum_type):
                                enum = contained.GetEnumeration()
                        except:
                            pass
                    else:
                        enum = field.GetEnumeration()

                    # Set all the enumerals to be their value.
                    if enum != None:
                        for key, value in enum.items():
                            query_env.r_exec("%s = %d" % (str(key),
                                                          int(value)))

                # Execute the expression.  If it's true, add this issue to
                # the results to be printed.  For exceptions that are raised,
                # we don't catch them; the calling function must handle
                # the errors.  We might want to change this in the future.
                if query_env.r_eval(query_str):
                    self.results.append(issue)
                
        return self.results

        
    # Functions for derived classes.

    def __GetAttachmentPath(self, location):
        """Return the path to the attachment at 'location'."""

        return os.path.join(self.path, "attachments", location)
    

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
# functions
########################################################################

def get_idb_class(idb_type):
    """Return the IDB class corresponding to the name 'idb_type'."""

    # Import modules conditionally, so we don't drag in lots of stuff
    # we won't need.

    if idb_type == "MemoryIdb":
        import qm.track.memory_idb
        return qm.track.memory_idb.MemoryIdb
    elif idb_type == "GadflyIdb":
        import qm.track.gadfly_idb
        return qm.track.gadfly_idb.GadflyIdb
    else:
        raise ValueError, "unknown IDB type %s" % idb_type


def get_field_type_description_for_query(field):
    """Return a summary of how to use 'field' in Python query expressions."""

    if isinstance(field, qm.fields.EnumerationField):
        enumerals = field.GetEnumerals()
        enumerals = map(lambda x: '"%s"' % x[0], enumerals)
        return "an enumeration of %s" % string.join(enumerals, ", ")
    elif isinstance(field, qm.fields.TimeField):
        return "a date/time (right now, it is %s)" % field.GetCurrentTime()
    elif isinstance(field, issue_class.IidField):
        return "a valid issue ID"
    elif isinstance(field, qm.fields.UidField):
        return "a valid user ID"
    elif isinstance(field, qm.fields.IntegerField):
        return "an integer"
    elif isinstance(field, qm.fields.TextField):
        return "a string"
    elif isinstance(field, qm.fields.SetField):
        contained_field = field.GetContainedField()
        return "a sequence; each element is %s" \
               % get_field_type_description_for_query(contained_field)
    elif isinstance(field, qm.fields.AttachmentField):
        return "an attachment; may not be used in queries"
    else:
        raise NotImplementedError


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
