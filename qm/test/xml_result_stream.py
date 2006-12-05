########################################################################
#
# File:   xml_result_stream.py
# Author: Mark Mitchell
# Date:   10/10/2001
#
# Contents:
#   QMTest XMLResultSream class.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# imports
########################################################################

from   qm.test.result_stream import *
import qm.xmlutil
import xml.dom.ext

########################################################################
# classes
########################################################################

class XMLResultStream(ResultStream):
    """An 'XMLResultStream' writes out results as XML.

    An 'XMLResultStream' writes out results as XML.  This stream is
    used to write out QMTest results files.  The DTD is designed in
    such a way that if QMTest is terminated in the middle of a test
    run, the file will still be nearly valid, as long as the
    interruption did not occur in the midst of writing out an
    individual result.  The closing tag for the results file will
    be missing."""

    def __init__(self, file):
        """Construct an 'XMLResultStream'.

        'file' -- The file object to which the results should be
        written.  Closing the file remains the responsibility of the
        caller."""

        # Initialize the base class.
        ResultStream.__init__(self)
        
        self.__file = file
        # Create an XML document, since the DOM API requires you
        # to have a document when you create a node.
        self.__document = qm.xmlutil.create_dom_document(
            public_id=qm.test.base.dtds["result"],
            dtd_file_name="result.dtd",
            document_element_tag="results")
        # Write out the prologue.
        self.__file.write("<?xml version='1.0' encoding='ISO-8859-1'?>\n")
        self.__file.write('<!DOCTYPE results PUBLIC "%s" "%s">\n'
                          % (qm.test.base.dtds["result"],
                             qm.xmlutil.make_system_id("result.dtd")))
        # Begin the list of results.
        self.__file.write("<results>\n")


    def WriteResult(self, result):
        """Output a test or resource result.

        'result' -- A 'Result'."""

        element = result.MakeDomNode(self.__document)
        xml.dom.ext.PrettyPrint(element, self.__file, indent=" ",
                                encoding="ISO-8859-1")
        

    def Summarize(self):
        """Output summary information about the results.

        When this method is called, the test run is complete.  Summary
        information should be displayed for the user, if appropriate.
        Any finalization, such as the closing of open files, should
        also be performed at this point."""

        # Finish the list of results.
        self.__file.write("\n</results>\n")

        ResultStream.Summarize(self)
