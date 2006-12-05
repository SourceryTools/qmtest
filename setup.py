########################################################################
#
# File:   setup.py
# Author: Stefan Seefeld
# Date:   2003-08-25
#
# Contents:
#   Installation script for the qmtest package
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from   distutils.core import setup, Extension
import sys
import os
import os.path
from   os.path import join
import string
import glob
from   qmdist.command.build import build
from   qmdist.command.build_doc import build_doc
from   qmdist.command.install_data import install_data
from   qmdist.command.install_lib import install_lib
from   qmdist.command.install_scripts import install_scripts
from   qmdist.command.check import check
from   qm.__version import version
import shutil

########################################################################
# Functions
########################################################################

def prefix(list, pref):

    return map(lambda x, p=pref: join(p, x), list)


def files_with_ext(dir, ext):
    """Return all files in 'dir' with a particular extension.

    'dir' -- The name of a directory.

    'ext' -- The extension.

    returns -- A sequence consisting of the filenames in 'dir' whose
    extension is 'ext'."""

    return prefix(filter(lambda f: f.endswith(ext),
                         os.listdir(dir)),
                  dir)


def select_share_files(share_files, dir, files):
    """Find installable files in 'dir'.

    'share_files' -- A dictionary mapping directories to lists of file
    names.

    'dir' -- The directory in which the 'files' are located.

    'files' -- A list of the files contained in 'dir'."""
    
    exts = (".txt", ".dtml", ".css", ".js", ".gif", ".dtd", ".mod")
    files = filter(lambda f: \
                     f == "CATALOG" or (os.path.splitext(f)[1] in exts),
                   files)
    if files:
        files = prefix(files, dir)
        dir = join("qm", dir[len("share/"):])
        share_files[dir] = files

diagnostics=['common.txt','common-help.txt']

messages=['help.txt', 'diagnostics.txt']

tutorial_files = files_with_ext("qm/test/share/tutorial/tdb", ".qmt")
test_dtml_files = files_with_ext("qm/test/share/dtml", ".dtml")

share_files = {}
os.path.walk("share", select_share_files, share_files)

# On UNIX, users invoke "qmtest".  On Windows, there is no way to make a
# Python script directly executable, unless its suffix is ".py".  It is
# difficult to get distutils to install just one script or the other, so
# we install both on all platforms.
qmtest_script = join("qm", "test", "qmtest")
qmtest_py_script = qmtest_script + ".py"
shutil.copyfile(qmtest_script, qmtest_py_script)
     
# We need the sigmask extension on POSIX systems, but don't want it on
# Win32.
if sys.platform != "win32":
    ext_modules = [Extension("qm.sigmask", ["qm/sigmask.c"])]
else:
    ext_modules = []

setup(name="qm", 
      version=version,
      author="CodeSourcery, LLC",
      author_email="info@codesourcery.com",
      maintainer="Mark Mitchell",
      maintainer_email="mark@codesourcery.com",
      url="http://www.codesourcery.com/qm/test",
      description="QMTest is an automated software test execution tool.",
      
      cmdclass={'build': build,
                'build_doc': build_doc,
                'install_data': install_data,
                'install_lib': install_lib,
                'install_scripts' : install_scripts,
                'check': check},

      packages=('qm',
                'qm/external',
                'qm/external/DocumentTemplate',
                'qm/test',
                'qm/test/classes',
                'qm/test/web'),
      ext_modules=ext_modules,
      scripts=[qmtest_script, qmtest_py_script],
      data_files=[('qm/messages/test',
                   prefix(messages, 'qm/test/share/messages')),
                  # DTML files for the GUI.
                  ("qm/dtml/test", test_dtml_files),
                  # The documentation.
                  ('qm/doc', ('README', 'COPYING')),
                  ('qm/doc/test/html', ['qm/test/doc/html/*.html',
                                        'qm/test/doc/html/qm.css']),
                  ('qm/doc/test/print', ["qm/test/doc/print/*.pdf"]),
                  # The tutorial.
                  ("qm/tutorial/test/tdb", tutorial_files),
                  ("qm/tutorial/test/tdb/QMTest",
                   ("qm/test/share/tutorial/tdb/QMTest/configuration",))]
                 # The files from the top-level "share" directory.
                 + share_files.items())

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
