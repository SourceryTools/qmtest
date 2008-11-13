# -*- coding: ISO-8859-1 -*-
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
"""Tests for TALInterpreter.

$Id: test_talinterpreter.py 69782 2006-08-25 17:05:12Z mgedmin $
"""
import os
import sys
import unittest

from StringIO import StringIO

from zope.tal.taldefs import METALError, I18NError, TAL_VERSION
from zope.tal.taldefs import TALExpressionError
from zope.tal.htmltalparser import HTMLTALParser
from zope.tal.talparser import TALParser
from zope.tal.talinterpreter import TALInterpreter
from zope.tal.talgenerator import TALGenerator
from zope.tal.dummyengine import DummyEngine
from zope.tal.dummyengine import MultipleDomainsDummyEngine
from zope.tal.dummyengine import DummyTranslationDomain
from zope.tal.tests import utils
from zope.i18nmessageid import Message


class TestCaseBase(unittest.TestCase):

    def _compile(self, source, source_file=None):
        generator = TALGenerator(xml=0, source_file=source_file)
        parser = HTMLTALParser(generator)
        parser.parseString(source)
        program, macros = parser.getCode()
        return program, macros


class MacroErrorsTestCase(TestCaseBase):

    def setUp(self):
        dummy, macros = self._compile('<p metal:define-macro="M">Booh</p>')
        self.macro = macros['M']
        self.engine = DummyEngine(macros)
        program, dummy = self._compile('<p metal:use-macro="M">Bah</p>')
        self.interpreter = TALInterpreter(program, {}, self.engine)

    def tearDown(self):
        try:
            self.interpreter()
        except METALError:
            pass
        else:
            self.fail("Expected METALError")

    def test_mode_error(self):
        self.macro[1] = ("mode", "duh")

    def test_version_error(self):
        self.macro[0] = ("version", "duh")


class MacroFunkyErrorTest(TestCaseBase):

    def test_div_in_p_using_macro(self):
        dummy, macros = self._compile('<p metal:define-macro="M">Booh</p>')
        engine = DummyEngine(macros)
        program, dummy = self._compile(
            '<p metal:use-macro="M"><div>foo</div></p>')
        interpreter = TALInterpreter(program, {}, engine)

        output = interpreter()
        self.assertEqual(output, '<p><div>foo</div></p>')


class MacroExtendTestCase(TestCaseBase):

    def setUp(self):
        s = self._read(('input', 'pnome_template.pt'))
        self.pnome_program, pnome_macros = self._compile(s)
        s = self._read(('input', 'acme_template.pt'))
        self.acme_program, acme_macros = self._compile(s)
        s = self._read(('input', 'document_list.pt'))
        self.doclist_program, doclist_macros = self._compile(s)
        macros = {
            'pnome_macros_page': pnome_macros['page'],
            'acme_macros_page': acme_macros['page'],
            }
        self.engine = DummyEngine(macros)

    def _read(self, path):
        dir = os.path.dirname(__file__)
        fn = os.path.join(dir, *path)
        f = open(fn)
        data = f.read()
        f.close()
        return data

    def test_preview_acme_template(self):
        # An ACME designer is previewing the ACME design.  For the
        # purposes of this use case, extending a macro should act the
        # same as using a macro.
        result = StringIO()
        interpreter = TALInterpreter(
            self.acme_program, {}, self.engine, stream=result)
        interpreter()
        actual = result.getvalue().strip()
        expected = self._read(('output', 'acme_template.html')).strip()
        self.assertEqual(actual, expected)

    def test_preview_acme_template_source(self):
        # Render METAL attributes in acme_template
        result = StringIO()
        interpreter = TALInterpreter(
            self.acme_program, {}, self.engine, stream=result, tal=False)
        interpreter()
        actual = result.getvalue().strip()
        expected = self._read(('output', 'acme_template_source.html')).strip()
        self.assertEqual(actual, expected)


