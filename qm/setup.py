########################################################################
#
# File:   setup.py
# Author: Mark Mitchell
# Date:   01/02/2002
#
# Contents:
#   QM Distutils setup script.
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   distutils.core import setup
import os
import os.path
import string

########################################################################
# Functions
########################################################################

def find_packages_r(packages, dirname, names):
    """If 'dirname' is a QM package, add it to 'packages'.

    'packages' -- A mutable sequence of package names.

    'dirname' -- The (relative) path from the base of the QM package
    to the directory.

    'names' -- A mutable sequence of file names indicating files (and
    directories) contained in the directory given by 'dirname'."""

    # If the directory contains a file called __init__.py, it is a
    # package.  Directories named "classes" contain extension classes.
    if "__init__.py" in names or os.path.basename(dirname) == "classes":
        # Replace a leading "." with "qm".
        d = "qm" + dirname[1:]
        # Replace path separators with periods.
        d = string.replace(d, os.sep, ".")
        if os.altsep:
            d = string.replace(dirname, os.altsep, ".")
        packages.append(d)
    # Exclude directories named "build"; they are created by Distutils.
    if "build" in names:
        names.remove("build")

########################################################################
# Main Program
########################################################################

# Find all of the packages that make up QM.
packages = []
os.path.walk(".", find_packages_r, packages)

setup(name="qm", 
      version="1.1",
      packages=packages,
      package_dir={ 'qm' : '.' })
