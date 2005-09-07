########################################################################
#
# File:   dg_test.py
# Author: Mark Mitchell
# Date:   04/17/2003
#
# Contents:
#   DGTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from   dejagnu_test import DejaGNUTest
import fnmatch
import os
from   qm.test.result import Result
from   qm.fields import BooleanField
import re

########################################################################
# Classes
########################################################################

class DGTest(DejaGNUTest):
    """A 'DGTest' is a test using the DejaGNU 'dg' driver.

    This test class emulates the 'dg.exp' source file in the DejaGNU
    distribution."""

    class DGException(Exception):
        """The exception class raised by 'DGTest'.

        When a 'DGTest' method detects an error situation, it raises
        an exception of this type."""

        pass



    __dg_command_regexp \
         = re.compile(r"{[ \t]+dg-([-a-z]+)[ \t]+(.*)[ \t]+}[^}]*$")
    """A regular expression matching commands embedded in the source file."""

    # The values of these constants have been chosen so that they
    # match the valid values for the 'dg-do' command.
    KIND_PREPROCESS = "preprocess"
    KIND_COMPILE = "compile"
    KIND_ASSEMBLE = "assemble"
    KIND_LINK = "link"
    KIND_RUN = "run"

    keep_output = BooleanField(default_value=False,
        description="""True if the output file should be retained
        after the test is complete.  Otherwise, it is removed.""")

    _default_kind = KIND_COMPILE
    """The default test kind.

    This value can be overridden by a 'dg-do' command in the test file."""
    
    __test_kinds = (
        KIND_PREPROCESS,
        KIND_COMPILE,
        KIND_ASSEMBLE,
        KIND_LINK,
        KIND_RUN
        )
    """The kinds of tests supported by 'dg.exp'."""

    __DIAG_BOGUS = "bogus"
    __DIAG_ERROR = "error"
    __DIAG_WARNING = "warning"
    
    __diagnostic_descriptions = {
        __DIAG_ERROR : "errors",
        __DIAG_WARNING : "warnings",
        __DIAG_BOGUS : "bogus messages",
        "build" : "build failure",
        }
    """A map from dg diagnostic kinds to descriptive strings."""
    
    def _RunDGTest(self, tool_flags, default_options, context, result,
                   path = None,
                   default_kind = None,
                   keep_output = None):
        """Run a 'dg' test.

        'tool_flags' -- A list of strings giving a set of options to be
        provided to the tool being tested.
        
        'default_options' -- A list of strings giving a default set of
        options to be provided to the tool being tested.  These options
        can be overridden by an embedded 'dg-options' command in the
        test itself.
        
        'context' -- The 'Context' in which this test is running.

        'result' -- The 'Result' of the test execution.

        'path' -- The path to the test file.  If 'None', the main test
        file path is used.
        
        'default_kind' -- The kind of test to perform.  If this value
        is 'None', then 'self._default_kind' is used.

        'keep_output' -- True if the output file should be retained
        after the test is complete.  Otherwise, it is removed.

        This function emulates 'dg-test'."""
        
        # Intialize.
        if default_kind is None:
            default_kind = self._default_kind
        self._kind = default_kind
        self._selected = None
        self._expectation = None
        self._options = list(default_options)
        self._diagnostics = []
        self._excess_errors_expected = False
        self._final_commands = []
        # Iterate through the test looking for embedded commands.
        line_num = 0
        if not path:
            path = self._GetSourcePath()
        root = self.GetDatabase().GetRoot()
        if path.startswith(root):
            self._name = path[len(root) + 1:]
        else:
            # We prepend "./" for output compatibility with DejaGNU.
            self._name = os.path.join(".", os.path.basename(path))
        for l in open(path).xreadlines():
            line_num += 1
            m = self.__dg_command_regexp.search(l)
            if m:
                f = getattr(self, "_DG" + m.group(1).replace("-", "_"))
                args = self._ParseTclWords(m.group(2),
                                           { "srcdir" : root })
                f(line_num, args, context)

        # If this test does not need to be run on this target, stop.
        if self._selected == 0:
            self._RecordDejaGNUOutcome(result,
                                       self.UNSUPPORTED,
                                       self._name)
            return

        # Run the tool being tested and process its output.
        file = self._RunDGToolPortion(path, tool_flags, context, result)

        # Run the executable generated (if applicable).
        self._RunDGExecutePortion(file, context, result)

        # Run dg-final tests.
        for c, a in self._final_commands:
            self._ExecuteFinalCommand(c, a, context, result)

        # For backward compatibility the function parameter overrides
        # the extension argument, if defined.
        do_keep_output = keep_output is None and self.keep_output or keep_output
        # Remove the output file.
        if not do_keep_output:
            try:
                os.remove(file)
            except:
                pass

    def _RunDGToolPortion(self, path, tool_flags, context, result):
        """Perform the tool-running portions of a DG test.

        Calls '_RunTool' and processes its output.

        returns -- The filename of the generated file."""

        # Run the tool being tested.
        output, file = self._RunTool(path, self._kind,
                                     tool_flags + self._options,
                                     context,
                                     result)

        # Check to see if the right diagnostic messages appeared.
        # This algorithm takes time proportional to the number of
        # lines in the output times the number of expected
        # diagnostics.  One could do much better, but DejaGNU does
        # not.
        for l, k, x, p, c in self._diagnostics:
            # Remove all occurrences of this diagnostic from the
            # output.
            if l is not None:
                ldesc = "%d" % l
                l = ":%s:" % ldesc
            else:
                ldesc = ""
                l = ldesc
            output, matched = re.subn(r"(?m)^.+" + l + r".*(" + p + r").*$",
                                      "", output)
            # Record an appropriate test outcome.
            message = ("%s %s (test for %s, line %s)"
                       % (self._name, c,
                          self.__diagnostic_descriptions[k], ldesc))
            if matched:
                if k == self.__DIAG_BOGUS:
                    outcome = self.FAIL
                else:
                    outcome = self.PASS
            else:
                if k == self.__DIAG_BOGUS:
                    outcome = self.PASS
                else:
                    outcome = self.FAIL
                    
            self._RecordDejaGNUOutcome(result, outcome, message, x)

        # Remove tool-specific messages that can be safely ignored.
        output = self._PruneOutput(output)
            
        # Remove leading blank lines.
        output = re.sub(r"^\n+", "", output)
        # If there's any output left, the test fails.
        message = self._name + " (test for excess errors)"
        if self._excess_errors_expected:
            expected = self.FAIL
        else:
            expected = self.PASS
        if output != "":
            self._RecordDejaGNUOutcome(result, self.FAIL,
                                       message, expected)
            result["DGTest.excess_errors"] = result.Quote(output)
        else:
            self._RecordDejaGNUOutcome(result, self.PASS,
                                       message, expected)

        return file


    def _RunDGExecutePortion(self, file, context, result):
        """Perform the executable-running portions of a DG test.

        If this is a "run" test, runs the executable generated by the
        tool and checks its output."""

        # Run the generated program.
        if self._kind == "run":
            if not os.path.exists(file):
                message = (self._name
                           + " compilation failed to produce executable")
                self._RecordDejaGNUOutcome(result, self.WARNING, message)
            else:
                outcome = self._RunTargetExecutable(context, result, file)
                # Add an annotation indicating what happened.
                message = self._name + " execution test"
                self._RecordDejaGNUOutcome(result, outcome, message,
                                           self._expectation)


    def _ExecuteFinalCommand(self, command, args, context, result):
        """Run a command specified with 'dg-final'.

        'command' -- A string giving the name of the command.
        
        'args' -- A list of strings giving the arguments (if any) to
        that command.

        'context' -- The 'Context' in which this test is running.

        'result' -- The 'Result' of this test."""

        raise self.DGException, \
              'dg-final command \"%s\" is not implemented' % command
        
        
    def _PruneOutput(self, output):
        """Remove unintersting messages from 'output'.

        'output' -- A string giving the output from the tool being
        tested.

        returns -- A modified version of 'output'.  This modified
        version does not contain tool output messages that are
        irrelevant for testing purposes."""

        raise NotImplementedError
    
        
    def _RunTool(self, path, kind, options, context, result):
        """Run the tool being tested.

        'path' -- The path to the test file.
        
        'kind' -- The kind of test to perform.

        'options' -- A list of strings giving command-line options to
        provide to the tool.

        'context' -- The 'Context' for the test execution.

        'result' -- The QMTest 'Result' for the test.

        returns -- A pair '(output, file)' where 'output' consists of
        any messages produced by the compiler, and 'file' is the name
        of the file produced by the compilation, if any."""

        raise NotImplementedError
        
        
    def _DGdo(self, line_num, args, context):
        """Emulate the 'dg-do' command.

        'line_num' -- The line number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if len(args) > 2:
            self._Error("dg-do: too many arguments")

        if len(args) >= 2:
            code = self._ParseTargetSelector(args[1], context)
            if code == "S":
                self._selected = 1
            elif code == "N":
                if self._selected != 1:
                    self._selected = 0
            elif code == "F":
                self._expectation = Result.FAIL
        else:
            self._selected = 1
            self._expectation = Result.PASS

        kind = args[0]
        if kind not in self.__test_kinds:
            self._Error("dg-do: syntax error")
            
        self._kind = kind


    def _DGfinal(self, line_num, args, context):
        """Emulate the 'dg-final' command.

        'line_num' -- The line number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if len(args) > 1:
            self._Error("dg-final: too many arguments")

        words = self._ParseTclWords(args[0])
        self._final_commands.append((words[0], words[1:]))
            
        
    def _DGoptions(self, line_num, args, context):
        """Emulate the 'dg-options' command.

        'line_num' -- The line number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if len(args) > 2:
            self._Error("'dg-options': too many arguments")

        if len(args) >= 2:
            code = self._ParseTargetSelector(args[1], context)
            if code == "S":
                self._options = self._ParseTclWords(args[0])
            elif code != "N":
                self._Error("'dg-options': 'xfail' not allowed here")
        else:
            self._options = self._ParseTclWords(args[0])


    def _DGbogus(self, line_num, args, context):
        """Emulate the 'dg-bogus' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""
        
        self.__ExpectDiagnostic(self.__DIAG_BOGUS, line_num, args, context)


    def _DGwarning(self, line_num, args, context):
        """Emulate the 'dg-warning' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        self.__ExpectDiagnostic(self.__DIAG_WARNING, line_num, args, context)

        
    def _DGerror(self, line_num, args, context):
        """Emulate the 'dg-error' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        self.__ExpectDiagnostic(self.__DIAG_ERROR, line_num, args, context)


    def _DGexcess_errors(self, line_num, args, context):
        """Emulate the 'dg-excess-errors' command.

        'line_num' -- The line number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if len(args) > 2:
            self._Error("'dg-excess-errors': too many arguments")

        if len(args) >= 2:
            code = self._ParseTargetSelector(args[1], context)
            if code in ("F", "S"):
                self._excess_errors_expected = True
        else:
            self._excess_errors_expected = True


    def __ExpectDiagnostic(self, kind, line_num, args, context):
        """Register an expected diagnostic.

        'kind' -- The kind of diagnostic expected.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if len(args) > 4:
            self._Error("'dg-" + kind + "': too many arguments")

        if len(args) >= 4:
            l = args[3]
            if l == "0":
                line_num = None
            elif l != ".":
                line_num = int(args[3])

        # Parse the target selector, if any.
        expectation = self.PASS
        if len(args) >= 3:
            code = self._ParseTargetSelector(args[2], context)
            if code == "N":
                return
            if code == "F":
                expectation = self.FAIL

        if len(args) >= 2:
            comment = args[1]
        else:
            comment = ""
            
        self._diagnostics.append((line_num, kind, expectation,
                                  args[0], comment))
        
        
    def _ParseTargetSelector(self, selector, context):
        """Parse the target 'selector'.

        'selector' -- A target selector.

        'context' -- The 'Context' in which the test is running.

        returns -- For a 'target' selector, 'S' if this test should be
        run, or 'N' if it should not.  For an 'xfail' selector, 'F' if
        the test is expected to fail; 'P' if if not.

        This function emulates dg-process-target."""

        # Split the selector into words.  In the DejaGNU code, this
        # operation is accomplished by treating the string as Tcl
        # list.
        words = selector.split()
        # Check the first word.
        if words[0] != "target" and words[0] != "xfail":
            raise QMException, "Invalid selector."
        # The rest of the selector is a space-separate list of
        # patterns.  See if any of them are matched by the current
        # target platform.
        target = self._GetTarget(context)
        match = 0
        for p in words[1:]:
            if (p == "native" and self._IsNative(context)
                or fnmatch.fnmatch(target, p)):
                match = 1
                break

        if words[0] == "target":
            if match:
                return "S"
            else:
                return "N"
        else:
            if match:
                return "F"
            else:
                return "P"
        
