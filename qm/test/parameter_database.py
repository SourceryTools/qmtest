########################################################################
#
# File:   parameter_database.py
# Author: Stefan Seefeld
# Date:   2005-01-17
#
# Contents:
#   Test database that parametrizes another test database..
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

from qm.test.database import *
from qm.test.suite import *

########################################################################
# classes
########################################################################

class ParameterDatabase(Database):
    """A database that parametrizes another database. 'Parameter' in this
    context refers to any name that is used as a label, and which stands
    for a specific set of arguments passed to tests.

    The 'ParameterDatabase' class is abstract. Subclasses need to implement
    the '_GetParametersForTest' as well as the '_GetArgumentsForParameter'
    method.
    """

    class ImplicitSuite(Suite):
        """ImplicitSuite represents a suite obtained from a test and a set
        of parameters applied to it."""

        def __init__(self, db, suite_id):

            Suite.__init__(self, {},
                           qmtest_id = suite_id,
                           qmtest_database = db)


        def GetTestIds(self):

            database = self.GetDatabase()
            id = self.GetId()
            return map(lambda p, db = database, id = id: db.JoinLabels(id, p),
                       database._GetParametersForTest(id))


        def IsImplicit(self):

            return True


    class WrapperSuite(Suite):
        """As tests from the wrapped Database are mapped to suites, suites
        from the wrapped Database have to be recreated with all tests
        replaced by ImplicitSuite instances. Additionally, new (explicit)
        suites may be added."""

        def __init__(self, db, suite, suite_ids = None):
            """Take over suite_ids from the wrapped database but replace
            test_ids by suite_ids if there are parameters available for
            them."""

            Suite.__init__(self, {},
                           qmtest_id = suite.GetId(),
                           qmtest_database = db)
            self.__suite = suite
            self.__suite_ids = suite_ids or []


        def GetSuiteIds(self):

            suite_ids = self.__suite.GetSuiteIds()
            for t in self.__suite.GetTestIds():
                if self.GetDatabase()._GetParametersForTest(t):
                    suite_ids.append(t)
            return suite_ids + self.__suite_ids


        def GetTestIds(self):

            test_ids = []
            for t in self.__suite.GetTestIds():
                if not self.GetDatabase()._GetParametersForTest(t):
                    test_ids.append(t)
            return test_ids


        def IsImplicit(self):

            return self.__suite.IsImplicit()


        def GetAllTestAndSuiteIds(self):

            db = self.GetDatabase()
            orig_test_ids, suite_ids = self.__suite.GetAllTestAndSuiteIds()
            test_ids = []
            for test in orig_test_ids:
                parameters = db._GetParametersForTest(test)
                if parameters:
                    suite_ids.append(test)
                    test_ids.extend(map(lambda p, test=test, db=db:
                                        db.JoinLabels(test, p),
                                        parameters))
                else:
                    test_ids.append(test)
            return test_ids, suite_ids + self.__suite_ids


    class ParameterSuite(Suite):
        """ParameterSuite represents a suite obtained from applying a
        given parameter to a suite from the wrapped DB."""

        def __init__(self, database, suite, parameter):
            """Construct a ParameterSuite.

            database -- The database this suite refers to.

            suite -- The original suite this suite parametrizes.

            parameter -- The value for the parameter to apply to the suite."""

            Suite.__init__(self, {},
                           qmtest_id = database.JoinLabels(suite.GetId(),
                                                           parameter),
                           qmtest_database = database)
            self.__suite = suite
            self.__parameter = parameter


        def GetSuiteIds(self):
            """ParameterSuites contain ParameterSuites which wrap suites
            contained in the wrapped suite."""

            database = self.GetDatabase()
            return map(lambda id, db = database, p = self.__parameter:
                       db.JoinLabels(id, p), self.__suite.GetSuiteIds())


        def GetTestIds(self):
            """ParameterSuites contain Tests obtained by applying the given
            parameter set to the tests contained in the wrapped suite."""

            database = self.GetDatabase()
            return map(lambda id, db = database, p = self.__parameter:
                       db.JoinLabels(id, p), self.__suite.GetTestIds())


        def IsImplicit(self):

            return False


    def __init__(self, database, path, arguments):

        self.label_class = database.label_class
        Database.__init__(self, path, arguments)
        self.__db = database


    def GetWrappedDatabase(self):

        return self.__db
    

    def _GetParametersForTest(self, test_id):
        """Return a list of parameters that can be applied to the test
        'test_id'."""
        
        return []

    
    def _GetArgumentsForParameter(self, test_id, parameter):
        """Return the set of arguments for this parameter.

        'test_id' -- The test id to which the parameter belongs.

        'parameter' -- The parameter for which the arguments are queried.

        returns -- A dictionary containing the argument as name/value pairs."""

        return {}
    

    def GetTest(self, test_id):

        directory, basename = self.SplitLabel(test_id)

        if not self.HasTest(test_id):
            raise NoSuchTestError, test_id

        test = self.__db.GetTest(directory)
        # now generate a new test
        arguments = test.GetArguments()

        #override parameters
        arguments.update(self._GetArgumentsForParameter(directory, basename))
        return TestDescriptor(self, test_id, test.GetClassName(),
                              arguments)

    def HasTest(self, test_id):

        # If test_id is a parametrized test, its basename has to refer to
        # a parameter set and the directory to a test in the wrapped DB.
        #
        # Else basename must not be a parameter set, and test_id a test
        # in the wrapped DB.

        directory, basename = self.SplitLabel(test_id)

        return (basename in self._GetParametersForTest(directory)
                and self.__db.HasTest(directory)
                or self.__db.HasTest(test_id))


    def GetTestIds(self, directory="", scan_subdirs=1):

        # directory may be a test in the wrapped DB...
        if self.__db.HasTest(directory):
            ids = [directory]
        # ...or a directory, in which case we only take it into account
        # if scan_subdirs == 1.
        elif scan_subdirs:
            ids = self.__db.GetTestIds(directory, scan_subdirs)
        else:
            return []

        tests = []
        for p in self._GetParametersForTest(directory):
            tests += map(lambda x, p = p, db = self: db.JoinLabels(x, p),
                         ids)
        return tests


    def GetSuite(self, suite_id):

        # If suite_id refers to a suite in the WD, wrap it.
        if self.__db.HasSuite(suite_id):
            return ParameterDatabase.WrapperSuite(self,
                                                  self.__db.GetSuite(suite_id))
        
        # If suite_id refers to a test in the WD, parametrize it.
        elif self.__db.HasTest(suite_id):
            return ParameterDatabase.ImplicitSuite(self, suite_id)

        raise NoSuchSuiteError, suite_id


    def HasSuite(self, suite_id):

        directory, basename = self.SplitLabel(suite_id)
        return (basename in self._GetParametersForTest(directory)
                and self.__db.HasSuite(directory)
                or self.__db.HasSuite(suite_id)
                or self.__db.HasTest(suite_id))


    def GetSuiteIds(self, directory="", scan_subdirs=1):

        if self.__db.HasTest(directory):
            return []
        
        suite_ids = self.__db.GetSuiteIds(directory, scan_subdirs)
        test_ids = self.__db.GetTestIds(directory, scan_subdirs)
        param_ids = map(lambda p, d = directory, db = self:
                        db.JoinLabels(d, p),
                        self._GetParametersForTest(directory))

        # The set of all (non-recursive) suite ids is composed of the
        # original suite ids plus original test ids (now being suite ids)
        # as well as explicit suites obtained by combining the given
        # directory with all parameters.
        ids = suite_ids + test_ids + param_ids
        if not scan_subdirs:
            return ids
        else:
            # The set of all suite ids is composed of the set above plus
            # everything above combined with all parameters.
            expl_ids = []
            for p in self._GetParametersForTest(directory):
                expl_ids += map(lambda x, p = p, db = self:
                                db.JoinLabels(x, p), suite_ids + test_ids)
            return ids + expl_ids


    def GetResource(self, resource_id):

        return self.__db.GetResource(resource_id)


    def HasResource(self, resource_id):

        return self.__db.HasResource(resource_id)


    def GetResourceIds(self, directory="", scan_subdirs=1):

        if self.__db.HasTest(directory):
            return []

        return self.__db.GetResourceIds(directory, scan_subdirs)


    def GetIds(self, kind, directory="", scan_subdirs = 1):

        if kind == Database.TEST:
            return GetTestIds(directory, scan_subdirs)
        
        return self.__db.GetIds(kind, directory, scan_subdirs)


    def GetSubdirectories(self, directory):

        # GetSubdirectories returns the subdirectories of the given directory.
        # As this Database turns all tests from the wrapped Database into
        # ImplicitSuites, we have to account for them here.
        #
        # Further, while 'directory' has to be a directory when looked at it
        # from this Database, it may well be a test in the context of the wrapped
        # Database, in which case it can't have subdirectories.
        if self.__db.HasTest(directory):
            return []
        
        subdirs = self.__db.GetSubdirectories(directory)
        subdirs += [d[directory and len(directory) + 1:] # Remove common prefix.
                    for d in self.__db.GetTestIds(directory, False)]
        return subdirs


    def GetAttachmentStore(self):

        return self.__db.GetAttachmentStore()


    def GetClassPath(self):

        return self.__db.GetClassPath()


    def GetTestClassNames(self):

        return self.__db.GetTestClassNames()


    def GetResourceClassNames(self):

        return self.__db.GetResourceClassNames()

