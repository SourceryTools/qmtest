########################################################################
#
# File:   read_thread.py
# Author: Mark Mitchell
# Date:   2002-11-13
#
# Contents:
#   ReadThread
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

class ReadThread(Thread):
    """An 'ReadThread' is a thread that reads from a file."""

    def __init__(self, f):
        """Construct a new 'ReadThread'.

        'f' -- The file object from which to read."""

        Thread.__init__(self, None, None, None)

        self.f = f
        
            
    def run(self):
        """Read the data from the stream."""

        try:
            self.data = self.f.read()
        except:
            self.data = ""
	self.f.close()

