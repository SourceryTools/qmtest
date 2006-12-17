##############################################################################
#
# Copyright (c) 2001, 2002, 2003 Zope Corporation and Contributors.
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
"""Dummy TAL expression engine so that I can test out the TAL implementation.

$Id: dummyengine.py 67630 2006-04-27 00:54:03Z jim $
"""
import re

from zope.interface import implements
from zope.tal.taldefs import NAME_RE, TALExpressionError, ErrorInfo
from zope.tal.interfaces import ITALExpressionCompiler, ITALExpressionEngine
from zope.i18nmessageid import Message
from zope.i18n.interfaces import ITranslationDomain

Default = object()

name_match = re.compile(r"(?s)(%s):(.*)\Z" % NAME_RE).match

class CompilerError(Exception):
    pass

class DummyEngine(object):

    position = None
    source_file = None

    implements(ITALExpressionCompiler, ITALExpressionEngine)

    def __init__(self, macros=None):
        if macros is None:
            macros = {}
        self.macros = macros
        dict = {'nothing': None, 'default': Default}
        self.locals = self.globals = dict
        self.stack = [dict]
        self.translationDomain = DummyTranslationDomain()
        self.useEngineAttrDicts = False

    # zope.tal.interfaces.ITALExpressionCompiler

    def getCompilerError(self):
        return CompilerError

    def compile(self, expr):
        return "$%s$" % expr

    # zope.tal.interfaces.ITALExpressionEngine

    def setSourceFile(self, source_file):
        self.source_file = source_file

    def setPosition(self, position):
        self.position = position

    def beginScope(self):
        self.stack.append(self.locals)

    def endScope(self):
        assert len(self.stack) > 1, "more endScope() than beginScope() calls"
        self.locals = self.stack.pop()

    def setLocal(self, name, value):
        if self.locals is self.stack[-1]:
            # Unmerge this scope's locals from previous scope of first set
            self.locals = self.locals.copy()
        self.locals[name] = value

    def setGlobal(self, name, value):
        self.globals[name] = value

    def getValue(self, name, default=None):
        value = self.globals.get(name, default)
        if value is default:
            value = self.locals.get(name, default)
        return value

    def evaluate(self, expression):
        assert (expression.startswith("$") and expression.endswith("$"),
            expression)
        expression = expression[1:-1]
        m = name_match(expression)
        if m:
            type, expr = m.group(1, 2)
        else:
            type = "path"
            expr = expression

        if type in ("string", "str"):
            return expr
        if type in ("path", "var", "global", "local"):
            return self.evaluatePathOrVar(expr)
        if type == "not":
            return not self.evaluate(expr)
        if type == "exists":
            return self.locals.has_key(expr) or self.globals.has_key(expr)
        if type == "python":
            try:
                return eval(expr, self.globals, self.locals)
            except:
                raise TALExpressionError("evaluation error in %s" % `expr`)
        if type == "position":
            # Insert the current source file name, line number,
            # and column offset.
            if self.position:
                lineno, offset = self.position
            else:
                lineno, offset = None, None
            return '%s (%s,%s)' % (self.source_file, lineno, offset)
        raise TALExpressionError("unrecognized expression: " + `expression`)

    # implementation; can be overridden
    def evaluatePathOrVar(self, expr):
        expr = expr.strip()
        if self.locals.has_key(expr):
            return self.locals[expr]
        elif self.globals.has_key(expr):
            return self.globals[expr]
        else:
            raise TALExpressionError("unknown variable: %s" % `expr`)

    def evaluateValue(self, expr):
        return self.evaluate(expr)

    def evaluateBoolean(self, expr):
        return self.evaluate(expr)

    def evaluateText(self, expr):
        text = self.evaluate(expr)
        if isinstance(text, (str, unicode, Message)):
            return text
        if text is not None and text is not Default:
            text = str(text)
        return text

    def evaluateStructure(self, expr):
        # TODO Should return None or a DOM tree
        return self.evaluate(expr)

    # implementation; can be overridden
    def evaluateSequence(self, expr):
        # TODO: Should return a sequence
        return self.evaluate(expr)

    def evaluateMacro(self, macroName):
        assert (macroName.startswith("$") and macroName.endswith("$"),
            macroName)
        macroName = macroName[1:-1]
        file, localName = self.findMacroFile(macroName)
        if not file:
            # Local macro
            macro = self.macros[localName]
        else:
            # External macro
            import driver
            program, macros = driver.compilefile(file)
            macro = macros.get(localName)
            if not macro:
                raise TALExpressionError("macro %s not found in file %s" %
                                         (localName, file))
        return macro

    # internal
    def findMacroFile(self, macroName):
        if not macroName:
            raise TALExpressionError("empty macro name")
        i = macroName.rfind('/')
        if i < 0:
            # No slash -- must be a locally defined macro
            return None, macroName
        else:
            # Up to last slash is the filename
            fileName = macroName[:i]
            localName = macroName[i+1:]
            return fileName, localName

    def setRepeat(self, name, expr):
        seq = self.evaluateSequence(expr)
        return Iterator(name, seq, self)

    def createErrorInfo(self, err, position):
        return ErrorInfo(err, position)

    def getDefault(self):
        return Default

    def translate(self, msgid, domain=None, mapping=None, default=None):
        self.translationDomain.domain = domain
        return self.translationDomain.translate(
            msgid, mapping, default=default)

    def evaluateCode(self, lang, code):
        # We probably implement too much, but I use the dummy engine to test
        # some of the issues that we will have.

        # For testing purposes only
        locals = {}
        globals = {}
        if self.useEngineAttrDicts:
            globals = self.globals.copy()
            locals = self.locals.copy()

        assert lang == 'text/server-python'
        import sys, StringIO

        # Removing probable comments
        if code.strip().startswith('<!--') and code.strip().endswith('-->'):
            code = code.strip()[4:-3]

        # Prepare code.
        lines = code.split('\n')
        lines = filter(lambda l: l.strip() != '', lines)
        code = '\n'.join(lines)
        # This saves us from all indentation issues :)
        if code.startswith(' ') or code.startswith('\t'):
            code = 'if 1 == 1:\n' + code + '\n'
        tmp = sys.stdout
        sys.stdout = StringIO.StringIO()
        try:
            exec code in globals, locals
        finally:
            result = sys.stdout
            sys.stdout = tmp

        # For testing purposes only
        self.codeLocals = locals
        self.codeGlobals = globals

        self.locals.update(locals)
        self.globals.update(globals)

        return result.getvalue()

