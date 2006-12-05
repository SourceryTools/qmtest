########################################################################
#
# File:   install_extensions.py
# Author: Stefan Seefeld
# Date:   2005-11-16
#
# Contents:
#   Command to install qmtest extensions.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.xmlutil
from distutils.command.install_lib import install_lib
import os, dircache, xml

########################################################################
# Classes
########################################################################

def _compare_files(a, b):
    """Compare the content of two files.

    'a' -- Filename of first file to be compared.

    'b' -- Filename of second file to be compared.

    returns -- True if both files have the same content, False otherwise."""

    file_a, file_b = open(a, 'r'), open(b, 'r')
    for line in file_a:
        if line != file_b.readline():
            return False
    if file_b.readline():
        return False
    return True


class install_extensions(install_lib):
    """Install extension files."""

    description = "install qmtest extension classes."


    def finalize_options(self):

        if not self.install_dir:
            i = self.distribution.get_command_obj('install')
            i.ensure_finalized()
            prefix = i.root or i.prefix
            self.install_dir = os.path.join(prefix, qm.extension_path)
        install_lib.finalize_options(self)

        b = self.distribution.get_command_obj('build_extensions')
        b.ensure_finalized()
        self.build_dir = b.build_dir


    def run(self):

        # Make sure we have built everything we need first
        self.run_command('build_extensions')

        if not os.path.isdir(self.install_dir):
            self.mkpath(self.install_dir)
        if not os.path.exists(os.path.join(self.install_dir, 'classes.qmc')):
            # This is the first time extensions are installed there.
            self.copy_tree(self.build_dir, self.install_dir)
        else:
            # Test that to-be-copied modules don't overwrite existing ones:
            old_files = [f for f in dircache.listdir(self.install_dir)
                         if f.endswith('.py')]
            new_files = [f for f in dircache.listdir(self.build_dir)
                         if f.endswith('.py') and f != '__init__.py']
            overlap = []
            for f in new_files:
                if f in old_files:
                    # Don't complain if both files are identical.
                    if not _compare_files(os.path.join(self.build_dir, f),
                                          os.path.join(self.install_dir, f)):
                        overlap.append(f)
            if overlap:
                print "Error: The following extension files already exist:"
                for o in overlap:
                    print "       %s"%o
                return
            # Copy all modules to the install directory.
            for f in new_files:
                self.copy_file(os.path.join(self.build_dir, f),
                               os.path.join(self.install_dir, f),
                               preserve_mode=0)
            
            # Carefully merge the new extensions into an existing repository.
            old_qmc = qm.xmlutil.load_xml_file(os.path.join(self.install_dir,
                                                            'classes.qmc'))
            old_root = old_qmc.documentElement

            new_qmc = qm.xmlutil.load_xml_file(os.path.join(self.build_dir,
                                                            'classes.qmc'))
            new_root = new_qmc.documentElement

            for ext in new_root.getElementsByTagName("class"):
                # If this entry already exists in the repository, skip it.
                name = ext.getAttribute("name")
                entries = [c for c in old_root.childNodes
                           if c.nodeType == xml.dom.Node.ELEMENT_NODE and
                           c.tagName == "class" and
                           c.getAttribute("name") == name]
                if not entries:
                    old_root.appendChild(ext)
                    old_root.appendChild(old_qmc.createTextNode('\n'))
            # Write new repository file.
            old_qmc.writexml(open(os.path.join(self.install_dir,
                                               'tmp-classes.qmc'), 'w'))
            # If that worked, update the original one.
            os.rename(os.path.join(self.install_dir, 'tmp-classes.qmc'),
                      os.path.join(self.install_dir, 'classes.qmc'))
