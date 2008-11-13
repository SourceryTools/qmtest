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
"""Page Template Resource

$Id: pagetemplateresource.py 26642 2004-07-20 21:48:46Z fdrake $
"""

from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from zope.app.pagetemplate.engine import TrustedAppPT

class PageTemplate(TrustedAppPT, PageTemplateFile):
    """
    Resource that is a page template
    """

    def __init__(self, filename, _prefix=None, content_type=None):
        _prefix = self.get_path_from_prefix(_prefix)
        super(PageTemplate, self).__init__(filename, _prefix)
        if content_type is not None:
            self.content_type = content_type

    def pt_getContext(self, request, **kw):
        namespace = super(PageTemplate, self).pt_getContext(**kw)
        namespace['context'] = None
        namespace['request'] = request
        return namespace

    def __call__(self, request, **keywords):
        namespace = self.pt_getContext(
            request=request,
            options=keywords
            )
        return self.pt_render(namespace)
