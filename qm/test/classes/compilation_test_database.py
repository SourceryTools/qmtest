########################################################################
#
# File:   compilation_test_database.py
# Author: Stefan Seefeld
# Date:   2006-07-28
#
# Contents:
#   CompilationTestDatabase.
#
# Copyright (c) 2006 by CodeSourcery, Inc.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import os, dircache
from   qm.common import parse_string_list
from   qm.extension import get_class_arguments
from   qm.fields import *
import qm.label
import qm.structured_text
import qm.test.base
from   qm.test.database import *
from   qm.test.suite import *
from   qm.test import context
from   qm.test.classes.explicit_suite import ExplicitSuite
from   qm.test.classes import compilation_test
from   qm.test.classes.compiler import Compiler
from   qm.test.classes.compiler_test import CompilationStep
from   qm.test.classes.compiler_table import CompilerTable

########################################################################
# classes
########################################################################

class CompilationTest(compilation_test.CompilationTest):
    """A CompilationTest fetches compilation parameters from environment
    variables CPPFLAGS, <lang>_options, and <lang>_ldflags in addition
    to the CompilerTable-related parameters."""

    options = SetField(TextField(), computed="true")
    ldflags = SetField(TextField(), computed="true")
    source_files = SetField(TextField(), computed="true")
    executable = TextField(computed="true")
    language = TextField()


    def _GetCompilationSteps(self, c):

        lang = self.language
        compiler = c['CompilerTable.compilers'][lang]
        label_components = self.GetDatabase().GetLabelComponents(self.GetId())
        label_components[-1] = os.path.splitext(label_components[-1])[0]
        selector = '.'.join(label_components)
        path = c.GetDerivedValue(selector, lang + '_path')
        if path:
            compiler = Compiler(path, compiler.GetOptions(), compiler.GetLDFlags())
        options = (parse_string_list(c.GetDerivedValue(
            selector, 'CPPFLAGS', '')) +
                   parse_string_list(c.GetDerivedValue(
            selector, lang + '_options', '')))
        ldflags = (parse_string_list(c.GetDerivedValue(
            selector, lang + '_ldflags', '')))

        return [CompilationStep(compiler,
                                Compiler.MODE_LINK, self.source_files,
                                self.options + options,
                                self.ldflags + ldflags,
                                self.executable, [])]


class CompilationTestDatabase(Database):
    """A 'CompilationTestDatabase' test database maps source code files to
    compilation tests."""

    srcdir = TextField(title = "Source Directory",
                       description = "The root of the test suite's source tree.")
    excluded_subdirs = SetField(TextField(),
                                default_value = ['QMTest', 'CVS', '.svn', 'build'])
    test_extensions = DictionaryField(TextField(),
                                      EnumerationField(enumerals = ['c', 'cplusplus']),
                                      default_value = {'.c':'c',
                                                       '.cpp':'cplusplus',
                                                       '.cxx':'cplusplus',
                                                       '.cc':'cplusplus',
                                                       '.C':'cplusplus',
                                                       '.f':'fortran'})
    _is_generic_database = True
    

    def __init__(self, path, arguments):

        self.label_class = "file_label.FileLabel"
        self.modifiable = "false"
        # Initialize the base class.
        super(CompilationTestDatabase, self).__init__(path, **arguments)

        
    def GetSubdirectories(self, directory):

        dirname = os.path.join(self.srcdir, directory)
        return [subdir for subdir in dircache.listdir(dirname)
                if (os.path.isdir(os.path.join(dirname, subdir)) and
                    subdir not in self.excluded_subdirs)]


    def GetIds(self, kind, directory = '', scan_subdirs = 1):

        dirname = os.path.join(self.srcdir, directory)
        if not os.path.isdir(dirname):
            raise NoSuchSuiteError, directory

        if kind == Database.TEST:
            ids = [self.JoinLabels(directory, f)
                   for f in dircache.listdir(dirname)
                   if (os.path.isfile(os.path.join(dirname, f)) and
                       os.path.splitext(f)[1] in self.test_extensions)]

        elif kind == Database.RESOURCE:
            ids = []
            
        else: # SUITE
            ids = [self.JoinLabels(directory, d)
                   for d in self.GetSubdirectories(directory)
                   if d not in self.excluded_subdirs]

        if scan_subdirs:
            for subdir in dircache.listdir(dirname):
                if (subdir not in self.excluded_subdirs
                    and os.path.isdir(os.path.join(dirname, subdir))):
                    dir = self.JoinLabels(directory, subdir)
                    ids.extend(self.GetIds(kind, dir, True))

        return ids
    

    def GetExtension(self, id):

        if not id:
            return DirectorySuite(self, id)
            
        elif id == 'compiler_table':
            return CompilerTable({},
                                 qmtest_id = id,
                                 qmtest_database = self)

        id_components = self.GetLabelComponents(id)
        file_ext = os.path.splitext(id_components[-1])[1]
        if (file_ext in self.test_extensions and
            os.path.isfile(os.path.join(self.srcdir, id))):
            return self._MakeTest(id, self.test_extensions[file_ext])

        elif os.path.isdir(os.path.join(self.srcdir, id)):
            basename = os.path.basename(id)
            if not basename in self.excluded_subdirs:
                return DirectorySuite(self, id)

        else:
            return None


    def _MakeTest(self, test_id, language):


        src = os.path.abspath(os.path.join(self.srcdir, test_id))
        # Construct a unique name for the executable as it may be
        # kept for failure analysis.
        executable = os.path.splitext(os.path.basename(test_id))[0]
        if sys.platform == 'win32':
            executable += '.exe'

        resources = ['compiler_table']
        arguments = {}
        arguments['language'] = language
        arguments['source_files'] = [src]
        arguments['executable'] = executable
        arguments['resources'] = resources

        return CompilationTest(arguments,
                               qmtest_id = test_id,
                               qmtest_database = self)

