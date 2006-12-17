##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Browser widgets for items

$Id: boolwidgets.py 39064 2005-10-11 18:40:10Z philikon $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary

from zope.app.form.browser.widget import SimpleInputWidget, renderElement
from zope.app.form.browser.widget import DisplayWidget
from zope.app.form.browser.itemswidgets import RadioWidget
from zope.app.form.browser.itemswidgets import SelectWidget, DropdownWidget
from zope.app.form.interfaces import IInputWidget
from zope.app.i18n import ZopeMessageFactory as _

class CheckBoxWidget(SimpleInputWidget):
    """A checkbox widget used to display Bool fields.
    
    For more detailed documentation, including sample code, see
    ``tests/test_checkboxwidget.py``.
    """    
    type = 'checkbox'
    default = 0
    extra = ''

    def __call__(self):
        """Render the widget to HTML."""
        value = self._getFormValue()
        if value == 'on':
            kw = {'checked': 'checked'}
        else:
            kw = {}
        return "%s %s" % (
            renderElement(self.tag,
                          type='hidden',
                          name=self.name+".used",
                          id=self.name+".used",
                          value=""
                          ),
            renderElement(self.tag,
                          type=self.type,
                          name=self.name,
                          id=self.name,
                          cssClass=self.cssClass,
                          extra=self.extra,
                          value="on",
                          **kw),
            )

    def _toFieldValue(self, input):
        """Convert from HTML presentation to Python bool."""
        return input == 'on'

    def _toFormValue(self, value):
        """Convert from Python bool to HTML representation."""
        return value and 'on' or ''

    def hasInput(self):
        """Check whether the field is represented in the form."""
        return self.name + ".used" in self.request.form or \
            super(CheckBoxWidget, self).hasInput()

    def _getFormInput(self):
        """Returns the form input used by `_toFieldValue`.
        
        Return values:
        
          ``'on'``  checkbox is checked
          ``''``    checkbox is not checked
          ``None``  form input was not provided

        """
        if self.request.get(self.name) == 'on':
            return 'on'
        elif self.name + '.used' in self.request:
            return ''
        else:
            return None


def BooleanRadioWidget(field, request, true=_('on'), false=_('off')):
    vocabulary = SimpleVocabulary.fromItems( ((true, True), (false, False)) ) 
    return RadioWidget(field, vocabulary, request)


def BooleanSelectWidget(field, request, true=_('on'), false=_('off')):
    vocabulary = SimpleVocabulary.fromItems( ((true, True), (false, False)) )
    widget = SelectWidget(field, vocabulary, request)
    widget.size = 2
    return widget


def BooleanDropdownWidget(field, request, true=_('on'), false=_('off')):
    vocabulary = SimpleVocabulary.fromItems( ((true, True), (false, False)) )
    return DropdownWidget(field, vocabulary, request)


_msg_true = _("True")
_msg_false = _("False")

class BooleanDisplayWidget(DisplayWidget):

    def __call__(self):
        if self._renderedValueSet():
            value = self._data
        else:
            value = self.context.default
        if value:
            return _msg_true
        else:
            return _msg_false