class I18NCornerTestCaseBase(TestCaseBase):

    def factory(self, msgid, default, mapping={}):
        raise NotImplementedError("abstract method")

    def setUp(self):
        self.engine = DummyEngine()
        # Make sure we'll translate the msgid not its unicode representation
        self.engine.setLocal('foo',
            self.factory('FoOvAlUe${empty}', 'default', {'empty': ''}))
        self.engine.setLocal('bar', 'BaRvAlUe')

    def _check(self, program, expected):
        result = StringIO()
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        self.assertEqual(expected, result.getvalue())

    def test_simple_messageid_translate(self):
        # This test is mainly here to make sure our DummyEngine works
        # correctly.
        program, macros = self._compile(
            '<span i18n:translate="" tal:content="foo"/>')
        self._check(program, '<span>FOOVALUE</span>\n')

        program, macros = self._compile(
            '<span i18n:translate="" tal:replace="foo"/>')
        self._check(program, 'FOOVALUE\n')

        # i18n messages defined in Python are translated automatically
        # (no i18n:translate necessary)
        program, macros = self._compile(
            '<span tal:content="foo" />')
        self._check(program, '<span>FOOVALUE</span>\n')

        program, macros = self._compile(
            '<span tal:replace="foo" />')
        self._check(program, 'FOOVALUE\n')

    def test_attributes_translation(self):
        program, macros = self._compile(
            '<span tal:attributes="test bar"/>')
        self._check(program, '<span test="BaRvAlUe" />\n')

        program, macros = self._compile(
            '<span test="bar" i18n:attributes="test"/>')
        self._check(program, '<span test="BAR" />\n')

        program, macros = self._compile(
            '<span tal:attributes="test bar" i18n:attributes="test"/>')
        self._check(program, '<span test="BARVALUE" />\n')

        # i18n messages defined in Python are translated automatically
        # (no i18n:attributes necessary)
        program, macros = self._compile(
            '<span tal:attributes="test foo"/>')
        self._check(program, '<span test="FOOVALUE" />\n')

    def test_text_variable_translate(self):
        program, macros = self._compile(
            '<span tal:content="bar"/>')
        self._check(program, '<span>BaRvAlUe</span>\n')

        program, macros = self._compile(
            '<span i18n:translate="" tal:content="bar"/>')
        self._check(program, '<span>BARVALUE</span>\n')

        program, macros = self._compile(
            '<span i18n:translate="" tal:replace="bar"/>')
        self._check(program, 'BARVALUE\n')

    def test_text_translate(self):
        program, macros = self._compile(
            '<span tal:content="string:BaR"/>')
        self._check(program, '<span>BaR</span>\n')

        program, macros = self._compile(
            '<span i18n:translate="" tal:content="string:BaR"/>')
        self._check(program, '<span>BAR</span>\n')

        program, macros = self._compile(
            '<span i18n:translate="" tal:replace="string:BaR"/>')
        self._check(program, 'BAR\n')

    def test_structure_text_variable_translate(self):
        program, macros = self._compile(
            '<span tal:content="structure bar"/>')
        self._check(program, '<span>BaRvAlUe</span>\n')

        program, macros = self._compile(
            '<span i18n:translate="" tal:content="structure bar"/>')
        self._check(program, '<span>BARVALUE</span>\n')

        program, macros = self._compile(
            '<span i18n:translate="" tal:replace="structure bar"/>')
        self._check(program, 'BARVALUE\n')

        # i18n messages defined in Python are translated automatically
        # (no i18n:translate necessary)
        program, macros = self._compile(
            '<span tal:content="structure foo"/>')
        self._check(program, '<span>FOOVALUE</span>\n')

        program, macros = self._compile(
            '<span tal:replace="structure foo"/>')
        self._check(program, 'FOOVALUE\n')

    def test_structure_text_translate(self):
        program, macros = self._compile(
            '<span tal:content="structure string:BaR"/>')
        self._check(program, '<span>BaR</span>\n')

        program, macros = self._compile(
            '<span i18n:translate="" tal:content="structure string:BaR"/>')
        self._check(program, '<span>BAR</span>\n')

        program, macros = self._compile(
            '<span i18n:translate="" tal:replace="structure string:BaR"/>')
        self._check(program, 'BAR\n')

    def test_replace_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<span i18n:translate="" tal:replace="foo" i18n:name="foo_name"/>'
            '</div>')
        self._check(program, '<div>FOOVALUE</div>\n')

    def test_pythonexpr_replace_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<span i18n:translate="" tal:replace="python: foo"'
            '    i18n:name="foo_name"/>'
            '</div>')
        self._check(program, '<div>FOOVALUE</div>\n')

    def test_structure_replace_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<span i18n:translate="" tal:replace="structure foo"'
            '    i18n:name="foo_name"/>'
            '</div>')
        self._check(program, '<div>FOOVALUE</div>\n')

    def test_complex_replace_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<em tal:omit-tag="" i18n:name="foo_name">'
            '<span i18n:translate="" tal:replace="foo"/>'
            '</em>'
            '</div>')
        self._check(program, '<div>FOOVALUE</div>\n')

    def test_content_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<span i18n:translate="" tal:content="foo" i18n:name="foo_name"/>'
            '</div>')
        self._check(program, '<div><span>FOOVALUE</span></div>\n')

    def test_content_with_messageid_and_i18nname_and_i18ntranslate(self):
        # Let's tell the user this is incredibly silly!
        self.assertRaises(
            I18NError, self._compile,
            '<span i18n:translate="" tal:content="foo" i18n:name="foo_name"/>')

    def test_content_with_explicit_messageid(self):
        # Let's tell the user this is incredibly silly!
        self.assertRaises(
            I18NError, self._compile,
            '<span i18n:translate="ID" tal:content="foo" />')

    def test_content_with_plaintext_and_i18nname_and_i18ntranslate(self):
        # Let's tell the user this is incredibly silly!
        self.assertRaises(
            I18NError, self._compile,
            '<span i18n:translate="" i18n:name="color_name">green</span>')

    def test_translate_static_text_as_dynamic(self):
        program, macros = self._compile(
            '<div i18n:translate="">This is text for '
            '<span tal:content="bar" i18n:name="bar_name"/>.'
            '</div>')
        self._check(program,
                    '<div>THIS IS TEXT FOR <span>BaRvAlUe</span>.</div>\n')
        program, macros = self._compile(
            '<div i18n:translate="">This is text for '
            '<span i18n:translate="" tal:content="bar" i18n:name="bar_name"/>.'
            '</div>')
        self._check(program,
                    '<div>THIS IS TEXT FOR <span>BARVALUE</span>.</div>\n')

    def test_translate_static_text_as_dynamic_from_bytecode(self):
        program =  [('version', TAL_VERSION),
 ('mode', 'html'),
('setPosition', (1, 0)),
('beginScope', {'i18n:translate': ''}),
('startTag', ('div', [('i18n:translate', '', 'i18n')])),
('insertTranslation',
 ('',
  [('rawtextOffset', ('This is text for ', 17)),
   ('setPosition', (1, 40)),
   ('beginScope',
    {'tal:content': 'bar', 'i18n:name': 'bar_name', 'i18n:translate': ''}),
   ('i18nVariable',
       ('bar_name',
        [('startTag',
           ('span',
            [('i18n:translate', '', 'i18n'),
             ('tal:content', 'bar', 'tal'),
             ('i18n:name', 'bar_name', 'i18n')])),
         ('insertTranslation',
           ('',
             [('insertText', ('$bar$', []))])),
         ('rawtextOffset', ('</span>', 7))],
        None,
        0)),
   ('endScope', ()),
   ('rawtextOffset', ('.', 1))])),
('endScope', ()),
('rawtextOffset', ('</div>', 6))
]
        self._check(program,
                    '<div>THIS IS TEXT FOR <span>BARVALUE</span>.</div>\n')

    def test_for_correct_msgids(self):
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        #GChapelle: 
        #I have the feeling the i18n:translate with the i18n:name is wrong
        #
        #program, macros = self._compile(
        #    '<div i18n:translate="">This is text for '
        #    '<span i18n:translate="" tal:content="bar" '
        #    'i18n:name="bar_name"/>.</div>')
        program, macros = self._compile(
            '<div i18n:translate="">This is text for '
            '<span tal:content="bar" '
            'i18n:name="bar_name"/>.</div>')
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(1, len(msgids))
        self.assertEqual('This is text for ${bar_name}.', msgids[0][0])
        self.assertEqual({'bar_name': '<span>BaRvAlUe</span>'}, msgids[0][1])
        self.assertEqual(
            '<div>THIS IS TEXT FOR <span>BaRvAlUe</span>.</div>\n',
            result.getvalue())

    def test_for_correct_msgids_translate_name(self):
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        program, macros = self._compile(
            '<div i18n:translate="">This is text for '
            '<span i18n:translate="" tal:content="bar" '
            'i18n:name="bar_name"/>.</div>')
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(2, len(msgids))
        self.assertEqual('This is text for ${bar_name}.', msgids[1][0])
        self.assertEqual({'bar_name': '<span>BARVALUE</span>'}, msgids[1][1])
        self.assertEqual(
            '<div>THIS IS TEXT FOR <span>BARVALUE</span>.</div>\n',
            result.getvalue())

    def test_i18ntranslate_i18nname_and_attributes(self):
        # Test for Issue 301: Bug with i18n:name and i18n:translate
        # on the same element
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        program, macros = self._compile(
            '<p i18n:translate="">'
            'Some static text and a <a tal:attributes="href string:url"'
            ' i18n:name="link" i18n:translate="">link text</a>.</p>')
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(2, len(msgids))
        self.assertEqual('Some static text and a ${link}.', msgids[0][0])
        self.assertEqual({'link': '<a href="url">LINK TEXT</a>'}, msgids[0][1])
        self.assertEqual('link text', msgids[1][0])
        self.assertEqual(
            '<p>SOME STATIC TEXT AND A <a href="url">LINK TEXT</a>.</p>\n',
            result.getvalue())

    def test_for_raw_msgids(self):
        # Test for Issue 314: i18n:translate removes line breaks from
        # <pre>...</pre> contents
        # HTML mode
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        program, macros = self._compile(
            '<div i18n:translate=""> This is text\n'
            ' \tfor\n div. </div>'
            '<pre i18n:translate=""> This is text\n'
            ' <b>\tfor</b>\n pre. </pre>')
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(2, len(msgids))
        self.assertEqual(' This is text\n <b>\tfor</b>\n pre. ', msgids[0][0])
        self.assertEqual('This is text for div.', msgids[1][0])
        self.assertEqual(
            '<div>THIS IS TEXT FOR DIV.</div>'
            '<pre> THIS IS TEXT\n <B>\tFOR</B>\n PRE. </pre>\n',
            result.getvalue())

        # XML mode
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        parser = TALParser()
        parser.parseString(
            '<?xml version="1.0"?>\n'
            '<pre xmlns:i18n="http://xml.zope.org/namespaces/i18n"'
            ' i18n:translate=""> This is text\n'
            ' <b>\tfor</b>\n barvalue. </pre>')
        program, macros = parser.getCode()
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(1, len(msgids))
        self.assertEqual('This is text <b> for</b> barvalue.', msgids[0][0])
        self.assertEqual(
            '<?xml version="1.0"?>\n'
            '<pre>THIS IS TEXT <B> FOR</B> BARVALUE.</pre>\n',
            result.getvalue())

    def test_raw_msgids_and_i18ntranslate_i18nname(self):
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        program, macros = self._compile(
            '<div i18n:translate=""> This is text\n \tfor\n'
            '<pre i18n:name="bar" i18n:translate=""> \tbar\n </pre>.</div>')
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(2, len(msgids))
        self.assertEqual(' \tbar\n ', msgids[0][0])
        self.assertEqual('This is text for ${bar}.', msgids[1][0])
        self.assertEqual({'bar': '<pre> \tBAR\n </pre>'}, msgids[1][1])
        self.assertEqual(
            u'<div>THIS IS TEXT FOR <pre> \tBAR\n </pre>.</div>\n',
            result.getvalue())

    def test_for_handling_unicode_vars(self):
        # Make sure that non-ASCII Unicode is substituted correctly.
        # http://collector.zope.org/Zope3-dev/264
        program, macros = self._compile(
            "<div i18n:translate='' tal:define='bar python:unichr(0xC0)'>"
            "Foo <span tal:replace='bar' i18n:name='bar' /></div>")
        self._check(program, u"<div>FOO \u00C0</div>\n")

