########################################################################
#
# File:   queue.py
# Author: Mark Mitchell
# Date:   01/07/2002
#
# Contents:
#   Queue
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Notes
########################################################################

# On systems that do not support threads, the Python Queue module
# does not work.  This is probably a bug in Python; if there are
# no threads, there is no difficulty in being threadsafe, and the
# module should simply omit the calls to acquire and release locks.
# This module is a manual implementation of this idea, with the
# limitation that the maxsize parameter to the initialization function
# must always be zero.

try:
    import thread

    # If we successfully imported the thread module, we can just use
    # the builtin Queue.
    from Queue import *
except:
    # This code is based on the Python 2.2 Queue.py, but without
    # the threading calls.
    class Empty(Exception):
        "Exception raised by Queue.get(block=0)/get_nowait()."
        pass

    class Queue:
        def __init__(self, maxsize=0):
            """Initialize a queue object with a given maximum size.

            If maxsize is <= 0, the queue size is infinite.
            """
            assert maxsize <= 0
            self._init(maxsize)

        def qsize(self):
            """Return the approximate size of the queue (not reliable!)."""
            n = self._qsize()
            return n

        def empty(self):
            """Return 1 if the queue is empty, 0 otherwise (not reliable!)."""
            n = self._empty()
            return n

        def full(self):
            """Return 1 if the queue is full, 0 otherwise (not reliable!)."""
            n = self._full()
            return n

        def put(self, item, block=1):
            """Put an item into the queue.

            If optional arg 'block' is 1 (the default), block if
            necessary until a free slot is available.  Otherwise (block
            is 0), put an item on the queue if a free slot is immediately
            available, else raise the Full exception.
            """
            self._put(item)

        def put_nowait(self, item):
            """Put an item into the queue without blocking.

            Only enqueue the item if a free slot is immediately available.
            Otherwise raise the Full exception.
            """
            return self.put(item, 0)

        def get(self, block=1):
            """Remove and return an item from the queue.

            If optional arg 'block' is 1 (the default), block if
            necessary until an item is available.  Otherwise (block is 0),
            return an item if one is immediately available, else raise the
            Empty exception.
            """
            if not block and not self.queue:
                raise Empty
            item = self._get()
            return item

        def get_nowait(self):
            """Remove and return an item from the queue without blocking.

            Only get an item if one is immediately available.  Otherwise
            raise the Empty exception.
            """
            return self.get(0)

        # Override these methods to implement other queue organizations
        # (e.g. stack or priority queue).
        # These will only be called with appropriate locks held

        # Initialize the queue representation
        def _init(self, maxsize):
            self.maxsize = maxsize
            self.queue = []

        def _qsize(self):
            return len(self.queue)

        # Check whether the queue is empty
        def _empty(self):
            return not self.queue

        # Check whether the queue is full
        def _full(self):
            return self.maxsize > 0 and len(self.queue) == self.maxsize

        # Put a new item in the queue
        def _put(self, item):
            self.queue.append(item)

        # Get an item from the queue
        def _get(self):
            item = self.queue[0]
            del self.queue[0]
            return item
