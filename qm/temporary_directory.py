########################################################################
#
# File:   temporary_directory.py
# Author: Mark Mitchell
# Date:   05/07/2003
#
# Contents:
#   TemporaryDirectory
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import dircache
import os
import qm
import sys
import tempfile

########################################################################
# Classes
########################################################################

class TemporaryDirectory:
    """A 'TemporaryDirectory' is a directory for temporary files.

    Creating a new 'TemporaryDirectory results in the creation of a
    new directory in the file system.  The directory is automatically
    removed from the file system when the 'TemporaryDirectory' is
    destroyed."""

    def __init__(self):
        """Construct a new 'TemporaryDirectory."""

        self.__directory = None
        
        dir_path = tempfile.mktemp()
        try:
            os.mkdir(dir_path, 0700)
        except:
            exc_info = sys.exc_info()
            raise qm.common.QMException, \
                  qm.error("temp dir error",
                           dir_path=dir_path,
                           exc_class=str(exc_info[0]),
                           exc_arg=str(exc_info[1]))

        self.__directory = dir_path
    

    def GetPath(self):
        """Returns the path to the temporary directory.

        returns -- The path to the temporary directory."""

        return self.__directory
    
        
    def __del__(self):

        self.Remove()

        
    def Remove(self):
        """Remove the temporary directory.

        Removes the temporary directory, and all files and directories
        contained within it, from the file system."""
        
        if self.__directory is not None:
            self.__RemoveDirectory(self.__directory)
        self.__directory = None


    def __RemoveDirectory(self, path):
        """Remove the directory 'path'.

        Removes 'path', after first removing all of its contents."""
        
        # Remove everything in the directory.
        for entry in dircache.listdir(path):
            entry_path = os.path.join(path, entry)
            if os.path.isdir(entry_path):
                self.__RemoveDirectory(entry_path)
            else:
                os.unlink(entry_path)
        # Remove the directory itself.
        os.rmdir(path)
            
        
