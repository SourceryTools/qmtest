########################################################################
#
# File:   issue_store.py
# Author: Alex Samuel
# Date:   2001-09-19
#
# Contents:
#   Base implementation and accessories for issue stores.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

"""An issue store stores issue data.

An issue store implementation is a mechanism for storing issues' field
data.  QMTrack supports multiple issue store implementations, which may
include simple in-memory issue stores and more efficient database-based
stores.

An issue store only stores issues' field data.  Other IDB information,
such as issue classes, users, and other configuration, is stored
elsewhere in the IDB (see 'qm.track.issue_database').  Additionally, an
issue store does not store attachment data, though it does store other
portions of attachment field values.

An issue store implementation consists of a Python module file.  The
module must contain a subclass of 'IssueStore', which implements
storage and retrieval of issue field data.  The module must also provide
these three functions, which form the public interface to an issue store
implementation module:

  'create' -- Creates a new, empty issue store.

  'open' -- Opens a connection to an existing issue store, represented
  by an 'IssueStore' subclass instance.  The connection is closed via
  its 'Close' method.

  'destroy' -- Destroys an existing issue store.

The issue store implementation module must be placed in the Python
path.  Each 'IssueStore' class should define a 'module_name' attribute,
which specifies the full name of the Python module relative to the
Python path used."""

########################################################################
# imports
########################################################################

import issue_class
import qm.common
from   qm.common import MethodShouldBeOverriddenError

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

class IssueStore:
    """Base class for issue store connection implementations.

    An instance of a subclass of 'IssueStore' represents a connection to
    an existing issue store."""

    module_name = None
    """The name of the module providing this issue store implementation."""


    def __init__(self, path, issue_classes):
        """Create an issue store connection.

        'path' -- The path to the issue database directory.  The issue
        store may use one or more files or subdirectories in this
        directory.

        'issue_classes' -- A sequence of 'IssueClass' objects for issue
        classes in the containing issue database."""

        self.path = path
        self._issue_classes = issue_classes


    # Abstract public interface methods.

    def Close(self):
        """Close the issue store connection."""

        raise MethodShouldBeOverriddenError, "IssueStore.Close"


    def AddIssueClass(self, issue_class):
        """Augment the issue store to handle a new issue class.

        raises -- 'KeyError' if there already is an issue class with the
        same name."""

        raise MethodShouldBeOverriddenErorr, "IssueStore.AddIssueClass"


    def UpdateIssueClass(self, issue_class):
        """Modify the issue store for a change to an issue class.

        Call this function after changing an issue class currently
        handled by the issue store.  'issue_class' replaces the existing
        issue class with the same name.

        'issue_class' -- An 'IssueClass' object.

        raises -- 'KeyError' if there is no issue class already known to
        the issue store with the same name as 'issue_class'."""

        raise MethodShouldBeOverriddenError, "IssueStore.UpdateIssueClass"


    def AddIssue(self, issue, insert=0):
        """Add a new issue.

        Unless 'insert' is true, this function runs preupdate triggers
        on the issue before adding it.  One of these may veto the
        addition, in which case the function returns a false result.  If
        the addition succeeds, postupdate triggers are also run.

        'issue' -- The new issue.  Its ID must be available.  Its
        revision number must be zero.  Its issue class must be known to
        the issue store.

        'insert' -- If true, don't process triggers and add the issue
        unconditionally. 

        returns -- A true value if the addition succeeded, or a false
        value if it was vetoed by a trigger.

        raises -- 'ValueError' if there is already an issue with the
        same ID as 'issue'.

        postcondition -- The timestamp on the issue stored in the issue
        store is set to the current time."""
        
        raise MethodShouldBeOverriddenError, "IssueClass.AddIssue"


    def AddRevision(self, revision, insert=0):
        """Add a new revision of an existing issue.

        Unless 'insert' is true, this function runs preupdate triggers
        on the revision before adding it.  One of these may veto the
        addition, in which case the function returns a false result.  If
        the addition succeeds, postupdate triggers are also run.

        'revision' -- The new revision.  The revision must be of an
        issue that currently exists in the issue store.  Its revision
        number must be the next revision number for the issue.

        'insert' -- If true, don't process triggers and add the issue
        unconditionally. 

        returns -- A true value if the addition succeeded, or a false
        value if it was vetoed by a trigger.

        raises -- 'KeyError' if 'revision' is not a revision of an
        existing issue.

        postcondition -- The timestamp on the revision stored in the
        issue store is set to the current time."""
        
        raise MethodShouldBeOverriddenError, "IssueClass.AddRevision"


    def GetIssue(self, iid, revision=None):
        """Retrieve a revision of an issue by ID.

        'iid' -- The ID of the issue to retrieve.

        'revision' -- The revision number to retrieve.  If 'None', the
        current revision is returned.

        raises -- 'KeyError' if an issue with ID 'iid' cannot be
        found."""

        raise MethodShouldBeOverriddenError, "IssueClass.GetIssue"


    def Query(self, query, issue_class_name, all_revisions=0):
        """Return issues in one class matching a query.

        'query' -- A query string.  The string is a Python expression,
        and an issue revision is considered a match if the expression
        evaluates to a true value.

        'issue_class_name' -- The name of the issue class to query.
        Only issues in this class are considered.

        'all_revisions' -- If true, query all revisions of the issues in
        the issue class.  Only one revision of each issue will be
        returned; if several match, the most current one is used.
        Otherwise, query current revisions only.

        returns -- A sequence of matching issue revisions.  If
        'all_revisions' is false, all are current revisions.  Otherwise,
        some may not be."""

        raise MethodShouldBeOverriddenError, "IssueClass.Query"


    # Other public interface methods, for which default
    # implementations are provided.  Subclasses may redefine these for
    # optimization. 

    def HasIssue(self, iid):
        """Return true of the issue store contains an issue with 'iid'."""

        try:
            self.GetIssue(iid)
        except KeyError:
            return 0
        else:
            return 1


    def GetIssueHistory(self, iid):
        """Return a sequence of all revisions of an issue.

        'iid' -- The ID of the issue to retrieve.

        returns -- A sequence of 'Issue' objects.  The index of each
        element is its revision number.

        raises -- 'KeyError' if issue 'iid' cannot be found."""

        # Get the latest revision, to find its revision number.
        current_revision = self.GetIssue(iid)
        current_revision_number = current_revision.GetRevisionNumber()
        # Build a list of all revisions up to the current one.
        revisions = []
        for revision_number in range(0, current_revision_number):
            revisions.append(self.GetIssue(iid, revision_number))
        # Add the current one too.
        revisions.append(current_revision)
        return revisions


    def GetCurrentRevisionNumber(self, iid):
        """Return the current revision number of issue 'iid'.

        raises -- 'KeyError' if issue 'iid' cannot be found."""

        return self.GetIssue(iid).GetRevisionNumber()
    


########################################################################
# functions
########################################################################

def invoke_get_triggers(issue):
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
        if result.GetOutcome() == issue_class.TriggerResult.REJECT:
            # The trigger rejected this issue.  Stop processing the
            # issue.
            raise TriggerRejectError, result


def invoke_preupdate_triggers(issue, previous_issue):
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
        if result.GetOutcome() == issue_class.TriggerResult.REJECT:
            # The trigger vetoed the update.  Return immediately
            # without invoking further triggers.
            raise TriggerRejectError, result


def invoke_postupdate_triggers(issue, previous_issue):
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
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
