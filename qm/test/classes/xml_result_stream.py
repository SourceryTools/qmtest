########################################################################
#
# File:   xml_result_stream.py
# Author: Mark Mitchell
# Date:   10/10/2001
#
# Contents:
#   XMLResultStream, XMLResultReader
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.xmlutil
from   qm.test.file_result_reader import FileResultReader
from   qm.test.result import Result
from   qm.test.file_result_stream import FileResultStream

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
        super(XMLResultStream, self).__init__(arguments)
        
        # Create an XML document, since the DOM API requires you
        # to have a document when you create a node.
        self.__document = qm.xmlutil.create_dom_document(
            public_id="QMTest/Result",
            document_element_tag="results")
        # Write out the prologue.
        self.file.write("<?xml version='1.0' encoding='ISO-8859-1'?>\n")
        self.file.write('<!DOCTYPE results PUBLIC "%s" "%s">\n'
                        % (qm.xmlutil.make_public_id("QMTest/Result"),
                           qm.xmlutil.make_system_id("qmtest/result.dtd")))
        # Begin the list of results.
        self.file.write("<results>\n")


    def WriteAnnotation(self, key, value):

            element = self.__document.createElement("annotation")
            element.setAttribute("key", key)
            text = self.__document.createTextNode(value)
            element.appendChild(text)
            element.writexml(self.file)
            # Following increases readability of output:
            self.file.write("\n")


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



class XMLResultReader(FileResultReader):
    """Reads in 'Result's from an XML-formatted results file.

    To write such a file, see 'XMLResultStream'."""

    def __init__(self, arguments):

        super(XMLResultReader, self).__init__(arguments)

        document = qm.xmlutil.load_xml(self.file)
        node = document.documentElement
        results = qm.xmlutil.get_children(node, "result")
        self.__node_iterator = iter(results)

        # Read out annotations
        self._annotations = {}
        annotation_nodes = qm.xmlutil.get_children(node, "annotation")
        for node in annotation_nodes:
            key = node.getAttribute("key")
            value = qm.xmlutil.get_dom_text(node)
            self._annotations[key] = value


    def GetAnnotations(self):

        return self._annotations


    def _result_from_dom(self, node):
        """Extract a result from a DOM node.

        'node' -- A DOM node corresponding to a "result" element.

        returns -- A 'Result' object."""

        assert node.tagName == "result"
        # Extract the outcome.
        outcome = qm.xmlutil.get_child_text(node, "outcome")
        # Extract the test ID.
        test_id = node.getAttribute("id")
        kind = node.getAttribute("kind")
        # Build a Result.
        result = Result(kind, test_id, outcome)
        # Extract properties, one for each property element.
        for property_node in node.getElementsByTagName("property"):
            # The name is stored in an attribute.
            name = property_node.getAttribute("name")
            # The value is stored in the child text node.
            value = qm.xmlutil.get_dom_text(property_node)
            # Store it.
            result[name] = value

        return result


    def GetResult(self):

        try:
            return self._result_from_dom(self.__node_iterator.next())
        except StopIteration:
            return None

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
