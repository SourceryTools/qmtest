########################################################################
#
# File:   process_target.py
# Author: Mark Mitchell
# Date:   07/24/2002
#
# Contents:
#   ProcessTarget
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import cPickle
import os
from   qm.test.target import *

########################################################################
# Classes
########################################################################

class ProcessTarget(Target):
    """A 'ProcessTarget' runs tests in child processes."""

    arguments = [
        qm.fields.TextField(
            name="processes",
            title="Number of Processes",
            description="""The number of processes to devote to running tests.

            A positive integer that indicates the number of processes to
            use when running tests.  Larger numbers will allow more
            tests to be run at once.  You can experiment with this
            value to find the number that results in the fastest
            execution.""",
            default_value="1"),
        qm.fields.TextField(
            name="database_path",
            title="Database Path",
            description="""The path to the test database.

            A string giving the directory containing the test
            database.  If this value is the empty string, QMTest uses
            the path provided on the command line.""",
            default_value=""),
        qm.fields.TextField(
            name="qmtest",
            title="QMTest Path",
            description="""The path to the QMTest executable.

            A string giving the file name of the 'qmtest' executable
            program.  This path is used to invoke QMTest.""",
            default_value="/usr/local/bin/qmtest"),
        ]
    
    def __init__(self, database, properties):
        """Construct a new 'ProcessTarget'.

        'database' -- The 'Database' containing the tests that will be
        run.
    
        'properties'  -- A dictionary mapping strings (property names)
        to strings (property values)."""
        
        # Initialize the base class.
        Target.__init__(self, database, properties)

        # There are no children yet.
        self.__children = []
        self.__idle_children = []
        self.__busy_children = []
        self.__children_by_fd = {}
        
        
    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the target is idle.  If the target is idle,
        additional tasks may be assigned to it."""

        return self.__idle_children


    def Start(self, response_queue, engine=None):
        """Start the target.
        
        'response_queue' -- The 'Queue' in which the results of test
        executions are placed.

        'engine' -- The 'ExecutionEngine' that is starting the target,
        or 'None' if this target is being started without an
        'ExecutionEngine'."""

        Target.Start(self, response_queue, engine)

        for x in xrange(int(self.processes)):
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
                # output for the child.
                os.dup2(command_pipe[0], sys.stdin.fileno())
                os.dup2(response_pipe[1], sys.stdout.fileno())
                
                # Determine the test database path to use.
                database_path = self.database_path
                if not database_path:
                    database_path = self.GetDatabase().GetPath()
                # Determine the path to QMTest.
                qmtest_path = self.qmtest
                # Construct the command we want to invoke.
                arg_list = (self._GetInterpreter() +
                            [ qmtest_path, '-D', database_path, "remote" ])
                # Run it.
                qm.platform.replace_program(arg_list[0], arg_list)
                # Should be unreachable.
                assert 0
                
            else:
                # This is the parent process.
                self.__command_queue = []
                
                # Close the read end of the command pipe.
                os.close(command_pipe[0])
                # And the write end of the response pipe.
                os.close(response_pipe[1])
                
                # Remember the child.
                child = (child_pid,
                         os.fdopen(response_pipe[0], "r"),
                         os.fdopen(command_pipe[1], "w", 0))
                self.__children.append(child)
                self.__idle_children.append(child)
                self.__children_by_fd[response_pipe[0]] = child
                engine.AddInputHandler(response_pipe[0], self.__ReadResults)


    def Stop(self):
        """Stop the target.

        postconditions -- The target may no longer be used."""

        # Stop the children.
        for child in self.__children:
            try:
                cPickle.dump("Stop", child[2])
                child[2].close()
            except:
                pass
        # Read any remaining results.
        while self.__busy_children:
            self.__ReadResults(self.__busy_children[0][1].fileno())
        # Wait for the children to terminate.
        for child in self.__children:
            os.waitpid(child[0], 0)


    def RunTest(self, descriptor, context):
        """Run the test given by 'test_id'.

        'descriptor' -- The 'TestDescriptor' for the test.

        'context' -- The 'Context' in which to run the test."""

        # Use the child process at the head of the list.
        child = self.__idle_children.pop(0)
        self.__busy_children.append(child)
        # Write the test to the file.
        cPickle.dump(("RunTest", descriptor.GetId(), context),
                     child[2])


    def _GetInterpreter(self):
        """Return the interpreter to use.

        returns -- A list giving the path to an interpreter, and
        arguments to provide the interpreter.  This interpreter is
        used to run QMTest.  If '[]' is returned, then no intepreter
        is used."""

        return []
        

    def __ReadResults(self, fd):
        """Read results from one of the children.

        'fd' -- The descriptor from which the results should be read."""
        
        child = self.__children_by_fd[fd]
        try:
            results = cPickle.load(child[1])
            idle = None
            for result in results:
                self._RecordResult(result)
                if not idle and result.GetKind() == Result.TEST:
                    self.__idle_children.append(child)
                    self.__busy_children.remove(child)
                    idle = 1
        except EOFError:
            self.__idle_children.append(child)
            self.__busy_children.remove(child)
