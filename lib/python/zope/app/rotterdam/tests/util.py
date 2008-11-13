##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Rotterdam utilities tests

$Id: util.py 30238 2005-05-04 13:24:21Z hdima $
"""
import os
import zope.app.rotterdam.tests

dir = os.path.dirname(zope.app.rotterdam.tests.__file__)
input_dir = os.path.join(dir, 'input')
output_dir = os.path.join(dir, 'output')

def read_input(filename):
    filename = os.path.join(input_dir, filename)
    return open(filename, 'r').read().decode("utf-8")

def read_output(filename):
    filename = os.path.join(output_dir, filename)
    return open(filename, 'r').read().decode("utf-8")
