########################################################################
#
# File:   xml_result_stream.py
# Author: Mark Mitchell
# Date:   10/10/2001
#
# Contents:
#   QMTest XMLResultSream class.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   qm.test.file_result_stream import FileResultStream
import qm.xmlutil

########################################################################
# classes
########################################################################

class XMLResultStream(FileResultStream):
    """An 'XMLResultStream' writes out results as XML.

    An 'XMLResultStream' writes out results as XML.  This stream is
    used to write out QMTest results files.  The DTD is designed in
    such a way that if QMTest is terminated in the middle of a test
    run, the file will still be nearly valid, as long as the
    interruption did not occur in the midst of writing out an
    individual result.  The closing tag for the results file will
    be missing."""

    def __init__(self, arguments):

        # Initialize the base class.
        FileResultStream.__init__(self, arguments)
        
        # Create an XML document, since the DOM API requires you
        # to have a document when you create a node.
        self.__document = qm.xmlutil.create_dom_document(
            public_id=qm.test.base.dtds["result"],
            dtd_file_name="result.dtd",
            document_element_tag="results")
        # Write out the prologue.
        self.file.write("<?xml version='1.0' encoding='ISO-8859-1'?>\n")
        self.file.write('<!DOCTYPE results PUBLIC "%s" "%s">\n'
                        % (qm.test.base.dtds["result"],
                           qm.xmlutil.make_system_id("result.dtd")))
        # Begin the list of results.
        self.file.write("<results>\n")


    def WriteResult(self, result):
        """Output a test or resource result.

        'result' -- A 'Result'."""

        element = result.MakeDomNode(self.__document)
        element.writexml(self.file)
        self.file.write("\n")
        

    def Summarize(self):
        """Output summary information about the results.

        When this method is called, the test run is complete.  Summary
        information should be displayed for the user, if appropriate.
        Any finalization, such as the closing of open files, should
        also be performed at this point."""

        # Finish the list of results.
        self.file.write("\n</results>\n")

        FileResultStream.Summarize(self)
