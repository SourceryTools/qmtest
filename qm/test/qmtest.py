########################################################################
#
# File:   qmtest.py
# Author: Alex Samuel
# Date:   2001-03-15
#
# Contents:
#   QMTest command line application.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

# Set up the Python module lookup path to find QM.

import errno
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
import qm.diagnostic
import qm.platform
import qm.structured_text
import qm.test.cmdline
import traceback

########################################################################
# functions
########################################################################

def print_error_message(message):
    prefix = "%s: error: " % program_name
    message = qm.structured_text.to_text(str(message),
                                         indent=len(prefix))
    message = prefix + message[len(prefix):]
    sys.stderr.write(message)

########################################################################
# script
########################################################################

# Set the program name.
qm.common.program_name = "QMTest"

# Load messages.
qm.diagnostic.load_messages("test")

# Load RC options.
qm.rc.Load("test")
                                                       
program_name = os.path.basename(os.path.splitext(sys.argv[0])[0])

try:
    # Parse the command line.
    command = qm.test.cmdline.QMTest(program_name, sys.argv[1:],
                                     major_version, minor_version,
                                     release_version)
    # Execute the command.
    command.Execute(sys.stdout)
    exit_code = 0
except qm.cmdline.CommandError, msg:
    print_error_message(msg)
    sys.stderr.write(
        "Run '%s --help' to get instructions about how to use QMTest.\n"
        % program_name)
    exit_code = 2
except qm.common.QMException, msg:
    print_error_message(msg)
    exit_code = 1
except NotImplementedError:
    exc_info = sys.exc_info()
    method_name = traceback.extract_tb(exc_info[2])[-1][2]
    print_error_message(qm.message("not implemented",
                                   method_name = method_name))
    sys.stderr.write(qm.common.format_traceback(exc_info))
    exit_code = 1
except KeyboardInterrupt:
    # User killed it; that's OK.
    sys.stderr.write("\nqmtest: Interrupted.\n")
    exit_code = 0
    
# End the program.
qm.exit(exit_code)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
