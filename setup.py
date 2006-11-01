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
from   qmdist.command.build import build
from   qmdist.command.build_scripts import build_scripts
from   qmdist.command.build_doc import build_doc
from   qmdist.command.install_data import install_data
from   qmdist.command.install_lib import install_lib
from   qmdist.command.bdist_wininst import bdist_wininst
from   qmdist.command.check import check
from   qm.__version import version
import sys, os, os.path, glob, shutil

if sys.platform != "win32":
    # We need the sigmask extension on POSIX systems, but don't
    # want it on Win32.
    ext_modules = [Extension("qm.sigmask", ["qm/sigmask.c"])]
    scripts = ['scripts/qmtest']
else:
    ext_modules = []
    shutil.copyfile('scripts/qmtest', 'scripts/qmtest.py')
    scripts = ['scripts/qmtest.py', 'scripts/qmtest-postinstall.py']

def include(d, e):
    """Generate a pair of (directory, file-list) for installation.

    'd' -- A directory

    'e' -- A glob pattern"""
    
    return (d, [f for f in glob.glob('%s/%s'%(d, e)) if os.path.isfile(f)])

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
      data_files=[include('share/qmtest/messages', '*.txt'),
                  include('share/qmtest/diagnostics', '*.txt'),
                  # DTML files for the GUI.
                  include('share/qmtest/dtml', '*.dtml'),
                  include('share/qmtest/dtml/test/dtml', '*.dtml'),
                  include('share/qmtest/dtml/report/dtml', '*.dtml'),
                  # The documentation.
                  ('share/doc/qmtest', ('README', 'COPYING')),
                  include('share/doc/qmtest/html/tutorial', '*'),
                  include('share/doc/qmtest/print', 'tutorial.pdf'),
                  include('share/qmtest/tutorial/tdb', '*'),
                  include('share/qmtest/tutorial/tdb/QMTest', 'configuration'),
                  # The GUI.
                  include('share/qmtest/dtml', '*.dtml'),
                  include('share/qmtest/dtml/test', '*.dtml'),
                  include('share/qmtest/dtml/report', '*.dtml'),
                  include('share/qmtest/web', '*.js'),
                  include('share/qmtest/web/images', '*.gif'),
                  include('share/qmtest/web/stylesheets', '*.css'),

                  include('share/qmtest/xml', '*'),
                  include('share/qmtest/dtds',  '*.dtd')
                  ],
      )

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
