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
from distutils.command import build
from distutils.command import install_data
from distutils.spawn import find_executable
import os
import os.path
import string
import glob

def prefix(list, pref): return map(lambda x, p=pref: p + x, list)

class qm_install_data(install_data.install_data):
    """This class overrides the system install_data command. In addition
    to the original processing, a 'config' module is created that
    contains the data only available at installation time, such as
    installation paths."""

    def run(self):
        id = self.distribution.get_command_obj('install_data')
        il = self.distribution.get_command_obj('install_lib')
        install_data.install_data.run(self)
        config = os.path.join(il.install_dir, 'qm/config.py')
        self.announce("generating %s" %(config))
        outf = open(config, "w")
        outf.write("#the old way...\n")
        outf.write("import os\n")
        outf.write("os.environ['QM_HOME']='%s'\n"%(id.install_dir))
        outf.write("os.environ['QM_BUILD']='0'\n")
        outf.write("#the new way...\n")
        outf.write("version='%s'\n"%(self.distribution.get_version()))
        
        outf.write("class config:\n")
        outf.write("  data_dir='%s'\n"%(os.path.join(id.install_dir,
                                                     'share',
                                                     'qm')))
        outf.write("\n")

packages=['qm',
          'qm/external',
          'qm/external/DocumentTemplate',
          'qm/test',
          'qm/test/web']

classes= filter(lambda f: f[-3:] == '.py', os.listdir('qm/test/classes/'))
classes.append('classes.qmc')

diagnostics=['common.txt','common-help.txt']

messages=['help.txt', 'diagnostics.txt']

setup(cmdclass={'install_data': qm_install_data},
      name="qm", 
      version="2.1",
      packages=packages,
      scripts=['qm/test/qmtest.py'],
      data_files=[('share/qm/test/classes',
                   prefix(classes,'qm/test/classes/')),
                  ('share/qm/diagnostics',
                   prefix(diagnostics,'share/diagnostics/')),
                  ('share/qm/messages/test',
                   prefix(messages,'qm/test/share/messages/'))])

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
