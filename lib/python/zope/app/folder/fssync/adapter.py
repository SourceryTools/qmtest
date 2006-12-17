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
"""Filesystem synchronization support.

$Id$
"""
__docformat__ = 'restructuredtext'

from zope.fssync.server.entryadapter import DirectoryAdapter
from zope.app.component.interfaces import ISite


class FolderAdapter(DirectoryAdapter):
    """Adapter to provide an fssync interpretation of folders
    """

    def contents(self):
        """Compute a folder listing.

        A folder listing is a list of the items in the folder.  It is
        a combination of the folder contents and the site-manager, if
        a folder is a site.

        The adapter will take any mapping:

        >>> adapter = FolderAdapter({'x': 1, 'y': 2})
        >>> contents = adapter.contents()
        >>> contents.sort()
        >>> contents
        [('x', 1), ('y', 2)]

        If a folder is a site, then we'll get ++etc++site included:

        >>> import zope.interface
        >>> class Site(dict):
        ...     zope.interface.implements(ISite)
        ...
        ...     def getSiteManager(self):
        ...         return 'site goes here :)'
        
        >>> adapter = FolderAdapter(Site({'x': 1, 'y': 2}))
        >>> contents = adapter.contents()
        >>> contents.sort()
        >>> contents
        [('++etc++site', 'site goes here :)'), ('x', 1), ('y', 2)]

        """
        result = super(FolderAdapter, self).contents()
        if ISite.providedBy(self.context):
            sm = self.context.getSiteManager()
            result.append(('++etc++site', sm))
        return result
