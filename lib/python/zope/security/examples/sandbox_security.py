##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""A small, secure sandbox application.

This module is responsible of securing the sandbox application and run it in a
secure mode. There are several steps that are taken to set up the security

  1. map permissions to actions
  
  2. map authentication tokens/principals onto permissions
  
  3. implement checker and security policies that affect 1,2
  
  4. bind checkers to classes/instances
  
  5. proxy wrap as necessary

$Id: sandbox_security.py 73624 2007-03-26 12:50:23Z dobe $
"""
import sandbox
from zope.security.interfaces import IParticipation
from zope.security import checker, management, simplepolicies
from zope.interface import implements


# Define all permissions that will be available 
NotAllowed = 'Not Allowed'
Public = checker.CheckerPublic
TransportAgent = 'Transport Agent'
AccessServices = 'Access Services'
AccessAgents = 'Access Agents'
AccessTimeService = 'Access Time Services'
AccessAgentService = 'Access Agent Service'
AccessHomeService = 'Access Home Service'

AddAgent = 'Add Agent'
ALL='All'

NoSetAttr = lambda name: NotAllowed


class SimulationSecurityDatabase(object):
    """Security Database

    In the database, locations are mapped to authentication tokens to
    permissions.
    """
    origin = {
        'any' : [ALL]
        }

    jail = {
        'norse legend' : [TransportAgent, AccessServices, AccessAgentService,
                          AccessHomeService, TransportAgent, AccessAgents],
        'any' : [AccessTimeService, AddAgent]
        }

    valhalla = {
        'norse legend' : [AddAgent],
        'any' : [AccessServices, AccessTimeService, AccessAgentService,
                 AccessHomeService, TransportAgent, AccessAgents]
        }


class SimulationSecurityPolicy(simplepolicies.ParanoidSecurityPolicy):
    """Security Policy during the Simulation.

    A very simple security policy that is specific to the simulations.
    """

    def checkPermission(self, permission, object):
        """See zope.security.interfaces.ISecurityPolicy"""
        home = object.getHome()
        db = getattr(SimulationSecurityDatabase, home.getId(), None)

        if db is None:
            return False

        allowed = db.get('any', ())
        if permission in allowed or ALL in allowed:
            return True

        if not self.participations:
            return False

        for participation in self.participations:
            token = participation.principal.getAuthenticationToken()
            allowed = db.get(token, ())
            if permission not in allowed:
                return False

        return True


class AgentParticipation(object):
    """Agent Participation during the Simulation.

    A very simple participation that is specific to the simulations.
    """

    implements(IParticipation)

    def __init__(self, agent):
        self.principal = agent
        self.interaction = None


def PermissionMapChecker(permissions_map=None, set_permissions=None):
    """Create a checker from using the 'permission_map.'"""
    if permissions_map is None:
        permissions_map = {}
    if set_permissions is None:
        set_permissions = {}
    res = {}
    for key, value in permissions_map.items():
        for method in value:
            res[method] = key
    return checker.Checker(res, set_permissions)


#################################
# sandbox security settings
sandbox_security = {
    AccessServices : ['getService', 'addService', 'getServiceIds'],
    AccessAgents : ['getAgentsIds', 'getAgents'],
    AddAgent : ['addAgent'],
    TransportAgent : ['transportAgent'],
    Public : ['getId','getHome']
    }
sandbox_checker = PermissionMapChecker(sandbox_security)

#################################
# service security settings

# time service
tservice_security = { AccessTimeService:['getTime'] }
time_service_checker = PermissionMapChecker(tservice_security)

# home service
hservice_security = { AccessHomeService:['getAvailableHomes'] }
home_service_checker = PermissionMapChecker(hservice_security)

# agent service
aservice_security = { AccessAgentService:['getLocalAgents'] }
agent_service_checker = PermissionMapChecker(aservice_security)


def wire_security():

    management.setSecurityPolicy(SimulationSecurityPolicy)

    checker.defineChecker(sandbox.Sandbox, sandbox_checker)
    checker.defineChecker(sandbox.TimeService, time_service_checker)
    checker.defineChecker(sandbox.AgentDiscoveryService, agent_service_checker)
    checker.defineChecker(sandbox.HomeDiscoveryService, home_service_checker)

    def addAgent(self, agent):
        if not self._agents.has_key(agent.getId()) \
           and sandbox.IAgent.providedBy(agent):
            self._agents[agent.getId()]=agent
            agentChecker = checker.selectChecker(self)
            wrapped_home = agentChecker.proxy(self)
            agent.setHome(wrapped_home)
        else:
            raise sandbox.SandboxError("couldn't add agent %s" %agent)

    sandbox.Sandbox.addAgent = addAgent

    def setupAgent(self, agent):
        management.newInteraction(AgentParticipation(agent))

    sandbox.TimeGenerator.setupAgent = setupAgent

    def teardownAgent(self, agent):
        management.endInteraction()

    sandbox.TimeGenerator.teardownAgent = teardownAgent

    def GreenerPastures(agent):
        """ where do they want to go today """
        import random
        _homes = sandbox._homes
        possible_homes = _homes.keys()
        possible_homes.remove(agent.getHome().getId())
        new_home =  _homes.get(random.choice(possible_homes))
        return checker.selectChecker(new_home).proxy(new_home)

    sandbox.GreenerPastures = GreenerPastures


if __name__ == '__main__':
    wire_security()
    sandbox.main()
