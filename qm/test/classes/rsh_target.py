########################################################################
#
# File:   rsh_target.py
# Author: Mark Mitchell
# Date:   10/30/2001
#
# Contents:
#   QMTest RSHTarget class.
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
from   qm.test.target import *
import string

########################################################################
# classes
########################################################################

class RSHThread(CommandThread):
    """A 'RSHThread' executes commands remotely."""

    def __init__(self, target, write_file, read_file):
	"""Construct a new 'RSHThread'.

	'target' -- The 'Target' that owns this thread.

	'response_queue' -- The queue on which to write responses.

        'write_file' -- The file object to which commands should be
        written.  This file will be closed when the thread exits.

        'read_file' -- The file object from which results should be
        read.  This file will be closed when the thread exits."""

	CommandThread.__init__(self, target)

        self.__write_file = write_file
        self.__read_file = read_file
        

    def _RunTest(self, test_id, context):
        """Run the test given by 'test_id'.

        'test_id' -- The name of the test to be run.

        'context' -- The 'Context' in which to run the test."""

        command_object = ("RunTest", test_id, context)
        cPickle.dump(command_object, self.__write_file)
        result = cPickle.load(self.__read_file)
        self.RecordResult(result)
        

    def _SetUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource."""

        command_object = ("SetUpResource", resource_id, context)
        cPickle.dump(command_object, self.__write_file)
        result = cPickle.load(self.__read_file)
        self.RecordResult(result)


    def _CleanUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource."""

        command_object = ("CleanUpResource", resource_id, context)
        cPickle.dump(command_object, self.__write_file)
        result = cPickle.load(self.__read_file)
        self.RecordResult(result)


    def _Stop(self):
        """Stop the thread.

        This method is called in the thread after 'Stop' is called
        from the controlling thread.  Derived classes can use this
        method to release resources before the thread is destroyed."""
        
        cPickle.dump("Stop", self.__write_file)
        self.__write_file.close()
        self.__read_file.close()

        
    def RecordResult(self, result):
        """Record the 'result'.

        'result' -- A 'Result' of a test or resource execution."""

        # Pass the result back to the target.
        self.GetTarget().RecordResult(result)
        # Tell the target that we have nothing to do.
        self.GetTarget().NoteIdle()



class RSHTarget(Target):
    """A target that runs tests via a remote shell invocation.

    A 'RSHTarget' runs tests on a remote computer via a remote shell
    call.  The remote shell is in the style of 'rsh' and 'ssh'.  Using
    the remote shell, the target invokes the 'qmtest-remote' script,
    which services commands sent via 'stdin', and replies via
    'stdout'.

    This target recognizes the following properties:

      'remote_shell' -- The path to the remote shell executable to use.
      If omitted, the configuration variable 'remote_shell' is used
      instead.  If both are not specified, the default is
      '/usr/bin/ssh'.  The remote shell program must accept the
      command-line syntax 'remote_shell *remote_host* *remote_command*'.

      'host' -- The remote host name.  If omitted, the target name is
      used.

      'database_path' -- The path to the test database on the remote
      computer.  The test database must be identical to the local test
      database.  If omitted, the local test database path is used.

      'qmtest_remote' -- The path to the 'qmtest_remote' command on the
      remote computer.  The default is '/usr/local/bin/qmtest_remote'.

      'arguments' -- Additional command-line arguments to pass to the
      remote shell program.  The value of this property is split at
      space characters, and the arguments are added to the command line
      before the name of the remote host.

    """

    def __init__(self, target_spec, database, response_queue):
        """Construct a new 'RSHTarget'.

        'target_spec' -- The specification for the target.

        'database' -- The 'Database' containing the tests that will be
        run."""

        # Initialize the base class.
        Target.__init__(self, target_spec, database, response_queue)

        # Create a lock to guard all accesses to __idle.
        self.__lock = Lock()
        # Note that the target is presently idle.
        self.__idle = 1

        # Determine the host name.
        self.__host_name = self.GetProperty("host", None)
        if self.__host_name is None:
            # None specified; use the target name.
            self.__host_name = self.GetName()

        # Create two pipes: one to write commands to the remote
        # QMTest, and one to read responses.
        command_pipe = os.pipe()
        response_pipe = os.pipe()
        
        # Create the child process.
        child_pid = os.fork()
        
        if child_pid == 0:
            # This is the child process.

            # Close the write end of the command pipe.
            os.close(command_pipe[1])
            # And the read end of the response pipe.
            os.close(response_pipe[0])
            # Connect the pipes to the standard input and standard
            # output for thie child.
            os.dup2(command_pipe[0], sys.stdin.fileno())
            os.dup2(response_pipe[1], sys.stdout.fileno())
            
            # Determine the test database path to use.
            database_path = self.GetProperty(
                "database_path", default=database.GetPath())
            # Determine the path to the remote 'qmtest-remote' command.
            qmtest_remote_path = self.GetProperty(
                "qmtest_remote", "/usr/local/bin/qmtest-remote")
            # Construct the command we want to invoke remotely.  The
            # 'qmtest-remote' script processes commands from standard
            # I/O. 
            remote_arg_list = [
                '"%s"' % qmtest_remote_path,
                '"%s"' % database_path,
                str(self.GetConcurrency()),
                ]
            # Determine the remote shell program to use.
            remote_shell_program = self.GetProperty("remote_shell", None)
            if remote_shell_program is None:
                remote_shell_program = qm.rc.Get("remote_shell",
                                                 default="/usr/bin/ssh",
                                                 section="common")
            # Extra command-line arguments to the remote shell program
            # may be specified with the "arguments" property. 
            extra_arguments = self.GetProperty("arguments", None)
            if extra_arguments is None:
                # None specified.
                extra_arguments = []
            else:
                # Split them at spaces.
                extra_arguments = string.split(extra_arguments, " ")
            # Construct the remote shell command.
            arg_list = [
                remote_shell_program,
                ] \
                + extra_arguments \
                + [
                self.__host_name,
                string.join(remote_arg_list, " ")
                ]
            
            # Run the remote shell.
            qm.platform.replace_program(arg_list[0], arg_list)
            # Should be unreachable.
            assert 0

        else:
            # This is the parent process.  Remember the child.
            self.__command_queue = []
            self.__child_pid = child_pid
            self.__ready_threads = self.GetConcurrency()

            # Start the thread that will process responses from
            # the child.
            self.__thread = \
               RSHThread(self,
                         os.fdopen(command_pipe[1], "w", 0),
                         os.fdopen(response_pipe[0], "r"))
            self.__thread.start()
            
            
    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the target is idle.  If the target is idle,
        additional tasks may be assigned to it."""
        
        self.__lock.acquire()
        idle = self.__idle
        self.__lock.release()

        return idle


    def Stop(self):
        """Stop the target.

        postconditions -- The target may no longer be used."""
        
        self.__thread.Stop()
        # Wait for the remote shell process to terminate.
        os.waitpid(self.__child_pid, 0)


    def NoteIdle(self):
        """Called when the RemoteThread becomes idle."""

        self.__lock.acquire()
        self.__idle = 1
        self.__lock.release()
        
        
    def RunTest(self, test_id, context):
        """Run the test given by 'test_id'.

        'test_id' -- The name of the test to be run.

        'context' -- The 'Context' in which to run the test."""

        self.__thread.RunTest(test_id, context)


    def SetUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource."""

        self.__thread.SetUpResource(resource_id, context)


    def CleanUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource.

        Derived classes must override this method."""

        self.__thread.CleanUpResource(resource_id, context)
