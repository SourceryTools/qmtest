########################################################################
#
# File:   user.py
# Author: Alex Samuel
# Date:   2001-03-23
#
# Contents:
#   User management facilities.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

"""User management facilities.

Access to this module is primarily through two global variables.

  'database' -- The user database.  The database contains objects
  representing users, accessed via a *user ID*.  The user ID is a label
  uniquely identifying the user in the system.

  The user database also provides a notion of user groups.  Each group
  is identified by a group ID, and contains zero or more user IDs.  A
  user may belong to more than one group.  A group may not contain other
  groups. 

  'authenticator' -- The authenticator object by which the application
  authenticates users who attempt to access it via various channels.

Access the database object via this interface:

  * Use the database object as a Python map from user IDs to 'User'
    objects.  The 'keys' method returns a sequence of user IDs in the
    database. 

  * Call 'GetGroupIds' to return a sequence of group IDs.  Use the
    'GetGroup' method to retrieve a 'Group' object for a given group ID.

"""

########################################################################
# imports
########################################################################

import qm
import label
import xmlutil

########################################################################
# classes
########################################################################

class AuthenticationError(Exception):
    pass



class XmlDatabaseError(Exception):
    pass



class AccountDisabledError(AuthenticationError):
    pass



class User:
    """A user account record."""

    def __init__(self, user_id, role="user", enabled=1):
        """Create a new user account.

        'user_id' -- The ID for the user.

        'role' -- If "default", this is the default user account (there
        should be only one).  The default account, if provided, is used
        for otherwise unauthenticated operations.  If "admin", this is
        an administrator account.  If "user", this is an ordinary user
        account.

        'enabled' -- If true, this account is enabled; otherwise,
        disabled. 

        User accounts contain three sets of properties.  Each property
        is a name-value pair.  The three sets of properties are:

          informational properties -- General information about the
          user.  This may include the user's real name, contact
          information, etc.  These properties are generally
          user-visible, and should be modified only at the user's
          request.

          configuration properties -- Program-specific per-user
          configuration.  This includes user's preferences, such as
          preferred layout and output options.  These properties are
          typically hidden as implementation details, and are often
          changed implicitly as part of other operations.

          authentication properties -- Information used to authenticate
          the user.  This may include such things as passwords, PGP
          keys, and digital certificates.  There are no accessors for
          these properties; they should be used by authenticators only.

        """
        
        self.__id = user_id
        self.__role = role
        self.__is_enabled = enabled
        # Initialize properties.
        self.__authentication = {}
        self.__configuration = {}
        self.__info = {}


    def GetId(self):
        """Return the user ID of this user."""

        return self.__id


    def GetRole(self):
        """Return the role of this user."""

        return self.__role


    def IsEnabled(self):
        """Return true if this account is enabled."""

        return self.__is_enabled


    def GetConfigurationProperty(self, name, default=None):
        """Return a configuration property.

        'name' -- The name of the property.

        'default' -- The value to return if this property is not
        specified for the user account."""

        return self.__configuration.get(name, default)


    def SetConfigurationProperty(self, name, value):
        """Set the configuration property 'name' to 'value'."""

        self.__configuration[name] = value


    def GetInfoProperty(self, name, default=None):
        """Return an informational property.

        'name' -- The name of the property.

        'default' -- The value to return if this property is not
        specified for the user account."""

        return self.__info.get(name,default)


    def SetInfoProperty(self, name, value):
       """Set the informational property 'name' to 'value'."""

       self.__info[name] = value



class Group:
    """A group of users.

    A 'Group' object is treated as an ordinary list of user IDs (except
    that a user ID may not appear more than once in the list)."""

    def __init__(self, group_id, user_ids=[]):
        """Create a new group.

        'group_id' -- The ID of this group.

        'user_ids' -- IDs of users initially in the group."""

        if not label.is_valid(group_id):
            raise ValueError, 'invalid group ID "%s"' % group_id
        self.__id = group_id
        self.__user_ids = list(user_ids)


    def GetId(self):
        """Return the group_id of this group."""
        
        return self.__id


    def __len__(self):
        return len(self.__user_ids)


    def __getitem__(self, index):
        return self.__user_ids[index]


    def __setitem__(self, index, user_id):
        self.__user_ids[index] = user_id
        # Make sure 'user_id' appears only once.
        while self.__user_ids.count(user_id) > 1:
            self.__user_ids.remove(user_id)


    def __delitem__(self, index):
        del self.__user_ids[index]


    def append(self, user_id):
        # Don't add a given user more than once.
        if user_id not in self.__user_ids:
            self.__user_ids.append(user_id)


    def remove(self, user_id):
        self.__user_ids.remove(user_id)



class Authenticator:
    """Base class for authentication classes.

    An 'Authenticator' object is responsible for determining the
    authenticity of a user.  The inputs to an authentication action
    depend on the mechanism with which the user communicates with the
    program -- for instance, a web request, command invocation, or email
    message."""


    def AuthenticateDefaultUser(self):
        """Authenticate for the default user, if one is provided.

        returns -- The user ID of the default user."""

        raise qm.MethodShouldBeOverriddenError


    def AuthenticateWebRequest(self, request):
        """Authenticate a login web request.

        'request' -- A web request containing the user's login
        information.

        returns -- The user ID of the authenticated user."""

        raise qm.MethodShouldBeOverriddenError



class DefaultDatabase:
    default_user = User("default_user", "default")

    def GetDefaultUserId(self):
        return self.default_user.GetId()


    def keys(self):
        return [self.GetDefaultUserId()]


    def __getitem__(self, user_id):
        default_user_id = self.default_user.GetId()
        if user_id == default_user_id:
            return self.default_user
        else:
            raise KeyError, user_id


    def get(self, user_id, default=None):
        default_user_id = self.default_user.GetId()
        if user_id == default_user_id:
            return self.default_user
        else:
            return None


    def GetGroupIds(self):
        return []


    def GetGroup(self, group_id):
        raise KeyError, "no such group"



class DefaultAuthenticator(Authenticator):
    """Authenticator for only a single user, "default_user"."""

    def AuthenticateDefaultUser(self):
        return DefaultDatabase.default_user.GetId()


    def AuthenticateWebRequest(self, request):
        raise AuthenticationError



class XmlDatabaseUser(User):
    """A user account loaded from an XML user database."""

    def __init__(self, user_node):
        """Read in a user account.

        'user_node' -- A tag element DOM node representing the user."""

        # The user ID is stored in the ID attribute of the user element.
        user_id = user_node.getAttribute("id")
        # Also the role.
        role = user_node.getAttribute("role")
        # Determine whether the account is disabled.
        enabled = user_node.getAttribute("disabled") == "no"
        # Perform base class initialization.
        User.__init__(self, user_id, role, enabled)
        # Read informational properties.
        self.__GetProperties(user_node, "info",
                             self._User__info)
        # Read authentication properties.
        self.__GetProperties(user_node, "authentication",
                             self._User__authentication)
        # Read configuration properties.
        self.__GetProperties(user_node, "configuration",
                             self._User__configuration)


    def __GetProperties(self, node, tag, map):
        """Load properties from a DOM node.

        Load properties from property child elements of the unique child
        element 'tag' of DOM 'node'.  Store the properties in 'map'."""

        # Find all child elements of 'node' with 'tag'.
        elements = node.getElementsByTagName(tag)
        if len(elements) == 0:
            # The child may be omitted; that's OK.
            return
        # There element, if provided, should be unique.
        assert len(elements) == 1
        element = elements[0]

        # Loop over property sub-elements.
        for property_node in element.getElementsByTagName("property"):
            # The property name is stored in the name attribute.
            name = property_node.getAttribute("name")
            # The property value is stored as child CDATA.
            value = xmlutil.get_dom_text(property_node)
            map[name] = value



