from distutils.core import setup

setup(name="qm", 
      version="1.0",
      packages= ['qm', 'qm.test', 'qm.test.web', 'qm.test.classes' ],
      package_dir = { 'qm' : '.' })
