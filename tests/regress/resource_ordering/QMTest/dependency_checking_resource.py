########################################################################
#
# File:   dependency_checking_resource.py
# Author: Nathaniel Smith <njs@codesourcery.com>
# Date:   2004-05-20
#
# Contents:
#   A resource that checks that all its dependencies are set up before
#   it is, and aren't torn down until after it is.  Of course, all the
#   resources it depends on have to be of the same type.
#
# Copyright (c) 2004 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.test.resource import Resource

########################################################################
# Classes
########################################################################

_extant_resources = {}

class DependencyCheckingResource(Resource):

    def SetUp(self, context, result):

        # Make sure all resources we depend on have already been
        # set up.
        for r in self.resources:
            if not _extant_resources.has_key(r):
                result.Fail("Resource %s not set up yet" % r)

        # Mark ourself as set up.
        _extant_resources[self.GetId()] = 1


    def CleanUp(self, result):

        # Make sure all resources we depend on are still set up.
        for r in self.resources:
            if not _extant_resources.has_key(r):
                result.Fail("Resource %s torn down already" % r)

        # Mark ourself as no longer set up.
        del _extant_resources[self.GetId()]


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
