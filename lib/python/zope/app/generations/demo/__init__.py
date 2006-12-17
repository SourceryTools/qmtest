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
"""Demo package for evolution scripts

The evolution scripts in this package are pretty dumb. The just call
the evolve function defined here with a generation number. 

$Id: __init__.py 26816 2004-07-28 19:09:51Z pruggera $
"""
__docformat__ = 'restructuredtext'

key = 'zope.app.generations.demo-generation'

def evolve(context, generation):
    """Demo that "evolves" a database.

    All it does is write the generation to a database root item.
    """
    root = context.connection.root()
    root[key] = root.get(key, ()) + (generation, )
