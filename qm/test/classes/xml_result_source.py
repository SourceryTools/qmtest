########################################################################
#
# File:   xml_result_source.py
# Author: Nathaniel Smith
# Date:   2003-06-23
#
# Contents:
#   XMLResultSource
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.xmlutil
from   qm.test.file_result_source import FileResultSource
from   qm.test.result import Result

########################################################################
# Classes
########################################################################

class XMLResultSource(FileResultSource):
    """Reads in 'Result's from an XML-formatted results file.

    To write such a file, see 'XMLResultStream'."""

    def __init__(self, arguments):

        super(XMLResultSource, self).__init__(arguments)

        document = qm.xmlutil.load_xml(self.file)
        node = document.documentElement
        results = qm.xmlutil.get_children(node, "result")
        self.__node_iterator = iter(results)


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
