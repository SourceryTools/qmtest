#! /usr/bin/env python

# TODO:
#
# Labelling sections, etc. should fall to this module.  It then can pass
# the appropriate label to the generated file.  (Right?  But the LaTex
# filter could do its own labelling...)
#
# Right now, the "style" attribute gives the name of a styles file
# (sans a suffix like .css or .tex).  We need to somehow have defaults
# and overrides.
#

import xmllib
import urllib, urlparse
import re
import string
import exceptions

RuntimeError = exceptions.RuntimeError

def _TrueFalse(v=None, defv=1):
    if v is None:
        return defv
    v = string.lower(v)
    if v in ('yes','y','ok','true','t','1'):
        return 1
    elif v in ('no','n','false','f','0'):
        return 0
    else:
        return defv

class DocParse(xmllib.XMLParser):

    _RE_ABBREV = re.compile(r"^\s*(\w+)\s*=")
    _RE_ABVAR = re.compile(r"{:(\w+):}")

    def __init__(self, fmt, fileName=None, parent=None, target=None):
        xmllib.XMLParser.__init__(self)
        self._fmt = fmt
        self._state = [0]
        self._title = ''
        self._fileName = fileName
        self._parent = parent
        self._target = target
        self._abbrevs = {}
        if target is None:
            self._exec = 1
        else:
            self._exec = 0
        self._first_check = {
            'h1': {},
            'h2': {},
            'h3': {},
            'h4': {},
            'h5': {},
            'h6': {},
            'p': {} }
        self._first_check_active = []

        # SapCat specials
        self._UseCase_cnt = 0

    def _ExpandAbbrevs(self, text, recurse={}):
        m = self._RE_ABVAR.search(text)
        if m is None:
            return text
        k = m.group(1)
        if recurse.has_key(k):
            self.syntax_error('recursive expansion of abbreviation {:'+k+':}')
            return text[:m.start()] + self._ExpandAbbrevs(text[m.end():],
                                                          recurse)
        try:
            v = self._abbrevs[k]
        except KeyError:
            self.syntax_error('unknown abbreviation {:'+k+':}')
            return text[:m.start()] + self._ExpandAbbrevs(text[m.end():],
                                                          recurse)
        # Cannot have anything needing expansion here.
        pre = text[:m.start()]
        # Add the key to the dictionary; remove after expansion.  We
        # need to check for recursive expansions.
        recurse[k] = None
        s = self._ExpandAbbrevs(v, recurse)
        del recurse[k]
        # Possibly follow-on expansions.
        post = self._ExpandAbbrevs(text[m.end():], recurse)
        return pre + s + post

    def _AbbrevFile(self, url):
        "Read abbreviations from an abbrev file."
        f = urllib.urlopen(url)
        data = f.read()
        f.close()
        state = 0
        lineno = 1
        ws = string.whitespace
        vStart = string.letters + '_'
        vChar = vStart + string.digits
        for c in data:
            if state == 0:
                # Ignore whitespace.
                if c in ws:
                    pass
                elif c == '#':
                    state = 1
                elif c in vStart:
                    vName = c
                    val = ''
                    state = 2
                else:
                    m = 'abbrev file "' + url + '", line ' + str(lineno)
                    m = m + ': illegal abbreviation starting character'
                    self.syntax_error(m)
                    state = 1
            elif state == 1:
                # Ignore to end of line, then start an abbrev line.
                if c == '\n':
                    state = 0
            elif state == 2:
                # Build up a variable name.
                if c in vChar:
                    vName = vName + c
                elif c in ws:
                    state = 3
                elif c == '=':
                    state = 4
                else:
                    m = 'abbrev file "' + url + '", line ' + str(lineno)
                    m = m + ': illegal character in abbreviation name'
                    self.syntax_error(m)
                    state = 1
            elif state == 3:
                # Skip whitespace until '='
                if c == '=':
                    state = 4
                elif c in ws:
                    pass
                else:
                    m = 'abbrev file "' + url + '", line ' + str(lineno)
                    m = m + ': abbreviation definition missing ='
                    self.syntax_error(m)
                    state = 1
            elif state == 4:
                # Skip whitespace until quote.
                if c == '\n':
                    self._abbrevs[vName] = val
                    state = 0
                elif c in ws:
                    pass
                elif c == '"':
                    q = '"'
                    state = 5
                elif c == "'":
                    q = "'"
                    state = 5
                else:
                    m = 'abbrev file "' + url + '", line ' + str(lineno)
                    m = m + ': expansion must be quoted'
                    self.syntax_error(m)
                    state = 1
            elif state == 5:
                if c == q:
                    state = 4
                else:
                    val = val + c
            if c == '\n':
                lineno = lineno + 1
        if state == 2 or state == 3:
            m = 'abbrev file "' + url + '", line ' + str(lineno)
            m = m + ': missing abbreviation value (EOF)'
            self.syntax_error(m)
        elif state == 4:
            self._abbrevs[vName] = val
        elif state == 5:
            m = 'abbrev file "' + url + '", line ' + str(lineno)
            m = m + ': unclosed quoted expansion' 
            self.syntax_error(m)


    def handle_data(self, data):
        if self._exec > 0:
            s = self._state[-1]
            if s == 0:
                self._fmt.handle_text(data)
            elif s == 1:
                self._title = self._title + data

    def feed(self, data):
        lines = string.split(data, '\n')
        for L in lines:
            # Can handle abbrevs...
            L = self._ExpandAbbrevs(L)
            xmllib.XMLParser.feed(self, L+'\n')

    def handle_proc(self, proc, data):
        "Handle a procedure."
        if proc == "abbrev":
            # Defining an abbreviation.
            # data has the form: abbrv=Expansion which may have spaces
            # Henceforth, :abbrv: will become the expansion.
            #
            # Probably need abbrev files!
            m = self._RE_ABBREV.match(data)
            if m is not None:
                a = m.group(1)
                v = data[len(m.group(0)):]
                self._abbrevs[a] = v

    def handle_starttag(self, tag, method, attribs):
        print "<<" + tag + ">>"
        if self._exec > 0 or tag in ("Doc", "subdoc"):
            return apply(method, (self, attribs))
    def handle_endtag(self, tag, method):
        print "<</" + tag + ">>"
        if self._exec > 0 or tag in ("Doc", "subdoc"):
            return apply(method, (self,))

    def unknown_starttag(self, tag, attribs):
        self.syntax_error('Unknown start tag: ' + tag)
    def unknown_endtag(self, tag):
        self.syntax_error('Unknown end tag: ' + tag)

    def syntax_error(self, msg):
        fn = self._fileName
        if fn is not None:
            msg = 'File ' + fn + ', ' + msg
        xmllib.XMLParser.syntax_error(self, msg)

    def start_Doc(self, attribs):
        try:
            abbrevList = attribs['abbrevs']
        except KeyError:
            pass
        else:
            url = urlparse.urljoin(self._fileName, abbrevList)
            self._AbbrevFile(url)
        if self._parent is None:
            self._fmt.start_Doc(attribs)
    def end_Doc(self):
        if self._parent is None:
            self._fmt.end_Doc(self._title)

    def start_a(self, attribs):
        "Refer to a hyperlink."
        # First see if we are nested in an active link.  If
        # so, then this is not active.  It will not qualify
        # as a "first" link.
        fca = self._first_check_active
        for a in fca:
            if a:
                fca.append(0)
                return
        # Get the hyperreference.  If the "first" attribute is
        # set, it may or may not deactivate this link.
        try:
            lnk = attribs['href']
            try:
                fc = attribs['first']
                del attribs['first']
            except KeyError:
                active = 1
            else:
                try:
                    d = self._first_check[fc]
                except KeyError:
                    self.syntax_error('first attribute not one in: ' +
                                      str(self._first_check.keys()))
                    active = 1
                else:
                    if d.has_key(lnk):
                        active = 2
                    else:
                        active = 1
                        d[lnk] = None
        except KeyError:
            active = 0
        fca.append(active)
        if active:
            # Not called when active==0
            # First (or always visible): active==1
            # Not first: active==2
            self._fmt.start_a(attribs, active)
    def end_a(self):
        active = self._first_check_active[-1]
        del self._first_check_active[-1]
        if active:
            self._fmt.end_a()

    def start_abstract(self, attribs):
        self._fmt.start_abstract(attribs)
    def end_abstract(self):
        self._fmt.end_abstract()

    def start_address(self, attribs):
        self._fmt.start_address(attribs)
    def end_address(self):
        self._fmt.end_address()

    def start_appendix(self, attribs):
        self._first_check['h2'] = {}
        self._first_check['h3'] = {}
        self._first_check['h4'] = {}
        self._first_check['h5'] = {}
        self._first_check['h6'] = {}
        try:
            key = attribs['key']
            del attribs['key']
        except KeyError:
            key = None
        self._fmt.start_appendix(attribs, key)
    def end_appendix(self):
        self._fmt.end_appendix()

    def start_author(self, attribs):
        self._fmt.start_author(attribs)
    def end_author(self):
        self._fmt.end_author()

    def start_blockquote(self, attribs):
        try:
            cite = attribs['cite']
        except KeyError:
            cite = None
        self._fmt.start_blockquote(attribs, cite)
    def end_blockquote(self):
        self._fmt.end_blockquote()

    def start_br(self, attribs):
        self._fmt.start_br(attribs)
    def end_br(self):
        pass

    def start_cite(self, attribs):
        self._fmt.start_cite(attribs)
    def end_cite(self):
        self._fmt.end_cite()

    def start_code(self, attribs):
        self._fmt.start_code(attribs)
    def end_code(self):
        self._fmt.end_code()

    def start_contents(self, attribs):
        self._fmt.start_contents(attribs)
    def end_contents(self):
        pass

    def start_dd(self, attribs):
        self._fmt.start_dd(attribs)
    def end_dd(self):
        self._fmt.end_dd()

    def start_dfn(self, attribs):
        try:
            key = attribs['key']
            # Turn off "firstness"...
            for v in self._first_check.values():
                v[key] = None
        except KeyError:
            key = None
        self._fmt.start_dfn(attribs, key)
    def end_dfn(self):
        self._fmt.end_dfn()

    def start_dfnref(self, attribs):
        "Refer to a definition."
        fca = self._first_check_active
        active = 1
        for a in fca:
            if a:
                active = 0
        if active:
            try:
                key = attribs['key']
            except KeyError:
                self.syntax_error('missing required attribute "key"')
                key = None
            try:
                fc = attribs['first']
            except KeyError:
                active = 1
            else:
                try:
                    d = self._first_check[fc]
                except KeyError:
                    self.syntax_error('first attribute not one in: ' +
                                      str(self._first_check.keys()))
                    active = 1
                else:
                    if d.has_key(key):
                        active = 2
                    else:
                        active = 1
                        d[key] = None
        #
        # No key: active==0
        # First (always): active==1
        # Later: active==2
        self._fmt.start_dfnref(attribs, key, active)
        fca.append(active)
    def end_dfnref(self):
        active = self._first_check_active[-1]
        del self._first_check_active[-1]
        self._fmt.end_dfnref(active)

    def start_dl(self, attribs):
        self._fmt.start_dl(attribs)
    def end_dl(self):
        self._fmt.end_dl()

    def start_dt(self, attribs):
        self._fmt.start_dt(attribs)
    def end_dt(self):
        self._fmt.end_dt()

    def start_em(self, attribs):
        self._fmt.start_em(attribs)
    def end_em(self):
        self._fmt.end_em()

    def start_footnote(self, attribs):
        self._fmt.start_footnote(attribs)
    def end_footnote(self):
        self._fmt.end_footnote()

    def start_footnotes(self, attribs):
        self._fmt.start_footnotes(attribs)
    def end_footnotes(self):
        self._fmt.end_footnotes()

    def start_h1(self, attribs):
        self._first_check['h1'] = {}
        self._first_check['h2'] = {}
        self._first_check['h3'] = {}
        self._first_check['h4'] = {}
        self._first_check['h5'] = {}
        self._first_check['h6'] = {}
        self._start_header(1, attribs)
    def end_h1(self):
        self._fmt.end_header(1)

    def start_h2(self, attribs):
        self._first_check['h2'] = {}
        self._first_check['h3'] = {}
        self._first_check['h4'] = {}
        self._first_check['h5'] = {}
        self._first_check['h6'] = {}
        self._start_header(2, attribs)
    def end_h2(self):
        self._fmt.end_header(2)

    def start_h3(self, attribs):
        self._first_check['h3'] = {}
        self._first_check['h4'] = {}
        self._first_check['h5'] = {}
        self._first_check['h6'] = {}
        self._start_header(3, attribs)
    def end_h3(self):
        self._fmt.end_header(3)

    def start_h4(self, attribs):
        self._first_check['h4'] = {}
        self._first_check['h5'] = {}
        self._first_check['h6'] = {}
        self._start_header(4, attribs)
    def end_h4(self):
        self._fmt.end_header(4)

    def start_h5(self, attribs):
        self._first_check['h5'] = {}
        self._first_check['h6'] = {}
        self._start_header(5, attribs)
    def end_h5(self):
        self._fmt.end_header(5)

    def start_h6(self, attribs):
        self._first_check['h6'] = {}
        self._start_header(6, attribs)
    def end_h6(self):
        self._fmt.end_header(6)

    def _start_header(self, level, attribs):
        try:
            key = attribs['key']
            del attribs['key']
        except KeyError:
            key = None
        self._fmt.start_header(level, attribs, key)

    def start_hr(self, attribs):
        self._fmt.start_hr(attribs)
    def end_hr(self):
        pass

    def start_figure(self, attribs):
        "Insert an image."
        try:
            src = attribs['img']
            del attribs['img']
        except KeyError:
            self.syntax_error('missing required "img" attribute')
            return
        # %%% Eventually, determine the image size, etc....
        try:
            caption = attribs['caption']
            del attribs['caption']
        except KeyError:
            caption = None
        try:
            alt = attribs['alt']
            del attribs['alt']
        except KeyError:
            alt = caption
        try:
            key = attribs['key']
            del attribs['key']
        except KeyError:
            key = None
        self._fmt.start_figure(attribs, src, caption, alt, key)
    def end_figure(self):
        self._fmt.end_figure()

    def start_include(self, attribs):
        try:
            target = attribs['target']
        except KeyError:
            target = None
        try:
            fName = attribs['file']
        except KeyError:
            try:
                fName = attribs['url']
            except KeyError:
                # Nothing to include
                return
            else:
                # A url...
                fName = urlparse.urljoin(self._fileName, fName)
        else:
            # A file
            fName = urlparse.urljoin(self._fileName, 'file:' + fName)
        f = urllib.urlopen(fName)
        data = f.read()
        f.close()
        xp = DocParse(self._fmt, fName, self, target)
        xp.feed(data)
        xp.close()
    def end_include(self):
        pass

    def start_li(self, attribs):
        self._fmt.start_li(attribs)
    def end_li(self):
        self._fmt.end_li()

    def start_ol(self, attribs):
        self._fmt.start_ol(attribs)
    def end_ol(self):
        self._fmt.end_ol()

    def start_p(self, attribs):
        self._first_check['p'] = {}
        self._fmt.start_p(attribs)
    def end_p(self):
        self._fmt.end_p()

    def start_q(self, attribs):
        self._fmt.start_q(attribs)
    def end_q(self):
        self._fmt.end_q()

    def start_ref(self, attribs):
        try:
            key = attribs['key']
            del attribs['key']
        except KeyError:
            self.syntax_error('missing required "key" attribute')
            key = None
        self._fmt.start_ref(attribs, key)
    def end_ref(self):
        self._fmt.end_ref()

    def start_strong(self, attribs):
        self._fmt.start_strong(attribs)
    def end_strong(self):
        self._fmt.end_strong()

    def start_subdoc(self, attribs):
        if self._target is None:
            pass
        elif attribs['name'] == self._target or self._exec > 0:
            self._exec = self._exec + 1
    def end_subdoc(self):
        if self._target is None:
            pass
        elif self._exec > 0:
            self._exec = self._exec - 1

    def start_title(self, attribs):
        self._title = ''
        self._state.append( 1 )
    def end_title(self):
        del self._state[-1]

    def start_ul(self, attribs):
        self._fmt.start_ul(attribs)
    def end_ul(self):
        self._fmt.end_ul()

    def start_var(self, attribs):
        self._fmt.start_var(attribs)
    def end_var(self):
        self._fmt.end_var()

    # These implement things we need specific to the SapCat proposal.
    # They should somehow be abstracted to a separate class.

    def start_EnvVar(self, attribs):
        self._fmt.start_EnvVar(attribs)
    def end_EnvVar(self):
        self._fmt.end_EnvVar()

    def start_Sys(self, attribs):
        self._fmt.start_Sys(attribs)
    def end_Sys(self):
        self._fmt.end_Sys()

    def start_ManPage(self, attribs):
        command = attribs['command']
        description = attribs['description']
        self._fmt.start_ManPage(attribs, command, description)
    def end_ManPage(self):
        self._fmt.end_ManPage()

    def start_ManPage_Synopsis(self, attribs):
        self._fmt.start_ManPage_Synopsis(attribs)
    def end_ManPage_Synopsis(self):
        self._fmt.end_ManPage_Synopsis()

    def start_ManPage_Description(self, attribs):
        self._fmt.start_ManPage_Description(attribs)
    def end_ManPage_Description(self):
        self._fmt.end_ManPage_Description()

    def start_ManPage_Section(self, attribs):
        title = attribs['title']
        self._fmt.start_ManPage_Section(attribs, title)
    def end_ManPage_Section(self):
        self._fmt.end_ManPage_Section()

    def start_UseCase(self, attribs):
        ucc = self._UseCase_cnt = self._UseCase_cnt + 1
        try:
            name = attribs['name']
        except KeyError:
            self.syntax_error('Missing required "name"')
            name = 'Use Case #' + str(ucc)
        try:
            ident = attribs['ident']
        except KeyError:
            #self.syntax_error('Missing required "ident"')
            ident = 'UC'+str(ucc)
        try:
            key = attribs['key']
        except KeyError:
            key = ident
        self._fmt.start_UseCase(attribs, name, ident, key)
    def end_UseCase(self):
        self._fmt.end_UseCase()

    def start_UseCase_Description(self, attribs):
        self._fmt.start_UseCase_Section(attribs, 'Description')
    def end_UseCase_Description(self):
        self._fmt.end_UseCase_Section()

    def start_UseCase_Discussion(self, attribs):
        self._fmt.start_UseCase_Section(attribs, 'Discussion')
    def end_UseCase_Discussion(self):
        self._fmt.end_UseCase_Section()

    def start_UseCase_Priority(self, attribs):
        self._fmt.start_UseCase_Section(attribs, 'Priority')
    def end_UseCase_Priority(self):
        self._fmt.end_UseCase_Section()

    def start_UseCase_Section(self, attribs):
        sectionName = attribs['name']
        self._fmt.start_UseCase_Section(attribs, sectionName)
    def end_UseCase_Section(self):
        self._fmt.end_UseCase_Section()

    def start_UseCase_Sequence(self, attribs):
        self._fmt.start_UseCase_Section(attribs, 'Sequence')
    def end_UseCase_Sequence(self):
        self._fmt.end_UseCase_Section()

    def start_UseCase_Ref(self, attribs):
        key = attribs['key']
        self._fmt.start_UseCase_Ref(attribs, key)
    def end_UseCase_Ref(self):
        self._fmt.end_UseCase_Ref()

    
