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
"""Login/Password provider

$Id: loginpassword.py 26551 2004-07-15 07:06:37Z srichter $
"""
from zope.interface import implements
from interfaces import ILoginPassword

class LoginPassword(object):

    implements(ILoginPassword)

    def __init__(self, login, password):
        self.__login = login
        if login is None:
            self.__password = None
        else:
            self.__password = password or ""

    def getLogin(self):
        return self.__login

    def getPassword(self):
        return self.__password

    def needLogin(self, realm):
        pass
