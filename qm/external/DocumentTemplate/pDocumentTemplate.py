##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
__doc__='''Python implementations of document template some features


$Id$'''
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
