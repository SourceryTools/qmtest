########################################################################
#
# File:   test.py
# Author: Alex Samuel
# Date:   2000-12-23
#
# Contents:
#   Tests for module qm.
#
# Copyright (c) 2000 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

########################################################################
# imports
########################################################################

import qm
import qm.regression_test

########################################################################
# tests
########################################################################

def test_is_valid_label():
    return qm.is_valid_label("abcde") \
           and qm.is_valid_label("ab_xz_efg_0912_bjd__f_") \
           and qm.is_valid_label("_foo_bar", user=0) \
           and not qm.is_valid_label("_foo_bar") \
           and not qm.is_valid_label("") \
           and not qm.is_valid_label("Hello") \
           and not qm.is_valid_label("hello world")


def test_thunk_to_label():
    return qm.is_valid_label(qm.thunk_to_label("")) \
           and qm.is_valid_label(qm.thunk_to_label("abcyz_12390_")) \
           and qm.is_valid_label(qm.thunk_to_label("   abc 123   ")) \
           and qm.is_valid_label(qm.thunk_to_label("hello world!")) \
           and qm.is_valid_label(qm.thunk_to_label("(*@KAJD)92809  kj!")) \
           and qm.is_valid_label(qm.thunk_to_label("____foo bar____")) \
           and qm.is_valid_label(qm.thunk_to_label("This is a test."))


regression_tests = [
    test_is_valid_label,
    test_thunk_to_label,
    ]


if __name__ == "__main__":
    qm.regression_test.run_regression_test_driver(regression_tests)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