DocParse.elements = {
    'Doc': ( DocParse.start_Doc, DocParse.end_Doc ),
    'a': ( DocParse.start_a, DocParse.end_a ),
    'abstract': ( DocParse.start_abstract, DocParse.end_abstract ),
    'address': ( DocParse.start_address, DocParse.end_address ),
    'appendix': ( DocParse.start_appendix, DocParse.end_appendix ),
    'author': ( DocParse.start_author, DocParse.end_author ),
    'blockquote': ( DocParse.start_blockquote, DocParse.end_blockquote ),
    'br': ( DocParse.start_br, DocParse.end_br ),
    'cite': ( DocParse.start_cite, DocParse.end_cite ),
    'code': ( DocParse.start_code, DocParse.end_code ),
    'contents': ( DocParse.start_contents, DocParse.end_contents ),
    'dd': ( DocParse.start_dd, DocParse.end_dd ),
    'dfn': ( DocParse.start_dfn, DocParse.end_dfn ),
    'dfnref': ( DocParse.start_dfnref, DocParse.end_dfnref ),
    'dl': ( DocParse.start_dl, DocParse.end_dl ),
    'dt': ( DocParse.start_dt, DocParse.end_dt ),
    'em': ( DocParse.start_em, DocParse.end_em ),
    'figure': ( DocParse.start_figure, DocParse.end_figure ),
    'footnote': ( DocParse.start_footnote, DocParse.end_footnote ),
    'footnotes': ( DocParse.start_footnotes, DocParse.end_footnotes ),
    'h1': ( DocParse.start_h1, DocParse.end_h1 ),
    'h2': ( DocParse.start_h2, DocParse.end_h2 ),
    'h3': ( DocParse.start_h3, DocParse.end_h3 ),
    'h4': ( DocParse.start_h4, DocParse.end_h4 ),
    'h5': ( DocParse.start_h5, DocParse.end_h5 ),
    'h6': ( DocParse.start_h6, DocParse.end_h6 ),
    'hr': ( DocParse.start_hr, DocParse.end_hr ),
    'include': ( DocParse.start_include, DocParse.end_include ),
    'li': ( DocParse.start_li, DocParse.end_li ),
    'ol': ( DocParse.start_ol, DocParse.end_ol ),
    'p': ( DocParse.start_p, DocParse.end_p ),
    'q': ( DocParse.start_q, DocParse.end_q ),
    'ref': ( DocParse.start_ref, DocParse.end_ref ),
    'strong': ( DocParse.start_strong, DocParse.end_strong ),
    'subdoc': ( DocParse.start_subdoc, DocParse.end_subdoc ),
    'title': ( DocParse.start_title, DocParse.end_title ),
    'ul': ( DocParse.start_ul, DocParse.end_ul ),
    'var': ( DocParse.start_var, DocParse.end_var ),

    # Specific to SapCat
    'EnvVar': ( DocParse.start_EnvVar, DocParse.end_EnvVar ),
    'Sys': ( DocParse.start_Sys, DocParse.end_Sys ),
    'ManPage': ( DocParse.start_ManPage, DocParse.end_ManPage ),
    'ManPage-Synopsis': ( DocParse.start_ManPage_Synopsis,
                          DocParse.end_ManPage_Synopsis ),
    'ManPage-Description': ( DocParse.start_ManPage_Description,
                             DocParse.end_ManPage_Description ),
    'ManPage-Section': ( DocParse.start_ManPage_Section,
                         DocParse.end_ManPage_Section ),
    'UseCase': ( DocParse.start_UseCase, DocParse.end_UseCase ),
    'UseCase-Description': ( DocParse.start_UseCase_Description,
                             DocParse.end_UseCase_Description ),
    'UseCase-Discussion': ( DocParse.start_UseCase_Discussion,
                            DocParse.end_UseCase_Discussion ),
    'UseCase-Priority': ( DocParse.start_UseCase_Priority,
                          DocParse.end_UseCase_Priority ),
    'UseCase-Section': ( DocParse.start_UseCase_Section,
                         DocParse.end_UseCase_Section ),
    'UseCase-Sequence': ( DocParse.start_UseCase_Sequence,
                          DocParse.end_UseCase_Sequence ),
    'UseCase-Ref': ( DocParse.start_UseCase_Ref,
                     DocParse.end_UseCase_Ref )
    }