class I18NCornerTestCaseMessage(I18NCornerTestCaseBase):

    def factory(self, msgid, default=None, mapping={}, domain=None):
        return Message(msgid, domain=domain, default=default, mapping=mapping)

class UnusedExplicitDomainTestCase(I18NCornerTestCaseMessage):

    def setUp(self):
        # MultipleDomainsDummyEngine is a Engine
        # where default domain transforms to uppercase
        self.engine = MultipleDomainsDummyEngine()
        self.engine.setLocal('foo',
            self.factory('FoOvAlUe${empty}', 'default', {'empty': ''}))
        self.engine.setLocal('bar', 'BaRvAlUe')
        self.engine.setLocal('baz',
            self.factory('BaZvAlUe', 'default', {}))
        # Message ids with different domains
        self.engine.setLocal('toupper',
            self.factory('ToUpper', 'default', {}))
        self.engine.setLocal('tolower',
            self.factory('ToLower', 'default', {}, domain='lower'))

    def test_multiple_domains(self):
        program, macros = self._compile(
            '<div i18n:translate=""'
            '     tal:content="toupper" />')
        self._check(program, '<div>TOUPPER</div>\n')
        program, macros = self._compile(
            '<div i18n:translate=""'
            '     tal:content="tolower" />')
        self._check(program, '<div>tolower</div>\n')
        program, macros = self._compile(
            '<div i18n:translate=""'
            '     tal:content="string:ToUpper" />')
        self._check(program, '<div>TOUPPER</div>\n')
        program, macros = self._compile(
            '<div i18n:translate=""'
            '     i18n:domain="lower"'
            '     tal:content="string:ToLower" />')
        self._check(program, '<div>tolower</div>\n')
        program, macros = self._compile(
            '<div i18n:translate=""'
            '     tal:define="msgid string:ToUpper"'
            '     tal:content="msgid" />')
        self._check(program, '<div>TOUPPER</div>\n')
        program, macros = self._compile(
            '<div i18n:translate=""'
            '     i18n:domain="lower"'
            '     tal:define="msgid string:ToLower"'
            '     tal:content="msgid" />')
        self._check(program, '<div>tolower</div>\n')

    def test_unused_explicit_domain(self):
        #a_very_explicit_domain_setup_by_template_developer_that_wont_be_taken_into_account_by_the_ZPT_engine 
        #is a domain that transforms to lowercase
        self.engine.setLocal('othertolower',
            self.factory('OtherToLower', 'a_very_explicit_domain_setup_by_template_developer_that_wont_be_taken_into_account_by_the_ZPT_engine', {}, domain='lower'))
        program, macros = self._compile(
            '<div i18n:translate=""'
            '     tal:content="othertolower" />')
        self._check(program, '<div>othertolower</div>\n')
        #takes domain into account for strings
        program, macros = self._compile(
            '<div i18n:translate=""'
            '     i18n:domain="a_very_explicit_domain_setup_by_template_developer_that_wont_be_taken_into_account_by_the_ZPT_engine"'
            '     tal:content="string:ToLower" />')
        self._check(program, '<div>tolower</div>\n')
        #but not for messageids
        program, macros = self._compile(
            '<div i18n:translate=""'
            '     i18n:domain="a_very_explicit_domain_setup_by_template_developer_that_wont_be_taken_into_account_by_the_ZPT_engine"'
            '     tal:content="baz" />')
        self._check(program, '<div>BAZVALUE</div>\n')

class ScriptTestCase(TestCaseBase):

    def setUp(self):
        self.engine = DummyEngine()

    def _check(self, program, expected):
        result = StringIO()
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        self.assertEqual(expected, result.getvalue())

    def test_simple(self):
        program, macros = self._compile(
            '<p tal:script="text/server-python">print "hello"</p>')
        self._check(program, '<p>hello\n</p>\n')

    def test_script_and_tal_block(self):
        program, macros = self._compile(
            '<tal:block script="text/server-python">\n'
            '  global x\n'
            '  x = 1\n'
            '</tal:block>\n'
            '<span tal:replace="x" />')
        self._check(program, '\n1\n')
        self.assertEqual(self.engine.codeGlobals['x'], 1)

    def test_script_and_tal_block_having_inside_print(self):
        program, macros = self._compile(
            '<tal:block script="text/server-python">\n'
            '  print "hello"'
            '</tal:block>')
        self._check(program, 'hello\n\n')

    def test_script_and_omittag(self):
        program, macros = self._compile(
            '<p tal:omit-tag="" tal:script="text/server-python">\n'
            '  print "hello"'
            '</p>')
        self._check(program, 'hello\n\n')

    def test_script_and_inside_tags(self):
        program, macros = self._compile(
            '<p tal:omit-tag="" tal:script="text/server-python">\n'
            '  print "<b>hello</b>"'
            '</p>')
        self._check(program, '<b>hello</b>\n\n')

    def test_script_and_inside_tags_with_tal(self):
        program, macros = self._compile(
            '<p tal:omit-tag="" tal:script="text/server-python"> <!--\n'
            '  print """<b tal:replace="string:foo">hello</b>"""\n'
            '--></p>')
        self._check(program, '<b tal:replace="string:foo">hello</b>\n\n')

    def test_html_script(self):
        program, macros = self._compile(
            '<script type="text/server-python">\n'
            '  print "Hello world!"\n'
            '</script>')
        self._check(program, 'Hello world!\n')

    def test_html_script_and_javascript(self):
        program, macros = self._compile(
            '<script type="text/javascript" src="somefile.js" />\n'
            '<script type="text/server-python">\n'
            '  print "Hello world!"\n'
            '</script>')
        self._check(program,
                    '<script type="text/javascript" src="somefile.js" />\n'
                    'Hello world!\n')


