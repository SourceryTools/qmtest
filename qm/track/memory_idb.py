########################################################################
#
# File:   memory_idb.py
# Author: Alex Samuel
# Date:   2001-01-03
#
# Contents:
#   In-memory IDB implementation.  Uses Python pickling to make the
#   IDB persistent.
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

"""
In-memory IDB implementation.

All issues, revisions, and issue classes are constructed in memory.
Persistance is via standard Python pickling.
"""

########################################################################
# imports
########################################################################

import cPickle
import idb
import issue_class
import os
import qm
import types

########################################################################
# classes
########################################################################

class MemoryIdb(qm.track.IdbBase):

    # Issues and issue classes are stored in the following attributes:
    #
    #   '__issue_classes' -- A mapping from class names to
    #   'IssueClass' instances.
    #
    #   '__issues' -- A mapping from iids to sequences of 'Issue'
    #   instances.  Each sequence contains the revisions of the issue,
    #   indexed by revision number.


    # Overrides of base class functions.

    def __init__(self, path, create_idb=0):
        """Create a new IDB "connection".

        'path' -- The path to the persistent IDB.

        'create_idb' -- If true, creates a new IDB from scratch at the
        specified path.  Otherwise, loads in an existing IDB."""

        # Perform base class initialization.
        qm.track.IdbBase.__init__(self, path, create_idb)

        if create_idb:
            # Initially there are no issues and issue classes.
            self.__issue_classes = {}
            self.__issues = {}
        else:
            # Load the issue classes and issues from a pickle.
            pickle_file = open(self.__GetPicklePath(), "r")
            persistent = cPickle.load(pickle_file)
            pickle_file.close()
            # The pickle contains a tuple of these two items.
            self.__issue_classes, self.__issues = persistent


    def Close(self):
        """Close an IDB connection and write out the IDB state."""
        
        self.__Write()
        # Perform base class operation.
        qm.track.IdbBase.Close(self)


    # Abstract functions of the base class defined here.

    def GetIssueClass(self, name):
        return self.__issue_classes[name]
        

    def AddIssueClass(self, issue_class):
        name = issue_class.GetName()
        if self.__issue_classes.has_key(name):
            raise KeyError, "issue class name %s already exists" % name

        self.__issue_classes[name] = issue_class
        self.__Write()


    def AddIssue(self, issue, insert=0):
        """Add a new issue record to the database.

        'issue' -- The new issue.  The revision number is ignored and
        set to zero.

        'insert' -- If true, insert the issue without invoking any
        triggers or changing the issue.  The revision number on the
        issue must be zero.

        precondition -- The issue class of 'issue' must occur in this
        IDB, and fields of 'issue' must match the class's.

        raises -- 'idb.IssueExistsError' if there is already an issue in
        the IDB with the same IID as 'issue'."""

        # Make sure the issue is OK.
        issue.AssertValid()
        # Copy the issue, since we'll be holding onto it.
        issue = issue.copy()
        # Make sure the issue is in a class known to this IDB.
        issue_class = issue.GetClass()
        issue_class_name = issue_class.GetName()
        if not self.__issue_classes.has_key(issue_class_name) or \
           self.__issue_classes[issue_class_name] != issue_class:
            raise ValueError, "new issue in a class not in this IDB"
        # Make sure the iid is unique.
        iid = issue.GetId()
        if self.__issues.has_key(iid):
            raise idb.IssueExistsError, "iid is already used"

        if insert:
            assert issue.GetRevision() == 0
        else:
            # Set the initial revision number to zero.
            issue.SetField("revision", 0)
            # Set the timestamp to now.
            issue.StampTime()

        if not insert:
            # Invoke preupdate triggers.
            self._InvokePreupdateTriggers(issue, None)

        # Store the new issue.
        self.__issues[iid] = [issue]

        if not insert:
            # Invoke postupdate triggers.
            self._InvokePostupdateTriggers(issue, None)

        # Commit changes.
        self.__Write()


    def AddRevision(self, issue, insert=0):
        """Add a revision of an existing issue to the database.

        'issue' -- A new revision of an existing issue.  The revision
        number is ignored and replaced with the next consecutive one
        for the issue.

        'insert' -- If true, insert the revision without invoking any
        triggers or changing the revision.  The revision number on the
        issue must be the next revision number for the issue."""

        # Make sure the issue is OK.
        issue.AssertValid()
        # Copy the issue, since we'll be holding onto it.
        issue = issue.copy()
        # Retrieve the current list of revisions of the issue.
        iid = issue.GetId()
        revisions = self.__issues[iid]
        prevision_revision = revisions[-1]
        # Make sure the new revision is in the same issue class.
        if issue.GetClass() != revisions[0].GetClass():
            raise ValueError, "revision in different issue class"

        next_revision_number = len(revisions)
        if insert:
            assert issue.GetRevision() == next_revision_number
        else:
            # Assign the next revision number.
            issue.SetField("revision", next_revision_number)
            # Set the timestamp to now.
            issue.StampTime()

        if not insert:
            # Invoke preupdate triggers.
            self._InvokePreupdateTriggers(issue, previous_revision)

        # Store the new revision.
        revisions.append(issue)

        if not insert:
            # Invoke postupdate triggers.
            self._InvokePostupdateTriggers(issue, previous_revision)

        # Commit changes.
        self.__Write()


    def GetIssueClasses(self):
        """Return a sequence of issue classes in this IDB."""

        return self.__issue_classes.values()


    def GetIids(self):
        """Return a sequence containing all the IIDs in this IDB."""

        return self.__issues.keys()


    def GetIssues(self, issue_class=None):
        """Return a list of all the issues.

        'issue_class' -- If an issue class name or 'IssueClass'
        instance is provided, all issues in this class will be
        returned.  If 'issue_class' is 'None', returns all issues in
        all classes.

        returns -- Returns a list of all the issues in the
        database."""

        # If 'issue_class' is the name of an issue class, look up the
        # class itself.
        if isinstance(issue_class, types.StringType):
            issue_class = self.__issue_classes[issue_class]
        # Get all the issues.
        matching_issues = self.__issues.values()
        # If we're restricted to one class, limit to those.
        if issue_class is not None:
            filter_fn = lambda i, cl=issue_class: i[0].GetClass() == cl
            matching_issues = filter(filter_fn, matching_issues)
        # Don't return the issues themselves -- return copies instead.
        return map(lambda issue: issue[-1].copy(), matching_issues)

    
    def HasIssue(self, iid):
        """Return true if the IDB contains an issue with the IID 'iid'."""

        try:
            self.GetIssue(iid)
        except KeyError:
            return 0
        else:
            return 1


    def GetIssue(self, iid, revision=None, icl=None):
        """Return the current revision of issue 'iid'.

        'revision' -- The revision number to retrieve.  If 'None', the
        current revision is returned.

        'icl' -- If 'None', all issue classes are searched for 'iid'.
        If an issue class name or 'IssueClass' instance are given,
        only that issue class is used.

        raises -- 'KeyError' if an issue with 'iid' cannot be found."""

        # If 'issue_class' is the name of an issue class, look up the
        # class itself.
        if isinstance(issue_class, types.StringType):
            icl = self.__issue_classes[icl]
        # Look up the list of revisions of the issue.
        revisions = self.__issues[iid]
        # If an issue class was provided, make sure the issue is in
        # that class.  Otherwise, consider the issue not found.
        if icl != None \
           and revisions[0].GetClass() != icl:
            raise KeyError, "issue not found in specified issue class"
        if revision == None:
            # The current revision was requested; it's at the end of
            # the list.
            issue = revisions[-1]
        else:
            # Index into the list to retrieve the requested revision.
            issue = revisions[revision]

        # Found an issue.  Invoke get triggers.
        self._InvokeGetTriggers(issue)

        # All done.
        return issue.copy()


    def GetAllRevisions(self, iid, issue_class=None):
        """Return a sequence of all revisions of an issue.

        'iid' -- The issue of which to retrieve all revisions.

        'issue_class' -- The issue class to search for this issue.  If
        'None', all issue classes are checked.

        returns -- A sequence of 'IssueRecord' objects, all
        corresponding to 'iid', indexed by revision number."""

        # If 'issue_class' is the name of an issue class, look up the
        # class itself.
        if isinstance(issue_class, types.StringType):
            issue_class = self.__issue_classes[issue_class]
        # Look up the list of revisions of the issue.
        revisions = self.__issues[iid]
        # If an issue class was provided, make sure the issue is in
        # that class.  Otherwise, consider the issue not found.
        if issue_class != None \
           and revisions[0].GetClass() != issue_class:
            raise KeyError, "issue not found in specified issue class"

        # Invoke get triggers on each resulting revision.
        issues = []
        for issue in revisions:
            try:
                self._InvokeGetTriggers(issue)
            except idb.TriggerRejectError:
                pass
            else:
                # Keep the revision only if the trigger passed it.
                issues.append(issue.copy())

        # Return the list of revisions that were accepted.
        return issues


    def GetCurrentRevisionNumber(self, iid):
        """Return the current revision number for issue 'iid'."""

        # Retrieve the list of revisions of this issue.
        revisions = self.__issues[iid]
        # The current revision number is the revision number of the
        # last (most recent) revision.
        return revisions[-1].GetRevision()


    def UpdateIssueClass(self, issue_class):
        """Update an issue class.

        Finds the issue class in the IDB whose name is the same as that
        of 'issue_class', and replaces it with 'issue_class'.

        'issue_class' -- An 'IssueClass' object."""

        issue_class_name = issue_class.GetName()
        old_issue_class = self.GetIssueClass(issue_class_name)

        old_fields = old_issue_class.GetFields()
        old_field_names = map(lambda f: f.GetName(), old_fields)
        new_fields = issue_class.GetFields()
        new_field_names = map(lambda f: f.GetName(), new_fields)

        # Determine whether any fields were added or removed.
        added_fields = []
        for field in new_fields:
            if not field.GetName() in old_field_names:
                added_fields.append(field)
        removed_fields = []
        for field in old_fields:
            if not field.GetName() in new_field_names:
                removed_fields.append(field)

        # FIXME: Implement this.
        if len(added_fields) > 0 or len(removed_fields) > 0:
            raise NotImplementedError, "add or remove fields from issue class"

        # Replace the the old issue class with the new one.
        self.__issue_classes[issue_class_name] = issue_class
        self.__Write()


    # Helper functions.
    
    def __Write(self):
        """Write out the IDB state."""

        # Open a pickle file.
        pickle_file = open(self.__GetPicklePath(), "w")
        # The persistent state consists of a tuple containing the
        # issue class map and the issue map.
        persistent = (
            self.__issue_classes,
            self.__issues
            )
        cPickle.dump(persistent, pickle_file)
        pickle_file.close()


    def __GetPicklePath(self):
        """Return the full path to the IDB pickle file."""
        
        return os.path.join(self.path, "idb.pickle")



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
