########################################################################
#
# File:   gcc_database.py
# Author: Mark Mitchell
# Date:   12/17/2001
#
# Contents:
#  GCCDatabase
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

from   __future__ import nested_scopes
from   compiler import *
from   compiler_test import *
import dircache
import errno
from   executable import *
import fnmatch
import glob
import os
from   qm.attachment import *
from   qm.common import *
from   qm.test.directory_suite import *
from   qm.test.database import *
from   qm.test.result import *
import re
import string
import tempfile

# See if we have thread support.
try:
    from threading import *
    _have_threads = 1
except:
    _have_threads = 0
    
########################################################################
# Classes
########################################################################

class Demangler(RedirectedExecutable):
    """A 'Demangler' demangles its standard input."""

    def __init__(self, path, dir, input):
        """Construct a new 'Demangler'.

        'path' -- The path to the demangler.

        'dir' -- The directory in which to run the demangler.
        
        'input' -- A string giving the input to be provided to the
        demangler."""

        RedirectedExecutable.__init__(self, path)
        self.__input = input
        
        
    def _WriteStdin(self):
        """Write to the standard input pipe."""

        # Write as much as we can.
        if self.__input:
            written = os.write(self._stdin_pipe[1], self.__input[:4096])
            self.__input = self.__input[written:]
            # If there's no more, close the pipe.
            if not self.__input:
                os.close(self._stdin_pipe[1])
                self._stdin_pipe = None


        
