########################################################################
#
# File:   test.py
# Author: Alex Samuel
# Date:   2000-12-23
#
# Contents:
#   Tests for module qm.
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

import qm
import qm.regression_test
import qm.command_line
import string

########################################################################
# tests
########################################################################

def test_is_valid_label():
    return qm.is_valid_label("abcde") \
           and qm.is_valid_label("ab_xz_efg_0912_bjd__f_") \
           and qm.is_valid_label("_foo_bar", user=0) \
           and not qm.is_valid_label("_foo_bar") \
           and not qm.is_valid_label("") \
           and not qm.is_valid_label("Hello") \
           and not qm.is_valid_label("hello world")


def test_thunk_to_label():
    return qm.is_valid_label(qm.thunk_to_label("")) \
           and qm.is_valid_label(qm.thunk_to_label("abcyz_12390_")) \
           and qm.is_valid_label(qm.thunk_to_label("   abc 123   ")) \
           and qm.is_valid_label(qm.thunk_to_label("hello world!")) \
           and qm.is_valid_label(qm.thunk_to_label("(*@KAJD)92809  kj!")) \
           and qm.is_valid_label(qm.thunk_to_label("____foo bar____")) \
           and qm.is_valid_label(qm.thunk_to_label("This is a test."))


def test_parser_create():
    """Tests the creation of a CommandParser object.

    This will test the creation of a CommandParser by building a
    data structure of various flags and commands and calling the
    constructor CommandParser. It will only fail if that constructor
    raises an exception."""
    
    global my_parser
    name = 'qmtrack'
    option_a = ('a', 'a_option', None, 'Option A Description')
    option_b = ('b', 'b_option', 'foo', 'Option B Description')
    option_c = ('c', 'c_option', None, 'Option C Description')
    option_d = ('d', 'd_option', None, 'Option D Description')
    option_e = ('e', 'e_option', None, 'Option E Description')
    option_f = ('f', 'f_option', None, 'Option F Description')    
    command_1 = ('create', 'Create an issue', 'name',
                 "This command will create an issue. _name_ is the"
                 " name of the issue to be created.",
                 [option_d])
    command_2 = ('edit', 'Edit an issue', 'issue field1=foo field2+=bar',
                 "This command will edit an issue. _issue_ is the"
                 " name of the issue to be edited. field1, field2,..."
                 " are the fields to be edited.",
                 [option_e])
    command_3 = ('join', 'Join two issues', 'issue1 issue2',
                 "This command will join two issues. _issue1_ and"
                 " _issue2_ are the two issues to be joined.",
                 [option_f])

    options = [ option_a, option_b, option_c ]
    commands = [ command_1, command_2, command_3 ]

    my_parser = qm.command_line.CommandParser(name, options, commands)

    return 1


def test_parser_parse():
    """Tests the parsing of the command line.

    This will test the functionality of the parser by feeding it a command
    line and verifying that the results that it returns are correct. It
    will fail if either the return is incorrect or if the parser raises an
    exception."""

    command_line = '-b foo --a_option edit --e_option issue1 issue2'
    command_line = string.split(command_line)

    parsed_line = my_parser.ParseCommandLine(command_line)

    if parsed_line[0][0][0] != 'b_option':
        return 0
    if parsed_line[0][0][1] != 'foo':
        return 0
    if parsed_line[0][1][0] != 'a_option':
        return 0
    if parsed_line[0][1][1] != '':
        return 0
    if parsed_line[1] != 'edit':
        return 0;
    if parsed_line[2][0][0] != 'e_option':
        return 0;
    if parsed_line[2][0][1] != '':
        return 0;
    if parsed_line[3][0] != 'issue1':
        return 0;
    if parsed_line[3][1] != 'issue2':
        return 0;
    return 1


def test_parser_help():
    """Tests the help generation functionality of the parser.

    These tests will only fail if the parser functions to generate help
    raise an exception while building the strings to return."""
    
    my_parser.GetBasicHelp()
    my_parser.GetCommandHelp("create")
    my_parser.GetCommandHelp("edit")
    my_parser.GetCommandHelp("join")
    return 1


def test_parser_duplicate_long():
    """Test to verify that dupicate long options are not allowed."""
    
    name = 'qmtrack'
    option_a = ('a', 'a_option', None, 'Option A Description')
    option_b = ('b', 'a_option', None, 'Option A Description')
    option_c = ('a', 'c_option', None, 'Option A Description')    

    try:
        qm.command_line.CommandParser('qmtrack', [option_a, option_b], [])
        return 0
    except ValueError, msg:
        if str(msg) != "Duplicate long option":
            return 0
        return 1

    return 0


def test_parser_duplicate_short():
    """Test to verify that dupicate short options are not allowed."""
    
    name = 'qmtrack'
    option_a = ('a', 'a_option', None, 'Option A Description')
    option_b = ('b', 'a_option', None, 'Option A Description')
    option_c = ('a', 'c_option', None, 'Option A Description')    

    try:
        qm.command_line.CommandParser('qmtrack', [option_a, option_c], [])
        return 0
    except ValueError, msg:
        if str(msg) != "Duplicate short option":
            return 0
        return 1

    return 0


def test_parser_two_char_short():
    """Test to verify that only 1 character short options are allowed."""
    
    name = 'qmtrack'
    option_a = ('aa', 'a_option', None, 'Option A Description')

    try:
        qm.command_line.CommandParser('qmtrack', [option_a], [])
        return 0
    except ValueError, msg:
        if str(msg) != "Short option must have exactly 1 character":
            return 0
        return 1

    return 0


def test_parser_no_long():
    """Test to verify that long option format is required."""
    
    name = 'qmtrack'
    option_a = ('a', '', None, 'Option A Description')

    try:
        qm.command_line.CommandParser('qmtrack', [option_a], [])
        return 0
    except ValueError, msg:
        if str(msg) != "Long option must be specified":
            return 0
        return 1

    return 0


def test_parser_dup_command_short():
    """Test to verify the short dup. command is not allowed in a command"""
    
    option_d = ('d', 'd_option', None, 'Option D Description')
    option_e = ('d', 'e_option', None, 'Option E Description')
    command_1 = ('create', 'Create an issue', 'name',
                 "This command will create an issue. _name_ is the"
                 " name of the issue to be created.",
                 [option_d, option_e])
    try:
        qm.command_line.CommandParser('qmtrack', [], [command_1])
        return 0
    except ValueError, msg:
        if str(msg) != "Duplicate short command option":
            return 0
        return 1

    return 0


def test_parser_dup_command_long():
    """Test to verify the long dup. option is not allowed in a command."""
    
    option_d = ('d', 'd_option', None, 'Option D Description')
    option_e = ('e', 'd_option', None, 'Option E Description')
    command_1 = ('create', 'Create an issue', 'name',
                 "This command will create an issue. _name_ is the"
                 " name of the issue to be created.",
                 [option_d, option_e])
    try:
        qm.command_line.CommandParser('qmtrack', [], [command_1])
        return 0
    except ValueError, msg:
        if str(msg) != "Duplicate long command option":
            return 0
        return 1

    return 0

regression_tests = [
    test_is_valid_label,
    test_thunk_to_label,
    test_parser_create,
    test_parser_parse,
    test_parser_help,
    test_parser_duplicate_long,
    test_parser_duplicate_short,
    test_parser_two_char_short,
    test_parser_no_long,
    test_parser_dup_command_short,
    test_parser_dup_command_long
    ]


if __name__ == "__main__":
    qm.regression_test.run_regression_test_driver(regression_tests)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
