########################################################################
#
# File:   compiler_test.py
# Author: Mark Mitchell
# Date:   12/11/2001
#
# Contents:
#   CompilerTest
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

import compiler
from   compiler import *
import fnmatch
from   qm.test.result import *
from   qm.test.test import *

########################################################################
# Classes
########################################################################

class CompilerTest(Test):
    """A 'CompilerTest' tests a compiler.

    The test consists of compiling zero or more source files."""

    arguments = [
        qm.fields.TextField(
            name="mode",
            title="Mode",
            description="""The mode of testing desired.

            This field may be one of 'compile' (just compile the
            source files), 'link' (compile and link the files in one
            step), 'run' (compile and link the files and then run the
            resulting executable), or 'compile_and_link' (compile and
            link the files in two separate steps)."""),
        qm.fields.SetField(qm.fields.AttachmentField(
            name="source_files",
            title="Source Files",
            description="""The source files.""")),
        qm.fields.SetField(qm.fields.TextField(
            name="options",
            title="Options",
            default_value="",
            description="""Options to pass to the compiler.""")),
        qm.fields.IntegerField(
            name="is_severity_significant",
            title="Is Severity Significant?",
            default_value="1",
            description="""True if severities are significant.

            If the severity of dignostics is significant, the severity
            indicated by the markup in the test and that
            emitted by the compiler must match.  If the severity of
            diagnostics is insignificant, all that matters is that
            some diagnostic is emitted at the appropriate location."""),
        qm.fields.IntegerField(
            name="is_file_significant",
            title="Is File Significant?",
            default_value="1",
            description="""True if the file names are significant.

            If the file names of dignostics are significant, the file
            names indicated by the markup in the test and that
            emitted by the compiler must match.  If file names are
            insignificant of diagnostics is insignificant, all that
            matters is that the line numbers match."""),
        qm.fields.SetField(qm.fields.TextField(
            name="platforms",
            title="Platforms",
            description="""Targets on which to run the test.

            Each target is GNU machine triplet.  If the current platformt
            is not one of the indicated targets, the test is not
            executed.  If no platforms are specified, the test will be
            run on all platforms."""
            ))
    ]

    def __init__(self, **arguments):
        """Construct a new 'CompilerTest'."""

        apply(Test.__init__, (self,), arguments)

        self.__expected_diagnostics = None
        

    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        if not self._IsApplicableOnCurrentPlatform(context):
            return

        if self.mode == "compile":
            c = self._Compile(Compiler.MODE_COMPILE, context, result)[0]

            # Get the names of the source files.
            source_file_names = map(lambda s: s.GetDataFile(),
                                    self.source_files)
            # Compute the name of the object files.
            object_files = c.GetObjectNames(source_file_names)
            # Remove the object files.
            for object_file in object_files:
                try:
                    os.remove(object_file)
                except:
                    pass

        elif self.mode == "link":
            c = self._Compile(Compiler.MODE_LINK, context, result)[0]

            # Get the names of the source files.
            source_file_names = map(lambda s: s.GetDataFile(),
                                    self.source_files)
            # Compute the name of the executable.
            executable = c.GetExecutableName(source_file_names)

            # Remove the executable file, if it exists.
            try:
                os.remove(executable)
            except:
                pass

        elif self.mode == "compile_and_link":
            c = self._Compile(Compiler.MODE_COMPILE, context, result)[0]

            # Get the names of the source files.
            source_file_names = map(lambda s: s.GetDataFile(),
                                    self.source_files)
            # Compute the name of the object files.
            object_file_names = c.GetObjectNames(source_file_names)
            # Compute the name of the executable.
            executable = c.GetExecutableName(source_file_names)

            try:
                # If the test has already failed, stop now.
                if result.GetOutcome() != Result.PASS:
                    return
                # Link them together.
                (status, output, command) \
                    = c.CompileSourceFiles(Compiler.MODE_LINK,
                                           object_file_names,
                                           self._GetTimeout(context))
                # Annote the result with the raw information returned by the
                # compiler.
                result['CompilerTest.link_status'] = str(status)
                result['CompilerTest.link_output'] = output
                result['CompilerTest.link_command'] = string.join(command)
                # Get the list of emitted diagnostics.
                emitted_diagnostics = c.GetDiagnostics(output)
                # There should never be diagnostics at link time.
                if emitted_diagnostics:
                    result.Fail("Spurious diagnostics during link.")
                    # Add annotations showing the problem.
                    if emitted_diagnostics:
                        result['CompilerTest.spurious_link_diagnostics'] \
                            = self._DiagnosticsToString(emitted_diagnostics)
            finally:
                # Remove each of the object files.
                for object_file in object_file_names:
                    try:
                        os.remove(object_file)
                    except:
                        pass
                # Remove the executable file, if it exists.
                try:
                    os.remove(executable)
                except:
                    pass

        elif self.mode == "run":
            # Link the source files together.
            c = self._Compile(Compiler.MODE_LINK, context, result)[0]

            # Get the names of the source files.
            source_file_names = map(lambda s: s.GetDataFile(),
                                    self.source_files)
            # Compute the name of the executable.
            executable = c.GetExecutableName(source_file_names)

            try:
                # If the test has already failed, stop now.
                if result.GetOutcome() != Result.PASS:
                    return

                # Compute the environment for the child.
                environment = {}
                # Update LD_LIBRARY_PATH.  On IRIX 6, this variable
                # goes by other names, so we update them too.  It is
                # harmless to do this on other systems.
                for variable in ['LD_LIBRARY_PATH',
                                 'LD_LIBRARYN32_PATH',
                                 'LD_LIBRARYN64_PATH']:
                    old_path = os.environ.get(variable)
                    new_path = context.get('CompilerTest.ld_library_path')
                    if old_path and new_path:
                        new_path = new_path + ':' + old_path
                    environment[variable] = new_path

                # Run it.
                (status, output) \
                    = RunCommand([executable],
                                 self._GetTimeout(context),
                                 environment)

                # Add annotations indicating what happenned.
                result['CompilerTest.exit_status'] = str(status)
                result['CompilerTest.output'] = output

                # If the program did not exit with a zero exit code, the test
                # failed.
                if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                    result.Fail("Executable did not run successfully.")

                    # Add an annotation explaining what went wrong.
                    if os.WIFEXITED(status):
                        result['CompilerTest.exit_code'] \
                           = str(os.WEXITSTATUS(status))
                    elif os.WIFSIGNALED(status):
                        result['CompilerTest.signal'] \
                           = str(os.WTERMSIG(status))
            finally:
                # Remove the executable file, if it exists.
                try:
                    os.remove(executable)
                except:
                    pass

        else:
            assert 0

            
    def _Compile(self, mode, context, result):
        """Compile the source files.

        'mode' -- One of the 'Compiler.modes', indicating what kind of
        compilation should take place.
        
        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations.

        returns -- A tuple '(compiler, emitted_diagnostics)'
        consisting of the 'Compiler' used to compile the source files
        and the list of 'Diagnostic' objects that was generated by the
        compilation."""

        # Get the names of the source files.
        source_file_names = map(lambda s: s.GetDataFile(),
                                self.source_files)
        # Get the compiler.
        c = self._GetCompiler(context)
        # Compile the source files.
        (status, output, command) \
            = c.CompileSourceFiles(mode, source_file_names,
                                   self._GetTimeout(context))

        # Annote the result with the raw information returned by the
        # compiler.
        result['CompilerTest.status'] = str(status)
        result['CompilerTest.output'] = output
        result['CompilerTest.command'] = string.join(command)

        # Get the list of emitted diagnostics.
        emitted_diagnostics = c.GetDiagnostics(output)
        
        # Get the list of expected diagnostics.
        expected_diagnostics = self._GetExpectedDiagnostics()
        
        # Diagnostics that were not emitted, but should have been.
        missing_diagnostics = []
        # Diagnostics that were emitted, but should not have been.
        spurious_diagnostics = []
        # Expected diagnostics that have been matched.
        matched_diagnostics = []
        
        # Loop through the emitted diagnostics, trying to match each
        # with an expected diagnostic.
        for emitted_diagnostic in emitted_diagnostics:
            # If the emitted diagnostic is an internal compiler error,
            # then the test failed.  (The compiler crashed.)
            if emitted_diagnostic.severity == 'internal_error':
                result.Fail("Compiler crash.")
                continue
            # Assume that the emitted diagnostic is unexpected.
            is_expected = 0
            # Loop through the expected diagnostics, trying to find
            # one that matches the emitted diagnostic.  A single
            # emitted diagnostic might match more than one expected
            # diagnostic, so we can not break out of the loop early.
            for expected_diagnostic in expected_diagnostics:
                if self._IsDiagnosticExpected(emitted_diagnostic,
                                              expected_diagnostic):
                    matched_diagnostics.append(expected_diagnostic)
                    is_expected = 1
            if not is_expected:
                spurious_diagnostics.append(emitted_diagnostic)
        # Any expected diagnostics for which there was no
        # corresponding emitted diagnostic are missing diagnostics.
        for expected_diagnostic in expected_diagnostics:
            if expected_diagnostic not in matched_diagnostics:
                missing_diagnostics.append(expected_diagnostic)

        # If there were missing or spurious diagnostics, the test failed.
        if missing_diagnostics or spurious_diagnostics:
            # Compute a succint description of what went wrong.
            if missing_diagnostics and spurious_diagnostics:
                result.Fail("Missing and spurious diagnostics.")
            elif missing_diagnostics:
                result.Fail("Missing diagnostics.")
            else:
                result.Fail("Spurious diagnostics.")

            # Add annotations showing the problem.
            if spurious_diagnostics:
                result['CompilerTest.spurious_diagnostics'] \
                  = self._DiagnosticsToString(spurious_diagnostics)
            if missing_diagnostics:
                result['CompilerTest.missing_diagnostics'] \
                  = self._DiagnosticsToString(missing_diagnostics)

        return (c, emitted_diagnostics)

                 
    def _GetExpectedDiagnostics(self):
        """Return the expected diagnostics for this test.

        returns -- A list of 'Diagnostic' instances giving the
        diagnostic messages expected by this test."""

        if not self.__expected_diagnostics:
            # If the expected diagnostics have not yet already been
            # computed, compute them now.
            self.__expected_diagnostics = []
            # Iterate through each of the source files collected the
            # expected diagostics from each.
            for file in self.source_files:
                new_diagnostics = self.__ScanSourceFileForDiagnostics(file)
                self.__expected_diagnostics.extend(new_diagnostics)

        return self.__expected_diagnostics

                
    def _IsDiagnosticExpected(self, emitted, expected):
        """Returns true if 'emitted' matches 'expected'.

        'emitted' -- A 'Diagnostic emitted by the compiler.
        
        'expected' -- A 'Diagnostic' indicating an expectation about a
        diagnostic to be emitted by the compiler.

        returns -- True if the 'emitted' was expected by the
        'expected'."""

        # If the source positions do not match, there is no match.
        if expected.source_position:
            exsp = expected.source_position
            emsp = emitted.source_position

            if exsp.line and emsp.line != exsp.line:
                return 0
            if (self.is_file_significant
                and exsp.file
                and (os.path.basename(emsp.file)
                     != os.path.basename(exsp.file))):
                return 0
            if exsp.column and emsp.column != exsp.column:
                return 0
        
        # If the severities do not match, there is no match.
        if (self.is_severity_significant
            and expected.severity
            and emitted.severity != expected.severity):
            return 0
        # If the messages do not match, there is no match.
        if expected.message and not re.search(expected.message,
                                              emitted.message):
            return 0

        # There's a match.
        return 1
    

    def _DiagnosticsToString(self, diagnostics):
        """Return a string representing the 'diagnostics'.

        'diagnostics' -- A sequence of 'Diagnostic' instances.

        returns -- A string representing the 'Diagnostic's, with one
        diagnostic message per line."""

        # Compute the string representation of each diagnostic.
        diagnostic_strings = map(str, diagnostics)
        # Insert a newline between each string.
        return string.join(diagnostic_strings, '\n')

        
    def __ScanSourceFileForDiagnostics(self, source_file):
        """Scan 'source_file' for expected diagnostics.

        'source_file' -- An 'Attachment' indicating the source file to
        scan.

        returns -- A list of 'Diagnostic' instances giving the
        diagnostic messages expected by the 'source_file'."""

        filename = source_file.GetDataFile()
        scanner = self.GetScanner()
        return scanner.ScanSourceFileForDiagnostics(filename)
    

    def _GetCompiler(self, context):
        """Return the 'Compiler' indicated by the 'context'.

        'context' -- A 'Context' instance.

        returns -- The 'Compiler' indicated in the 'context'."""

        # Look for the kind of compiler requested.
        compiler_class = context['CompilerTest.class']
        # Look for the path to the compiler.
        compiler_path = context['CompilerTest.path']
        # Compute the options to pass to the compiler.
        compiler_options = string.split(self.options)
        
        return compiler.__dict__[compiler_class](compiler_path,
                                                 compiler_options)
    

    def _GetTimeout(self, context):
        """Return the timeout implied by the 'context'.

        'context' -- A 'Context' instance.

        returns -- The time, in seconds, that commands should be
        permitted to execute."""

        return int(context.get('CompilerTest.timeout', '60'))


    def _IsApplicableOnCurrentPlatform(self, context):
        """Return true if the test should be run.
        
        returns -- True if the test applies to the platform on which we
        are currently executed, as indicated by the 'context'."""

        # If not platforms were specified, run the test everywhere.
        if not self.platforms:
            return 1

        # Get the platform specified by the context.
        platform = context['CompilerTest.platform']
        # See if any of the platforms specified matches the current
        # platform.
        for p in self.platforms:
            if fnmatch.fnmatchcase(platform, p):
                return 1

        return 0

                

