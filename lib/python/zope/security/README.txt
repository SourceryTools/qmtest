==============
Zope3 Security
==============

Introduction
------------

The Security framework provides a generic mechanism to implement security
policies on Python objects.  This introduction provides a tutorial of the
framework explaining concepts, design, and going through sample usage from the
perspective of a Python programmer using the framework outside of Zope.

Definitions
-----------

Principal
~~~~~~~~~

A generalization of a concept of a user.

Permission
~~~~~~~~~~

A kind of access, i.e. permission to READ vs. permission to WRITE.
Fundamentally the whole security framework is organized around checking
permissions on objects.

Purpose
-------

The security framework's primary purpose is to guard and check access to
Python objects.  It does this by providing mechanisms for explicit and
implicit security checks on attribute access for objects.  Attribute names are
mapped onto permission names when checking access and the implementation of
the security check is defined by the security policy, which receives the
object, the permission name, and an interaction.

Interactions are objects that represent the use of the system by one or more
principals.  An interaction contains a list of participations, which
represents the way a single principal participates in the interaction.  An
HTTP request is one example of a participation.

Its important to keep in mind that the policy provided is just a default, and
it can be substituted with one which doesn't care about principals or
interactions at all.

Framework Components
--------------------

Low Level Components
~~~~~~~~~~~~~~~~~~~~

These components provide the infrastructure for guarding attribute access and
providing hooks into the higher level security framework.

Checkers
~~~~~~~~

A checker is associated with an object kind, and provides the hooks that map
attribute checks onto permissions deferring to the security manager (which in
turn defers to the policy) to perform the check.

Additionally, checkers provide for creating proxies of objects associated with
the checker.

There are several implementation variants of checkers, such as checkers that
grant access based on attribute names.

Proxies
~~~~~~~

Wrappers around Python objects that implicitly guard access to their wrapped
contents by delegating to their associated checker.  Proxies are also viral in
nature, in that values returned by proxies are also proxied.

High Level Components
---------------------

Security Management
~~~~~~~~~~~~~~~~~~~

Provides accessors for setting up interactions and the global security policy.

Interaction
~~~~~~~~~~~

Stores transient information on the list of participations.

Participation
~~~~~~~~~~~~~

Stores information about a principal participating in the interaction.

Security Policy
~~~~~~~~~~~~~~~

Provides a single method that accepts the object, the permission, and the
interaction of the access being checked and is used to implement the
application logic for the security framework.

Narrative (agent sandbox)
-------------------------

As an example we take a look at constructing a multi-agent distributed system,
and then adding a security layer using the Zope security model onto it.

Scenario
~~~~~~~~

Our agent simulation consists of autonomous agents that live in various agent
homes/sandboxes and perform actions that access services available at their
current home.  Agents carry around authentication tokens which signify their
level of access within any given home.  Additionally agents attempt to migrate
from home to home randomly.

The agent simulation was constructed separately from any security aspects.
Now we want to define and integrate a security model into the simulation.  The
full code for the simulation and the security model is available separately;
we present only relevant code snippets here for illustration as we go through
the implementation process.

For the agent simulation we want to add a security model such that we group
agents into two authentication groups, "norse legends", including the
principals thor, odin, and loki, and "greek men", including prometheus,
archimedes, and thucydides.

We associate permissions with access to services and homes.  We differentiate
the homes such that certain authentication groups only have access to services
or the home itself based on the local settings of the home in which they
reside.

We define the homes/sandboxes

  - origin - all agents start here, and have access to all
    services here.

  - valhalla - only agents in the authentication group 'norse
    legend' can reside here.

  - jail - all agents can come here, but only 'norse legend's
    can leave or access services.


Process
~~~~~~~

Loosely we define a process for implementing this security model

  - mapping permissions onto actions

  - mapping authentication tokens onto permissions

  - implementing checkers and security policies that use our
    authentication tokens and permissions.

  - binding checkers to our simulation classes

  - inserting the hooks into the original simulation code to add
    proxy wrappers to automatically check security.

  - inserting hooks into the original simulation to register the
    agents as the active principal in an interaction.


Defining a Permission Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~

We define the following permissions::

   NotAllowed = 'Not Allowed'
   Public = Checker.CheckerPublic
   TransportAgent = 'Transport Agent'
   AccessServices = 'Access Services'
   AccessAgents = 'Access Agents'
   AccessTimeService = 'Access Time Services'
   AccessAgentService = 'Access Agent Service'
   AccessHomeService = 'Access Home Service'

