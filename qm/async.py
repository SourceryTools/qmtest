########################################################################
#
# File:   async.py
# Author: Alex Samuel
# Date:   2001-07-27
#
# Contents:
#   Framework for asynchronous communication.
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

import cPickle
import os
import select
import string
import struct
import sys

########################################################################
# exceptions
########################################################################

class ConnectionClosedException(Exception):
    """Exception indicating that a connection has closed."""

    pass



class NoPacketException(Exception):
    """No complete packet is available to be read from the channel."""
    
    pass



class NothingToWaitForError(Exception):
    """No channel is available for reading or writing."""

    pass


########################################################################
# classes
########################################################################

class Channel:
    """A bidirectional communication channel via file descriptors.

    A channel represents a bidirectiondal data stream.  The two streams
    are distinct.  Data read and written is packetized, using a simple
    wire protocol: each packet is preceded by a four-byte
    integer-encoded packet length (which does not include the length
    itself).  These packets don't have anything to do with the
    underlying transport mechanism; they only control the chunks in
    which data is written or read.

    Note that 'Read' and 'Write' do not cause data actually to be read
    and written.  'Read' returns already-queued data that was previously
    read, and 'Write' enqueues data for later writing.  Call
    '_OnReadReady' and '_OnWriteReady' when the underlying file
    descriptors are ready for the respective operation, to actually move
    the data."""

    def __init__(self, read_fd, write_fd):
        """Construct a channel.

        'read_fd' -- The file descriptor from which to read data.

        'write_fd' -- The file descriptor from which to write data."""
        
        self.__read_fd = read_fd
        self.__write_fd = write_fd
        # A buffer for reading partial packets.
        self.__packet_buffer = None
        self.__packet_length = 0
        # A buffer for storing complete packets that have been read.
        self.__read_packets = []
        # A buffer for all outgoing data (multiple packets may be
        # smushed together).
        self.__write_buffer = ""


    def GetReadFileDescriptor(self):
        """Return the underlying file descriptor for reading data."""

        return self.__read_fd


    def GetWriteFileDescriptor(self):
        """Return the underlying file descriptor for writing data."""

        return self.__write_fd


    def Write(self, data):
        """Enqueue a packet of data for writing."""

        # Encode the length of the data, and prepend it.
        length = struct.pack("!i", len(data))
        # Add the data to the buffer.
        self.__write_buffer = self.__write_buffer + length + data


    def Flush(self):
        """Block until all data queued for writing has been written."""

        while self._HasDataForWrite():
            self._OnWriteReady()


    def IsReadReady(self):
        """Return true if a packet is ready to be read from the channel."""

        return len(self.__read_packets) > 0


    def Read(self):
        """Read a packet of data from the channel.

        This function does not block.

        returns -- A string containing the data of the packet read.

        raises -- 'NoPacketException' if no complete packet is currently
        available to be read."""

        if len(self.__read_packets) > 0:
            return self.__read_packets.pop(0)
        else:
            raise NoPacketException


    def Wait(self):
        """Block until a packet is availabe to read."""
        
        while not self.IsReadReady():
            self._OnReadReady()


    def Close(self):
        """Close the channel.

        postconditions -- The channel may not be used."""

        os.close(self.__read_fd)
        if self.__read_fd != self.__write_fd:
            os.close(self.__write_fd)
        del self.__read_fd
        del self.__write_fd


    def IsOpen(self):
        """Return true if the channel is open."""

        try:
            self.__read_fd
            return 1
        except AttributeError:
            return 0


    def _OnReadReady(self):
        """Process a read pending on the underlying read device.

        raises -- 'ConnectionClosedException' if the underlying device
        has been closed."""

        # Are we in the midst of reading a packet?
        if self.__packet_length == 0:
            # No, so start a new packet.  First read the length of the
            # new packet. 
            encoded_length = os.read(self.__read_fd, 4)
            # Was the connection closed?
            if len(encoded_length) == 0:
                raise ConnectionClosedException
            # Unpack the length.
            self.__packet_length = struct.unpack("!i", encoded_length)[0]
            self.__packet_buffer = ""
            
        # Try to read the remainder of the packet.
        read_length = self.__packet_length - len(self.__packet_buffer)
        data_read = os.read(self.__read_fd, read_length)
        # Was the connection closed mid-packet?
        if len(data_read) == 0:
            raise ConnectionClosedException
        # Append the data to the packet buffer.
        self.__packet_buffer = self.__packet_buffer + data_read

        # Has the entire packet been read?
        if len(self.__packet_buffer) == self.__packet_length:
            # Yes.  Add the packet to the queue of completed packets,
            # and clear the packet buffer.
            self.__read_packets.append(self.__packet_buffer)
            self.__packet_buffer = None
            self.__packet_length = 0


    def _HasDataForWrite(self):
        """Return true if data is buffered for writing."""

        return len(self.__write_buffer) > 0


    def _OnWriteReady(self):
        """Process a write pending on the underlying write device.

        preconditions -- Some data is buffered for writing."""

        assert self._HasDataForWrite()
        # Try to write all remaining data.
        bytes_written = os.write(self.__write_fd, self.__write_buffer)
        # It may be that less data was written.  That's OK; remove only
        # that data from the buffer.
        self.__write_buffer = self.__write_buffer[bytes_written:]



