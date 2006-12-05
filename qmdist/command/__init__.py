########################################################################
#
# File:   __init__.py
# Author: Mark Mitchell
# Date:   2003-10-14
#
# Contents:
#   Support functions for installation scripts.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import os.path

########################################################################
# Functions
########################################################################

def get_relative_path(dir1, dir2):
    """Return the relative path from 'dir1' to 'dir2'.

    'dir1' -- The path to a directory.

    'dir2' -- The path to a directory.
    
    returns -- The relative path from 'dir1' to 'dir2'."""

    dir1 = os.path.abspath(dir1)
    dir2 = os.path.abspath(dir2)
    rel_path = ""
    while not dir2.startswith(dir1):
        rel_path = os.path.join(os.pardir, rel_path)
        dir1 = os.path.dirname(dir1)
        if dir1 == os.sep:
            dir1 = ""
            break
    return os.path.join(rel_path, dir2[len(dir1) + 1:])
