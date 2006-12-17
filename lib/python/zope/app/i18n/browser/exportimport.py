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
"""Message Export/Import View

$Id: exportimport.py 26889 2004-08-04 04:00:36Z pruggera $
"""
__docformat__ = 'restructuredtext'

from zope.app.i18n.browser import BaseView
from zope.i18n.interfaces import IMessageExportFilter, IMessageImportFilter

class ExportImport(BaseView):

    def exportMessages(self, languages):
        self.request.response.setHeader('content-type',
                                        'application/x-gettext')
        filter = IMessageExportFilter(self.context)
        return filter.exportMessages(languages)

    def importMessages(self, languages, file):
        filter = IMessageImportFilter(self.context)
        filter.importMessages(languages, file)
        return self.request.response.redirect(self.request.URL[-1])
