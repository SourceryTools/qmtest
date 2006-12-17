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
"""Define view component for ZPT page eval results.

$Id: zptpage.py 68696 2006-06-17 02:25:39Z ctheune $
"""

import zope.formlib.form

import zope.app.zptpage.interfaces

class ZPTPageEval(object):

    def index(self, **kw):
        """Call a Page Template"""

        template = self.context
        request = self.request

        request.response.setHeader('content-type',
                                   template.content_type)

        return template.render(request, **kw)

class EditForm(zope.formlib.form.EditForm):
    """Edit form for ZPT pages."""

    form_fields = zope.formlib.form.Fields(
            zope.app.zptpage.interfaces.IZPTPage,
            render_context=True).omit('evaluateInlineCode')

    def setUpWidgets(self, ignore_request=False):
        self.adapters = {}

        # We need to extract the data directly, as we can not pass on the
        # request for macro expansion otherwise.
        data = {}
        data['source'] = self.context.getSource(self.request)

        self.widgets = zope.formlib.form.setUpWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            data=data, form=self, adapters=self.adapters,
            ignore_request=ignore_request)

