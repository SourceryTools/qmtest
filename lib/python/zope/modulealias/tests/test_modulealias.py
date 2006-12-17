##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Module Alias Tests

$Id$
"""
import unittest
import sys
import warnings
from zope.configuration import xmlconfig
from zope.configuration.config import ConfigurationContext
# math is imported as an example module to test with
import math

stuff = """
<configure
    xmlns="http://namespaces.zope.org/zope"
    i18n_domain="zope"
    >

  <include package="zope.modulealias" file="meta.zcml"/>

  <modulealias module="unittest" alias="unittest_alias"/>

</configure>
"""


class Test(unittest.TestCase):

    def setUp(self):
        self.keys = sys.modules.keys()
        self.__showwarning = warnings.showwarning
        warnings.showwarning = lambda *a, **k: None

    def tearDown(self):
        warnings.showwarning = self.__showwarning
        keys = sys.modules.keys()
        for key in keys:
            if key not in self.keys:
                del sys.modules[key]

    def test_definemodulealias(self):
        context = ConfigurationContext()
        from zope.modulealias.metaconfigure import alias_module
        alias_module(module='unittest', alias='unittest_alias',
                     context=context)
        self.assert_('unittest_alias' in sys.modules.keys())
        self.assertEqual(sys.modules['unittest_alias'],sys.modules['unittest'])

    def test_cantoverride(self):
        context = ConfigurationContext()
        from zope.modulealias.metaconfigure import alias_module
        from zope.modulealias.metaconfigure import ModuleAliasException
        self.assertRaises(ModuleAliasException, alias_module,
                          module='unittest', alias='zope.modulealias.tests',
                          context=context)

    def test_samemodule_doesntfail(self):
        context = ConfigurationContext()
        from zope.modulealias.metaconfigure import alias_module
        self.assert_('math' in sys.modules)
        sys.modules['zope.modulealias.tests.test_modulealias.math'] = math
        alias_module(module='zope.modulealias.tests.test_modulealias.math',
                     alias='math',
                     context=context)

    def test_module_not_imported(self):
        context = ConfigurationContext()
        from zope.modulealias.metaconfigure import alias_module
        m1 = 'zope.modulealias.tests.dummymodule'
        m2 = 'zope.modulealias.tests.dummymodule2'
        self.assert_(m1 not in sys.modules)
        alias_module(module=m1, alias=m2, context=context)
        self.assert_(m1 in sys.modules)
        self.assert_(sys.modules[m1] is sys.modules[m2])
        # Clean up after ourselves, so the test can be run in a loop:
        del sys.modules[m1]
        del sys.modules[m2]
        # Normal import causes the dummymodule to appear in the
        # package module as well, so remove it there, since
        # ConfigurationContext.resolve() will prefer that to
        # sys.modules.
        from zope.modulealias import tests
        del tests.dummymodule

    def test_nonmodule_alias(self):
        from zope.modulealias.metaconfigure import ModuleAliasException
        context = ConfigurationContext()
        from zope.modulealias.metaconfigure import alias_module
        m1 = 'zope.modulealias.tests.test_modulealias.Test'
        m2 = 'zope.modulealias.tests.test_modulealias.Test2'
        self.assertRaises(ModuleAliasException,
                          alias_module, module=m1, alias=m2, context=context,
                          )
                          
    def test_zcml(self):
        context = xmlconfig.string(stuff)
        self.assert_('unittest_alias' in sys.modules.keys())
        self.assertEqual(sys.modules['unittest_alias'],sys.modules['unittest'])

    
                     
def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