class I18NErrorsTestCase(TestCaseBase):

    def _check(self, src, msg):
        try:
            self._compile(src)
        except I18NError:
            pass
        else:
            self.fail(msg)

    def test_id_with_replace(self):
        self._check('<p i18n:id="foo" tal:replace="string:splat"></p>',
                    "expected i18n:id with tal:replace to be denied")

    def test_missing_values(self):
        self._check('<p i18n:attributes=""></p>',
                    "missing i18n:attributes value not caught")
        self._check('<p i18n:data=""></p>',
                    "missing i18n:data value not caught")
        self._check('<p i18n:id=""></p>',
                    "missing i18n:id value not caught")

    def test_id_with_attributes(self):
        self._check('''<input name="Delete"
                       tal:attributes="name string:delete_button"
                       i18n:attributes="name message-id">''',
            "expected attribute being both part of tal:attributes" +
            " and having a msgid in i18n:attributes to be denied")

class OutputPresentationTestCase(TestCaseBase):

    def test_attribute_wrapping(self):
        # To make sure the attribute-wrapping code is invoked, we have to
        # include at least one TAL/METAL attribute to avoid having the start
        # tag optimized into a rawtext instruction.
        INPUT = r"""
        <html this='element' has='a' lot='of' attributes=', so' the='output'
              needs='to' be='line' wrapped='.' tal:define='foo nothing'>
        </html>"""
        EXPECTED = r'''
        <html this="element" has="a" lot="of"
              attributes=", so" the="output" needs="to"
              be="line" wrapped=".">
        </html>''' "\n"
        self.compare(INPUT, EXPECTED)

    def test_unicode_content(self):
        INPUT = """<p tal:content="python:u'déjà-vu'">para</p>"""
        EXPECTED = u"""<p>déjà-vu</p>""" "\n"
        self.compare(INPUT, EXPECTED)

    def test_unicode_structure(self):
        INPUT = """<p tal:replace="structure python:u'déjà-vu'">para</p>"""
        EXPECTED = u"""déjà-vu""" "\n"
        self.compare(INPUT, EXPECTED)

    def test_i18n_replace_number(self):
        INPUT = """
        <p i18n:translate="foo ${bar}">
        <span tal:replace="python:123" i18n:name="bar">para</span>
        </p>"""
        EXPECTED = u"""
        <p>FOO 123</p>""" "\n"
        self.compare(INPUT, EXPECTED)

    def test_entities(self):
        INPUT = ('<img tal:define="foo nothing" '
                 'alt="&a; &#1; &#x0a; &a &#45 &; &#0a; <>" />')
        EXPECTED = ('<img alt="&a; &#1; &#x0a; '
                    '&amp;a &amp;#45 &amp;; &amp;#0a; &lt;&gt;" />\n')
        self.compare(INPUT, EXPECTED)

    def compare(self, INPUT, EXPECTED):
        program, macros = self._compile(INPUT)
        sio = StringIO()
        interp = TALInterpreter(program, {}, DummyEngine(), sio, wrap=60)
        interp()
        self.assertEqual(sio.getvalue(), EXPECTED)


