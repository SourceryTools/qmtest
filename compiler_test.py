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
# For license terms see the file COPYING.
#
########################################################################

from   compiler import *
import errno
from   qm.test.result import *
from   qm.test.test import *
import string

########################################################################
# Classes
########################################################################

class CompiledExecutable(RedirectedExecutable):
    """A 'CompiledExecutable' is one generated by a compiler."""

    def _StdinPipe(self):
        """Return a pipe to which to redirect the standard input.

        returns -- A pipe, or 'None' if the standard input should be
        closed in the child."""

        # There is no input available for the child.
        return None


            
class CompilationStep:
    """A single compilation step."""

    def __init__(self, mode, files, options, output, diagnostics):
        """Construct a new 'CompilationStep'.

        'mode' -- As for 'Compiler.Compile'.

        'files' -- As for 'Compiler.Compile'.

        'options' -- As for 'Compiler.Compile'.

        'output' -- As for 'Compiler.Compile'.

        'diagnostics' -- A sequence of 'Diagnostic' instances
        indicating diagnostic messages that are expected from this
        compilation step."""

        self.mode = mode
        self.files = files
        self.options = options
        self.output = output
        self.diagnostics = diagnostics



class CompilerBase:
    """A 'CompilerBase' is used by compilation test and resource clases."""

    def _CheckStatus(self, result, prefix, desc, status,
                     non_zero_exit_ok = 0):
        """Check the exit status from a command.

        'result' -- The 'Result' object to update.

        'prefix' -- The prefix that should be used when creating
        result annotations.

        'desc' -- A description of the executing program.
        
        'status' -- The exit status, as returned by 'waitpid'.

        'non_zero_exit_ok' -- True if a non-zero exit code is not
        considered failure.

        returns -- False is the test failed, true otherwise."""

        if sys.platform == "win32" or os.WIFEXITED(status):
            # Obtain the exit code.
            if sys.platform == "win32":
                exit_code = status
            else:
                exit_code = os.WEXITSTATUS(status)
            # If the exit code is non-zero, the test fails.
            if exit_code != 0 and not non_zero_exit_ok:
                result.Fail("%s failed with exit code %d." % (desc, exit_code))
                # Record the exit code in the result.
                result[prefix + "exit_code"] = str(exit_code)
                return 0
        elif os.WIFSIGNALED(status):
            # Obtain the signal number.
            signal = os.WTERMSIG(status)
            # If the program gets a fatal signal, the test fails .
            result.Fail("%s received fatal signal %d." % (desc, signal))
            result[prefix + "signal"] = str(signal)
            return 0
        else:
            # A process should only be able to stop by exiting, or
            # by being terminated with a signal.
            assert None

        return 1
    

    def _GetDirectory(self):
        """Get the name of the directory in which to run.

        'returns' -- The name of the directory in which this test or
        resource will execute."""

        return os.path.join(".", "build", self.GetId())
    
        
    def _MakeDirectoryRecursively(self, directory):
        """Create 'directory' and its parents.

        'directory' -- The name of the directory to create.  It must
        be a relative path"""

        (parent, base) = os.path.split(directory)
        # Make sure the parent directory exists.
        if parent and not os.path.isdir(parent):
            self._MakeDirectoryRecursively(parent)
        # Create the final directory.
        try:
            os.mkdir(directory)
        except EnvironmentError, e:
            # It's OK if the directory already exists.
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
            
            
    def _MakeDirectory(self):
        """Create a directory in which to place generated files.

        returns -- The name of the directory."""

        # Get the directory name.
        directory = self._GetDirectory()
        # Create it.
        self._MakeDirectoryRecursively(directory)

        return directory


    def _RemoveDirectory(self, result):
        """Remove the directory in which generated files are placed.

        'result' -- The 'Result' of the test or resource.  If the
        'result' indicates success, the directory is removed.
        Otherwise, the directory is left behind to allow investigation
        of the reasons behind the test failure."""

        if result.GetOutcome() == Result.PASS:
            try:
                qm.common.rmdir_recursively(self._GetDirectory())
            except:
                # If the directory cannot be removed, that is no
                # reason for the test to fail.
                pass


    def _GetObjectFileName(self, source_file_name, object_extension):
        """Return the default object file name for 'soruce_file_name'.

        'source_file_name' -- A string giving the name of a source
        file.

        'object_extension' -- The extension used for object files.

        returns -- The name of the object file that will be created by
        compiling 'source_file_name'."""

        basename = os.path.basename(source_file_name)
        return os.path.splitext(basename)[0] + object_extension
    

    def _QuoteForHTML(self, text):

        for t, h in (('&', '&amp;'),
                     ('<', '&lt;'),
                     ('>', '&gt;'),
                     ('"', "&quot;")):
            if text.find(t) >= 0:
                text = h.join(text.split(t))

        return text
    


