########################################################################
#
# File:   memory_issue_store.py
# Author: Alex Samuel
# Date:   2001-01-03
#
# Contents:
#   In-memory issue store implementation.  Issues are persisted in an
#   XML file.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

"""In-memory issue store implementation.

All issues and revisions are stored in memory while connected to the
issue store.  Persistance is via the standard XML issue history file
format."""

########################################################################
# imports
########################################################################

import __builtin__
import issue
import issue_class
import issue_store
import os
import qm.common
import shutil

_builtin_open = __builtin__.open

########################################################################
# classes
########################################################################

class IssueStore(issue_store.IssueStore):
    """A connection to an in-memory issue store."""

    module_name = "qm.track.memory_issue_store"


    def __init__(self, path, issue_classes, issues):
        """Create a new IDB connection.

        'path' -- The path to the persistent IDB."""

        # Perform base class initialization.
        issue_store.IssueStore.__init__(self, path, issue_classes)
        self.__issues = issues


    # Abstract functions of the base class defined here.

    def Close(self):
        self.__Write()
        # Render this object inoperative.
        del self.__issues


    def AddIssueClass(self, issue_class):
        name = issue_class.GetName()
        # Make sure there isn't already an issue class by this name.
        if self._issue_classes.has_key(name):
            raise KeyError, "issue class name %s already exists" % name
        # Remember it; nothing else to do.
        self._issue_classes[name] = issue_class


    def UpdateIssueClass(self, issue_class):
        issue_class_name = issue_class.GetName()
        old_issue_class = self._issue_classes[issue_class_name]

        # Determine whether any fields were added or removed.
        added_fields = []
        removed_fields = []
        for field in issue_class.GetFields():
            field_name = field.GetName()
            try:
                old_field = old_issue_class.GetField(field_name)
            except KeyError:
                # There is no field by this name in the old issue
                # class.  It's a new field.
                added_fields.append(field)
            else:
                if old_field.__class__ is not field.__class__:
                    # There is a field by the same name, but it's a
                    # different type.
                    removed_fields.append(old_field)
                    added_fields.append(field)
        for field in old_issue_class.GetFields():
            if not issue_class.HasField(field.GetName()):
                # A field in the old class with no corresponding field
                # in the new class.  
                removed_fields.append(field)

        # Replace the the old issue class with the new one.
        self._issue_classes[issue_class_name] = issue_class

        # Update all the issues in this class.
        for issue_history in self.__issues.values():
            if issue_history[0].GetClass() is old_issue_class:
                # Scan over revisions of this issue.
                for revision in issue_history:
                    # For each field removed from the issue class,
                    # remove the corresponding value.
                    for field in removed_fields:
                        del revision._Issue__fields[field.GetName()]
                    # For each field added to the issue class, set the
                    # issue's value to the default value for the field.
                    for field in added_fields:
                        revision._Issue__fields[field.GetName()] = \
                            field.GetDefaultValue()
                    # Point the issue at the new, revised issue class
                    # object.
                    revision._Issue__issue_class = issue_class


    def AddIssue(self, issue, insert=0):
        iid = issue.GetId()
        qm.common.print_message(3, "Adding issue %s.\n" % iid)
        # Make sure the issue is OK.
        issue.AssertValid()
        # Make sure the revision number is zero.
        assert issue.GetRevisionNumber() == 0
        # Make sure the issue is in a class known to this IDB.
        issue_class = issue.GetClass()
        issue_class_name = issue_class.GetName()
        if not self._issue_classes.has_key(issue_class_name) or \
           self._issue_classes[issue_class_name] != issue_class:
            raise ValueError, "new issue in a class not in this IDB"
        # Make sure the IID is unique.
        if self.__issues.has_key(iid):
            raise ValueError, "iid is already used"

        # Copy the issue, since we'll be holding onto it.
        issue = issue.copy()
        if not insert:
            # Set the timestamp to now.
            issue.StampTime()
            # Invoke preupdate triggers.
            issue_store.invoke_preupdate_triggers(issue, None)

        # Store the new issue.
        self.__issues[iid] = [issue]

        if not insert:
            # Invoke postupdate triggers.
            issue_store.invoke_postupdate_triggers(issue, None)


    def AddRevision(self, revision, insert=0):
        iid = revision.GetId()
        revision_number = revision.GetRevisionNumber()
        qm.common.print_message(3, "Adding revision %s of issue %s.\n"
                                % (revision_number, iid))
        # Make sure the issue is OK.
        revision.AssertValid()
        # Copy the issue, since we'll be holding onto it.
        revision = revision.copy()
        # Retrieve the current list of revisions of the issue.
        history = self.__issues[iid]
        next_revision_number = len(history)
        # Make sure the new revision is in the same issue class.
        if revision.GetClass() != history[0].GetClass():
            raise ValueError, "revision in different issue class"
        # Make sure the new revision has the right revision number.
        assert revision_number == next_revision_number

        current_revision = history[-1]

        if not insert:
            # Set the timestamp to now.
            revision.StampTime()
            # Invoke preupdate triggers.
            issue_store.invoke_preupdate_triggers(revision, current_revision)

        # Store the new revision.
        history.append(revision)

        if not insert:
            # Invoke postupdate triggers.
            issue_store.invoke_postupdate_triggers(revision, current_revision)


    def GetIssue(self, iid, revision=None):
        # Look up the list of revisions of the issue.
        revisions = self.__issues[iid]
        if revision is None:
            # The current revision was requested; it's at the end of
            # the list.
            issue = revisions[-1]
        else:
            # Index into the list to retrieve the requested revision.
            issue = revisions[revision]

        # Found an issue.  Invoke get triggers.
        issue_store.invoke_get_triggers(issue)
        # All done.
        return issue.copy()


    def Query(self, query, issue_class_name, all_revisions=0):
        # Construct a list of histories of issues in the issue class
        # named by 'issue_class_name'. 
        issues_in_class = \
            filter(lambda his, name=issue_class_name:
                   his[0].GetClass().GetName() == name,
                   self.__issues.values())
        results = []
        # Loop over current revisions or all revisions, depending on
        # 'all_revisions'. 
        if all_revisions:
            for history in issues_in_class:
                # Scan over revisions from most current to least
                # current. 
                for revision_number in range(len(history) - 1, -1, -1):
                    revision = history[revision_number]
                    if issue.eval_issue_expression(query, revision):
                        # Query matched this revision.
                        results.append(revision)
                        # Break out of the inner loop so we don't
                        # consider earlier revisions.
                        break
        else:
            for history in issues_in_class:
                # Query the current revision only.
                current_revision = history[-1]
                if issue.eval_issue_expression(query, current_revision):
                    results.append(current_revision)
                
        return results


    # Helper functions.
    
    def __Write(self):
        """Write out the IDB state."""

        # We write the issues to a temporary file, and then copy this
        # file over the main issues file.  This is done for safety: if
        # the write is interrupted, we haven't corrupted the old issue
        # file, at least.

        # Construct the temporary file name.
        temporary_path = _get_issue_path(self.path) + ".crash"
        # Write the issues to the temporary file.
        file = _builtin_open(temporary_path, "w")
        issue.write_issue_histories(self.__issues.values(), file)
        file.close()
        # Overwrite the main issues file.
        shutil.copy(temporary_path, _get_issue_path(self.path))
        # Remove the temporary file.
        os.unlink(temporary_path)
        


