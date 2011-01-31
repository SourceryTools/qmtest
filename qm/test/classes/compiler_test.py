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
from   qm.test.result import *
from   qm.test.test import *
import os, dircache

########################################################################
# Classes
########################################################################

class CompilationStep:
    """A single compilation step."""

    def __init__(self, compiler, mode, files, options = [], ldflags = [],
                 output = None , diagnostics = []):
        """Construct a new 'CompilationStep'.

        'compiler' -- A Compiler object.

        'mode' -- As for 'Compiler.Compile'.

        'files' -- As for 'Compiler.Compile'.

        'options' -- As for 'Compiler.Compile'.

        'ldflags' -- As for 'Compiler.Compile'.

        'output' -- As for 'Compiler.Compile'.

        'diagnostics' -- A sequence of 'Diagnostic' instances
        indicating diagnostic messages that are expected from this
        compilation step."""

        self.compiler = compiler
        self.mode = mode
        self.files = files
        self.options = options
        self.ldflags = ldflags
        self.output = output
        self.diagnostics = diagnostics



class CompilerBase:
    """A 'CompilerBase' is used by compilation test and resource clases."""

    def _GetDirectory(self, context):
        """Get the name of the directory in which to run.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'returns' -- The name of the directory in which this test or
        resource will execute."""

        if context.has_key("CompilerTest.scratch_dir"):
            return os.path.join(context["CompilerTest.scratch_dir"],
                                self.GetId())
        else:
            return os.path.join(".", "build", self.GetId())
    
        
    def _MakeDirectory(self, context):
        """Create a directory in which to place generated files.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        returns -- The name of the directory."""

        # Get the directory name.
        directory = self._GetDirectory(context)
        # Create it.
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory


    def _RemoveDirectory(self, context, result):
        """Remove the directory in which generated files are placed.

        'result' -- The 'Result' of the test or resource.  If the
        'result' indicates success, the directory is removed.
        Otherwise, the directory is left behind to allow investigation
        of the reasons behind the test failure."""

        def removedir(directory, dir = True):
            for n in dircache.listdir(directory):
                name = os.path.join(directory, n)
                if os.path.isfile(name):
                    os.remove(name)
                elif os.path.isdir(name):
                    removedir(name)
            if dir: os.rmdir(directory)

        cleanup = context.GetBoolean("CompilerTest.cleanup_executable", True)
        if result.GetOutcome() == Result.PASS and cleanup:
            try:
                directory = self._GetDirectory(context)
                removedir(directory, False)
                os.removedirs(directory)
            except:
                # If the directory cannot be removed, that is no
                # reason for the test to fail.
                pass


    def _GetObjectFileName(self, source_file_name, object_extension):
        """Return the default object file name for 'source_file_name'.

        'source_file_name' -- A string giving the name of a source
        file.

        'object_extension' -- The extension used for object files.

        returns -- The name of the object file that will be created by
        compiling 'source_file_name'."""

        basename = os.path.basename(source_file_name)
        return os.path.splitext(basename)[0] + object_extension
    


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

        # If an executable is generated, executable_path will contain
        # the generated path.
        executable_path = None
        # See what we need to run this test.
        steps = self._GetCompilationSteps(context)
        # See if we need to run this test.
        is_execution_required = self._IsExecutionRequired()
        # Create the temporary build directory.
        self._MakeDirectory(context)
        
        # Keep track of which compilation step we are performing so
        # that we can annotate the result appropriately.
        step_index = 1

        # Perform each of the compilation steps.
        for step in steps:
            # Get the compiler to use for this test.
            compiler = step.compiler

            # Compute a prefix for the result annotations.
            prefix = self._GetAnnotationPrefix() + "step_%d_" % step_index

            # Get the compilation command.
            command = compiler.GetCompilationCommand(step.mode, step.files,
                                                     step.options,
                                                     step.ldflags,
                                                     step.output)
            result[prefix + "command"] = result.Quote(' '.join(command))
            # Run the compiler.
            timeout = context.get("CompilerTest.compilation_timeout", -1)
            (status, output) \
                = compiler.ExecuteCommand(self._GetDirectory(context),
                                          command, timeout)
            # Annotate the result with the output.
            if output:
                result[prefix + "output"] = result.Quote(output)
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
            # If step.diagnostics is non-empty, a non-zero status
            # is not considered a failure.
            if not result.CheckExitStatus(prefix, desc, status,
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


    def _GetTarget(self, context):
        """Returns a target for the executable to be run on.

        'context' -- The Context in which this test is being executed.

        returns -- A Host to run the executable on."""

        raise NotImplementedError


    def _IsExecutionRequired(self):
        """Returns true if the generated executable should be run.

        returns -- True if the generated executable should be run."""

        return 0
        

    def _GetExecutableArguments(self):
        """Returns the arguments to the generated executable.

        returns -- A list of strings, to be passed as argumensts to
        the generated executable.""" 

        return []

    
    def _MustExecutableExitSuccessfully(self):
        """Returns true if the executable must exit with code zero.

        returns -- True if the generated executable (if any) must exit
        with code zero.  Note that the executable will not be run at
        all (and so the return value of this function will be ignored)
        if '_IsExecutionRequired' does not return true."""

        return True
        
        
    def _GetAnnotationPrefix(self):
        """Return the prefix to use for result annotations.

        returns -- The prefix to use for result annotations."""

        return "CompilerTest."


    def _GetEnvironment(self, context):
        """Return the environment to use for test execution.

        returns -- The environment dictionary to use for test execution."""


        return None


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

        # Compute the result annotation prefix.
        prefix = self._GetAnnotationPrefix() + "execution_"
        # Record the command line.
        path = os.path.join(self._GetDirectory(context), path)
        arguments = self._GetExecutableArguments()
        result[prefix + "command"] \
           = "<tt>" + path + " " + " ".join(arguments) + "</tt>"

        # Compute the environment.
        environment = self._GetEnvironment(context)

        library_dirs = self._GetLibraryDirectories(context)
        if library_dirs:
            if not environment:
                environment = dict()
            # Update LD_LIBRARY_PATH.  On IRIX 6, this variable
            # goes by other names, so we update them too.  It is
            # harmless to do this on other systems.
            for variable in ['LD_LIBRARY_PATH',
                             'LD_LIBRARYN32_PATH',
                             'LD_LIBRARYN64_PATH']:
                old_path = environment.get(variable)
                new_path = ':'.join(library_dirs)
                if old_path and new_path:
                    new_path = new_path + ':' + old_path
                environment[variable] = new_path

        target = self._GetTarget(context)
        timeout = context.get("CompilerTest.execution_timeout", -1)
        status, output = target.UploadAndRun(path,
                                             arguments,
                                             environment,
                                             timeout)
        # Record the output.
        result[prefix + "output"] = result.Quote(output)
        self._CheckExecutableOutput(result, output)
        # Check the output status.
        result.CheckExitStatus(prefix, "Executable", status,
                               not self._MustExecutableExitSuccessfully())


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
                self._DiagnosticsToString(result, 
                                          "spurious_diagnostics",
                                          spurious_diagnostics)
            if missing_diagnostics:
                self._DiagnosticsToString(result, 
                                          "missing_diagnostics",
                                          missing_diagnostics)

        # If errors occurred, there is no point in trying to run
        # the executable.
        return not errors_occurred


    def _CheckExecutableOutput(self, result, output):
        """Checks the output from the generated executable.

        'result' -- The 'Result' object for this test.

        'output' -- The output generated by the executable.

        If the output is unsatisfactory, 'result' is modified
        appropriately."""
        
        pass

    
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


    def _DiagnosticsToString(self, result, annotation, diagnostics):
        """Return a string representing the 'diagnostics'.

        'diagnostics' -- A sequence of 'Diagnostic' instances.

        returns -- A string representing the 'Diagnostic's, with one
        diagnostic message per line."""

        # Compute the string representation of each diagnostic.
        diagnostic_strings = map(str, diagnostics)
        # Insert a newline between each string.
        result[self._GetAnnotationPrefix() + annotation] \
            = result.Quote("\n".join(diagnostic_strings))
