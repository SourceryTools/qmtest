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
"""Schema package constructor

$Id: __init__.py 69907 2006-08-31 21:16:48Z mgedmin $
"""
from zope.schema._field import Field, Container, Iterable, Orderable
from zope.schema._field import MinMaxLen, Choice
from zope.schema._field import Bytes, ASCII, BytesLine, ASCIILine
from zope.schema._field import Text, TextLine, Bool, Int, Float, Decimal
from zope.schema._field import Tuple, List, Set, FrozenSet
from zope.schema._field import Password, Dict, Datetime, Date, Timedelta
from zope.schema._field import Time, SourceText
from zope.schema._field import Object, URI, Id, DottedName
from zope.schema._field import InterfaceField
from zope.schema._schema import getFields, getFieldsInOrder
from zope.schema._schema import getFieldNames, getFieldNamesInOrder
from zope.schema.accessors import accessors
from zope.schema.interfaces import ValidationError
