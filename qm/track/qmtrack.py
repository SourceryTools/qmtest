########################################################################
#
# File:   qmtrack
# Author: Alex Samuel
# Date:   2001-02-17
#
# Contents:
#   QMTrack command line application
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

    # Load QMTrack diagnostics.
    diagnostic_file = \
        qm.common.get_share_directory("diagnostics", "track.txt")
    qm.diagnostic.diagnostic_set.ReadFromFile(diagnostic_file)
    # Load QMTrack help messages.
    help_file = \
        qm.common.get_share_directory("diagnostics", "track-help.txt")
    qm.diagnostic.help_set.ReadFromFile(help_file)

    # Load RC options.
    qm.rc.Load("track")
                                                       
    # Run the command on the command line.
    exit_code = qm.track.cmdline.run_command(sys.argv)

    # End the program.
    sys.exit(exit_code)

except KeyboardInterrupt:
    sys.stderr.write("Interrupted.\n")
    sys.exit(1)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
