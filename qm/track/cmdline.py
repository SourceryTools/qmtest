########################################################################
#
# File:   cmdline.py
# Author: Benjamin Chelf
# Date:   2001-01-17
#
# Contents:
#   QMTrack command processing.
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
import qm.track
import qm.cmdline
import string

########################################################################
# classes
########################################################################

class Command:
    """A QMTrack command.

    A 'Command' object parses, checks, and executes a command.  The
    class does not handle setup of the IDB itself; the caller is
    responsible for this."""

    name = "qmtrack"
    """The name of the application."""
    
    command = ""
    """The command line as given to us."""
    
    formats = (
        'none', 'iid', 'iid-single', 'summary', 'short', 'long',
        'full', 'xml'
        )

    # The following are the options and commands for qmtrack.  To edit
    # these, simply add or remove one in this style, and then add or
    # remove it from the appropriate array directly below these
    # definitions.
    format_option = ('f', 'format', 'type', 'Format for output')
    database_option = ('i', 'idb', 'path', 'Path to IDB')
    help_option = ('h', 'help', None, 'Help')
    class_option = ('c', 'class', 'class_name', 'Class for new issue')
    query_class_option = ('c', 'class', 'class_name',
                          'Class of issues to query')
    port_option = ('P', 'port', 'port', 'Server port number')
    log_file_option = (None, 'log-file', 'path', 'Log file name')
    idb_type_option = (None, 'idb-type', 'type', 'IDB type')
    test_values_option = (None, 'test-values', None,
                          'Populate IDB with values for testing')

    qmtrack_options = [ format_option, database_option, help_option ]
    """All the command line options for qmtrack."""
    
    qmtrack_commands = [

        ('create',
         'Create a new issue',
         '-c classname field[=,+=]value...',
         "This command will create an issue. The field/value pairs "
         "indicate attributes for the given issue. You must specify the "
         "class for the field with the" " class flag. You must also "
         "specify the mandatory fields, 'id', 'categories', and " 
         "'summary'.",
         [ help_option, class_option ]
         ),
        
        ('edit',
         'Edit an issue',
         'id field[=,+=,-=]value...',
         "This command will edit an issue. The 'id' is the issue's "
         "id. The field/value pairs represent the fields you wish to "
         "edit. A new revision of the issue will be created.",
         [ help_option ]
         ),
        
        ('split',
         'Split an issue',
         'id',
         "This command will split a single issue into two issues. The "
         "new issues will be the children of the original issue and it "
         "will be their parent.",
         [ help_option ]
         ),
        
        ('join',
         'Join two issues',
         'id1 id2',
         "This command will join two issues into a single issue. The "
         "resulting issue will be the child of each of the original "
         "issues and they will be its parent.",
         [ help_option ]
         ),

        ('query',
         'Query the database',
         'expression',
         "This command will query the database to find all issues for "
         "which the query expression evalutes to true.",
         [ help_option, query_class_option ]
         ),

        ('server',
         'Start the server',
         '',
         "This command starts the QMTrack server.  The server provides "
         "a web user interface and remote command access over HTTP.",
         [ help_option, port_option, log_file_option ]
         ),
    
        ('show',
         'Display an issue',
         'id',
         "This command displays a single issue.  This command is a "
         "shortcut for 'query iid==value'.",
         [ help_option ]
         ),

        ('initialize',
         'Initialize an IDB',
         'path',
         "This command initializes a new issue database (IDB).  Valid "
         "IDB types are 'MemoryIdb' and 'GadflyIdb'.",
         [ help_option, idb_type_option, test_values_option ],
        ),
        
    ]
    """All the commands for qmtrack."""

    # The following are the strings for all the warnings and errors
    # that can be encountered in this module.
    format_error = 'unknown format %s'
    command_error = 'no command specified'
    unrecognized_error = 'unrecognized command %s'
    field_exist = 'no field %s in issue class %s'
    field_set_use_equal = 'operator = not allowed for set field %s'
    field_set_use_plus = \
      'cannot use operators += or -= on non-set field %s'
    create_class_error_syn = 'create: no issue class specified'
    create_field_error = 'create: missing mandatory fields (%s)'
    create_class_error_sem = 'create: issue class %s does not exist'
    create_issue_error = 'create: iid %s already exists'
    create_no_equals_error = 'create: incorrect argument %s'
    edit_issue_error_syn = 'edit: no iid specified'
    edit_issue_error_sem = 'edit: iid %s not found'
    split_issue_error_syn = 'split: no iid specified'
    split_issue_error_sem = 'split: iid %s not found'
    split_iid_error_sem = 'split: iid %s already exists'
    join_issue_error_syn = 'join: fewer than two iids specified'
    join_issue_error_sem = 'join: iid %s not found'
    join_iid_error_sem = 'join: iid %s already exists'
    query_error_syn = 'query: no query specified'
    query_invalid_id = 'query: unknown name %s'
    query_invalid_att = 'query: unknown attribute %s'
    query_exception = 'query: an exception occured: %s: %s'
    show_wrong_args = 'show: no iid specified'
    show_no_iid = 'show: iid %s not found'
    initialize_invalid_idb_class = 'initialize: IDB type %s is invalid'
    initialize_wrong_flag = 'initialize: --idb option is not allowed'
    initialize_no_idb_path = 'initialize: missing IDB path'
    
    def __init__(self, argument_list):
        """Create a new command processor.

        'argument_list' -- This is a list representing the argument
        list (with options) to be parsed and then executed.  This list
        contains not only the command and its options, but also the
        program options found before the command.  It is usually
        sufficent to simply use sys.argv[1:] as the argument to this
        constructor."""

        self.__argument_list = argument_list

        # Build a map used to dispatch command names to handlers.
        self.__command_dispatch = {
            'create': self.__PerformCreate,
            'edit': self.__PerformEdit,
            'initialize': self.__PerformInitialize,
            'join': self.__PerformJoin,
            'query': self.__PerformQuery,
            'server' : self.__PerformServer,
            'show' : self.__PerformShow,
            'split': self.__PerformSplit,
            }

        self.__Parse()


    def GetCommand(self):
        """Get the name of the command given.

        returns -- This function returns a string for the name of the
        given command."""

        return self.__command_name


    def GetGlobalOptions(self):
        """Return a dictionary containing global options.

        returns -- A dictionary whose keys are the long names of
        global options that were specified on the command line.  For
        flags that take arguments, the corresponding value is the flag
        argument."""

        return self.__global_options


    def GetCommandOptions(self):
        """Return a dictionary containing command options.

        returns -- A dictionary whose keys are the long names of
        command options that were specified on the command line.  For
        flags that take arguments, the corresponding value is the flag
        argument."""

        return self.__command_options


    def RequiresIdb(self):
        """Return true if this command requires an IDB connection."""

        # If a help option was specified, we won't need the IDB.
        if self.GetGlobalOptions().has_key('help'):
            return 0
        if self.GetCommandOptions().has_key('help'):
            return 0
        # Some commands don't require an IDB connection.
        if self.GetCommand() in ('initialize', ):
            return 0
        # All other commands require an IDB.
        return 1


    def RequiresLocalIdb(self):
        """Return true if this command requires a local IDB connection."""

        # If it doesn't require an IDB at all, it can't possibly
        # require a local one.
        if not self.RequiresIdb():
            return 0
        # Do any commands require a local IDB?
        if self.GetCommand() == 'server':
            return 1
        # All other commands can be invoked remotely.
        return 0

        
    def Execute(self, output):
        """Execute the command."""

        # If the user specified the help command, print out the help
        # and exit.
        if self.GetGlobalOptions().has_key('help'):
            output.write(self.parser.GetBasicHelp())
            return

        # If the user asked for help for a specific command, print out
        # the help for that command and exit.
        if self.GetCommandOptions().has_key('help'):
            output.write(self.parser.GetCommandHelp(self.__command_name))
            return

        if self.__command_name == '':
            # The user did not specify a command so we report an error.
            raise qm.cmdline.CommandError, self.command_error
        else:
            # Look up a handler for the command.  The command parser
            # should already have flagged the case where the command
            # is unrecognized.
            assert self.__command_dispatch.has_key(self.__command_name)
            handler = self.__command_dispatch[self.__command_name]
            # Call the command handler function.
            handler(output)
        

    def __ParseFieldValuePairs(self, list):
        """Parse the field value pairs from a list of strings.

        On the command line, field/value pairs are given in the form:
        field=value, field+=value, or field-=value.  This function splits
        up those fields and values and puts them in a hash.  In the simple
        '=' case, the value is simply the only value for the field.  For
        the '+=' case, the hash will contain a key with name,
        'fieldname+'.  Conversely, in the '-=' case, the hash will contain
        a key with the name 'fieldname-'.  This way, the caller must
        handle the separate cases for each set type field.

        'list' -- This is a list of strings of field=value pairs.

        returns -- This is a hash of field/value pairs with set types as
        described above."""

        hash = {}

        for pair in list:
            # Check to make sure there is an '=' in the pair.
            if string.find(pair, '=') == -1:
                raise qm.cmdline.CommandError, \
                      self.create_no_equals_error % pair
            name, value = string.split(pair, '=', 1)
            if value != '':
                # If the last character is a '+' or a '-', we need
                # to the value differently than if we just have a '='
                # to assign a value to a field.
                if string.rfind(name, '+') == len(name) - 1 \
                   or string.rfind(name, '-') == len(name) - 1:
                    # This mapping has not been defined yet.  Define it.
                    if not hash.has_key(name):
                        hash[name] = []
                    # Add the value to the list of values for this hash.
                    hash[name].append(value)
                # In the case of a '=' assignment, overwrite the value
                # in the hash so the last value placed in it is the one
                # to use.
                else:
                    hash[name] = value

        return hash
        
    
    def __Parse(self):
        """Parse the command.

        After this function is called, the command will be parsed.  All
        exceptions from bad input will be caught.

        raises -- 'qm.cmdline.CommandError' if there is a command line
        error."""

        self.parser = qm.cmdline.CommandParser(self.name,
                                               self.qmtrack_options,
                                               self.qmtrack_commands)
        ( flags,
          self.__command_name,
          command_flags,
          self.__arguments
          ) = self.parser.ParseCommandLine(self.__argument_list)

        # For global flags, build a mapping from flag names to flag
        # arguments for flags that were specified.
        self.__global_options = {}
        for flag, flag_argument in flags:
            self.__global_options[flag] = flag_argument
        # Do the same for command flags.
        self.__command_options = {}
        for flag, flag_argument in command_flags:
            self.__command_options[flag] = flag_argument

        # Did the user specify a format style?
        if self.__global_options.has_key('format'):
            # Yes, use it.
            self.format_name = self.__global_options['format']
        else:
            # Choose a default, depending on the command.
            if self.__command_name in ("query", "show"):
                # For these commands, more thorough output makes sense
                # by default.
                self.format_name = "summary"
            else:
                # For other commands, just show the issue id.
                self.format_name = "iid"

        # Make sure the format is valid.
        if not self.format_name in self.formats:
            raise qm.cmdline.CommandError, \
                  self.format_error % self.format_name
        
    
    def __CheckFieldTypes(self, hash, issue_class):
        """Check that the field types are correctly used.

        This method checks that '+=' and '-=' are only used with fields of
        set type and that '=' is not used on fields of set type.

        'hash' -- This is a mapping of the values passed in as returned by
        ParseFieldValuePairs.

        'issue_class' -- This is the class for this issue to do the checking.
        """

        for key, value in hash.items():
            # First we set whether or not to the user used this type
            # as a set or not.  They used it as a set if they used the
            # '+=' or '-=' syntax.  The 'set' variable keeps track of
            # this.
            is_set_operation = 0
            if string.rfind(key, '+') == len(key) - 1:
                field_name = string.replace(key, '+', '')
                is_set_operation = 1
            elif string.rfind(key, '-') == len(key) - 1:
                field_name = string.replace(key, '-', '')
                is_set_operation = 1
            else:
                field_name = key

            # If there is no such field by the given name, we must
            # report the error.
            if not issue_class.HasField(field_name):
                raise qm.cmdline.CommandError, \
                      self.field_exist \
                      % (field_name, issue_class.GetName())

            # If the field does exist, get the field.
            field = issue_class.GetField(field_name)
            # If the field is of the set type, and they used the syntax
            # for a non-set type, report an error.
            if isinstance(field, qm.track.issue_class.IssueFieldSet):
                if not is_set_operation:
                    raise qm.cmdline.CommandError, \
                          self.field_set_use_equal % field_name
            # Conversely, if the field is of a non-set type, and they
            # used the syntax for a set type, report an error.
            else:
                if is_set_operation:
                    raise qm.cmdline.CommandError, \
                          self.field_set_use_plus % field_name
                    
        
    def __PerformCreate(self, output):
        """Create an issue because the create command was given."""

        # Get the class of the issue from the command line.
        try:
            issue_class_name = self.GetCommandOptions()['class']
        except KeyError:
            # The class was not specified.  Report an error.
            raise qm.cmdline.CommandError, self.create_class_error_syn

        # Split the 'field=value' arguments up into pairs.
        hash = self.__ParseFieldValuePairs(self.__arguments)

        # If the issue class they specified does not exist, catch the
        # exception and report an error.
        idb = qm.track.get_idb()
        try:
            icl = idb.GetIssueClass(issue_class_name)
        except KeyError:
            raise qm.cmdline.CommandError, \
                  self.create_class_error_sem % issue_class_name

        # Check that the user used the correct operator for the types of
        # fields that they specify.
        self.__CheckFieldTypes(hash, icl)

        # Check that the user gave values for all fiels that do not
        # have a default value and are, therefore, mandatory.
        mandatory_fields = []
        for field in icl.GetFields():
            # If a field in the issue class doesn't have a default value,
            # it is required that the user specify a value when creating
            # the issue.
            if not field.HasDefaultValue():
                mandatory_fields.append(field.GetName())

        missing = []
        for field in mandatory_fields:
            # The field could be a normal field or a set.  Notice that for
            # set fields, we only look for the '+' operator because a '-'
            # operator in a create will not do us much good for setting
            # a field with no default value.
            if not hash.has_key(field) and not hash.has_key(field + '+'):
                missing.append(field)

        # If some mandatory fields were missing, report an error.
        if missing != []:
            raise qm.cmdline.CommandError, \
                  self.create_field_error % string.join(missing, ',')
        
        # Once we have checked that everything is in order to create the
        # new issue, we build it based on the argument pairs.
        iid = hash['iid']
        new_issue = qm.track.Issue(icl, iid)
        for key, value in hash.items():
            if key != 'iid':
                try:
                    if string.rfind(key, '+') == len(key) - 1:
                        new_issue.SetField(string.replace(key, '+', ''), value)
                    elif string.rfind(key, '-') != len(key) - 1:
                        new_issue.SetField(key, value)
                except ValueError, msg:
                    raise qm.cmdline.CommandError, msg
            
        # Add the issue to the database.  Check to see if the issue
        # with that 'iid' already exists.  If so, report an error.
        try:
            idb.AddIssue(new_issue)
        except ValueError:
            raise qm.cmdline.CommandError, self.create_issue_error % iid

        self.__PrintResults(output, new_issue)


    def __PerformEdit(self, output):
        """Edit an issue because the edit command was given."""

        # If there are no command arguments to the command, they did
        # not specify a command to be edited and we report an error.
        if len(self.__arguments) == 0:
            raise qm.cmdline.CommandError, self.edit_issue_error_syn
        
        iid = self.__arguments[0]

        # Get the given issue out of the database.  If the issue is not
        # in the database, report an error.
        idb = qm.track.get_idb()
        try:
            issue = idb.GetIssue(iid)
        except KeyError:
            raise qm.cmdline.CommandError, self.edit_issue_error_sem % iid

        # Split arguments up into pairs.
        hash = self.__ParseFieldValuePairs(self.__arguments[1:])

        # Check that the user used the correct operator for the types of
        # fields that they specify.
        self.__CheckFieldTypes(hash, issue.GetClass())
        
        # Set the fields in the issue according to their edited values.
        for key, value in hash.items():
            if key != 'iid':
                if string.rfind(key, '+') == len(key) - 1:
                    # For each item in the set, add it to the already
                    # existing list of items for that field.
                    field_name = string.replace(key, '+', '')
                    current_items = issue.GetField(field_name)
                    # Validate the value before we use it.
                    value \
                    = issue.GetClass().GetField(field_name).Validate(value)
                    for item in value:
                        # Only add it if its not already in the list.
                        if not item in current_items:
                            current_items.append(item)
                    issue.SetField(field_name, current_items)
                elif string.rfind(key, '-') == len(key) - 1:
                    # For each item in the set, remove it from the already
                    # existing list of items for that field.  Warning,
                    # this part operates in n^2 time for the number
                    # of items in the field.
                    field_name = string.replace(key, '-', '')
                    current_items = issue.GetField(field_name)
                    # Validate the value before we use it.
                    value \
                    = issue.GetClass().GetField(field_name).Validate(value)
                    for item in value:
                        new_items = []
                        for item2 in current_items:
                            if item != item2:
                                new_items.append(item2)
                        current_items = new_items
                    issue.SetField(field_name, current_items)
                else:
                    issue.SetField(key, value)                   

        # Finally, add the new revision of the issue to the database.
        idb.AddRevision(issue)

        self.__PrintResults(output, issue)


    def __PerformSplit(self, output):
        """Split one issue into two."""

        # If there are no command arguments to the command, they did
        # not specify a command to be split and we report an error.
        if len(self.__arguments) == 0:
            raise qm.cmdline.CommandError, self.split_issue_error_syn
        
        iid = self.__arguments[0]

        # Get the issue out of the database.
        idb = qm.track.get_idb()
        try:
            issue = idb.GetIssue(iid)
        except KeyError:
            raise qm.cmdline.CommandError, self.split_issue_error_sem % iid

        # Copy the original issue.
        issue1 = issue.Copy()
        issue2 = issue.Copy()

        # Set the parents and children.
        issue1.SetField('parents', [ issue ])
        issue2.SetField('parents', [ issue ])
        issue.SetField('children', [ issue1, issue2 ])

        # Set the ids of the new children.
        issue1.SetField('iid', issue.GetField('iid') + ".1")
        issue2.SetField('iid', issue.GetField('iid') + ".2")        

        # Check to see if the issue names already exist.  If so,
        # report an error.
        try:
            idb.GetIssue(issue1.GetId())
            raise qm.cmdline.CommandError, \
                  self.split_iid_error_sem % issue1.GetId()
        except ValueError:
            # Couldn't find the issue; that's good.
            pass
        try:
            idb.GetIssue(issue2.GetId())
            raise qm.cmdline.CommandError, \
                  self.split_iid_error_sem % issue2.GetId()
        except ValueError:
            # Couldn't find the issue; that's good.
            pass

        # Add the new issues to the database.
        idb.AddIssue(issue1)
        idb.AddIssue(issue2)

        self.__PrintResults(output, issue1, issue2)


    def __PerformJoin(self, output):
        """Join two issues into a single one."""

        # Join should take exactly two arguments, the iids of the issues
        # to be joined.  If a different number of arguments are given,
        # report an error.
        if len(self.__arguments) != 2:
            raise qm.cmdline.CommandError, self.join_issue_error_syn
        
        iid1 = self.__arguments[0]
        iid2 = self.__arguments[1]

        # Get the issues out of the database.
        idb = qm.track.get_idb()
        try:
            issue1 = idb.GetIssue(iid1)
        except KeyError:
            raise qm.cmdline.CommandError, self.join_issue_error_sem % iid1
        try:
            issue2 = idb.GetIssue(iid2)
        except KeyError:
            raise qm.cmdline.CommandError, self.join_issue_error_sem % iid2

        # How are we supposed to map over all the fields to combine
        # the two issues?  For enumerals, do we want intersection or union?
        # We should probably think about this more.  For now, this function
        # will only copy the first issue, give it a new name, and set the
        # parents/children correctly.
        new_issue = issue1.Copy()
        new_issue.SetField('iid', issue1.GetField('iid') + '.'
                           + issue2.GetField('iid'))
        new_issue.SetField('parents', [ issue1, issue2 ])
        issue1.SetField('children', [ new_issue ])
        issue2.SetField('children', [ new_issue ])

        # Add the new issue to the database.  Check to see if the issue
        # names already exist.  If so, report an error.
        try:
            idb.AddIssue(new_issue)
        except ValueError:
            raise ComandError, \
                  self.join_iid_error_sem % issue1.GetId()

        self.__PrintResults(output, new_issue)


    def __PerformQuery(self, output):
        """Perform a query on the database."""

        # Get the class of the issue from the command line.  Use
        # 'None' if the class was not specified.
        issue_class_name = self.GetCommandOptions().get('class', None)

        # If there are no command arguments to the command, they did
        # not specify a query string to be use and we report an error.
        if len(self.__arguments) == 0:
            raise qm.cmdline.CommandError, self.query_error_syn

        # Combine the arguments to the query into one string so that
        # the expression may be passed to the Python expression
        # evaluator.
        query_str = string.join(self.__arguments)

        idb = qm.track.get_idb()
        results = idb.Query(query_str, issue_class_name)

        apply(self.__PrintResults, (output, ) + tuple(results))


    def __PerformServer(self, output):
        """Process the server command."""

        command_options = self.GetCommandOptions()
        # Get the port number specified by a command option, if any.
        # Otherwise use a default value.
        port_number = int(command_options.get('port', 8000))
        # Was a log file specified?
        try:
            log_file_path = command_options['log-file']
            # Yes.
            if log_file_path == '-':
                # A hyphen path name means standard output.
                log_file = sys.stdout
            else:
                # Otherwise, it's a file name.  Open it for append.
                log_file = open(log_file_path, "a+")
        except KeyError:
            # --log-file wasn't specified, so no logging.
            log_file = None
        # Start the server.
        qm.track.start_server(port_number, log_file)
    
    
    def __PerformShow(self, output):
        """Process the show command."""

        # Make sure an iid argument was specified.
        if len(self.__arguments) != 1:
            raise qm.cmdline.CommandError, self.show_wrong_args
        
        iid = self.__arguments[0]

        # Get the given issue out of the database.  If the issue is not
        # in the database, report an error.
        idb = qm.track.get_idb()
        try:
            issue = idb.GetIssue(iid)
        except KeyError:
            raise qm.cmdline.CommandError, self.show_no_iid % iid

        self.__PrintResults(output, issue)


    def __PerformInitialize(self, output):
        """Process the initialize command."""

        command_options = self.GetCommandOptions()
        # Determine the IDB class name from the command line or
        # default.
        try:
            idb_class_name = command_options['idb-type']
        except KeyError:
            # FIXME: Use the MemoryIdb implementation by default, for
            # now. 
            idb_class_name = 'MemoryIdb'
        # Make sure the class name is valid.
        try:
            idb_class = qm.track.idb.get_idb_class(idb_class_name)
        except ValueError:
            raise qm.cmdline.ConfigurationError, \
                  self.initialize_invalid_idb_class % idb_class_name
        # For this command, the IDB path is provided as an argument.
        # Make sure the --idb flag wasn't specified, to make sure
        # users aren't confused.
        if self.GetGlobalOptions().has_key('idb'):
            raise qm.cmdline.CommandError, \
                  self.initialize_wrong_flag
        # Make sure the argument was provided.
        if len(self.__arguments) != 1:
            raise qm.cmdline.CommandError, \
                  self.initialize_no_idb_path
        idb_path = self.__arguments[0]

        # Create the IDB.
        qm.track.initialize_idb(idb_path, idb_class_name)

        # If requested, populate the IDB with test values.
        if command_options.has_key('test-values'):
            qm.track.open_idb(idb_path)
            qm.track.setup_idb_for_test()
            qm.track.close_idb()


    def __PrintResults(self, output, *issues):
        """Print the list of issues that are the results of the command.

        'output' -- A file object to write the results to.

        'issues' -- A sequence of issues that resultsed from a command."""

        # Switch on the type of formatting.  For each different type,
        # print out the results in the correct format.
        if self.format_name == 'none':
            # No output.
            pass
        elif self.format_name == 'iid':
            iids = map(lambda issue: issue.GetId(), issues)
            output.write(string.join(iids, ',') + '\n')
        elif self.format_name == 'iid-single':
            for issue in issues:
                output.write(issue.GetId() + '\n')
        elif self.format_name == 'summary':
            for issue in issues:
                output.write('id: ' + issue.GetId() + '\n')
                output.write('summary:  ' + issue.GetField('summary'))
                output.write('\n\n')
        # We will make the 'short' format the same as 'iid-single' format
        # for now.
        elif self.format_name == 'short':
            for issue in issues:
                output.write(issue.GetId() + '\n')
        # We will make the 'full' format the same as the 'summary' format
        # for now.
        elif self.format_name == 'full':
            for issue in issues:
                output.write('id: ' + issue.GetId() + '\n')
                output.write('summary:  ' + issue.GetField('summary'))
                output.write('\n\n')
        elif self.format_name == 'xml':
            raise UnimplementedError


    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End: