##############################################################################
#
# Copyright (c) 2002, 2003 Zope Corporation and Contributors.
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
"""Basic Object Formatting

This module implements basic object formatting functionality, such as
date/time, number and money formatting.

$Id: format.py 68836 2006-06-25 06:40:31Z hdima $
"""
import re
import math
import datetime
import pytz
import pytz.reference

from zope.i18n.interfaces import IDateTimeFormat, INumberFormat
from zope.interface import implements


def _findFormattingCharacterInPattern(char, pattern):
    return [entry for entry in pattern
            if isinstance(entry, tuple) and entry[0] == char]

class DateTimeParseError(Exception):
    """Error is raised when parsing of datetime failed."""

class DateTimeFormat(object):
    __doc__ = IDateTimeFormat.__doc__

    implements(IDateTimeFormat)

    _DATETIMECHARS = "aGyMdEDFwWhHmsSkKz"

    def __init__(self, pattern=None, calendar=None):
        if calendar is not None:
            self.calendar = calendar
        self._pattern = pattern
        self._bin_pattern = None
        if self._pattern is not None:
            self._bin_pattern = parseDateTimePattern(self._pattern,
                                                     self._DATETIMECHARS)

    def setPattern(self, pattern):
        "See zope.i18n.interfaces.IFormat"
        self._pattern = pattern
        self._bin_pattern = parseDateTimePattern(self._pattern,
                                                 self._DATETIMECHARS)

    def getPattern(self):
        "See zope.i18n.interfaces.IFormat"
        return self._pattern

    def parse(self, text, pattern=None, asObject=True):
        "See zope.i18n.interfaces.IFormat"
        # Make or get binary form of datetime pattern
        if pattern is not None:
            bin_pattern = parseDateTimePattern(pattern)
        else:
            bin_pattern = self._bin_pattern
            pattern = self._pattern

        # Generate the correct regular expression to parse the date and parse.
        regex = ''
        info = buildDateTimeParseInfo(self.calendar, bin_pattern)
        for elem in bin_pattern:
            regex += info.get(elem, elem)
        try:
            results = re.match(regex, text).groups()
        except AttributeError:
            raise DateTimeParseError(
                  'The datetime string did not match the pattern %r.'
                  % pattern)
        # Sometimes you only want the parse results
        if not asObject:
            return results

        # Map the parsing results to a datetime object
        ordered = [None, None, None, None, None, None, None]
        bin_pattern = filter(lambda x: isinstance(x, tuple), bin_pattern)

        # Handle years; note that only 'yy' and 'yyyy' are allowed
        if ('y', 2) in bin_pattern:
            year = int(results[bin_pattern.index(('y', 2))])
            if year > 30:
                ordered[0] = 1900 + year
            else:
                ordered[0] = 2000 + year
        if ('y', 4) in bin_pattern:
            ordered[0] = int(results[bin_pattern.index(('y', 4))])

        # Handle months (text)
        month_entry = _findFormattingCharacterInPattern('M', bin_pattern)
        if month_entry and month_entry[0][1] == 3:
            abbr = results[bin_pattern.index(month_entry[0])]
            ordered[1] = self.calendar.getMonthTypeFromAbbreviation(abbr)
        elif month_entry and month_entry[0][1] >= 4:
            name = results[bin_pattern.index(month_entry[0])]
            ordered[1] = self.calendar.getMonthTypeFromName(name)
        elif month_entry and month_entry[0][1] <= 2:
            ordered[1] = int(results[bin_pattern.index(month_entry[0])])

        # Handle hours with AM/PM
        hour_entry = _findFormattingCharacterInPattern('h', bin_pattern)
        if hour_entry:
            hour = int(results[bin_pattern.index(hour_entry[0])])
            ampm_entry = _findFormattingCharacterInPattern('a', bin_pattern)
            if not ampm_entry:
                raise DateTimeParseError(
                      'Cannot handle 12-hour format without am/pm marker.')
            ampm = self.calendar.pm == results[bin_pattern.index(ampm_entry[0])]
            if hour == 12:
                ampm = not ampm
            ordered[3] = (hour + 12*ampm)%24

        # Shortcut for the simple int functions
        dt_fields_map = {'d': 2, 'H': 3, 'm': 4, 's': 5, 'S': 6}
        for field in dt_fields_map.keys():
            entry = _findFormattingCharacterInPattern(field, bin_pattern)
            if not entry: continue
            pos = dt_fields_map[field]
            ordered[pos] = int(results[bin_pattern.index(entry[0])])

        # Handle timezones
        tzinfo = None
        pytz_tzinfo = False # If True, we should use pytz specific syntax
        tz_entry = _findFormattingCharacterInPattern('z', bin_pattern)
        if ordered[3:] != [None, None, None, None] and tz_entry:
            length = tz_entry[0][1]
            value = results[bin_pattern.index(tz_entry[0])]
            if length == 1:
                hours, mins = int(value[:-2]), int(value[-2:])
                tzinfo = pytz.FixedOffset(hours * 60 + mins)
            elif length == 2:
                hours, mins = int(value[:-3]), int(value[-2:])
                tzinfo = pytz.FixedOffset(hours * 60 + mins)
            else:
                try:
                    tzinfo = pytz.timezone(value)
                    pytz_tzinfo = True
                except KeyError:
                    # TODO: Find timezones using locale information
                    pass

        # Create a date/time object from the data
        # If we have a pytz tzinfo, we need to invoke localize() as per
        # the pytz documentation on creating local times.
        # NB. If we are in an end-of-DST transition period, we have a 50%
        # chance of getting a time 1 hour out here, but that is the price
        # paid for dealing with localtimes.
        if ordered[3:] == [None, None, None, None]:
            return datetime.date(*[e or 0 for e in ordered[:3]])
        elif ordered[:3] == [None, None, None]:
            if pytz_tzinfo:
                return tzinfo.localize(
                    datetime.time(*[e or 0 for e in ordered[3:]])
                    )
            else:
                return datetime.time(
                    *[e or 0 for e in ordered[3:]], **{'tzinfo' :tzinfo}
                    )
        else:
            if pytz_tzinfo:
                return tzinfo.localize(datetime.datetime(
                    *[e or 0 for e in ordered]
                    ))
            else:
                return datetime.datetime(
                    *[e or 0 for e in ordered], **{'tzinfo' :tzinfo}
                    )

    def format(self, obj, pattern=None):
        "See zope.i18n.interfaces.IFormat"
        # Make or get binary form of datetime pattern
        if pattern is not None:
            bin_pattern = parseDateTimePattern(pattern)
        else:
            bin_pattern = self._bin_pattern

        text = u''
        info = buildDateTimeInfo(obj, self.calendar, bin_pattern)
        for elem in bin_pattern:
            text += info.get(elem, elem)

        return text


class NumberParseError(Exception):
    """Error that can be raised when smething unexpected happens during the
    number parsing process."""


class NumberFormat(object):
    __doc__ = INumberFormat.__doc__

    implements(INumberFormat)

    def __init__(self, pattern=None, symbols={}):
        # setup default symbols
        self.symbols = {
            u'decimal': u'.',
            u'group': u',',
            u'list':  u';',
            u'percentSign': u'%',
            u'nativeZeroDigit': u'0',
            u'patternDigit': u'#',
            u'plusSign': u'+',
            u'minusSign': u'-',
            u'exponential': u'E',
            u'perMille': u'\xe2\x88\x9e',
            u'infinity': u'\xef\xbf\xbd',
            u'nan': '' }
        self.symbols.update(symbols)
        self._pattern = pattern
        self._bin_pattern = None
        if self._pattern is not None:
            self._bin_pattern = parseNumberPattern(self._pattern)

    def setPattern(self, pattern):
        "See zope.i18n.interfaces.IFormat"
        self._pattern = pattern
        self._bin_pattern = parseNumberPattern(self._pattern)

    def getPattern(self):
        "See zope.i18n.interfaces.IFormat"
        return self._pattern

    def parse(self, text, pattern=None):
        "See zope.i18n.interfaces.IFormat"
        # Make or get binary form of datetime pattern
        if pattern is not None:
            bin_pattern = parseNumberPattern(pattern)
        else:
            bin_pattern = self._bin_pattern
            pattern = self._pattern
        # Determine sign
        num_res = [None, None]
        for sign in (0, 1):
            regex = ''
            if bin_pattern[sign][PADDING1] is not None:
                regex += '[' + bin_pattern[sign][PADDING1] + ']+'
            if bin_pattern[sign][PREFIX] != '':
                regex += '[' + bin_pattern[sign][PREFIX] + ']'
            if bin_pattern[sign][PADDING2] is not None:
                regex += '[' + bin_pattern[sign][PADDING2] + ']+'
            regex += '([0-9'
            min_size = bin_pattern[sign][INTEGER].count('0')
            if bin_pattern[sign][GROUPING]:
                regex += self.symbols['group']
                min_size += min_size/3
            regex += ']{%i,100}' %(min_size)
            if bin_pattern[sign][FRACTION]:
                max_precision = len(bin_pattern[sign][FRACTION])
                min_precision = bin_pattern[sign][FRACTION].count('0')
                regex += '['+self.symbols['decimal']+']'
                regex += '[0-9]{%i,%i}' %(min_precision, max_precision)
            if bin_pattern[sign][EXPONENTIAL] != '':
                regex += self.symbols['exponential']
                min_exp_size = bin_pattern[sign][EXPONENTIAL].count('0')
                pre_symbols = self.symbols['minusSign']
                if bin_pattern[sign][EXPONENTIAL][0] == '+':
                    pre_symbols += self.symbols['plusSign']
                regex += '[%s]?[0-9]{%i,100}' %(pre_symbols, min_exp_size)
            regex +=')'
            if bin_pattern[sign][PADDING3] is not None:
                regex += '[' + bin_pattern[sign][PADDING3] + ']+'
            if bin_pattern[sign][SUFFIX] != '':
                regex += '[' + bin_pattern[sign][SUFFIX] + ']'
            if bin_pattern[sign][PADDING4] is not None:
                regex += '[' + bin_pattern[sign][PADDING4] + ']+'
            num_res[sign] = re.match(regex, text)

        if num_res[0] is not None:
            num_str = num_res[0].groups()[0]
            sign = +1
        elif num_res[1] is not None:
            num_str = num_res[1].groups()[0]
            sign = -1
        else:
            raise NumberParseError('Not a valid number for this pattern %r.'
                                    % pattern)
        # Remove possible grouping separators
        num_str = num_str.replace(self.symbols['group'], '')
        # Extract number
        type = int
        if self.symbols['decimal'] in num_str:
            type = float
            num_str = num_str.replace(self.symbols['decimal'], '.')
        if self.symbols['exponential'] in num_str:
            type = float
            num_str = num_str.replace(self.symbols['exponential'], 'E')
        return sign*type(num_str)

    def _format_integer(self, integer, pattern):
        size = len(integer)
        min_size = pattern.count('0')
        if size < min_size:
            integer = self.symbols['nativeZeroDigit']*(min_size-size) + integer
        return integer

    def _format_fraction(self, fraction, pattern):
        max_precision = len(pattern)
        min_precision = pattern.count('0')
        precision = len(fraction)
        roundInt = False
        if precision > max_precision:
            round = int(fraction[max_precision]) >= 5
            fraction = fraction[:max_precision]
            if round:
                if fraction != '':
                    # add 1 to the fraction, maintaining the decimal
                    # precision; if the result >= 1, need to roundInt
                    fractionLen = len(fraction)
                    rounded = int(fraction) + 1
                    fraction = ('%0' + str(fractionLen) + 'i') % rounded
                    if len(fraction) > fractionLen:	# rounded fraction >= 1
                        roundInt = True
                        fraction = fraction[1:]
                else:
                    # fraction missing, e.g. 1.5 -> 1. -- need to roundInt
                    roundInt = True

        if precision < min_precision:
            fraction += self.symbols['nativeZeroDigit']*(min_precision -
                                                         precision)
        if fraction != '':
            fraction = self.symbols['decimal'] + fraction
        return fraction, roundInt

    def format(self, obj, pattern=None):
        "See zope.i18n.interfaces.IFormat"
        # Make or get binary form of datetime pattern
        if pattern is not None:
            bin_pattern = parseNumberPattern(pattern)
        else:
            bin_pattern = self._bin_pattern
        # Get positive or negative sub-pattern
        if obj >= 0:
            bin_pattern = bin_pattern[0]
        else:
            bin_pattern = bin_pattern[1]


        if bin_pattern[EXPONENTIAL] != '':
            obj_int_frac = str(obj).split('.')
            # The exponential might have a mandatory sign; remove it from the
            # bin_pattern and remember the setting
            exp_bin_pattern = bin_pattern[EXPONENTIAL]
            plus_sign = u''
            if exp_bin_pattern.startswith('+'):
                plus_sign = self.symbols['plusSign']
                exp_bin_pattern = exp_bin_pattern[1:]
            # We have to remove the possible '-' sign
            if obj < 0:
                obj_int_frac[0] = obj_int_frac[0][1:]
            if obj_int_frac[0] == '0':
                # abs() of number smaller 1
                if len(obj_int_frac) > 1:
                    res = re.match('(0*)[0-9]*', obj_int_frac[1]).groups()[0]
                    exponent = self._format_integer(str(len(res)+1),
                                                    exp_bin_pattern)
                    exponent = self.symbols['minusSign']+exponent
                    number = obj_int_frac[1][len(res):]
                else:
                    # We have exactly 0
                    exponent = self._format_integer('0', exp_bin_pattern)
                    number = self.symbols['nativeZeroDigit']
            else:
                exponent = self._format_integer(str(len(obj_int_frac[0])-1),
                                                exp_bin_pattern)
                number = ''.join(obj_int_frac)

            fraction, roundInt = self._format_fraction(number[1:],
                                                       bin_pattern[FRACTION])
            if roundInt:
                number = str(int(number[0]) + 1) + fraction
            else:
                number = number[0] + fraction

            # We might have a plus sign in front of the exponential integer
            if not exponent.startswith('-'):
                exponent = plus_sign + exponent

            pre_padding = len(bin_pattern[FRACTION]) - len(number) + 2
            post_padding = len(exp_bin_pattern) - len(exponent)
            number += self.symbols['exponential'] + exponent

        else:
            obj_int_frac = str(obj).split('.')
            if len(obj_int_frac) > 1:
                fraction, roundInt = self._format_fraction(obj_int_frac[1],
                                                 bin_pattern[FRACTION])
            else:
                fraction = ''
                roundInt = False
            if roundInt:
                obj = round(obj)
            integer = self._format_integer(str(int(math.fabs(obj))),
                                           bin_pattern[INTEGER])
            # Adding grouping
            if bin_pattern[GROUPING] == 1:
                help = ''
                for pos in range(1, len(integer)+1):
                    if (pos-1)%3 == 0 and pos != 1:
                        help = self.symbols['group'] + help
                    help = integer[-pos] + help
                integer = help
            pre_padding = len(bin_pattern[INTEGER]) - len(integer)
            post_padding = len(bin_pattern[FRACTION]) - len(fraction)+1
            number = integer + fraction

        # Put it all together
        text = ''
        if bin_pattern[PADDING1] is not None and pre_padding > 0:
            text += bin_pattern[PADDING1]*pre_padding
        text += bin_pattern[PREFIX]
        if bin_pattern[PADDING2] is not None and pre_padding > 0:
            if bin_pattern[PADDING1] is not None:
                text += bin_pattern[PADDING2]
            else:
                text += bin_pattern[PADDING2]*pre_padding
        text += number
        if bin_pattern[PADDING3] is not None and post_padding > 0:
            if bin_pattern[PADDING4] is not None:
                text += bin_pattern[PADDING3]
            else:
                text += bin_pattern[PADDING3]*post_padding
        text += bin_pattern[SUFFIX]
        if bin_pattern[PADDING4] is not None and post_padding > 0:
            text += bin_pattern[PADDING4]*post_padding

        # TODO: Need to make sure unicode is everywhere
        return unicode(text)



