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
"""

$Id: dt_string.py 38178 2005-08-30 21:50:19Z mj $
"""
import re, thread

from zope.documenttemplate.dt_util import ParseError, render_blocks
from zope.documenttemplate.dt_var import Var, Call, Comment
from zope.documenttemplate.dt_return import ReturnTag, DTReturn

from types import TupleType

_marker = []  # Create a new marker object.

class String:
    """Document templates defined from strings.

    Document template strings use an extended form of python string
    formatting.  To insert a named value, simply include text of the
    form: '%(name)x', where 'name' is the name of the value and 'x' is
    a format specification, such as '12.2d'.

    To intrduce a block such as an 'if' or an 'in' or a block continuation,
    such as an 'else', use '[' as the format specification.  To
    terminate a block, ise ']' as the format specification, as in::

      %(in results)[
        %(name)s
      %(in results)]

    """

    from zope.documenttemplate.dt_util import TemplateDict

    # Document Templates masquerade as functions:
    class func_code:
        pass
    func_code = func_code()
    func_code.co_varnames = 'self', 'REQUEST'
    func_code.co_argcount = 2
    func_defaults = ()

    def errQuote(self, s):
        return s

    def parse_error(self, mess, tag, text, start):
        raise ParseError("%s, for tag %s, on line %s of %s<p>" % (
            mess, self.errQuote(tag), len(text[:start].split('\n')),
            self.errQuote(self.__name__)))

    commands={
        'var': Var,
        'call': Call,
        'in': ('in', 'dt_in','In'),
        'with': ('with', 'dt_with','With'),
        'if': ('if', 'dt_if','If'),
        'unless': ('unless', 'dt_if','Unless'),
        'else': ('else', 'dt_if','Else'),
        'comment': Comment,
        'raise': ('raise', 'dt_raise','Raise'),
        'try': ('try', 'dt_try','Try'),
        'let': ('let', 'dt_let', 'Let'),
        'return': ReturnTag,
        }

    def SubTemplate(self, name):
        return String('', __name__=name)


    def tagre(self):
        return re.compile(
            '%\\('                                    # beginning
            '(?P<name>[a-zA-Z0-9_/.-]+)'              # tag name
            '('
            '[\000- ]+'                               # space after tag name
            '(?P<args>([^\\)"]+("[^"]*")?)*)'         # arguments
            ')?'
            '\\)(?P<fmt>[0-9]*[.]?[0-9]*[a-z]|[]![])' # end
            , re.I)


    def _parseTag(self, match_ob, command=None, sargs='', tt=TupleType):
        tag, args, command, coname = self.parseTag(match_ob, command, sargs)
        if isinstance(command, tt):
            cname, module, name = command
            d={}
            try:
                exec 'from %s import %s' % (module, name) in d
            except ImportError:
                exec 'from zope.documenttemplate.%s import %s' % (module,
                                                                  name) in d
            command = d[name]
            self.commands[cname] = command
        return tag, args, command, coname


    def parseTag(self, match_ob, command=None, sargs=''):
        """Parse a tag using an already matched re

        Return: tag, args, command, coname

        where: tag is the tag,
               args is the tag\'s argument string,
               command is a corresponding command info structure if the
                  tag is a start tag, or None otherwise, and
               coname is the name of a continue tag (e.g. else)
                 or None otherwise
        """
        tag, name, args, fmt = match_ob.group(0, 'name', 'args', 'fmt')
        args = args and args.strip() or ''

        if fmt == ']':
            if not command or name != command.name:
                raise ParseError('unexpected end tag', tag)
            return tag, args, None, None
        elif fmt == '[' or fmt == '!':
            if command and name in command.blockContinuations:

                if name=='else' and args:
                    # Waaaaaah! Have to special case else because of
                    # old else start tag usage. Waaaaaaah!
                    l = len(args)
                    if not (args == sargs or
                            args == sargs[:l] and sargs[l:l+1] in ' \t\n'):
                        return tag, args, self.commands[name], None

                return tag, args, None, name

            try:
                return tag, args, self.commands[name], None
            except KeyError:
                raise ParseError('Unexpected tag', tag)
        else:
            # Var command
            args = args and ("%s %s" % (name, args)) or name
            return tag, args, Var, None


    def varExtra(self, match_ob):
        return match_ob.group('fmt')


    def parse(self, text, start=0, result=None, tagre=None):
        if result is None:
            result = []
        if tagre is None:
            tagre = self.tagre()
        mo = tagre.search(text, start)
        while mo:
            l = mo.start(0)

            try:
                tag, args, command, coname = self._parseTag(mo)
            except ParseError, m:
                self.parse_error(m[0], m[1], text, l)

            s = text[start:l]
            if s:
                result.append(s)
            start = l + len(tag)

            if hasattr(command,'blockContinuations'):
                start = self.parse_block(text, start, result, tagre,
                                         tag, l, args, command)
            else:
                try:
                    if command is Var:
                        r = command(self, args, self.varExtra(mo))
                    else:
                        r = command(self, args)
                    if hasattr(r,'simple_form'):
                        r = r.simple_form
                    result.append(r)
                except ParseError, m:
                    self.parse_error(m[0], tag, text, l)

            mo = tagre.search(text, start)

        text = text[start:]
        if text:
            result.append(text)
        return result


    def skip_eol(self, text, start, eol=re.compile('[ \t]*\n')):
        # if block open is followed by newline, then skip past newline
        mo = eol.match(text, start)
        if mo is not None:
            start = start + mo.end(0) - mo.start(0)

        return start


    def parse_block(self, text, start, result, tagre,
                    stag, sloc, sargs, scommand):

        start = self.skip_eol(text, start)

        blocks = []
        tname = scommand.name
        sname = stag
        sstart = start
        sa = sargs
        while True:

            mo = tagre.search(text, start)
            if mo is None:
                self.parse_error('No closing tag', stag, text, sloc)
            l = mo.start(0)

            try:
                tag, args, command, coname= self._parseTag(mo, scommand, sa)
            except ParseError, m:
                self.parse_error(m[0], m[1], text, l)

            if command:
                start = l + len(tag)
                if hasattr(command, 'blockContinuations'):
                    # New open tag.  Need to find closing tag.
                    start=self.parse_close(text, start, tagre, tag, l,
                                           command, args)
            else:
                # Either a continuation tag or an end tag
                section = self.SubTemplate(sname)
                section._v_blocks = section.blocks = \
                                    self.parse(text[:l],sstart)
                section._v_cooked = None
                blocks.append((tname, sargs, section))

                start = self.skip_eol(text, l+len(tag))

                if coname:
                    tname = coname
                    sname = tag
                    sargs = args
                    sstart = start
                else:
                    try:
                        r = scommand(self, blocks)
                        if hasattr(r,'simple_form'):
                            r = r.simple_form
                        result.append(r)
                    except ParseError, m:
                        self.parse_error(m[0], stag, text, l)

                    return start


    def parse_close(self, text, start, tagre, stag, sloc, scommand, sa):
        while True:
            mo = tagre.search(text, start)
            if mo is None:
                self.parse_error('No closing tag', stag, text, sloc)
            l = mo.start(0)

            try:
                tag, args, command, coname= self._parseTag(mo, scommand, sa)
            except ParseError, m:
                self.parse_error(m[0], m[1], text, l)

            start = l + len(tag)
            if command:
                if hasattr(command, 'blockContinuations'):
                    # New open tag.  Need to find closing tag.
                    start = self.parse_close(text, start, tagre, tag, l,
                                             command, args)
            elif not coname:
                return start


    shared_globals={}


    def __init__(self, source_string='', mapping=None, __name__='<string>',
                 **vars):
        """\
        Create a document template from a string.

        The optional parameter, 'mapping', may be used to provide a
        mapping object containing defaults for values to be inserted.
        """
        self.raw = source_string
        self.initvars(mapping, vars)


    def default(self, name=None, **kw):
        """Change or query default values in a document template.

        If a name is specified, the value of the named default value
        before the operation is returned.

        Keyword arguments are used to provide default values.
        """
        if name:
            name = self.globals[name]
        for key in kw.keys():
            self.globals[key] = kw[key]
        return name


    def var(self,name=None,**kw):
        """Change or query a variable in a document template.

        If a name is specified, the value of the named variable before
        the operation is returned.

        Keyword arguments are used to provide variable values.
        """
        if name:
            name = self._vars[name]
        for key in kw.keys():
            self._vars[key] = kw[key]
        return name


    def munge(self, source_string=None, mapping=None, **vars):
        """Change the text or default values for a document template."""
        if mapping is not None or vars:
            self.initvars(mapping, vars)
        if source_string is not None:
            self.raw = source_string
        self.cook()


    def read_raw(self, raw=None):
        return self.raw


    def read(self, raw=None):
        return self.read_raw()


    def cook(self, cooklock=thread.allocate_lock()):
        cooklock.acquire()
        try:
            self._v_blocks = self.parse(self.read())
            self._v_cooked = None
        finally:
            cooklock.release()


    def initvars(self, globals, vars):
        if globals:
            for k in globals.keys():
                if k[:1] != '_' and not vars.has_key(k):
                    vars[k] = globals[k]
        self.globals = vars
        self._vars = {}


    def __render_with_namespace__(self, md):
        return self(None, md)

    def __call__(self,client=None,mapping={},**kw):
        '''\
        Generate a document from a document template.

        The document will be generated by inserting values into the
        format string specified when the document template was
        created.  Values are inserted using standard python named
        string formats.

        The optional argument 'client' is used to specify a object
        containing values to be looked up.  Values will be looked up
        using getattr, so inheritence of values is supported.  Note
        that names beginning with '_' will not be looked up from the
        client.

        The optional argument, 'mapping' is used to specify a mapping
        object containing values to be inserted.

        Values to be inserted may also be specified using keyword
        arguments.

        Values will be inserted from one of several sources.  The
        sources, in the order in which they are consulted, are:

          o  Keyword arguments,

          o  The 'client' argument,

          o  The 'mapping' argument,

          o  The keyword arguments provided when the object was
             created, and

          o  The 'mapping' argument provided when the template was
             created.

        '''
        # print '============================================================'
        # print '__called__'
        # print self.raw
        # print kw
        # print client
        # print mapping
        # print '============================================================'

        if mapping is None:
            mapping = {}

        if not hasattr(self,'_v_cooked'):
            try:
                changed = self.__changed__()
            except:
                changed = 1
            self.cook()
            if not changed:
                self.__changed__(0)

        pushed=None
        try:
            if isinstance(mapping, self.TemplateDict):
                pushed=0
        except:
            pass

        globals = self.globals
        if pushed is not None:
            # We were passed a TemplateDict, so we must be a sub-template
            md = mapping
            push = md._push
            if globals:
                push(self.globals)
                pushed = pushed+1
        else:
            md = self.TemplateDict()
            push = md._push
            shared_globals = self.shared_globals
            if shared_globals:
                push(shared_globals)
            if globals:
                push(globals)
            if mapping:
                push(mapping)
            md.validate = self.validate
            if client is not None:
                if isinstance(client, TupleType):
                    md.this = client[-1]
                else:
                    md.this = client
            pushed=0

        level = md.level
        if level > 200:
            raise SystemError('infinite recursion in document template')
        md.level = level+1

        if client is not None:
            if isinstance(client, TupleType):
                # if client is a tuple, it represents a "path" of clients
                # which should be pushed onto the md in order.
                for ob in client:
                    md._push_instance(ob)
                    pushed += 1
            else:
                # otherwise its just a normal client object.
                md._push_instance(client)
                pushed += 1

        if self._vars:
            push(self._vars)
            pushed += 1

        if kw:
            push(kw)
            pushed += 1

        try:
            try:
                result = render_blocks(self._v_blocks, md)
            except DTReturn, v:
                result = v.v
            return result
        finally:
            if pushed:
                md._pop(pushed) # Get rid of circular reference!
            md.level=level # Restore previous level


    validate=None

    def __str__(self):
        return self.read()


    def __getstate__(self, _special=('_v_', '_p_')):
        # Waaa, we need _v_ behavior but we may not subclass Persistent
        d={}
        for k, v in self.__dict__.items():
            if k[:3] in _special: continue
            d[k] = v
        return d

    def compile_python_expresssion(self, src):
        return compile(src, getattr(self, '__name__', '<string>'), 'eval')
    