class CompilerTest(Test, CompilerBase):
    """A 'CompilerTest' tests a compiler."""

    _ignored_diagnostic_regexps = ()
    """A sequence of regular expressions matching diagnostics to ignore."""

    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        # Get the compiler to use for this test.
        compiler = self._GetCompiler(context)

        # If an executable is generated, executable_path will contain
        # the generated path.
        executable_path = None
        # See what we need to run this test.
        steps = self._GetCompilationSteps(context)
        # See if we need to run this test.
        is_execution_required = self._IsExecutionRequired()
        
        # Keep track of which compilation step we are performing so
        # that we can annotate the result appropriately.
        step_index = 1

        # Perform each of the compilation steps.
        for step in steps:
            # Compute a prefix for the result annotations.
            prefix = self._GetAnnotationPrefix() + "step_%d_" % step_index

            # Get the compilation command.
            command = compiler.GetCompilationCommand(step.mode, step.files,
                                                     step.options,
                                                     step.output)
            result[prefix + "command"] = \
                "<tt>" + string.join(command) + "</tt>"
            # Run the compiler.
            (status, output) \
                = compiler.ExecuteCommand(self._GetDirectory(), command)

             # Make sure that the output is OK.
            if not self._CheckOutput(context, result, prefix, output,
                                     step.diagnostics):
                # If there were errors, do not try to run the program.
                is_execution_required = 0
            
            # Check the output status.
            if step.mode == Compiler.MODE_LINK:
                desc = "Link"
            else:
                desc = "Compilation"
            if not self._CheckStatus(result, prefix, desc, status,
                                     step.diagnostics):
                return

            # If this compilation generated an executable, remember
            # that fact.
            if step.mode == Compiler.MODE_LINK:
                executable_path = os.path.join(".", step.output or "a.out")

            # We're on to the next step.
            step_index = step_index + 1

        # Execute the generated program, if appropriate.
        if executable_path and is_execution_required:
            self._RunExecutable(executable_path, context, result)
        
        
    def _GetCompiler(self, context):
        """Return the 'Compiler' to use.

        'context' -- The 'Context' in which this test is being
        executed."""

        raise NotImplementedError
        
        
    def _GetCompilationSteps(self, context):
        """Return the compilation steps for this test.

        'context' -- The 'Context' in which this test is being
        executed.
        
        returns -- A sequence of 'CompilationStep' objects."""

        raise NotImplementedError


    def _IsExecutionRequired(self):
        """Returns true if the generated executable should be run.

        returns -- True if the generated executable should be run."""

        return 0
        
        
    def _GetAnnotationPrefix(self):
        """Return the prefix to use for result annotations.

        returns -- The prefix to use for result annotations."""

        return "CompilerTest."


    def _GetLibraryDirectories(self, context):
        """Returns the directories to search for libraries.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        returns -- A sequence of strings giving the paths to the
        directories to search for libraries."""

        return context.get("CompilerTest.library_dirs", "").split()


    def _RunExecutable(self, path, context, result):
        """Run an executable generated by the compiler.

        'path' -- The path to the generated executable.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        # Create an object representing the executable.
        executable = CompiledExecutable()
        # Compute the command line for the executable.
        interpreter = context.get("CompilerTest.interpreter")
        if interpreter:
            arguments = [interpreter, path]
        else:
            arguments = [path]
        # Compute the environment.
        library_dirs = self._GetLibraryDirectories(context)
        if library_dirs:
            environment = os.environ.copy()
            # Update LD_LIBRARY_PATH.  On IRIX 6, this variable
            # goes by other names, so we update them too.  It is
            # harmless to do this on other systems.
            for variable in ['LD_LIBRARY_PATH',
                             'LD_LIBRARYN32_PATH',
                             'LD_LIBRARYN64_PATH']:
                old_path = environment.get(variable)
                new_path = string.join(self._library_dirs, ":")
                if old_path and new_path:
                    new_path = new_path + ':' + old_path
            environment[variable] = new_path
        else:
            # Use the default values.
            environment = None

        status = executable.Run(arguments,
                                environment = environment,
                                dir = self._GetDirectory())
        # Compute the result annotation prefix.
        prefix = self._GetAnnotationPrefix() + "execution_"
        # Remember the output streams.
        result[prefix + "stdout"] = "<pre>" + executable.stdout + "</pre>"
        result[prefix + "stderr"] = "<pre>" + executable.stderr + "</pre>"
        # Check the output status.
        self._CheckStatus(result, prefix, "Executable", status)


    def _CheckOutput(self, context, result, prefix, output, diagnostics):
        """Check that the 'output' contains appropriate diagnostics.

        'context' -- The 'Context' for the test that is being
        executed.

        'result' -- The 'Result' of the test.

        'prefix' -- A string giving the prefix for any annotations to
        be added to the 'result'.

        'output' -- A string giving the output of the compiler.

        'diagnostics' -- The diagnostics that are expected for the
        compilation.

        returns -- True if there were no errors so severe as to
        prevent execution of the test."""

        # Annotate the result with the output.
        if output:
            result[prefix + "output"] \
                = "<pre>" + self._QuoteForHTML(output) + "</pre>"

        # Get the compiler to use to parse the output.
        compiler = self._GetCompiler(context)
        
        # Parse the output.
        emitted_diagnostics \
            = compiler.ParseOutput(output, self._ignored_diagnostic_regexps)

        # Diagnostics that were not emitted, but should have been.
        missing_diagnostics = []
        # Diagnostics that were emitted, but should not have been.
        spurious_diagnostics = []
        # Expected diagnostics that have been matched.
        matched_diagnostics = []
        # Keep track of any errors.
        errors_occurred = 0
        
        # Loop through the emitted diagnostics, trying to match each
        # with an expected diagnostic.
        for emitted_diagnostic in emitted_diagnostics:
            # If the emitted diagnostic is an internal compiler error,
            # then the test failed.  (The compiler crashed.)
            if emitted_diagnostic.severity == 'internal_error':
                result.Fail("The compiler issued an internal error.")
                return 0
            if emitted_diagnostic.severity == "error":
                errors_occurred = 1
            # Assume that the emitted diagnostic is unexpected.
            is_expected = 0
            # Loop through the expected diagnostics, trying to find
            # one that matches the emitted diagnostic.  A single
            # emitted diagnostic might match more than one expected
            # diagnostic, so we can not break out of the loop early.
            for expected_diagnostic in diagnostics:
                if self._IsDiagnosticExpected(emitted_diagnostic,
                                              expected_diagnostic):
                    matched_diagnostics.append(expected_diagnostic)
                    is_expected = 1
            if not is_expected:
                spurious_diagnostics.append(emitted_diagnostic)
        # Any expected diagnostics for which there was no
        # corresponding emitted diagnostic are missing diagnostics.
        for expected_diagnostic in diagnostics:
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
                result[self._GetAnnotationPrefix() + "spurious_diagnostics"] \
                  = self._DiagnosticsToString(spurious_diagnostics)
            if missing_diagnostics:
                result[self._GetAnnotationPrefix() + "missing_diagnostics"] \
                  = self._DiagnosticsToString(missing_diagnostics)

        # If errors occurred, there is no point in trying to run
        # the executable.
        return not errors_occurred


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
            if (exsp.file and (os.path.basename(emsp.file)
                               != os.path.basename(exsp.file))):
                return 0
            if exsp.column and emsp.column != exsp.column:
                return 0
        
        # If the severities do not match, there is no match.
        if (expected.severity and emitted.severity != expected.severity):
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
        return "<pre>" + string.join(diagnostic_strings, '\n') + "</pre>"
