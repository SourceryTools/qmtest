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

from distutils.core import setup
import sys
import os
import os.path
import string
import glob

from qmdist.command.build_doc import build_doc
from qmdist.command.install_data import install_data

def prefix(list, pref): return map(lambda x, p=pref: p + x, list)

packages=['qm',
          'qm/external',
          'qm/external/DocumentTemplate',
          'qm/test',
          'qm/test/web']

classes= filter(lambda f: f[-3:] == '.py',
                os.listdir(os.path.join('qm','test','classes')))
classes.append('classes.qmc')

diagnostics=['common.txt','common-help.txt']

messages=['help.txt', 'diagnostics.txt']

html_docs = []
print_docs = []

if not os.path.isdir(os.path.normpath('qm/test/doc/html')):
    print """Warning: to include documentation into the package please run
         the \'build_doc\' command first."""

else:
    html_docs = filter(lambda f: f[-5:] == '.html',
                       os.listdir(os.path.normpath('qm/test/doc/html')))
    print_docs = ['manual.tex', 'manual.pdf']

setup(cmdclass={'build_doc': build_doc,
                #'build': qm_build,
                'install_data': install_data},
      name="qm", 
      version="2.1",
      packages=packages,
      scripts=['qm/test/qmtest.py'],
      data_files=[('share/qm/test/classes',
                   prefix(classes,'qm/test/classes/')),
                  ('share/qm/diagnostics',
                   prefix(diagnostics,'share/diagnostics/')),
                  ('share/qm/messages/test',
                   prefix(messages,'qm/test/share/messages/')),
                  ('share/qm/doc/html',
                   prefix(html_docs, 'qm/test/doc/html/')),
                  ('share/qm/doc/print',
                   prefix(print_docs, 'qm/test/doc/print/'))])

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
