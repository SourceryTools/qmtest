########################################################################
#
# File:   report.py
# Author: Stefan Seefeld
# Date:   2005-02-13
#
# Contents:
#   QMTest ReportGenerator class.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm
import qm.xmlutil
from qm.common import PythonException
from qm.test import base
from qm.test.result import Result
from qm.test.reader_test_run import ReaderTestRun
import xml.sax
import sys

########################################################################
# Classes
########################################################################

class ReportGenerator:
    """A 'ReportGenerator' generates a test report from one or more
    result files."""

    def __init__(self, output, database=None):

        if output and output != '-':
            self.output = open(output, 'w+')
        else:
            self.output = sys.stdout
        self.database = database
        self.__document = qm.xmlutil.create_dom_document(
            public_id="QMTest/Report",
            document_element_tag="report")


    def GenerateReport(self, flat, arguments):
        """Generates a report file with results collected from a set of
        result files.

        'flat' -- True to indicate a flat result listing, False if tests should be
        reported according to the database directory structure.

        'arguments' -- command arguments of the form [result [-e expectation]]+

        returns -- None."""

        # Construct a list of (result / expectation file) tuples.
        # As the expectation file is optional, see whether there
        # is an '-e' option, and then adjust the remainder accordingly.
        input = []
        while arguments:
            if len(arguments) >= 3 and arguments[1] == '-e':
                input.append((arguments[0], arguments[2]))
                arguments = arguments[3:]
            else:
                input.append((arguments[0],None))
                arguments = arguments[1:]

        # Write out the prologue.
        self.output.write("<?xml version='1.0' encoding='ISO-8859-1'?>\n")
        self.output.write("<report>\n")

        test_runs = self._LoadTestRuns(input)

        self.output.write("  <runs>\n")
        for test_run, expectations in test_runs:
            self.output.write("  <run>\n")
        
            annotations = test_run.GetAnnotations()
            for key, value in annotations.iteritems():

                element = self.__document.createElement("annotation")
                element.setAttribute("key", key)
                text = self.__document.createTextNode(value)
                element.appendChild(text)
                element.writexml(self.output, addindent = " ", newl = "\n")
            self.output.write("  </run>\n")
        self.output.write("  </runs>\n")

        if flat:
            self._ReportFlat(test_runs)
        else:
            self._Report(test_runs)
            
        self.output.write("</report>\n")


    def _LoadTestRuns(self, input):
        """Load test runs from the provided input.

        'input' -- A list of pairs of file names referring to result files /
        expectation files. The expectation file member may be None.

        returns -- A list of pairs of TestRun objects."""

        runs = []
        for result_file, exp_file in input:
            results = None
            expectations = None

            try:
                file = result_file
                reader = base.load_results(file, self.database)
                results = ReaderTestRun(reader)
                if exp_file:
                    file = exp_file
                    reader = base.load_results(file, self.database)
                    expectations = ReaderTestRun(reader)
            except IOError, e:
                raise PythonException("Error reading '%s'"%file, IOError, e)
            except xml.sax.SAXException, e:
                raise PythonException("Error loading '%s'"%file,
                                      xml.sax.SAXException, e)
            runs.append((results, expectations))
        return runs


    def _GetIds(self, test_runs):
        """Return a list of ids to report results from.
        This list is obtained from the database if it is present,
        or else by taking the union of all items reported in the
        test runs.

        'test_runs' -- A list of result / expectation table pairs.

        returns -- The tuple of resource-setup-ids, test-ids,
        and resource-cleanup-ids."""

        test_ids = []
        resource_setup_ids = []
        resource_cleanup_ids = []
        if self.database:
            test_ids = self.database.GetTestIds()
            resource_setup_ids = self.database.GetResourceIds()
            resource_cleanup_ids = resource_setup_ids
        else:
            for results, e in test_runs:
                for result in results.GetAllResults("", Result.TEST):
                    if not result.GetId() in test_ids:
                        test_ids.append(result.GetId())
                for result in results.GetAllResults("", Result.RESOURCE_SETUP):
                    if not result.GetId() in resource_setup_ids:
                        resource_setup_ids.append(result.GetId())
                for result in results.GetAllResults("", Result.RESOURCE_CLEANUP):
                    if not result.GetId() in resource_cleanup_ids:
                        resource_cleanup_ids.append(result.GetId())
        return test_ids, resource_setup_ids, resource_cleanup_ids


    def _ReportFlat(self, test_runs):
        """Generate test report with the given set of test runs.
        The report will contain a flat list of item ids.

        'test_runs' -- List of pairs of TestRun objects."""

        ids = self._GetIds(test_runs)
        kinds = [Result.TEST, Result.RESOURCE_SETUP, Result.RESOURCE_CLEANUP]

        element = self.__document.createElement('results')
        # Report all items, sorted by their kind.
        for k in [0, 1, 2]:
            for id in ids[k]:
                self._ReportItem(kinds[k], id, id, test_runs, element)

        element.writexml(self.output, indent = " ", addindent = " ",
                         newl = "\n")


    def _Report(self, test_runs):
        """Generate test report with the given set of test runs.
        The report will contain a tree structure with items appearing in their
        respective subdirectory.

        'test_runs' -- List of pairs of TestRun objects."""

        element = self.__document.createElement('results')
        root = self._ReportSubdirectory('', test_runs, element)
        root.writexml(self.output, indent=" ", addindent=" ", newl="\n")


    def _ReportSubdirectory(self, directory, test_runs, element=None):
        """Generate a DOM node for the given directory containing its results.

        'directory' -- The directory for which to generate the report node.

        'test_runs' -- The List of TestRuns.

        'element' -- DOM element to store results into.
        If this is None, an element will be created.
        
        returns -- DOM element node containing the xmlified results."""

        if not element:
            element = self.__document.createElement('subdirectory')
            element.setAttribute('name', directory)

        # Start with the subdirectories.
        for dir in self.database.GetSubdirectories(directory):
            child = self._ReportSubdirectory(self.database.JoinLabels(directory, dir),
                                             test_runs)
            element.appendChild(child)

        # Report all items, sorted by kind.
        for id in self.database.GetIds('test', directory, False):
            self._ReportItem('test', id, self.database.SplitLabel(id)[1],
                             test_runs, element)
        for id in self.database.GetIds('resource', directory, False):
            self._ReportItem('resource_setup', id, self.database.SplitLabel(id)[1],
                             test_runs, element)
            self._ReportItem('resource_cleanup', id, self.database.SplitLabel(id)[1],
                             test_runs, element)
        return element


    def _ReportItem(self, kind, item_id, name, test_runs, parent):
        """Report a single item.

        'kind' -- The kind of item to report.

        'item_id' -- The item id to report.

        'name' -- The item's name (usually either the absolute or relative id).

        'test_runs' -- The list of test runs.

        'parent' -- An XML element to insert new nodes into."""

        # Create one item node per id...
        item = self.__document.createElement('item')
        item.setAttribute('id', name)
        item.setAttribute('kind', kind)
        parent.appendChild(item)

        # ...and fill it with one result per test run.
        for results, expectations in test_runs:
            result = results.GetResult(item_id, kind)
            if not result:
                result = Result(kind, item_id, Result.UNTESTED)
            # Inject two new annotations containing the expectation values.
            if expectations:
                exp = expectations.GetResult(item_id, kind)
                if exp:
                    result['qmtest.expected_outcome'] = exp.GetOutcome()
                    cause = exp.get('qmtest.cause')
                    if cause:
                        result['qmtest.expected_cause'] = cause

            child = result.MakeDomNode(self.__document)
            # Remove redundant attributes
            child.removeAttribute('id')
            child.removeAttribute('kind')
            item.appendChild(child)
