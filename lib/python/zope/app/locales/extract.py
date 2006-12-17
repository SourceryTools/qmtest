#!/usr/bin/env python2.4
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
"""Extract message strings from python modules, page template files
and ZCML files.

$Id: extract.py 69460 2006-08-13 21:56:54Z philikon $
"""
__docformat__ = 'restructuredtext'

import os, sys, fnmatch
import time
import tokenize
import traceback
from pygettext import safe_eval, normalize, make_escapes

from zope.interface import implements
from zope.i18nmessageid import Message
from zope.app.locales.interfaces import IPOTEntry, IPOTMaker, ITokenEater

DEFAULT_CHARSET = 'UTF-8'
DEFAULT_ENCODING = '8bit'

pot_header = '''\
##############################################################################
#
# Copyright (c) 2003-2004 Zope Corporation and Contributors.
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
msgid ""
msgstr ""
"Project-Id-Version: %(version)s\\n"
"POT-Creation-Date: %(time)s\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: Zope 3 Developers <zope3-dev@zope.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=%(charset)s\\n"
"Content-Transfer-Encoding: %(encoding)s\\n"
"Generated-By: zope/app/locales/extract.py\\n"

'''

class POTEntry(object):
    r"""This class represents a single message entry in the POT file.

    >>> make_escapes(0)
    >>> class FakeFile(object):
    ...     def write(self, data):
    ...         print data,

    Let's create a message entry:

    >>> entry = POTEntry(Message("test", default="default"))
    >>> entry.addComment("# Some comment")
    >>> entry.addLocationComment(os.path.join("path", "file"), 10)

    Then we feed it a fake file:

    >>> entry.write(FakeFile())
    # Some comment
    #: path/file:10
    #. Default: "default"
    msgid "test"
    msgstr ""
    <BLANKLINE>

    Multiline default values generate correct comments:

    >>> entry = POTEntry(Message("test", default="\nline1\n\tline2"))
    >>> entry.write(FakeFile())
    #. Default: ""
    #.  "line1\n"
    #.  "\tline2"
    msgid "test"
    msgstr ""
    <BLANKLINE>
    """

    implements(IPOTEntry)

    def __init__(self, msgid, comments=None):
        self.msgid = msgid
        self.comments = comments or ''

    def addComment(self, comment):
        self.comments += comment + '\n'

    def addLocationComment(self, filename, line):
        self.comments += '#: %s:%s\n' % (
            filename.replace(os.sep, '/'), line)

    def write(self, file):
        if self.comments:
            file.write(self.comments)
        if (isinstance(self.msgid, Message) and
            self.msgid.default is not None):
            default = self.msgid.default.strip()
            lines = normalize(default).split("\n")
            lines[0] = "#. Default: %s\n" % lines[0]
            for i in range(1, len(lines)):
                lines[i] = "#.  %s\n" % lines[i]
            file.write("".join(lines))
        file.write('msgid %s\n' % normalize(self.msgid))
        file.write('msgstr ""\n')
        file.write('\n')

    def __cmp__(self, other):
        return cmp(self.comments, other.comments)

class POTMaker(object):
    """This class inserts sets of strings into a POT file.
    """
    implements(IPOTMaker)

    def __init__ (self, output_fn, path):
        self._output_filename = output_fn
        self.path = path
        self.catalog = {}

    def add(self, strings, base_dir=None):
        for msgid, locations in strings.items():
            if msgid == '':
                continue
            if msgid not in self.catalog:
                self.catalog[msgid] = POTEntry(msgid)

            for filename, lineno in locations:
                if base_dir is not None:
                    filename = filename.replace(base_dir, '')
                self.catalog[msgid].addLocationComment(filename, lineno)

    def _getProductVersion(self):
        # First, try to get the product version
        fn = os.path.join(self.path, 'version.txt')
        if os.path.exists(fn):
            return open(fn, 'r').read().strip()
        # Second, try to find a Zope version
        from zope.app.applicationcontrol.zopeversion import ZopeVersionUtility
        return ZopeVersionUtility.getZopeVersion()

    def write(self):
        file = open(self._output_filename, 'w')
        file.write(pot_header % {'time':     time.ctime(),
                                 'version':  self._getProductVersion(),
                                 'charset':  DEFAULT_CHARSET,
                                 'encoding': DEFAULT_ENCODING})

        # Sort the catalog entries by filename
        catalog = self.catalog.values()
        catalog.sort()

        # Write each entry to the file
        for entry in catalog:
            entry.write(file)

        file.close()

