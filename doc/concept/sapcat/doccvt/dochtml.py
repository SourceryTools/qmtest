import docfmt
import string

# TODO:
#
# We really need to store a list of buffers containing headers.  When
# the document is closed, we check if there is a TOC.  If so, then
# they are modified to contain headers to the TOC.  This way, we can
# format a document whether or not there is a TOC.
#
# Similarly, the Footnotes header is treated like other headers in
# this treatment.
#
# Also, can we do something sensible about footnotes even if there
# is no footnote section?  We could create a separate "footnotes"
# file, or perhaps using JavaScript, we can make them visible...
# Using JavaScript might be good to do, always.
#
# Marginal notes?
#
# Right now, to add a new text type, do these things:
# 1 - Add information for start, end tags to main XML parser.
# 2 - Choose a good base representation (div, pre, etc.).  Create
#     a css class for this.
# 3 - Add start, end to this class, using the base representation
#     and class.
# It seems like we could do much of this using some sort of configuration
# file, since the steps seem pretty well-defined and simple.
#
# Right now, the "style" attribute gives the name of a styles file
# (sans a suffix like .css or .tex).  We need to somehow have defaults
# and overrides.

_EntityMap = {
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    '"': '&quot;'
    }
_SpecialMap = {
    }
_SpecialMap[chr(253)] = '&#8211;'  # &ndash;
_SpecialMap[chr(254)] = '&#8212;'  # &mdash;

def EntityString(s):
    res = ''
    e = _EntityMap
    for c in s:
        try:
            res = res + e[c]
        except KeyError:
            res = res + c
    return SpecialString(res)
def SpecialString(s):
    res = ''
    e = _SpecialMap
    for c in s:
        try:
            res = res + e[c]
        except KeyError:
            res = res + c
    return res


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

