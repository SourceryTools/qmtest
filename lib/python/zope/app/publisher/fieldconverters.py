##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Zope-specific request field converters.

$Id: fieldconverters.py 67630 2006-04-27 00:54:03Z jim $
"""
from datetime import datetime

from zope.publisher.browser import registerTypeConverter
from zope.datetime import parse as parseDateTime

def field2date_via_datetimeutils(v):
    """Converter for request fields marshalled as ':date'.

    o TODO: Uses the non-localized and non-tzinfo-aware 'parseDateTime'
            utility from zope.datetime;  a better alternative
            would be more I18N / L10N aware, perhaps even adapting to
            the expressed preferences of the user.
    """
    if hasattr(v,'read'):
        v = v.read()
    else:
        v = str(v)

    # *Don't* force a timezone if not passed explicitly;  leave it as
    # "naive" datetime.
    year, month, day, hour, minute, second, tzname = parseDateTime(v, local=0)

    # TODO:  look up a real tzinfo object using 'tzname'
    #
    # Option 1:  Use 'timezones' module as global registry::
    #
    #   from zope.app.timezones import getTimezoneInfo
    #   tzinfo = getTimezoneInfo(tzname)
    #
    # Option 2:  Use a utility (or perhaps a view, for L10N).
    #
    #   tz_lookup = getUtility(ITimezoneLookup)
    #   tzinfo = tz_lookup(tzname)
    #
    return datetime(year, month, day, hour, minute, second,
                  # tzinfo=tzinfo
                   )

ZOPE_CONVERTERS = [('date', field2date_via_datetimeutils)]

def registerZopeConverters():

    for field_type, converter in ZOPE_CONVERTERS:
        registerTypeConverter(field_type, converter)