########################################################################
# functions
########################################################################

# These three functions are part of the module interface for issue store
# implementations.

def create(path, configuration):
    # Create a new issue store with no classes or issues.
    new_issue_store = IssueStore(path, [], {})
    # Close it, which writes it out.
    new_issue_store.Close()


def open(path, issue_classes, configuration, attachment_store):
    # Load the issue histories.
    qm.common.print_message(3, "MemoryIdb: Loading issues... ")
    histories = \
        issue.load_issue_histories(_get_issue_path(path),
                                   issue_classes, attachment_store)

    # Install them and perform sanity checks.
    qm.common.print_message(3, "checking... ")
    issues = {}
    for issue_history in histories:
        issue_class = issue_history[0].GetClass()
        iid = issue_history[0].GetId()
        # Make sure all revisions of an issue have the same
        # issue ID and class and the proper sequence ascending
        # revision numbers.
        for index in xrange(0, len(issue_history)):
            revision = issue_history[index]
            assert revision.GetClass() is issue_class
            assert revision.GetId() == iid
            assert revision.GetRevisionNumber() == index
        # Store the issue.
        issues[iid] = issue_history
        # Make sure the issue class object matches the one
        # registered for the issue class of that name.
        assert issue_classes[issue_class.GetName()] is issue_class

    qm.common.print_message(3, "done.\n")
    return IssueStore(path, issue_classes, issues)


def destroy(path):
    # Remove the issue file.
    issue_file_path = _get_issue_path(path)
    os.unlink(issue_file_path)


# Helper functions.

def _get_issue_path(idb_path):
    """Return the path to the file containing issue data.

    'idb_path' -- The path to the IDB."""

    return os.path.join(idb_path, "issues")


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
