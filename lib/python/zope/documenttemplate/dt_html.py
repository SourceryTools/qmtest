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
"""HTML formated DocumentTemplates

$Id: dt_html.py 38178 2005-08-30 21:50:19Z mj $
"""
import re
from zope.documenttemplate.dt_string import String
from zope.documenttemplate.dt_util import ParseError

class DTMLRegExClass:

    def search(self, text, start=0,
               name_match=re.compile('[\0- ]*[a-zA-Z]+[\0- ]*').match,
               start_search=re.compile('[<&]').search,
               ent_name=re.compile('[-a-zA-Z0-9_.]+').match
               ):

        while True:
            mo = start_search(text, start)
            if mo is None:
                return None
            s = mo.start(0)

            if text[s:s+6] == '<dtml-':
                e = n = s+6
                while True:
                    e = text.find('>', e+1)
                    if e < 0:
                        return None
                    if len(text[n:e].split('"'))%2:
                        # check for even number of "s inside
                        break

                en = 1
                end = ''

            elif text[s:s+7] == '</dtml-':
                e=n=s+7
                while True:
                    e=text.find('>',e+1)
                    if e < 0:
                        return None
                    if len(text[n:e].split('"'))%2:
                        # check for even number of "s inside
                        break

                en=1
                end='/'

            else:
                if text[s:s+5] == '&dtml' and text[s+5] in '.-':
                    n=s+6
                    e=text.find(';', n)
                    if e >= 0:
                        args=text[n:e]
                        l=len(args)
                        mo = ent_name(args)
                        if mo is not None and mo.end(0)-mo.start(0) == l:
                            d=self.__dict__
                            if text[s+5] == '-':
                                d[1] = d['end'] = ''
                                d[2] = d['name'] = 'var'
                                d[0] = text[s:e+1]
                                d[3] = d['args'] = args + ' html_quote'
                                self._start = s
                                return self
                            else:
                                nn=args.find('-')
                                if nn >= 0 and nn < l-1:
                                    d[1]=d['end']=''
                                    d[2]=d['name']='var'
                                    d[0]=text[s:e+1]
                                    args=(args[nn+1:]+' '+
                                          args[:nn].replace('.', ' '))
                                    d[3]=d['args']=args
                                    self._start = s
                                    return self

                start = s + 1
                continue

            break

        mo=name_match(text,n)
        if mo is None:
            return None
        l = mo.end(0) - mo.start(0)
        a=n+l
        name=text[n:a].strip()

        args=text[a:e].strip()

        d=self.__dict__
        d[0]=text[s:e+en]
        d[1]=d['end']=end
        d[2]=d['name']=name
        d[3]=d['args']=args

        self._start = s
        return self


    def group(self, *args):
        get=self.__dict__.get
        if len(args)==1:
            return get(args[0])
        return tuple(map(get, args))


    def start(self, *args):
        return self._start



class HTML(String):
    """HTML Document Templates

    HTML Document templates use HTML server-side-include syntax,
    rather than Python format-string syntax.  Here's a simple example:

      <dtml-in results>
        <dtml-var name>
      </dtml-in>

    HTML document templates quote HTML tags in source when the
    template is converted to a string.  This is handy when templates
    are inserted into HTML editing forms.
    """

    def tagre(self):
        return DTMLRegExClass()


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
        args=args.strip()
        if end:
            if not command or name != command.name:
                raise ParseError('unexpected end tag', tag)
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
            raise ParseError('Unexpected tag', tag)


    def SubTemplate(self, name):
        return HTML('', __name__=name)

    def varExtra(self,tagre):
        return 's'

    def quotedHTML(self,
                   text=None,
                   character_entities=(
                       (('&'), '&amp;'),
                       (("<"), '&lt;' ),
                       ((">"), '&gt;' ),
                       (('"'), '&quot;'))): #"
        if text is None:
            text=self.read_raw()
        for re, name in character_entities:
            if text.find(re) >= 0:
                text = name.join(text.split(re))
        return text

    errQuote = quotedHTML

    def __str__(self):
        return self.quotedHTML()
