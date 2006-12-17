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
"""Make assertions about permissions needed to access class instances
attributes

$Id: protectclass.py 26696 2004-07-23 08:20:41Z hdima $
"""
from zope.security.checker import defineChecker, getCheckerForInstancesOf
from zope.security.checker import Checker, CheckerPublic


def protectName(class_, name, permission):
    """Set a permission on a particular name."""

    checker = getCheckerForInstancesOf(class_)
    if checker is None:
        checker = Checker({}, {})
        defineChecker(class_, checker)

    if permission == 'zope.Public':
        # Translate public permission to CheckerPublic
        permission = CheckerPublic

    # We know a dictionary was used because we set it
    protections = checker.get_permissions
    protections[name] = permission

def protectSetAttribute(class_, name, permission):
    """Set a permission on a particular name."""

    checker = getCheckerForInstancesOf(class_)
    if checker is None:
        checker = Checker({}, {})
        defineChecker(class_, checker)

    if permission == 'zope.Public':
        # Translate public permission to CheckerPublic
        permission = CheckerPublic

    # We know a dictionary was used because we set it
    # Note however, that if a checker was created manually
    # and the caller used say NamesChecker or MultiChecker,
    # then set_permissions may be None here as Checker
    # defaults a missing set_permissions parameter to None.
    # Jim says this doensn't happens with the C version of the
    # checkers because they use a 'shared dummy dict'.
    protections = checker.set_permissions
    protections[name] = permission

def protectLikeUnto(class_, like_unto):
    """Use the protections from like_unto for class_"""

    unto_checker = getCheckerForInstancesOf(like_unto)
    if unto_checker is None:
        return

    # We know a dictionary was used because we set it
    # Note however, that if a checker was created manually
    # and the caller used say NamesChecker or MultiChecker,
    # then set_permissions may be None here as Checker
    # defaults a missing set_permissions parameter to None.
    # Jim says this doensn't happens with the C version of the
    # checkers because they use a 'shared dummy dict'.
    unto_get_protections = unto_checker.get_permissions
    unto_set_protections = unto_checker.set_permissions

    checker = getCheckerForInstancesOf(class_)
    if checker is None:
        checker = Checker({}, {})
        defineChecker(class_, checker)

    get_protections = checker.get_permissions
    for name in unto_get_protections:
        get_protections[name] = unto_get_protections[name]

    set_protections = checker.set_permissions
    for name in unto_set_protections:
        set_protections[name] = unto_set_protections[name]
