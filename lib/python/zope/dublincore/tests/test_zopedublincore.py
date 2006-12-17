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
"""Test Zope's Dublin Core implementation

$Id: test_zopedublincore.py 66902 2006-04-12 20:16:30Z philikon $
"""

from unittest import TestCase, TestSuite, main, makeSuite

class Test(TestCase):

    def testImplementa(self):
        from zope.interface.verify import verifyObject
        from zope.dublincore.interfaces import IZopeDublinCore
        verifyObject(IZopeDublinCore, self.dc)

    def _Test__new(self):
        from zope.dublincore.zopedublincore import ZopeDublinCore
        return ZopeDublinCore()

    def setUp(self):
        self.dc = self._Test__new()

    def __testGetQualified(self, name, values):
        ovalues = getattr(self.dc, 'getQualified'+name)()

        ivalues = list(values)
        ivalues.sort()
        ovalues = list(ovalues)
        ovalues.sort()
        self.assertEqual(ovalues, ivalues)

    def __testQualified(self, name,
                        values = [
                           (u'', u'blah blah'),
                           (u'old', u'bleep bleep'),
                           (u'old', u'bleep bleep \u1111'),
                           (u'foo\u1111', u'bleep bleep'),
                           ]
                        ):
        getattr(self.dc, 'setQualified'+name)(values)
        self.__testGetQualified(name, values)

    def testOtherQualified(self):
        for name in ('Sources', 'Relations', 'Coverages'):
            self.__testQualified(name)


    def testScalars(self):
        for qname, mname, pname in (
            ('Titles', 'Title', 'title'),
            ('Descriptions', 'Description', 'description'),
            ('Publishers', 'Publisher', 'publisher'),
            ('Types', 'Type', 'type'),
            ('Formats', 'Format', 'format'),
            ('Identifiers', 'Identifier', 'identifier'),
            ('Languages', 'Language', 'language'),
            ('Rights', 'Rights', 'rights'),
            ):
            self.__testQualified(qname)
            dc = self.dc
            self.assertEqual(getattr(dc, pname), u'blah blah')
            self.assertEqual(getattr(dc, mname)(), u'blah blah')

            self.assertRaises(Exception, setattr, dc, pname, 'foo')
            setattr(dc, pname, u'foo')
            self.assertEqual(getattr(dc, pname), u'foo')
            self.assertEqual(getattr(dc, mname)(), u'foo')
            self.__testGetQualified(qname,
                                    [
                                       (u'', u'foo'),
                                       (u'old', u'bleep bleep'),
                                       (u'old', u'bleep bleep \u1111'),
                                       (u'foo\u1111', u'bleep bleep'),
                                       ]
                                    )

    def testSequences(self):
        for qname, mname, pname in (
            ('Creators', 'Creator', 'creators'),
            ('Subjects', 'Subject', 'subjects'),
            ('Contributors', 'Contributors', 'contributors'),
            ):
            self.__testQualified(qname, [
                                           (u'', u'foo'),
                                           (u'', u'bar'),
                                           (u'', u'baz'),
                                           (u'', u'baz\u1111'),
                                           (u'old', u'bleep bleep'),
                                           (u'old', u'bleep bleep \u1111'),
                                           (u'foo\u1111', u'bleep bleep'),
                                       ]
                                 )
            dc = self.dc

            v = getattr(dc, pname)
            v = list(v)
            v.sort()
            self.assertEqual(v, [u'bar', u'baz', u'baz\u1111', u'foo'])

            v = getattr(dc, mname)()
            v = list(v)
            v.sort()
            self.assertEqual(v, [u'bar', u'baz', u'baz\u1111', u'foo'])


            self.assertRaises(Exception, setattr, dc, pname, 'foo')
            self.assertRaises(Exception, setattr, dc, pname, ['foo'])

            setattr(dc, pname, [u'high', u'low', u'spam', u'eggs', u'ham', ])

            v = getattr(dc, pname)
            v = list(v)
            v.sort()
            self.assertEqual(v, [u'eggs', u'ham', u'high', u'low', u'spam'])

            v = getattr(dc, mname)()
            v = list(v)
            v.sort()
            self.assertEqual(v, [u'eggs', u'ham', u'high', u'low', u'spam'])

            self.__testGetQualified(qname,
                                    [
                                       (u'', u'high'),
                                       (u'', u'low'),
                                       (u'', u'spam'),
                                       (u'', u'eggs'),
                                       (u'', u'ham'),
                                       (u'old', u'bleep bleep'),
                                       (u'old', u'bleep bleep \u1111'),
                                       (u'foo\u1111', u'bleep bleep'),
                                       ]
                                    )



    def testDates(self):
        self.__testQualified('Dates', [
            (u'', u'1990-01-01'),
            (u'Created', u'1980-10-01T23:11:10-04:00'),
            (u'Modified', u'2002-10-01T12:09:22-04:00'),
            (u'Effective', u'2002-10-09T00:00:00-04:00'),
            (u'Expires', u'2002-10-16T00:00:00-04:00'),
            (u'xxx', u'2000-07-04'),
            (u'xxx', u'2001-12-31'),
            (u'foo \u1111', u'2001-12-31'),
            ])

        from zope.datetime import parseDatetimetz

        dc = self.dc
        self.assertEqual(dc.created,
                         parseDatetimetz('1980-10-01T23:11:10-04:00'))
        self.assertEqual(dc.modified,
                         parseDatetimetz('2002-10-01T12:09:22-04:00'))
        self.assertEqual(dc.effective,
                         parseDatetimetz('2002-10-09T00:00:00-04:00'))
        self.assertEqual(dc.expires,
                         parseDatetimetz('2002-10-16T00:00:00-04:00'))

        self.assertEqual(dc.Date(), u'1990-01-01')
        self.assertEqual(dc.CreationDate(), u'1980-10-01T23:11:10-04:00')
        self.assertEqual(dc.ModificationDate(), u'2002-10-01T12:09:22-04:00')
        self.assertEqual(dc.EffectiveDate(), u'2002-10-09T00:00:00-04:00')
        self.assertEqual(dc.ExpirationDate(), u'2002-10-16T00:00:00-04:00')


        dt = parseDatetimetz('2002-10-03T14:51:55-04:00')

        dc.modified = dt

        self.assertRaises(Exception, setattr, dc, 'modified', 'foo')

        modified = [qv[1]
                    for qv in dc.getQualifiedDates()
                    if qv[0] == u'Modified']

        self.failIf(len(modified) != 1, "should be only one: %r" % modified)

        self.assertEqual(parseDatetimetz(modified[0]), dt)

        modified = dc.ModificationDate()
        self.assertEqual(parseDatetimetz(modified), dt)


def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