DEFAULT = 0
IN_QUOTE = 1
IN_DATETIMEFIELD = 2

class DateTimePatternParseError(Exception):
    """DateTime Pattern Parse Error"""


def parseDateTimePattern(pattern, DATETIMECHARS="aGyMdEDFwWhHmsSkKz"):
    """This method can handle everything: time, date and datetime strings."""
    result = []
    state = DEFAULT
    helper = ''
    char = ''
    quote_start = -2

    for pos in range(len(pattern)):
        prev_char = char
        char = pattern[pos]
        # Handle quotations
        if char == "'":
            if state == DEFAULT:
                quote_start = pos
                state = IN_QUOTE
            elif state == IN_QUOTE and prev_char == "'":
                helper += char
                state = DEFAULT
            elif state == IN_QUOTE:
                # Do not care about putting the content of the quote in the
                # result. The next state is responsible for that.
                quote_start = -1
                state = DEFAULT
            elif state == IN_DATETIMEFIELD:
                result.append((helper[0], len(helper)))
                helper = ''
                quote_start = pos
                state = IN_QUOTE
        elif state == IN_QUOTE:
            helper += char

        # Handle regular characters
        elif char not in DATETIMECHARS:
            if state == IN_DATETIMEFIELD:
                result.append((helper[0], len(helper)))
                helper = char
                state = DEFAULT
            elif state == DEFAULT:
                helper += char

        # Handle special formatting characters
        elif char in DATETIMECHARS:
            if state == DEFAULT:
                # Clean up helper first
                if helper:
                    result.append(helper)
                helper = char
                state = IN_DATETIMEFIELD

            elif state == IN_DATETIMEFIELD and prev_char == char:
                helper += char

            elif state == IN_DATETIMEFIELD and prev_char != char:
                result.append((helper[0], len(helper)))
                helper = char

    # Some cleaning up
    if state == IN_QUOTE:
        if quote_start == -1:
            raise DateTimePatternParseError(
                  'Waaa: state = IN_QUOTE and quote_start = -1!')
        else:
            raise DateTimePatternParseError(
                  'The quote starting at character %i is not closed.' %
                   quote_start)
    elif state == IN_DATETIMEFIELD:
        result.append((helper[0], len(helper)))
    elif state == DEFAULT:
        result.append(helper)

    return result


