########################################################################
#
# File:   index.py
# Author: Alex Samuel
# Date:   2001-02-08
#
# Contents:
#   Web form for main QMTrack web page.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

"""Web form for QMTrack menu page."""

########################################################################
# imports
########################################################################

import qm.web
import web

########################################################################
# classes
########################################################################

class IndexPage(web.DtmlPage):
    """Main QMTrack index page."""

    def __init__(self):
        # Initialize the base class.
        web.DtmlPage.__init__(self, "index.dtml")


    def GetIssueClasses(self):
        return self.request.GetSession().idb.GetIssueClasses()


    def GetDefaultIssueClass(self):
        return self.request.GetSession().idb.GetDefaultIssueClass()


    def MakeLogoutForm(self):
        request = qm.web.WebRequest("logout", base=self.request)
        request["_redirect_url"] = self.request.GetUrl()
        return request.AsForm(name="logout_form")



########################################################################
# functions
########################################################################

def handle_index(request):
    """Handle a request for the index page."""

    # Make a new page instance, so the list of issue classes is
    # refreshed. 
    return IndexPage()(request)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