and create a dictionary database mapping homes to authentication groups which
are linked to associated permissions.


Defining and Binding Checkers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Checkers are the foundational unit for the security framework.  They define
what attributes can be accessed or set on a given instance.  They can be used
implicitly via Proxy objects, to guard all attribute access automatically or
explicitly to check a given access for an operation.

Checker construction expects two functions or dictionaries, one is used to map
attribute names to permissions for attribute access and another to do the same
for setting attributes.

We use the following checker factory function::

   def PermissionMapChecker(permissions_map={},
                            setattr_permission_func=NoSetAttr):
       res = {}
       for k,v in permissions_map.items():
           for iv in v:
               res[iv]=k
       return checker.Checker(res.get, setattr_permission_func)

   time_service_checker = PermissionMapChecker(
                                  # permission : [methods]
                                  {'AccessTimeService':['getTime']}
                                  )

with the NoSetAttr function defined as a lambda which always return the
permission `NotAllowed`.

To bind the checkers to the simulation classes we register our checkers with
the security model's global checker registry::

   import sandbox_simulation
   from zope.security.checker import defineChecker
   defineChecker(sandbox_simulation.TimeService, time_service_checker)


Defining a Security Policy
~~~~~~~~~~~~~~~~~~~~~~~~~~

We implement our security policy such that it checks the current agent's
authentication token against the given permission in the home of the object
being accessed::

  class SimulationSecurityPolicy:

      implements(ISecurityPolicy)

      createInteraction = staticmethod(simpleinteraction.createInteraction)

      def checkPermission(self, permission, object, interaction):

          home = object.getHome()
          db = getattr(SimulationSecurityDatabase, home.getId(), None)

          if db is None:
              return False

          allowed = db.get('any', ())
          if permission in allowed or ALL in allowed:
              return True

          if interaction is None:
              return False
          if not interaction.participations:
              return False
          for participation in interaction.participations:
              token = participation.principal.getAuthenticationToken()
              allowed = db.get(token, ())
              if permission not in allowed:
                  return False

          return True

There are no specific requirements for the interaction class, so we can just
use `zope.security.simpleinteraction.Interaction`.

Since an interaction can have more than one principal, we check that *all* of
them are given the necessary permission.  This is not really necessary since
we only create interactions with a single active principal.

There is some additional code present to allow for shortcuts in defining the
permission database when defining permissions for all auth groups and all
permissions.


Integration
~~~~~~~~~~~

At this point we have implemented our security model, and we need to integrate
it with our simulation model.  We do so in three separate steps.

First we make it such that agents only access homes that are wrapped in a
security proxy.  By doing this all access to homes and services (proxies have
proxied return values for their methods) is implicitly guarded by our security
policy.

The second step is that we want to associate the active agent with the
security context so the security policy will know which agent's authentication
token to validate against.

The third step is to set our security policy as the default policy for the
Zope security framework.  It is possible to create custom security policies at
a finer grained than global, but such is left as an exercise for the reader.


Interaction Access
~~~~~~~~~~~~~~~~~~

The *default* implementation of the interaction management interfaces defines
interactions on a per thread basis with a function for an accessor.  This
model is not appropriate for all systems, as it restricts one to a single
active interaction per thread at any given moment.  Reimplementing the
interaction access methods though is easily doable and is noted here for
completeness.


Perspectives
~~~~~~~~~~~~

It's important to keep in mind that there is a lot more that is possible using
the security framework than what's been presented here.  All of the
interactions are interface based, such that if you need to re-implement the
semantics to suite your application a new implementation of the interface will
be sufficient.  Additional possibilities range from restricted interpreters
and dynamic loading of untrusted code to non Zope web application security
systems.  Insert imagination here ;-).


Zope Perspective
~~~~~~~~~~~~~~~~

A Zope3 programmer will never commonly need to interact with the low level
security framework.  Zope3 defines a second security package over top the low
level framework and authentication sources and checkers are handled via zcml
registration.  Still those developing Zope3 will hopefully find this useful as
an introduction into the underpinnings of the security framework.


Code
~~~~

The complete code for this example is available.

- sandbox.py - the agent framework

- sandbox_security.py - the security implementation and binding to the agent
  framework.


Authors
~~~~~~~

- Kapil Thangavelu <hazmat at objectrealms.net>
- Guido Wesdorp <guido at infrae.com>
- Marius Gedminas <marius at pov.lt>

