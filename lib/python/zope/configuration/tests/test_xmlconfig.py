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
"""Test XML configuration (ZCML) machinery.

$Id: test_xmlconfig.py 37395 2005-07-23 23:24:37Z philikon $
"""
import unittest
import os
from zope.testing.doctestunit import DocTestSuite
from zope.configuration import xmlconfig, config
from zope.configuration.tests.samplepackage import foo
from pprint import PrettyPrinter, pprint


class FauxLocator(object):
  def __init__(self, file, line, column):
    self.file, self.line, self.column = file, line, column
  def getSystemId(self):
    return self.file
  def getLineNumber(self):
    return self.line
  def getColumnNumber(self):
    return self.column

class FauxContext(object):
  
  def setInfo(self, info):
    self.info = info
  def getInfo(self):
    return self.info
  def begin(self, name, data, info):
    self.begin_args = name, data
    self.info = info
  def end(self):
    self.end_called = 1

def path(*p):
    return os.path.join(os.path.dirname(__file__), *p)

def test_ConfigurationHandler_normal():
    """
    >>> context = FauxContext()
    >>> locator = FauxLocator('tests//sample.zcml', 1, 1)
    >>> handler = xmlconfig.ConfigurationHandler(context)
    >>> handler.setDocumentLocator(locator)

    >>> handler.startElementNS((u"ns", u"foo"), u"foo",
    ...                        {(u"xxx", u"splat"): u"splatv",
    ...                         (None, u"a"): u"avalue",
    ...                         (None, u"b"): u"bvalue",
    ...                        })
    >>> context.info
    File "tests//sample.zcml", line 1.1
    >>> from pprint import PrettyPrinter
    >>> pprint=PrettyPrinter(width=50).pprint
    >>> pprint(context.begin_args)
    ((u'ns', u'foo'),
     {'a': u'avalue', 'b': u'bvalue'})
    >>> getattr(context, "end_called", 0)
    0

    >>> locator.line, locator.column = 7, 16
    >>> handler.endElementNS((u"ns", u"foo"), u"foo")
    >>> context.info
    File "tests//sample.zcml", line 1.1-7.16
    >>> context.end_called
    1
    
    """

def test_ConfigurationHandler_err_start():
    """

    >>> class FauxContext(FauxContext):
    ...   def begin(self, *args):
    ...     raise AttributeError("xxx")
    
    >>> context = FauxContext()
    >>> locator = FauxLocator('tests//sample.zcml', 1, 1)
    >>> handler = xmlconfig.ConfigurationHandler(context)
    >>> handler.setDocumentLocator(locator)

    >>> try:
    ...   v = handler.startElementNS((u"ns", u"foo"), u"foo",
    ...                              {(u"xxx", u"splat"): u"splatv",
    ...                               (None, u"a"): u"avalue",
    ...                               (None, u"b"): u"bvalue",
    ...                              })
    ... except xmlconfig.ZopeXMLConfigurationError, v:
    ...   pass
    >>> print v
    File "tests//sample.zcml", line 1.1
        AttributeError: xxx
    
    """

def test_ConfigurationHandler_err_end():
    """

    >>> class FauxContext(FauxContext):
    ...   def end(self):
    ...     raise AttributeError("xxx")

    >>> context = FauxContext()
    >>> locator = FauxLocator('tests//sample.zcml', 1, 1)
    >>> handler = xmlconfig.ConfigurationHandler(context)
    >>> handler.setDocumentLocator(locator)

    >>> handler.startElementNS((u"ns", u"foo"), u"foo",
    ...                        {(u"xxx", u"splat"): u"splatv",
    ...                         (None, u"a"): u"avalue",
    ...                         (None, u"b"): u"bvalue",
    ...                        })

    >>> locator.line, locator.column = 7, 16
    >>> try:
    ...   v = handler.endElementNS((u"ns", u"foo"), u"foo")
    ... except xmlconfig.ZopeXMLConfigurationError, v:
    ...   pass
    >>> print v
    File "tests//sample.zcml", line 1.1-7.16
        AttributeError: xxx
    
    """

