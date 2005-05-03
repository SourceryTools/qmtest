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
from qm.test import base
from qm.test.result import Result
import xml.sax

########################################################################
# Classes
########################################################################

class ReportGenerator:
    """A 'ReportGenerator' generates a test report from one or more
    result files."""

    def __init__(self, output, database=None):

        self.output = open(output, 'w+')
        self.database = database
        self.__document = qm.xmlutil.create_dom_document(
            public_id="QMTest/Report",
            document_element_tag="report")


    def GenerateReport(self, result_files):
        """Generates a report file with results collected from a set of
        result files.

        'result_files' -- List of file names specifying result files.

        returns -- None."""

        # Write out the prologue.
        self.output.write("<?xml version='1.0' encoding='ISO-8859-1'?>\n")
        self.output.write('<!DOCTYPE report PUBLIC "%s" "%s">\n'
                        % (qm.xmlutil.make_public_id("QMTest/Report"),
                           qm.xmlutil.make_system_id("qmtest/report.dtd")))
        self.output.write("<report>\n")
        self._WriteTestIds(result_files)

        results = self._CreateResultStreams(result_files)        
        for result in results:
            self._Report(result)
        self.output.write("</report>\n")


    def _CreateResultStreams(self, result_files):
        """Create result streams for all result files.

        'result_files' -- A list of file names referring to result files.

        returns -- A list of 'ResultStream' objects."""

        results = []
        for r in result_files:
            try:
                result = base.load_results(open(r, "rb"), self.database)
                results.append(result)
            except (IOError, xml.sax.SAXException), exception:
                # skip this file
                # FIXME: should we write out a warning ?
                pass
        return results
    

    def _WriteTestIds(self, result_files):
        """Generate an entry in the output containing a list of all
        available test ids. This list is obtained from the database
        if it is present, or else by taking the union of all tests
        reported in the result objects.

        'results' -- A list of result files.

        returns -- None."""

        self.output.write("<suite>\n")
        test_ids = []
        suite_ids = []
        if self.database:
            test_ids, suite_ids = self.database.ExpandIds([''])
        else:
            results = self._CreateResultStreams(result_files)

            for result_reader in results:
                for result in result_reader:
                    if not result.GetId() in test_ids:
                        test_ids.append(result.GetId())
        for t in test_ids:
            self.output.write("<test id=\"%s\" />\n"%t)
        self.output.write("</suite>\n")


    def _Report(self, results):
        """Write one set of results into the report.

        'results' -- ResultReader the results are to be read from.

        returns -- None."""

        self.output.write("<results>\n")
        annotations = results.GetAnnotations()
        for key, value in annotations.iteritems():

            element = self.__document.createElement("annotation")
            element.setAttribute("key", key)
            text = self.__document.createTextNode(value)
            element.appendChild(text)
            element.writexml(self.output, addindent = " ", newl = "\n")
            
        for result in results:
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
