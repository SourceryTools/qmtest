########################################################################
#
# File:   compiler.py
# Author: Mark Mitchell
# Date:   12/11/2001
#
# Contents:
#   Compiler
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

import os
import os.path
import StringIO
import re
import resource
import signal
import sys

########################################################################
# Functions
########################################################################

def RunCommand(arguments, timeout=0, environment=None):
    """Run the command given by 'arguments'.

    'arguments' -- A sequence of strings.  The first argument is
    the path giving the command to execute.  The system will
    search the 'PATH' environment variable for the command.

    'timeout' -- The number of seconds for which the child process
    should be permitted to execute.  If '0', then there is no limit.

    'environment' -- A dictionary mapping environment variable names
    to the values that they should take in the subprocess.  These
    variables are added to any environment variables that are already
    set.  If 'None', the current environment is used.
    
    returns -- A tuple '(status, output)' containing the exit status
    from the command (as returned by 'waitpid') and any output written
    to the standard output and/or standard error streams."""

    # Create a pipe.  The child will write its output through the
    # pipe.
    (r, w) = os.pipe()

    # Fork.
    child = os.fork()
    if child == 0:
        try:
            # Disable core dumps.
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            # Set the timeout.
            if timeout:
                signal.signal(signal.SIGALRM, signal.SIG_DFL)
                signal.alarm(timeout)
            else:
                assert None
            # This is the child.  We do not need to read from the
            # pipe.
            os.close(r)
            # Redirect the standard output and standard error to
            # the write end of the pipe.
            os.dup2(w, sys.stdout.fileno())
            os.dup2(w, sys.stderr.fileno())
            # Close the standard input in case the compiler tries
            # to read from there.
            sys.stdin.close()
            # Compute the environment for the command.
            if environment:
                new_environment = os.environ.copy()
                new_environment.update(environment)
            else:
                environment = os.environ
            # Run the command.
            os.execvpe(arguments[0], arguments, environment)
        except:
            # If we could not spawn the child process, exit
            # immediately.
            os._exit(1)

    # This is the parent.  We do not need the write end of the
    # pipe.
    os.close(w)
    # Read the entire contents of the pipe.
    f = os.fdopen(r)
    output = f.read()
    f.close()
    # Figure out what happened to the child.
    status = os.waitpid(child, 0)[1]

    return (status, output)

########################################################################
# Classes
########################################################################

class Compiler:
    """A 'Compiler' compiles and links source files."""

    MODE_COMPILE = 'compile'
    """Compile the source files, but do not link them."""
    
    MODE_LINK = 'link'
    """Compile and link the source files."""
    
    modes = [ MODE_COMPILE, MODE_LINK ]
    """The available compilation modes."""

    def __init__(self, path, options=None):
        """Construct a new 'GPP'.

        'path' -- A string giving the location of the compiler
        executable.

        'arguments' -- A list of strings indicating options to the
        compiler, or 'None' if there are no options."""

        self._path = path
        if options:
            self._options = options
        else:
            self._options = []
            

    def GetPath(self):
        """Returns the path to this 'Compiler'.

        returns -- A string giving the location of the compiler
        executable."""

        return self._path



class SourcePosition:
    """A 'SourcePosition' indicates a location in source code.

    A 'SourcePosition' consists of:

    - A file name.  The file name is a string.  It may be an absolute
      or relative path.  If no file name is available, the file name
      is the empty string.

    - A line number, indexed from one.  If no line number is
      available, the line number is zero.

    - A column number, indexed from one.  If no column number is
      available, the column nubmer is zero."""

    def __init__(self, file, line, column):
        """Construct a new 'SourcePosition'.

        'file' -- The file name.

        'line' -- The line number, indexed from one.  If no line numer
        is availble, use zero for this parameter.

        'column' -- The column number, indexed from one.  If no column
        number is available, use zero for this parameter."""

        assert file
        
        self.file = file
        self.line = line
        self.column = column

        
    def __str__(self):
        """Return an information representation of this 'SourcePosition'.

        returns -- A string representing this 'SourcePosition'"""

        result = ''
        if self.file:
            result = result + '"%s"' % self.file
        if self.line:
            result = result + ', line %d' % self.line
        if self.column:
            result = result + ': %d' % self.column

        return result

    
        
class Diagnostic:
    """A 'Diagnostic' is a message issued by a compiler.

    Each 'Diagnostic' has the following attributes:

    - The source position that the compiler associates with the
      diagnostic.

    - The severity of the diagnostic.
    
    - The message issued by the compiler.

    A 'Diagnostic' may either be an actual diagnostic emitted by a
    compiler, or it may be the pattern for a diagnostic that might be
    emitted.  In the latter case, the message is a regular expression
    indicating the message that should be emitted."""

    def __init__(self, source_position, severity, message):
        """Construct a new 'Diagnostic'.

        'source_position' -- A 'SourcePosition' indicating where the
        diagnostic was issued.  For an expected diagnostic, 'None'
        indicates that the position does not matter.

        'severity' -- A string indicating the severity of the
        diagnostic.  For an expected diagnostic, 'None' indicates
        that the severity does not matter.

        'message' -- For an emitted diagnostic, a string indicating
        the message produced by the compiler.  For an expected
        diagnostic, a string giving a regular expression indicating
        the message that might be emitted.  For an expected
        diagnostic, 'None' indicates that the message does not
        matter."""

        self.source_position = source_position
        self.severity = severity
        self.message = message


    def __str__(self):
        """Return an informal representation of this 'Diagnostic'.

        returns -- A string representing this 'Diagnostic'."""

        if self.source_position:
            source_position_string = str(self.source_position)
        else:
            source_position_string = "<no source position>"

        if self.severity:
            severity_string = self.severity
        else:
            severity_string = "<no severity>"

        if self.message:
            message_string = self.message
        else:
            message_string = "<no message>"

        return '%s: %s: %s' % (source_position_string,
                               severity_string,
                               message_string)


