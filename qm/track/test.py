########################################################################
#
# File:   test.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   Tests for module qm.track.
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

import os
import os.path
import qm.regression_test 
from   qm.track import *
import qm.track.gadfly_idb
import qm.track.memory_idb
import sys

########################################################################
# tests
########################################################################

def test_issue_class_name():
    """Test the initialization and retrieval of issue class names."""

    name = "test_class"
    c = IssueClass(name)
    return c.GetName() == name


def test_mandatory_fields_1():
    """Test the creation of mandatory fields."""

    c = IssueClass("test_class")
    mandatory_fields = ("iid", "revision", "user", "timestamp", "summary",
                        "categories", "parents", "children", "state")
    for field in mandatory_fields:
        if not c.HasField(field):
            return 0
    return 1


def test_set_field_1():
    # IssueFieldSet should throw a TypeError if its argument isn't a
    # field.
    try:
        set = IssueFieldSet(0)
        return 0
    except TypeError:
        return 1
    

def test_set_field_2():
    # IssueFieldSet should throw a ValueError if its argument isn't a
    # field.
    try:
        contents = IssueFieldSet(IssueFieldInteger("test_int"))
        set = IssueFieldSet(contents)
        return 0
    except ValueError:
        return 1


def test_set_field_3():
    # The name of a set field is the name of the contained field.
    name = "test_field"
    contents = IssueFieldInteger(name)
    set = IssueFieldSet(contents)
    return set.GetName() == name


def test_mandatory_fields_2():
    iid = "test_iid"
    test_class = IssueClass("test_class")
    issue = Issue(test_class, iid)
    if issue.GetId() != iid or issue.GetField("iid") != iid:
        return 0
    if issue.GetRevision() != 0:
        return 0
    if issue.GetField("summary") != '':
        return 0
    return 1


def test_set_field_4():
    field_name = "test_field"
    issue_class = IssueClass("test_class")
    text_field = IssueFieldText(field_name)
    issue_class.AddField(IssueFieldSet(text_field))
    issue = Issue(issue_class, "i0")
    issue.SetField(field_name, [ "hello", "world", 42 ])
    return issue.GetField(field_name) == [ "hello", "world", "42" ]


def test_enumeration_field_1():
    field_name = "test_field"
    enum = { "small" : 1, "medium" : 10, "large" : 100 }
    issue_class = IssueClass("test_class")
    field = IssueFieldEnumeration(field_name, enum)
    field.SetDefaultValue("medium")
    issue_class.AddField(field)
    issue = Issue(issue_class, "i0")
    if issue.GetField(field_name) != 10:
        return 0
    issue.SetField(field_name, "small")
    if issue.GetField(field_name) != 1:
        return 0
    issue.SetField(field_name, 100)
    if issue.GetField(field_name) != 100:
        return 0
    return 1


def test_time_field_1():
    field_name = "test_field"
    issue_class = IssueClass("test_class")
    issue_class.AddField(IssueFieldTime(field_name))
    issue = Issue(issue_class, "i0")
    issue.SetField(field_name, "2000-12-22 12:00")
    if issue.GetField(field_name) != "2000-12-22 12:00":
        return 0
    return 1
    

def test_time_field_2():
    field_name = "test_field"
    issue_class = IssueClass("test_class")
    issue_class.AddField(IssueFieldTime(field_name))
    issue = Issue(issue_class, "i0")
    # An exception should be raised if we try to set the field value
    # to something that doesn't look like a time.
    try:
        issue.SetField(field_name, "not a valid time")
        return 0
    except ValueError:
        return 1


idb_path = "./test_idb"

def test_create_idb():
    # Blow away an old database, if it exists.
    if os.path.isdir(idb_path):
        os.system("rm -r %s" % idb_path) 
    # Create a new IDB.
    idb_impl(idb_path, create_idb=1)
    # There should be something there.
    return os.path.isdir(idb_path)


