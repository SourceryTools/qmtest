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
"""IResult adapters for files.

$Id: fileresult.py 74219 2007-04-17 21:45:57Z gary $
"""

import tempfile
from zope import component, interface
import zope.publisher.interfaces.http
import zope.publisher.http
from zope.publisher.interfaces.http import IResult
from zope.security.proxy import removeSecurityProxy

class FallbackWrapper:
    interface.implements(IResult)

    def __init__(self, f):
        self.close = f.close
        self._file = f

    def __iter__(self):
        f = self._file
        while 1:
            v = f.read(32768)
            if v:
                yield v
            else:
                break

@component.adapter(file, zope.publisher.interfaces.http.IHTTPRequest)
@interface.implementer(zope.publisher.http.IResult)
def FileResult(f, request):
    f = removeSecurityProxy(f)
    if request.response.getHeader('content-length') is None:
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        request.response.setHeader('Content-Length', str(size))
        
    wrapper = request.environment.get('wsgi.file_wrapper')
    if wrapper is not None:
        f = wrapper(f)
    else:
        f = FallbackWrapper(f)
    return f

# We need to provide an adapter for temporary files *if* they are different
# than regular files. Whether they are is system dependent. Sigh.
# If temporary files are the same type, we'll create a fake type just
# to make the registration work.
_tfile = tempfile.TemporaryFile()
_tfile.close()
_tfile = _tfile.__class__
if _tfile is file:
    # need a fake one. Sigh
    class _tfile:
        pass

@component.adapter(_tfile, zope.publisher.interfaces.http.IHTTPRequest)
@interface.implementer(zope.publisher.http.IResult)
def TemporaryFileResult(f, request):
    return FileResult(f, request)
