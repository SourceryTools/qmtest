########################################################################
#
# File:   qmtest.in
# Author: Alex Samuel
# Date:   2001-03-15
#
# Contents:
#   QMTest command line application.
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

import qm
import qm.cmdline
import qm.platform
import qm.structured_text
import qm.test.cmdline
import sys

########################################################################
# functions
########################################################################

def print_error_message(message):
    message = qm.structured_text.to_text(str(message))
    sys.stderr.write("%s: error: %s" % (program_name, message))

########################################################################
# script
########################################################################

# Set the program name.
qm.common.program_name = "QMTest"

# Load QMTest diagnostics.
diagnostic_file = qm.get_share_directory("diagnostics", "test.txt")
qm.diagnostic.diagnostic_set.ReadFromFile(diagnostic_file)
# Load QMTest help messages.
help_file = qm.get_share_directory("diagnostics", "test-help.txt")
qm.diagnostic.help_set.ReadFromFile(help_file)

# Load RC options.
qm.rc.Load("test")
                                                       
program_name = os.path.basename(os.path.splitext(sys.argv[0])[0])

try:
    # Parse the command line.
    command = qm.test.cmdline.QMTest(program_name, sys.argv[1:])
    # Execute the command.
    command.Execute(sys.stdout)
    exit_code = 0

except RuntimeError, msg:
    print_error_message(msg)
    exit_code = 1

except qm.cmdline.CommandError, msg:
    print_error_message(str(msg)
                        + "\n\nInvoke %s --help for help with usage.\n"
                        % program_name)
    exit_code = 2

except KeyboardInterrupt:
    # User killed it; that's OK.
    sys.stderr.write("\nInterrupted.\n")
    exit_code = 0

# End the program.
sys.exit(exit_code)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
