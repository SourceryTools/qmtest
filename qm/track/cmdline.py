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

import issue
import issue_database
import os
import os.path
import qm
import qm.common
import qm.cmdline
import qm.fields
import qm.platform
import qm.structured_text
import qm.track.issue
import qm.xmlutil
import rexec
import server
import string
import sys

########################################################################
# constants
########################################################################

idb_environment_variable_name = "QMTRACK_DB_PATH"
"""The name of the environment variable containing the IDB path."""

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
    
    formats = (
        'export',
        'full',
        'iid',
        'iid-single',
        'long',
        'none',
        'short',
        'summary',
        'xml',
        )

    # The following are the options and commands for qmtrack.  To edit
    # these, simply add or remove one in this style, and then add or
    # remove it from the appropriate array directly below these
    # definitions.

    format_option_spec = (
        "f",
        "format",
        "TYPE",
        "Format for output."
        )

    database_option_spec = (
        "D",
        "idb",
        "PATH",
        "Path to issue database."
        )

    help_option_spec = (
        "h",
        "help",
        None,
        "Display usage summary."
        )

    remote_database_option_spec = (
        "R",
        "remote-idb",
        "URL",
        "URL of remote QMTrack server."
        )

    class_option_spec = (
        "c",
        "class",
        "NAME",
        "Class for new issue."
        )
    
    query_class_option_spec = (
        "c",
        "class",
        "NAME",
        "Class of issues to query."
        )
    
    port_option_spec = (
        "P",
        "port",
        "PORT",
        "Server port number."
        )

    address_option_spec = (
        "A",
        "address",
        "ADDRESS",
        "Local address."
        )

    log_file_option_spec = (
        None,
        "log-file",
        "PATH",
        "Log file name."
        )
    
    issue_store_implementation_option_spec = (
        None,
        "issue-store",
        "MODULE",
        "Issue store implementation module."
        )

    test_values_option_spec = (
        None,
        "test-values",
        None,
        "Populate IDB with values for testing."
        )
    
    internal_option_spec = (
        None,
        "internal",
        None,
        "Set up IDB for internal use."
        )
    
    output_option_spec = (
        "o",
        "output",
        "FILE",
        "Write output to FILE (- for stdout)."
        )

    verbose_option_spec = (
        "v",
        "verbose",
        None,
        "Display informational messages."
        )

    start_browser_option_spec = (
        "b",
        "start-browser",
        None,
        "Open a browser window to the Web interface."
        )

    force_option_spec = (
        None,
        "force",
        None,
        "Perform the command without confirmation."
        )

    qmtrack_option_specs = [
        database_option_spec,
        help_option_spec,
        remote_database_option_spec,
        verbose_option_spec,
        ]
    """All the command line options for qmtrack."""
    
    qmtrack_commands = [

        ("configure-idb",
         "Configure the IDB.",
         "",
"""This command starts the QMTrack issue database configuration server.
You may interact with the server via a web user interface over HTTP.""",
         [ help_option_spec, port_option_spec, address_option_spec,
           start_browser_option_spec ],
         ),

        ("create",
         "Create a new issue.",
         "-c classname field[=,+=]value...",
"""This command will create an issue. The field/value pairs indicate
attributes for the given issue. You must specify the class for the field
with the" " class flag. You must also specify the mandatory fields,
'id', 'categories', and 'summary'.""",
         [ help_option_spec, class_option_spec, format_option_spec,
           output_option_spec ]
         ),
        
        ("destroy-idb",
         "Destroy an IDB.",
         "",
"""This command destroys an issue database and removes associated
files.""",
         [ help_option_spec, force_option_spec ],
         ),

        ("edit",
         "Edit an issue.",
         "id field[=,+=,-=]value...",
"""This command will edit an issue. The 'id' is the issue's id. The
field/value pairs represent the fields you wish to edit. A new revision
of the issue will be created. """,
         [ help_option_spec, format_option_spec, output_option_spec ]
         ),

        ("import",
         "Import issues from XML files.",
         "FILE ...",
         """
This command imports issues or issue revisions stored in an XML file.
Each file may contain either individual issues (from the "xml" output
format) or complete issue revision histories (from the "export" output
format).
         """,
         [ help_option_spec, format_option_spec, output_option_spec ]
         ),

        ("create-idb",
         "Create an issue database.",
         "[ NAME=VALUE ... ]",
"""Initialize a new issue database.  You may specify configuration
properties on the command line.

Optionally, specify the issue store module with the '--issue-store'
option.  QMTrack includes these issue store modules:

    'qm.track.memory_issue_store' [default] -- Keep all issues in
    memory while running.  Store issues in an XML file.

You may specify another module instead; make sure it is in the
'PYTHONPATH'.""",
         [ help_option_spec, issue_store_implementation_option_spec,
           test_values_option_spec, internal_option_spec,
           output_option_spec ],
        ),
        
        ("join",
         "Join two issues.",
         "id1 id2",
"""This command will join two issues into a single issue. The resulting
issue will be the child of each of the original issues and they will be
its parent.""",
         [ help_option_spec, format_option_spec, output_option_spec ]
         ),

        ("query",
         "Query the database.",
         "expression",
"""This command will query the database to find all issues for which the
query expression evalutes to true.""",
         [ help_option_spec, query_class_option_spec,
           format_option_spec, output_option_spec ]
         ),

        ("server",
         "Start the server.",
         "",
"""This command starts the QMTrack server.  The server provides a web
user interface and remote command access over HTTP.""",
         [ help_option_spec, port_option_spec, address_option_spec,
           log_file_option_spec, start_browser_option_spec ]
         ),
    
        ("show",
         "Display an issue.",
         "id",
"""This command displays a single issue.  This command is a shortcut for
'query iid==value'.""",
         [ help_option_spec, format_option_spec, output_option_spec ]
         ),

        ("split",
         "Split an issue.",
         "id",
"""This command will split a single issue into two issues. The new
issues will be the children of the original issue and it will be their
parent.""",
         [ help_option_spec, format_option_spec, output_option_spec ]
         ),

    ]
    """All the commands for qmtrack."""

    # The following are the strings for all the warnings and errors
    # that can be encountered in this module.
    initialize_no_idb_path = "initialize: missing IDB path"
    
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
            "configure-idb" : self.__PerformConfigureIdb,
            "create" : self.__PerformCreate,
            "destroy-idb" : self.__PerformDestroyIdb,
            "edit" : self.__PerformEdit,
            "import" : self.__PerformImport,
            "create-idb" : self.__PerformCreateIdb,
            "join" : self.__PerformJoin,
            "query" : self.__PerformQuery,
            "server" : self.__PerformServer,
            "show" : self.__PerformShow,
            "split" : self.__PerformSplit,
            }

        self.__Parse()


    def GetCommand(self):
        """Get the name of the command given.

        returns -- This function returns a string for the name of the
        given command."""

        return self.__command_name


    def GetArgumentList(self):
        """Return the argument list that initialized this command."""

        return self.__argument_list


    def HasGlobalOption(self, option):
        """Return true if global 'option' was specified."""

        for opt, opt_arg in self.__global_options:
            if opt == option:
                return 1
        return 0


    def GetGlobalOption(self, option, default=None):
        """Return the value of global 'option', or 'default' if omitted."""

        for opt, opt_arg in self.__global_options:
            if opt == option:
                return opt_arg
        return default


    def HasCommandOption(self, option):
        """Return true if command 'option' was specified."""

        for opt, opt_arg in self.__command_options:
            if opt == option:
                return 1
        return 0
    

    def GetCommandOption(self, option, default=None):
        """Return the value of command 'option', or 'default' if ommitted."""

        for opt, opt_arg in self.__command_options:
            if opt == option:
                return opt_arg
        return default


    def GetIdbPath(self):
        """Figure out the path to the IDB to use for this invocation.

        Consults command-line options and environment variables.

        raises -- 'CommandError' if this function cannot figure out the
        path to the IDB."""

        # Was the path to the IDB specified via a command-line option?
        idb_path = self.GetGlobalOption("idb", None)
        if idb_path is None:
            # No IDB path specified explicitly.  Try the environment
            # variable.
            try:
                idb_path = os.environ[idb_environment_variable_name]
            except KeyError:
                # The environment variable wasn't set, either.  Can't
                # find the IDB, so give up.
                raise qm.cmdline.CommandError, \
                      qm.error("missing idb", envvar=env_var_name)
        return idb_path


    def RequiresIdb(self):
        """Return true if this command requires an IDB connection."""

        # If a help option was specified, we won't need the IDB.
        if self.HasGlobalOption("help") or self.HasCommandOption("help"):
            return 0
        # Some commands don't require an IDB connection.
        if self.GetCommand() in ("create-idb", "destroy-idb", ):
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

        
    def Execute(self, idb, output):
        """Execute the command."""

        # Was the output option specified?
        output_file_name = self.GetCommandOption("output", None)
        if output_file_name is not None:
            # Export to the specified file name.
            output_file = open(output_file_name, "w")
            output = output_file
        else:
            # Otherwise use the normal output.
            output_file = None

        # If the user specified the help command, print out the help
        # and exit.
        if self.HasGlobalOption("help"):
            output.write(self.parser.GetBasicHelp())
            return

        # If the user asked for help for a specific command, print out
        # the help for that command and exit.
        if self.HasCommandOption("help"):
            output.write(self.parser.GetCommandHelp(self.__command_name))
            return

        # Look up a handler for the command.  The command parser
        # should already have flagged the case where the command
        # is unrecognized.
        assert self.__command_dispatch.has_key(self.__command_name)
        handler = self.__command_dispatch[self.__command_name]
        # Call the command handler function.
        handler(idb, output)

        # Close the output file, if we opened it.
        if output_file is not None:
            output_file.close()
        

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
                      qm.track.error("create no equals", arg=pair)
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
                                               self.qmtrack_option_specs,
                                               self.qmtrack_commands)
        ( self.__global_options,
          self.__command_name,
          self.__command_options,
          self.__arguments
          ) = self.parser.ParseCommandLine(self.__argument_list)

        # Make sure the user specified a command.
        if self.__command_name == "" \
           and not self.HasGlobalOption("help"):
            # The user did not specify a command so we report an error.
            raise qm.cmdline.CommandError, \
                  qm.track.error("missing command")

        # Did the user specify a format style?  If so, use it.
        self.format_name = self.GetCommandOption("format", None)
        if self.format_name is None:
            # No format specified. Choose a default, depending on the
            # command.
            if self.__command_name in ("query", "show"):
                # For these commands, more thorough output makes sense
                # by default.
                self.format_name = "summary"
            else:
                # For other commands, just show the issue id.
                self.format_name = "iid"

        # Handle the verbose option.  The verbose level is the number of
        # times the verbose option was specified.
        qm.common.verbose = self.__global_options.count(("verbose", ""))

        # Make sure the format is valid.
        if not self.format_name in self.formats:
            raise qm.cmdline.CommandError, \
                  qm.track.error("format error", format=self.format_name)

    
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
                      qm.track.error("field exist", field=field_name, \
                                     issue_class=issue_class.GetName())

            # If the field does exist, get the field.
            field = issue_class.GetField(field_name)
            # If the field is of the set type, and they used the syntax
            # for a non-set type, report an error.
            if isinstance(field, qm.fields.SetField):
                if not is_set_operation:
                    raise qm.cmdline.CommandError, \
                          qm.track.error("field set use equal", \
                                         field=field_name)
            # Conversely, if the field is of a non-set type, and they
            # used the syntax for a set type, report an error.
            else:
                if is_set_operation:
                    raise qm.cmdline.CommandError, \
                          qm.track.error("field set use plus", \
                                         field=field_name)
                    
        
    def __PerformCreate(self, idb, output):
        """Create an issue because the create command was given."""

        # Get the class of the issue from the command line.
        issue_class_name = self.GetCommandOption("class", None)
        if issue_class_name is None:
            # The class was not specified.  Report an error.
            raise qm.cmdline.CommandError, \
                  qm.track.error("create class error syn")

        # Split the 'field=value' arguments up into pairs.
        hash = self.__ParseFieldValuePairs(self.__arguments)

        # If the issue class they specified does not exist, catch the
        # exception and report an error.
        try:
            icl = idb.GetIssueClass(issue_class_name)
        except KeyError:
            raise qm.cmdline.CommandError, \
                  qm.track.error("create field error", \
                                 field=issue_class_name)

        # Check that the user used the correct operator for the types of
        # fields that they specify.
        self.__CheckFieldTypes(hash, icl)

        # FIXME: Are there any fields that have to be specified
        # explicitly? 
        mandatory_fields = []

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
                  qm.track.error("create field error", \
                                 field=string.join(missing, ','))
        
        # Once we have checked that everything is in order to create the
        # new issue, we build it based on the argument pairs.
        iid = hash['iid']
        new_issue = qm.track.Issue(icl, iid=iid)
        for key, value in hash.items():
            if key != 'iid':
                try:
                    if string.rfind(key, '+') == len(key) - 1:
                        new_issue.SetField(string.replace(key, '+', ''),
                                           value)
                    elif string.rfind(key, '-') != len(key) - 1:
                        new_issue.SetField(key, value)
                except ValueError, msg:
                    raise qm.cmdline.CommandError, \
                          qm.track.error("create build error")
            
        # Add the issue to the database.  Check to see if the issue
        # with that 'iid' already exists.  If so, report an error.
        try:
            idb.GetIssueStore().AddIssue(new_issue)
        except ValueError:
            raise qm.cmdline.CommandError, \
                  qm.track.error("create issue error", iid=iid)

        self.__PrintResults(idb, output, new_issue)


    def __PerformEdit(self, idb, output):
        """Edit an issue because the edit command was given."""

        # If there are no command arguments to the command, they did
        # not specify a command to be edited and we report an error.
        if len(self.__arguments) == 0:
            raise qm.cmdline.CommandError, \
                  qm.track.error("edit issue error syn")
        
        iid = self.__arguments[0]

        # Get the given issue out of the database.  If the issue is not
        # in the database, report an error.
        try:
            issue = idb.GetIssueStore().GetIssue(iid)
        except KeyError:
            raise qm.cmdline.CommandError, \
                  qm.track.error("edit issue error sem", iid=iid)

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
        idb.GetIssueStore().AddRevision(issue)

        self.__PrintResults(idb, output, issue)


    def __PerformSplit(self, idb, output):
        """Split one issue into two."""

        istore = idb.GetIssueStore()
        # If there are no command arguments to the command, they did
        # not specify a command to be split and we report an error.
        if len(self.__arguments) == 0:
            raise qm.cmdline.CommandError, \
                  qm.track.error("split issue error syn")
        
        iid = self.__arguments[0]

        # Get the issue out of the database.
        try:
            issue = istore.GetIssue(iid)
        except KeyError:
            raise qm.cmdline.CommandError, \
                  qm.track.error("split issue error sem", iid=iid)

        self.split_issue_error_sem % iid

        # Copy the original issue.
        issue1 = issue.copy()
        issue2 = issue.copy()

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
            istore.GetIssue(issue1.GetId())
            raise qm.cmdline.CommandError, \
                  qm.track.error("split iid error sem", iid=issue1.GetId())
        except ValueError:
            # Couldn't find the issue; that's good.
            pass
        try:
            istore.GetIssue(issue2.GetId())
            raise qm.cmdline.CommandError, \
                  qm.track.error("split iid error sem", iid=issue2.GetId())
        except ValueError:
            # Couldn't find the issue; that's good.
            pass

        # Add the new issues to the database.
        istore.AddIssue(issue1)
        istore.AddIssue(issue2)

        self.__PrintResults(idb, output, issue1, issue2)


    def __PerformJoin(self, idb, output):
        """Join two issues into a single one."""

        istore = idb.GetIssueStore()
        # Join should take exactly two arguments, the iids of the issues
        # to be joined.  If a different number of arguments are given,
        # report an error.
        if len(self.__arguments) != 2:
            raise qm.cmdline.CommandError, \
                  qm.track.error("join issue error syn")
        
        iid1 = self.__arguments[0]
        iid2 = self.__arguments[1]

        # Get the issues out of the database.
        try:
            issue1 = istore.GetIssue(iid1)
        except KeyError:
            raise qm.cmdline.CommandError, \
                  qm.track.error("join issue error sem", iid=iid1)
        try:
            issue2 = istore.GetIssue(iid2)
        except KeyError:
            raise qm.cmdline.CommandError, \
                  qm.track.error("join issue error sem", iid=iid2)

        # How are we supposed to map over all the fields to combine
        # the two issues?  For enumerals, do we want intersection or union?
        # We should probably think about this more.  For now, this function
        # will only copy the first issue, give it a new name, and set the
        # parents/children correctly.
        new_issue = issue1.copy()
        new_issue.SetField('iid', issue1.GetField('iid') + '.'
                           + issue2.GetField('iid'))
        new_issue.SetField('parents', [ issue1, issue2 ])
        issue1.SetField('children', [ new_issue ])
        issue2.SetField('children', [ new_issue ])

        # Add the new issue to the database.  Check to see if the issue
        # names already exist.  If so, report an error.
        try:
            istore.AddIssue(new_issue)
        except ValueError:
            raise ComandError, \
                  qm.track.error("join iid error sem", iid=issue1.GetId())

        self.__PrintResults(idb, output, new_issue)


    def __PerformQuery(self, idb, output):
        """Perform a query on the database."""

        # Get the class of the issue from the command line.  Use
        # 'None' if the class was not specified.
        issue_class_name = self.GetCommandOption("class", None)

        # If there are no command arguments to the command, they did
        # not specify a query string to be use and we report an error.
        if len(self.__arguments) == 0:
            raise qm.cmdline.CommandError, \
                  qm.track.error("query error syn")

        # Combine the arguments to the query into one string so that
        # the expression may be passed to the Python expression
        # evaluator.
        query_str = string.join(self.__arguments)

        if issue_class_name is None:
            # No issue class was specified.  Therefore, search all issue
            # classes.  Obtain all their names.
            issue_class_names = map(lambda cl: cl.GetName(),
                                    idb.GetIssueClasses())
        else:
            # Search only one issue class.
            issue_class_names = [ issue_class_name ]
        results = []
        # Aggregate query results for all issue classes.
        istore = idb.GetIssueStore()
        for name in issue_class_names:
            results = results + (istore.Query(query_str, name))

        apply(self.__PrintResults, (idb, output, ) + tuple(results))


    def __HandleServerOptions(self, default_address=""):
        # Get the port number specified by a command option, if any.
        port_number = self.GetCommandOption("port", None)
        if port_number is None:
            # The port number was not specified.  Use a default value.
            port_number = 8000
        else:
            try:
                port_number = int(port_number)
            except ValueError:
                raise qm.cmdline.CommandError, \
                      qm.error("bad port number")
        # Get the local address specified by a command option, if any.
        # If not was specified, use the empty string, which corresponds
        # to all local addresses.
        address = self.GetCommandOption("address", default_address)
        # Was a log file specified?
        log_file_path = self.GetCommandOption("log-file", None)
        if log_file_path is not None:
            # Yes.
            if log_file_path == "-":
                # A hyphen path name means standard output.
                log_file = sys.stdout
            else:
                # Otherwise, it's a file name.  Open it for append.
                log_file = open(log_file_path, "a+")
        else:
            # The option '--log-file' wasn't specified, so no logging.
            log_file = None
            
        return (port_number, address, log_file)



    def __PerformConfigureIdb(self, idb, output):
        """Process the server command."""

        # FIXME: Security.  Restrict access to the configuration
        # database with a cookie value in the URL?

        # FIXME: Default to binding to localhost only?

        # Construct the server.
        port_number, address, log_file = self.__HandleServerOptions()
        web_server = server.make_configuration_server(idb, port_number,
                                                      address, log_file)

        # Construct the URL to the main page on the server.
        if address == "":
            url_address = qm.platform.get_host_name()
        else:
            url_address = address
        url = "http://%s:%d/track/config-idb" % (url_address, port_number)

        if self.HasCommandOption("start-browser"):
            # Now that the server is bound to its address, we can point
            # a browser at it safely.
            qm.platform.open_in_browser(url)
        else:
            qm.common.print_message(0, "%s server running at %s .\n"
                                    % (qm.common.program_name, url))

        # Go.
        server.run_server(web_server)

    
    def __PerformServer(self, idb, output):
        """Process the server command."""

        # Construct the server.
        port_number, address, log_file = self.__HandleServerOptions()
        web_server = server.make_server(idb, port_number, address, log_file)

        # Construct the URL to the main page on the server.
        if address == "":
            url_address = qm.platform.get_host_name()
        else:
            url_address = address
        url = "http://%s:%d/track/index" % (url_address, port_number)

        if self.HasCommandOption("start-browser"):
            # Now that the server is bound to its address, we can point
            # a browser at it safely.
            qm.platform.open_in_browser(url)
        else:
            qm.common.print_message(0, "%s server running at %s .\n"
                                    % (qm.common.program_name, url))

        # Print the XML-RPM URL for this server, if verbose.
        xml_rpc_url = web_server.GetXmlRpcUrl()
        qm.common.print_message(1, "XML-RPC URL is %s .\n" % xml_rpc_url)
        # Write the URL file.  It contains the XML-RPC URL for this server.
        url_path = os.path.join(self.GetIdbPath(), "server.url")
        url_file = open(url_path, "w")
        url_file.write(xml_rpc_url + '\n')
        url_file.close()

        try:
            # Start the server.
            web_server.Run()
        finally:
            # Clean up the URL file.
            os.remove(url_path)

    
    def __PerformShow(self, idb, output):
        """Process the show command."""

        # Make sure an iid argument was specified.
        if len(self.__arguments) != 1:
            raise qm.cmdline.CommandError, \
                  qm.track.error("show wrong args")
        
        iid = self.__arguments[0]

        # Get the given issue out of the database.  If the issue is not
        # in the database, report an error.
        try:
            issue = idb.GetIssueStore().GetIssue(iid)
        except KeyError:
            raise qm.cmdline.CommandError, \
                  qm.track.error("show no iid", iid=iid)

        self.__PrintResults(idb, output, issue)


    def __PerformCreateIdb(self, idb_, output):
        """Create a new issue database."""

        idb_path = self.GetIdbPath()

        # Determine the IDB class name from the command line or
        # default.

        # FIXME: Use the MemoryIdb implementation by default, for now.
        issue_store_module_name = self.GetCommandOption(
            "issue-store", "qm.track.memory_issue_store")

        # Make sure the class name is valid.
        try:
            issue_store_module = \
                qm.common.load_module(issue_store_module_name)
        except ImportError, exception:
            raise qm.ConfigurationError, \
                  qm.track.error("issue store module error",
                                 name=issue_store_module_name,
                                 error=str(exception))

        # Extract configuration variables from the command line.
        configuration = {}
        for argument in self.__arguments:
            if not "=" in argument:
                raise qm.cmdline.CommandError, \
                      qm.error("invalid property", error="argument") 
            key, value = string.split(argument, "=", 1)
            configuration[key] = value

        # Create the IDB.
        idb = issue_database.create(
            idb_path, issue_store_module_name, configuration)

        # If requested, populate the IDB for testing.
        if self.HasCommandOption("test-values"):
            idb = issue_database.open(idb_path)
            issue_database.setup_for_test(idb)
            idb.Close()

        # Print a helpful message.
        message = qm.warning("new idb message",
                             path=idb_path,
                             envvar=idb_environment_variable_name, 
                             userdb=os.path.join(idb_path, "users.xml"))
        message = qm.structured_text.to_text(message)
        output.write(message)


    def __PerformDestroyIdb(self, idb, output):
        """Destroy an issue database."""

        idb_path = self.GetIdbPath()
        # Make sure there is something that looks like an IDB there.
        if not os.path.isdir(idb_path):
            raise qm.cmdline.CommandError, \
                  qm.error("no idb at path", idb_path=idb_path)

        while not self.HasCommandOption("force"):
            # Ask the user for for confirmation.
            sys.stdout.write("Are you sure you want to delete the IDB "
                             "at %s? [y/n] " % idb_path)
            sys.stdout.flush()
            # Get an answer.
            input = string.lower(sys.stdin.readline())
            if input[0] == 'y':
                # Confirmed; fall out of this loop and proceded.
                break
            elif input[0] == 'n':
                # Aborted.  Unlock and return.
                lock.Unlock()
                return
            else:
                # Otherwise, loop.
                continue

        # Destroy the IDB.
        issue_database.destroy(idb_path)


    def __PerformImport(self, idb, output):
        """Process the import command."""

        # Make sure some import files were specified.
        if len(self.__arguments) == 0:
            raise qm.cmdline.CommandError, \
                  qm.track.error("missing import files")
        file_names = self.__arguments

        # Load issues from all files.
        issues = []
        for file_name in file_names:
            # Open and parse the XML file.
            document = qm.xmlutil.load_xml_file(file_name)

            document_element = document.documentElement
            document_tag = document_element.tagName

            # What kind of document is it?
            if document_tag == "issues":
                # An "issues" document contains individual issues.
                # Import them as current revisions.
                self.__ImportIssues(idb, document_element)
            elif document_tag == "histories":
                # A "histories" document contains entire revision
                # histories of issues.  Import them as entire issues. 
                self.__ImportIssueHistories(idb, document_element)
            else:
                raise issue.IssueFileError, \
                      qm.error("xml file unknown document element",
                               element_tag=document_tag)
            

    def __ImportIssues(self, idb, node):
        """Import issues from DOM "issues" element 'node' into 'idb'."""

        istore = idb.GetIssueStore()

        issue_classes = qm.common.make_map_from_list(
            idb.GetIssueClasses(), lambda icl: icl.GetName())
        issues = issue.get_issues_from_dom_node(node, issue_classes)

        # Loop over the issues.
        for issue in issues:
            iid = issue.GetId()
            try:
                # Try to get the current revision for this IID.
                current_revision = istore.GetIssue(iid)
            except KeyError:
                # Couldn't get it; that means it's a new issue.
                istore.AddIssue(issue)
                output.write("imported issue %s new\n" % iid)
            else:
                # Got the current revision, so this issue already
                # exists.  So add a new revision, but first make sure
                # it's different from the current one.
                differences = qm.track.get_differing_fields(issue,
                                                            current_revision)
                if len(differences) == 0:
                    # No differences; don't add a revision.
                    output.write("imported issue %s is current; skipping\n"
                                 % iid)
                else:
                    # Add the new revision.
                    istore.AddRevision(issue)
                    output.write(
                        "imported issue %s revision %d\n"
                        % (iid, current_revision.GetRevisionNumber() + 1))


    def __ImportIssueHistories(self, idb_, node):
        """Import issue histories from DOM element 'node'. into 'idb_'."""

        # FIXME: Handle any errors?
        issue_histories = issue.get_histories_from_dom_node(node)
        for history in issue_histories:
            idb.import_issue_history(idb_, history)
            


    def __PrintResults(self, idb, output, *issues):
        """Print the list of issues that are the results of the command.

        'idb' -- The issue database.

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
                output.write('ID: ' + issue.GetId() + '\n')
                output.write('Summary:  ' + issue.GetField('summary'))
                output.write('\n\n')
        # We will make the 'short' format the same as 'iid-single' format
        # for now.
        elif self.format_name == 'short':
            for issue in issues:
                output.write(issue.GetId() + '\n')
        # We will make the 'full' format the same as the 'long' format
        # for now.
        elif self.format_name == 'long' or self.format_name == "full":
            for issue in issues:
                for field in issue.GetClass().GetFields():
                    if field.IsAttribute("hidden"):
                        continue
                    value = str(issue.GetField(field.GetName()))
                    output.write("%-24s: %s\n" % (field.GetTitle(), value))
                output.write('\n\n')
        elif self.format_name == 'xml':
            qm.track.issue.issues_to_xml(issues, output)
        elif self.format_name == "export":
            # Retrieve the issue history for each issue.
            istore = idb.GetIssueStore()
            histories = []
            for issue in issues:
                history = istore.GetIssueHistory(issue.GetId())
                histories.append(history)
            # Write them.
            qm.track.issue.write_issue_histories(histories, output)



########################################################################
# functions
########################################################################

def run_command(argument_list,
                output_file=sys.stdout,
                error_file=sys.stderr):
    """Construct a command from 'argument_list', and execute it.

    'argument_list' -- A list of command-line arguments, as 'sys.argv'.
    The first element is the name of the script used to invoke QMTrack. 

    'output_file' -- A file object to which to write normal output.

    'error_file' -- A file object to which to write error messages.

    returns -- An integer exit code."""

    # Separate off the script name.
    script_name = argument_list[0]
    argument_list = argument_list[1:]

    try:
        # Parse the argument list.
        try:
            command = Command(argument_list)
        except qm.cmdline.CommandError, msg:
            error_file.write("%s error:\n" % script_name)
            error_file.write(qm.structured_text.to_text(str(msg)))
            error_file.write("Invoke %s --help for help with usage.\n"
                             % script_name)
            return 2

        # We'll set 'server_url' to the URL of the remote server, if
        # applicable.  Otherwise, 'idb' is the local IDB instance.
        server_url = None
        idb = None

        # Now execute the command.  Is it to be executed remotely?
        if command.RequiresIdb():
            if command.HasGlobalOption("remote-idb"):
                # The user specified a URL to a remote server.  Use it
                # for remote mode.
                server_url = command.GetGlobalOption("remote-idb")
            else:
                # We have a local IDB path.
                idb_path = command.GetIdbPath()
                # Open the IDB.
                try:
                    idb = issue_database.open(idb_path)
                except issue_database.AccessIdbRemotelyInstead, exception:
                    # Tried to open the IDB, but it's in use.  Luckily,
                    # we can connect to the server that's using it.
                    server_url = str(exception)

        # So, are we using a remote IDB or a local one?
        if server_url is not None and command.RequiresIdb():
            # If this command requires a local IDB, we're out of luck.
            if command.RequiresLocalIdb():
                raise RuntimeError, qm.error("idb in use")
            # Use a remote IDB.
            qm.common.print_message(2, 
                qm.message("using remote idb", url=server_url))
            server.execute_remotely(command, server_url,
                                    output_file, error_file)
        else:
            # Use a local IDB.
            try:
                # Execute the command.
                exit_code = server.execute_locally(
                    command, idb, output_file, error_file)
            finally:
                # Close the session, if one's open.
                if idb is not None:
                    idb.Close()

    except KeyboardInterrupt:
        # User killed it; that's OK.
        error_file.write("Interrupted.\n")
        return 0

    except qm.platform.SignalException, exception:
        # The program was ended by an exception.
        error_file.write("Terminated by %s.\n" % str(exception))
        return 0


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
