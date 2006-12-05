########################################################################
#
# File:   qmtrack
# Author: Alex Samuel
# Date:   2001-02-17
#
# Contents:
#   QMTrack command line application
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

# Set up the Python module lookup path to find QMTrack.

import os
import os.path

if os.environ['QM_BUILD'] == '1':
    setup_path_dir = os.path.join(os.environ['QM_HOME'], 'qm')
else:
    setup_path_dir = os.path.join(os.environ['QM_HOME'], 'lib/qm/qm')
execfile(os.path.join(setup_path_dir, 'setup_path.py'))

try:

########################################################################
# imports
########################################################################

    import qm.common
    import qm.diagnostic
    import qm.track.cmdline
    import sys

########################################################################
# script
########################################################################

    # Set the program name.
    qm.common.program_name = "QMTrack"

    # Load messages.
    qm.diagnostic.load_messages("track")

    # Load RC options.
    qm.rc.Load("track")
                                                       
    # Run the command on the command line.
    exit_code = qm.track.cmdline.run_command(sys.argv)

except KeyboardInterrupt:
    sys.stderr.write("Interrupted.\n")
    exit_code = 1

qm.common.exit(exit_code)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