class SourceFileScanner:
    """A 'SourceFileScanner' scans a source file for diagnostics."""

    diagnostic_regexps = { }
    """A map from severities (strings) to regular expressions.  If the
    regular expression matches a portion of a line, then that line
    indicates that a diagnostic with the indicated severity is
    expected there."""

    severities = ['warning', 'error']
    """The severities that can be specified in the source files."""

    def GetTestMode(self, contents):
        """Return the test mode given the test file 'contents'.

        'contents' -- A string giving the body of the file containing
        the test.

        returns -- A string indicating the test mode.

        This method must be overridden by derived classes."""

        assert 0


    def GetCompilerOptions(self, contents):
        """Return the compiler options given the test file 'contents'.

        'contents' -- A string giving the body of the file containing
        the test.

        returns -- A string indicating the options to use.

        This method may be overridden by derived classes."""

        assert 0

        
    def ScanSourceFileForDiagnostics(self, source_file):
        """Scan 'source_file' for expected diagnostics.

        'source_file' -- The name of a source file.

        returns -- A list of 'Diagnostic' instances giving the
        diagnostic messages expected by the 'source_file'."""

        # There are no diagnostics yet.
        expected_diagnostics = []
        # Open the source file.
        f = open(source_file)
        # The first line is line 1.
        line_number = 1
        # Read all of the lines from the source_file.
        for line in f.readlines():
            # See if this line matches any of the regular expressions
            # that indicate a diagnostic.
            for severity in self.severities:
                match = self.diagnostic_regexps[severity].search(line)
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
                    source_position \
                        = SourcePosition(source_file, expected_line, 0)
                    # Create a Diagnostic.
                    diagnostic = Diagnostic(source_position, severity, None)
                    # Add it to the list.
                    expected_diagnostics.append(diagnostic)
            # We have read one more line.
            line_number = line_number + 1
        # Close the file.
        f.close()

        return expected_diagnostics



