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

import qm.async
import qm.common
import qm.cmdline
import qm.platform
import qm.structured_text
import qm.test.base
import qm.test.run
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
program_name = sys.argv[0]

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

        # Construct a channel for communicating via the standard I/O
        # streams. 
        channel = qm.async.Channel(sys.stdin.fileno(), sys.stdout.fileno())

        # Construct a proxy target specification for the target we'll
        # use to execute the tests locally.  Since this target is just a
        # proxy for commands sent to a remote-execution target on the
        # scheduling node, most of the target parameters are irrelevant.
        # The target's main responsibility is to divide commands among
        # subprocesses, and multiplex their replies.
        target_spec = qm.test.run.TargetSpec(
            name=None,
            class_name="qm.test.run._RemoteDemultiplexerTarget",
            group=None,
            concurrency=concurrency,
            properties={})
        # Instantiate the proxy target.
        target = qm.test.run._RemoteDemultiplexerTarget(target_spec, channel)
        # Run the proxy target's relay loop.  This relays commands and
        # replies until the quit command is received.
        try:
            target.RelayCommands()
        except:
            sys.stderr.write("FOO\n")
            target.Stop()
            raise
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
