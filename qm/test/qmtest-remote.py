########################################################################
#
# File:   qmtest-remote.in
# Author: Alex Samuel
# Date:   2001-08-11
#
# Contents:
#   QMTest remote test execution program.
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

# Usage:
#
#     qmtest-remote DB-PATH CONCURRENCY
#
# Arguments:
#
#     DB-PATH is the path to the test database.
#
#     CONCURRENCY is the degree of concurrency for running tests and
#     resource functions.  This argument must be a positive integer.
#
# This script reads commands for executing tests and resource functions
# from standard input, executes them (in concurrent subprocesses), and
# writes replies (including test results) to standard output.  The
# format for commands and replies are according to the protocol used by
# 'qm.test.run.process_commands'.
#
# See 'qm.test.run.RemoteShellTarget' and
# 'qm.test.run._RemoteDemultiplexerTarget' for information about how
# this script is used internally by QMTest to implement remote test
# execution.

# Set up the Python module lookup path to find QM.

import os
import os.path

if os.environ['QM_BUILD'] == '1':
    setup_path_dir = os.path.join(os.environ['QM_HOME'], 'qm')
else:
    setup_path_dir = os.path.join(os.environ['QM_HOME'], 'lib/qm/qm')
execfile(os.path.join(setup_path_dir, 'setup_path.py'))

########################################################################
# imports
########################################################################

import cPickle
import qm.common
import qm.cmdline
import qm.platform
import qm.structured_text
import qm.test.base
import qm.test.run
import Queue
import sys
from   threading import *

########################################################################
# functions
########################################################################

def print_error_message(message):
    message = qm.structured_text.to_text(str(message))
    sys.stderr.write("%s: error:\n%s" % (program_name, message))
    
########################################################################
# script
########################################################################

# Set the program name.
qm.common.program_name = "QMTest"
program_name = os.path.splitext(sys.argv[0])[0]

# Load QMTest diagnostics.
diagnostic_file = qm.get_share_directory("diagnostics", "test.txt")
qm.diagnostic.diagnostic_set.ReadFromFile(diagnostic_file)

try:
    # This script must be run with exactly two command-line arguments.
    if len(sys.argv) != 3:
        # Wrong number of arguments.  Complain.
        sys.stderr.write("Usage: %s DB-PATH CONCURRENCY\n" % program_name)
        exit_code = 2
    else:
        # Parse the arguments.
        database_path = sys.argv[1]
        concurrency = sys.argv[2]
        # Load the test database,
        qm.test.base.load_database(database_path)

        # Create the queue that the local threads will use to write
        # replies.
        response_queue = Queue.Queue(0)
        
        # Construct a proxy target specification for the target we'll
        # use to execute the tests locally.  Since this target is just a
        # proxy for commands sent to a remote-execution target on the
        # scheduling node, most of the target parameters are irrelevant.
        # The target's main responsibility is to divide commands among
        # subprocesses, and multiplex their replies.
        target_spec = qm.test.run.TargetSpec(
            name=None,
            class_name="qm.test.run.SubprocessTarget",
            group=None,
            concurrency=concurrency,
            properties={})
        # Instantiate the proxy target.
        target = qm.test.run.SubprocessTarget(target_spec, response_queue)

        # Read commands from standard input, and reply to standard
        # output.
        while 1:
            # The number of replies that we expect.
            expected_replies = 0
            
            # Fill up the target's queue.
            while target.GetQueueLength() < 0:
                # Read a command.
                command_type, id, context = cPickle.load(sys.stdin)
                # Provide it to the target.
                target.EnqueueCommand(command_type, id, context)
                # If we got the quit command, exit.
                if command_type == "quit":
                    break
                # We expect a reply to every command except "quit".
                expected_replies = expected_replies + 1
                
            # Ask the target to process the queue.
            target.ProcessQueue()

            while expected_replies > 0:
                # Read the result.
                target, response = response_queue.get()
                # Allow the local target to process the response.
                target.OnReply(response, None)
                # Pass the result back.
                cPickle.dump(response[0], sys.stdout)
                # We've gotten one reply.
                expected_replies = expected_replies - 1

            # The standard output stream is bufferred, but the master
            # will block waiting for a response, so we must flush
            # the buffer here.
            sys.stdout.flush()
            
            if command_type == "quit":
                break;
                
        # All is well.
        exit_code = 0

except RuntimeError, msg:
    print_error_message(msg)
    exit_code = 1

# End the program.
sys.exit(exit_code)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
