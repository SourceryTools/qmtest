##############################################################################
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""Cached properties

See the CachedProperty class.

$Id: property.py 38680 2005-09-29 09:12:36Z jim $
"""
ncaches = 0l

class CachedProperty(object):
    """Cached Properties
    """

    def __init__(self, func, *names):
        global ncaches
        ncaches += 1
        self.data = (func, names,
                     "_v_cached_property_key_%s" % ncaches,
                     "_v_cached_property_value_%s" % ncaches)

    def __get__(self, inst, class_):
        if inst is None:
            return self

        func, names, key_name, value_name = self.data

        key = names and [getattr(inst, name) for name in names]
        value = getattr(inst, value_name, self)

        if value is not self:
            # We have a cached value
            if key == getattr(inst, key_name, self):
                # Cache is still good!
                return value
            
        # We need to compute and cache the value

        value = func(inst)
        setattr(inst, key_name, key)
        setattr(inst, value_name, value)
        
        return value


class Lazy(object):
    """Lazy Attributes
    """

    def __init__(self, func, name=None):
        if name is None:
            name = func.__name__
        self.data = (func, name)

    def __get__(self, inst, class_):
        if inst is None:
            return self

        func, name = self.data
        value = func(inst)
        inst.__dict__[name] = value
        
        return value

class readproperty(object):

    def __init__(self, func):
        self.func = func

    def __get__(self, inst, class_):
        if inst is None:
            return self

        func = self.func
        return func(inst)
    
