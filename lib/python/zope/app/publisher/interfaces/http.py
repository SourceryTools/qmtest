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
"""Zope's HTTP-specific Publisher interfaces.

$Id: http.py 25177 2004-06-02 13:17:31Z jim $
"""
from zope.component.interfaces import IPresentation
from zope.component.interfaces import IView


class IHTTPPresentation(IPresentation):
    """HTTP presentations are for interaction with users using Web HTTPs
    """

class IHTTPView(IHTTPPresentation, IView):
    "HTTP View"


class ILogin(IHTTPView):
    """A simple login interface."""

    def login():
        """Login the user.

        This method should generate some sort of UI to request the username
        and password.
        """


class ILogout(IHTTPView):
    """A simple logout interface."""

    def logout():
        """Logout the user.

        This can mean different things. For example, when dealing with
        cookie-based logins (browser), then it simply means deleting the
        cookie. If we deal with HTTP Authentication, we just want to send
        another challenge.
        """