class TokenEater(object):
    """This is almost 100% taken from `pygettext.py`, except that I
    removed all option handling and output a dictionary.

    >>> eater = TokenEater()
    >>> make_escapes(0)

    TokenEater eats tokens generated by the standard python module
    `tokenize`.

    >>> import tokenize
    >>> from StringIO import StringIO

    We feed it a (fake) file:

    >>> file = StringIO(
    ...     "_(u'hello ${name}', u'buenos dias', {'name': 'Bob'}); "
    ...     "_(u'hi ${name}', mapping={'name': 'Bob'})"
    ...     )
    >>> tokenize.tokenize(file.readline, eater)

    The catalog of collected message ids contains our example

    >>> catalog = eater.getCatalog()
    >>> items = catalog.items()
    >>> items.sort()
    >>> items
    [(u'hello ${name}', [(None, 1)]), (u'hi ${name}', [(None, 1)])]

    The key in the catalog is not a unicode string, it's a real
    message id with a default value:

    >>> msgid = items.pop(0)[0]
    >>> msgid
    u'hello ${name}'
    >>> msgid.default
    u'buenos dias'

    >>> msgid = items.pop(0)[0]
    >>> msgid
    u'hi ${name}'
    >>> msgid.default
    u''

    Note that everything gets converted to unicode.
    """
    implements(ITokenEater)

    def __init__(self):
        self.__messages = {}
        self.__state = self.__waiting
        self.__data = []
        self.__lineno = -1
        self.__freshmodule = 1
        self.__curfile = None

    def __call__(self, ttype, tstring, stup, etup, line):
        self.__state(ttype, tstring, stup[0])

    def __waiting(self, ttype, tstring, lineno):
        if ttype == tokenize.NAME and tstring in ['_']:
            self.__state = self.__keywordseen

    def __suiteseen(self, ttype, tstring, lineno):
        # ignore anything until we see the colon
        if ttype == tokenize.OP and tstring == ':':
            self.__state = self.__suitedocstring

    def __suitedocstring(self, ttype, tstring, lineno):
        # ignore any intervening noise
        if ttype == tokenize.STRING:
            self.__addentry(safe_eval(tstring), lineno, isdocstring=1)
            self.__state = self.__waiting
        elif ttype not in (tokenize.NEWLINE, tokenize.INDENT,
                           tokenize.COMMENT):
            # there was no class docstring
            self.__state = self.__waiting

    def __keywordseen(self, ttype, tstring, lineno):
        if ttype == tokenize.OP and tstring == '(':
            self.__data = []
            self.__msgid = ''
            self.__default = ''
            self.__lineno = lineno
            self.__state = self.__openseen
        else:
            self.__state = self.__waiting

    def __openseen(self, ttype, tstring, lineno):
        if ((ttype == tokenize.OP and tstring == ')') or
                (ttype == tokenize.NAME and tstring == 'mapping')):
            # We've seen the last of the translatable strings.  Record the
            # line number of the first line of the strings and update the list
            # of messages seen.  Reset state for the next batch.  If there
            # were no strings inside _(), then just ignore this entry.
            if self.__data or self.__msgid:
                if self.__default:
                    msgid = self.__msgid
                    default = self.__default
                elif self.__msgid:
                    msgid = self.__msgid
                    default = ''.join(self.__data)
                else:
                    msgid = ''.join(self.__data)
                    default = None
                self.__addentry(msgid, default)
            self.__state = self.__waiting
        elif ttype == tokenize.OP and tstring == ',':
            if not self.__msgid:
                self.__msgid = ''.join(self.__data)
            elif not self.__default:
                self.__default = ''.join(self.__data)
            self.__data = []
        elif ttype == tokenize.STRING:
            self.__data.append(safe_eval(tstring))

    def __addentry(self, msg, default=None, lineno=None, isdocstring=0):
        if lineno is None:
            lineno = self.__lineno

        if default is not None:
            default = unicode(default)
        msg = Message(msg, default=default)
        entry = (self.__curfile, lineno)
        self.__messages.setdefault(msg, {})[entry] = isdocstring

    def set_filename(self, filename):
        self.__curfile = filename
        self.__freshmodule = 1

    def getCatalog(self):
        catalog = {}
        # Sort the entries.  First sort each particular entry's keys, then
        # sort all the entries by their first item.
        reverse = {}
        for k, v in self.__messages.items():
            keys = v.keys()
            keys.sort()
            reverse.setdefault(tuple(keys), []).append((k, v))
        rkeys = reverse.keys()
        rkeys.sort()
        for rkey in rkeys:
            rentries = reverse[rkey]
            rentries.sort()
            for msgid, locations in rentries:
                catalog[msgid] = []

                locations = locations.keys()
                locations.sort()

                for filename, lineno in locations:
                    catalog[msgid].append((filename, lineno))

        return catalog