class Multiplexer:
    """Multiplexer for asynchronous communication with multiple channels."""

    def __init__(self):
        """Create a new manager.

        The server initially has no channels attached."""

        self.__channels = []
        self.__channels_by_read_fd = {}
        self.__channels_by_write_fd = {}


    def AddChannel(self, channel):
        """Add a channel to the manager.

        'channel' -- The channel to add.

        raises -- 'ValueError' if there is already a channel with the
        same read file descriptor attached to the manager.

        Does nothing if 'channel' is already attached to this manager."""

        # Don't add the same channel twice.
        if channel in self.__channels:
            return
        # Check arguments.
        read_fd = channel.GetReadFileDescriptor()
        if self.__channels_by_read_fd.has_key(read_fd):
            raise ValueError, "duplicate read file descriptor"
        write_fd = channel.GetWriteFileDescriptor()
        if self.__channels_by_write_fd.has_key(write_fd):
            raise ValueError, "duplicate write file descriptor"
        # Store the channel.
        self.__channels.append(channel)
        self.__channels_by_read_fd[read_fd] = channel
        self.__channels_by_write_fd[write_fd] = channel


    def RemoveChannel(self, channel):
        """Remove a channel from the manager.

        'channel' -- The channel to remove."""

        self.__channels.remove(channel)
        del self.__channels_by_read_fd[channel.GetReadFileDescriptor()]
        del self.__channels_by_write_fd[channel.GetWriteFileDescriptor()]


    def Wait(self, timeout=None):
        """Wait for a channel to become ready to read.

        This function blocks, servicing write-ready and read-ready
        events on all channels, until some data is read (or a channel
        closes)."""
        
        while 1:
            # We'll accept a read event from any channel.  Construct a
            # list of all channels' read file descriptors.
            read_fds = self.__channels_by_read_fd.keys()
            # We only care about write-ready events from channels with
            # data waiting to write.  Construct a list of write file
            # descriptors of such channels.
            write_channels = filter(lambda ch: ch._HasDataForWrite(),
                                    self.__channels)
            write_fds = map(lambda ch: ch.GetWriteFileDescriptor(),
                            write_channels)
            # To prevent a deadlock, raise an exception if no file
            # descriptors remain.
            if len(read_fds) == 0 and len(write_fds) == 0:
                raise NothingToWaitForError
            # Call 'select' with appropriate arguments.
            if timeout is None:
                select_results = select.select(read_fds, write_fds, [])
            else:
                select_results = select.select(read_fds, write_fds, [],
                                               timeout)
            read_ready_fds, write_ready_fds, ignored = select_results

            # For each channel that's ready to read, process the
            # incoming data.
            for fd in read_ready_fds:
                channel = self.__channels_by_read_fd[fd]
                try:
                    channel._OnReadReady()
                except ConnectionClosedException:
                    channel.Close()
                    self.RemoveChannel(channel)
                    write_fd = channel.GetWriteFileDescriptor()
                    if write_fd in write_ready_fds:
                        write_ready_fds.remove(write_fd)

            # For each channel that's ready to write, write out some
            # buffered data.
            for fd in write_ready_fds:
                channel = self.__channels_by_write_fd[fd]
                try:
                    channel._OnWriteReady()
                except ConnectionClosedException:
                    channel.Close()
                    self.RemoveChannel(channel)

            # Return if some data was read.
            if len(read_ready_fds) > 0:
                return


    def GetChannelCount(self):
        """Return the number of channels known to the manager."""
        
        return len(self.__channels)
        