class XmlDatabase:
    """An XML user database.

    An object of this class behaves as a read-only map from user IDs to
    'User' objects."""

    def __init__(self, database_path):
        """Read in the XML user database."""

        document = xmlutil.load_xml_file(database_path)

        node = document.documentElement
        assert node.tagName == "users"

        self.__users = {}
        self.__groups = {}
        self.__default_user_id = None

        # Load users.
        for user_node in node.getElementsByTagName("user"):
            user = XmlDatabaseUser(user_node)
            # Store the account.
            self.__users[user.GetId()] = user
            # Make note if this is the default user.
            if user.GetRole() == "default":
                if self.__default_user_id is not None:
                    # More than one default user was specified.
                    raise XmlDatabaseError, "multiple default users"
                self.__default_user_id = user.GetId()

        # Load groups.
        for group_node in node.getElementsByTagName("group"):
            group_id = group_node.getAttribute("id")
            user_ids = xmlutil.get_dom_children_texts(group_node, "user-id")
            # Make sure all the user IDs listed for this group are IDs
            # we know. 
            for user_id in user_ids:
                if not self.__users.has_key(user_id):
                    raise XmlDatabaseError, "user %s in group %s is unknown" \
                          % (user_id, group_id)
            # Make the group.
            group = Group(group_id, user_ids)
            self.__groups[group_id] = group
            


    def GetDefaultUserId(self):
        """Return the ID of the default user, or 'None'."""
        
        return self.__default_user_id


    def GetGroupIds(self):
        """Return the IDs of user groups."""

        return self.__groups.keys()


    def GetGroup(self, group_id):
        """Return the group with ID 'group_id'."""

        return self.__groups[group_id]


    # Methods for emulating a map object.

    def __getitem__(self, user_id):
        return self.__users[user_id]


    def get(self, user_id, default=None):
        return self.__get(user_id, default)


    def keys(self):
        return self.__users.keys()



class XmlDatabaseAuthenticator(Authenticator):
    """An authenticator based on contents of the XML user database."""

    def __init__(self, database):
        """Create a new authenticator.

        Authentication is performed based on information stored in
        'XmlDatabase' instance 'database'."""

        assert isinstance(database, XmlDatabase)
        self.__database = database


    def AuthenticateDefaultUser(self):
        # Try to perform a password authentication for the default user
        # with an empty password.
        default_user_id = self.__database.GetDefaultUserId()
        return self.AuthenticatePassword(default_user_id, "")


    def AuthenticateWebRequest(self, request):
        # Extract the user name and password from the web request.
        user_name = request["_login_user_name"]
        password = request["_login_password"]
        return self.AuthenticatePassword(user_name, password)


    def AuthenticatePassword(self, user_name, password):
        try:
            # Look up the user ID.
            user = database[user_name]
            expected_password = user._User__authentication.get("password",
                                                               None)
        except KeyError:
            # No user was found with this user ID.
            expected_password = None
        if expected_password is None \
           or expected_password != password:
            # No password specified for this user, or the provided
            # password doesn't match.
            raise AuthenticationError, "invalid user name/password"
        # Is the account enabled?
        if not user.IsEnabled():
            # No.  Prevent authentication.
            raise AccountDisabledError, user_name
        return user_name



########################################################################
# functions
########################################################################

def load_xml_database(path):
    """Load users from XML database at 'path' and set up authenticator."""

    global database
    global authenticator

    # Use a finally block to make sure either both are set, or neither.
    try:
        xml_database = XmlDatabase(path)
        xml_authenticator = XmlDatabaseAuthenticator(xml_database)
    except:
        raise
    else:
        database = xml_database
        authenticator = xml_authenticator
    

########################################################################
# variables
########################################################################

database = DefaultDatabase()
authenticator = DefaultAuthenticator()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
