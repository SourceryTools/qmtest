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

import qm.test.base
import qm.web
import web

########################################################################
# classes
########################################################################

class DirItem:
    """A generic item in the directory listing.

    'DirItem' objects have two attributes:

    'type' -- One of "test", "suite", or "action".

    'id' -- The item's ID."""

    def __init__(self, type, item_id):
        self.type = type
        self.id = item_id



class DirPageInfo(web.PageInfo):
    """DTML contect for generating DTML template dir.dtml.

    These attributes are available in DTML:

    'path' -- The path to the top of the tree being displayed.  If the
    entire database is displayed, the path is ".".

    'items' -- A sorted list of 'DirItem' objects representing the items
    to display."""

    def __init__(self, request, path):
        # Initialize the base class.
        web.PageInfo.__init__(self, request)
        # Set up attributes.
        self.path = path
        
        database = qm.test.base.get_database()

        # Construct 'DirItem' objects for tests, actions, and suites. 
        test_ids = map(lambda i: DirItem("test", i),
                       database.GetTestIds(path))
        action_ids = map(lambda i: DirItem("action", i),
                         database.GetActionIds(path))
        suite_ids = map(lambda i: DirItem("suite", i),
                        database.GetSuiteIds(path))
        # Mix them together and sort them by ID.
        self.items = suite_ids + test_ids + action_ids
        self.items.sort(lambda i1, i2: cmp(i1.id, i2.id))


    def FormatItem(self, item):
        """Return a representation of 'item', a 'DirItem' object."""

        if item.type == "test":
            return self.FormatTestId(item.id)
        elif item.type == "suite":
            return self.FormatSuiteId(item.id)
        elif item.type == "action":
            return self.FormatActionId(item.id)



########################################################################
# functions
########################################################################

def handle_dir(request):
    """Generate the dir page.

    'request' -- A 'WebRequest' object.

    The request has these fields:

    'path' -- A path in test/action/suite ID space.  If specified, only
    tests and actions in this subtree are displayed, and their IDs are
    displayed relative to this path.  If omitted, the entire contents of
    the test database are shown."""

    # Was a path specified?
    try:
        path = request["path"]
    except:
        # No.  Use the root path.
        path = "."

    # Generate HTML.
    page_info = DirPageInfo(request, path)
    return web.generate_html_from_dtml("dir.dtml", page_info)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
