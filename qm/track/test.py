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

import qm.regression_test 
from qm.track import *

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
    fields = c.GetFields()
    for field in mandatory_fields:
        if not fields.has_key(field):
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
    issue_class.AddField(IssueFieldSet(text_field, []))
    issue = Issue(issue_class, "i0")
    issue.SetField(field_name, [ "hello", "world", 42 ])
    return issue.GetField(field_name) == [ "hello", "world", "42" ]


def test_enumeration_field_1():
    field_name = "test_field"
    enum = { "small" : 1, "medium" : 10, "large" : 100 }
    issue_class = IssueClass("test_class")
    issue_class.AddField(IssueFieldEnumeration(field_name, enum, "medium"))
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
    issue_class.AddField(IssueFieldTime(field_name,
                                        IssueFieldTime.current_time))
    issue = Issue(issue_class, "i0")
    issue.SetField(field_name, "2000-12-22 12:00")
    if issue.GetField(field_name) != "2000-12-22 12:00":
        return 0
    return 1
    

def test_time_field_2():
    field_name = "test_field"
    issue_class = IssueClass("test_class")
    issue_class.AddField(IssueFieldTime(field_name,
                                        IssueFieldTime.current_time))
    issue = Issue(issue_class, "i0")
    # An exception should be raised if we try to set the field value
    # to something that doesn't look like a time.
    try:
        issue.SetField(field_name, "not a valid time")
        return 0
    except ValueError:
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
    ]


if __name__ == "__main__":
    qm.regression_test.run_regression_test_driver(regression_tests)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
