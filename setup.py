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
from   qmdist.command.build_py import build_py
from   qmdist.command.build_scripts import build_scripts
from   qmdist.command.build_doc import *
from   qmdist.command.install_lib import install_lib
from   qmdist.command.bdist_wininst import bdist_wininst
from   qmdist.command.check import check
import sys, os, os.path, glob, shutil

version='2.4'

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
                'build_py': build_py,
                'build_scripts': build_scripts,
                'build_doc': build_doc,
                'build_html_tutorial': build_html_tutorial,
                'build_pdf_tutorial': build_pdf_tutorial,
                'build_ref_manual': build_ref_manual,
                'build_man_page': build_man_page,
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
                  # The documentation.
                  ('share/doc/qmtest', ('ChangeLog', 'README', 'NEWS', 'COPYING', 'LICENSE.OPL')),
                  include('share/man/man1', '*'),
                  include('share/doc/qmtest/html/tutorial', '*'),
                  include('share/doc/qmtest/print', 'tutorial.pdf'),
                  include('share/doc/qmtest/examples/xml_tdb', '*'),
                  include('share/doc/qmtest/examples/xml_tdb/QMTest', 'configuration'),
                  include('share/doc/qmtest/examples/compilation_tdb', '*'),
                  include('share/doc/qmtest/examples/compilation_tdb/subdir', '*'),
                  include('share/doc/qmtest/examples/compilation_tdb/QMTest', 'configuration'),
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
