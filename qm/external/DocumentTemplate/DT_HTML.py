##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""HTML formated DocumentTemplates

$Id$"""

from DT_String import String, FileMixin
import DT_String, regex
from DT_Util import ParseError, str
from string import strip, find, split, join, rfind, replace

class dtml_re_class:

    def search(self, text, start=0,
               name_match=regex.compile('[\0- ]*[a-zA-Z]+[\0- ]*').match,
               end_match=regex.compile('[\0- ]*\(/\|end\)',
                                       regex.casefold).match,
               start_search=regex.compile('[<&]').search,
               ent_name=regex.compile('[-a-zA-Z0-9_.]+').match,
               find=find,
               strip=strip,
               replace=replace,
               ):

        while 1:
            s=start_search(text, start)
            if s < 0: return -1
            if text[s:s+5] == '<!--#':
                n=s+5
                e=find(text,'-->',n)
                if e < 0: return -1
                en=3

                l=end_match(text,n)
                if l > 0:
                    end=strip(text[n:n+l])
                    n=n+l
                else: end=''

            elif text[s:s+6] == '<dtml-':
                e=n=s+6
                while 1:
                    e=find(text,'>',e+1)
                    if e < 0: return -1
                    if len(split(text[n:e],'"'))%2:
                        # check for even number of "s inside
                        break

                en=1
                end=''

            elif text[s:s+7] == '</dtml-':
                e=n=s+7
                while 1:
                    e=find(text,'>',e+1)
                    if e < 0: return -1
                    if len(split(text[n:e],'"'))%2:
                        # check for even number of "s inside
                        break

                en=1
                end='/'

            else:
                if text[s:s+5] == '&dtml' and text[s+5] in '.-':
                    n=s+6
                    e=find(text,';',n)                        
                    if e >= 0:
                        args=text[n:e]
                        l=len(args)
                        if ent_name(args) == l:
                            d=self.__dict__
                            if text[s+5]=='-':
                                d[1]=d['end']=''
                                d[2]=d['name']='var'
                                d[0]=text[s:e+1]
                                d[3]=d['args']=args+' html_quote'
                                return s
                            else:
                                nn=find(args,'-')
                                if nn >= 0 and nn < l-1:
                                    d[1]=d['end']=''
                                    d[2]=d['name']='var'
                                    d[0]=text[s:e+1]
                                    args=(args[nn+1:]+' '+
                                          replace(args[:nn],'.',' '))
                                    d[3]=d['args']=args
                                    return s
                        
                start=s+1
                continue

            break

        l=name_match(text,n)
        if l < 0: return l
        a=n+l
        name=strip(text[n:a])

        args=strip(text[a:e])

        d=self.__dict__
        d[0]=text[s:e+en]
        d[1]=d['end']=end
        d[2]=d['name']=name
        d[3]=d['args']=args

        return s

    def group(self, *args):
        get=self.__dict__.get
        if len(args)==1:
            return get(args[0])
        return tuple(map(get, args))

        

class HTML(DT_String.String):
    """HTML Document Templates

    HTML Document templates use HTML server-side-include syntax,
    rather than Python format-string syntax.  Here's a simple example:

      <!--#in results-->
        <!--#var name-->
      <!--#/in-->

    HTML document templates quote HTML tags in source when the
    template is converted to a string.  This is handy when templates
    are inserted into HTML editing forms.
    """

    tagre__roles__=()
    def tagre(self):
        return dtml_re_class()

    parseTag__roles__=()
    def parseTag(self, tagre, command=None, sargs=''):
        """Parse a tag using an already matched re

        Return: tag, args, command, coname

        where: tag is the tag,
               args is the tag\'s argument string,
               command is a corresponding command info structure if the
                  tag is a start tag, or None otherwise, and
               coname is the name of a continue tag (e.g. else)
                 or None otherwise
        """
        tag, end, name, args, =tagre.group(0, 'end', 'name', 'args')
        args=strip(args)
        if end:
            if not command or name != command.name:
                raise ParseError, ('unexpected end tag', tag)
            return tag, args, None, None

        if command and name in command.blockContinuations:

            if name=='else' and args:
                # Waaaaaah! Have to special case else because of
                # old else start tag usage. Waaaaaaah!
                l=len(args)
                if not (args==sargs or
                        args==sargs[:l] and sargs[l:l+1] in ' \t\n'):
                    return tag, args, self.commands[name], None
            
            return tag, args, None, name

        try: return tag, args, self.commands[name], None
        except KeyError:
            raise ParseError, ('Unexpected tag', tag)

    SubTemplate__roles__=()
    def SubTemplate(self, name): return HTML('', __name__=name)

    varExtra__roles__=()
    def varExtra(self,tagre): return 's'

    manage_edit__roles__=()
    def manage_edit(self,data,REQUEST=None):
        'edit a template'
        self.munge(data)
        if REQUEST: return self.editConfirmation(self,REQUEST)

    quotedHTML__roles__=()
    def quotedHTML(self,
                   text=None,
                   character_entities=(
                       (('&'), '&amp;'),
                       (("<"), '&lt;' ),
                       ((">"), '&gt;' ),
                       (('"'), '&quot;'))): #"
        if text is None: text=self.read_raw()
        for re,name in character_entities:
            if find(text, re) >= 0: text=join(split(text,re),name)
        return text

    errQuote__roles__=()
    errQuote=quotedHTML

    def __str__(self):
        return self.quotedHTML()

    # these should probably all be deprecated.
    management_interface__roles__=()
    def management_interface(self):
        '''Hook to allow public execution of management interface with
        everything else private.'''
        return self

    manage_editForm__roles__=()
    def manage_editForm(self, URL1, REQUEST):
        '''Display doc template editing form''' #"
        
        return self._manage_editForm(
            self,
            mapping=REQUEST,
            __str__=str(self),
            URL1=URL1
            )

    manage_editDocument__roles__=()
    manage__roles__=()
    manage_editDocument=manage=manage_editForm

class HTMLDefault(HTML):
    '''\
    HTML document templates that edit themselves through copy.

    This is to make a distinction from HTML objects that should edit
    themselves in place.
    '''
    copy_class__roles__=()
    copy_class=HTML

    manage_edit__roles__=()
    def manage_edit(self,data,PARENTS,URL1,REQUEST):
        'edit a template'
        newHTML=self.copy_class(data,self.globals,self.__name__)
        setattr(PARENTS[1],URL1[rfind(URL1,'/')+1:],newHTML)
        return self.editConfirmation(self,REQUEST)


class HTMLFile(FileMixin, HTML):
    """\
    HTML Document templates read from files.

    If the object is pickled, the file name, rather
    than the file contents is pickled.  When the object is
    unpickled, then the file will be re-read to obtain the string.
    Note that the file will not be read until the document
    template is used the first time.
    """
    manage_default__roles__=()
    def manage_default(self, REQUEST=None):
        'Revert to factory defaults'
        if self.edited_source:
            self.edited_source=''
            self._v_cooked=self.cook()
        if REQUEST: return self.editConfirmation(self,REQUEST)

    manage_editForm__roles__=()
    def manage_editForm(self, URL1, REQUEST):
        '''Display doc template editing form'''

        return self._manage_editForm(mapping=REQUEST,
                                     document_template_edit_width=
                                     self.document_template_edit_width,
                                     document_template_edit_header=
                                     self.document_template_edit_header,
                                     document_template_form_header=
                                     self.document_template_form_header,
                                     document_template_edit_footer=
                                     self.document_template_edit_footer,
                                     URL1=URL1,
                                     __str__=str(self),
                                     FactoryDefaultString=FactoryDefaultString,
                                     )
    manage_editDocument__roles__=()
    manage__roles__=()
    manage_editDocument=manage=manage_editForm

    manage_edit__roles__=()
    def manage_edit(self,data,
                    PARENTS=[],URL1='',URL2='',REQUEST='', SUBMIT=''):
        'edit a template'
        if SUBMIT==FactoryDefaultString: return self.manage_default(REQUEST)
        if find(data,'\r'):
            data=join(split(data,'\r\n'),'\n\r')
            data=join(split(data,'\n\r'),'\n')
            
        if self.edited_source:
            self.edited_source=data
            self._v_cooked=self.cook()
        else:
            __traceback_info__=self.__class__
            newHTML=self.__class__()
            newHTML.__setstate__(self.__getstate__())
            newHTML.edited_source=data
            setattr(PARENTS[1],URL1[rfind(URL1,'/')+1:],newHTML)
        if REQUEST: return self.editConfirmation(self,REQUEST)
