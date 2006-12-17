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
"""Browser widgets

$Id: __init__.py 68937 2006-07-01 17:18:56Z hdima $
"""
__docformat__ = 'restructuredtext'

from zope.app.form.browser.widget import BrowserWidget, DisplayWidget
from zope.app.form.browser.widget import UnicodeDisplayWidget

from zope.app.form.browser.textwidgets import TextWidget, BytesWidget
from zope.app.form.browser.textwidgets import TextAreaWidget, BytesAreaWidget
from zope.app.form.browser.textwidgets import PasswordWidget, FileWidget
from zope.app.form.browser.textwidgets import ASCIIWidget, ASCIIAreaWidget
from zope.app.form.browser.textwidgets import IntWidget, FloatWidget
from zope.app.form.browser.textwidgets import DatetimeWidget, DateWidget
from zope.app.form.browser.textwidgets import DatetimeI18nWidget
from zope.app.form.browser.textwidgets import DateI18nWidget
from zope.app.form.browser.textwidgets import DatetimeDisplayWidget
from zope.app.form.browser.textwidgets import DateDisplayWidget
from zope.app.form.browser.textwidgets import BytesDisplayWidget
from zope.app.form.browser.textwidgets import ASCIIDisplayWidget
from zope.app.form.browser.textwidgets import URIDisplayWidget

# Widgets for boolean fields
from zope.app.form.browser.boolwidgets import CheckBoxWidget
from zope.app.form.browser.boolwidgets import BooleanRadioWidget
from zope.app.form.browser.boolwidgets import BooleanSelectWidget
from zope.app.form.browser.boolwidgets import BooleanDropdownWidget

# Choice and Sequence Display Widgets
from zope.app.form.browser.itemswidgets import ItemDisplayWidget
from zope.app.form.browser.itemswidgets import ItemsMultiDisplayWidget
from zope.app.form.browser.itemswidgets import SetDisplayWidget
from zope.app.form.browser.itemswidgets import ListDisplayWidget

# Widgets for fields with vocabularies.
# Note that these are only dispatchers for the widgets below.
from zope.app.form.browser.itemswidgets import ChoiceDisplayWidget
from zope.app.form.browser.itemswidgets import ChoiceInputWidget
from zope.app.form.browser.itemswidgets import CollectionDisplayWidget
from zope.app.form.browser.itemswidgets import CollectionInputWidget
from zope.app.form.browser.itemswidgets import ChoiceCollectionDisplayWidget
from zope.app.form.browser.itemswidgets import ChoiceCollectionInputWidget

# Widgets that let you choose a single item from a list
# These widgets are multi-views on (field, vocabulary)
from zope.app.form.browser.itemswidgets import SelectWidget
from zope.app.form.browser.itemswidgets import DropdownWidget
from zope.app.form.browser.itemswidgets import RadioWidget

# Widgets that let you choose several items from a list
# These widgets are multi-views on (field, vocabulary)
from zope.app.form.browser.itemswidgets import MultiSelectWidget
from zope.app.form.browser.itemswidgets import MultiSelectSetWidget
from zope.app.form.browser.itemswidgets import MultiCheckBoxWidget
from zope.app.form.browser.itemswidgets import OrderedMultiSelectWidget

# Widgets that let you enter several items in a sequence
# These widgets are multi-views on (sequence type, value type)
from zope.app.form.browser.sequencewidget import SequenceWidget
from zope.app.form.browser.sequencewidget import TupleSequenceWidget
from zope.app.form.browser.sequencewidget import ListSequenceWidget
from zope.app.form.browser.sequencewidget import SequenceDisplayWidget

from zope.app.form.browser.objectwidget import ObjectWidget
