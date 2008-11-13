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
"""Generic PAS Plugins

$Id: generic.py 70031 2006-09-07 14:02:13Z flox $
"""
__docformat__ = "reStructuredText"
from zope.interface import implements

from zope.app.security.interfaces import IUnauthenticatedPrincipal

from zope.app.authentication import interfaces


class NoChallengeCredentialsPlugin(object):
    """A plugin that doesn't challenge if the principal is authenticated.

    There are two reasonable ways to handle an unauthorized error for an
    authenticated principal:

      - Inform the user of the unauthorized error

      - Let the user login with a different set of credentials

    Since either approach is reasonable, we need to give the site manager
    some way of specifying one of the two policies.

    By default, a user will be challenged for a new set of credentials if
    unauthorized. A site manager can insert this plugin in the front of the
    plugin list to prevent that challenge from occurring. This will
    typically result in an 'Unauthorized' message to the user.

    The 'challenge' behavior of the plugin is simple. To illustrate, we'll
    create a plugin:

      >>> challenger = NoChallengeCredentialsPlugin()

    and a test request with an authenticated principal:

      >>> from zope.publisher.browser import TestRequest
      >>> request = TestRequest()
      >>> IUnauthenticatedPrincipal.providedBy(request.principal)
      False

    When we challenge using the plugin:

      >>> challenger.challenge(request)
      True

    we get a value that signals the PAU that this plugin successfully
    challenged the user (even though it actually did nothing). The PAU
    will stop trying to challenge and the user will not get a chance to
    provide different credentials. The result is typically an error message.

    On the other hand, if the user is unauthenticated:

      >>> class Principal(object):
      ...     implements(IUnauthenticatedPrincipal)
      >>> request.setPrincipal(Principal())
      >>> IUnauthenticatedPrincipal.providedBy(request.principal)
      True

    the plugin challenge will return None:

      >>> print challenger.challenge(request)
      None

    signaling the PAU that it should try the next plugin for a challenge. If
    the PAU is configured properly, the user will receive a challenge and be
    allowed to provide different credentials.
    """
    implements(interfaces.ICredentialsPlugin)

    def extractCredentials(self, request):
        return None

    def challenge(self, request):
        if not IUnauthenticatedPrincipal.providedBy(request.principal):
            return True
        return None

    def logout(self, request):
        return False

