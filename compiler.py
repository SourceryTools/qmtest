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
# For license terms see the file COPYING.
#
########################################################################

from   executable import *
import os
import os.path
import StringIO
import re
import resource
import sys

########################################################################
# Classes
########################################################################
    
class CompilerExecutable(RedirectedExecutable):
    """A 'CompilerExecutable' is a 'Compiler' that is being run."""

    def __init__(self, compiler, dir = None):
        """Construct a new 'CompilerExecutable'.

        'compiler' -- The 'Compiler' to run.

        'dir' -- If not 'None', The directory in which to run the
        compiler."""

        RedirectedExecutable.__init__(self, compiler.GetPath(), dir)


    def _InitializeChild(self):
        """Initialize the child process.

        After 'fork' is called this method is invoked to give the
        child a chance to initialize itself.  '_InitializeParent' will
        already have been called in the parent process."""

        # Disable compiler core dumps.
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        # Do whatever the base class version would otherwise do.
        RedirectedExecutable._InitializeChild(self)


    def _StdinPipe(self):
        """Return a pipe to which to redirect the standard input.

        returns -- A pipe, or 'None' if the standard input should be
        closed in the child."""

        # The compiler should not need the standard input.
        return None


    def _StderrPipe(self):
        """Return a pipe to which to redirect the standard input.

        returns -- A pipe, or 'None'.  If 'None' is returned, but
        '_StdoutPipe' returns a pipe, then the standard error and
        standard input will both be redirected to that pipe.  However,
        if '_StdoutPipe' also returns 'None', then the standard error
        will be closed in the child."""

        # The standard output and standard error are combined.
        return None



