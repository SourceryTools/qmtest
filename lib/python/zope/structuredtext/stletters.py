##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
$Id: stletters.py 25177 2004-06-02 13:17:31Z jim $
"""

import string

def punc_func(exclude):
    punc = r''
    for char in string.punctuation:
        if char not in exclude:
            punc = punc + r'\%s' % char
    return punc

digits = string.digits
letters = string.letters
literal_punc = punc_func("'")
dbl_quoted_punc = punc_func("\"")
strongem_punc = punc_func('*')
under_punc = punc_func('_<>')
phrase_delimiters = r'\s\.\,\?\/\!\&\(\)'
