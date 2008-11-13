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
"""Pluggable Authentication utility implementation.

BBB: ENTIRE PACKAGE IS DEPRECATED!!! 12/05/2004 Gone in 3.3

$Id: __init__.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import random
import sys
import time
import random
import zope.schema
from warnings import warn
from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree

from zope.interface import implements
from zope.component.interfaces import IViewFactory
from zope.deprecation import deprecated
from zope.traversing.api import getPath
from zope.location import locate

from zope.app import zapi
from zope.app.component import queryNextUtility
from zope.app.container.interfaces import IOrderedContainer
from zope.app.container.interfaces import IContainerNamesContainer, INameChooser
from zope.app.container.interfaces import IContained
from zope.app.container.constraints import ItemTypePrecondition
from zope.app.container.constraints import ContainerTypesConstraint
from zope.app.container.contained import Contained, setitem, uncontained
from zope.app.container.ordered import OrderedContainer
from zope.app.security.interfaces import ILoginPassword, IAuthentication
from zope.app.security.interfaces import PrincipalLookupError

from interfaces import IUserSchemafied, IPluggableAuthentication
from interfaces import IPrincipalSource, ILoginPasswordPrincipalSource
from interfaces import IContainedPrincipalSource, IContainerPrincipalSource

def gen_key():
    """Return a random int (1, MAXINT), suitable for use as a `BTree` key."""

    return random.randint(0, sys.maxint-1)

class PluggableAuthentication(OrderedContainer):

    implements(IPluggableAuthentication, IOrderedContainer)

    def __init__(self, earmark=None, hide_deprecation_warning=False):
        if not hide_deprecation_warning:
            warn("The `pluggableauth` module has been deprecated in favor of "
                 "the new `pas` code, which is much more modular and powerful.",
                 DeprecationWarning, 2)        
        self.earmark = earmark
        # The earmark is used as a token which can uniquely identify
        # this authentication utility instance even if the utility moves
        # from place to place within the same context chain or is renamed.
        # It is included in principal ids of principals which are obtained
        # from this auth utility, so code which dereferences a principal
        # (like getPrincipal of this auth utility) needs to take the earmark
        # into account. The earmark cannot change once it is assigned.  If it
        # does change, the system will not be able to dereference principal
        # references which embed the old earmark.
        OrderedContainer.__init__(self)

    def authenticate(self, request):
        """ See `IAuthentication`. """
        for ps_key, ps in self.items():
            loginView = zapi.queryMultiAdapter((ps, request), name="login")
            if loginView is not None:
                principal = loginView.authenticate()
                if principal is not None:
                    return principal

        next = queryNextUtility(self, IAuthentication, None)
        if next is not None:
            return next.authenticate(request)

        return None

    def unauthenticatedPrincipal(self):
        # It's safe to assume that the global auth utility will
        # provide an unauthenticated principal, so we won't bother.
        return None

    def unauthorized(self, id, request):
        """ See `IAuthentication`. """

        next = queryNextUtility(self, IAuthentication)
        if next is not None:
            return next.unauthorized(id, request)

        return None

    def getPrincipal(self, id):
        """ See `IAuthentication`.

        For this implementation, an `id` is a string which can be
        split into a 3-tuple by splitting on tab characters.  The
        three tuple consists of (`auth_utility_earmark`,
        `principal_source_id`, `principal_id`).

        In the current strategy, the principal sources that are members
        of this authentication utility cannot be renamed; if they are,
        principal references that embed the old name will not be
        dereferenceable.

        """

        next = None

        try:
            auth_svc_earmark, principal_src_id, principal_id = id.split('\t',2)
        except (TypeError, ValueError, AttributeError):
            auth_svc_earmark, principal_src_id, principal_id = None, None, None
            next = queryNextUtility(self, IAuthentication)

        if auth_svc_earmark != self.earmark:
            # this is not our reference because its earmark doesnt match ours
            next = queryNextUtility(self, IAuthentication)

        if next is not None:
            return next.getPrincipal(id)

        source = self.get(principal_src_id)
        if source is None:
            raise PrincipalLookupError(principal_src_id)
        return source.getPrincipal(id)

    def getPrincipals(self, name):
        """ See `IAuthentication`. """

        for ps_key, ps in self.items():
            for p in ps.getPrincipals(name):
                yield p

        next = queryNextUtility(self, IAuthentication)
        if next is not None:
            for p in next.getPrincipals(name):
                yield p

    def addPrincipalSource(self, id, principal_source):
        """ See `IPluggableAuthentication`.

        >>> pas = PluggableAuthentication(None, True)
        >>> sps = BTreePrincipalSource()
        >>> pas.addPrincipalSource('simple', sps)
        >>> sps2 = BTreePrincipalSource()
        >>> pas.addPrincipalSource('not_quite_so_simple', sps2)
        >>> pas.keys()
        ['simple', 'not_quite_so_simple']
        """

        if not IPrincipalSource.providedBy(principal_source):
            raise TypeError("Source must implement IPrincipalSource")
        locate(principal_source, self, id)
        self[id] = principal_source        

    def removePrincipalSource(self, id):
        """ See `IPluggableAuthentication`.

        >>> pas = PluggableAuthentication(None, True)
        >>> sps = BTreePrincipalSource()
        >>> pas.addPrincipalSource('simple', sps)
        >>> sps2 = BTreePrincipalSource()
        >>> pas.addPrincipalSource('not_quite_so_simple', sps2)
        >>> sps3 = BTreePrincipalSource()
        >>> pas.addPrincipalSource('simpler', sps3)
        >>> pas.keys()
        ['simple', 'not_quite_so_simple', 'simpler']
        >>> pas.removePrincipalSource('not_quite_so_simple')
        >>> pas.keys()
        ['simple', 'simpler']
        """

        del self[id]


# BBB: Gone in 3.3.
PluggableAuthenticationService = PluggableAuthentication

deprecated('PluggableAuthenticationService',
           'The pluggable authentication service has been deprecated in '
           'favor of authentication (aka PAS). This reference will be gone in '
           'Zope 3.3.')

def PluggableAuthenticationAddSubscriber(self, event):
    r"""Generates an earmark if one is not provided.

    Define a stub for `PluggableAuthentication`

    >>> from zope.traversing.interfaces import IPhysicallyLocatable
    >>> class PluggableAuthStub(object):
    ...     implements(IPhysicallyLocatable)
    ...     def __init__(self, earmark=None):
    ...         self.earmark = earmark
    ...     def getName(self):
    ...         return 'PluggableAuthName'

    The subscriber generates an earmark for the auth utility if one is not
    set in the init.

    >>> stub = PluggableAuthStub()
    >>> event = ''
    >>> PluggableAuthenticationAddSubscriber(stub, event)
    >>> stub.earmark is not None
    True

    The subscriber does not modify an earmark for the auth utility if one
    exists already.

    >>> earmark = 'my sample earmark'
    >>> stub = PluggableAuthStub(earmark=earmark)
    >>> event = ''
    >>> PluggableAuthenticationAddSubscriber(stub, event)
    >>> stub.earmark == earmark
    True
    """
    if self.earmark is None:
        # we manufacture what is intended to be a globally unique
        # earmark if one is not provided in __init__
        myname = zapi.name(self)
        rand_id = gen_key()
        t = int(time.time())
        self.earmark = '%s-%s-%s' % (myname, rand_id, t)
                

class IBTreePrincipalSource(
    ILoginPasswordPrincipalSource,
    IContainerPrincipalSource,
    IContainedPrincipalSource,
    INameChooser,
    IContainerNamesContainer,
    ):

    def __setitem__(name, principal):
        """Add a `principal`

        The name must be the same as the principal login
        """

    __setitem__.precondition  = ItemTypePrecondition(IUserSchemafied)

class IBTreePrincipalSourceContained(IContained):

    __parent__ = zope.schema.Field(
        constraint = ContainerTypesConstraint(IBTreePrincipalSource),
        )

class BTreePrincipalSource(Persistent, Contained):
    """An efficient, scalable provider of Authentication Principals."""

    implements(IBTreePrincipalSource)

    def __init__(self):

        self._principals_by_number = IOBTree()
        self._numbers_by_login = OIBTree()

    # IContainer-related methods

    def __delitem__(self, login):
        """ See `IContainer`.

        >>> sps = BTreePrincipalSource()
        >>> prin = SimplePrincipal('fred', 'fred', '123')
        >>> sps['fred'] = prin
        >>> int(sps.get('fred') == prin)
        1
        >>> del sps['fred']
        >>> int(sps.get('fred') == prin)
        0

        """
        number = self._numbers_by_login[login]

        uncontained(self._principals_by_number[number], self, login)
        del self._principals_by_number[number]
        del self._numbers_by_login[login]

    def __setitem__(self, login, ob):
        """ See `IContainerNamesContainer`

        >>> sps = BTreePrincipalSource()
        >>> prin = SimplePrincipal('gandalf', 'shadowfax')
        >>> sps['doesntmatter'] = prin
        >>> sps.get('doesntmatter')
        """
        setitem(self, self.__setitem, login, ob)

    def __setitem(self, login, ob):
        store = self._principals_by_number

        key = gen_key()
        while not store.insert(key, ob):
            key = gen_key()

        ob.id = key
        self._numbers_by_login[ob.login] = key

    def keys(self):
        """ See `IContainer`.

        >>> sps = BTreePrincipalSource()
        >>> sps.keys()
        []
        >>> prin = SimplePrincipal('arthur', 'tea')
        >>> sps['doesntmatter'] = prin
        >>> sps.keys()
        ['arthur']
        >>> prin = SimplePrincipal('ford', 'towel')
        >>> sps['doesntmatter'] = prin
        >>> sps.keys()
        ['arthur', 'ford']
        """

        return list(self._numbers_by_login.keys())

    def __iter__(self):
        """ See `IContainer`.

        >>> sps = BTreePrincipalSource()
        >>> sps.keys()
        []
        >>> prin = SimplePrincipal('trillian', 'heartOfGold')
        >>> sps['doesntmatter'] = prin
        >>> prin = SimplePrincipal('zaphod', 'gargleblaster')
        >>> sps['doesntmatter'] = prin
        >>> [i for i in sps]
        ['trillian', 'zaphod']
        """

        return iter(self.keys())

    def __getitem__(self, key):
        """ See `IContainer`

        >>> sps = BTreePrincipalSource()
        >>> prin = SimplePrincipal('gag', 'justzisguy')
        >>> sps['doesntmatter'] = prin
        >>> sps['gag'].login
        'gag'
        """

        number = self._numbers_by_login[key]
        return self._principals_by_number[number]

    def get(self, key, default=None):
        """ See `IContainer`

        >>> sps = BTreePrincipalSource()
        >>> prin = SimplePrincipal(1, 'slartibartfast', 'fjord')
        >>> sps['slartibartfast'] = prin
        >>> principal = sps.get('slartibartfast')
        >>> sps.get('marvin', 'No chance, dude.')
        'No chance, dude.'
        """

        try:
            number = self._numbers_by_login[key]
        except KeyError:
            return default

        return self._principals_by_number[number]

    def values(self):
        """ See `IContainer`.

        >>> sps = BTreePrincipalSource()
        >>> sps.keys()
        []
        >>> prin = SimplePrincipal('arthur', 'tea')
        >>> sps['doesntmatter'] = prin
        >>> [user.login for user in sps.values()]
        ['arthur']
        >>> prin = SimplePrincipal('ford', 'towel')
        >>> sps['doesntmatter'] = prin
        >>> [user.login for user in sps.values()]
        ['arthur', 'ford']
        """

        return [self._principals_by_number[n]
                for n in self._numbers_by_login.values()]

    def __len__(self):
        """ See `IContainer`

        >>> sps = BTreePrincipalSource()
        >>> int(len(sps) == 0)
        1
        >>> prin = SimplePrincipal(1, 'trillian', 'heartOfGold')
        >>> sps['trillian'] = prin
        >>> int(len(sps) == 1)
        1
        """

        return len(self._principals_by_number)

    def items(self):
        """ See `IContainer`.

        >>> sps = BTreePrincipalSource()
        >>> sps.keys()
        []
        >>> prin = SimplePrincipal('zaphod', 'gargleblaster')
        >>> sps['doesntmatter'] = prin
        >>> [(k, v.login) for k, v in sps.items()]
        [('zaphod', 'zaphod')]
        >>> prin = SimplePrincipal('marvin', 'paranoid')
        >>> sps['doesntmatter'] = prin
        >>> [(k, v.login) for k, v in sps.items()]
        [('marvin', 'marvin'), ('zaphod', 'zaphod')]
        """

        # We're being expensive here (see values() above) for convenience
        return [(p.login, p) for p in self.values()]

    def __contains__(self, key):
        """ See `IContainer`.

        >>> sps = BTreePrincipalSource()
        >>> prin = SimplePrincipal('slinkp', 'password')
        >>> sps['doesntmatter'] = prin
        >>> int('slinkp' in sps)
        1
        >>> int('desiato' in sps)
        0
        """
        return self._numbers_by_login.has_key(key)

    has_key = __contains__

    # PrincipalSource-related methods

    def getPrincipal(self, id):
        """ See `IPrincipalSource`.

        `id` is the id as returned by ``principal.getId()``,
        not a login.

        """

        id = id.split('\t')[2]
        id = int(id)

        try:
            return self._principals_by_number[id]
        except KeyError:
            raise PrincipalLookupError(id)

    def getPrincipals(self, name):
        """ See `IPrincipalSource`.

        >>> sps = BTreePrincipalSource()
        >>> prin1 = SimplePrincipal('gandalf', 'shadowfax')
        >>> sps['doesntmatter'] = prin1
        >>> prin1 = SimplePrincipal('frodo', 'ring')
        >>> sps['doesntmatter'] = prin1
        >>> prin1 = SimplePrincipal('pippin', 'pipe')
        >>> sps['doesntmatter'] = prin1
        >>> prin1 = SimplePrincipal('sam', 'garden')
        >>> sps['doesntmatter'] = prin1
        >>> prin1 = SimplePrincipal('merry', 'food')
        >>> sps['doesntmatter'] = prin1
        >>> [p.login for p in sps.getPrincipals('a')]
        ['gandalf', 'sam']
        >>> [p.login for p in sps.getPrincipals('')]
        ['frodo', 'gandalf', 'merry', 'pippin', 'sam']
        >>> [p.login for p in sps.getPrincipals('sauron')]
        []
        """

        for k in self.keys():
            if k.find(name) != -1:
                yield self[k]

    def authenticate(self, login, password):
        """ See `ILoginPasswordPrincipalSource`. """
        number = self._numbers_by_login.get(login)
        if number is None:
            return
        user = self._principals_by_number[number]
        if user.password == password:
            return user


    def checkName(self, name, object):
        """Check to make sure the name is valid

        Don't allow suplicate names:

        >>> sps = BTreePrincipalSource()
        >>> prin1 = SimplePrincipal('gandalf', 'shadowfax')
        >>> sps['gandalf'] = prin1
        >>> sps.checkName('gandalf', prin1)
        Traceback (most recent call last):
        ...
        LoginNameTaken: gandalf

        """
        if name in self._numbers_by_login:
            raise LoginNameTaken(name)

    def chooseName(self, name, object):
        """Choose a name for the principal

        Always choose the object's existing name:

        >>> sps = BTreePrincipalSource()
        >>> prin1 = SimplePrincipal('gandalf', 'shadowfax')
        >>> sps.chooseName(None, prin1)
        'gandalf'

        """
        return object.login

class LoginNameTaken(Exception):
    """A login name is in use
    """


class SimplePrincipal(Persistent, Contained):
    """A no-frills `IUserSchemafied` implementation."""

    implements(IUserSchemafied, IBTreePrincipalSourceContained)

    def __init__(self, login, password, title='', description=''):
        self._id = ''
        self.login = login
        self.password = password
        self.title = title
        self.description = description
        self.groups = []

    def _getId(self):
        source = self.__parent__
        auth = source.__parent__
        return "%s\t%s\t%s" %(auth.earmark, source.__name__, self._id)

    def _setId(self, id):
        self._id = id

    id = property(_getId, _setId)

    def getTitle(self):
        warn("Use principal.title instead of principal.getTitle().",
             DeprecationWarning, 2)
        return self.title

    def getDescription(self):
        warn("Use principal.description instead of principal.getDescription().",
             DeprecationWarning, 2)
        return self.description

    def getLogin(self):
        """See `IReadUser`."""
        return self.login

    def validate(self, test_password):
        """ See `IReadUser`.

        >>> pal = SimplePrincipal('gandalf', 'shadowfax', 'The Grey Wizard',
        ...                       'Cool old man with neato fireworks. '
        ...                       'Has a nice beard.')
        >>> pal.validate('shdaowfax')
        False
        >>> pal.validate('shadowfax')
        True
        """
        return test_password == self.password

class PrincipalAuthenticationView(object):
    """Simple basic authentication view

    This only handles requests which have basic auth credentials
    in them currently (`ILoginPassword`-based requests).
    If you want a different policy, you'll need to write and register
    a different view, replacing this one.
    
    """
    implements(IViewFactory)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def authenticate(self):
        a = ILoginPassword(self.request, None)
        if a is None:
            return
        login = a.getLogin()
        password = a.getPassword()

        p = self.context.authenticate(login, password)
        return p