class Compiler:
    """A 'Compiler' compiles and links source files."""

    MODE_COMPILE = 'compile'
    """Compile the source files, but do not assemble them."""
    
    MODE_ASSEMBLE = 'assemble'
    """Compile the source files, but do not link them."""
    
    MODE_LINK = 'link'
    """Compile and link the source files."""
    
    modes = [ MODE_COMPILE, MODE_ASSEMBLE, MODE_LINK ]
    """The available compilation modes."""

    def __init__(self, path, options=None):
        """Construct a new 'GPP'.

        'path' -- A string giving the location of the compiler
        executable.

        'options' -- A list of strings indicating options to the
        compiler, or 'None' if there are no options."""

        self._path = path
        self.SetOptions(options or [])
            

    def Compile(self, mode, files, dir, options=[], output=None):
        """Compile the 'files'.
        
        'mode' -- The compilation mode (one of the 'Compiler.modes')
        that should be used to compile the 'files'.

        'files' -- A sequence of strings giving the names of source
        files (including, in general, assembly files, object files,
        and libraries) that should be compiled.

        'dir' -- The directory in which to run the compiler.
        
        'options' -- A sequence of strings indicating additional
        options that should be provided to the compiler.

        'output' -- The name of the file should be created by the
        compilation.  If 'None', the compiler will use a default
        value.

        returns -- A tuple '(status, output, command)'.  The 'status'
        is the exit status returned by the compiler, as indicated by
        'waitpid'.  The 'output' is a string containing the standard
        outpt and standard errror generated by the compiler.  The
        'command' is a list of strings indicating the command used to
        perform the compilation."""

        # Get the command to use.
        command = self.GetCompilationCommand(mode, files, options, output)
        # Invoke the compiler.
        executable = CompilerExecutable(self, dir)
        status = executable.Run(command)
        # Return all of the information.
        return (status, executable.stdout, command)
        
        
    def GetCompilationCommand(self, mode, files, options=[], output=None):
        """Return the appropriate command for compiling 'files'.

        'mode' -- The compilation mode (one of the 'Compiler.modes')
        that should be used to compile the 'files'.

        'files' -- A sequence of strings giving the names of source
        files (including, in general, assembly files, object files,
        and libraries) that should be compiled.

        'options' -- A sequence of strings indicating additional
        options that should be provided to the compiler.

        'output' -- The name of the file should be created by the
        compilation.  If 'None', the compiler will use a default
        value.  (In some cases there may be multiple outputs.  For
        example, when generating multiple object files from multiple
        source files, the compiler will create a variety of objects.)

        returns -- A sequence of strings indicating the arguments,
        including 'argv[0]', for the compilation command."""

        # Start with the path to the compiler.
        command = [self.GetPath()]
        # Add switches indicating the compilation mode, if appropriate.
        command += self._GetModeSwitches(mode)
        # Add the options that should be used with every compilation.
        command += self._options
        # Add the options that apply to this compilation.
        command += options
        # Set the output file.
        if output:
            command += ["-o", output]
        # Add the input files.
        command += files

        return command
        

    def ParseOutput(self, output, ignore_regexps = ()):
        """Turn the 'output' into a sqeuence of 'Diagnostic's.

        'output' -- A string containing the compiler's output.

        'ignore_regexps' -- A sequence of regular expressions.  If a
        diagnostic message matches one of these regular expressions,
        it will be ignored.

        returns -- A list of 'Diagnostic's corresponding to the
        messages indicated in 'output', in the order that they were
        emitted."""

        assert None
        
        
    def GetPath(self):
        """Return the location of the executable.

        returns -- A string giving the location of the executable.
        This location is the one that was specified as the 'path'
        argument to '__init__'."""
        
        return self._path


    def GetOptions(self):
        """Return the list of compilation options.

        returns -- A list of strings giving the compilation options
        specified when the 'Compiler' was constructed."""

        return self._options


    def SetOptions(self, options):
        """Reset the list of compiler options.
        
        'options' -- A list of strings indicating options to the
        compiler, or 'None' if there are no options."""

        self._options = options

        
    def _GetModeSwitches(self, mode):
        """Return the compilation switches for the compilation 'mode'.

        'mode' -- The compilation mode (one of 'Compiler.modes').

        returns -- A sequence of strings indicating the switches that
        are used to indicate the compilation mode."""

        # Compilation is indicated by the "-c" option.
        if mode == self.MODE_COMPILE:
            return ["-S"]
        elif mode == self.MODE_ASSEMBLE:
            return ["-c"]
            
        # Other modes require no special option.
        return []
            
        

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

        self.file = file
        self.line = line
        self.column = column

        
    def __str__(self):
        """Return an information representation of this 'SourcePosition'.

        returns -- A string representing this 'SourcePosition'"""

        result = ''
        if self.file:
            result = result + '"%s"' % os.path.split(self.file)[0]
        if self.line:
            if self.file:
                result = result + ', '
            result = result + 'line %d' % self.line
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
          re.compile('^(?P<file>[^:]*):((?P<line>[^:]*):)?'
                     '(\s*(?P<column>[0-9]+):)? '
                     'warning: (?P<message>.*)$'),
        'error':
          re.compile('^(?P<file>[^:]*):((?P<line>[^:]*):)?'
                     '(\s*(?P<column>[0-9]+):)? '
                     '(?P<message>.*)$')
        }
    """A map from severities to compiled regular expressions.  If the
    regular expression matches a line in the compiler output, then that
    line indicates a diagnostic with the indicated severity."""

    _internal_error_regexp = re.compile('Internal (compiler )?error')
    """A compiled regular expression.  When an error message is matched
    by this regular expression, the error message indicates an
    internal error in the compiler."""

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
            
        
    def ParseOutput(self, output, ignore_regexps = ()):
        """Return the 'Diagnostic's indicated in the 'output'.

        'output' -- A string giving the output from the compiler.

        'ignore_regexps' -- A sequence of regular expressions.  If a
        diagnostic message matches one of these regular expressions,
        it will be ignored.
        
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
                for ignore_regexp in ignore_regexps:
                    if ignore_regexp.match(match.group()):
                        ignore = 1
                        break
                if ignore:
                    continue

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


        return diagnostics
