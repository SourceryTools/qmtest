##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Five baseclasses for zope.formlib.form

$Id: view.py 65461 2006-02-25 19:50:17Z philikon $
"""
from zope.formlib import form, page

from Products.Five.browser import BrowserView
from Products.Five.formlib.formbase import AddForm, EditForm, Form
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from Products.Five.formlib.tests.content import IContent, Content

class AddContentForm(AddForm):
    """AddForm for creating and adding IContent objects
    """
    
    form_fields = form.Fields(IContent)

    def createAndAdd(self, data):
        id = data.get('id')
        ctnt = Content(
            id,  data.get('title'), somelist=data.get('somelist'))
        self.context._setObject(id, ctnt)

class EditContentForm(EditForm):
    """EditForm for editing IContent objects
    """
    
    form_fields = form.Fields(IContent)
    