def clean_info_path(s):
    part1 = s[:6]
    part2 = s[6:s.find('"', 6)]
    part2 = part2[part2.find("tests"):]
    part2 = part2.replace(os.sep, '/')
    part3 = s[s.find('"', 6):].rstrip()
    return part1+part2+part3

def clean_path(s):
    s = s[s.find("tests"):]
    s = s.replace(os.sep, '/')
    return s

def test_processxmlfile():
    """

    >>> file = open(path("samplepackage", "configure.zcml"))
    >>> context = config.ConfigurationMachine()
    >>> xmlconfig.registerCommonDirectives(context)
    >>> xmlconfig.processxmlfile(file, context)

    >>> foo.data
    []

    >>> context.execute_actions()
    
    >>> data = foo.data.pop()

    >>> data.args
    (('x', 'blah'), ('y', 0))
    
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/configure.zcml", line 12.2-12.29

    >>> print clean_info_path(str(data.info))
    File "tests/samplepackage/configure.zcml", line 12.2-12.29
        <test:foo x="blah" y="0" />

    >>> data.package
    >>> data.basepath
    """

def test_file():
    """

    >>> file_name = path("samplepackage", "configure.zcml")
    >>> context = xmlconfig.file(file_name)
    
    >>> data = foo.data.pop()

    >>> data.args
    (('x', 'blah'), ('y', 0))
    
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/configure.zcml", line 12.2-12.29

    >>> print clean_info_path(str(data.info))
    File "tests/samplepackage/configure.zcml", line 12.2-12.29
        <test:foo x="blah" y="0" />

    >>> data.package
    >>> print clean_path(data.basepath)
    tests/samplepackage
    """

def test_include_by_package():
    """
    >>> context = config.ConfigurationMachine()
    >>> xmlconfig.registerCommonDirectives(context)
    >>> import zope.configuration.tests.samplepackage as package
    >>> xmlconfig.include(context, 'configure.zcml', package)
    >>> context.execute_actions()
    
    >>> data = foo.data.pop()

    >>> data.args
    (('x', 'blah'), ('y', 0))
    
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/configure.zcml", line 12.2-12.29

    >>> print clean_info_path(str(data.info))
    File "tests/samplepackage/configure.zcml", line 12.2-12.29
        <test:foo x="blah" y="0" />

    >>> data.package is package
    1
    
    >>> data.basepath[-13:]
    'samplepackage'

    >>> [clean_path(p) for p in data.includepath]
    ['tests/samplepackage/configure.zcml']


    """

# Not any more
##     Including the same file more than once produces an error:

##     >>> try:
##     ...   xmlconfig.include(context, 'configure.zcml', package)
##     ... except xmlconfig.ConfigurationError, e:
##     ...   'OK'
##     ...
##     'OK'

def test_include_by_file():
    """
    >>> context = config.ConfigurationMachine()
    >>> xmlconfig.registerCommonDirectives(context)
    >>> here = os.path.dirname(__file__)
    >>> path = os.path.join(here, "samplepackage", "foo.zcml")
    >>> xmlconfig.include(context, path)
    >>> context.execute_actions()
    
    >>> data = foo.data.pop()

    >>> data.args
    (('x', 'foo'), ('y', 2))
    
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/foo.zcml.in", line 12.2-12.28

    >>> print clean_info_path(str(data.info))
    File "tests/samplepackage/foo.zcml.in", line 12.2-12.28
        <test:foo x="foo" y="2" />

    >>> data.package
    
    >>> data.basepath[-13:]
    'samplepackage'

    >>> [clean_path(p) for p in data.includepath]
    ['tests/samplepackage/foo.zcml.in']
    """