class DocHtml(docfmt.DocFormat):

    def __init__(self, f):
        docfmt.DocFormat.__init__(self, f)
        h = self._head = docfmt.StringIO()
        self.insert_buffer(h)
        self._tail = docfmt.StringIO()
        self._contents = docfmt.StringIO()
        self._footnotes = docfmt.StringIO()
        self._footcnt = 0
        self._TOCMinLevel = 2
        self._sections = [0,0,0,0,0]
        self._appendixcnt = 0
        self._TOCLastLev = 0
        self._labelHeaders = 1
        self._labelHeader = []
        self._hdr_mapTarg = {}
        self._hdr_mapName = {}
        self._hdr_Ref = {}
        self._figureCnt = 0
        self._figureRCnt = 0
        self._headerCnt = 0
        self._state = [ 0 ]
        self._quoteNest = 0
        self._dfnKey = []
        #
        # For SapCat
        self._UseCase_cnt = 0
        self._UseCase_mapTarg = {}
        self._UseCase_mapIdent = {}
        self._UseCase_mapName = {}
        self._UseCase_Ref = {}

    def close(self):
        self.finalize_tail()
        self.insert_buffer(self._tail)
        self.finalize_contents()
        self.finalize_ref()
        self.finalize_UseCase()
        docfmt.DocFormat.close(self)

    def start_Doc(self, attribs):
        h = self._head
        h.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n')
        h.write('            "http://www.w3.org/TR/html4/loose.dtd">\n')
        h.write('<html>\n')
        h.write('  <head>\n')
        h.write('  <meta http-equiv="Content-Style-Type" content="text/css">\n')
        try:
            sFile = attribs['style']
        except KeyError:
            pass
        else:
            if sFile is not None:
                f = open(sFile+'.css', 'r')
                h.write(f.read())
                f.close()
    def end_Doc(self, title):
        h = self._head
        if title == '':
            h.write('<title>Untitled</title>\n')
        else:
            h.write('<title>' + title + '</title>\n')
        h.write('  </head>\n\n')
        h.write('<body bgcolor="white">\n')
        h.write('  <div class="Doc">\n')

    def finalize_tail(self):
        self.write('</div></body></html>\n')

    def start_contents_entry(self, lev, tag=None):
        "Begin an entry in the table of contents; return the anchor tag."

        c = self._contents
        ll = self._TOCLastLev
        if ll == 0:
            # Need to initialize table of contents.
            c.write('<h2><a name="contents">Contents</a></h2>\n')
            c.write('<div class="contents">\n')
            ll = self._TOCLastLev = 1
        if ll == lev:
            c.write('</li>\n')
        while ll < lev:
            c.write('<ul>\n')
            ll = ll + 1
        while ll > lev:
            c.write('</ul>\n')
            ll = ll - 1
        self._TOCLastLev = ll
        if tag is None:
            hc = self._headerCnt = self._headerCnt + 1
            tag = 'header-' + str(hc)
        c.write('<li><a href="%s">' % ( EntityString('#' + str(tag)), ))
        self._state.append( 2 )
        return str(tag)

    def end_contents_entry(self):
        "End an entry in the table of contents."
        self._contents.write('</a>\n')
        del self._state[-1]

    def finalize_contents(self):
        "Close up the table of contents."
        ll = self._TOCLastLev
        if ll > 0:
            c = self._contents
            while ll >= self._TOCMinLevel:
                c.write('</ul>\n')
                ll = ll - 1
            c.write('</div>\n')

    def write_contents(self, text):
        self._contents.write(text)


    def handle_text(self, text):
        text = SpecialString(text)
        self._write_text(text)

    def _write_text(self, text):
        "Direct text to the correct locations."
        s = self._state[-1]
        if s == 0:
            # Main text
            self.write(text)
        elif s == 1:
            # Footnote text
            self._footnotes.write(text)
        elif s == 2:
            # Entry to go in Table of Contents.
            self.write_contents(text)
            self.write(text)

    def _write_text_nc(self, text):
        "Direct text to the correct locations, but not into the TOC."
        s = self._state[-1]
        if s == 0:
            # Main text
            self.write(text)
        elif s == 1:
            # Footnote text
            self._footnotes.write(text)
        elif s == 2:
            # Entry not to go in Table of Contents like it normally would.
            self.write(text)

    def start_a(self, attribs, active):
        w = self._write_text_nc
        w('<a')
        if active == 2 and self._state[-1] == 0:
            w(' class="NotFirst"')
        for (k,v) in attribs.items():
            w(' '+k+'="'+EntityString(v)+'"')
        w('>')
    def end_a(self):
        self._write_text_nc('</a>')

    def start_abstract(self, attribs):
        "Begin an abstract."
        w = self.write
        w('<h2>Abstract</h2>\n')
        w('<div class="Abstract" style="left-margin: 10%; right-margin: 10%;">\n')
    def end_abstract(self):
        "End an abstract."
        self.write('</div>\n')

    def start_address(self, attribs):
        self.write('<center><address>')
    def end_address(self):
        self.write('</address></center>')

    def start_appendix(self, attribs, key):
        "Start an appendix header."
        useLabel = _TrueFalse(attribs['labelled'], self._labelHeaders)
        self._labelHeader.append(useLabel)
        w = self.write
        if useLabel:
            acnt = self._appendixcnt
            self._appendixcnt = self._appendixcnt + 1
            alabel = ''
            while acnt >= 0:
                alabel = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[acnt % 26] + alabel
                acnt = (acnt / 26) - 1
            tag = 'app_' + alabel
        else:
            alabel = '?'
            tag = None
        tag = self.start_contents_entry(2, tag)
        w('<h2><a href="#contents" name="' + EntityString(tag) + '">')
        if useLabel:
            w(alabel + '</a>&nbsp;&nbsp;')
        if key is not None:
            self._hdr_mapTarg[key] = EntityString(tag)
            self._hdr_mapName[key] = alabel
    def end_appendix(self):
        useLabel = self._labelHeader[-1]
        del self._labelHeader[-1]
        self.end_contents_entry()
        if not useLabel:
            self.write('</a>')
        self.write('</h2>\n')
        

    def start_author(self, attribs):
        self.write('<address>')
    def end_author(self):
        self.write('</address>')

    def start_blockquote(self, attribs, cite):
        self._write_text('<blockquote')
        if cite is not None:
            self._write_text(' cite="' + EntityString(cite) + '"')
        self._write_text('>\n')
    def end_blockquote(self):
        self._write_text('</blockquote>\n')

    def start_br(self, attribs):
        self._write_text('<br>')
    def end_br(self):
        pass

    def start_cite(self, attribs):
        self._write_text('<cite>')
    def end_cite(self):
        self._write_text('</cite>')

    def start_code(self, attribs):
        self._write_text('<code>')
    def end_code(self):
        self._write_text('</code>')

    def start_contents(self, attribs):
        self.insert_buffer(self._contents)
    def end_contents(self):
        pass

    def start_dd(self, attribs):
        self._write_text('<dd>')
    def end_dd(self):
        self._write_text('</dd>')

    def start_dfn(self, attribs, key):
        w = self._write_text
        if key is not None:
            w('<a name="DFN-' + EntityString(key) + '">')
        self._dfnKey.append(key)
        self._write_text('<dfn class="Dfn"><span class="Dfn">')
    def end_dfn(self):
        w = self._write_text
        w('</span></dfn>')
        k = self._dfnKey[-1]
        del self._dfnKey[-1]
        if k is not None:
            w('</a>')

    def start_dfnref(self, attribs, key, active):
        w = self._write_text
        wnc = self._write_text_nc
        #wnc = self.write
        w('<span class="Dfnref">')
        if key is not None and active > 0:
            wnc('<a href="#DFN-' + EntityString(key) + '"')
            if active == 2 and self._state[-1] == 0:
                wnc(' class="DfnrefNotFirst"')
            else:
                wnc(' class="Dfnref"')
            wnc('>')
        self._dfnKey.append(key)
    def end_dfnref(self, active):
        w = self._write_text
        wnc = self._write_text_nc
        #wnc = self.write
        k = self._dfnKey[-1]
        del self._dfnKey[-1]
        if k is not None and active > 0:
            wnc('</a>')
        w('</span>')

    def start_dl(self, attribs):
        self._write_text('<dl>\n')
    def end_dl(self):
        self._write_text('</dl>\n')

    def start_dt(self, attribs):
        self._write_text('<dt>')
    def end_dt(self):
        self._write_text('</dt>')

    def start_em(self, attribs):
        self._write_text('<em>')
    def end_em(self):
        self._write_text('</em>')

    def start_figure(self, attribs, src, caption, alt, key):
        w = self.write
        w('<div class="Figure">\n')
        w('<center>\n')
        w('<div class="FigureImage">\n')
        rCnt = self._figureRCnt = self._figureRCnt + 1
        if caption is not None:
            figCnt = self._figureCnt = self._figureCnt + 1
            figName = str(figCnt)
        else:
            figName = '?'
        if key is not None:
            figTarg = 'fig_' + str(rCnt)
            self._hdr_mapTarg[key] = figTarg
            self._hdr_mapName[key] = figName
            w('<a name="' + EntityString(figTarg) + '">')
        w('<img src="' + EntityString(src) + '"')
        if alt is not None:
            w(' alt="' + EntityString(alt) + '"')            
        for k,v in attribs.items():
            w(' ' + k + '="' + EntityString(v) + '"')
        w('>')
        if key is not None:
            w('</a>')
        w('</div>\n')
        w('</center>\n')
        if caption is not None:
            w('<br clear="all">\n')
            w('<center>\n')
            w('<p class="FigureCaption">\n')
            w('<b><span class="FigureCaptionLabel">Figure&nbsp;'
              + str(figCnt) + ':&nbsp;</span></b>')
            w(caption)
            w('</p>\n')
            w('</center>')
    def end_figure(self):
        w = self.write
        w('</div>\n')

    def start_footnote(self, attribs):
        f = self._footnotes
        fc = self._footcnt = self._footcnt + 1
        self.write('<sup>[<a href="#footnote-%d" name="footref-%d">%d</a>]</sup>' %
                   ( fc, fc, fc ) )
        self._state.append( 1 )
        # %%% Initialize footnotes
        f.write('<tr valign=baseline><td align=right>')
        f.write('<a href="#footref-%d" name="footnote-%d">[%d]</a>&nbsp;</td>' %
                ( fc, fc, fc ) )
        f.write('<td width=600><p>\n')

    def end_footnote(self):
        del self._state[-1]
        f = self._footnotes
        f.write('</p></td></tr>\n')


    def start_footnotes(self, attribs):
        "Insert the footnote page here."
        tag = self.start_contents_entry(2, 'header-footnotes')
        self._contents.write('Footnotes')
        self.end_contents_entry()
        self.write('<h2><a href="#contents" name="' + EntityString(tag) + '">'
                   + 'Footnotes' + '</a></h2>\n')
        self.write('<table summary="This table lists the footnotes for the document.">\n')
        self.insert_buffer(self._footnotes)
    def end_footnotes(self):
        self.write('</table>\n')

    def start_header(self, level, attribs, key):
        "Start a header."
        w = self.write
        w('<h%d>' % (level,))
        if level >= self._TOCMinLevel:
            useLabel = _TrueFalse(attribs['labelled'], self._labelHeaders)
            self._labelHeader.append(useLabel)
            if useLabel:
                lev = level - self._TOCMinLevel
                sections = self._sections
                for i in range(len(sections)):
                    if i == lev:
                        sections[i] = sections[i] + 1
                    elif i > lev:
                        sections[i] = 0
                sectag = string.join(map(str,sections[0:lev+1]), '.')
                tag =  'sect_' + string.join(map(str,sections[0:lev+1]), '_')
            else:
                sectag = '?'
                tag = None
            tag = self.start_contents_entry(level, tag)
            w('<a href="#contents" name="' + EntityString(tag) + '">')
            if useLabel:
                w(sectag + '</a>&nbsp;&nbsp;')
            if key is not None:
                self._hdr_mapTarg[key] = EntityString(tag)
                self._hdr_mapName[key] = sectag
    def end_header(self, level):
        if level >= self._TOCMinLevel:
            useLabel = self._labelHeader[-1]
            del self._labelHeader[-1]
            self.end_contents_entry()
            if not useLabel:
                self.write('</a>')
        self.write('</h%d>\n' % (level,))

    def start_hr(self, attribs):
        self.write('<hr>\n')
    def end_hr(self):
        pass

    def start_li(self, attribs):
        self._write_text('<li>\n')
    def end_li(self):
        self._write_text('</li>\n')

    def start_ol(self, attribs):
        self._write_text('<ol>\n')
    def end_ol(self):
        self._write_text('</ol>\n')

    def start_p(self, attribs):
        self._write_text('<p>\n')
    def end_p(self):
        self._write_text('</p>\n')

    def start_q(self, attribs):
        # The <q> markup is still rarely implemented.  So we will
        # instead insert quotes.
        qn = self._quoteNest = self._quoteNest + 1
        if qn % 2 == 1:
            self._write_text('&#8220;')   # &ldquo
        else:
            self._write_text('&#8216;')   # &lsquo
    def end_q(self):
        qn = self._quoteNest = self._quoteNest - 1
        if qn % 2 == 0:
            self._write_text('&#8221;')   # &rdquo
        else:
            self._write_text('&#8217;')   # &rsqui

    def start_ref(self, attribs, key):
        "Retrieve a reference."
        b = docfmt.StringIO()
        r = self._hdr_Ref
        try:
            bList = r[key]
        except KeyError:
            bList = r[key] = []
        bList.append(b)
        self.insert_buffer(b)
    def end_ref(self):
        self._write_text('</a>')
    def finalize_ref(self):
        "Finalize references"
        mapTarg = self._hdr_mapTarg
        mapName = self._hdr_mapName
        for k,bl in self._hdr_Ref.items():
            targ = mapTarg[k]
            name = mapName[k]
            for b in bl:
                b.write('<a href="#' + targ + '">')
                b.write(SpecialString(name))

    def start_strong(self, attribs):
        self._write_text('<strong>')
    def end_strong(self):
        self._write_text('</strong>')

    def start_ul(self, attribs):
        self._write_text('<ul>\n')
    def end_ul(self):
        self._write_text('</ul>\n')

    def start_var(self, attribs):
        self._write_text('<var>')
    def end_var(self):
        self._write_text('</var>')

    # These are specific the the SapCat doc.

    def start_EnvVar(self, attribs):
        self._write_text('<code class="EnvVar">')
    def end_EnvVar(self):
        self._write_text('</code>')

    def start_Sys(self, attribs):
        if attribs.has_key('abbrev'):
            self._write_text('<abbr title="'
                             + EntityString(attribs['abbrev'])
                             + '">')
            self._Sys = 1
        elif attribs.has_key('acronym'):
            self._write_text('<acronym title="'
                             + EntityString(attribs['acronym'])
                             + '">')
            self._Sys = 2
        else:
            self._Sys = 0
        self._write_text('<code class="Sys">')
    def end_Sys(self):
        self._write_text('</code>')
        if self._Sys == 1:
            self._write_text('</abbr>')
        elif self._Sys == 2:
            self._write_text('</acronym>')
        del self._Sys

    def start_ManPage(self, attribs, command, decription):
        self.write('<dl class="ManPage">')
        self.write('<dt><strong class="ManPageHeader">NAME</strong></dt>')
        self.write('<dd><code>' + command + '</code>')
        self.write(' &#8212; ')
        self.write(EntityString(decription))
        self.write('\n<br><br></dd>\n')
    def end_ManPage(self):
        self.write('</dl>')

    def start_ManPage_Synopsis(self, attribs):
        self.write('<dt><strong class="ManPageHeader">SYNOPSIS</strong></dt>\n')
        self.write('<dd>\n')
    def end_ManPage_Synopsis(self):
        self.write('\n</br></br></dd>\n')

    def start_ManPage_Description(self, attribs):
        self.write('<dt><strong class="ManPageHeader">DESCRIPTION</strong></dt>\n')
        self.write('<dd>\n')
    def end_ManPage_Description(self):
        self.write('\n</br></br></dd>\n')

    def start_ManPage_Section(self, attribs, title):
        self.write('<dt><strong class="ManPageHeader">' + title + '</strong></dt>\n')
        self.write('<dd>\n')
    def end_ManPage_Section(self):
        self.write('\n</br></br></dd>\n')


    def start_UseCase(self, attribs, name, ident, key):
        "Start a Use Case mark-up."
        w = self.write
        ucc = self._UseCase_cnt = self._UseCase_cnt + 1
        targ = "usecase-" + str(ucc)
        self._UseCase_mapTarg[key] = targ
        self._UseCase_mapName[key] = name
        self._UseCase_mapIdent[key] = ident
        w('<div class="UseCase">')

        #w('<div class="UseCaseTitle">\n')
        #w('<p class="UseCaseTitleKey">'
        #  + '<a class="UseCaseTitleKeyText" name="' + targ + '">'
        #  + EntityString(ident) + '</a></p>\n')
        #w('<p class="UseCaseTitle">' + EntityString(name) + '</p>\n')
        #w('<br clear="all">\n')
        #w('</div>\n')

        w('<div style="margin-left: -8%">'
          + '<table width="100%" summary="' + EntityString(name) + '">'
          + '<tr><td width="5%" bgcolor="#cccccc">'
          + '<a name="' + targ + '" style="font-size: small">'
          + SpecialString(ident) + '</a>'
          + '</td><td width="85%">'
          + '<b><i><span style="font-style: italic; font-weight: bold">'
          + '&nbsp;&nbsp;' + SpecialString(name)
          + '</span></i></b>'
          + '</td></tr></table><br clear="all"></div>\n')

        w('<dl>\n')
    def end_UseCase(self):
        "End a Use Case mark-up."
        self.write('</dl></div>\n')

    def start_UseCase_Section(self, attribs, sectionName):
        "Mark up a Use Case section."
        self.write('<dt><strong class="UseCaseHeader">'
                   + EntityString(sectionName)
                   + '</strong></dt><dd>\n')
    def end_UseCase_Section(self):
        self.write('</br></dd>\n')

    def start_UseCase_Ref(self, attribs, key):
        "Reference to a use case."

        b = docfmt.StringIO()
        r = self._UseCase_Ref
        try:
            bList = r[key]
        except KeyError:
            bList = r[key] = []
        bList.append(b)
        self.insert_buffer(b)
    def end_UseCase_Ref(self):
        self._write_text('</a>')

    def finalize_UseCase(self):
        "Finalize references to use cases."
        mapTarg = self._UseCase_mapTarg
        mapIdent = self._UseCase_mapIdent
        for k, bl in self._UseCase_Ref.items():
            targ = mapTarg[k]
            ident = mapIdent[k]
            for b in bl:
                b.write('<a href="#' + targ + '">')
                b.write(SpecialString(ident))