def test_add_issue_class():
    log_file = open("test.py.sqllog", "wt")
    idb = idb_impl(idb_path, log_file)
    icl = qm.track.IssueClass("test_class")
    icl.AddField(IssueFieldInteger("a_number", 14))
    field = IssueFieldInteger("int_set")
    icl.AddField(IssueFieldSet(field))
    idb.AddIssueClass(icl)
    if idb.GetIssueClass("test_class") == None:
        return 0
    return 1
    

def test_add_issues():
    idb = idb_impl(idb_path)
    icl = idb.GetIssueClass("test_class")

    i = qm.track.Issue(icl, "iss_0")
    i.SetField("summary", "An issue.")
    i.SetField("a_number", 72)
    idb.AddIssue(i)
    
    i = qm.track.Issue(icl, "iss_1")
    i.SetField("summary", "Another issue.")
    i.SetField("int_set", [5, 15, 25])
    idb.AddIssue(i)
    
    i = qm.track.Issue(icl, "iss_2")
    i.SetField("summary", "The third issue.")
    i.SetField("a_number", -15)
    i.SetField("int_set", [10, 20, 30])
    idb.AddIssue(i)

    i.SetField("a_number", -16)
    i.SetField("int_set", [10, 30])
    idb.AddRevision(i)

    return 1


def test_get_issues():
    idb = idb_impl(idb_path)
    i = idb.GetIssue("iss_1")
    if i.GetField("a_number") != 14:
        return 0
    if i.GetField("summary") != "Another issue.":
        return 0

    # Get the current revision of iss_2.
    i = idb.GetIssue("iss_2")
    if i.GetField("a_number") != -16:
        return 0
    if i.GetField("summary") != "The third issue.":
        return 0
    if i.GetField("int_set") != [10, 30]:
        return 0

    # Retrieve a past revision of iss_2.
    i = idb.GetIssue("iss_2", revision=0)
    if i.GetField("a_number") != -15:
        return 0

    if i.GetField("summary") != "The third issue.":
        return 0
    if i.GetField("int_set") != [10, 20, 30]:
        return 0

    all_revisions = idb.GetAllRevisions("iss_2")
    if len(all_revisions) != 2:
        return 0

    return 1


def test_attachments():
    idb = idb_impl(idb_path)
    icl = qm.track.IssueClass("test_class2")
    icl.AddField(IssueFieldAttachment("attachment"))
    idb.AddIssueClass(icl)
    i = qm.track.Issue(icl, "iss_5")
    idb.AddIssue(i)
    i = idb.GetIssue("iss_5")
    if i.GetField("attachment") != None:
        return 0
    return 1


class TestPreupdateTrigger(qm.track.Trigger):
    """Trigger implementation for testing preupdate triggers.

    Rejects issues whose iids start with the letter x."""

    def __init__(self):
        qm.track.Trigger.__init__(self, "test preupdate trigger")


    def __call__(self, issue, previous_issue):
        if issue.GetId()[0] == 'x':
            return qm.track.TriggerOutcome(self, 0,
                                           "issue ID may not start with x")
        else:
            return qm.track.TriggerOutcome(self, 1)



def test_preupdate_trigger():
    """Test preupdate triggers.

    Register an instance of 'TestPreupdateTrigger'.  Test that an issue
    may not be added with the iid "xxx", but that "www" and "yyy" are
    accepted."""

    idb = idb_impl(idb_path)
    idb.RegisterTrigger("preupdate", TestPreupdateTrigger())
    icl = idb.GetIssueClass("test_class")
    # Should be able to add an issue with iid "www".
    if not idb.AddIssue(qm.track.Issue(icl, "www")):
        return 0
    # Should not be able to add an issue with iid "xxx".
    if idb.AddIssue(qm.track.Issue(icl, "xxx")):
        return 0
    # Should be able to add an issue with iid "yyy".
    if not idb.AddIssue(qm.track.Issue(icl, "yyy")):
        return 0
    # The issue "www" should have been added successfully.
    try:
        idb.GetIssue("www", issue_class=icl)
    except KeyError:
        return 0
    # The issue "xxx" should not have been added.
    try:
        idb.GetIssue("xxx", issue_class=icl)
        return 0
    except KeyError:
        pass
    # The issue "yyy" should have been added successfully.
    try:
        idb.GetIssue("yyy", issue_class=icl)
    except KeyError:
        return 0
    # All done.
    return 1


