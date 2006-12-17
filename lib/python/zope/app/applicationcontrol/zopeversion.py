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
"""Utility to retrieve the Zope version.

$Id: zopeversion.py 41452 2006-01-26 14:57:18Z hdima $
"""
__docformat__ = 'restructuredtext'

import os
import re
from xml.dom.minidom import parse

import zope.app
from zope.app.applicationcontrol.interfaces import IZopeVersion
from zope.interface import implements


class ZopeVersion(object):

    implements(IZopeVersion)

    __tags = re.compile(r'/(tags|branches)/([^/]+)/')

    def __init__(self, path=None):
        if path is None:
            path = os.path.dirname(os.path.abspath(zope.app.__file__))
        self.path = path
        self.result = None

    def getZopeVersion(self):
        """See zope.app.applicationcontrol.interfaces.IZopeVersion"""
        if self.result is not None:
            return self.result

        self.result = "Development/Unknown"

        # is this a SVN checkout?
        svndir = os.path.join(self.path, ".svn")
        if os.path.isdir(svndir):
            self.__setSVNVersion(svndir)
        else:
            # try to get official Zope release information
            versionfile = os.path.join(self.path, "version.txt")
            if os.path.isfile(versionfile):
                f = file(versionfile)
                try:
                    self.result = f.readline().strip() or self.result
                finally:
                    f.close()
        return self.result

    def __setSVNVersion(self, svndir):
            entriesfile = os.path.join(svndir, "entries")

            # get the version information
            if os.path.isfile(entriesfile):
                doc = parse(entriesfile)
                here = doc.getElementsByTagNameNS("svn:", "entry").item(0)
                if here:
                    url = here.getAttribute("url")
                    revision = here.getAttribute("revision")

                    if revision and url:
                        match = self.__tags.search(url)
                        if match is None:
                            tag = ""
                        else:
                            type, value = match.groups()
                            if type == "tags":
                                tag = "/Tag: %s" % value
                            elif type == "branches":
                                tag = "/Branch: %s" % value
                        self.result = ("Development/Revision: %s%s"
                                      % (revision, tag))

ZopeVersionUtility = ZopeVersion()
