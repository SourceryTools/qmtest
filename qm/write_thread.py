########################################################################
#
# File:   write_thread.py
# Author: Mark Mitchell
# Date:   2002-11-13
#
# Contents:
#   WriteThread
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from threading import *

########################################################################
# Classes
########################################################################

class WriteThread(Thread):
    """A 'WriteThread' is a thread that writes to a file."""

    def __init__(self, f, data):
        """Construct a new 'WriteThread'.

        'f' -- The file object to which to write.

        'data' -- The string to be written to the file."""

        Thread.__init__(self, None, None, None)

        self.f = f
        self.data = data
        

    def run(self):
        """Write the data to the stream."""
        
        self.f.write(self.data)
	self.f.close()

        
