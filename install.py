########################################################################
#
# File:   install.py
# Author: Alex Samuel
# Date:   2001-03-28
#
# Contents:
#   Installation script for QM tools.
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

########################################################################
# imports
########################################################################

import dircache
import os
import py_compile
import re
import shutil
import sys

execfile("qm/setup_path.py")

########################################################################
# configuration
########################################################################

# The template from which the setup path script is created.
setup_path_script_template_path = "qm/setup_path.py.in"

# Package directories containing Python files that need to be installed
# in the lib area.
packages = [
    "gadfly",
    "zope-dtml",
    "sgmlop",
    "xmlrpc",
    "PyXML/build/lib.%s-%s" % (__python_platform, __python_version),
    "qm"
    ]

# Scripts that must be copied to the bin directory.  The key
# is the name of the script that will be generated; the value is
# its location in the build directory.
scripts = {
    "qmtest": "qm/test/qmtest",
    "qmtest-remote": "qm/test/qmtest-remote",
    "qmtrack": "qm/track/qmtrack",
    }

# Documentation files to install.
doc_files = [
    "README",
    "COPYING",
    "doc/manual/print/manual.pdf",
    ]

# Directories containing DocBook-generated documentation.
doc_dirs = [
    "manual/html",
    ]

########################################################################
# functions
########################################################################

def copy_tree(src, dst, expand_symlinks=0):
    """Copy a directory tree, recursively.

    Unlike 'shutil.copytree', it's OK if 'dst' and subdirectories of it
    exist, as long as no files under 'dst' conflict with corresponding
    directories under 'src'.
    
    'src' -- The source directory to copy.

    'dst' -- The destination directory.

    'expand_symlinks' -- If true, the copy reads through symlinks and
    expands their targets.  If false, symlinks are copied as such.

    raises -- 'RuntimeError' if an existing file in or under 'dst'
    conflicts with a directory in 'src'.

    raises -- 'RuntimeError' if 'src' contains, directly or indirectly,
    an entry that is not a file, directory, or symbolic link."""
    
    # Create the 'dst' directory, if it doesn't exist.
    if not os.path.isdir(dst):
        if os.path.exists(dst):
            raise RuntimeError, \
                  "%s exists but is not a directory" % dst
        os.makedirs(dst)

    # Scan over directory contents.
    entries = dircache.listdir(src)
    for entry in entries:
        # Construct paths to corresponding source and destination.
        src_entry = os.path.join(src, entry)
        dst_entry = os.path.join(dst, entry)
        # Handle symlinks specially, if 'expand_symlinks' is not true.
        # Otherwise, treat that entry as the target to which the symlink
        # points. 
        if not expand_symlinks and os.path.islink(src_entry):
            # Create an equivalent symlink.
            target = os.readlink(src_entry)
            os.symlink(target, dst_entry)
        elif os.path.isfile(src_entry):
            # Copy a file.
            shutil.copy(src_entry, dst_entry)
        elif os.path.isdir(src_entry):
            # Copy a directory, recursively.
            copy_tree(src_entry, dst_entry)
        else:
            # We don't try to copy pipes, sockets, devices, etc.
            raise RuntimeError, "cannot copy %s" % src_entry


def install_package(src, dst):
    """Install a package from 'src' to 'dst'.

    'src' -- The package directory.

    'dst' -- The directory in which the contents of the package will be
    installed."""

    # Create the destination directory if it doesn't exist.
    if not os.path.exists(dst):
        os.makedirs(dst, 0755)
        os.chmod(dst, 0755)
    # Look at the contents of the package directory.
    for e in os.listdir(src):
        # Construct full paths for the file and its correspondence in
        # the destination directory.
        e_src = os.path.join(src, e)
        e_dst = os.path.join(dst, e)
        # Extract the file extension.
        extension = os.path.splitext(e)[1]

        if os.path.isdir(e_src):
            # It's a directory; call ourself recursively.
            install_package(e_src, e_dst)

        elif extension == ".py":
            # It's a Python source file.
            print "installing %s" % e_dst
            # Copy it to the destination.
            shutil.copy(e_src, e_dst)
            os.chmod(e_dst, 0644)
            # Compile it to bytecode.
            py_compile.compile(e_dst)

        elif extension == ".so":
            # It's a shared object, presumably part of a native Python
            # module. 
            print "installing %s" % e_dst
            # Copy it to the destination.
            shutil.copy(e_src, e_dst)
            os.chmod(e_dst, 0755)

        else:
            # Skip everything else.
            pass
            

def set_data_file_permissions(arg, dirname, names):
    """Set the permissions for data files.

    For use as a callback to 'os.path.walk'."""
    
    # The directory gets mode 755.
    os.chmod(dirname, 0755)
    for name in names:
        # Contents get mode 644.
        os.chmod(os.path.join(dirname, name), 0644)

    
########################################################################
# script
########################################################################

# Skip the first argument; that's the name of this script.
arguments = sys.argv[1:]
# There should be four arguments exactly.
if len(arguments) != 4:
    sys.stderr.write("Usage: python install.py "
                     "BINDIR LIBDIR SHAREDIR DOCDIR\n")
    sys.exit(1)
# Unpack them.
bin_dir, lib_dir, share_dir, doc_dir = arguments

# This is the first line that's added to generated scripts.
bin_handler = "#!%s\n" % sys.executable

# Install all packages.
for directory in packages:
    install_package(directory, os.path.join(lib_dir, directory))

# Create the bin directory if it doesn't exist.
if not os.path.exists(bin_dir):
    os.makedirs(bin_dir, 0755)
    os.chmod(bin_dir, 0755)
# Construct each of the scripts.
for script_name, build_location in scripts.items():
    # Construct the path to the binary script.
    script_path = os.path.join(bin_dir, script_name)
    print "generating %s" % script_path
    shutil.copy(build_location, script_path)
    os.chmod(script_path, 0755)

# Create the parent of the share directory.
share_parent_dir = os.path.dirname(share_dir)
if not os.path.exists(share_parent_dir):
    os.makedirs(share_parent_dir, 0755)
    os.chmod(share_parent_dir, 0755)
# Copy the share directory tree wholesale.
print "copying %s" % share_dir
copy_tree("share", share_dir)
# Set the permissions of the files in the tree.
os.path.walk(share_dir, set_data_file_permissions, None)

# Create the doc directory if it doesn't exit.
if not os.path.exists(doc_dir):
    os.makedirs(doc_dir, 0755)
    os.chmod(doc_dir, 0755)
# Copy documentation files there.
for doc_file in doc_files:
    dest = os.path.join(doc_dir, os.path.basename(doc_file))
    # Documentation may not have been built.  
    if os.path.isfile(doc_file):
        print "installing %s" % dest
        shutil.copy(doc_file, dest)
        os.chmod(dest, 0644)
    else:
        print "warning: missing documentation file %s" % doc_file
for dir in doc_dirs:
    # Documentation may not have been built.
    src = os.path.join("doc", dir)
    if os.path.isdir(src):
        dest = os.path.join(doc_dir, dir)
        dest_dir = os.path.dirname(dest)
        print "copying %s" % src
        copy_tree(src, dest)
    else:
        print "warning: missing documentation directory %s" % dir

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
