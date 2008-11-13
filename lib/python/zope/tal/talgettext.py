#!/usr/bin/env python
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
"""Program to extract internationalization markup from Page Templates.

Once you have marked up a Page Template file with i18n: namespace tags, use
this program to extract GNU gettext .po file entries.

Usage: talgettext.py [options] files
Options:
    -h / --help
        Print this message and exit.
    -o / --output <file>
        Output the translation .po file to <file>.
    -u / --update <file>
        Update the existing translation <file> with any new translation strings
        found.

$Id: talgettext.py 39851 2005-11-02 22:11:10Z srichter $
"""
import sys
import time
import getopt
import traceback

from zope.interface import implements
from zope.tal.htmltalparser import HTMLTALParser
from zope.tal.talinterpreter import TALInterpreter, normalize
from zope.tal.dummyengine import DummyEngine
from zope.tal.interfaces import ITALExpressionEngine
from zope.tal.taldefs import TALExpressionError
from zope.i18nmessageid import Message

pot_header = '''\
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR ORGANIZATION
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"POT-Creation-Date: %(time)s\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=CHARSET\\n"
"Content-Transfer-Encoding: ENCODING\\n"
"Generated-By: talgettext.py %(version)s\\n"
'''

NLSTR = '"\n"'

def usage(code, msg=''):
    # Python 2.1 required
    print >> sys.stderr, __doc__
    if msg:
        print >> sys.stderr, msg
    sys.exit(code)


class POTALInterpreter(TALInterpreter):
    def translate(self, msgid, default=None, i18ndict=None, obj=None):
        if default is None:
            default = getattr(msgid, 'default', unicode(msgid))
        # If no i18n dict exists yet, create one.
        if i18ndict is None:
            i18ndict = {}
        if obj:
            i18ndict.update(obj)
        # Mmmh, it seems that sometimes the msgid is None; is that really
        # possible?
        if msgid is None:
            return None
        # TODO: We need to pass in one of context or target_language
        return self.engine.translate(msgid, self.i18nContext.domain, i18ndict,
                                     default=default, position=self.position)


class POEngine(DummyEngine):
    implements(ITALExpressionEngine)

    def __init__(self, macros=None):
        self.catalog = {}
        DummyEngine.__init__(self, macros)

    def evaluate(*args):
        # If the result of evaluate ever gets into a message ID, we want
        # to notice the fact in the .pot file.
        return '${DYNAMIC_CONTENT}'

    def evaluatePathOrVar(*args):
        # Actually this method is never called.
        return 'XXX'

    def evaluateSequence(self, expr):
        return (0,) # dummy

    def evaluateBoolean(self, expr):
        return True # dummy

    def translate(self, msgid, domain=None, mapping=None, default=None,
                  # Position is not part of the ITALExpressionEngine
                  # interface
                  position=None):

        # Make the message is a Message object, if the default differs
        # from the value, so that the POT generator can put the default
        # text into a comment.
        if default is not None and normalize(default) != msgid:
            msgid = Message(msgid, default=default)

        if domain not in self.catalog:
            self.catalog[domain] = {}
        domain = self.catalog[domain]

        if msgid not in domain:
            domain[msgid] = []
        domain[msgid].append((self.file, position))
        return 'x'