def test_include_by_file_glob():
    """
    >>> context = config.ConfigurationMachine()
    >>> xmlconfig.registerCommonDirectives(context)
    >>> here = os.path.dirname(__file__)
    >>> path = os.path.join(here, "samplepackage/baz*.zcml")
    >>> xmlconfig.include(context, files=path)
    >>> context.execute_actions()
    
    >>> data = foo.data.pop()
    >>> data.args
    (('x', 'foo'), ('y', 3))
    
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/baz3.zcml", line 5.2-5.28

    >>> print clean_info_path(str(data.info))
    File "tests/samplepackage/baz3.zcml", line 5.2-5.28
        <test:foo x="foo" y="3" />
    
    >>> data.package
    
    >>> data.basepath[-13:]
    'samplepackage'

    >>> [clean_path(p) for p in data.includepath]
    ['tests/samplepackage/baz3.zcml']
    
    >>> data = foo.data.pop()
    >>> data.args
    (('x', 'foo'), ('y', 2))
    
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/baz2.zcml", line 5.2-5.28

    >>> print clean_info_path(str(data.info))
    File "tests/samplepackage/baz2.zcml", line 5.2-5.28
        <test:foo x="foo" y="2" />

    >>> data.package
    
    >>> data.basepath[-13:]
    'samplepackage'

    >>> [clean_path(p) for p in data.includepath]
    ['tests/samplepackage/baz2.zcml']
    """

def clean_actions(actions):
    return [
      {'discriminator': discriminator,
       'info': clean_info_path(`info`),
       'includepath': [clean_path(p) for p in includepath],
       }
      for (discriminator, callable, args, kw, includepath, info, order)
      in [config.expand_action(*action) for action in actions]
      ]

def clean_text_w_paths(error):
    r = []
    for line in unicode(error).split("\n"):
      line = line.rstrip()
      if not line:
        continue
      l = line.find('File "') 
      if l >= 0:
        line = line[:l] + clean_info_path(line[l:])
      r.append(line)
    return '\n'.join(r)

