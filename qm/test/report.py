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
import xml.sax

########################################################################
# Classes
########################################################################

class ReportGenerator:
    """A 'ReportGenerator' generates a test report from one or more
    result files."""

    class Expectation:
        """An internal helper class to facilitate access to expectations."""
        
        def __init__(self, outcome, cause):

            self.outcome, self.cause = outcome, cause
            

    def __init__(self, output, database=None):

        self.output = open(output, 'w+')
        self.database = database
        self.__document = qm.xmlutil.create_dom_document(
            public_id="QMTest/Report",
            document_element_tag="report")


    def GenerateReport(self, arguments):
        """Generates a report file with results collected from a set of
        result files.

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
        self.output.write('<!DOCTYPE report PUBLIC "%s" "%s">\n'
                        % (qm.xmlutil.make_public_id("QMTest/Report"),
                           qm.xmlutil.make_system_id("qmtest/report.dtd")))
        self.output.write("<report>\n")
        self._WriteTestIds(input)

        results = self._CreateResultStreams(input)
        for result in results:
            self._Report(result)
        self.output.write("</report>\n")


    def _CreateResultStreams(self, input):
        """Create result streams for all result files.

        'input' -- A list of pairs of file names referring to result files /
        expectation files. The expectation file member may be None.

        returns -- A list of pairs of ResultStream / Expectation objects."""

        results = []
        for result_file, exp_file in input:
            try:
                result = base.load_results(open(result_file, "rb"), self.database)
            except IOError, e:
                raise PythonException("Error reading '%s'"%result_file,
                                      IOError, e)
            except xml.sax.SAXException, e:
                raise PythonException("Error loading '%s'"%result_file,
                                      xml.sax.SAXException, e)
            exp = {}
            if exp_file:
                try:
                    exp_reader = base.load_results(open(exp_file, "rb"),
                                                   self.database)
                    for e in exp_reader:
                        if e.GetKind() == Result.TEST:
                            outcome = e.GetOutcome()
                            cause = e.get('qmtest.cause')
                            exp[e.GetId()] = ReportGenerator.Expectation(outcome,
                                                                         cause)
                except IOError, e:
                    raise PythonException("Error reading '%s'"%exp_file,
                                          IOError, e)
                except xml.sax.SAXException, e:
                    raise PythonException("Error loading '%s'"%exp_file,
                                          xml.sax.SAXException, e)
            results.append((result, exp))
        return results
    

    def _WriteTestIds(self, input):
        """Generate an entry in the output containing a list of all
        available test ids. This list is obtained from the database
        if it is present, or else by taking the union of all tests
        reported in the result objects.

        'input' -- A list of result / expectation file pairs.

        returns -- None."""

        self.output.write("<suite>\n")
        test_ids = []
        suite_ids = []
        if self.database:
            test_ids, suite_ids = self.database.ExpandIds([''])
        else:
            for r, e in self._CreateResultStreams(input):
                for exp in e:
                    if not exp in test_ids:
                        test_ids.append(exp)
                for result in r:
                    if not result.GetId() in test_ids:
                        test_ids.append(result.GetId())
        for t in test_ids:
            self.output.write("<test id=\"%s\" />\n"%t)
        self.output.write("</suite>\n")


    def _Report(self, results):
        """Write one set of results into the report.

        'results' -- ResultReader the results are to be read from.

        'expectations' -- ResultReader the expectations are to be read from.
        This may be None.

        returns -- None."""

        self.output.write("<results>\n")
        annotations = results[0].GetAnnotations()
        for key, value in annotations.iteritems():

            element = self.__document.createElement("annotation")
            element.setAttribute("key", key)
            text = self.__document.createTextNode(value)
            element.appendChild(text)
            element.writexml(self.output, addindent = " ", newl = "\n")
            
        for result in results[0]:
            # Inject two new annotations containing the expectation values.
            if results[1]:
                exp = results[1].get(result.GetId())
                if exp:
                    result['qmtest.expected_outcome'] = exp.outcome
                    if exp.cause:
                        result['qmtest.expected_cause'] = exp.cause
            element = result.MakeDomNode(self.__document)
            element.writexml(self.output, indent = " ", addindent = " ",
                             newl = "\n")


        self.output.write("</results>\n")


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
