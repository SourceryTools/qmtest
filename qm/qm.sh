#! /bin/sh 

########################################################################
#
# File:   qm.sh
# Author: Mark Mitchell
# Date:   10/04/2001
#
# Contents:
#   QM script.
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

########################################################################
# Notes
########################################################################

# This script must be extremely portable.  It should run on all UNIX
# platforms without modification.
# 
# The following commands are used by this script and are assumed
# to be in the PATH:
#
#   basename
#   dirname
#   expr
#   pwd
#   sed
#   test
#   true

########################################################################
# Functions
########################################################################

# Prints an error message indicating that the QM installation could
# not be found and exits with a non-zero exit code.

qm_could_not_find_qm() {
cat >&2 <<EOF
error: Could not find the QM installation.

       Set the QM_HOME environment variable to the directory 
       in which you installed QM.
EOF

    exit 1
}

# Returns true if $1 is an absolute path.

qm_is_absolute_path() {
    expr "$1" : '/.*$' > /dev/null 2>&1
}

# Returns true if $1 contains at least one directory separator.

qm_contains_dirsep() {
    expr "$1" : '.*/' > /dev/null 2>&1
}

# Prints out the components that make up the colon-separated path
# given by $1.

qm_split_path() {
    echo $1 | sed -e 's|:| |g'
}

########################################################################
# Main Program
########################################################################

# Find the root of the QM installation in the following way:
#
# 1. If the QM_HOME environment variable is set, its value is
#    used unconditionally.
#
# 2. Otherwise, determine the path to this script.  If $0 is
#    an absolute path, that value is used.  Otherwise, search
#    the PATH environment variable just as the shell would do.
#
#    Having located this script, iterate up through the directories
#    that contain $0 until we find a directory containing `lib/qm' or
#    file called `qm/qm.sh'.  (It is not sufficient to simply apply
#    'dirname' twice because of pathological cases like
#    `./././bin/qmtest.sh'.)  This directory is the root of the
#    installation.  In the former case, we have found an installed
#    QM; in the latter we have found a build directory where QM
#    is being developed.
#
# After determining the root of the QM installation, set the QM_HOME
# environment variable to that value.  If we have found QM in the
# build directory, set the QM_BUILD environment variable to 1.  
# Otherwise, set it to 0.

# Assume that QM is not running out of the build directory.
QM_BUILD=0

# Check to see if QM_HOME is set.
if test x"${QM_HOME}" = x; then
    # Find the path to this script.  Set qm_path to the absolute
    # path to this script.
    if qm_is_absolute_path "$0"; then
	# If $0 is an absolute path, use it.
	qm_path="$0"
    elif qm_contains_dirsep "$0"; then
	# If $0 is something like `./qmtest', transform it into
	# an absolute path.
	qm_path="`pwd`/$0"
    else
	# Otherwise, search the PATH.
	for d in `qm_split_path "${PATH}"`; do
	    if test -f "${d}/$0"; then
		qm_path="${d}/$0"
		break
	    fi
	done

	# If we did not find this script, then we must give up.
	if test x"${qm_path}" = x; then
	    qm_could_not_find_qm
	fi

	# If the path we have found is a relative path, make it
	# an absolute path.
	if ! qm_is_absolute_path "${qm_path}"; then
	    qm_path="`pwd`/${qm_path}"
	fi
    fi

    # Iterate through the directories containing this script.
    while true; do
	# Go the next containing directory.  We do this at the
	# beginning of the loop because $qm_path is the path
	# to the script, not a directory containing it, on the
	# first iteration.
	qm_path=`dirname ${qm_path}`
	# If there is a subdirectory called `lib/qm', then 
	# we have found the root of the QM installation.
	if test -d "${qm_path}/lib/qm"; then
	    QM_HOME="${qm_path}"
	    break
	fi
	# Alternatively, if we have find a file called `qm/qm.sh',
	# then we have found the root of the QM build directory.
	if test -f "${qm_path}/qm/qm.sh"; then
	    QM_HOME="${qm_path}"
	    QM_BUILD=1
	    break
	fi
	# If we have reached the root directory, then we have run
	# out of places to look.
	if test "x${qm_path}" = x/; then
	    qm_could_not_find_qm
	fi
    done
fi

# Export QM_HOME so that we can find it from within Python.
export QM_HOME
# Export QM_BUILD so that QM knows where to look for other modules.
export QM_BUILD

# Decide which Python installation to use in the following way:
#
# 1. If ${QM_PYTHON} exists, use it.
#
# 2. Otherwise, If ${QM_HOME}/bin/python exists, use it.
#
# 3. Otherwise, use whatever `python' is in the path.
#
# Set qm_python to this value.

if test "x${QM_PYTHON}" != x; then
    qm_python="${QM_PYTHON}"
elif test -f "${QM_HOME}/bin/python"; then
    qm_python="${QM_HOME}/bin/python"
else
    qm_python="python"
fi

# Figure out where to find the main Python script.
if test ${QM_BUILD} -eq 0; then
    qm_libdir="${QM_HOME}/lib/qm/qm"
else
    qm_libdir="${QM_HOME}/qm"
fi
qm_script=`basename $0`

case ${qm_script} in
    qmtest | qmtest-remote) qm_script_dir=test;;
    qmtrack) qm_script_dir=track;;
esac

qm_script="${qm_libdir}/${qm_script_dir}/${qm_script}.py"

# Start the python interpreter, passing it all of the arguments
# present on our command line.
exec "${qm_python}" -O "${qm_script}" "$@"
