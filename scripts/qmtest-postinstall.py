# Post installation script for the Windows installer
# This script is needed to adjust variables in qm/config.py
# typically set during installation.

from os.path import join
import sys, re
from distutils import sysconfig

def reset_config_variables(config_file, **vars):
    """Reset specific variables in the given config file to new values.

    'config_file' -- The config file to modify.

    'vars' -- dict object containing variables to reset, with their new values.

    """

    script = open(config_file, 'r').read()
    for v in vars:
        script, found = re.subn('%s=.*'%v,'%s=%s'%(v, repr(vars[v])), script)
        if not found: script += '%s=%s'%(v, repr(vars[v]))
    open(config_file, 'w').write(script)


def install():
    print 'Adjusting configuration parameters...'
    site_packages = join(sysconfig.get_config_var('BINLIBDEST'), 'site-packages')
    config_file = join(site_packages, 'qm', 'config.py')
    prefix = sysconfig.get_config_var('prefix')
    version = sys.version_info[:2]
    extension_path = join('share', 'qmtest', 'site-extensions-%d.%d'%version)
    reset_config_variables(config_file,
                           prefix=prefix, extension_path=extension_path)
    print 'Done.'

def remove():
    pass


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == '-install':
        install()
    elif mode == '-remove':
        remove()
