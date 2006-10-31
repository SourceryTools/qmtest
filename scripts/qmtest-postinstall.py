# Post installation script for the Windows installer
# This script is needed to adjust variables in qm/config.py
# typically set during installation.

import os, os.path, sys, re
from distutils import sysconfig

def install():
    print 'Adjusting configuration parameters...'
    site_packages = os.path.join(sysconfig.get_config_var('BINLIBDEST'),
                                 'site-packages')
    config_file = os.path.join(site_packages, 'qm', 'config.py')
    script = open(config_file, 'r').read()
    prefix = sysconfig.get_config_var('prefix')
    # Adjust 'prefix' variable.
    script = re.sub('prefix=.*', "prefix='%s'"%prefix.replace('\\','\\\\'),
                    script)
    extension_dir = os.path.join('share', 'qmtest',
                                 'site-extensions-%d.%d'%sys.version_info[:2])
    # Adjust 'extension_dir' variable.
    script = re.sub('extension_path=.*',
                    "extension_path='%s'"%extension_dir.replace('\\','\\\\'),
                    script)
    # Write the script back out.
    open(config_file, 'w').write(script)
    print 'Done.'

def remove():
    pass


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == '-install':
        install()
    elif mode == '-remove':
        remove()