def buildDateTimeParseInfo(calendar, pattern):
    """This method returns a dictionary that helps us with the parsing.
    It also depends on the locale of course."""
    info = {}
    # Generic Numbers
    for field in 'dDFkKhHmsSwW':
        for entry in _findFormattingCharacterInPattern(field, pattern):
            # The maximum amount of digits should be infinity, but 1000 is
            # close enough here.
            info[entry] = r'([0-9]{%i,1000})' %entry[1]

    # year (Number)
    for entry in _findFormattingCharacterInPattern('y', pattern):
        if entry[1] == 2:
            info[entry] = r'([0-9]{2})'
        elif entry[1] == 4:
            info[entry] = r'([0-9]{4})'
        else:
            raise DateTimePatternParseError("Only 'yy' and 'yyyy' allowed." )

    # am/pm marker (Text)
    for entry in _findFormattingCharacterInPattern('a', pattern):
        info[entry] = r'(%s|%s)' %(calendar.am, calendar.pm)

    # era designator (Text)
    # TODO: works for gregorian only right now
    for entry in _findFormattingCharacterInPattern('G', pattern):
        info[entry] = r'(%s|%s)' %(calendar.eras[1][1], calendar.eras[2][1])

    # time zone (Text)
    for entry in _findFormattingCharacterInPattern('z', pattern):
        if entry[1] == 1:
            info[entry] = r'([\+-][0-9]{3,4})'
        elif entry[1] == 2:
            info[entry] = r'([\+-][0-9]{2}:[0-9]{2})'
        elif entry[1] == 3:
            info[entry] = r'([a-zA-Z]{3})'
        else:
            info[entry] = r'([a-zA-Z /\.]*)'

    # month in year (Text and Number)
    for entry in _findFormattingCharacterInPattern('M', pattern):
        if entry[1] == 1:
            info[entry] = r'([0-9]{1,2})'
        elif entry[1] == 2:
            info[entry] = r'([0-9]{2})'
        elif entry[1] == 3:
            info[entry] = r'('+'|'.join(calendar.getMonthAbbreviations())+')'
        else:
            info[entry] = r'('+'|'.join(calendar.getMonthNames())+')'

    # day in week (Text and Number)
    for entry in _findFormattingCharacterInPattern('E', pattern):
        if entry[1] == 1:
            info[entry] = r'([0-9])'
        elif entry[1] == 2:
            info[entry] = r'([0-9]{2})'
        elif entry[1] == 3:
            info[entry] = r'('+'|'.join(calendar.getDayAbbreviations())+')'
        else:
            info[entry] = r'('+'|'.join(calendar.getDayNames())+')'

    return info