def find_files(dir, pattern, exclude=()):
    files = []

    def visit(files, dirname, names):
        names[:] = filter(lambda x:x not in exclude, names)
        files += [os.path.join(dirname, name)
                  for name in fnmatch.filter(names, pattern)
                  if name not in exclude]

    os.path.walk(dir, visit, files)
    return files

def py_strings(dir, domain="zope", exclude=()):
    """Retrieve all Python messages from `dir` that are in the `domain`.
    """
    eater = TokenEater()
    make_escapes(0)
    for filename in find_files(
            dir, '*.py', exclude=('extract.py', 'pygettext.py')+tuple(exclude)):
        fp = open(filename)
        try:
            eater.set_filename(filename)
            try:
                tokenize.tokenize(fp.readline, eater)
            except tokenize.TokenError, e:
                print >> sys.stderr, '%s: %s, line %d, column %d' % (
                    e[0], filename, e[1][0], e[1][1])
        finally:
            fp.close()
    # One limitation of the Python message extractor is that it cannot
    # determine the domain of the string, since it is not contained anywhere
    # directly. The only way this could be done is by loading the module and
    # inspect the '_' function. For now we simply assume that all the found
    # strings have the domain the user specified.
    return eater.getCatalog()

def zcml_strings(dir, domain="zope", site_zcml=None):
    """Retrieve all ZCML messages from `dir` that are in the `domain`.
    """
    from zope.app.appsetup import config
    import zope
    dirname = os.path.dirname
    if site_zcml is None:
        # TODO this assumes a checkout directory structure
        site_zcml = os.path.join(dirname(dirname(dirname(zope.__file__))),
                                 "site.zcml")
    context = config(site_zcml, features=("devmode",), execute=False)
    return context.i18n_strings.get(domain, {})

def tal_strings(dir, domain="zope", include_default_domain=False, exclude=()):
    """Retrieve all TAL messages from `dir` that are in the `domain`.
    """
    # We import zope.tal.talgettext here because we can't rely on the
    # right sys path until app_dir has run
    from zope.tal.talgettext import POEngine, POTALInterpreter
    from zope.tal.htmltalparser import HTMLTALParser
    engine = POEngine()

    class Devnull(object):
        def write(self, s):
            pass

    for filename in find_files(dir, '*.pt', exclude=tuple(exclude)):
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

    # See whether anything in the domain was found
    if not engine.catalog.has_key(domain):
        return {}
    # We do not want column numbers.
    catalog = engine.catalog[domain].copy()
    # When the Domain is 'default', then this means that none was found;
    # Include these strings; yes or no?
    if include_default_domain:
        catalog.update(engine.catalog['default'])
    for msgid, locations in catalog.items():
        catalog[msgid] = map(lambda l: (l[0], l[1][0]), locations)
    return catalog