class TestSourceAnnotations(unittest.TestCase):

    # there are additional test files in input/ and output/ subdirs
    # (test_sa*)

    def setUp(self):
        program = []
        macros = {}
        engine = DummyEngine()
        self.interpreter = TALInterpreter(program, macros, engine)
        self.sio = self.interpreter.stream = StringIO()
        self.interpreter._pending_source_annotation = True

    def testFormatSourceAnnotation(self):
        interpreter = self.interpreter
        interpreter.sourceFile = '/path/to/source.pt'
        interpreter.position = (123, 42)
        self.assertEquals(interpreter.formatSourceAnnotation(),
            "<!--\n" +
            "=" * 78 + "\n" +
            "/path/to/source.pt (line 123)\n" +
            "=" * 78 + "\n" +
            "-->")

    def testFormatSourceAnnotation_no_position(self):
        interpreter = self.interpreter
        interpreter.sourceFile = '/path/to/source.pt'
        interpreter.position = (None, None)
        self.assertEquals(interpreter.formatSourceAnnotation(),
            "<!--\n" +
            "=" * 78 + "\n" +
            "/path/to/source.pt\n" +
            "=" * 78 + "\n" +
            "-->")

    def test_annotated_stream_write(self):
        interpreter = self.interpreter
        interpreter.formatSourceAnnotation = lambda: '@'
        test_cases = [
            '@some text',
            '\n',
            '<?xml ...?>@some text',
            ' <?xml ...?>@some text',
            '\n<?xml ...?>@some text',
            '<?xml ...',
            '<?xml ...?>@\n<!DOCTYPE ...>some text',
        ]
        for output in test_cases:
            input = output.replace('@', '')
            self.sio.seek(0)
            self.sio.truncate()
            interpreter._pending_source_annotation = True
            interpreter._annotated_stream_write(input)
            self.assertEquals(self.sio.getvalue(), output)
            if '@' in output:
                self.assert_(not interpreter._pending_source_annotation)
            else:
                self.assert_(interpreter._pending_source_annotation)


