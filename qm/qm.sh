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
# For license terms see the file COPYING.
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
# Variables
########################################################################

# Set by the makefile:
qm_rel_libdir=@@@RELLIBDIR@@@

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
#    that contain $0 until we find a directory containing
#    $qm_rel_libdir or file called `qm/qm.sh'.  (It is not sufficient
#    to simply apply 'dirname' twice because of pathological cases
#    like `./././bin/qmtest.sh'.)  This directory is the root of the
#    installation.  In the former case, we have found an installed QM;
#    in the latter we have found a build directory where QM is being
#    developed.
#
# After determining the root of the QM installation, set the QM_HOME
# environment variable to that value.  If we have found QM in the
# build directory, set the QM_BUILD environment variable to 1.  
# Otherwise, set it to 0.
#
# Set QM_PATH to the path to this script.

# Assume that QM is not running out of the build directory.
QM_BUILD=${QM_BUILD:-0}

# Check to see if QM_HOME is set.
if test x"${QM_HOME}" = x; then
    # Find the path to this script.  Set qm_path to the absolute
    # path to this script.
    if qm_is_absolute_path "$0"; then
	# If $0 is an absolute path, use it.
	QM_PATH="$0"
    elif qm_contains_dirsep "$0"; then
	# If $0 is something like `./qmtest', transform it into
	# an absolute path.
	QM_PATH="`pwd`/$0"
    else
	# Otherwise, search the PATH.
	for d in `qm_split_path "${PATH}"`; do
	    if test -f "${d}/$0"; then
		QM_PATH="${d}/$0"
		break
	    fi
	done

	# If we did not find this script, then we must give up.
	if test x"${QM_PATH}" = x; then
	    qm_could_not_find_qm
	fi

	# If the path we have found is a relative path, make it
	# an absolute path.
	if ! qm_is_absolute_path "${QM_PATH}"; then
	    QM_PATH="`pwd`/${QM_PATH}"
	fi
    fi

    # Iterate through the directories containing this script.
    QM_HOME=`dirname "${QM_PATH}"`
    while true; do
	# If there is a subdirectory called $qm_rel_libdir, then 
	# we have found the root of the QM installation.
	if test -d "${QM_HOME}/${qm_rel_libdir}"; then
	    break
	fi
	# Alternatively, if we have find a file called `qm/qm.sh',
	# then we have found the root of the QM build directory.
	if test -f "${QM_HOME}/qm/qm.sh"; then
	    QM_BUILD=1
	    break
	fi
	# If we have reached the root directory, then we have run
	# out of places to look.
	if test "x${QM_HOME}" = x/; then
	    qm_could_not_find_qm
	fi
	# Go the next containing directory.
	QM_HOME=`dirname "${QM_HOME}"`
    done
else
    # The QM_HOME variable was set.
    if test ${QM_BUILD} -eq 0; then
	QM_PATH=$QM_HOME/bin/qmtest
    else
	QM_PATH=$QM_HOME/qm/test/qmtest
    fi
fi

# Export QM_HOME and QM_PATH so that we can find them from within Python.
export QM_HOME
export QM_PATH
# Export QM_BUILD so that QM knows where to look for other modules.
export QM_BUILD

# When running QMTest from the build environment, run Python without
# optimization.  In a production environment, use optimization.
if test x"${QM_PYTHON_FLAGS}" = x; then
    if test ${QM_BUILD} -eq 1; then
        QM_PYTHON_FLAGS=""
    else
        QM_PYTHON_FLAGS="-O"
    fi
fi

# Decide which Python installation to use in the following way:
#
# 1. If ${QM_PYTHON} exists, use it.
#
# 2. Otherwise, If ${QM_HOME}/bin/python exists, use it.
#
# 3. Otherwise, if /usr/bin/python2 exists, use it.
#    
#    Red Hat's "python2" RPM installs Python in /usr/bin/python2, so
#    as not to conflict with the "python" RPM which installs 
#    Python 1.5 as /usr/bin/python.  QM requires Python 2, and we
#    do not want every user to have to set QM_PYTHON, so we must
#    look for /usr/bin/python2 specially.
#
# 4. Otherwise, use whatever "python" is in the path.
#
# Set qm_python to this value.

if test "x${QM_PYTHON}" != x; then
    qm_python="${QM_PYTHON}"
elif test -f "${QM_HOME}/bin/python"; then
    qm_python="${QM_HOME}/bin/python"
elif test -f "/usr/bin/python2"; then
    qm_python="/usr/bin/python2"
else
    qm_python="python"
fi

# Figure out where to find the main Python script.
if test ${QM_BUILD} -eq 0; then
    qm_libdir="${QM_HOME}/${qm_rel_libdir}"
else
    qm_libdir="${QM_HOME}/qm"
fi
qm_script=`basename $0`

# Just in case we installed into a weird place:
qm_python_path_dir=`expr "${qm_libdir}" : '\(.*\)/qm'`
PYTHONPATH=${qm_python_path_dir}:$PYTHONPATH
export PYTHONPATH

case ${qm_script} in
    qmtest) qm_script_dir=test;;
    qmtrack) qm_script_dir=track;;
esac

qm_script="${qm_libdir}/${qm_script_dir}/${qm_script}.py"

# Start the python interpreter, passing it all of the arguments
# present on our command line.  It would be nice to be able to
# issue an error message if that does not work, beyond that which
# the shell issues, but exec does not return on failure.
exec "${qm_python}" ${QM_PYTHON_FLAGS} "${qm_script}" "$@"
