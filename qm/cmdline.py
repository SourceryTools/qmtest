########################################################################
#
# File:   cmdline.py
# Author: Benjamin Chelf
# Date:   2001-01-09
#
# Contents:
#   Code for command line interface.
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
#  Using the Command Parser
#
#  The command parser can be used by giving a list of flags and commands
#  to be parsed. See the constructor below for the exact structure of
#  those things. You can then use the parser to 1) generate help strings
#  for the general program, 2) generate help strings for specific
#  commands, and 3) parse command lines to split up which flags were
#  passed, which command was given, and the arguments and flags to that
#  command that were specified.
#
########################################################################

########################################################################
# imports
########################################################################

import copy
import getopt
import qm
import string
import structured_text
import sys

########################################################################
# classes
########################################################################

class CommandError(qm.UserError):

    pass



class CommandParser:
    """Class for the functionality that parses the command line.

    The command parser is used to easily specify a list of command line
    options and commands to be parsed from an argument list."""
    
    def __init__(self, name, options, commands):
        """Create a new command parser.

        'name' -- The name of the executable that we are currently
        using.  This will normally be argv[0].
        
        'options' -- A list of 4-tuples specifying flags that you wish
        this parser to accept.  The 4-tuple has the following form:
        (short_form, long_form, flags, description).  'short_form' must be
        exactly one character.  'long_form' must be specified for every
        flag in the list.  'arg_name' is a string representing the name of
        the argument that is passed to this flag.  If it is 'None,' then
        this flag doesn't take an argument.  'description' is a string
        describing the flag.

        'commands' -- A list of 5-tuples specifying commands to be
        accepted after the command line flags.  The 5-tuple has the
        form '(name, short_description, args_string, long_description,
        flags)'.

          'name' -- The string for the command.

          'short_description' -- A short description of the command to
          be printed out in general help.

          'args_string' -- The string that will be printed after the
          command in the command specific help.

          'long_description' -- The long description to be printed out
          in the command specfic help.

          'flags' -- A list of 4-tuples of the same form as the
          'options' described above.
        """

        self.__name = name
        
        # Check that the options are ok.
        self.CheckOptions(options)
        self.__options = copy.deepcopy(options)

        self.__option_to_long = {}
        for option in self.__options:
            # Check for duplicate short options.
            if self.__option_to_long.has_key('-' + option[0]):
                raise ValueError, "duplicate short option -%s" % option[0]
            self.__option_to_long['-' + option[0]] = option[1]
            # Check for duplicate long options.
            if self.__option_to_long.has_key('--' + option[1]):
                raise ValueError, "duplicate long option --%s" % option[1]
            self.__option_to_long['--' + option[1]] = option[1]
        
        # Check that the options for each command are ok.
        for command in commands:
            self.CheckOptions(command[4])

        self.__commands = copy.deepcopy(commands)
        for i in range(0, len(self.__commands)):
            command = self.__commands[i]
            map = {}
            for option in command[4]:
                if option[0] is not None:
                    # Check for duplicate short options.
                    if map.has_key('-' + option[0]):
                        raise ValueError, \
                              "duplicate short command option -%s" \
                              % option[0]
                    map['-' + option[0]] = option[1]
                # Check for duplicate long options.
                if map.has_key('--' + option[1]):
                    raise ValueError, \
                          "duplicate long command option --%s" % option[1]
                map['--' + option[1]] = option[1]
            command = command + (map,)
            self.__commands[i] = command

        # Build the options string for getopt.
        self.__getopt_options = self.BuildGetoptString(self.__options)


    def CheckOptions(self, options):
        """Check that a list of options 4-tuples is correct.

        'options' -- A list of 4-tuples as described above.

        returns -- 1 if the options are all valid, 0 otherwise."""

        for short_option, long_option, flags, descripton in options:
            # The short form of the option must have exactly 1 character.
            if short_option != None and len(short_option) != 1:
                raise ValueError, "short option must have exactly 1 character"
            # The long form of the option must be specified.
            if long_option == None or len(long_option) == 0:
                raise ValueError, \
                      "long option must be specified for -%s" % short_option
        
        return 1


    def BuildGetoptList(self, options):
        """Build a getopt list for the long options.

        'options' -- A list of 4-tuples as described above.

        returns -- A list to be passed to getopt to parse long options."""

        # Build the options string for getopt.
        getopt_list = []

        for option in options:
            # Tell getopt that this option takes an argument.
            if option[2] != None:
                getopt_list.append(option[1] + '=')
            else:
                getopt_list.append(option[1])

        return getopt_list
        
        
    def BuildGetoptString(self, options):
        """Build a getopt string for the options passed in.

        'options' -- A list of 4-tuples as described above.

        returns -- A string to be passed to getopt to parse the
        options."""

        # Build the options string for getopt.
        getopt_string = ''

        for option in options:
            if option[0] is not None:
                getopt_string = getopt_string + option[0]
                # Tell getopt that this option takes an argument.
                if option[2] != None:
                    getopt_string = getopt_string + ':'

        return getopt_string


    def GetOptionsHelp(self, options):
        """Return a string that is the basic help for options.

        options -- A list of options to get the help string for.

        returns -- A string to be printed for the options."""

        help_string = ""

        # Print out the short form, long form, and then the description.
        for option in options:
            # Format the short form, if there is one.
            if option[0] is None:
                short_form = "   "
            else:
                short_form = "-%s," % option[0]
            # Format the long form.  Include the option arugment, if
            # there is one. 
            if option[2] is None:
                long_form = "--%-24s" % option[1]
            else:
                long_form = "--%-24s" % (option[1] + " " + option[2])
            # Generate a line for this option.
            help_string = help_string \
                          + "  %s %s: %s\n" \
                          % (short_form, long_form, option[3])

        return help_string

        
    def GetBasicHelp(self):
        """Return a string that is the basic help for the commands.

        returns -- A string to be printed with basic functionality of
        arguments and commands."""

        help_string = "Usage: %s " % self.__name
        help_string = help_string \
                      + "[ FLAGS ] COMMAND [ COMMAND-FLAGS ] [ ARGUMENTS ]\n\n"
        help_string = help_string + "flags:\n"
        help_string = help_string + self.GetOptionsHelp(self.__options)
        help_string = help_string + "\ncommands:\n"
        # Print out the commands and their short descriptions.
        for command in self.__commands:
            help_add = "%-30s: %s"%(command[0], command[1])
            help_string = help_string + "  %s\n"%(help_add)
        help_string = help_string \
                      + "\nInvoke\n  %s COMMAND --help\n" \
                      "for information about " \
                      "COMMAND-FLAGS and ARGUMENTS.\n\n" % self.__name

        return help_string

    
    def GetCommandHelp(self, command):
        """Return a string that is the help for a specific command.

        command -- A string of the command that you want help for.

        returns -- A string of help for a given command."""

        help_string = "Usage: %s %s [ FLAGS ] "%(self.__name, command)
        for command_item in self.__commands:
            if command_item[0] == command:
                help_string = help_string + command_item[2] + "\n\n"
                help_string = help_string + "Flags:\n"
                help_string = help_string \
                              + self.GetOptionsHelp(command_item[4])
                help_string = help_string + "\n"
                help_string = help_string \
                              + structured_text.to_text(command_item[3])
                return help_string
            
        return "Command not found"

        
    def ParseCommandLine(self, argv):
        """Parse a command line.

        'argv' -- A string containing the command line starting with
        argv[1].  It should not contain the name of the executed program.

        returns -- A 4-tuple of the flags given, the command given, the
        command flags, and the command arguments.  Its form is this:
        (flags, command, command_flags, command_args).  'flags' is a list
        of 2-tuples indicating each flag specified and the argument given
        to that flag (if applicable).  'command' is the command given.
        'command_flags' is a list of 2-tuples indicating each flag given
        to the command and its possible argument.  'command-args' is a
        list of arguments as given to the command.  If no command is
        given, then the function will return '' for the command, [] for
        the arguments, and [] for the command flags.

        raises -- 'CommandError' if the command is invalid."""

        # Get the flags off of the front of the command line.
        getopt_list = self.BuildGetoptList(self.__options)

        try:
            flags, args = getopt.getopt(argv, self.__getopt_options,
                                        getopt_list)
        except getopt.error, msg:
            raise CommandError, msg
        
        for i in range(0, len(flags)):
            flag = flags[i]
            new_flag = (self.__option_to_long[flag[0]], flag[1])
            flags[i] = new_flag
        
        # Did not specify anything on the command line except flags.
        if args == []:
            return (flags, '', [], [])
        
        # Get the command.
        command = args[0]

        # This checks to make sure the command they specified is actually
        # a command that we know.  Checking this now saves trouble
        # in having to do it later.
        found = 0
        for command_item in self.__commands:
            if command == command_item[0]:
                found = 1

        if found == 0:
            # The command they specified does not exist; print out the
            # help and raise an exception.
            raise CommandError, 'unrecognized command %s' % command
            
        # Get the arguments to the command.
        args = string.join(args[1:])
        command_options = []

        for command_item in self.__commands:
            if command_item[0] == command:
                command_options = command_item[4]
                break
        getopt_string = self.BuildGetoptString(command_options)
        getopt_list = self.BuildGetoptList(command_options)
        try:
            command_flags, command_args = getopt.getopt(string.split(args),
                                                        getopt_string,
                                                        getopt_list)
        except getopt.error, msg:
            raise CommandError, "%s: %s" % (command, msg)

        for i in range(0, len(command_flags)):
            flag = command_flags[i]
            new_flag = (command_item[5][flag[0]], flag[1])
            command_flags[i] = new_flag
            
        return (flags, command, command_flags, command_args)