########################################################################
# functions
########################################################################

def write_object(channel, object):
    """Write a Python object to a channel.

    The object is written to the file descriptor in binary pickle
    format, preceded by an integer count of the number of bytes in the
    pickle format.

    Use 'read_object' to read the object at the other end of the
    communications connection.

    'channel' -- The channel to write to.

    'object' -- A pickleable data object to write to the file."""

    # Pickle the object.
    data = cPickle.dumps(object, 1)
    # Encode the length of the pickle, and prepend it.
    data = struct.pack("!i", len(data)) + data
    # Write it all.
    channel.Write(data)


def read_object(channel):
    """Read a Python object from a channel.

    See 'write_object' for a description of the object's binary format.

    'channel' -- The channel to read from.

    returns -- The object read.

    raises -- 'ConnectionClosedException' if the file descriptor was
    closed."""

    # First read the length of the pickled object.
    encoded_length = channel.Read(4)
    # Unpack the length.
    length = struct.unpack("!i", encoded_length)[0]
    # Read the pickled object data.  
    data = channel.Read(length)
    # Decode and return the Python object.
    return cPickle.loads(data)


def fork_with_channel():
    """Fork, with bidirectional communications between parent and child.

    returns -- A pair '(child_pid, channel)'.  'child_pid' is zero when
    returning in the child process, or the child's process ID when
    returning in the parent process.  In either case, 'channel' is a
    'Channel' object for communicating with the other process."""

    # A pipe for writing from the parent to the child.
    parent_to_child_pipe = os.pipe()
    # A pipe for writing from the child to the parent.
    child_to_parent_pipe = os.pipe()

    # Fork a child process.
    child_pid = os.fork()

    if child_pid == 0:
        # This is the child process.  Close the file descriptors we
        # won't use here.
        os.close(parent_to_child_pipe[1])
        os.close(child_to_parent_pipe[0])
        # Construct the child's channel.
        channel = Channel(parent_to_child_pipe[0], child_to_parent_pipe[1])
        return (0, channel)

    else:
        # This is the parent process.  Close the file descriptors we
        # won't use here.
        os.close(parent_to_child_pipe[0])
        os.close(child_to_parent_pipe[1])
        # Construct the parent's channel.
        channel = Channel(child_to_parent_pipe[0], parent_to_child_pipe[1])
        return (child_pid, channel)
    

def fork_with_stdio_channel():
    """Fork, with a channel to the child's standard I/O streams.

    'fork_with_stdio_channel' is similar to 'fork_with_channel', except
    that the channel's read and write ends are attached to standard
    input and output, respectively, in the child process.

    returns -- A pair '(child_pid, channel)'.  'child_pid' is zero when
    returning in the child process, or the child's process ID when
    returning in the parent process.  In either case, 'channel' is a
    'Channel' object for communicating with the other process."""

    child_pid, channel = fork_with_channel()
    if child_pid == 0:
        os.dup2(channel.GetReadFileDescriptor(), sys.stdin.fileno())
        os.dup2(channel.GetWriteFileDescriptor(), sys.stdout.fileno())
    return child_pid, channel


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