class TestErrorTracebacks(TestCaseBase):

    # Regression test for http://www.zope.org/Collectors/Zope3-dev/697

    def test_define_slot_does_not_clobber_source_file_on_exception(self):
        m_program, m_macros = self._compile("""
            <div metal:define-macro="amacro">
              <div metal:define-slot="aslot">
              </div>
            </div>
            """, source_file='macros.pt')
        p_program, p_macros = self._compile("""
            <div metal:use-macro="amacro">
              <div metal:fill-slot="aslot">
                <tal:x replace="no_such_thing" />
              </div>
            </div>
            """, source_file='page.pt')
        engine = DummyEngine(macros=m_macros)
        interp = TALInterpreter(p_program, {}, engine, StringIO())
        # Expect TALExpressionError: unknown variable: 'no_such_thing'
        self.assertRaises(TALExpressionError, interp)
        # Now the engine should know where the error occurred
        self.assertEquals(engine.source_file, 'page.pt')
        self.assertEquals(engine.position, (4, 16))

    def test_define_slot_restores_source_file_if_no_exception(self):
        m_program, m_macros = self._compile("""
            <div metal:define-macro="amacro">
              <div metal:define-slot="aslot">
              </div>
              <tal:x replace="no_such_thing" />
            </div>
            """, source_file='macros.pt')
        p_program, p_macros = self._compile("""
            <div metal:use-macro="amacro">
              <div metal:fill-slot="aslot">
              </div>
            </div>
            """, source_file='page.pt')
        engine = DummyEngine(macros=m_macros)
        interp = TALInterpreter(p_program, {}, engine, StringIO())
        # Expect TALExpressionError: unknown variable: 'no_such_thing'
        self.assertRaises(TALExpressionError, interp)
        # Now the engine should know where the error occurred
        self.assertEquals(engine.source_file, 'macros.pt')
        self.assertEquals(engine.position, (5, 14))



def test_suite():
    suite = unittest.makeSuite(I18NErrorsTestCase)
    suite.addTest(unittest.makeSuite(MacroErrorsTestCase))
    suite.addTest(unittest.makeSuite(MacroExtendTestCase))
    suite.addTest(unittest.makeSuite(OutputPresentationTestCase))
    suite.addTest(unittest.makeSuite(ScriptTestCase))
    suite.addTest(unittest.makeSuite(I18NCornerTestCaseMessage))
    suite.addTest(unittest.makeSuite(UnusedExplicitDomainTestCase))
    suite.addTest(unittest.makeSuite(TestSourceAnnotations))
    suite.addTest(unittest.makeSuite(TestErrorTracebacks))

    # TODO: Deactivated test, since we have not found a solution for this and
    # it is a deep and undocumented HTML parser issue.
    # Fred is looking into this.
    #suite.addTest(unittest.makeSuite(MacroFunkyErrorTest))

    return suite

if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