def test_includeOverrides():
    """
    When we have conflicting directives, we can resolve them if one of
    the conflicting directives was from a file that included all of
    the others.  The problem with this is that this requires that all
    of the overriding directives be in one file, typically the
    top-most including file. This isn't very convenient.  Fortunately,
    we can overcome this with the includeOverrides directive. Let's
    look at an example to see how this works.

    Look at the file bar.zcml. It includes bar1.zcml and bar2.zcml.
    bar2.zcml includes configure.zcml and has a foo
    directive. bar2.zcml includes bar21.zcml.  bar2.zcml has a foo
    directive that conflicts with one in bar1.zcml.  bar2.zcml also
    overrides a foo directive in bar21.zcml.  bar21.zcml has a foo
    directive that conflicts with one in in configure.zcml. Whew!

    Let's see what happens when we try to process bar.zcml.

    >>> context = config.ConfigurationMachine()
    >>> xmlconfig.registerCommonDirectives(context)
    
    >>> here = os.path.dirname(__file__)
    >>> path = os.path.join(here, "samplepackage", "bar.zcml")
    >>> xmlconfig.include(context, path)

    So far so good, let's look at the configuration actions:

    >>> pprint=PrettyPrinter(width=70).pprint
    >>> pprint(clean_actions(context.actions))
    [{'discriminator': (('x', 'blah'), ('y', 0)),
      'includepath': ['tests/samplepackage/bar.zcml',
                      'tests/samplepackage/bar1.zcml',
                      'tests/samplepackage/configure.zcml'],
      'info': 'File "tests/samplepackage/configure.zcml", line 12.2-12.29'},
     {'discriminator': (('x', 'blah'), ('y', 1)),
      'includepath': ['tests/samplepackage/bar.zcml',
                      'tests/samplepackage/bar1.zcml'],
      'info': 'File "tests/samplepackage/bar1.zcml", line 5.2-5.24'},
     {'discriminator': (('x', 'blah'), ('y', 0)),
      'includepath': ['tests/samplepackage/bar.zcml',
                      'tests/samplepackage/bar2.zcml',
                      'tests/samplepackage/bar21.zcml'],
      'info': 'File "tests/samplepackage/bar21.zcml", line 3.2-3.24'},
     {'discriminator': (('x', 'blah'), ('y', 2)),
      'includepath': ['tests/samplepackage/bar.zcml',
                      'tests/samplepackage/bar2.zcml',
                      'tests/samplepackage/bar21.zcml'],
      'info': 'File "tests/samplepackage/bar21.zcml", line 4.2-4.24'},
     {'discriminator': (('x', 'blah'), ('y', 2)),
      'includepath': ['tests/samplepackage/bar.zcml',
                      'tests/samplepackage/bar2.zcml'],
      'info': 'File "tests/samplepackage/bar2.zcml", line 5.2-5.24'},
     {'discriminator': (('x', 'blah'), ('y', 1)),
      'includepath': ['tests/samplepackage/bar.zcml',
                      'tests/samplepackage/bar2.zcml'],
      'info': 'File "tests/samplepackage/bar2.zcml", line 6.2-6.24'}]
    
    As you can see, there are a number of conflicts (actions with the same
    discriminator).  Some of these can be resolved, but many can't, as
    we'll find if we try to execuse the actions:

    >>> try:
    ...    v = context.execute_actions()
    ... except config.ConfigurationConflictError, v:
    ...    pass
    >>> print clean_text_w_paths(str(v))
    Conflicting configuration actions
      For: (('x', 'blah'), ('y', 0))
        File "tests/samplepackage/configure.zcml", line 12.2-12.29
            <test:foo x="blah" y="0" />
        File "tests/samplepackage/bar21.zcml", line 3.2-3.24
            <foo x="blah" y="0" />
      For: (('x', 'blah'), ('y', 1))
        File "tests/samplepackage/bar1.zcml", line 5.2-5.24
            <foo x="blah" y="1" />
        File "tests/samplepackage/bar2.zcml", line 6.2-6.24
            <foo x="blah" y="1" />

    Note that the conflicts for (('x', 'blah'), ('y', 2)) aren't
    included in the error because they could be resolved.

    Let's try this again using includeOverrides.  We'll include
    baro.zcml which includes bar2.zcml as overrides.

    >>> context = config.ConfigurationMachine()
    >>> xmlconfig.registerCommonDirectives(context)
    >>> path = os.path.join(here, "samplepackage", "baro.zcml")
    >>> xmlconfig.include(context, path)

    Now, if we look at the actions:
    
    >>> pprint(clean_actions(context.actions))
    [{'discriminator': (('x', 'blah'), ('y', 0)),
      'includepath': ['tests/samplepackage/baro.zcml',
                      'tests/samplepackage/bar1.zcml',
                      'tests/samplepackage/configure.zcml'],
      'info': 'File "tests/samplepackage/configure.zcml", line 12.2-12.29'},
     {'discriminator': (('x', 'blah'), ('y', 1)),
      'includepath': ['tests/samplepackage/baro.zcml',
                      'tests/samplepackage/bar1.zcml'],
      'info': 'File "tests/samplepackage/bar1.zcml", line 5.2-5.24'},
     {'discriminator': (('x', 'blah'), ('y', 0)),
      'includepath': ['tests/samplepackage/baro.zcml'],
      'info': 'File "tests/samplepackage/bar21.zcml", line 3.2-3.24'},
     {'discriminator': (('x', 'blah'), ('y', 2)),
      'includepath': ['tests/samplepackage/baro.zcml'],
      'info': 'File "tests/samplepackage/bar2.zcml", line 5.2-5.24'},
     {'discriminator': (('x', 'blah'), ('y', 1)),
      'includepath': ['tests/samplepackage/baro.zcml'],
      'info': 'File "tests/samplepackage/bar2.zcml", line 6.2-6.24'}]

    We see that:

    - The conflicting actions between bar2.zcml and bar21.zcml have
      been resolved, and

    - The remaining (after conflict resolution) actions from bar2.zcml
      and bar21.zcml have the includepath that they would have if they
      were defined in baro.zcml and this override the actions from
      bar1.zcml and configure.zcml.

    We can now execute the actions without problem, since the
    remaining conflicts are resolvable:

    >>> context.execute_actions()

    We should now have three entries in foo.data:

    >>> len(foo.data)
    3

    >>> data = foo.data.pop(0)
    >>> data.args
    (('x', 'blah'), ('y', 0))
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/bar21.zcml", line 3.2-3.24
    
    >>> data = foo.data.pop(0)
    >>> data.args
    (('x', 'blah'), ('y', 2))
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/bar2.zcml", line 5.2-5.24
    
    >>> data = foo.data.pop(0)
    >>> data.args
    (('x', 'blah'), ('y', 1))
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/bar2.zcml", line 6.2-6.24


    We expect the exact same results when using includeOverrides with
    the ``files`` argument instead of the ``file`` argument.  The
    baro2.zcml file uses the former:

    >>> context = config.ConfigurationMachine()
    >>> xmlconfig.registerCommonDirectives(context)
    >>> path = os.path.join(here, "samplepackage", "baro2.zcml")
    >>> xmlconfig.include(context, path)

    Actions look like above:

    >>> pprint(clean_actions(context.actions))
    [{'discriminator': (('x', 'blah'), ('y', 0)),
      'includepath': ['tests/samplepackage/baro2.zcml',
                      'tests/samplepackage/bar1.zcml',
                      'tests/samplepackage/configure.zcml'],
      'info': 'File "tests/samplepackage/configure.zcml", line 12.2-12.29'},
     {'discriminator': (('x', 'blah'), ('y', 1)),
      'includepath': ['tests/samplepackage/baro2.zcml',
                      'tests/samplepackage/bar1.zcml'],
      'info': 'File "tests/samplepackage/bar1.zcml", line 5.2-5.24'},
     {'discriminator': (('x', 'blah'), ('y', 0)),
      'includepath': ['tests/samplepackage/baro2.zcml'],
      'info': 'File "tests/samplepackage/bar21.zcml", line 3.2-3.24'},
     {'discriminator': (('x', 'blah'), ('y', 2)),
      'includepath': ['tests/samplepackage/baro2.zcml'],
      'info': 'File "tests/samplepackage/bar2.zcml", line 5.2-5.24'},
     {'discriminator': (('x', 'blah'), ('y', 1)),
      'includepath': ['tests/samplepackage/baro2.zcml'],
      'info': 'File "tests/samplepackage/bar2.zcml", line 6.2-6.24'}]

    >>> context.execute_actions()
    >>> len(foo.data)
    3
    >>> del foo.data[:]

    """

