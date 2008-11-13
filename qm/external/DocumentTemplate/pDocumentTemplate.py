##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Python implementations of document template some features


$Id$"""
__version__='$Revision$'[11:-2]

import string, sys, types
from string import join

StringType=type('')
TupleType=type(())
isFunctionType={}
for name in ['BuiltinFunctionType', 'BuiltinMethodType', 'ClassType',
             'FunctionType', 'LambdaType', 'MethodType', 'UnboundMethodType']:
    try: isFunctionType[getattr(types,name)]=1
    except: pass

try: # Add function and method types from Extension Classes
    import ExtensionClass
    isFunctionType[ExtensionClass.PythonMethodType]=1
    isFunctionType[ExtensionClass.ExtensionMethodType]=1
except: pass

isFunctionType=isFunctionType.has_key

isSimpleType={}
for n in dir(types):
    if (n[-4:]=='Type' and n != 'InstanceType' and
        not isFunctionType(getattr(types, n))):
        isSimpleType[getattr(types, n)]=1

isSimpleType=isSimpleType.has_key

class InstanceDict:

    validate=None

    def __init__(self,o,namespace,validate=None):
        self.self=o
        self.cache={}
        self.namespace=namespace
        if validate is None: self.validate=namespace.validate
        else: self.validate=validate

    def has_key(self,key):
        return hasattr(self.self,key)

    def keys(self):
        return self.self.__dict__.keys()

    def __repr__(self): return 'InstanceDict(%s)' % str(self.self)

    def __getitem__(self,key):

        cache=self.cache
        if cache.has_key(key): return cache[key]
        
        inst=self.self

        if key[:1]=='_':
            if key != '__str__':
                raise KeyError, key # Don't divuldge private data
            r=str(inst)
        else:
            try: r=getattr(inst,key)
            except AttributeError: raise KeyError, key

        v=self.validate
        if v is not None: v(inst,inst,key,r,self.namespace)

        self.cache[key]=r
        return r

class MultiMapping:

    def __init__(self): self.dicts=[]

    def __getitem__(self, key):
        for d in self.dicts:
            try: return d[key]
            except KeyError, AttributeError: pass
        raise KeyError, key

    def push(self,d): self.dicts.insert(0,d)

    def pop(self, n=1):
        r = self.dicts[-1]
        del self.dicts[:n]
        return r

    def keys(self):
        kz = []
        for d in self.dicts:
            kz = kz + d.keys()
        return kz

class DictInstance:
    
    def __init__(self, mapping):
        self.__d=mapping

    def __getattr__(self, name):
        try: return self.__d[name]
        except KeyError: raise AttributeError, name
        
class TemplateDict:

    level=0

    def _pop(self, n=1): return self.dicts.pop(n)
    def _push(self, d): return self.dicts.push(d)

    def __init__(self):
        m=self.dicts=MultiMapping()
        self._pop=m.pop
        self._push=m.push
        try: self.keys=m.keys
        except: pass

    def __getitem__(self,key,call=1,
                    simple=isSimpleType,
                    isFunctionType=isFunctionType,
                    ):

        v = self.dicts[key]
        if call:
            if hasattr(v, '__render_with_namespace__'):
                return v.__render_with_namespace__(self)
            vbase = getattr(v, 'aq_base', v)
            if callable(vbase):
                if getattr(vbase, 'isDocTemp', None):
                    return v(None, self)
                return v()
        return v

    def has_key(self,key):
        try:
            v=self.dicts[key]
        except KeyError:
            return 0
        return 1
    
    getitem=__getitem__

    def __call__(self, *args, **kw):
        if args:
            if len(args)==1 and not kw:
                m=args[0]
            else:
                m=self.__class__()
                for a in args: m._push(a)
                if kw: m._push(kw)
        else: m=kw
        return (DictInstance(m),)

def render_blocks(blocks, md):
    rendered = []
    append=rendered.append
    for section in blocks:
        if type(section) is TupleType:
            l=len(section)
            if l==1:
                # Simple var
                section=section[0]
                if type(section) is StringType: section=md[section]
                else: section=section(md)
                section=str(section)
            else:
                # if
                cache={}
                md._push(cache)
                try:
                    i=0
                    m=l-1
                    while i < m:
                        cond=section[i]
                        if type(cond) is StringType:
                            n=cond
                            try:
                                cond=md[cond]
                                cache[n]=cond
                            except KeyError, v:
                                v=str(v)
                                if n != v: raise KeyError, v, sys.exc_traceback
                                cond=None
                        else: cond=cond(md)
                        if cond:
                            section=section[i+1]
                            if section: section=render_blocks(section,md)
                            else: section=''
                            m=0
                            break
                        i=i+2
                    if m:
                        if i==m: section=render_blocks(section[i],md)
                        else: section=''

                finally: md._pop()

        elif type(section) is not StringType:
            section=section(md)

        if section: rendered.append(section)

    l=len(rendered)
    if l==0: return ''
    elif l==1: return rendered[0]
    return join(rendered, '')
    return rendered
