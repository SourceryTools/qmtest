##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import os, re, shutil, sys, tempfile, unittest, warnings
from zope.testing import doctest, renormalizing
import zope.deferredimport

class OutErr:

    @staticmethod
    def write(message):
        sys.stdout.write(message)

def warn(message, type_, stacklevel):
    frame = sys._getframe(stacklevel)
    path = frame.f_globals['__file__']
    file = open(path)
    lineno = frame.f_lineno
    for i in range(lineno):
        line = file.readline()

    print "%s:%s: %s: %s\n  %s" % (
        path,
        frame.f_lineno,
        type_.__name__,
        message,
        line.strip(),
        )

def setUp(test):
    d = test.globs['tmp_d'] = tempfile.mkdtemp('deferredimport')

    def create_module(**modules):
        for name, src in modules.iteritems():
            f = open(os.path.join(d, name+'.py'), 'w')
            f.write(src)
            f.close()
            test.globs['created_modules'].append(name)

    test.globs['created_modules'] = []
    test.globs['create_module'] = create_module

    zope.deferredimport.__path__.append(d)

    test.globs['oldstderr'] = sys.stderr
    sys.stderr = OutErr

    test.globs['saved_warn'] = warnings.warn
    warnings.warn = warn

def tearDown(test):
    sys.stderr = test.globs['oldstderr']

    zope.deferredimport.__path__.pop()
    shutil.rmtree(test.globs['tmp_d'])
    for name in test.globs['created_modules']:
        sys.modules.pop(name, None)
    warnings.warn = test.globs['saved_warn']

def test_suite():
    checker = renormalizing.RENormalizing((
        (re.compile(r'.+[/\\]README.txt'), 'README.txt'),
        ))
    return doctest.DocFileSuite(
        'README.txt',
        setUp=setUp, tearDown=tearDown,
        optionflags=doctest.NORMALIZE_WHITESPACE,
        checker=checker,
        )

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