class OldDejaGNUSourceFileScanner(SourceFileScanner):
    """A 'OldDejaGNUSourceFileScanner' scans a source file for diagnostics.
    
    This class uses the method embodied in the 'old-dejagnu.exp'
    DejaGNU script."""

    diagnostic_regexps = {
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
        
    _mode_map = { "Build then link:" : 'compile_and_link',
                  "Build don't link:" : 'compile',
                  "Build don't run:" : 'link' }
    """A map from strings to test mode.  When the test case contains
    one of the strings, the corresponding test mode is used."""

    _default_options = "-ansi -pedantic-errors -Wno-long-long"
    """Default compiler options."""
    
    _options_regexp = re.compile("Special.*Options:(?P<options>.*)")
    """A compiled regular expression.  When this expression matches
    part of the input file, the 'options' match group indicates
    compiler options that should be used instead of
    '_default_options'."""

    def GetTestMode(self, contents):
        """Return the test mode given the test file 'contents'.

        'contents' -- A string giving the body of the file containing
        the test.

        returns -- A string indicating the test mode."""

        mode = None
        
        # See if there is an entry that specifies the test mode.
        for (s, c) in self._mode_map.items():
            if string.find(contents, s) != -1:
                return c

        # If there are any expected errors or warnings, the test is a
        # LinkTest, not a RunTest.
        for severity in ('error', 'warning'):
            regexp = self.diagnostic_regexps[severity]
            if regexp.search(contents):
                return 'link'
        
        # If no test mode has been specified, run the program.
        return 'run'


    def GetCompilerOptions(self, contents):
        """Return the compiler options given the test file 'contents'.

        'contents' -- A string giving the body of the file containing
        the test.

        returns -- A string indicating the options to use."""

        match = self._options_regexp.search(contents)
        if match:
            return match.group('options')

        return self._default_options



class DGSourceFileScanner(SourceFileScanner):
    """A 'DGSourceFileScanner' scans a source file for diagnostics.
    
    This class uses the method embodied in the 'dg.exp' DejaGNU script."""

    diagnostic_regexps = {
        'warning' : re.compile('{\s*dg-warning '),
        'error' : re.compile('{\s*dg-error ')
    }
    """A map from severities (strings) to regular expressions.  If the
    regular expression matches a portion of a line, then that line
    indicates that a diagnostic with the indicated severity is
    expected there."""

    _line_regexp = re.compile('\s(?P<line>[0-9]+)\s$')
    """A compiled regular expression.  If a diagnostic specification
    matches this regular expression, then the 'line' match group gives
    the line number at which the diagnostic is expected."""

    _mode_regexp = re.compile('{\s*dg-do\s+(?P<mode>\S+)')
    """A compiled regular expression.  The test file should match
    this regular expression.  The 'mode' match group indicates
    the kind of test."""
    
    _default_options = "-ansi -pedantic-errors -Wno-long-long"
    """Default compiler options."""

    _options_regexp = re.compile('{\s*dg-options\s+"?(?P<options>.*)"?\s*}')
    """A compiled regular expression.  When this expression matches
    part of the input file, the 'options' match group indicates
    compiler options that should be used instead of
    '_default_options'."""

    def GetTestMode(self, contents):
        """Return the test mode given the test file 'contents'.

        'contents' -- A string giving the body of the file containing
        the test.

        returns -- A string indicating the test mode."""

        return self._mode_regexp.search(contents).group('mode')


    def GetCompilerOptions(self, contents):
        """Return the compiler options given the test file 'contents'.

        'contents' -- A string giving the body of the file containing
        the test.

        returns -- A string indicating the options to use."""

        match = self._options_regexp.search(contents)
        if match:
            return match.group('options')

        return self._default_options


            
class OldDejaGNUTest(CompilerTest):
    scanner = OldDejaGNUSourceFileScanner()
    
    def GetScanner(self):
        return self.scanner



class DGTest(CompilerTest):
    scanner = DGSourceFileScanner()
    
    def GetScanner(self):
        return self.scanner