class UpdatePOEngine(POEngine):
    """A slightly-less braindead POEngine which supports loading an existing
    .po file first."""

    def __init__ (self, macros=None, filename=None):
        POEngine.__init__(self, macros)

        self._filename = filename
        self._loadFile()
        self.base = self.catalog
        self.catalog = {}

    def __add(self, id, s, fuzzy):
        "Add a non-fuzzy translation to the dictionary."
        if not fuzzy and str:
            # check for multi-line values and munge them appropriately
            if '\n' in s:
                lines = s.rstrip().split('\n')
                s = NLSTR.join(lines)
            self.catalog[id] = s

    def _loadFile(self):
        # shamelessly cribbed from Python's Tools/i18n/msgfmt.py
        # 25-Mar-2003 Nathan R. Yergler (nathan@zope.org)
        # 14-Apr-2003 Hacked by Barry Warsaw (barry@zope.com)

        ID = 1
        STR = 2

        try:
            lines = open(self._filename).readlines()
        except IOError, msg:
            print >> sys.stderr, msg
            sys.exit(1)

        section = None
        fuzzy = False

        # Parse the catalog
        lno = 0
        for l in lines:
            lno += True
            # If we get a comment line after a msgstr, this is a new entry
            if l[0] == '#' and section == STR:
                self.__add(msgid, msgstr, fuzzy)
                section = None
                fuzzy = False
            # Record a fuzzy mark
            if l[:2] == '#,' and l.find('fuzzy'):
                fuzzy = True
            # Skip comments
            if l[0] == '#':
                continue
            # Now we are in a msgid section, output previous section
            if l.startswith('msgid'):
                if section == STR:
                    self.__add(msgid, msgstr, fuzzy)
                section = ID
                l = l[5:]
                msgid = msgstr = ''
            # Now we are in a msgstr section
            elif l.startswith('msgstr'):
                section = STR
                l = l[6:]
            # Skip empty lines
            if not l.strip():
                continue
            # TODO: Does this always follow Python escape semantics?
            l = eval(l)
            if section == ID:
                msgid += l
            elif section == STR:
                msgstr += '%s\n' % l
            else:
                print >> sys.stderr, 'Syntax error on %s:%d' % (infile, lno), \
                      'before:'
                print >> sys.stderr, l
                sys.exit(1)
        # Add last entry
        if section == STR:
            self.__add(msgid, msgstr, fuzzy)

    def evaluate(self, expression):
        try:
            return POEngine.evaluate(self, expression)
        except TALExpressionError:
            pass

    def evaluatePathOrVar(self, expr):
        return 'who cares'

    def translate(self, msgid, domain=None, mapping=None, default=None,
                  position=None):
        if msgid not in self.base:
            POEngine.translate(self, msgid, domain, mapping, default, position)
        return 'x'


def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'ho:u:',
            ['help', 'output=', 'update='])
    except getopt.error, msg:
        usage(1, msg)

    outfile = None
    engine = None
    update_mode = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-o', '--output'):
            outfile = arg
        elif opt in ('-u', '--update'):
            update_mode = True
            if outfile is None:
                outfile = arg
            engine = UpdatePOEngine(filename=arg)

    if not args:
        print 'nothing to do'
        return

    # We don't care about the rendered output of the .pt file
    class Devnull(object):
        def write(self, s):
            pass

    # check if we've already instantiated an engine;
    # if not, use the stupidest one available
    if not engine:
        engine = POEngine()

    # process each file specified
    for filename in args:
        try:
            engine.file = filename
            p = HTMLTALParser()
            p.parseFile(filename)
            program, macros = p.getCode()
            POTALInterpreter(program, macros, engine, stream=Devnull(),
                             metal=False)()
        except: # Hee hee, I love bare excepts!
            print 'There was an error processing', filename
            traceback.print_exc()

    # Now output the keys in the engine.  Write them to a file if --output or
    # --update was specified; otherwise use standard out.
    if (outfile is None):
        outfile = sys.stdout
    else:
        outfile = file(outfile, update_mode and "a" or "w")

    catalog = {}
    for domain in engine.catalog.keys():
        catalog.update(engine.catalog[domain])

    messages = catalog.copy()
    try:
        messages.update(engine.base)
    except AttributeError:
        pass
    if '' not in messages:
        print >> outfile, pot_header % {'time': time.ctime(),
                                        'version': __version__}

    msgids = catalog.keys()
    # TODO: You should not sort by msgid, but by filename and position. (SR)
    msgids.sort()
    for msgid in msgids:
        positions = engine.catalog[msgid]
        for filename, position in positions:
            outfile.write('#: %s:%s\n' % (filename, position[0]))

        outfile.write('msgid "%s"\n' % msgid)
        outfile.write('msgstr ""\n')
        outfile.write('\n')


if __name__ == '__main__':
    main()
