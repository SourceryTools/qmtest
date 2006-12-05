########################################################################
#
# File:   lock.py
# Author: Mark Mitchell
# Date:   07/03/2002
#
# Contents:
#   Lock
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Notes
########################################################################

# On systems that do not support threads, Threading.Lock() is
# unavailable.  This module provides a class with the same interface
# that works on systems without threads.

try:
    import thread
    from threading import Lock, RLock
except:

    class Lock:

        def acquire(blocking = 1):
            # The lock can always be acquired.
            pass

        def release():
            # There is nothing to do to release the lock.
            pass



    class RLock(Lock):

        pass
