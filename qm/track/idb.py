########################################################################
#
# File:   idb.py
# Author: Alex Samuel
# Date:   2000-12-21
#
# Contents:
#   Generic issue database (IDB) code.
#
# Copyright (c) 2000, 2001 by CodeSourcery, LLC.  All rights reserved. 
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
import issue_class
from   issue_class import TriggerResult
import os
import qm
import qm.code
from   qm.code import abstract_method
import qm.common
import qm.fields
import qm.track.issue
import string
import types

########################################################################
# exceptions
########################################################################

class TriggerRejectError(RuntimeError):
    """An exception indicating that a trigger has rejected an operation.

    This exception is thrown when a trigger was invoked and returned a
    'REJECT' outcome while proccessing a read or write operation on an
    issue database.

    The exception argument is a 'TriggerResult' object."""


    def GetResult(self):
        """Return the accompanying trigger result."""

        return self.args[0]



########################################################################
# classes
########################################################################

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


    def Query(self, query_str, issue_class_name):
        """Query on the database.
        
        query_str -- The string with the python expression to be evaluated
        on each issue to determine if the issue matches.
        
        issue_class_name -- The name of the class of which you wish to
        query issues.  Only issues of that class will be queried.  
        
        returns -- This function returns a list of issues that match a
        query."""

        results = [ ]
        for issue in self.GetIssues():
            # We should only do the query if the issue is of the correct
            # class.
            if issue.GetClass().GetName() == issue_class_name \
               and qm.track.issue.eval_issue_expression(query_str, issue):
                results.append(issue)
                    
        return results


    # Functions that must be overridden in derived classes.

    def GetIssueClass(self, name):
        """Return an issue class object."""
        
        raise qm.common.MethodShouldBeOverriddenError, "BaseIdb.GetIssueClass"


    def AddIssueClass(self, issue_class):
        """Add 'issue_class' to the IDB.

        raises -- 'KeyError' if there is already a class in the
        IDB with the same name as the name of 'issue_class'."""

        raise qm.common.MethodShouldBeOverriddenError, "BaseIdb.AddIssueClass"

    
    def GetIssues(self):
        """Return a list of all the issues.

        *This method is deprecated and should not be used.*"""

        raise qm.common.MethodShouldBeOverriddenError, "BaseIdb.GetIssues"


    def AddIssue(self, issue):
        """Add a new issue record to the database.

        'issue' -- The new issue.  The revision number is ignored and
        set to zero.

        precondition -- The issue class of 'issue' must occur in this
        IDB, and fields of 'issue' must match the class's.

        returns -- A true value if the insert succeeded, or a false
        value if it was vetoed by a trigger."""

        raise qm.common.MethodShouldBeOverriddenError, "BaseIdb.AddIssue"


    # Functions for derived classes.

    def __GetAttachmentPath(self, location):
        """Return the path to the attachment at 'location'."""

        return os.path.join(self.path, "attachments", location)
    

    def __InvokeGetTriggers(self, issue):
        """Run "get" triggers on 'issue'.

        Invokes the 'Get' method of any triggers registered in the issue
        class of 'issue'.

        raises -- 'TriggerRejectError' if a trigger rejects the get
        operation."""

        # Invoke all triggers for this issue class.
        trigger_list = issue.GetClass().GetTriggers()
        for trigger in trigger_list:
            # Invoke the trigger.  
            result = trigger.Get(issue)
            if result.GetOutcome() == TriggerResult.REJECT:
                # The trigger rejected this issue.  Stop processing the
                # issue.
                raise TriggerRejectError, result
            

    def __InvokePreupdateTriggers(self, issue, previous_issue):
        """Run "preupdate" triggers for an issue update.

        Invokes the 'Preupdate' method of any triggers registered in the
        issue class of 'issue'.

        raises -- 'TriggerRejectError' if a trigger rejects the get
        operation.

        'issue' -- The issue after the update.

        'previous_issue' -- The previous revision of the same issue,
        before the update."""

        # Invoke all triggers for this issue class.
        trigger_list = issue.GetClass().GetTriggers()
        for trigger in trigger_list:
            # Invoke the trigger.
            result = trigger.Preupdate(issue, previous_issue)
            if result.GetOutcome() == TriggerResult.REJECT:
                # The trigger vetoed the update.  Return immediately
                # without invoking further triggers.
                raise TriggerRejectError, result


    def __InvokePostupdateTriggers(self, issue, previous_issue):
        """Run "postupdate" triggers for an issue update.

        Invokes the 'Postupdate' method of any triggers registered in
        the issue class of 'issue'.

        'issue' -- The issue after the update.

        'previous_issue' -- The previous revision of the same issue,
        before the update."""

        # Invoke all triggers for this issue class.
        trigger_list = issue.GetClass().GetTriggers()
        for trigger in trigger_list:
            # Invoke the trigger.
            trigger.Postupdate(issue, previous_issue)



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


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