def buildDateTimeInfo(dt, calendar, pattern):
    """Create the bits and pieces of the datetime object that can be put
    together."""
    if isinstance(dt, datetime.time):
        dt = datetime.datetime(1969, 01, 01, dt.hour, dt.minute, dt.second,
                               dt.microsecond)
    elif (isinstance(dt, datetime.date) and
          not isinstance(dt, datetime.datetime)):
        dt = datetime.datetime(dt.year, dt.month, dt.day)

    if dt.hour >= 12:
        ampm = calendar.pm
    else:
        ampm = calendar.am

    h = dt.hour%12
    if h == 0:
        h = 12

    weekday = (dt.weekday() + (8 - calendar.week['firstDay'])) % 7 + 1

    day_of_week_in_month = (dt.day - 1) / 7 + 1

    week_in_month = (dt.day + 6 - dt.weekday()) / 7 + 1

    # Getting the timezone right
    tzinfo = dt.tzinfo or pytz.utc
    tz_secs = tzinfo.utcoffset(dt).seconds
    tz_secs = (tz_secs > 12*3600) and tz_secs-24*3600 or tz_secs
    tz_mins = int(math.fabs(tz_secs % 3600 / 60))
    tz_hours = int(math.fabs(tz_secs / 3600))
    tz_sign = (tz_secs < 0) and '-' or '+'
    tz_defaultname = "%s%i%.2i" %(tz_sign, tz_hours, tz_mins)
    tz_name = tzinfo.tzname(dt) or tz_defaultname
    tz_fullname = getattr(tzinfo, 'zone', None) or tz_name

    info = {('y', 2): unicode(dt.year)[2:],
            ('y', 4): unicode(dt.year),
            }

    # Generic Numbers
    for field, value in (('d', dt.day), ('D', int(dt.strftime('%j'))),
                         ('F', day_of_week_in_month), ('k', dt.hour or 24),
                         ('K', dt.hour%12), ('h', h), ('H', dt.hour),
                         ('m', dt.minute), ('s', dt.second),
                         ('S', dt.microsecond), ('w', int(dt.strftime('%W'))),
                         ('W', week_in_month)):
        for entry in _findFormattingCharacterInPattern(field, pattern):
            info[entry] = (u'%%.%ii' %entry[1]) %value

    # am/pm marker (Text)
    for entry in _findFormattingCharacterInPattern('a', pattern):
        info[entry] = ampm

    # era designator (Text)
    # TODO: works for gregorian only right now
    for entry in _findFormattingCharacterInPattern('G', pattern):
        info[entry] = calendar.eras[2][1]

    # time zone (Text)
    for entry in _findFormattingCharacterInPattern('z', pattern):
        if entry[1] == 1:
            info[entry] = u"%s%i%.2i" %(tz_sign, tz_hours, tz_mins)
        elif entry[1] == 2:
            info[entry] = u"%s%.2i:%.2i" %(tz_sign, tz_hours, tz_mins)
        elif entry[1] == 3:
            info[entry] = tz_name
        else:
            info[entry] = tz_fullname

    # month in year (Text and Number)
    for entry in _findFormattingCharacterInPattern('M', pattern):
        if entry[1] == 1:
            info[entry] = u'%i' %dt.month
        elif entry[1] == 2:
            info[entry] = u'%.2i' %dt.month
        elif entry[1] == 3:
            info[entry] = calendar.months[dt.month][1]
        else:
            info[entry] = calendar.months[dt.month][0]

    # day in week (Text and Number)
    for entry in _findFormattingCharacterInPattern('E', pattern):
        if entry[1] == 1:
            info[entry] = u'%i' %weekday
        elif entry[1] == 2:
            info[entry] = u'%.2i' %weekday
        elif entry[1] == 3:
            info[entry] = calendar.days[dt.weekday() + 1][1]
        else:
            info[entry] = calendar.days[dt.weekday() + 1][0]

    return info