DocParse.attributes = {
    'Doc': { 'abbrevs': None,
             'style': None },
    'a': { 'href': None,
           'name': None,
           'first': None,
           },
    'abstract': None,
    'address': None,
    'appendix': { 'key': None,
                  'labelled': 'yes' },
    'author': None,
    'blockquote': { 'cite': None },
    'br': None,
    'cite': None,
    'code': None,
    'contents': None,
    'dd': None,
    'dfn': { 'key': None },
    'dfnref': { 'key': None,
                'first': None },
    'dl': None,
    'dt': None,
    'em': None,
    'figure': { 'alt': None,
             'caption': None,
             'key': None,
             'img': None },
    'footnote': None,
    'footnotes': None,
    'h1': None,
    'h2': { 'key': None,
            'labelled': 'yes' },
    'h3': { 'key': None,
            'labelled': 'yes' },
    'h4': { 'key': None,
            'labelled': 'yes' },
    'h5': { 'key': None,
            'labelled': 'yes' },
    'h6': { 'key': None,
            'labelled': 'no' },
    'hr': None,
    'include': { 'file': None,
                 'url': None,
                 'target': None },
    'li': None,
    'ol': None,
    'p': None,
    'q': None,
    'ref': { 'key': None },
    'strong': None,
    'subdoc': { 'name': None },
    'title': None,
    'ul': None,
    'var': None,

    # Specific to SapCat
    'EnvVar': None,
    'Sys': { 'abbrev': None,
             'acronym': None
             },
    'ManPage': { 'command': None,
                 'description': None
                 },
    'ManPage-Synopsis': None,
    'ManPage-Description': None,
    'ManPage-Section': { 'title': None },
    'UseCase': { 'name': None,
                 'ident': None,
                 'key': None
                 },
    'UseCase-Description': None,
    'UseCase-Discussion': None,
    'UseCase-Priority': None,
    'UseCase-Section': { 'name': None },
    'UseCase-Sequence': None,
    'UseCase-Ref': { 'key': None }
    }


DocParse.entitydefs = {
    'lt': '&#60;',	# < (must use charref)
    'gt': '&#62;',      # >
    'amp': '&#38;',     # & (must use charref)
    'quot': '&#34;',    # "
    'apos': '&#39;',    # '
    'nbsp': '&#160;',   # non-breaking space
    'ndash': '&#8211;',  # --
    'mdash': '&#8212;'  # ---
    }
# Need to replace these (until we have Unicode?)
DocParse.entitydefs['ndash'] = chr(253)
DocParse.entitydefs['mdash'] = chr(254)
