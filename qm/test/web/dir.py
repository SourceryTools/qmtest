########################################################################
#
# File:   dir.py
# Author: Alex Samuel
# Date:   2001-04-16
#
# Contents:
#   Web GUI for displaying and manipulating test database contents.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

########################################################################
# imports
########################################################################

import qm.label
import qm.test.base
import qm.web
import web

########################################################################
# classes
########################################################################

class DirPage(web.DtmlPage):
    """A test database directory page.

    These attributes are available in DTML:

    'path' -- The label directory that is being displayed.

    'subdirs' -- A sequence of labels giving the subdirectories of
    this directory.
    
    'test_ids' -- A sequence of labels giving the tests in this
    directory.
    
    'suite_ids' -- A sequence of labels giving the suites in this
    directory.

    'resource_ids' -- A sequence of labels giving the resources in
    this directory."""

    def __init__(self, path):
        """Construct a 'DirPage'.

        'path' -- The label directory to display."""
        
        # Initialize the base class.
        web.DtmlPage.__init__(self, "dir.dtml")
        
        database = qm.test.base.get_database()

        self.path = path
        self.subdir_ids = database.GetSubdirectories(path)
        self.subdir_ids = map(qm.label.AsAbsolute(path), self.subdir_ids)
        self.test_ids = database.GetTestIds(path, scan_subdirs=0)
        self.suite_ids = database.GetSuiteIds(path, scan_subdirs=0)
        self.resource_ids = database.GetResourceIds(path, scan_subdirs=0)


########################################################################
# functions
########################################################################

def handle_dir(request):
    """Generate the dir page.

    'request' -- A 'WebRequest' object.

    The request has these fields:

    'path' -- A path in test/resource/suite ID space.  If specified,
    only tests and resources in this subtree are displayed, and their
    IDs are displayed relative to this path.  If omitted, the entire
    contents of the test database are shown."""

    # Was a path specified?
    try:
        path = request["id"]
    except:
        # No.  Use the root path.
        path = "."
    # Generate HTML.
    return DirPage(path)(request)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
