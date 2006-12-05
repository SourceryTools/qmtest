########################################################################
#
# File:   rsh_target.py
# Author: Mark Mitchell
# Date:   10/30/2001
#
# Contents:
#   QMTest RSHTarget class.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import cPickle
import os
from   qm.test.command_thread import *
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

        'write_file' -- The file object to which commands should be
        written.  This file will be closed when the thread exits.

        'read_file' -- The file object from which results should be
        read.  This file will be closed when the thread exits."""

	CommandThread.__init__(self, target)

        self.__write_file = write_file
        self.__read_file = read_file
        

    def _RunTest(self, descriptor, context):
        """Run the test given by 'descriptor'.

        'descriptor' -- The 'TestDescriptor' for the test to be run.

        'context' -- The 'Context' in which to run the test."""

        test_id = descriptor.GetId()
        command_object = ("RunTest", test_id, context)
        try:
            cPickle.dump(command_object, self.__write_file)
            results = cPickle.load(self.__read_file)
            for result in results:
                self.GetTarget()._RecordResult(result)
        except:
            result = Result(Result.TEST, test_id, context)
            result.NoteException()
            self.GetTarget()._RecordResult(result)


    def _Stop(self):
        """Stop the thread.

        This method is called in the thread after 'Stop' is called
        from the controlling thread.  Derived classes can use this
        method to release resources before the thread is destroyed."""
        
        try:
            cPickle.dump("Stop", self.__write_file)
        except:
            # If, for example, the pipe we are writing to has been
            # closed by the child process we will be unable to issue
            # the stop command.  By handling the exception, however,
            # we can avoid crashing QMTest.
            pass
        self.__write_file.close()
        self.__read_file.close()

        
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
      before the name of the remote host."""

    def __init__(self, name, group, concurrency, properties, database):
        """Construct a new 'RSHTarget'.

        'name' -- A string giving a name for this target.

        'group' -- A string giving a name for the target group
        containing this target.

        'concurrency' -- The amount of parallelism desired.  If 1, the
        target will execute only a single command at once.

        'properties'  -- A dictionary mapping strings (property names)
        to strings (property values).
        
        'database' -- The 'Database' containing the tests that will be
        run."""

        # Initialize the base class.
        Target.__init__(self, name, group, concurrency, properties,
                        database)

        # Create a lock to guard all accesses to __idle.
        self.__lock = Lock()
        # Note that the target is presently idle.
        self.__idle = 1

        # Determine the host name.
        self.__host_name = self.GetProperty("host", None)
        if self.__host_name is None:
            # None specified; use the target name.
            self.__host_name = self.GetName()

                        
    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the target is idle.  If the target is idle,
        additional tasks may be assigned to it."""
        
        self.__lock.acquire()
        idle = self.__idle
        self.__lock.release()

        return idle


    def Start(self, response_queue, engine=None):
        """Start the target.
        
        'response_queue' -- The 'Queue' in which the results of test
        executions are placed.

        'engine' -- The 'ExecutionEngine' that is starting the target,
        or 'None' if this target is being started without an
        'ExecutionEngine'."""

        Target.Start(self, response_queue, engine)

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
                "database_path", default=self.GetDatabase().GetPath())
            # Determine the path to the remote 'qmtest-remote' command.
            qmtest_remote_path = self.GetProperty(
                "qmtest_remote", "/usr/local/bin/qmtest")
            # Construct the command we want to invoke remotely.  The
            # 'qmtest-remote' script processes commands from standard
            # I/O. 
            remote_arg_list = [
                qmtest_remote_path, '-D', database_path, "remote"
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

            # Close the read end of the command pipe.
            os.close(command_pipe[0])
            # And the write end of the response pipe.
            os.close(response_pipe[1])

            # Start the thread that will process responses from
            # the child.
            self.__thread = \
               RSHThread(self,
                         os.fdopen(command_pipe[1], "w", 0),
                         os.fdopen(response_pipe[0], "r"))
            self.__thread.start()


    def Stop(self):
        """Stop the target.

        postconditions -- The target may no longer be used."""

        # Stop the thread.
        self.__thread.Stop()
        self.__thread.join()
        # Wait for the remote shell process to terminate.
        os.waitpid(self.__child_pid, 0)


    def RunTest(self, descriptor, context):
        """Run the test given by 'test_id'.

        'descriptor' -- The 'TestDescriptor' for the test.

        'context' -- The 'Context' in which to run the test."""

        self.__thread.RunTest(descriptor, context)


    def _RecordResult(self, result):
        """Record the 'result'.

        'result' -- A 'Result' of a test or resource execution."""

        # If this is a test result, then this thread has finished all
        # of its work.
        if result.GetKind() == Result.TEST:
            self.__lock.acquire()
            self.__idle = 1
            self.__lock.release()
        # Pass the result back to the execution engine.
        Target._RecordResult(self, result)
