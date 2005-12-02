########################################################################
#
# File:   compiler_table.py
# Author: Mark Mitchell
# Date:   04/16/2003
#
# Contents:
#   CompilerTable
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

"""Support for compiler test databases.

This module contains the 'CompilerTable' resource class which can be
used by compiler test databases to determine which compiler to test
based on context variables provided by the user."""

########################################################################
# Imports
########################################################################

import compiler
import qm
from   qm.test.resource import Resource
from   local_host import LocalHost

########################################################################
# Classes
########################################################################

class CompilerTable(Resource):
    """A map from programming languages to 'Compiler's.

    The 'CompilerTable' resource uses the context to determine which
    compilers the user wants to test.  Test databases containing
    compiler tests should arrange for the tests they compain to depend
    on a 'CompilerTable' resource.

    The first context variable which is examined is
    'CompilerTable.languages'.  The value should be a
    whitespace-separated list of programming language names.  (See
    below for standardized names for some languages.)

    Then, for each language 'l' in the list of languages, the
    following context variables are examined:

    - 'CompilerTable.l_kind'

      The kind of compiler (e.g., "GCC" or "EDG") used to compile
      programs of language 'l'.  The 'kind' must name a class derived
      from 'Compiler'.

    - 'CompilerTable.l_path'

      The path to the compiler for language 'l'.  This path may be
      either absolute or relative.

    - 'CompilerTable.l_options'

      A whitespace-separated list of command-line options to provide
      to the compiler for language 'l'.  These options are passed to
      the constructor for the 'Compiler' object; generally, all tests
      are run with these options, followed by any test-specific
      options.  For example, if the user wants to test the compiler
      when run with '-O2', the user would put '-O2' in the 'l_options'
      context variable.

    The 'CompilerTable' resource provides the following context
    variables to all tests that depend upon the resource:

    - 'CompilerTable.compilers'

       The 'compilers' variable is a map from language names to
       instances of 'Compiler'.  Test classes should obtain the
       'Compiler' to use when compiling source files by using this
       map.

    - 'CompilerTable.target'

       An instance of 'Host' that can be used to run compiler
       programs."""

    LANG_C = "c"
    """The name of the C programming language."""
    
    LANG_CPLUSPLUS = "cplusplus"
    """The name of the C++ programming language."""
    
    def SetUp(self, context, result):

        # There are no compilers yet.
        compilers = {}
        
        # See what programming languages are supported.
        languages = context["CompilerTable.languages"].split()

        # For each language, create a Compiler.
        for l in languages:
            # Retrieve information from the context.
            kind = context["CompilerTable." + l + "_kind"].strip()
            path = context["CompilerTable." + l + "_path"].strip()
            # Look for (optional) command-line options.
            opts = context.get("CompilerTable." + l + "_options",
                               "").split()
            ldflags = context.get("CompilerTable." + l + "_ldflags",
                                  "").split()
            # Find the Python class corresponding to this compiler.
            compiler_class = compiler.__dict__[kind]
            # Instantiate the compiler.
            c = compiler_class(path, opts)
            c.SetLDFlags(ldflags)
            # Store it in the compilers map.
            compilers[l] = c
            
        # Make the table available to tests.
        context["CompilerTable.compilers"] = compilers

        # For backwards compatibility, we recognize this old
        # context variable here.
        interpreter = context.get("CompilerTest.interpreter")
        if interpreter:
            interpreter = interpreter.split()
            arguments = { simulator : interpreter[0],
                          simulator_args : interpreter[1:] }
            target = qm.test.classes.Simulator(arguments)
        else:
            target_desc = context.get("CompilerTable.target")
            if target_desc is None:
                target = LocalHost({})
            else:
                f = lambda n: qm.test.base.get_extension_class(n, "host",
                                                               None)
                host_class, arguments \
                    = qm.extension.parse_descriptor(target_desc.strip(), f)
                target = host_class(arguments)
        context["CompilerTable.target"] = target
