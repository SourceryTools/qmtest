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
########################################################################

from   compiler import *
from   compiler_test import *
import dircache
import os
from   qm.attachment import *
from   qm.test.directory_suite import *
from   qm.test.database import *
import re
import string

########################################################################
# Classes
########################################################################

class GPPDatabase(Database):
    """A 'GPPDatabase' is a G++ test database."""

    _test_extension = ".C"
    """The extension (including the leading period) that indicates
    that a file is a test."""

    _suite_prefix = "g++."
    """The prefix that indicates that a subdirectory is an implicit
    subsuite."""

    _skip_regexp = re.compile("Skip if not target:\s*(?P<platform>.*)\s*")
    """A compiled regular expression.  When this expression matches
    part of the input file, the 'platform' match group indicates a
    GNU platform triple.  If the current platform does not match this
    value, the test should be skipped on this platform."""

    _additional_source_files_regexp \
        = re.compile("Additional sources:\s*(?P<source_files>.*)\s*")
    """A compiled regular expression.  When this expression matches
    part of the input file, the 'source_files' match group indicates
    additional source files that should be compiled along with the
    main source file."""
        
    def __init__(self, path):
        """Construct a 'GPPDatabase'.

        'path' -- A string containing the absolute path to the directory
        containing the database."""

        Database.__init__(self, path, FileAttachmentStore(self))

    # Methods that deal with tests.

    def GetTestIds(self, directory=".", scan_subdirs=1):
        """Return all test IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all tests located within 'directory',
        as absolute labels."""

        # There are no tests yet.
        test_names = []

        # Compute the path name of the directory in which to start.
        path = self._GetPathFromDirectory(directory)

        # Iterate through all the files and subdirectories in the
        # directory.
        for entry in dircache.listdir(path):
            # Split the file name into its components.
            (base, extension) = os.path.splitext(entry)

            # See if it is a test file.
            if extension == self._test_extension:
                if not qm.label.is_valid(base):
                    print "Invalid test name %s" % base
                    continue
                # Add this test to the list.
                test_names.append(qm.label.join(directory, base))
                # Go on to the next entry in the directory.
                continue

            # Compute the absolute path to entry.
            entry_path = os.path.join(path, entry)
            # Otherwise, see if it is a subdirectory containing more
            # tests.
            if (scan_subdirs and self._GetSuiteNameFromPath(entry)
                and os.path.isdir(entry_path)):
                # Compute the label for the subdirectory.
                subdirectory \
                    = qm.label.join(directory,
                                    entry[len(self._suite_prefix):])
                # Recurse on the subdirectory.
                test_names.extend(self._GetTestIds(subdirectory,
                                                   scan_subdirs))

        return test_names
                

    def GetTest(self, test_id):
        """Return the 'TestDescriptor' for the test named 'test_id'.

        'test_id' -- A label naming the test.

        returns -- A 'TestDescriptor' corresponding to 'test_id'.
        
        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'."""

        # Split the test name into its components.
        (directory, test_name) = qm.label.split(test_id)
        # Compute the file system path corresponding to the test.
        path = os.path.join(self._GetPathFromDirectory(directory),
                            test_name + self._test_extension)
        
        # Read the contents of the file.
        file = open(path)
        contents = file.read()
        file.close()

        # Determine what kind of test this is.
        top_level_suite = qm.label.split_fully(test_id)[0]
        if top_level_suite == "old-deja":
            test_class = "compiler_test.OldDejaGNUTest"
            scanner = OldDejaGNUTest.scanner
        else:
            test_class = "compiler_test.DGTest"
            scanner = DGTest.scanner
        
        # Figure out what mode of test is indicated.
        mode = scanner.GetTestMode(contents)

        # See if this test indicates particular compiler options.
        options = scanner.GetCompilerOptions(contents)

        # Construct the set of source files.
        source_files = [path]
        match = self._additional_source_files_regexp.search(contents)
        if match:
            for sf in string.split(match.group('source_files')):
                source_files.append(os.path.join(os.path.dirname(path), sf))

        # Create the descriptor arguments.
        attachments = []
        for sf in source_files:
            basename = os.path.basename(sf)
            attachment = Attachment("text/plain", basename,
                                    basename, sf,
                                    self.GetAttachmentStore())
            attachments.append(attachment)
        arguments = {'mode' : mode,
                     'source_files' : attachments,
                     'options' : options,
                     # The "old-dejagnu" harness does not treat the
                     # severity specified as significant.
                     'is_severity_significant' : 0,
                     # Similarly, the name of the file is not
                     # significant.
                     'is_file_significant' : 0}
        # See if the test is not supposed to be skipped on this platform.
        match = self._skip_regexp.search(contents)
        if match:
            platform = match.group('platform')
            arguments['platforms'] = [platform]
        # Create the TestDescriptor.
        descriptor = TestDescriptor(self, test_id, test_class, arguments)

        # Set the working directory for the test.
        descriptor.SetWorkingDirectory(os.path.dirname(path))

        return descriptor
        
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
        path = self._GetPathFromDirectory(suite_id)
        
        # If it's a subdirectory, return a 'DirectorySuite'.
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

        # Iterate through all the files and subdirectories in the
        # directory.
        for entry in dircache.listdir(path):
            # See if this entry could name a suite.
            suite = self._GetSuiteNameFromPath(entry)
            # If it's not a valid name, skip it.
            if not suite:
                continue
            # We're only interested in subdirectories.
            suite_path = os.path.join(path, entry)
            if not os.path.isdir(suite_path):
                continue
            # Add the name of the suite to the list.
            suite_name = qm.label.join(directory, suite)
            suite_names.append(suite_name)
            # Scan subdirectories if requested.
            if scan_subdirs:
                suite_names.extend(self.GetSuiteIds(suite_name,
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

    def GetSubdirectories(self, directory):
        """Return the immediate subdirectories of 'directory'.

        'directory' -- A label indicating a directory in the database.

        returns -- A sequence of (relative) labels indictating the
        immediate subdirectories of 'directory'.  For example, if "a.b"
        and "a.c" are directories in the database, this method will
        return "b" and "c" given "a" as 'directory'."""

        # There are no subdirectories yet.
        subdirectories = []
        
        # Compute the file system path corresponding to directory.
        path = self._GetPathFromDirectory(directory)

        # Go through all of the subdirectories in that directory.
        for file in dircache.listdir(path):
            # Check for the required prefix first.  (If we checked
            # os.path.isdir first, we would end up calling 'stat' on
            # every file in the directory.)
            suite = self._GetSuiteNameFromPath(file)
            if not suite:
                continue
            # We're only interested in directories.
            if not os.path.isdir(os.path.join(path, file)):
                continue
            # Add the suite to the list of subdirectories.
            subdirectories.append(suite)

        return subdirectories
            
        
    def _GetPathFromDirectory(self, directory):
        """Return the path corresponding to 'directory'.

        'directory' -- A label indicating a directory in the database.

        reutrns -- A string giving the file system path corresponding
        to 'directory'."""

        # Compute the path name of the directory in which to start.
        path = self.GetPath()
        # For each component of the label, add a subdirectory.
        for subdirectory in qm.label.split_fully(directory):
            path = os.path.join(path, self._suite_prefix + subdirectory)

        return path


    def _GetSuiteNameFromPath(self, path):
        """Returns true iff 'path' could name a test suite.

        'path' -- A file name, without any path separators, that might
        name a test suite.

        returns -- 'None', if the 'path' cannot name a test suite.
        Otherwise, the label for the suite named is returned.  This
        routine only checks the file name.  It does not check other
        conditions.  For example, it does not check whether the the
        'path' denotes a directory, as opposed to a file.

        This routine can be used as a predicate; the return value is
        true if and only if 'path' is a valid suite name."""

        # If the prefix isn't correct
        if path[:len(self._suite_prefix)] != self._suite_prefix:
            return None

        return path[len(self._suite_prefix):]
