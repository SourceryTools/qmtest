########################################################################
#
# File:   resource_adapter.py
# Author: Mark Mitchell
# Date:   2005-09-02
#
# Contents:
#   QMTest ResourceAdapter class.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.test.resource import Resource
from qm.test.test import Test

########################################################################
# Classes
########################################################################

class ResourceAdapter(Resource):
    """A 'ResourceAdapter' converts test classes to resource classes.

    If 'C' is a test class, then a class derived from
    'ResourceAdapter' and 'C' (in that order!) will be a resource
    class.  The resource class 'Setup' method is equivalent to the
    'Test' class 'Run' method.  The 'CleanUp' action is empty."""

    def SetUp(self, context, result):
        
        # To set up the resource, just run the underlying test class.
        self.Run(context, result)

    
