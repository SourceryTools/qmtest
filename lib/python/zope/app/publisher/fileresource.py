##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Browser File Resource

$Id: fileresource.py 67630 2006-04-27 00:54:03Z jim $
"""
import os
import posixpath
from time import time

from zope.contenttype import guess_content_type
from zope.datetime import rfc1123_date


class File(object):
    
    def __init__(self, path, name):
        self.path = path

        f = open(path, 'rb')
        data = f.read()
        f.close()
        self.content_type, enc = guess_content_type(path, data)
        self.__name__ = name
        self.lmt = float(os.path.getmtime(path)) or time()
        self.lmh = rfc1123_date(self.lmt)


class Image(File):
    """Image objects stored in external files."""

    def __init__(self, path, name):
        super(Image, self).__init__(path, name)
        if self.content_type in (None, 'application/octet-stream'):
            ext = os.path.splitext(self.path)[1]
            if ext:
                self.content_type = 'image/%s' % ext[1:]
