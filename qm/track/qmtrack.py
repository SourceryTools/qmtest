########################################################################
#
# File:   qmtrack.py
# Author: Benjamin Chelf
# Date:   2001-01-17
#
# Contents:
#   This file contains the implmenation of the command-line version of
#   qmtrack.
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

########################################################################
# imports
########################################################################

import os
import os.path
import sys
import rexec
import qm
import qm.command_line
import string
from types import *
from   qm.track import *
import qm.track.gadfly_idb
import qm.track.memory_idb

########################################################################
# classes
########################################################################

class CommandLine:
    """Class for the command line version of qmtrack.

    This is used to issue commands to the database via command line. Since
    this class only takes a string as the command line, the other methods
    of modifying the database may go through this one if they wish."""

    name = "qmtrack"
    """The name of the application."""
    
    command = ""
    """The command line as given to us."""
    
    formats = ('none', 'iid', 'iid-single', 'summary', 'short',
               'long', 'full', 'xml')
    
    # The options and commands for qmtrack. To edit these, simply add
    # or remove one in this style, and then add or remove it from
    # the appropriate array directly below these definitions.
    format_option = ('f', 'format', 'type', 'Format for output')
    database_option = ('d', 'database', 'location', 'Database location')
    help_option = ('h', 'help', None, 'Help')
    class_option = ('c', 'class', 'class_name', 'Class for new issue')
    
    create_command = ('create', 'Create a new issue',
                      '-c classname field[=,+=]value...',
                      "This command will create an issue. The field/value"
                      " pairs indicate attributes for the given issue."
                      " You must specify the class for the field with the"
                      " class flag. You must also specify the mandatory"
                      " fields, 'id',"
                      " 'categories', and 'summary'.", [ help_option,
                                                         class_option ])
    edit_command = ('edit', 'Edit an issue', 'id field[=,+=,-=]value...',
                    "This command will edit an issue. The 'id' is the"
                    " issue's id. The field/value pairs represent the"
                    " fields you wish to edit. A new revision of the"
                    " issue will be created.", [ help_option ])
    split_command = ('split', 'Split an issue', 'id',
                     "This command will split a single issue into two"
                     " issues. The new issues will be the children of the"
                     " original issue and it will be their parent.",
                     [ help_option ])
    join_command = ('join', 'Join two issues', 'id1 id2',
                    "This command will join two issues into a single"
                    " issue. The resulting issue will be the child of"
                    " each of the original issues and they will be its"
                    " parent.", [ help_option ])
    query_command = ('query', 'Query the database', 'expression',
                     "This command will query the database to find all"
                     " issues that cause the given 'expression' to"
                     " evalute to true.", [ help_option ])
    
    qmtrack_options = [ format_option, database_option, help_option ]
    """All the command line options for qmtrack."""
    
    qmtrack_commands = [ create_command, edit_command, split_command,
                         join_command, query_command ]
    """All the commands for qmtrack."""

    # The following are the strings for all the warnings and errors
    # that can be encountered in this module.
    format_warn = 'Unknown format type, using default.'
    database_loc_error = 'Must specify database location.'
    database_exist_error = 'Database does not exist.'
    command_error = 'Must specify a command.'
    unrecognized_error = 'Unrecognized command.'
    field_exist_begin = 'No field of name "'
    field_exist_end = '" exists in the issue class.'
    field_set_use_equal_begin = 'Cannot use operator "=" on field "'
    field_set_use_equals_end = '" of set type.'
    field_set_use_plus_begin = 'Cannot use operators "+=" or "-=" on field "'
    field_set_use_plus_end = '" of non-set type.'
    create_class_error_syn = \
    'Must specify an issue class when creating an issue.'
    create_field_error_begin = 'Missing mandatory field(s) "'
    create_field_error_end = '" in create command.'
    create_class_error_sem = 'Given issue class does not exist.'
    create_issue_error = 'An issue with that iid already exists.'
    create_no_equals_error = 'Must specify a field and a value.'
    edit_issue_error_syn = 'Must specify an issue id to edit.'
    edit_issue_error_sem = 'Cannot find issue to edit in database.'
    split_issue_error_syn = 'Must specify an issue id to split.'
    split_issue_error_sem = 'Cannot find isue to split in database.'
    split_iid_error_sem = \
    'Split causes a iid conflict with another issue.'
    join_issue_error_syn = 'Must specify 2 issues to join.'
    join_issue_error_sem_begin = 'Cannot find issue "'
    join_issue_error_sem_end = '" to join in database.'
    join_iid_error_sem = 'Join causes an iid conflict with another issue.'
    query_invalid_id_begin = 'Unknown identifier "'
    query_invalid_id_end = '" in query string.'
    query_invalid_att_begin = 'Unknown attribute "'
    query_invalid_att_end = '" in query string.'
    query_exception = 'Exception occured while evaluating query string'
    unimplemented = 'Unimplemented feature.'
    
    def __init__(self, command, output):
        """Create a new command line.

        'command' -- The list representing the command (with options) to
        be parsed and then executed. This list contains not only the
        command and its options, but also the program options found before
        the command. It is usually sufficent to simply use sys.argv[1:]
        as the argument to this constructor.

        'output' -- The file descriptor (usually standard out) of the
        file to which the output should be directed. It should already
        be opened for writing."""

        self.command = command
        self.output = output
        self.results = []


    def __del__(self):
        """End the parsing."""

        if idb != None:
            self.idb.__del__

    
    def ParseFieldValuePairs(self, list):
        """Parse the field value pairs from a list of strings.

        On the command line, field/value pairs are given in the form:
        field=value, field+=value, or field-=value. This function splits
        up those fields and values and puts them in a hash. In the simple
        '=' case, the value is simply the only value for the field. For
        the '+=' case, the hash will contain a key with name,
        'fieldname+'. Conversely, in the '-=' case, the hash will contain
        a key with the name 'fieldname-'. This way, the caller must handle
        the separate cases for each set type field.

        'list' -- a list of strings of field=value pairs.

        returns -- a hash of field, value pairs with set types as
        described above."""

        hash = {}

        for pair in list:
            # Check to make sure there is an '=' in the pair.
            if string.find(pair, '=') == -1:
                self.parser.ErrorHandler(1, self.create_no_equals_error,
                                         1, 'create')
            # This will cause a problem if there is no = in there.
            name, value = string.split(pair, '=', 1)
            if value != '':
                # Last character is a +
                if string.rfind(name, '+') == len(name) - 1 or \
                   string.rfind(name, '-') == len(name) - 1:
                    # This hash hasn't been defined yet.
                    if not hash.has_key(name):
                        hash[name] = []
                        # Add the value to the list for this hash
                        hash[name].append(value)
                        # Regular field. Overwrite the value in the hash so
                        # the last value placed in it is the one to use.
                else:
                    hash[name] = value

        return hash
        
    
    def ParseCommand(self):
        """Parse the command.

        After this function is called, the command will be parsed. All
        exceptions from bad input will be caught.

        returns -- 0 on success, 1 on failure or if no command is
        to be executed (in the case of asking for help)."""

        self.parser = qm.command_line.CommandParser(self.name,
                                                    self.qmtrack_options,
                                                    self.qmtrack_commands,
                                                    self.output)
        self.parsed = self.parser.ParseCommandLine(self.command)

        # Failed. Unrecognized option or command option.
        if self.parsed == -1:
            return 1

        self.flags = self.parsed[0]
        self.command_name = self.parsed[1]
        self.command_flags = self.parsed[2]
        self.command_args = self.parsed[3]

        self.format_name = self.GetOption('format')
        if self.format_name[0] == 0:
            self.format_name = 'iid'
        else:
            self.format_name = self.format_name[1]

        found = 0
        for format in self.formats:
            if format == self.format_name:
                found = 1

        if found == 0:
            # Non-fatal, can use default. syntax
            self.parser.ErrorHandler(0, format_warn, 0, '')
            self.format_name = 'iid'
        
        if self.GetOption('help')[0] == 1:
            write(self.parser.GetBasicHelp(), self.output)
            sys.exit(0)

        return 0

    
    def OpenDatabase(self):
        """Open the database cooresponding to one for the command.

        This function prepares the database for editing by opening it.

        returns -- 0 on success, 1 on error."""

        # Right now, the only way to specify the database location is
        # on the command line, so we require that the database is given
        # there. Perhaps we will someday have a default location, an
        # installation location, or an .qmtrackrc file or all of the
        # above.
        database_location = self.GetOption(self.database_option[1])

        # Database location was not specified on the command line
        if database_location[0] == 0:
            # fatal syntax
            self.parser.ErrorHandler(1, self.database_loc_error, 1, '')
            return 1
        
        # Create a new idb_impl object. This will open the database.
        # XXX: We need a way of specifying what type of database we have.
        # Is this information that will be attainable for the db itself?
        if os.path.isdir(database_location[1]):
            self.idb = qm.track.memory_idb.MemoryIdb(database_location[1])
        # The database doesn't exist. We must create it. Print out
        # error.
        else:
            self.parser.ErrorHandler(1, self.database_exist_error, 0, '')
            return 1

            
        return 0


    def CheckFieldTypes(self, hash, issue_class):
        """Check that the field types are correctly used.

        This method checks that '+=' and '-=' are only used with set
        field classes and that '=' is not used on set field classes.

        'hash' -- a hash of the values passed in as returned by
        ParseFieldValuePairs.

        'issue_class' -- the class for this issue to do the checking.

        'returns' -- 0 on success, 1 on error."""

        set = 0
        for key, value in hash.items():
            if string.rfind(key, '+') == len(key) - 1:
                field_name = string.replace(key, '+', '')
                set = 1
            elif string.rfind(key, '-') == len(key) - 1:
                field_name = string.replace(key, '-', '')
                set = 1
            else:
                field_name = key

            # If there is no such field by the given name, that's an
            # error.
            if not issue_class.HasField(field_name):
                self.parser.ErrorHandler(1, self.field_exist_begin +
                                         field_name +
                                         self.field_exist_end, 0, '')
                return 1

            field = issue_class.GetField(field_name)
            if isinstance(field, qm.track.issue_class.IssueFieldSet):
                if set == 0:
                    self.parser.ErrorHandler(1,
                                             self.field_set_use_equals_begin +
                                             field_name +
                                             self.field_set_use_equals_end,
                                             0, '')
                    return 1
            else:
                if set == 1:
                    self.parser.ErrorHandler(1,
                                             self.field_set_use_plus_begin +
                                             field_name +
                                             self.field_set_use_plus_end,
                                             0, '')
                    return 1
            
        return 0
                    
        
    def PerformCreate(self):
        """Create an issue because the create command was given.

        returns -- 0 on success, 1 on error."""

        # Get the class of the issue from the command line.
        class_value = self.GetCommandOption('class')
        if class_value[0] == 0:
            self.parser.ErrorHandler(1, self.create_class_error_syn, 1,
                                     'create')
            return 1

        # Split arguments up into pairs.
        hash = self.ParseFieldValuePairs(self.command_args)

        # Catch the exception if the issue class doesn't exist
        try:
            icl = self.idb.GetIssueClass(class_value[1])
        except KeyError:
            # fatal semantic
            self.parser.ErrorHandler(1, self.create_class_error_sem, 0, '')
            return 1

        # Check for type errors in setting fields.
        if self.CheckFieldTypes(hash, icl) == 1:
            return 1

        # Check for mandatory fields
        mandatory_fields = []
        for field in icl.GetFields():
            # If a field in the issue class doesn't have a default value,
            # it is required that the user specify a value when creating
            # the issue.
            if not field.HasDefaultValue():
                mandatory_fields.append(field.GetName())

        missing = []
        for field in mandatory_fields:
            # The field could be a normal field or a set.
            if not hash.has_key(field) and not hash.has_key(field + '+'):
                missing.append[field]

        # Some mandatory fields were missing
        if missing != []:
            self.parser.ErrorHandler(1, self.create_field_error_begin +
                                     string.join(missing[0:], ',') +
                                     self.create_field_error_end, 0, '')
            return 1
        
        # Build the new issue based on the argument pairs.
        new_issue = qm.track.Issue(icl, hash['iid'])
        for key, value in hash.items():
            if key != 'iid':
                if string.rfind(key, '+') == len(key) - 1:
                    new_issue.SetField(string.replace(key, '+', ''), value)
                elif string.rfind(key, '-') != len(key) - 1:
                    new_issue.SetField(key, value)

        # Add the issue. Check to see if the issue already exists.
        # If so, report an error.
        try:
            self.idb.AddIssue(new_issue)
        except ValueError:
            # fatal semantic
            self.parser.ErrorHandler(1, self.create_issue_error, 0, '')
            return 1

        # Set the results field for later use.
        self.results = [ new_issue ]
        return 0


    def PerformEdit(self):
        """Edit an issue because the edit command was given.

        returns -- 0 on succes, 1 on error."""

        if len(self.command_args) == 0:
            self.parser.ErrorHandler(1, self.edit_issue_error_syn, 1,
                                     'edit')
            return 1
        
        iid = self.command_args[0]

        # Get the issue out of the database.
        try:
            issue = self.idb.GetIssue(iid)
        except KeyError:
            self.parser.ErrorHandler(1, self.edit_issue_error_sem, 0, '')
            return 1

        # Split arguments up into pairs.
        hash = self.ParseFieldValuePairs(self.command_args[1:])

        # Check for type errors in setting fields.
        if self.CheckFieldTypes(hash, issue.GetClass()) == 1:
            return 1
        
        # Set the fields in the issue according to their edited values.
        for key, value in hash.items():
            if key != 'iid':
                if string.rfind(key, '+') == len(key) - 1:
                    # For each item in the set, add it to the already
                    # existing list of items for that field.
                    field_name = string.replace(key, '+', '')
                    current_items = issue.GetField(field_name)
                    # Validate the value before we use it
                    value = \
                          issue.GetClass().GetField(field_name).Validate(value)
                    for item in value:
                        # Only add it if its not already in the list
                        if not item in current_items:
                            current_items.append(item)
                    issue.SetField(field_name, current_items)
                elif string.rfind(key, '-') == len(key) - 1:
                    # For each item in the set, remove it from the already
                    # existing list of items for that field. Warning,
                    # this part operates in n^2 time for the number
                    # of items in the field.
                    field_name = string.replace(key, '-', '')
                    current_items = issue.GetField(field_name)
                    # Validate the value before we use it
                    value = \
                          issue.GetClass().GetField(field_name).Validate(value)
                    for item in value:
                        new_items = []
                        for item2 in current_items:
                            if item != item2:
                                new_items.append(item2)
                        current_items = new_items
                    issue.SetField(field_name, current_items)
                else:
                    issue.SetField(key, value)                   

        self.idb.AddRevision(issue)
        self.results = [ issue ]
        return 0


    def PerformSplit(self):
        """Split one issue into two.

        returns -- 0 on succes, 1 on error."""

        if len(self.command_args) == 0:
            self.parser.ErrorHandler(1, self.split_issue_error_syn, 1,
                                     'split')
            return 1
        
        iid = self.command_args[0]

        # Get the issue out of the database.
        try:
            issue = self.idb.GetIssue(iid)
        except KeyError:
            # fatal semantic
            self.parser.ErrorHandler(1, self.split_issue_error_sem, 0, '')
            return 1

        # Copy the original issue
        issue1 = issue.Copy()
        issue2 = issue.Copy()

        # Set the parents and children
        issue1.SetField('parents', [ issue ])
        issue2.SetField('parents', [ issue ])
        issue.SetField('children', [ issue1, issue2 ])

        # Set the ids of the new children
        issue1.SetField('iid', issue.GetField('iid') + ".1")
        issue2.SetField('iid', issue.GetField('iid') + ".2")        

        # Add the new issues. Check to see if the issue names already exist.
        # If so, report an error.
        try:
            self.idb.AddIssue(issue1)
            self.idb.AddIssue(issue2)
        except ValueError:
            # fatal semantic
            self.parser.ErrorHandler(1, self.split_iid_error_sem, 0, '')
            return 1

        # Set the results for future use
        self.results = [ issue1, issue2 ]
        
        return 0


    def PerformJoin(self):
        """Join two issues into a single one.

        returns -- 0 on succes, 1 on error."""

        if len(self.command_args) != 2:
            # fatal syntax
            self.parser.ErrorHandler(1, self.join_issue_error_syn, 1,
                                     'join')
            return 1
        
        iid1 = self.command_args[0]
        iid2 = self.command_args[1]

        # Get the issues out of the database.
        try:
            issue1 = self.idb.GetIssue(iid1)
        except KeyError:
            # fatal semantic
            self.parser.ErrorHandler(1,
                                     self.join_issue_error_sem_begin +
                                     iid1 +
                                     self.join_issue_error_sem_end, 0, '')
            return 1
        try:
            issue2 = self.idb.GetIssue(iid2)
        except KeyError:
            # fatal semantic
            self.parser.ErrorHandler(1,
                                     self.join_issue_error_sem_begin +
                                     iid2 +
                                     self.join_issue_error_sem_end, 0, '')
            return 1

        # How are we supposed to map over all the fields to combine
        # the two issues? For enumerals, do we want intersection or union?
        # We should probably think about this more. For now, this function
        # will only copy the first issue, give it a new name, and set the
        # parents/children correctly.
        new_issue = issue1.Copy()
        new_issue.SetField('iid', issue1.GetField('iid') + '.' +
                           issue2.GetField('iid'))
        new_issue.SetField('parents', [ issue1, issue2 ])
        issue1.SetField('children', [ new_issue ])
        issue2.SetField('children', [ new_issue ])

        # Add the new issue. Check to see if the issue names already exist.
        # If so, report an error.
        try:
            self.idb.AddIssue(new_issue)
        except ValueError:
            self.parser.ErrorHandler(1, self.join_iid_error_sem, 0, '')
            return 1

        # Set the results for future use
        self.results = [ new_issue ]
        
        return 0


    def PerformQuery(self):
        """Perform a query on the database.

        returns -- 0 on success, 1 on failure."""

        query_str = string.join(self.command_args[0:])

        self.results = [ ]
        for issue in self.idb.GetIssues():
            # We have a list of revisions; we want only the last one.
            issue = issue[len(issue) - 1]
            query_env = rexec.RExec()
            # Import string operations for them.
            query_env.r_exec("import string");
            c = issue.GetClass()
            # Set up the execution environment for the expression.
            for field in c.GetFields():
                field_name = field.GetName()
                # This sets each field to be its current value in the issue.
                field_value = issue.GetField(field_name)
                if type(field_value) == StringType:
                    field_value = "'" + field_value + "'"
                query_env.r_exec("%s = %s" % (field_name, field_value))
                # This is somewhat of a hack. We have to check to
                # see if this class is an enumeration. If it is,
                # grab the mapping and use that. Otherwise, it might
                # be a set of enumerations, in which case we need to
                # fish into the set to get the mapping of each thing
                # that could be in the set.
                enum = field.GetAttribute("enumeration", "")
                if enum == "":
                    try:
                        contained = field.GetContainedField()
                        enum = contained.GetAttribute("enumeration", "")
                        if enum != "":
                            enum = contained.GetEnumeration()
                    except:
                        enum = ""
                else:
                    enum = field.GetEnumeration()

                # This sets all the enumerals to be their value.
                if enum != "":
                    for key, value in enum.items():
                        query_env.r_exec("%s = %d" % (str(key), int(value)))

            # Execute the expression. If it's true, add this issue to
            # the results to be printed.
            try:
                if query_env.r_eval(query_str):
                    self.results.append(issue)
            except NameError, msg:
                self.parser.ErrorHandler(1, self.query_invalid_id_begin +
                                         str(msg) +
                                         self.query_invalid_id_end,
                                         0, '')
                return 0
            except AttributeError, msg:
                self.parser.ErrorHandler(1, self.query_invalid_att_begin +
                                         str(msg) +
                                         self.query_invalid_att_end,
                                         0, '')
                return 0
            except:
                self.parser.ErrorHandler(1, self.query_exception, 0, '')
                return
        
        self.output.write("Issues found: %d\n" % len(self.results))
        return 1
    
    
    def PerformCommand(self):
        """Perform the command given via the string to the constructor.

        This function performs the command given in the constructor. It
        does not return any of the information to be printed.

        returns -- 0 on success, 1 on error."""

        if self.command_name == 'create':
            return self.PerformCreate()    
        elif self.command_name == 'edit':
            return self.PerformEdit()
        elif self.command_name == 'join':
            return self.PerformJoin()
        elif self.command_name == 'split':
            return self.PerformSplit()
        elif self.command_name == 'query':
            return self.PerformQuery()
        # Did not specify a command
        elif self.command_name == '':
            self.parser.ErrorHandler(1, self.command_error, 1, '')
        # Specified a command that doesn't exist
        else:
            self.parser.ErrorHandler(1, self.unrecognized_error, 1, '')
            return 1
        
        return 0;


    def PrintResults(self):
        """Print the list of issues that are the results of the command.

        returns -- 0 on success, 1 on failure."""

        if self.format_name == 'none':
            return 0
        elif self.format_name == 'iid':
            for i in range(0, len(self.results) - 1):
                issue = self.results[i]
                self.output.write(issue.GetId() + ', ')
            self.output.write(self.results[len(self.results) - 1].GetId())
            self.output.write('\n');
        elif self.format_name == 'iid-single':
            for issue in self.results:
                self.output.write(issue.GetId() + '\n')
        elif self.format_name == 'summary':
            for issue in self.results:
                self.output.write('id: ' + issue.GetId() + '\n')
                self.output.write('summary:  ' + issue.GetField('summary'))
                self.output.write('\n\n')
        # Same as 'iid-single' for now
        elif self.format_name == 'short':
            for issue in self.results:
                self.output.write(issue.GetId() + '\n')
        # Same as 'summary' for now
        elif self.format_name == 'full':
            for issue in self.results:
                self.output.write('id: ' + issue.GetId() + '\n')
                self.output.write('summary:  ' + issue.GetField('summary'))
                self.output.write('\n\n')
        elif self.format_name == 'xml':
            self.output.write('Unimplemented output format.')
            return 1
        return 0


    def GetCommand(self):
        """Get the name of the command given.

        returns -- a string for the name of the given command."""

        return self.command_name


    def GetOptionHelper(self, long_name, option_list):
        """Helper for the GetOption and GetCommandOption defined below."""
        # Loop over the flags given to determine if the desired option
        # was given.
        for i in range(0, len(option_list)):
            flag = option_list[i]
            if flag[0] == long_name:
                return [1, flag[1]]

        return [0]

        
    def GetOption(self, long_name):
        """Get the value of the given option.

        This method will retrieve whether or not an option was given. If
        it was given, the value passed to the option will also be
        returned. Note that this is the GetCommandOption which should be
        used for querying options to the given command.

        'long_name' -- The name of the desired option, in long form.

        returns -- a list of 1 or 2 items. The first item will be 0 if the
        option was not given, 1 if it was. If the option was given (value
        of 1), and the option has an argument, the second item in the list
        will be that argument."""

        return self.GetOptionHelper(long_name, self.flags)


    def GetCommandOption(self, long_name):
        """Get the value of the given command option.

        Same as GetOption but for the options to the qmtrack command
        instead of the options to the application.

        'long_name' -- The name of the desired option, in long form.

        returns -- a list of 1 or 2 items. The first item will be 0 if the
        option was not given, 1 if it was. If the option was given (value
        of 1), and the option has an argument, the second item in the list
        will be that argument."""

        return self.GetOptionHelper(long_name, self.command_flags)

        
########################################################################
# functions
########################################################################

if __name__ == "__main__":
    try:
        program = CommandLine(sys.argv[1:], sys.stdout)
        program.ParseCommand()
        program.OpenDatabase()
        program.PerformCommand()
        program.PrintResults()
    except ValueError:
        sys.exit(1)
    sys.exit(0)        
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
