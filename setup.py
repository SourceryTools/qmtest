########################################################################
#
# File:   setup.py
# Author: Stefan Seefeld
# Date:   2003-08-25
#
# Contents:
#   Installation script for the qmtest package
#
# Copyright (c) 2003 by CodeSourcery.  All rights reserved. 
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
from   qmdist.command.build_scripts import build_scripts
from   qmdist.command.build_doc import build_doc
from   qmdist.command.install_data import install_data
from   qmdist.command.install_lib import install_lib
from   qmdist.command.bdist_wininst import bdist_wininst
from   qmdist.command.check import check
from   qm.__version import version
import shutil

########################################################################
# Functions
########################################################################

def files_with_ext(dir, ext):
    """Return all files in 'dir' with a particular extension.

    'dir' -- The name of a directory.

    'ext' -- The extension.

    returns -- A sequence consisting of the filenames in 'dir' whose
    extension is 'ext'."""

    return [join(dir, file) for file in os.listdir(dir) if file.endswith(ext)]


def select_share_files(share_files, dir, files):
    """Find installable files in 'dir'.

    'share_files' -- A dictionary mapping directories to lists of file
    names.

    'dir' -- The directory in which the 'files' are located.

    'files' -- A list of the files contained in 'dir'."""
    
    exts = (".txt", ".dtml", ".css", ".js", ".gif", ".dtd", ".mod", ".xslt")
    files = [join(dir, f)
             for f in files
             if f == "CATALOG" or os.path.splitext(f)[1] in exts]
    if files:
        dir = join("share", "qm", dir[len("share/"):])
        share_files[dir] = files

diagnostics=['common.txt','common-help.txt']

messages=['help.txt', 'diagnostics.txt']

tutorial_files = files_with_ext("qm/test/share/tutorial/tdb", ".qmt")
test_dtml_files = files_with_ext("qm/test/share/dtml", ".dtml")
report_dtml_files = files_with_ext("qm/test/share/dtml/report", ".dtml")

share_files = {}
os.path.walk("share", select_share_files, share_files)

if sys.platform != "win32":
    # We need the sigmask extension on POSIX systems, but don't
    # want it on Win32.
    ext_modules = [Extension("qm.sigmask", ["qm/sigmask.c"])]
    scripts = ['scripts/qmtest']
else:
    ext_modules = []
    shutil.copyfile('scripts/qmtest', 'scripts/qmtest.py')
    scripts = ['scripts/qmtest.py', 'scripts/qmtest-postinstall.py']

setup(name="qmtest", 
      version=version,
      author="CodeSourcery",
      author_email="info@codesourcery.com",
      maintainer="CodeSourcery",
      maintainer_email="qmtest@codesourcery.com",
      url="http://www.codesourcery.com/qmtest",
      description="QMTest is an automated software test execution tool.",
      
      cmdclass={'build': build,
                'build_scripts': build_scripts,
                'build_doc': build_doc,
                'install_data': install_data,
                'install_lib': install_lib,
                'bdist_wininst' : bdist_wininst,
                'check': check},

      packages=('qm',
                'qm/dist',
                'qm/dist/command',
                'qm/external',
                'qm/external/DocumentTemplate',
                'qm/test',
                'qm/test/classes',
                'qm/test/web'),
      ext_modules=ext_modules,
      scripts=scripts,
      data_files=[('share/qm/messages/test',
                   [join('qm/test/share/messages', m) for m in messages]),
                  # DTML files for the GUI.
                  ("share/qm/dtml/test", test_dtml_files),
                  ("share/qm/dtml/report", report_dtml_files),
                  # The documentation.
                  ('share/doc/qm', ('README', 'COPYING')),
                  ('share/doc/qm/test/html/tutorial',
                   ['share/doc/qmtest/html/tutorial/*.html',
                    'share/doc/qmtest/html/tutorial/cs.css']),
                  ('share/doc/qm/test/print',
                   ['share/doc/qmtest/print/*.pdf']),
                  # The tutorial.
                  ("share/qm/tutorial/test/tdb", tutorial_files),
                  ("share/qm/tutorial/test/tdb/QMTest",
                   ("qm/test/share/tutorial/tdb/QMTest/configuration",))]
                 # The files from the top-level "share" directory.
                 + share_files.items())

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
