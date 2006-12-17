##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Static tree utilities

$Id: utils.py 26551 2004-07-15 07:06:37Z srichter $
"""
import zlib

from zope.interface import implements
from zope.app.tree.interfaces import ITreeStateEncoder

class TreeStateEncoder(object):
    """Encodes tree state

    >>> expanded_nodes = ['a', 'c', 'foobar']
    >>> encoder = TreeStateEncoder()
    >>> encoded = encoder.encodeTreeState(expanded_nodes)
    >>> decoded = encoder.decodeTreeState(encoded)
    >>> decoded == expanded_nodes
    True
    """
    implements(ITreeStateEncoder)

    # note that this implementation relies on the node ids not
    # containing colons
    def encodeTreeState(self, expanded_nodes):
        tree_state = ":".join(expanded_nodes)
        tree_state = zlib.compress(tree_state)
        return b2a(tree_state)

    def decodeTreeState(self, tree_state):
        tree_state = a2b(tree_state)
        tree_state = zlib.decompress(tree_state)
        return tree_state.split(":")

#
# The following code has been taken unchanged from Zope2's
# ZTUtils.Tree module
#

from binascii import b2a_base64, a2b_base64
from string import translate, maketrans

a2u_map = maketrans('+/=', '-._')
u2a_map = maketrans('-._', '+/=')

def b2a(s):
    '''Encode a value as a cookie- and url-safe string.

    Encoded string use only alphanumeric characters, and "._-".
    '''
    s = str(s)
    if len(s) <= 57:
        return translate(b2a_base64(s)[:-1], a2u_map)
    frags = []
    for i in range(0, len(s), 57):
        frags.append(b2a_base64(s[i:i + 57])[:-1])
    return translate(''.join(frags), a2u_map)

def a2b(s):
    '''Decode a b2a-encoded string.'''
    s = translate(s, u2a_map)
    if len(s) <= 76:
        return a2b_base64(s)
    frags = []
    for i in range(0, len(s), 76):
        frags.append(a2b_base64(s[i:i + 76]))
    return ''.join(frags)

