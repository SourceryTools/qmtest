##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
$Id: html.py 41188 2006-01-08 09:27:48Z philikon $
"""

import re
import sys
from cgi import escape

__metaclass__ = type

class HTML:

    element_types = {
        '#text': '_text',
        'StructuredTextDocument': 'document',
        'StructuredTextParagraph': 'paragraph',
        'StructuredTextExample': 'example',
        'StructuredTextBullet': 'bullet',
        'StructuredTextNumbered': 'numbered',
        'StructuredTextDescription': 'description',
        'StructuredTextDescriptionTitle': 'descriptionTitle',
        'StructuredTextDescriptionBody': 'descriptionBody',
        'StructuredTextSection': 'section',
        'StructuredTextSectionTitle': 'sectionTitle',
        'StructuredTextLiteral': 'literal',
        'StructuredTextEmphasis': 'emphasis',
        'StructuredTextStrong': 'strong',
        'StructuredTextLink': 'link',
        'StructuredTextXref': 'xref',
        'StructuredTextInnerLink':'innerLink',
        'StructuredTextNamedLink':'namedLink',
        'StructuredTextUnderline':'underline',
        'StructuredTextTable':'table',
        'StructuredTextSGML':'sgml',
        }


    def dispatch(self, doc, level, output):
        getattr(self, self.element_types[doc.getNodeName()])(doc, level, output)

    def __call__(self, doc, level=1, header=True):
        r=[]
        self.header = header
        self.dispatch(doc, level-1, r.append)
        return ''.join(r)

    def _text(self, doc, level, output):
        output(doc.getNodeValue())

    def document(self, doc, level, output):
        children=doc.getChildNodes()

        if self.header:
            output('<html>\n')
            if (children and
                 children[0].getNodeName() == 'StructuredTextSection'):
                output('<head>\n<title>%s</title>\n</head>\n' %
                         children[0].getChildNodes()[0].getNodeValue())
            output('<body>\n')

        for c in children:
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)

        if self.header:
            output('</body>\n')
            output('</html>\n')

    def section(self, doc, level, output):
        children=doc.getChildNodes()
        for c in children:
            getattr(self, self.element_types[c.getNodeName()])(c, level+1, output)

    def sectionTitle(self, doc, level, output):
        output('<h%d>' % (level))
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</h%d>\n' % (level))

    def description(self, doc, level, output):
        p=doc.getPreviousSibling()
        if p is None or  p.getNodeName() is not doc.getNodeName():
            output('<dl>\n')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        n=doc.getNextSibling()
        if n is None or n.getNodeName() is not doc.getNodeName():
            output('</dl>\n')

    def descriptionTitle(self, doc, level, output):
        output('<dt>')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</dt>\n')

    def descriptionBody(self, doc, level, output):
        output('<dd>')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</dd>\n')

    def bullet(self, doc, level, output):
        p=doc.getPreviousSibling()
        if p is None or p.getNodeName() is not doc.getNodeName():
            output('\n<ul>\n')
        output('<li>')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        n=doc.getNextSibling()
        output('</li>\n')
        if n is None or n.getNodeName() is not doc.getNodeName():
            output('\n</ul>\n')

    def numbered(self, doc, level, output):
        p=doc.getPreviousSibling()
        if p is None or p.getNodeName() is not doc.getNodeName():
            output('\n<ol>\n')
        output('<li>')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        n=doc.getNextSibling()
        output('</li>\n')
        if n is None or n.getNodeName() is not doc.getNodeName():
            output('\n</ol>\n')

    def example(self, doc, level, output):
        i=0
        for c in doc.getChildNodes():
            if i==0:
                output('\n<pre>\n')
                output(escape(c.getNodeValue()))
                output('\n</pre>\n')
            else:
                getattr(self, self.element_types[c.getNodeName()])(
                    c, level, output)

    def paragraph(self, doc, level, output):
        output('<p>')
        for c in doc.getChildNodes():
            if c.getNodeName() in ['StructuredTextParagraph']:
                getattr(self, self.element_types[c.getNodeName()])(
                    c, level, output)
            else:
                getattr(self, self.element_types[c.getNodeName()])(
                    c, level, output)
        output('</p>\n')

    def link(self, doc, level, output):
        output('<a href="%s">' % doc.href)
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</a>')

    def emphasis(self, doc, level, output):
        output('<em>')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</em>')

    def literal(self, doc, level, output):
        output('<code>')
        for c in doc.getChildNodes():
            output(escape(c.getNodeValue()))
        output('</code>')

    def strong(self, doc, level, output):
        output('<strong>')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</strong>')

    def underline(self, doc, level, output):
        output("<u>")
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output("</u>")

    def innerLink(self, doc, level, output):
        output('<a href="#ref');
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('">[')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output(']</a>')

    def namedLink(self, doc, level, output):
        output('<a name="ref')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('">[')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output(']</a>')

    def sgml(self,doc,level,output):
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)

    def xref(self, doc, level, output):
        val = doc.getNodeValue()
        output('<a href="#ref%s">[%s]</a>' % (val, val) )

    def table(self,doc,level,output):
        """
        A StructuredTextTable holds StructuredTextRow(s) which
        holds StructuredTextColumn(s). A StructuredTextColumn
        is a type of StructuredTextParagraph and thus holds
        the actual data.
        """
        output('<table border="1" cellpadding="2">\n')
        for row in doc.getRows()[0]:
            output("<tr>\n")
            for column in row.getColumns()[0]:
                if hasattr(column,"getAlign"):
                    str = '<%s colspan="%s" align="%s" valign="%s">' % (column.getType(),
                                                                  column.getSpan(),
                                                                  column.getAlign(),
                                                                  column.getValign())
                else:
                    str = '<td colspan="%s">' % column.getSpan()
                output(str)
                for c in column.getChildNodes():
                    getattr(self, self.element_types[c.getNodeName()])(c, level, output)
                if hasattr(column,"getType"):
                    output("</"+column.getType()+">\n")
                else:
                    output("</td>\n")
            output("</tr>\n")
        output("</table>\n")

class HTMLWithImages(HTML):

    element_types = HTML.element_types
    element_types.update({'StructuredTextImage': 'image'})

    def image(self, doc, level, output):
        if hasattr(doc, 'key'):
            output('<a name="%s"></a>\n' % doc.key)
        output('<img src="%s" alt="%s" />\n' % (doc.href, doc.getNodeValue()))
        if doc.getNodeValue() and hasattr(doc, 'key'):
            output('<p><b>Figure %s</b> %s</p>\n' % (doc.key, doc.getNodeValue()))
