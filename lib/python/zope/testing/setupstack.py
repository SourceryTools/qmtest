##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Stack-based test doctest setUp and tearDown

See setupstack.txt
"""

import os, shutil, tempfile

key = '__' + __name__

def register(test, function, *args, **kw):
    stack = test.globs.get(key)
    if stack is None:
        stack = test.globs[key] = []
    stack.append((function, args, kw))

def tearDown(test):
    stack = test.globs.get(key)
    while stack:
        f, p, k = stack.pop()
        f(*p, **k)

def setUpDirectory(test):
    tmp = tempfile.mkdtemp()
    register(test, shutil.rmtree, tmp)
    here = os.getcwd()
    register(test, os.chdir, here)
    os.chdir(tmp)

    
