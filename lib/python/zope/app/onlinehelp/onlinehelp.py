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
"""Implementation of OnlineHelp System.

This is the default implementation of the `OnlineHelp`. It defines the global
`OnlineHelp` in which all basic Zope-core help screens are registered.

$Id: onlinehelp.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import os

from zope.interface import implements
from zope.configuration.exceptions import ConfigurationError
from zope.traversing.interfaces import IContainmentRoot

from zope.app import zapi
from zope.app.onlinehelp.interfaces import IOnlineHelp, IOnlineHelpTopic
from zope.app.onlinehelp.onlinehelptopic import OnlineHelpTopic

class OnlineHelp(OnlineHelpTopic):
    """
    >>> import os
    >>> from zope import component
    >>> from zope.component.interfaces import IFactory
    >>> from zope.component.factory import Factory
    >>> from zope.app.onlinehelp.tests.test_onlinehelp import testdir
    >>> from zope.app.onlinehelp.tests.test_onlinehelp import I1, Dummy1
    >>> path = os.path.join(testdir(), 'help.txt')

    Create an `OnlineHelp` instance

    >>> onlinehelp = OnlineHelp('Help', path)

    First do the interface verifying tests.

    >>> from zope.interface.verify import verifyObject
    >>> from zope.traversing.interfaces import IContainmentRoot
    >>> verifyObject(IOnlineHelp, onlinehelp)
    True
    >>> verifyObject(IContainmentRoot, onlinehelp)
    True

    Register a new subtopic for interface 'I1' and view 'view.html'

    >>> from zope.app.onlinehelp.onlinehelptopic import OnlineHelpTopic
    >>> from zope.app.onlinehelp.onlinehelptopic import RESTOnlineHelpTopic
    >>> from zope.app.onlinehelp.onlinehelptopic import STXOnlineHelpTopic
    >>> from zope.app.onlinehelp.onlinehelptopic import ZPTOnlineHelpTopic
    >>> default = Factory(OnlineHelpTopic)
    >>> rest = Factory(RESTOnlineHelpTopic)
    >>> stx = Factory(STXOnlineHelpTopic)
    >>> zpt = Factory(ZPTOnlineHelpTopic)
    >>> component.provideUtility(default, IFactory, 'onlinehelp.topic.default')
    >>> component.provideUtility(rest, IFactory, 'onlinehelp.topic.rest')
    >>> component.provideUtility(stx, IFactory, 'onlinehelp.topic.stx')
    >>> component.provideUtility(zpt, IFactory, 'onlinehelp.topic.zpt')
    >>> path = os.path.join(testdir(), 'help2.txt')
    >>> onlinehelp.registerHelpTopic('', 'help2', 'Help 2',
    ...     path, I1, 'view.html')

    Test if the subtopic is set correctly
    >>> onlinehelp['help2'].title
    'Help 2'

    Additionally it should appear as a utility
    >>> from zope.app import zapi
    >>> topic = zapi.getUtility(IOnlineHelpTopic,'help2')
    >>> topic.title
    'Help 2'

    add another topic without parent
    >>> onlinehelp.registerHelpTopic('missing', 'help3', 'Help 3',
    ...     path, I1, 'view.html')

    The new topic should not be a child of the onlinehelp instance
    >>> 'help3' in onlinehelp.keys()
    False

    But it is available as a utility
    >>> topic = zapi.getUtility(IOnlineHelpTopic,'missing/help3')
    >>> topic.title
    'Help 3'

    now register the missing parent
    >>> onlinehelp.registerHelpTopic('', 'missing', 'Missing',
    ...     path, I1, 'view.html')

    This is a child on the onlinehelp
    >>> 'missing' in onlinehelp.keys()
    True

    >>> missing = onlinehelp['missing']

    This topic should now have 'help3' as a child
    >>> 'help3' in missing.keys()
    True

    """
    implements(IOnlineHelp, IContainmentRoot)

    def __init__(self, title, path):
        super(OnlineHelp, self).__init__('',title, path, None)

    def registerHelpTopic(self, parent_path, id, title,
                          doc_path, interface=None, view=None,
                          class_=None, resources=None):
        "See zope.app.onlineHelp.interfaces.IOnlineHelp"

        if not os.path.exists(doc_path):
            raise ConfigurationError(
                "Help Topic definition %s does not exist" % doc_path
                )

        if class_ is None:
            class_ = OnlineHelpTopic

        # Create topic base on the custom class or OnlinHelpTopic
        topic = class_(id, title, doc_path, parent_path, interface, view)

        # add resources to topic
        if resources is not None:
            topic.addResources(resources)

        # add topic to onlinehelp hierarchy
        parent = None
        try:
            parent = zapi.traverse(self, parent_path)
            parent[id] = topic
        except KeyError:
            pass

        for t in zapi.getUtilitiesFor(IOnlineHelpTopic):
            if parent is None:
                if t[1].getTopicPath() == parent_path:
                    t[1][id] = topic
            if topic.getTopicPath() == t[1].parentPath:
                topic[t[1].id] = t[1]

        # Add topic to utilities registry
        #utils = zapi.getService(Utilities)
        #utils.provideUtility(IOnlineHelpTopic, topic, topic.getTopicPath())

        zapi.getGlobalSiteManager().registerUtility(
            topic, IOnlineHelpTopic, topic.getTopicPath())
