########################################################################
#
# File:   qmtest-remote.py
# Author: Alex Samuel
# Date:   2001-08-11
#
# Contents:
#   QMTest remote test execution program.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
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
import sys

# The Python interpreter will place the directory containing this
# script in the default path to search for modules.  That is
# unncessary for QMTest, and harmful, since then "import resource"
# imports the resource module in QMTest, not the global module of
# the same name.
sys.path = sys.path[1:]

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
from   qm.test.base import *
import qm.test.run
import Queue
import sys

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

# Load RC options.
qm.rc.Load("test")

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
        database = qm.test.base.load_database(database_path)

        # Get the target class.
        target_class = get_extension_class("serial_target.SerialTarget",
                                           'target', database)
        # Build the target.
        target = target_class(None, None, int(concurrency), {},
                              database)

        # Start the target.
        response_queue = Queue.Queue(0)
        target.Start(response_queue)
        
        # Read commands from standard input, and reply to standard
        # output.
        while 1:
            # Read the command.
            command = cPickle.load(sys.stdin)
            
            # If the command is just a string, it should be
            # the 'Stop' command.
            if isinstance(command, types.StringType):
                assert command == "Stop"
                target.Stop()
                break

            # Decompose command.
            method, id, context = command
            # Get the descriptor.
            descriptor = database.GetTest(id)
            # Run it.
            target.RunTest(descriptor, context)
            # There are no results yet.
            results = []
            # Read all of the results.
            while 1:
                try:
                    result = response_queue.get(0)
                    results.append(result)
                except Queue.Empty:
                    # There are no more results.
                    break
            # Pass the results back.
            cPickle.dump(results, sys.stdout)
            # The standard output stream is bufferred, but the master
            # will block waiting for a response, so we must flush
            # the buffer here.
            sys.stdout.flush()
                
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