def test_XMLConfig():
    """Test processing a configuration file.

    We'll use the same example from test_includeOverrides:

    >>> here = os.path.dirname(__file__)
    >>> path = os.path.join(here, "samplepackage", "baro.zcml")

    First, process the configuration file:
    
    >>> x = xmlconfig.XMLConfig(path)

    Second, call the resulting object to process the actions:

    >>> x()

    And verify the data as above:

    >>> len(foo.data)
    3
    
    >>> data = foo.data.pop(0)
    >>> data.args
    (('x', 'blah'), ('y', 0))
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/bar21.zcml", line 3.2-3.24
    
    >>> data = foo.data.pop(0)
    >>> data.args
    (('x', 'blah'), ('y', 2))
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/bar2.zcml", line 5.2-5.24
    
    >>> data = foo.data.pop(0)
    >>> data.args
    (('x', 'blah'), ('y', 1))
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/bar2.zcml", line 6.2-6.24
    
    Finally, clean up.

    >>> from zope.testing.cleanup import CleanUp
    >>> CleanUp().cleanUp()
    """

def test_XMLConfig_w_module():
    """Test processing a configuration file for a module.

    We'll use the same example from test_includeOverrides:

    >>> import zope.configuration.tests.samplepackage as module

    First, process the configuration file:
    
    >>> x = xmlconfig.XMLConfig("baro.zcml", module)

    Second, call the resulting object to process the actions:

    >>> x()

    And verify the data as above:

    >>> len(foo.data)
    3
    
    >>> data = foo.data.pop(0)
    >>> data.args
    (('x', 'blah'), ('y', 0))
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/bar21.zcml", line 3.2-3.24
    
    >>> data = foo.data.pop(0)
    >>> data.args
    (('x', 'blah'), ('y', 2))
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/bar2.zcml", line 5.2-5.24
    
    >>> data = foo.data.pop(0)
    >>> data.args
    (('x', 'blah'), ('y', 1))
    >>> print clean_info_path(`data.info`)
    File "tests/samplepackage/bar2.zcml", line 6.2-6.24
    
    Finally, clean up.

    >>> from zope.testing.cleanup import CleanUp
    >>> CleanUp().cleanUp()
    """
    


def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.configuration.xmlconfig'),
        DocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
