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
import os
import os.path
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


    def __init__(self, path, create_idb=0):
        """Create a new IDB "connection".

        'path' -- The path to the persistent IDB.

        'create_idb' -- If true, creates a new IDB from scratch at the
        specified path.  Otherwise, loads in an existing IDB."""

        # Perform base class initialization.
        qm.track.IdbBase.__init__(self)
        # Store away the path.
        self.path = path
        # If this is a new IDB, create the directory to contain it.
        if create_idb and not os.path.isdir(path):
            os.mkdir(path)

        # Create a lock, and lock immediately.
        lock_path = os.path.join(path, "lock")
        self.lock = qm.FileSystemMutex(lock_path)
        self.lock.Lock()

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
        

    def __del__(self):
        """Close an IDB connection and write out the IDB state."""
        
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

        # Unlock the IDB.
        self.lock.Unlock()


    def __GetPicklePath(self):
        """Return the full path to the IDB pickle file."""
        
        return os.path.join(self.path, "idb.pickle")


    def GetIssueClass(self, name):
        """Return the issue class named by 'name'."""

        return self.__issue_classes[name]
        

    def AddIssueClass(self, issue_class):
        """Add 'issue_class' to the IDB.

        raises -- 'RuntimeError' if there is already a class in the
        IDB with the same name as the name of 'issue_class'."""

        name = issue_class.GetName()
        if self.__issue_classes.has_key(name):
            raise RuntimeError, "issue class name %s already exists" % name

        self.__issue_classes[name] = issue_class


    def AddIssue(self, issue):
        """Add a new issue record to the database.

        'issue' -- The new issue.  The revision number is ignored and
        set to zero.

        precondition -- The issue class of 'issue' must occur in this
        IDB, and fields of 'issue' must match the class's.

        returns -- A true value if the insert succeeded, or a false
        value if it was vetoed by a trigger."""

        # Copy the issue, since we'll be holding onto it.
        issue = issue.Copy()
        # Make sure the issue is in a class known to this IDB.
        issue_class = issue.GetClass()
        issue_class_name = issue_class.GetName()
        if not self.__issue_classes.has_key(issue_class_name) or \
           self.__issue_classes[issue_class_name] != issue_class:
            raise ValueError, "new issue in a class not in this IDB"
        # Make sure the iid is unique.
        iid = issue.GetId()
        if self.__issues.has_key(iid):
            raise ValueError, "iid is already used"
        # Set the initial revision number to zero.
        issue.SetField("revision", 0)
        # Store the new issue.
        return self.__InsertIssue(issue)


    def AddRevision(self, issue):
        """Add a revision of an existing issue to the database.

        'issue' -- A new revision of an existing issue.  The revision
        number is ignored and replaced with the next consecutive one
        for the issue.

        returns -- A true value if the insert succeeded, or a false
        value if it was vetoed by a trigger."""

        # Copy the issue, since we'll be holding onto it.
        issue = issue.Copy()
        # Retrieve the current list of revisions of the issue.
        iid = issue.GetId()
        revisions = self.__issues[iid]
        # Make sure the new revision is in the same issue class.
        if issue.GetClass() != revisions[0].GetClass():
            raise ValueError, "revision in different issue class"
        # Assign the next revision number.
        next_revision = len(revisions)
        issue.SetField("revision", next_revision)
        # Store the new revision.
        return self.__InsertIssue(issue)


    def GetIssueClasses(self):
        """Return a sequence of issue classes in this IDB."""

        return self.__issue_classes.values()


    def GetIssues(self):
        """Return a list of all the issues.

        This function is a hack to test the querying.  We want something
        better for sure in the future.  Created by Benjamin Chelf.
        FOR INTERNAL USE ONLY.

        'returns' -- This function returns a list of all the issues in the
        database."""

        return self.__issues.values()

    
    def GetIssue(self, iid, revision=None, issue_class=None):
        """Return the current revision of issue 'iid'.

        'revision' -- The revision number to retrieve.  If 'None', the
        current revision is returned.

        'issue_class' -- If 'None', all issue classes are searched for
        'iid'.  If an issue class name or 'IssueClass' instance are
        given, only that issue class is used.

        raises -- 'KeyError' if an issue with 'iid' cannot be found."""

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
        if revision == None:
            # The current revision was requested; it's at the end of
            # the list.
            issue = revisions[-1]
        else:
            # Index into the list to retrieve the requested revision.
            issue = revisions[revision]

        # Found an issue.  Inoke get triggers.
        result, outcomes = self._IdbBase__InvokeGetTriggers(issue)
        # Did the trigger veto the get?
        if not result:
            # The trigger vetoed the retrieval, so behave as if the
            # issue was nout found.
            raise KeyError, "no revision with IID '%s' found" % iid
        # FIXME: Do something with outcomes.
        # All done.
        return issue


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
            result, outcomes = self._IdbBase__InvokeGetTriggers(issue)
            # Keep the revision only if the trigger passed it.
            if result:
                issues.append(issue)
            # FIXME: Do something with outcomes.
        # Return the full list of revisions.
        return issues


    def GetCurrentRevisionNumber(self, iid):
        """Return the current revision number for issue 'iid'."""

        # Retrieve the list of revisions of this issue.
        revisions = self.__issues[iid]
        # The current revision number is the revision number of the
        # last (most recent) revision.
        return revisions[-1].GetRevision()


    def Query(self, query_record, current_revision_only=1):
        """Return a sequence of issues matching 'query_record'.

        'query_record' -- An instance of IssueRecord specifying the query.

        'current_revision_only -- If true, don't match revisions other
        than the current revision of each issue."""

        raise NotImplementedError


    # Helper functions.
    
    def __InsertIssue(self, issue):
        """Insert an issue record into the database.

        'issue' -- An 'Issue' instance, either for a new issue or for
        a new revision of an existing issue.

        returns -- A true value if the insert succeded, or a false
        value if a preupdate trigger vetoed the isertion."""

        iid = issue.GetId()
        if self.__issues.has_key(iid):
            revisions = self.__issues[iid]
            previous_issue = revisions[-1]
        else:
            revisions = None
            previous_issue = None

        # Invoke preupdate triggers.
        result, outcomes = \
                self._IdbBase__InvokePreupdateTriggers(issue, previous_issue)
        # FIXME: Do something with outcomes.
        # Did a trigger veto the update?
        if not result:
            return 0

        if revisions != None:
            # This is not the first revision of the issue.  Append
            # this new revision to the end.
            revisions.append(issue)
        else:
            # This is the first revision of the issue.  Create a new
            # list of revisions.
            self.__issues[iid] = [issue]

        # Invoke postupdate triggers.
        outcomes = self._IdbBase__InvokePostupdateTriggers(issue,
                                                           previous_issue)
        # FIXME: Do something with outcomes.
        return 1



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