class GCCTest(CompilerTest):
    """A 'GCCTest' is a test from the GCC test suite."""

    arguments = [
        qm.fields.AttachmentField(
            name="source_file",
            title="Source File",
            description="""The source file."""),
        qm.fields.TextField(
            name="options",
            title="Options",
            description="""Compiler command-line options.""",
            default="(None)"),
    ]

    _severities = [ 'warning', 'error' ]
    """The diagnostic severities used by GCC."""

    _ignored_diagnostic_regexps = CompilerTest._ignored_diagnostic_regexps \
        + (re.compile("^.*: In (function|member|method|constructor"
                      "|instantiation|program|subroutine|block-data)"),
           re.compile("^.*: At (top level|global scope)"),
           re.compile("^collect2: ld returned .*"),
           re.compile("^Please submit.*instructions"),
           re.compile("^.*: warning -f(pic|PIC) ignored for target"),
           re.compile("^.*file path prefix .* never used"),
           re.compile("^.*linker input file unused since linking not done"),
           )
    """A sequence of regular expressions matching diagnostics to ignore."""

    def __init__(self, **arguments):
        """Construct a new 'GCCTest'."""

        apply(CompilerTest.__init__, (self,), arguments)
        # The primary source file has not yet been read.
        self._source = None
        

    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations.

        returns -- True iff and only if the test is really being run;
        false if we are running in the mode where we are generated
        expectations.""" 

        # Check to see if we are running in the special mode used
        # to generate a list of expected failures.
        if context.has_key("GCCTest.generate_xfails"):
            if self._IsExpectedToFail(context):
                result.Fail("Expected failure.")
            return 0
        else:
            CompilerTest.Run(self, context, result)
            return 1
        

    def _GetSourcePath(self):
        """Return the patch to the primary source file.

        returns -- A string giving the path to the primary source
        file."""

        return self.source_file.GetDataFile()

    
    def _GetSource(self):
        """Return the contents of the primary source file.

        returns -- A string containing the entire contents of the
        primary source file."""

        if not self._source:
            # The file has not already been read, so read it now.
            f = open(self._GetSourcePath())
            self._source = f.read()
            f.close()

        return self._source


    def _GetHostPlatform(self, context):
        """Return the tested platform.

        returns -- A string giving the GNU platform triplet for the
        platform being tested."""

        return context['GCCTest.host']


    def _GetTargetPlatform(self, context):
        """Return the tested platform.

        returns -- A string giving the GNU platform triplet for the
        platform being tested."""

        return context['GCCTest.target']


    def _GetExecutable(self):
        """Return the name of the executable to generate.

        returns -- A string giving the (relative) path to the
        executable that should be generated for this test."""

        # On DOS/Windows the executable name must end with ".exe", and
        # it is harmless to add this extension on UNIX platforms.
        base = os.path.splitext(os.path.basename(self.GetId()))[0]
        return base + ".exe"


    def _IsExpectedToFail(self, context):
        """Return true if this test is expected to fail.

        'context' -- The 'Context' in which this test is being
        executed.
        
        returns -- True iff this test is expected to fail."""

        return 0
    
    
    def _DoesTargetMatch(self, target, host, pattern):
        """Return true if 'target' matches the 'pattern'.

        'target' -- The GNU triplet for the target.

        'host' -- The GNU triplet for the host.

        'pattern' -- A glob pattern or 'native'.  If the former, the
        target must match the glob pattern to be considered a match.
        If the latter, the 'host' and 'target' must be the same."""

        if pattern == "native":
            return host == target

        return fnmatch.fnmatch(target, pattern)
    
        
    def _ParseTclWords(self, s):
        """Separate 's' into words, in the same way that Tcl would.

        's' -- A string.

        returns -- A sequence of strings, each of which is a Tcl
        word.

        Some Tcl constructs (namely variable substitution and command
        substitution) are not supported and result in exceptions.
        Invalid inputs (like the string consisting of a single quote)
        also result in exceptions.
        
        See 'Tcl and the Tk Toolkit', by John K. Ousterhout, copyright
        1994 by Addison-Wesley Publishing Company, Inc. for details
        about the syntax of Tcl."""

        # There are no words yet.
        words = []
        # There is no current word.
        word = None
        # We are not processing a double-quoted string.
        in_double_quoted_string = 0
        # Nor are we processing a brace-quoted string.
        in_brace_quoted_string = 0
        # Iterate through all of the characters in s.
        while s:
            # See what the next character is.
            c = s[0]
            # A "$" indicates variable substitution.  A "[" indicates
            # command substitution.
            if (c == "$" or c == "[") and not in_brace_quoted_string:
                raise QMException, "Unsupported Tcl substitution."
            # A double-quote indicates the beginning of a double-quoted
            # string.
            elif c == '"' and not in_brace_quoted_string:
                # We are now entering a new double-quoted string, or
                # leaving the old one.
                in_double_quoted_string = not in_double_quoted_string
                # Skip the quote.
                s = s[1:]
                # The quote starts the word.
                if word is None:
                    word = ""
            # A "{" indicates the beginning of a brace-quoted string.
            elif c == '{' and not in_double_quoted_string:
                # If that's not the opening quote, add it to the
                # string.
                if in_brace_quoted_string:
                    if word is not None:
                        word = word + "{"
                    else:
                        word = "{"
                # The quote starts the word.
                if word is None:
                    word = ""
                # We are entering a brace-quoted string.
                in_brace_quoted_string += 1
                # Skip the brace.
                s = s[1:]
            elif c == '}' and in_brace_quoted_string:
                # Leave the brace quoted string.
                in_brace_quoted_string -= 1
                # Skip the brace.
                s = s[1:]
                # If that's not the closing quote, add it to the
                # string.
                if in_brace_quoted_string:
                    if word is not None:
                        word = word + "{"
                    else:
                        word = "{"
            # A backslash-newline is translated into a space.
            elif c == '\\' and len(s) > 1 and s[1] == '\n':
                # Skip the backslash and the newline.
                s = s[2:]
                # Now, skip tabs and spaces.
                while s and (s[0] == ' ' or s[0] == '\t'):
                    s = s[1:]
                # Now prepend one space.
                s = " " + s
            # A backslash indicates backslash-substitution.
            elif c == '\\' and not in_brace_quoted_string:
                # There should be a character following the backslash.
                if len(s) == 1:
                    raise QMException, "Invalid Tcl string."
                # Skip the backslash.
                s = s[1:]
                # See what the next character is.
                c = s[0]
                # If it's a control character, use the same character
                # in Python.
                if c in ["a", "b", "f", "n", "r", "t", "v"]:
                    c = eval('"\%s"' % c)
                    s = s[1:]
                # "\x" indicates a hex literal.
                elif c == "x":
                    raise QMException, "Unsupported Tcl escape."
                # "\d" where "d" is a digit indicates an octal literal.
                elif c.isdigit():
                    raise QMException, "Unsupported Tcl escape."
                # Any other character just indicates the character
                # itself.
                else:
                    s = s[1:]
                # Add it to the current word.
                if word is not None:
                    word = word + c
                else:
                    word = c
            # A space or tab indicates a word separator.
            elif ((c == ' ' or c == '\t')
                  and not in_double_quoted_string
                  and not in_brace_quoted_string):
                # Add the current word to the list of words.
                if word is not None:
                    words.append(word)
                # Skip over the space.
                s = s[1:]
                # Keep skipping while the leading character of s is
                # a space or tab.
                while s and (s[0] == ' ' or s[0] == '\t'):
                    s = s[1:]
                # Start the next word.
                word = None
            # Any other character is just added to the current word.
            else:
                if word is not None:
                    word = word + c
                else:
                    word = c
                s = s[1:]

        # If we were working on a word when we reached the end of
        # the stirng, add it to the list.
        if word is not None:
            words.append(word)

        return words



class GPPTest(GCCTest):
    """A 'GPPTest' is a test for 'g++'."""

    _default_options = ["-ansi", "-pedantic-errors", "-Wno-long-long"]
    """A list of strings giving the options to use by default if no
    options are specified by the test."""

    _compiler = None
    """The 'Compiler' being tested."""

    _library_directories = []
    """The list of directories to search for libraries."""

    _v3_directory = None
    """The directory containing libstdc++-v3."""
    
    # If we have thread support, we must synchronize access to the class
    # variables.
    if _have_threads:
        _lock = Lock()

    
    def __init__(self, **arguments):
        """Construct a new 'GCCTest'."""

        apply(GCCTest.__init__, (self,), arguments)

        # Assume that we do not need to run the generated executable.
        self._run_executable = 0
        

    def _GetCompiler(self, context):
        """Return the 'Compiler' to use.

        'context' -- The 'Context' in which this test is being
        executed."""

        if not GPPTest._compiler:
            if _have_threads:
                self._lock.acquire()
            try:
                if GPPTest._compiler:
                    return GPPTest._compiler
                # Compute the path to the compiler.
                if context.has_key("GCCTest.prefix"):
                    path = os.path.join(context["GCCTest.prefix"],
                                        "bin", "g++")
                else:
                    path = context["GPPTest.gpp"]
                # There are no compiler options yet.
                options = []
                # Make error messages easier to parse.
                options.append('-fmessage-length=0')
                # See if there are any compiler options specified in the
                # context.
                options += string.split(context.get("GCCTest.flags", ""))
                options += string.split(context.get("GPPTest.flags", ""))

                # Create the 'Compiler'.
                compiler = GPP(path, options)

                # Get the base of the objdir; the libraries can be found
                # relative to that.
                objdir = context['GCCTest.objdir']
                # Run the compiler to find out what multilib directory is
                # in use.
                executable = CompilerExecutable(compiler)
                executable.Run([compiler.GetPath()] + compiler.GetOptions() 
                               + ['--print-multi-dir'])
                directory = executable.stdout[:-1]
                # Add the V3 library directory.
                self._v3_directory \
                    = os.path.join(objdir,
                                   self._GetTargetPlatform(context),
                                   directory,
                                   "libstdc++-v3")
                GPPTest._library_directories.append(os.path.join
                                                    (self._v3_directory,
                                                     "src", ".libs"))
                # Add the directory containing libgcc.
                GPPTest._library_directories.append(os.path.join(objdir, "gcc",
                                                                 directory))
                # Add -L options for all the directories we should search
                # for libraries.
                for d in GPPTest._library_directories:
                    options.append("-L" + d)
                
                # Run a script to findout what flags to use when compiling
                # for the V3 library.
                executable = \
                    RedirectedExecutable(os.path.join(self._v3_directory,
                                                      "testsuite_flags"))
                executable.Run(["testsuite_flags", "--build-includes"])
                options += string.split(executable.stdout)
                compiler.SetOptions(options)
                
                GPPTest._compiler = compiler
            finally:
                if _have_threads:
                    self._lock.release()
                    
        return GPPTest._compiler

        
    def _GetLibraryDirectories(self, context):
        """Returns the directories to search for libraries.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        returns -- A sequence of strings giving the paths to the
        directories to search for libraries."""

        # Make sure that the compiler exists; initializing it creates
        # _library_directories.
        self._GetCompiler(context)
        
        return GPPTest._library_directories

    
    def _GetCompilationOptions(self, contents):
        """Return the options to given the indicated test 'contents'.

        'contents' -- A string giving the body of the test.

        returns -- A list of strings giving the options to pass to the
        compiler when compiling the test."""
        
        # See what compiler options are specified by the test.
        match = self._options_regexp.search(contents)
        if match:
            return string.split(match.group("options"))

        if self.options != "(None)":
            return string.split(self.options)

        return self._default_options


    def _IsExecutionRequired(self):
        """Returns true if the generated executable should be run.

        returns -- True if the generated executable should be run."""

        return self._run_executable
    

    
class OldDejaGNUTest(GPPTest):
    """An 'OldDejaGNUTest' is a test using the 'old-dejagnu' driver."""

    _additional_source_files_regexp \
        = re.compile("Additional sources:\s*(?P<source_files>.*)\s*")
    """A compiled regular expression.  When this expression matches
    part of the input file, the 'source_files' match group indicates
    additional source files that should be compiled along with the
    main source file."""

    _diagnostic_regexps = {
        'warning' : re.compile('WARNING - '),
        'error' : re.compile('ERROR - ')
    }
    """A map from severities (strings) to regular expressions.  If the
    regular expression matches a portion of a line, then that line
    indicates that a diagnostic with the indicated severity is
    expected there."""
    
    _line_regexp = re.compile("LINE (?P<line>[0-9]+)")
    """A compiled regular expression.  If a diagnostic specification
    matches this regular expression, then the 'line' match group gives
    the line number at which the diagnostic is expected."""
        
    _options_regexp = re.compile("Special.*Options:(?P<options>.*)")
    """A compiled regular expression.  When this expression matches
    part of the input file, the 'options' match group indicates
    compiler options that should be used instead of
    '_default_options'."""

    _skip_regexp = re.compile("Skip if not target:\s*(?P<platforms>.*)\s*")
    """A compiled regular expression.  When this expression matches
    part of the input file, the 'platforms' match group indicates 
    GNU platform triplets patterns for which the test should be skipped."""

    _xfail_regexp = re.compile("XFAIL([ \t]+(?P<platforms>.*))?[ \t]*$", re.M)
    """A compiled regular expression.  When this expression matches
    part of the input file, the 'platforms' match group indicates GNU
    platform tripletsfor which the test is expected to fail."""

    _ignored_diagnostic_regexps = GPPTest._ignored_diagnostic_regexps \
        + (re.compile('^.*: In (.*function|method|.*structor)'),
           re.compile('^.*: In instantiation of'),
           re.compile('^.*:   instantiated from'),
           re.compile('^.*: At (top level|global scope)'),
           re.compile('^.*file path prefix .* never used'),
           re.compile('^.*linker input file unused since linking not done'),
           re.compile('^collect: re(compiling|linking)'),
           re.compile('^collect2: ld returned.*'),
           )
    """A sequence of regular expressions matching diagnostics to ignore."""
    
    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        # Get the contents of the test.
        contents = self._GetSource()

        # Find the current host and target platforms.
        self._host = self._GetHostPlatform(context)
        self._target = self._GetTargetPlatform(context)
        
        # See if it is supposed to be run on the current platform.
        match = self._skip_regexp.search(contents)
        if match:
            # Get the list of patterns corresponding to platforms to
            # skip.
            skip_platforms = string.split(match.group('platforms'))
            # Assume that we should skip the test.
            skip = 1
            # See if any of them match the current platform.
            for sp in skip_platforms:
                if self._DoesTargetMatch(self._target, self._host, sp):
                    skip = 0
                    break

            if skip:
                result.SetOutcome(Result.UNTESTED)
                result[Result.CAUSE] = "Test skipped on %s." % self._target
                result["GCCTest.supported_targets"] \
                    = string.join(skip_platforms)
                return

        # So that we are thread safe, all work is done in a directory
        # corresponding to this test.
        self._MakeDirectoryForTest()
        # Run the test.
        GCCTest.Run(self, context, result)
        # Remove the temporary directory.
        self._RemoveDirectoryForTest(result)


    def _IsExpectedToFail(self, context):
        """Return true if this test is expected to fail.

        'context' -- The 'Context' in which this test is being
        executed.

        returns -- True iff this test is expected to fail."""

        # Get the contents of the source file.
        contents = self._GetSource()
        # See if the test is expected to fail on this target.
        pos = 0
        # Go through the source file looking for XFAIL lines.
        while 1:
            # See if there's an XFAIL line.
            match = self._xfail_regexp.search(contents, pos)
            # If not, we're done.
            if not match:
                return 0
            # See on what platforms failure is expected.
            platforms = match.group("platforms")
            # If there are no platforms, the test is expected to fail
            # everywhere.
            if platforms is None or not platforms.split():
                return 1
            # Get the variout platforms.
            platforms = platforms.split()
            # See if any of them match the current platform.
            for p in platforms:
                if self._DoesTargetMatch(self._target, self._host, p):
                    return 1
            # Look for the next occurrence.
            pos = match.end()
                
        
    def _GetCompilationSteps(self):
        """Return the compilation steps for this test.

        returns -- A sequence of 'CompilationStep' objects."""

        # Get the path to the primary source file.
        path = self.source_file.GetDataFile()
        
        # Get the contents of the source file.
        contents = self._GetSource()
        
        # Construct the set of source files.
        source_files = [path]
        match = self._additional_source_files_regexp.search(contents)
        if match:
            for sf in string.split(match.group("source_files")):
                source_files.append(os.path.join(os.path.dirname(path), sf))

        # Scan the source file for expected diagnostics.
        diagnostics = self._GetExpectedDiagnostics(path, contents)

        # See what compiler options are specified by the test.
        options = self._GetCompilationOptions(contents)
        
        # There are no compilation steps yet.
        steps = []

        # Figure out what kind of action to take with the source files.
        if string.find(contents, "Build don't link:") != -1:
            # Compile the source files, but do not link them.
            step = CompilationStep(Compiler.MODE_ASSEMBLE,
                                   source_files,
                                   options,
                                   None,
                                   diagnostics)
            steps.append(step)
        elif string.find(contents, "Build don't run:") != -1:
            # Compile and link the source files, but do not run them.
            step = CompilationStep(Compiler.MODE_LINK,
                                   source_files,
                                   options,
                                   self._GetExecutable(),
                                   diagnostics)
            steps.append(step)
        elif string.find(contents, "Build then link:") != -1:
            # Compile the source files. 
            step = CompilationStep(Compiler.MODE_ASSEMBLE,
                                   source_files,
                                   options,
                                   None,
                                   diagnostics)
            steps.append(step)
            # Link the resulting object files together.
            object_files \
                = map(lambda s: \
                          os.path.splitext(os.path.split(s)[1])[0] + ".o",
                      source_files)
            step = CompilationStep(Compiler.MODE_LINK,
                                   object_files,
                                   options,
                                   self._GetExecutable(),
                                   [])
            steps.append(step)
        else:
            # Compile, link, and run the program.
            step = CompilationStep(Compiler.MODE_LINK,
                                   source_files,
                                   options,
                                   self._GetExecutable(),
                                   diagnostics)
            steps.append(step)
            # Run the program, unless errors or warnings are
            # expected.  (It is unclear why DejaGNU tests should not
            # be run if a *warning* occurs, but they are not.)
            if diagnostics:
                self._run_executable = 0
            else:
                self._run_executable = 1

        return steps


    def _GetExpectedDiagnostics(self, file_name, contents):
        """Scan 'contents' for expected diagnostics.

        'file_name' -- The name of the file.
        
        'contents' -- The contents of the file.

        returns -- A list of 'Diagnostic' instances giving the
        diagnostic messages expected by the 'contents'."""

        # There are no diagnostics yet.
        expected_diagnostics = []
        # Open the source file.
        f = StringIO.StringIO(contents)
        # The first line is line 1.
        line_number = 1
        # Read all of the lines from the file.
        for line in f.readlines():
            # See if this line matches any of the regular expressions
            # that indicate a diagnostic.
            for severity in self._severities:
                match = self._diagnostic_regexps[severity].search(line)
                # If there was a match, then there is a new expected
                # diagnostic on this line.
                if match:
                    # Figure out at what line this diagnostic is
                    # expected.
                    line_match = self._line_regexp.search(line)
                    if line_match:
                        expected_line = int(line_match.group('line'))
                    else:
                        expected_line = line_number
                    # Create the source position for the diagnostic.
                    # The DejaGNU driver ignores the file name.
                    source_position \
                        = SourcePosition(None, expected_line, 0)
                    # Create a Diagnostic.  Oddly, the DejaGNU driver
                    # ignores the severity completely.
                    diagnostic = Diagnostic(source_position, None, None)
                    # Add it to the list.
                    expected_diagnostics.append(diagnostic)
            # We have read one more line.
            line_number = line_number + 1
        # Close the file.
        f.close()

        return expected_diagnostics


    
class DGTest(GPPTest):
    """A 'DGTest' is a test using the 'dg' test driver."""

    _dg_command_regexp \
         = re.compile(r'{\s+dg-(?P<command>[-a-z]+)\s+'
                      r'(?P<arguments>.*)\s+}[^}]*$')
    """A compiled regular expression that matches lines in the input
    source file that indicate DejaGNU commands.  The 'command' match
    group indicates the name of the command (without the 'dg-'
    prefix), while the 'arguments' match group gives any arguments
    to the command, as a single string."""

    _line_count_regexp \
         = re.compile(r'^ *(?P<actual>[0-9]+).*count\((?P<expected>[0-9]+)\)')
    """A compiled regular expression that maches lines in gcov output
    that indicate line number execution counts."""

    _branch_start_regexp = re.compile(r'branch\((?P<probs>[0-9 ]+)\)')
    """A compiled regulard expression that matches the start of a
    branch probability group."""

    _branch_end_regexp = re.compile(r'branch\(end\)')
    """A compiled regulard expression that matches the end of a
    branch probability group."""
         
    _branch_regexp \
        = re.compile(r'branch [0-9]+ taken = (?P<prob>-?[0-9]+)%')
    """A compiled regular expression that matches a branch probability line."""
    
    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        # Get the contents of the source file.
        contents = self._GetSource()
        # Figure out on what target the test is running.
        target = self._GetTargetPlatform(context)
        # Process all the commands therein.
        self._ProcessCommands(contents, target,
                              self._GetHostPlatform(context))

        # Perhaps the test is not meant to be run on this platform.
        if self._mode is None:
            result.SetOutcome(Result.UNTESTED)
            result[Result.CAUSE] = "Test skipped on %s." % target
            return

        # So that we are thread safe, all work is done in a directory
        # corresponding to this test.
        self._MakeDirectoryForTest()
        # If checking coverage information, make sure there are no
        # stale coverage files around.
        if self._check_coverage:
            for f in glob.glob(os.path.join(self._GetDirectoryForTest(),
                                            "*.da")):
                os.remove(f)

        # Run the test.
        if not GCCTest.Run(self, context, result):
            return

        # If the test isn't passing at this point, there's no point in
        # doing additional work.
        if result.GetOutcome() != Result.PASS:
            return

        # See if there are assembly patterns for which to look.
        if (self._assembly_patterns
            or self._demangled_assembly_patterns
            or self._forbidden_assembly_patterns
            or self._forbidden_demangled_assembly_patterns):
            # Get the basename for the source file.
            file_name \
                = os.path.split(self.source_file.GetDataFile())[1]
            # Get the assembly file in which we are supposed to look.
            file_name = os.path.join(self._GetDirectoryForTest(),
                                     os.path.splitext(file_name)[0] + ".s")
            # Read the contents of the file.
            file = open(file_name)
            asm_contents = file.read()
            file.close()

            # See if all the desired patterns are there.
            for p in self._assembly_patterns:
                if not re.search(p, asm_contents):
                    result.Fail("Assembly file does not contain '%s'."
                                % p,
                                { "DGTest.pattern" : p })
                    return

            # Make sure that the forbidden patterns are not there.
            for p in self._forbidden_assembly_patterns:
                if re.search(p, asm_contents):
                    result.Fail("Assembly file contains '%s'." % p,
                                { "DGTest.pattern" : p})

            # If we have to demangle the contents, do it.
            if (self._demangled_assembly_patterns
                or self._forbidden_demangled_assembly_patterns):
                demangler = Demangler(context["DGTest.demangler"],
                                      self._GetDirectoryForTest(),
                                      asm_contents)
                demangler.Run([demangler.GetPath()])
                asm_contents = demangler.stdout

            # See if all the patterns are there.
            for p in self._demangled_assembly_patterns:
                if not re.search(p, asm_contents):
                    result.Fail("Assembly file does not contain '%s'."
                                % p,
                                { "DGTest.pattern" : p })
                    return

            # Make sure that the forbidden patterns are not there.
            for p in self._forbidden_demangled_assembly_patterns:
                if re.search(p, asm_contents):
                    result.Fail("Assembly file contains '%s'." % p,
                                { "DGTest.pattern" : p})

        # Check the coverage data.
        self._CheckCoverage(context, result)
        # Remove the temporary directory.
        self._RemoveDirectoryForTest(result)
        

    def _GetCompilationSteps(self):
        """Return the compilation steps for this test.

        returns -- A sequence of 'CompilationStep' objects."""

        # Get the path to the primary source file.
        path = self.source_file.GetDataFile()
        
        # Get the contents of the source file.
        contents = self._GetSource()

        # There is only one source file.
        source_files = [path] + self._GetAdditionalSourceFiles(path)
        
        # Get the diagnostics expected for this test.
        diagnostics = self._expected_diagnostics
        
        # See what compiler options are specified by the test.
        options = self._GetCompilationOptions(contents)

        # There are no compilation steps yet.
        steps = []

        # Some modes are not yet implemented.
        if self._mode == "preprocess":
            raise "Not implemented."
        elif self._mode == "compile":
            # Compile the source files, but do not link them.
            step = CompilationStep(Compiler.MODE_COMPILE,
                                   source_files,
                                   options,
                                   None,
                                   diagnostics)
            steps.append(step)
        elif self._mode == "assemble":
            # Compile the source files, but do not link them.
            step = CompilationStep(Compiler.MODE_ASSEMBLE,
                                   source_files,
                                   options,
                                   None,
                                   diagnostics)
            steps.append(step)
        elif self._mode == "link" or self._mode == "run":
            # Compile the source files, but do not link them.
            step = CompilationStep(Compiler.MODE_LINK,
                                   source_files,
                                   options,
                                   self._GetExecutable(),
                                   diagnostics)
            steps.append(step)
            # If the mode is "run" remember that.
            if self._mode == "run":
                self._run_executable = 1

        return steps

    
    def _GetCompilationOptions(self, contents):
        """Return the options to given the indicated test 'contents'.

        'contents' -- A string giving the body of the test.

        returns -- A list of strings giving the options to pass to the
        compiler when compiling the test."""
        
        # See what compiler options are specified by the test.
        return self._options


    def _GetAdditionalSourceFiles(self, path):
        """Return source files to be included other than the primary
        source file.

        'path' -- The path to the primary source file.

        returns -- A list of strings giving the names of additional
        source files."""

        return []
    
        
    def _ParseSelector(self, selector):
        """Return the target indicated by the 'selector'.

        'selector' -- A target/xfail selector in the form specified by
        'dg.exp'.

        returns -- A pair '(kind, patterns)' where 'kind' is either
        'xfail' or 'target', and 'patterns' is a sequence of strings
        giving the target patterns indicated by the selector."""

        # Split the selector into words.
        words = selector.split()
        # If the first word is not "target", that's a problem.
        if words[0] != "target" and words[0] != "xfail":
            raise QMException, "Invalid selector."
        # All the rest of the words are patterns.
        return (words[0], words[1:])
        
        
    def _CheckSelector(self, selector, target, host):
        """Return the target indicated by the 'selector'.

        'selector' -- A target/xfail selector in the form specified by
        'dg.exp'.

        'target' -- The GNU triplet for the target.

        'host' -- The GNU triplet for the host.

        returns -- A pair '(kind, is_matched)' where 'kind' is either
        'xfail' or 'target', and 'is_matched' is true iff the current
        'host' and 'target' match any of the patterns specified."""

        # Parse the selector.
        (kind, patterns) = self._ParseSelector(selector)
        # Assume none of the patterns match.
        is_matched = 0
        # Go through each of the patterns.
        for p in patterns:
            if self._DoesTargetMatch(target, host, p):
                is_matched = 1
                break

        return (kind, is_matched)
    
        
    def _ProcessCommands(self, contents, target, host):
        """Process any 'dg-' commands in the 'contents'.

        'contents' -- A string giving the body of the test.

        'target' -- The GNU triplet for the target.

        'host' -- The GNU triplet for the host.

        See 'dg.exp' in the DejaGNU distribution for the Tcl code that
        this code emulates."""

        # Assume that only compilation is required.
        self._mode = "compile"
        # And that the default options should be used.
        if self.options != "(None)":
            self._options = []
        else:
            self._options = self._default_options
        # And there are no patterns that we need to find in the .s
        # file.
        self._assembly_patterns = []
        self._demangled_assembly_patterns = []
        self._forbidden_assembly_patterns = []
        self._forbidden_demangled_assembly_patterns = []
        # And there is no coverage testing.
        self._check_coverage = 0
        self._check_branches = 0
        self._check_calls = 0
        self._coverage_arguments = []
        # And there are no expected diagnostics.
        self._expected_diagnostics = []
        # And the test is not expected to fail.
        self._is_expected_to_fail = 0

        # Create a file-like object to run through the contents.
        f = StringIO.StringIO(contents)
        # Keep track of the current line.
        line_number = 0
        # Iterate through all the lines.
        for line in f.readlines():
            # Increment the line number.
            line_number += 1
            # See if this line indicates a dg-command.
            match = self._dg_command_regexp.search(line)
            # If not, skip forward to the next line.
            if not match:
                continue
            # If it did match, process the command.
            command = match.group('command')
            arguments = match.group('arguments')
            # The arguments are given as a string, but they need to be
            # separated into Tcl words.
            arguments = self._ParseTclWords(arguments)

            if command == "do":
                if len(arguments) > 2 or len(arguments) < 1:
                    raise QMException, "Incorrect usage of dg-do."
                if len(arguments) == 2:
                    # Parse the selector.
                    (kind, is_matched) \
                        = self._CheckSelector(arguments[1], target, host)
                    # If it's a target selector, we may not want to
                    # run this test at all.
                    if kind == "target" and not is_matched:
                        self._mode = None
                    # Otherwise, it may indicate an expected failure.
                    elif kind == "xfail" and is_matched:
                        self._is_expected_to_fail = 1
                    else:
                        self._mode = arguments[0]
                else:
                    self._mode = arguments[0]
            elif command == "options":
                if len(arguments) < 1 or len(arguments) > 2:
                    raise QMException, "Incorrect usage of dg-options."
                # If there is a target selector, these options may not
                # apply on this target.
                if len(arguments) == 2:
                    (kind, is_matched) \
                        = self._CheckSelector(arguments[1], target, host)
                    if kind == "target" and not is_matched:
                        continue
                # The options are those specified by the first argument.    
                self._options = string.split(arguments[0])
            elif command == "final":
                if len(arguments) != 1:
                    raise QMException, "Incorrect usage of dg-final."
                # The argument is itself a Tcl command.
                words = self._ParseTclWords(arguments[0])
                # If there are no words, the command was invalid.
                if not words:
                    raise QMException, "Incorrect usage of dg-final."
                # The command is the first word.
                command = words[0]
                # The arguments are the remainder.
                arguments = words[1:]
                # See if it's an assembly-scanning command. 
                if (command == "scan-assembler"
                    or command == "scan-assembler-dem"
                    or command == "scan-assembler-not"
                    or command == "scan-assembler-dem-not"):
                    if len(arguments) != 1:
                        raise QMException, "Incorrect usage of %s." % command
                    pattern = arguments[0]
                    if command == "scan-assembler":
                        self._assembly_patterns.append(pattern)
                    elif command == "scan-assembler-dem":
                        self._demangled_assembly_patterns.append(pattern)
                    elif command == "scan-assembler-not":
                        self._forbidden_assembly_patterns.append(pattern)
                    elif command == "scan-assembler-dem-not":
                        self._forbidden_demangled_assembly_patterns.append(
                            pattern)
                elif command == "run-gcov":
                    self._check_coverage = 1
                    self._coverage_arguments = arguments
                    # Load the .x file -- if present.
                    x_file = (os.path.splitext(self._GetSourcePath())[0]
                              + ".x")
                    try:
                        x_contents = open(x_file).read()
                        if x_file.find("xfail") != -1:
                            self._is_expected_to_fail = 1
                        if x_file.find("gcov_verify_branches") != -1:
                            self._check_branches = 1
                        if x_file.find("gcov_verify_calls") != -1:
                            self._check_calls = 1
                    except:
                        pass
                else:
                    raise QMException, \
                          "Unsupported dg-final command '%s'" % command
            elif (command == "warning" or command == "error"
                  or command == "bogus"):
                if len(arguments) > 4 or len(arguments) < 1:
                    raise QMException, "Incorrect usage of dg-%s" % command
                # See if there is a target selector.
                if len(arguments) >= 3:
                    # See if the selector matches.
                    (kind, is_matched) \
                        = self._CheckSelector(arguments[2], target, host)
                    # This diagnostic may not apply on this target.
                    if kind == "target" and not is_matched:
                        continue
                    elif kind == "xfail" and is_matched:
                        self._is_expected_to_fail = 1
                # The dg-bogus command indicates an error message that
                # should not occur.  There is no explicit support for
                # that in our test classes; all unexpected diagnostics
                # cause failure.  However, an dg-bogus command with an
                # expectd failure indicator means that the test is
                # expected to fail.
                if command == "bogus":
                    continue
                # Figure out what line number to use.
                if len(arguments) == 4:
                    ln = arguments[3]
                    if ln == ".":
                        ln = line_number
                    elif ln == "0":
                        ln = 0
                    else:
                        ln = int(ln)
                else:
                    ln = line_number
                # Create the diagnostic.  The DejaGNU driver ignores
                # the severity.
                diagnostic = Diagnostic(SourcePosition(None, ln, 0),
                                        None,
                                        arguments[0])
                # Add it to the list.
                self._expected_diagnostics.append(diagnostic)
            else:
                raise QMException, "Unsupported command 'dg-%s'." % command

        # Add options from the multi-option directory case to the list
        # of options.
        if self.options != "(None)":
            self._options = self._options + string.split(self.options)


    def _IsExpectedToFail(self, context):
        """Return true if this test is expected to fail.

        'context' -- The 'Context' in which this test is being
        executed.

        returns -- True iff this test is expected to fail."""
        
        return self._is_expected_to_fail


    def _CheckCoverage(self, context, result):
        """Run 'gcov' and examine the results.

        'result' -- The 'Result' object to update."""

        if not self._check_coverage:
            return

        # Run "gcov".
        gcov = RedirectedExecutable(context.get("GCCTest.gcov", "gcov"),
                                    self._GetDirectoryForTest())
        status = gcov.Run(["gcov"] + self._coverage_arguments)
        prefix = self._GetAnnotationPrefix() + "gcov_"
        if not self._CheckStatus(result, prefix, "Coverage tool", status):
            return

        # Get the contents of the gcov output file.
        filename = os.path.join(self._GetDirectoryForTest(),
                                self._coverage_arguments[-1] + ".gcov")
        lines = open(filename).readlines()
        
        # Check line execution counts.
        line_number = 0
        for line in lines:
            line_number += 1
            match = self._line_count_regexp.match(line)
            if not match:
                continue
            actual = match.group("actual")
            expected = match.group("expected")

            if actual != expected:
                result.Fail("Incorrect line count for line %d." % line_number)
                result[prefix + "actual"] = actual
                result[prefix + "expected"] = expected
                return

        if self._CheckBranches(result, lines):
            return
        
        if self._check_calls:
            raise QMException, "Checking call results is unsupported."
        
            
    def _CheckBranches(self, result, lines):
        """Check that the branch probabilities are correct.

        'result' -- The 'Result' to update.

        'lines' -- A sequence of lines from the gcov output.

        returns -- False if the test failed."""

        if not self._check_branches:
            return 1
        
        prefix = self._GetAnnotationPrefix() + "gcov_"
        branch_line = 0
        expected_probs = []
        line_number = 0
        for line in lines:
            line_number += 1
            check_no_remaining_probs = 0
            match = self._branch_end_regexp.match(line)
            if match:
                check_no_remaining_probs = 1
                remaining_probs = expected_probs

            match = self._branch_start_regexp.match(line)
            if match:
                # If there are branches that we have not seen, fail.
                check_no_remaining_probs = 1
                remaining_probs = expected_probs
                expected_probs = map(lambda s : int(s),
                                     string.split(match.group("probs")))
                # Normalize all probabilities into the range 0 - 50.
                expected_probs = map(lambda p : ((p < 50) and p) or (100 - p),
                                     expected_probs)

            match = self._branch_regexp.match(line)
            if match:
                prob = int(match.group("prob"))
                if prob < 0 or prob > 100:
                    result.Fail("Invalid branch probability at line %d."
                                % line_number)
                    result[prefix + "probability"] = prob
                    # Normalize all probabilities into the range 0 - 50.
                    if prob > 50:
                        prob = 100 - prob
                        # It's OK if some branch probabilities are not
                        # listed.  
                        if prob in expected_probs:
                            expected_probs.remove(prob)

            if check_no_remaining_probs and remaining_probs:
                # If there are branches that we have not seen, fail.
                result.Fail("Missing branch probabilities for line %d."
                            % branch_line)
                result[prefix + "missing_probabilities"] \
                              = string.join(map(lambda i : str(i),
                                                remaining_probs))
                return 0

        return 1


                    
class InitPriorityTest(DGTest):
    """An 'InitPriorityTest' tests the 'init_priority' attribute."""

    def _IsExpectedToFail(self, context):
        """Return true if this test is expected to fail.

        'context' -- The 'Context' in which this test is being
        executed.

        returns -- True iff this test is expected to fail."""

        # The test is expected to fail if the compiler does not
        # understand the 'init_priority' attribute.  Create a
        # temporary file to test that.  We make five attempts at
        # creating the temporary file since there is a race condition
        # between the time that we get the filename and the time that
        # we get the file itself.
        for i in range(5):
            filename = tempfile.mktemp(".cpp")
            try:
                file = open(filename, "w")
            except EnvironmentError, e:
                if e.errno == errno.EEXIST:
                    continue
        # Create the contents of the file.
        try:
            file.write("struct S{};\n"
                       "S s __attribute__((init_priority(5000)));\n")
            file.close()
            # Compile the file.
            compiler = self._GetCompiler(context)
            output = compiler.Compile(Compiler.MODE_COMPILE, [filename],
                                      self._GetDirectoryForTest())[1]
            # If there are any diagnostics, the compiler does not
            # understand the attribute.
            if (compiler.ParseOutput(output)):
                return 1
            else:
                return 0
        finally:
            os.remove(filename)

        
    def _GetAdditionalSourceFiles(self, path):
        """Return source files to be included other than the primary
        source file.

        'path' -- The path to the primary source file.
        
        returns -- A list of strings giving the names of additional
        source files."""

        files = []
        
        if self.GetId() == "g++.dg/special/conpr-2.C":
            files = ["conpr-2a.C"]
        elif self.GetId() == "g++.dg/special/conpr-3.C":
            files = ["conpr-3a.C", "conpr-3b.C"]
        elif self.GetId() == "g++.dg/special/conpr-3r.C":
            files = ["conpr-3b.C", "conpr-3a.C"]

        return map(lambda f, p=path: os.path.join(os.path.split(p)[0], f),
                   files)



class GPPBprobTest(GPPTest):
    """A 'GPPBranchProbTest' is a G++ test for branch probabilities."""

    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        self._MakeDirectoryForTest()
        # Remove any stale profiling files.
        for f in glob.glob(os.path.join(self._GetDirectoryForTest(),
                                        "*.da")):
            os.remove(f)

        compiler = self._GetCompiler(context)
        path = self.source_file.GetDataFile()
        options = string.split(self.options)

        # Build the test with "-fprofile-arcs"
        base = os.path.basename(self.GetId())
        base = os.path.splitext(base)[0]
        profiled_exe_path = os.path.join(".", base + "1.exe")
        (status, output, command) \
            = compiler.Compile(Compiler.MODE_LINK,
                               [path],
                               self._GetDirectoryForTest(),
                               options + ["-fprofile-arcs"],
                               profiled_exe_path)
        prefix = self._GetAnnotationPrefix() + "profile_arcs_"
        result[prefix + "output"] = output
        result[prefix + "command"] = string.join(command)
        if not self._CheckStatus(result, prefix, "Compiler", status):
            return

        # Run the program.
        executable = \
            CompiledExecutable(profiled_exe_path,
                               self._GetDirectoryForTest(),
                               self._GetLibraryDirectories(context),
                               context.get("CompilerTest.interpreter"))
        status = executable.Run([profiled_exe_path])
        prefix = self._GetAnnotationPrefix() + "execution_"
        if not self._CheckStatus(result, prefix, "Executable", status):
            return

        # Build the test with "-fbranch-probabilities"
        profiled_exe_path = os.path.join(".", base + "2.exe")
        (status, output, command) \
            = compiler.Compile(Compiler.MODE_LINK,
                               [path],
                               self._GetDirectoryForTest(),
                               options + ["-fbranch-probabilities"],
                               profiled_exe_path)
        prefix = self._GetAnnotationPrefix() + "branch_probs_"
        result[prefix + "output"] = output
        result[prefix + "command"] = string.join(command)
        self._CheckStatus(result, prefix, "Compiler", status)

        # Remove the temporary directory.
        self._RemoveDirectoryForTest(result)
        
    
class GCCDatabase(Database):
    """A 'GCCDatabase' is a G++ test database."""

    class InvalidTestNameException(QMException):
        """An 'InvalidTestNameException' indicates an invalid test name.

        Not all possible test names are valid names of GCC tests; in
        particular all GCC tests must be contained within
        subdirectories of the GCC testsuite hierarchy."""

        def __init__(self, test_id):
            """Construct a new 'InvalidTestNameException'.

            'test_id' -- The invalid test name."""

            self.test_id = test_id

    _test_extension = ".C"
    """The extension (including the leading period) that indicates
    that a file is a test."""

    _prefix_map = (
        ("g++.old-deja/",  "gcc_database.OldDejaGNUTest"),
        ("g++.dg/bprob/", "gcc_database.GPPBprobTest"),
        ("g++.dg/special/", "gcc_database.InitPriorityTest"),
        ("g++.dg/", "gcc_database.DGTest"),
    )
    """A sequence whose elements are of the form '(prefix,
    classname)'.  If first part of a test name matches the prefix,
    the corresponding test class is used to run that test."""

    _subdirectories = {
        "" : ["g++.dg", "g++.old-deja"],
    }
    """A map from directory names (as absolute labels) to lists of
    relative labels.  The relative labels give the subdirectories for
    the directory."""
    
    _extra_subdirectories = {
        "g++.dg" : ["special"],
    }
    """A map from directory names (as absolute labels) to lists of
    relative labels.  The relative labels give additional
    subdirectories that cannot be found by the default method."""

    _suite_predicates = (
        ("g++.old-deja", "_IsOldDejaSuite"),
        ("g++.dg/bprob", "_IsMultioptionSuite"),
        ("g++.dg/debug", "_IsMultioptionSuite"),
        ("g++.dg", "_IsGPPDGSuite"),
    )
    """A sequence of pairs '(label, function)'.  When determining
    whether a file is a suite, we call the 'function' corresponding to
    the first 'label' that is a prefix of the directory containing the
    file, passing it 'self', the directory, and the file name.  If the
    'function' returns true, the file is considered to be a contained
    suite and the value returned to be the label for the suite.  If
    the directory does not match any of the labels, the file is not
    considered a suite.  The 'function' is represented by a string;
    the string must correspond to a method of 'GCCDatabase'."""

    _suite_prefixes = (
        ("g++.old-deja", "g++."),
    )
    """A sequence of pairs '(dir_prefix, suite_prefix)'.  If a
    directory label matches the 'dir_prefix', then file system
    directory giving labels within the directory are formed by
    prefixing the suite name with the 'suite_prefix'."""
    
    _tests_in_directory = {
        "g++.dg/special" : ["conpr-1.C", "conpr-2.C", "conpr-3.C",
                            "conpr-3r.C", "initp1.C"],
    }
    """A map from directory names (as absolute labels) to lists of
    relative labels.  The relative labels give the tests present in
    that directory.  If there is no entry in this map, then the file
    system is searched for appropriate source files."""

    _multioption_directories = (
        "g++.dg/bprob",
        "g++.dg/debug",
    )
    """A sequence of directory labels.  These directories contain
    test files, but each test is supposed to be run with multiple
    compiler options.  Therefore, the test is considered a
    subdirectory; the subdirectory will contain variants of the test
    corresponding to each of the sets of compiler options."""

    def __init__(self, path, **attributes):
        """Construct a 'GPPDatabase'.

        'path' -- A string containing the absolute path to the directory
        containing the database.

        'attributes' -- A dictionary mapping attribute names to
        values.  These values will be stored in the instance
        dictionary as fields."""

        # If there is a testsuite_root attribute, use that as the
        # root of the testsuite.  Otherwise, use the path.
        self.__testsuite_root \
            = attributes.get("GCCDatabase.testsuite_root", path)
        self._debug_options = []
        for opt in string.split(attributes.get("GCCDatabase.debug_options",
                                               "-g")):
            for level in ("1", "", "3"):
                self._debug_options.append((opt + level,))
                self._debug_options.append((opt + level, "-O2"))
                self._debug_options.append((opt + level, "-O3"))

        # Use FileLabels for this test class.
        attributes[self.ATT_LABEL_CLASS] = "file_label.FileLabel"
        # Call the base class constructor.
        apply(Database.__init__, (self, path), attributes)
        # Create an attachment store for the database.
        self.__store = FileAttachmentStore(self)
        
    # Methods that deal with tests.

    def GetTestIds(self, directory=".", scan_subdirs=1):
        """Return all test IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all tests located within 'directory',
        as absolute labels."""
        
        # Look for special tests.
        test_names = self._tests_in_directory.get(directory, [])
        # If there is a special list, return it.
        if test_names:
            return map(lambda n: self.JoinLabels(directory, n),
                       test_names)

        # Handle directories that corresponnd to tests that are run
        # with multiple options.
        (parent, base) = self.SplitLabel(directory)
        if parent in self._multioption_directories:
            for x in range(len(self._GetMultipleOptions(parent))):
                test_names.append(self.JoinLabels(directory,
                                                  base + ("_%d" % x)))
            return test_names

        # Compute the path name of the directory in which to start.
        path = self._GetPathFromDirectory(directory)
        
        # Add the files from this directory.
        if directory not in self._multioption_directories:
            for n in self._GetTestFilesInDirectory(path):
                test_names.append(self.JoinLabels(directory, n))

        # If requested, iterate through all of the subdirectories.
        if scan_subdirs:
            for subdirectory in self.GetSubdirectories(directory):
                # Compute the absolute name of the subdirectory.
                absolute = self.JoinLabels(directory, subdirectory)
                # Recurse on the subdirectory.
                test_names.extend(self.GetTestIds(absolute, 1))

        return test_names
                

    def GetTest(self, test_id):
        """Return the 'TestDescriptor' for the test named 'test_id'.

        'test_id' -- A label naming the test.

        returns -- A 'TestDescriptor' corresponding to 'test_id'.
        
        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'."""

        # Compute the path to the primary source file.
        path = self._GetTestPath(test_id)
        # If the file does not exist, then there is no such test.
        if not os.path.exists(path):
            raise NoSuchTestError, test_id
        
        # Construct the attachment for the primary source file.
        basename = os.path.basename(path)
        attachment = Attachment("text/plain", basename,
                                basename, path,
                                self.GetAttachmentStore())
        # Get the test class associated with this test.
        test_class = self._GetTestClass(test_id)

        directory, base  = self.SplitLabel(test_id)
        parent = self.LabelDirname(directory)
        if parent in self._multioption_directories:
            variant = int(base[base.rfind("_") + 1:])
            options = self._GetMultipleOptions(parent)[variant]
            options = string.join(self._GetMultipleOptions(parent)[variant])
        else:
            options = "(None)"
        
        # Create the TestDescriptor
        descriptor = TestDescriptor(self, test_id, test_class,
                                    { 'source_file' : attachment,
                                      'options' : options,
                                      'directory' :
                                      os.path.join(".",
                                                   self._LabelToPath(test_id))
                                      })
        
        return descriptor
        

    def RemoveTest(self, test_id):
        """Remove the test named 'test_id' from the database.

        'test_id' -- A label naming the test that should be removed.

        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'.

        Derived classes must override this method."""

        # Compute the path to the source file.
        path = self._GetTestPath(test_id)

        # If the path does not exist, there is no test with the
        # indicated name.
        if not os.path.exists(path):
            raise NoSuchTestError, test_id

        # Remove the test.
        os.remove(path)
        

    def _GetTestPath(self, test_id):
        """Return the path to the source file for the indicated test.

        'test_id' -- A string giving the name of a test.

        returns -- A string giving the path to the source file
        corresponding to the indicated test."""

        # There is one test that is a special case: conpr-3r is just
        # conpr-3 with the files linked in another order.
        if test_id == "g++.dg/special/conpr-3r.C":
            test_id = "g++.dg/special/conpr-3.C"
            
        # Split the test name into its components.
        (directory, test_name) = self.SplitLabel(test_id)

        # If the parent of the directory is a multioption directory,
        # then directory itself gives us the path to the test.
        parent = self.LabelDirname(directory)
        if parent in self._multioption_directories:
            return self._GetTestPath(directory)
        
        # Compute the file system path corresponding to the test.
        dirpath = self._GetPathFromDirectory(directory)

        return os.path.join(dirpath, test_name)


    def _GetTestClass(self, test_id):
        """Return the name of the test class to use for 'test_id'.

        'test_id' -- A string giving the name of a test.  The test
        must already exist.

        returns -- A string giving the name of the test class."""

        for (prefix, class_name) in self._prefix_map:
            if test_id[:len(prefix)] == prefix:
                return class_name

        # We should never get here; a test with an invalid prefix
        # should not be allowed to exist in the first place.
        assert None
        
    
    def _GetMultipleOptions(self, directory):
        """Return the sequence of options to use for tests in 'directory'.

        'directory' -- An absolute label for a directory.  This value
        must appear in '_multioption_directories'.

        returns -- A sequence of sequences.  Each component sequence
        gives a set of compiler options, as strings.  Each test in
        'directory' should be run with each of the sets of compiler
        options given.  For example, if the sequence returned is
        '(("-O", "-fno-builtin"), ("-O2"))', the test should be run
        once with '-O -fno-builtin' and once with '-O2'."""

        if directory == "g++.dg/bprob":
            return (("-g",), ("-O0",), ("-O1",), ("-O2",), ("-O3",),
                    ("-O3", "-g"), ("-Os",))
        elif directory == "g++.dg/debug":
            return self._debug_options

        assert None
        
        
    # Methods that deal with suites.

    def GetSuite(self, suite_id):
        """Return the 'Suite' for the suite named 'suite_id'.

        'suite_id' -- A label naming the suite.

        returns -- An instance of 'Suite' (or a derived class of
        'Suite') corresponding to 'suite_id'.
        
        raises -- 'NoSuchSuiteError' if there is no test in the database
        named 'test_id'.

        All databases must have an implicit suite called '.' that
        contains all tests in the database."""

        # Compute the path corresponding to the 'suite_id'.
        (parent, base) = self.SplitLabel(suite_id)
        if parent in self._multioption_directories:
            path = self._GetTestPath(suite_id)
            if os.path.exists(path):
                return DirectorySuite(self, suite_id)
        else:
            path = self._GetPathFromDirectory(suite_id)
            if os.path.isdir(path):
                return DirectorySuite(self, suite_id)
            
        # Otherwise the suite does not exist.
        raise NoSuchSuiteError, suite_id
    
        
    def GetSuiteIds(self, directory=".", scan_subdirs=1):
        """Return all suite IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all suites located within 'directory',
        as absolute labels."""

        # There are no suites yet.
        suite_names = []
        
        # Compute the path name of the directory in which to start.
        path = self._GetPathFromDirectory(directory)

        # Get all of the immediate subdirectories, as absolute labels.
        subdirs = map(lambda s: self.JoinLabels(directory, s),
                      self.GetSubdirectories(directory))
        # Add them (and their children) to suite_names.
        for subdirectory in subdirs:
            suite_names.append(subdirectory)
            # If requested, add the children recursively.
            if scan_subdirs:
                suite_names.extend(self.GetSuiteIds(subdirectory,
                                                    scan_subdirs))

        return suite_names
                  
    # Methods that deal with resources.

    def GetResource(self, resource_id):
        """Return the 'ResourceDescriptor' for the resource 'resouce_id'.

        'resource_id' -- A label naming the resource.

        returns -- A 'ResourceDescriptor' corresponding to 'resource_id'.
        
        raises -- 'NoSuchResourceError' if there is no resource in the
        database named 'resource_id'."""

        # There are no resources in a DejaGNU test suite.
        raise NoSuchResourceError, resource_id
    

    def RemoveResource(self, resource_id):
        """Remove the resource named 'resource_id' from the database.

        'resource_id' -- A label naming the resource that should be
        removed.

        raises -- 'NoSuchResourceError' if there is no resource in the
        database named 'resource_id'."""
        
        # There are no resources in a DejaGNU test suite.
        raise NoSuchResourceError, resource_id

        
    def GetResourceIds(self, directory=".", scan_subdirs=1):
        """Return all resource IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all resources located within 'directory',
        as absolute labels."""

        # There are no resources in a DejaGNU test suite.
        return []
    
    # Miscellaneous methods.

    def GetAttachmentStore(self):
        """Returns the 'AttachmentStore' associated with the database.

        returns -- The 'AttachmentStore' containing the attachments
        associated with tests and resources in this database."""

        return self.__store


    def GetSubdirectories(self, directory):
        """Return the immediate subdirectories of 'directory'.

        'directory' -- A label indicating a directory in the database.

        returns -- A sequence of (relative) labels indictating the
        immediate subdirectories of 'directory'.  For example, if "a.b"
        and "a.c" are directories in the database, this method will
        return "b" and "c" given "a" as 'directory'."""

        # If the list of subdirectories is hardwired, return it.
        subdirectories = self._subdirectories.get(directory, [])
        if subdirectories:
            return subdirectories
        
        # Compute the file system path corresponding to directory.
        path = self._GetPathFromDirectory(directory)

        # Go through all of the subdirectories in that directory.
        for file in dircache.listdir(path):
            # Check to see whether the 'path' could be a suite.
            suite = self._GetSuiteNameFromPath(directory, path, file)
            if not suite:
                continue
            # We're only interested in directories.
            if not os.path.isdir(os.path.join(path, file)):
                continue
            # Add the suite to the list of subdirectories.
            subdirectories.append(suite)

        # Add any special-case subdirectories.
        subdirectories.extend(self._extra_subdirectories.get(directory, []))

        # Also, if this directory contains tests that are run with
        # multiple options, make each of them into a subdirectory.
        if directory in self._multioption_directories:
            subdirectories.extend(self._GetTestFilesInDirectory(path))
        
        return subdirectories
            
        
    def GetTestClassNames(self):
        """Return the kinds of tests that the database can store.

        returns -- A sequence of strings.  Each string names a
        class, including the containing module.  Only classes
        of these types can be stored in the database.

        Derived classes may override this method.  The default
        implementation allows all available test classes, but the
        derived class may allow only a subset."""

        return map(lambda x: x[1], self._prefix_map)
    
        
    def _GetPathFromDirectory(self, directory):
        """Return the path corresponding to 'directory'.

        'directory' -- A label indicating a directory in the database.

        returns -- A string giving the file system path corresponding
        to 'directory'."""

        return os.path.join(self._GetTestsuiteRoot(), directory)


    def _GetSuiteNameFromPath(self, directory, dirpath, path):
        """Return true iff 'path' could name a test suite.

        'directory' -- The label giving the path to the directory
        containing the possible suite.
        
        'dirpath' -- The file system directory corresponding to
        'directory'.

        'path' -- A file name, without any path separators, that might
        name a test suite.

        returns -- 'None', if the 'path' cannot name a test suite.
        Otherwise, the (relative) label for the suite named is
        returned.  This routine only checks the file name.  It does
        not check other conditions.  For example, it does not check
        whether the the 'path' denotes a directory, as opposed to a
        file.

        This routine can be used as a predicate; the return value is
        true if and only if 'path' is a valid suite name."""

        for (prefix, predicate) in self._suite_predicates:
            if directory[:len(prefix)] == prefix:
                return (eval("self.%s(directory, dirpath, path)"
                             % predicate))

        return None


    def _GetTestFilesInDirectory(self, path):
        """Return the (relative) labels for test files in 'path'.

        'path' -- The (file system) directory in which to search.

        returns -- A list of (relative) labels for test files in 'path'."""

        test_names = []
        
        # Iterate through all the files in the directory.
        for entry in dircache.listdir(path):
            # Split the file name into its components.
            if os.path.splitext(entry)[1] == self._test_extension:
                # Add this test to the list.
                test_names.append(entry)

        return test_names

        
    def _IsOldDejaSuite(self, directory, dirpath, path):
        """Return true if 'path' names a suite within 'directory'.

        'directory' -- The label of the directory in which 'path' is
        contained.

        'dirpath' -- The file system directory corresponding to
        'directory'.

        'path' -- The (relative) name of a file within the directory.

        returns -- The (relative) label corresponding to the suite, if
        'path' names a suite, or None if it does not."""

        # If the path begins with "g++.", it names a suite.
        if path[:len("g++.")] == "g++.":
            return path

        return None
        
    
    def _IsMultioptionSuite(self, directory, dirpath, path):
        """Return true if 'path' names a suite within 'directory'.

        'directory' -- The label of the directory in which 'path' is
        contained.

        'dirpath' -- The file system directory corresponding to
        'directory'.

        'path' -- The (relative) name of a file within the directory.

        returns -- The (relative) label corresponding to the suite, if
        'path' names a suite, or None if it does not."""

        (base, extension) = os.path.splitext(path)
        if extension == self._test_extension:
            return base

        return None
    

    def _IsGPPDGSuite(self, directory, dirpath, path):
        """Return true if 'path' names a suite within 'directory'.

        'directory' -- The label of the directory in which 'path' is
        contained.

        'dirpath' -- The file system directory corresponding to
        'directory'.
        
        'path' -- The (relative) name of a file within the directory.

        returns -- The (relative) label corresponding to the suite, if
        'path' names a suite, or None if it does not."""

        # Compute the full path to the possible suite.
        dirpath = os.path.join(dirpath, path)
        # Scan the directory looking for .C files.
        for file in dircache.listdir(dirpath):
            if fnmatch.fnmatch(file, "*" + self._test_extension):
                return path

        return None


    def _GetTestsuiteRoot(self):
        """Return the file system directory containing the testsuite.

        returns -- A string giving the path to the root of the GCC
        testsuite, i.e., the directory containing 'gcc.c-torture' and
        'g++.old-deja'."""

        return self.__testsuite_root
