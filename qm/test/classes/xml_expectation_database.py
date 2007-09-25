########################################################################
#
# File:   xml_expectation_database.py
# Author: Stefan Seefeld
# Date:   2007-09-18
#
# Contents:
#   QMTest XMLExpectationDatabase extension class.
#
# Copyright (c) 2007 by CodeSourcery, Inc.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.fields import TextField
from qm.test.expectation_database import ExpectationDatabase
from qm.test.result import Result
from qm.test.base import load_results
from qm.xmlutil import *
import re

########################################################################
# Classes
########################################################################

class XMLExpectationDatabase(ExpectationDatabase):
    """An 'XMLExpectationDatabase' reads expectations from
    an XML file."""

    file_name = TextField()


    def __init__(self, **args):

        super(XMLExpectationDatabase, self).__init__(**args)
        self._expectations = []
        document = load_xml(open(self.file_name))
        root = document.documentElement
        for e in root.getElementsByTagName('expectation'):
            test_id = e.getAttribute('test_id')
            outcome = {'pass':Result.PASS,
                       'fail':Result.FAIL,}[e.getAttribute('outcome')]
            filters = {}
            for a in e.getElementsByTagName('annotation'):
                filters[a.getAttribute('name')] = a.getAttribute('value')
            description = e.getElementsByTagName('description')
            if description: description = get_dom_text(description[0])
            self._expectations.append((test_id, outcome, filters, description))


    def Lookup(self, test_id):

        
        outcome, description = Result.PASS, ''
        for rule_id, rule_outcome, rule_annotations, rule_description in self._expectations:
            if re.match(rule_id, test_id):
                match = True
                for a in rule_annotations.iteritems():
                    if (a[0] not in self.testrun_parameters or
                        not re.match(a[1], self.testrun_parameters[a[0]])):
                        match = False
                if match:
                    outcome = rule_outcome
                    description = rule_description
        return Result(Result.TEST, test_id, outcome,
                      annotations={'description':description})