class Iterator(object):

    def __init__(self, name, seq, engine):
        self.name = name
        self.seq = seq
        self.engine = engine
        self.nextIndex = 0

    def next(self):
        i = self.nextIndex
        try:
            item = self.seq[i]
        except IndexError:
            return 0
        self.nextIndex = i+1
        self.engine.setLocal(self.name, item)
        return 1


class DummyTranslationDomain(object):
    implements(ITranslationDomain)

    domain = ''

    msgids = {} 

    def appendMsgid(self, domain, data):
        if not self.msgids.has_key(domain):
            self.msgids[domain] = []
        self.msgids[domain].append(data)    
    
    def getMsgids(self, domain):
        return self.msgids[domain]

    def clearMsgids(self):
        self.msgids = {}

    def translate(self, msgid, mapping=None, context=None,
                  target_language=None, default=None):

        domain = self.domain
        # This is a fake translation service which simply uppercases non
        # ${name} placeholder text in the message id.
        #
        # First, transform a string with ${name} placeholders into a list of
        # substrings.  Then upcase everything but the placeholders, then glue
        # things back together.

        # If the domain is a string method, then transform the string
        # by calling that method.

        # MessageID attributes override arguments
        if isinstance(msgid, Message):
            domain = msgid.domain
            mapping = msgid.mapping
            default = msgid.default
            if default is None: # Message doesn't substitute itself for
                default = msgid # missing default

        # simulate an unknown msgid by returning None
        if msgid == "don't translate me":
            text = default
        elif domain and hasattr('', domain):
            text = getattr(msgid, domain)()
        else:
            domain = 'default'
            text = msgid.upper()

        self.appendMsgid(domain, (msgid, mapping))
        
        def repl(m):
            return unicode(mapping[m.group(m.lastindex).lower()])
        cre = re.compile(r'\$(?:([_A-Za-z][-\w]*)|\{([_A-Za-z][-\w]*)\})')
        return cre.sub(repl, text)

class MultipleDomainsDummyEngine(DummyEngine):
    
    def translate(self, msgid, domain=None, mapping=None, default=None):
        
        if isinstance(msgid, Message):
            domain = msgid.domain
        
        if domain == 'a_very_explicit_domain_setup_by_template_developer_that_wont_be_taken_into_account_by_the_ZPT_engine':
            domain = 'lower'
        
        self.translationDomain.domain = domain
        return self.translationDomain.translate(
            msgid, mapping, default=default)

