########################################################################
#
# File:   compilation_test.py
# Author: Stefan Seefeld
# Date:   2005-10-17
#
# Contents:
#   CompilationTest
#   CompiledResource
#   ExecutableTest
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

from compiler_test import CompilationStep, CompilerTest
from   qm.fields import *
from   qm.test.database import get_database
from   qm.test.result import *
from   qm.test.test import *
from   qm.test.resource import *
import qm.executable
from   qm.extension import parse_descriptor
from   qm.test.base import get_extension_class
from   compiler import Compiler
from   local_host import LocalHost


def _get_host(context, variable):
    """Get a host instance according to a particular context variable.
    Return a default 'LocalHost' host if the variable is undefined.

    'context' -- The context to read the host descriptor from.

    'variable' -- The name to which the host descriptor is bound.

    returns -- A Host instance.

    """

    target_desc = context.get(variable)
    if target_desc is None:
        target = LocalHost({})
    else:
        f = lambda n: get_extension_class(n, "host", get_database())
        host_class, arguments = parse_descriptor(target_desc.strip(), f)
        target = host_class(arguments)
    return target


########################################################################
# Classes
########################################################################

class CompilationTest(CompilerTest):
    """A CompilationTest compiles and optionally runs an executable.
    CompilationTest allows simple cross-testing. To run the executable on
    anything other than localhost, specify a Host descriptor by means of the
    context variable 'CompilationTest.target'."""

    options = SetField(TextField(description="""Test-specific options to pass to the compiler."""))
    ldflags = SetField(TextField(description="""Test-specific link flags to pass to the compiler."""))
    source_files = SetField(TextField(description="Source files to be compiled."))
    executable = TextField(description="The name of the executable to be compiled.")
    execute = BooleanField(default_value = True,
        description="Whether or not to run the compiled executable.")
    

    def Run(self, context, result):

        self._MakeDirectory(context)
        CompilerTest.Run(self, context, result)
        if self.execute:
            self._RemoveDirectory(context, result)


    def _GetCompiler(self, context):
        """The name of the compiler executable is taken from the context variable
        'CompilationTest.compiler_path'."""

        name = context["CompilationTest.compiler_path"]
        options = context.GetStringList("CompilationTest.compiler_options", [])
        ldflags = context.GetStringList("CompilationTest.compiler_ldflags", [])
        return Compiler(name, options, ldflags)


    def _GetCompilationSteps(self, context):

        # Compile the executable in a single step so we can apply all
        # options at once.
        return [CompilationStep(self._GetCompiler(context),
                                Compiler.MODE_LINK, self.source_files,
                                self.options, self.ldflags, self.executable, [])]


    def _IsExecutionRequired(self):

        return self.execute


    def _GetTarget(self, context):

        return _get_host(context, "CompilationTest.target")
        

    def _CheckOutput(self, context, result, prefix, output, diagnostics):

        if output:
            result[prefix + "output"] = result.Quote(output)

        return True


class CompiledResource(Resource):
    """A CompiledResource compiles an executable."""

    options = SetField(TextField(description="Resource-specific options to pass to the compiler."))
    source_files = SetField(TextField(description="Source files to be compiled."))
    executable = TextField(description="The name of the executable to be compiled.")


    def SetUp(self, context, result):

        self._context = context
        self._compiler = CompilationTest({'options':self.options,
                                          'source_files':self.source_files,
                                          'executable':self.executable,
                                          'execute':False},
                                         qmtest_id = self.GetId(),
                                         qmtest_database = self.GetDatabase())
        
        self._compiler.Run(context, result)
        directory = self._compiler._GetDirectory(context)
        self._executable = os.path.join(directory, self.executable)
        context['CompiledResource.executable'] = self._executable
        

    def CleanUp(self, result):

        self._compiler._RemoveDirectory(self._context, result)


class ExecutableTest(Test):
    """An ExecuableTest runs an executable from a CompiledResource.
    ExecutableTest allows simple cross-testing. To run the executable on
    anything other than localhost, specify a Host descriptor by means of the
    context variable 'ExecutableTest.host'."""

    args = SetField(TextField(description="Arguments to pass to the executable."))

    def Run(self, context, result):

        executable = context['CompiledResource.executable']
        host = _get_host(context, 'ExecutableTest.host')
        status, output = host.UploadAndRun(executable, self.args)
        if not result.CheckExitStatus('ExecutableTest.', 'Program', status):
            result.Fail('Unexpected exit_code')        
        if output:
            result['ExecutableTest.output'] = result.Quote(output)