# Number Pattern Parser States
BEGIN = 0
READ_PADDING_1 = 1
READ_PREFIX = 2
READ_PREFIX_STRING = 3
READ_PADDING_2 = 4
READ_INTEGER = 5
READ_FRACTION = 6
READ_EXPONENTIAL = 7
READ_PADDING_3 = 8
READ_SUFFIX = 9
READ_SUFFIX_STRING = 10
READ_PADDING_4 = 11
READ_NEG_SUBPATTERN = 12

# Binary Pattern Locators
PADDING1 = 0
PREFIX = 1
PADDING2 = 2
INTEGER = 3
FRACTION = 4
EXPONENTIAL = 5
PADDING3 = 6
SUFFIX = 7
PADDING4 = 8
GROUPING = 9

class NumberPatternParseError(Exception):
    """Number Pattern Parse Error"""


def parseNumberPattern(pattern):
    """Parses all sorts of number pattern."""
    prefix = ''
    padding_1 = None
    padding_2 = None
    padding_3 = None
    padding_4 = None
    integer = ''
    fraction = ''
    exponential = ''
    suffix = ''
    grouping = 0
    neg_pattern = None

    SPECIALCHARS = "*.,#0;E'"

    length = len(pattern)
    state = BEGIN
    helper = ''
    for pos in range(length):
        char = pattern[pos]
        if state == BEGIN:
            if char == '*':
                state = READ_PADDING_1
            elif char not in SPECIALCHARS:
                state = READ_PREFIX
                prefix += char
            elif char == "'":
                state = READ_PREFIX_STRING
            elif char in '#0':
                state = READ_INTEGER
                helper += char
            else:
                raise NumberPatternParseError(
                      'Wrong syntax at beginning of pattern.')

        elif state == READ_PADDING_1:
            padding_1 = char
            state = READ_PREFIX

        elif state == READ_PREFIX:
            if char == "*":
                state = READ_PADDING_2
            elif char == "'":
                state = READ_PREFIX_STRING
            elif char == "#" or char == "0":
                state = READ_INTEGER
                helper += char
            else:
                prefix += char

        elif state == READ_PREFIX_STRING:
            if char == "'":
                state = READ_PREFIX
            else:
                prefix += char

        elif state == READ_PADDING_2:
            padding_2 = char
            state = READ_INTEGER

        elif state == READ_INTEGER:
            if char == "#" or char == "0":
                helper += char
            elif char == ",":
                grouping = 1
            elif char == ".":
                integer = helper
                helper = ''
                state = READ_FRACTION
            elif char == "E":
                integer = helper
                helper = ''
                state = READ_EXPONENTIAL
            elif char == "*":
                integer = helper
                helper = ''
                state = READ_PADDING_3
            elif char == ";":
                integer = helper
                state = READ_NEG_SUBPATTERN
            elif char == "'":
                integer = helper
                state = READ_SUFFIX_STRING
            else:
                integer = helper
                suffix += char
                state = READ_SUFFIX

        elif state == READ_FRACTION:
            if char == "#" or char == "0":
                helper += char
            elif char == "E":
                fraction = helper
                helper = ''
                state = READ_EXPONENTIAL
            elif char == "*":
                fraction = helper
                helper = ''
                state = READ_PADDING_3
            elif char == ";":
                fraction = helper
                state = READ_NEG_SUBPATTERN
            elif char == "'":
                fraction = helper
                state = READ_SUFFIX_STRING
            else:
                fraction = helper
                suffix += char
                state = READ_SUFFIX

        elif state == READ_EXPONENTIAL:
            if char in ('0', '#', '+'):
                helper += char
            elif char == "*":
                exponential = helper
                helper = ''
                state = READ_PADDING_3
            elif char == ";":
                exponential = helper
                state = READ_NEG_SUBPATTERN
            elif char == "'":
                exponential = helper
                state = READ_SUFFIX_STRING
            else:
                exponential = helper
                suffix += char
                state = READ_SUFFIX

        elif state == READ_PADDING_3:
            padding_3 = char
            state = READ_SUFFIX

        elif state == READ_SUFFIX:
            if char == "*":
                state = READ_PADDING_4
            elif char == "'":
                state = READ_SUFFIX_STRING
            elif char == ";":
                state = READ_NEG_SUBPATTERN
            else:
                suffix += char

        elif state == READ_SUFFIX_STRING:
            if char == "'":
                state = READ_SUFFIX
            else:
                suffix += char

        elif state == READ_PADDING_4:
            if char == ';':
                state = READ_NEG_SUBPATTERN
            else:
                padding_4 = char

        elif state == READ_NEG_SUBPATTERN:
            neg_pattern = parseNumberPattern(pattern[pos:])[0]
            break

    # Cleaning up states after end of parsing
    if state == READ_INTEGER:
        integer = helper
    if state == READ_FRACTION:
        fraction = helper
    if state == READ_EXPONENTIAL:
        exponential = helper

    pattern = (padding_1, prefix, padding_2, integer, fraction, exponential,
               padding_3, suffix, padding_4, grouping)

    if neg_pattern is None:
        neg_pattern = pattern

    return pattern, neg_pattern
