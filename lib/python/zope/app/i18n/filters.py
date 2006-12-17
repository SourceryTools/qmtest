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
"""Translation Domain Message Export and Import Filters

$Id: filters.py 38178 2005-08-30 21:50:19Z mj $
"""
__docformat__ = 'restructuredtext'

import time, re
from types import StringTypes
from zope.interface import implements

from zope.i18n.interfaces import IMessageExportFilter, IMessageImportFilter
from zope.app.i18n.interfaces import ILocalTranslationDomain


class ParseError(Exception):
    def __init__(self, state, lineno):
        Exception.__init__(self, state, lineno)
        self.state = state
        self.lineno = lineno

    def __str__(self):
        return "state %s, line %s" % (self.state, self.lineno)


class GettextExportFilter(object):

    implements(IMessageExportFilter)
    __used_for__ = ILocalTranslationDomain


    def __init__(self, domain):
        self.domain = domain

    def exportMessages(self, languages):
        'See IMessageExportFilter'
        domain = self.domain.domain

        if isinstance(languages, StringTypes):
            language = languages
        elif len(languages) == 1:
            language = languages[0]
        else:
            raise TypeError(
                'Only one language at a time is supported for gettext export.')

        dt = time.time()
        dt = time.localtime(dt)
        dt = time.strftime('%Y/%m/%d %H:%M', dt)
        output = _file_header %(dt, language.encode('UTF-8'),
                                domain.encode('UTF-8'))

        for msgid in self.domain.getMessageIds():
            msgstr = self.domain.translate(msgid, target_language=language)
            msgstr = msgstr.encode('UTF-8')
            msgid = msgid.encode('UTF-8')
            output += _msg_template %(msgid, msgstr)

        return output



class GettextImportFilter(object):

    implements(IMessageImportFilter)
    __used_for__ = ILocalTranslationDomain


    def __init__(self, domain):
        self.domain = domain

    def importMessages(self, languages, file):
        'See IMessageImportFilter'

        if isinstance(languages, StringTypes):
            language = languages
        elif len(languages) == 1:
            language = languages[0]
        else:
            raise TypeError(
                'Only one language at a time is supported for gettext export.')

        result = parseGetText(file.readlines())[3]
        headers = parserHeaders(''.join(result[('',)][1]))
        del result[('',)]
        charset = extractCharset(headers['content-type'])
        for msg in result.items():
            msgid = unicode(''.join(msg[0]), charset)
            msgid = msgid.replace('\\n', '\n')
            msgstr = unicode(''.join(msg[1][1]), charset)
            msgstr = msgstr.replace('\\n', '\n')
            self.domain.addMessage(msgid, msgstr, language)



def extractCharset(header):
    charset = header.split('charset=')[-1]
    return charset.lower()


def parserHeaders(headers_text):
    headers = {}
    for line in headers_text.split('\\n'):
        name = line.split(':')[0]
        value = ''.join(line.split(':')[1:])
        headers[name.lower()] = value

    return headers


def parseGetText(content):
    # The regular expressions
    com = re.compile('^#.*')
    msgid = re.compile(r'^ *msgid *"(.*?[^\\]*)"')
    msgstr = re.compile(r'^ *msgstr *"(.*?[^\\]*)"')
    re_str = re.compile(r'^ *"(.*?[^\\])"')
    blank = re.compile(r'^\s*$')

    trans = {}
    pointer = 0
    state = 0
    COM, MSGID, MSGSTR = [], [], []
    while pointer < len(content):
        line = content[pointer]
        #print 'STATE:', state
        #print 'LINE:', line, content[pointer].strip()
        if state == 0:
            COM, MSGID, MSGSTR = [], [], []
            if com.match(line):
                COM.append(line.strip())
                state = 1
                pointer = pointer + 1
            elif msgid.match(line):
                MSGID.append(msgid.match(line).group(1))
                state = 2
                pointer = pointer + 1
            elif blank.match(line):
                pointer = pointer + 1
            else:
                raise ParseError(0, pointer + 1)
        elif state == 1:
            if com.match(line):
                COM.append(line.strip())
                state = 1
                pointer = pointer + 1
            elif msgid.match(line):
                MSGID.append(msgid.match(line).group(1))
                state = 2
                pointer = pointer + 1
            elif blank.match(line):
                pointer = pointer + 1
            else:
                raise ParseError(1, pointer + 1)

        elif state == 2:
            if com.match(line):
                COM.append(line.strip())
                state = 2
                pointer = pointer + 1
            elif re_str.match(line):
                MSGID.append(re_str.match(line).group(1))
                state = 2
                pointer = pointer + 1
            elif msgstr.match(line):
                MSGSTR.append(msgstr.match(line).group(1))
                state = 3
                pointer = pointer + 1
            elif blank.match(line):
                pointer = pointer + 1
            else:
                raise ParseError(2, pointer + 1)

        elif state == 3:
            if com.match(line) or msgid.match(line):
                # print "\nEn", language, "detected", MSGID
                trans[tuple(MSGID)] = (COM, MSGSTR)
                state = 0
            elif re_str.match(line):
                MSGSTR.append(re_str.match(line).group(1))
                state = 3
                pointer = pointer + 1
            elif blank.match(line):
                pointer = pointer + 1
            else:
                raise ParseError(3, pointer + 1)

    # the last also goes in
    if tuple(MSGID):
        trans[tuple(MSGID)] = (COM, MSGSTR)

    return COM, MSGID, MSGSTR, trans


_file_header = '''
msgid ""
msgstr ""
"Project-Id-Version: Zope 3\\n"
"PO-Revision-Date: %s\\n"
"Last-Translator: Zope 3 Gettext Export Filter\\n"
"Zope-Language: %s\\n"
"Zope-Domain: %s\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
'''

_msg_template = '''
msgid "%s"
msgstr "%s"
'''