########################################################################
# Compilers
########################################################################
    
class GPP(Compiler):
    """A 'GPP' is the GNU Compiler Collection C++ compiler."""

    _severities = [ 'warning', 'error' ]
    """The diagnostic severities generated by the compiler.  Order
    matters; the order given here is the order that the
    '_severity_regexps' will be tried."""

    _severity_regexps = {
        'warning' :
          re.compile('^(?P<file>[^:]*):(?P<line>[^:]*):((?P<column>[^:]*):)? '
                     'warning: (?P<message>.*)$'),
        'error':
          re.compile('^(?P<file>[^:]*):(?P<line>[^:]*):((?P<column>[^:]*):)? '
                     '(?P<message>.*)$')
        }
    """A map from severities to compiled regular expressions.  If the
    regular expression matches a line in the compiler output, then that
    line indicates a diagnostic with the indicated severity."""

    _ignore_regexps = [
        re.compile('^.*: In (.*function|method|.*structor)'),
        re.compile('^.*: In instantiation of'),
        re.compile('^.*:   instantiated from'),
        re.compile('^.*: At (top level|global scope)'),
        re.compile('^.*file path prefix .* never used'),
        re.compile('^.*linker input file unused since linking not done'),
        re.compile('^collect: re(compiling|linking)'),
        ]
    
    _internal_error_regexp = re.compile('Internal (compiler )?error')
    """A compiled regular expression.  When an error message is matched
    by this regular expression, the error message indicates an
    internal error in the compiler."""

    def CompileSourceFiles(self, mode, source_files, timeout):
        """Compile the 'source_files'.

        'mode' -- The compilation mode (one of 'Compiler.modes') in
        which the 'source_files' should be compiled.
        
        'source_files' -- A sequence of strings giving the names of
        source files (and/or object files) that should be compiled.

        'timeout' -- The maximum number of seconds that the compiler
        is permitted to run before being terminated.

        returns -- A tuple '(status, output, command)'.  The 'status'
        is the exit status returned by the command, as returned by
        'waitpid'.  The 'output' is a string containing the complete
        standard output and standard error streams produced by the
        compiler.  The 'command' is the list of arguments making up
        the command that was issued to perform the compilation.

        After this method has been called, certain files will be
        present in the file system.  If 'mode' is 'MODE_COMPILE',
        there will be an object file corresponding to each of the
        source files, using the natural extension for the target
        system.  If 'mode' is 'MODE_LINK', there will be a single
        executable file with the name given by 'GetExecutableName'."""

        assert mode in Compiler.modes
        
        # Create the command invoking the compiler.
        command = [self._path]
        # Add the compiler options.
        command.extend(self._options)
        # Emit single-line diagnostics to make parsing diagnostics easier.
        command.append('-fmessage-length=0')
        # Disable linking, if appropriate.
        if mode == Compiler.MODE_COMPILE:
            command.append('-c')
        elif mode == Compiler.MODE_LINK:
            command.append('-o')
            command.append(self.GetExecutableName(source_files))

        # Add the names of the source files.
        command.extend(source_files)

        # Run the compiler.
        (status, output) = RunCommand(command, timeout)
        
        return (status, output, command)


    def GetExecutableName(self, source_files):
        """Return the name of the executable for the 'source_files'.

        'source_files' -- A sequence of strings giving the names of
        the source files.

        returns -- A string giving the name of the executable file
        that will be generated from the 'source_files'."""

        return os.path.splitext(source_files[0])[0]


    def GetObjectNames(self, source_files):
        """Return the names of the object files built from the 'source_files'.

        'source_files' -- A sequence of strings giving the names of
        the source files.

        returns -- A sequence of strings giving the names of the
        object files generated from the 'source_files'."""

        return map(lambda s: os.path.splitext(s)[0] + ".o",
                   source_files)
            
        
    def GetDiagnostics(self, output):
        """Return the 'Diagnostic's indicated in the 'output'.

        'output' -- A string giving the output from the compiler.

        returns -- A list of 'Diagnostic's corresponding to the
        messages indicated in 'output', in the order that they were
        emitted."""

        # Assume there were no diagnostics.
        diagnostics = []
        # Create a file object containing the 'output'.
        f = StringIO.StringIO(output)
        # Reall all of the output, line by line.
        for line in f.readlines():
            for severity in self._severities:
                match = self._severity_regexps[severity].match(line)
                # If it does not look like an error message, skip it.
                if not match:
                    continue

                # Some error messages are ignored.
                ignore = 0
                for ignore_regexp in self._ignore_regexps:
                    if ignore_regexp.match(match.group()):
                        ignore = 1
                        break

                if not ignore:
                    # An internal error is an error that indicates that
                    # the compiler crashed.
                    message = match.group('message')
                    if (severity == 'error'
                        and self._internal_error_regexp.search(message)):
                        severity = 'internal_error'

                    # If there is no line number, then we will not be
                    # able to convert it to an integer.
                    try:
                        line_number = int(match.group('line'))
                    except:
                        line_number = 0

                    # See if there is a column number.
                    try:
                        column_number = int(match.group('column'))
                    except:
                        column_number = 0
                        
                    source_position = SourcePosition(match.group('file'),
                                                     line_number,
                                                     column_number)
                    diagnostic = Diagnostic(source_position,
                                            severity,
                                            message)
                    diagnostics.append(diagnostic)
                    break

        return diagnostics
