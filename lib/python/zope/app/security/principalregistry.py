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
"""Global Authentication Utility or Principal Registry

$Id: principalregistry.py 69465 2006-08-14 12:49:46Z ctheune $
"""
from zope.interface import implements

from zope.app.authentication.interfaces import IPasswordManager
from zope.app.security.interfaces import PrincipalLookupError
from zope.app import zapi
from zope.security.interfaces import IPrincipal, IGroupAwarePrincipal
from zope.app.security import interfaces
from zope.app.container.contained import Contained, contained


class DuplicateLogin(Exception): pass
class DuplicateId(Exception): pass

class PrincipalRegistry(object):

    implements(interfaces.IAuthentication, interfaces.ILogout)

    # Methods implementing IAuthentication

    def authenticate(self, request):
        a = interfaces.ILoginPassword(request, None)
        if a is not None:
            login = a.getLogin()
            if login is not None:
                p = self.__principalsByLogin.get(login, None)
                if p is not None:
                    password = a.getPassword()
                    if p.validate(password):
                        return p
        return None

    __defaultid = None
    __defaultObject = None

    def defineDefaultPrincipal(self, id, title, description='',
                               principal=None):
        if id in self.__principalsById:
            raise DuplicateId(id)
        self.__defaultid = id
        if principal is None:
            principal = UnauthenticatedPrincipal(id, title, description)
        self.__defaultObject = contained(principal, self, id)
        return principal

    def unauthenticatedPrincipal(self):
        return self.__defaultObject

    def unauthorized(self, id, request):
        if id is None or id is self.__defaultid:
            a = interfaces.ILoginPassword(request)
            a.needLogin(realm="Zope")

    def getPrincipal(self, id):
        r = self.__principalsById.get(id)
        if r is None:
            if id == self.__defaultid:
                return self.__defaultObject
            raise PrincipalLookupError(id)
        return r

    def getPrincipalByLogin(self, login):
        return self.__principalsByLogin[login]

    def getPrincipals(self, name):
        name = name.lower()
        return [p for p in self.__principalsById.itervalues()
                  if p.title.lower().startswith(name) or
                     p.getLogin().lower().startswith(name)]

    def logout(self, request):
        # not supporting basic auth logout -- no such thing
        pass

    # Management methods

    def __init__(self):
        self.__principalsById = {}
        self.__principalsByLogin = {}

    def definePrincipal(self, principal, title, description='',
            login='', password='', passwordManagerName='Plain Text'):
        id=principal
        if login in self.__principalsByLogin:
            raise DuplicateLogin(login)

        if id in self.__principalsById or id == self.__defaultid:
            raise DuplicateId(id)

        p = Principal(id, title, description,
            login, password, passwordManagerName)
        p = contained(p, self, id)

        self.__principalsByLogin[login] = p
        self.__principalsById[id] = p

        return p

    def registerGroup(self, group):
        id = group.id
        if id in self.__principalsById or id == self.__defaultid:
            raise DuplicateId(id)

        self.__principalsById[group.id] = group

    def _clear(self):
        self.__init__()
        self.__defaultid = None
        self.__defaultObject = None

principalRegistry = PrincipalRegistry()

# Register our cleanup with Testing.CleanUp to make writing unit tests simpler.
from zope.testing.cleanup import addCleanUp
addCleanUp(principalRegistry._clear)
del addCleanUp

class PrincipalBase(Contained):

    def __init__(self, id, title, description):
        self.id = id
        self.title = title
        self.description = description
        self.groups = []

class Group(PrincipalBase):

    def getLogin(self):
        return '' # to make registry search happy

class Principal(PrincipalBase):

    implements(IGroupAwarePrincipal)

    def __init__(self, id, title, description, login,
            pw, pwManagerName="Plain Text"):
        super(Principal, self).__init__(id, title, description)
        self.__login = login
        self.__pwManagerName = pwManagerName
        self.__pw = pw

    def __getPasswordManager(self):
        return zapi.getUtility(IPasswordManager, self.__pwManagerName)

    def getLogin(self):
        return self.__login

    def validate(self, pw):
        pwManager = self.__getPasswordManager()
        return pwManager.checkPassword(self.__pw, pw)


class UnauthenticatedPrincipal(PrincipalBase):

    implements(interfaces.IUnauthenticatedPrincipal)

class UnauthenticatedGroup(Group):

    implements(interfaces.IUnauthenticatedGroup)

class AuthenticatedGroup(Group):

    implements(interfaces.IAuthenticatedGroup)

class EverybodyGroup(Group):

    implements(interfaces.IEveryoneGroup)

