########################################################################
#
# File:   compilation_test.py
# Author: Stefan Seefeld
# Date:   2005-10-17
#
# Contents:
#   SimpleCompilationTest
#   SimpleCompiledResource
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

from compiler_test import CompilationStep, CompilerTest
from   qm.fields import *
from   qm.test.result import *
from   qm.test.test import *
from   qm.test.resource import *
from   compiler import Compiler
from   local_host import LocalHost

########################################################################
# Classes
########################################################################

class SimpleCompilationTest(CompilerTest):
    """A SimpleCompilationTest compiles source files and optionally runs the
    generated executable."""

    options = SetField(TextField(description="""Test-specific options to pass to the compiler."""))
    source_files = SetField(TextField(description="Source files to be compiled."))
    executable = TextField(description="The name of the executable to be compiled.")
    execute = BooleanField(default_value = True,
        description="Whether or not to run the compiled executable.")
    

    def Run(self, context, result):

        self._MakeDirectory(context)
        CompilerTest.Run(self, context, result)
        self._RemoveDirectory(context, result)


    def _GetCompiler(self, context):
        """The name of the compiler executable is taken from the context variable
        'SimpleCompileTest.compiler_path'."""

        name = context["SimpleCompilationTest.compiler_path"]
        options = context.get("SimpleCompilationTest.compiler_options", [])
        return Compiler(name, options)


    def _GetCompilationSteps(self, context):

        # Compile the executable in a single step so we can apply all
        # options at once.
        return [CompilationStep(Compiler.MODE_LINK, self.source_files,
                                self.options, self.executable, [])]


    def _IsExecutionRequired(self):

        return self.execute


    def _GetTarget(self, context):

        # Run the executable locally.
        return LocalHost({})
        

    def _CheckOutput(self, context, result, prefix, output, diagnostics):

        if output:
            result[prefix + "output"] = result.Quote(output)

        return True


class SimpleCompiledResource(Resource):
    """A SimpleCompiledResource compiles source files into an executable which then
    is available for execution to dependent test instances."""

    options = SetField(TextField(description="Resource-specific options to pass to the compiler."))
    source_files = SetField(TextField(description="Source files to be compiled."))
    executable = TextField(description="The name of the executable to be compiled.")


    def SetUp(self, context, result):

        compiler = SimpleCompilationTest({'options':self.options,
                                          'source_files':self.source_files,
                                          'executable':self.executable,
                                          'execute':False})
        
        compiler.Run(self, context, result)
        context['SimpleCompiledResource.executable'] = self.executable
        

    def CleanUp(self, result):

        # Whether or not to clean up (i.e. remove the executable) is best
        # expressed via the context.
        pass
