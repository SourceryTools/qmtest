=================================
New Authentication Service Design
=================================

The current implementation will be replaced. The following is a design
I came up with together with Jim Fulton.
-- itamar

Note that this design is implemented (in some form) by the pluggable
auth service. This document needs to be updated to reflect the final
implementation. 


Design notes for new AuthenticationService
------------------------------------------

The service contains a list of user sources. They implement interfaces,
starting with::


 class IUserPassUserSource:
     """Authenticate using username and password."""

     def authenticate(username, password):
         "Returns boolean saying if such username/password pair exists"


 class IDigestSupportingUserSource(IUserPassUserSource):
     """Allow fetching password, which is required by digest auth methods"""

     def getPassword(username):
         "Return password for username"


etc.  Probably there will be others as well, for dealing with certificate
authentication and what not.  Probably we need to expand above interfaces
to deal with principal titles and descriptions, and so on.

A login method (cookie auth, HTTP basic auth, digest auth, FTP auth),
is registered as a view on one of the above interfaces. 

::

  class ILoginMethodView:

        def authenticate():
             """Return principal for request, or None."""

        def unauthorized():
             """Tell request that a login is required."""


The authentication service is then implemented something like this::


  class AuthenticationService:

      def authenticate(self, request):
          for us in self.userSources:
               loginView = getView(self, us, "login", request)
               principal = loginView.authenticate()
               if principal is not None:
                   return principal

      def unauthorized(self, request):
          loginView = getView(self, self.userSources[0], request)
          loginView.unauthorized()