class TestGetTrigger(qm.track.Trigger):
    """Trigger implementation for testing get triggers.

    Rejects issues with the iid "www"."""

    def __init__(self):
        qm.track.Trigger.__init__(self, "test get trigger")


    def __call__(self, issue, previous_issue):
        assert previous_issue == None
        iid = issue.GetId()
        return qm.track.TriggerOutcome(self, iid != "www")



def test_get_trigger():
    """Test get triggers.

    Register an instance of 'TestGetTrigger'.  Test that the issue
    with iid "www" is accessible before, and no longer accessible
    afterwards.  Test that another issue is accessible afterwards."""

    idb = idb_impl(idb_path)
    # The issue "www" should be accessible.
    try:
        idb.GetIssue("www")
    except KeyError:
        return 0
    idb.RegisterTrigger("get", TestGetTrigger())
    # The issue "www" should no longer be accessible.
    try:
        idb.GetIssue("www")
        return 0
    except KeyError:
        pass
    # The issue "yyy" should still be accessible.
    try:
        idb.GetIssue("yyy")
    except KeyError:
        return 0
    # All done.
    return 1


class TestPostupdateTrigger(qm.track.Trigger):
    """Trigger implementation for testing postupdate triggers.

    Stores away the most recent summary for each iid it has seen."""

    def __init__(self):
        qm.track.Trigger.__init__(self, "test postupdate trigger")
        self.summary_map = {}


    def __call__(self, issue, previous_issue):
        assert (previous_issue == None and issue.GetRevision() == 0) \
               or (issue.GetRevision() == previous_issue.GetRevision() + 1)
        summary = issue.GetField("summary")
        self.summary_map[issue.GetId()] = summary



def test_postupdate_trigger():
    """Test postupdate triggers.

    Register an instance of 'TestPostupdateTrigger'.  Add a few issue
    revisions, and make sure the trigger was called."""

    idb = idb_impl(idb_path)
    # Create and register the trigger.
    trigger = TestPostupdateTrigger()
    idb.RegisterTrigger("postupdate", trigger)
    # Add a new issue.
    icl = idb.GetIssueClass("test_class")
    issue = qm.track.Issue(icl, "tpt1")
    issue.SetField("summary", "value 1")
    idb.AddIssue(issue)
    # Add another revision of it.
    issue.SetField("summary", "value 2")
    idb.AddRevision(issue)
    # And another new issue.
    issue = qm.track.Issue(icl, "tpt2")
    issue.SetField("summary", "value 3")
    idb.AddIssue(issue)
    # Make sure the revision numbers were recorded when the trigger
    # was called.
    try:
        if trigger.summary_map["tpt1"] != "value 2":
            return 0
        if trigger.summary_map["tpt2"] != "value 3":
            return 0
    except KeyError:
        return 0
    # All done.
    return 1


regression_tests = [
    test_enumeration_field_1,
    test_issue_class_name,
    test_mandatory_fields_1,
    test_mandatory_fields_2,
    test_set_field_1,
    test_set_field_2,
    test_set_field_3,
    test_set_field_4,
    test_time_field_1,
    test_time_field_2,

    # The next several test are interrelated, and their order must be
    # preserved.
    test_create_idb,
    test_add_issue_class,
    test_add_issues,
    test_get_issues,
    test_attachments,
    test_preupdate_trigger,
    test_get_trigger,
    test_postupdate_trigger,
    ]


if __name__ == "__main__":
    failures = 0

    print "testing memory IDB"
    idb_impl = qm.track.memory_idb.MemoryIdb
    failures = failures + qm.regression_test.\
               run_regression_test_driver(regression_tests)

    print "\ntesting Gadfly IDB"
    idb_impl = qm.track.gadfly_idb.GadflyIdb
    failures = failures + qm.regression_test.\
               run_regression_test_driver(regression_tests)

    sys.exit(failures)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
