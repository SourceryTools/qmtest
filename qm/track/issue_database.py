########################################################################
#
# File:   issue_database.py
# Author: Alex Samuel
# Date:   2001-09-19
#
# Contents:
#   Issue database.
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

"""An issue database stores QMTrack state.

An issue database (IDB) stores complete, persistent state information
about a QMTrack deployment.  An issue database is implemented by a
directory containing the following:

  - A user database, containing user account information.

  - An attachment store, which contains bulk data for file attachments
    (see 'qm.attachment').  This is implemented as a subdirectory.

  - A file containing a specification of the issue classes in the IDB.

  - A configuration database file, containing miscellaneous
    configuration properties of the IDB and its user interface.

  - An issue store, which stores the issue data itself.  Multiple
    implementations of the issue store are possible (see
    'qm.track.issue_store' and derived modules); each may be implemented
    by one or more files and subdirectories.

    An issue store is implemented with a Python module.  The
    "issue_store_module" configuration property specifies which issue
    store implementation module to use for a given IDB.

"""

########################################################################
# imports
########################################################################

import __builtin__
import issue
import issue_class
import os
import qm.common
import qm.attachment
import qm.user
import qm.xmlutil
import shutil
import string
import time

_builtin_open = __builtin__.open

########################################################################
# constants
########################################################################

idb_configuration_dtd = \
    "-//Software Carpentry//QMTrack IDB Configuration V0.1//EN"

issue_class_dtd = \
    "-//Software Carpentry//QMTrack Issue Classes V0.1//EN"

# The number of times to attempt to take an IDB lock before giving up.
_lock_retry_count = 5

# The time, in seconds, to wait before retrying to take an IDB lock.
_lock_retry_wait = 0.05

########################################################################
# exceptions
########################################################################

class IdbError(RuntimeError):
    """A problem occurred loading, interpreting, or saving an IDB."""

    pass



class AccessIdbRemotelyInstead(Exception):
    """The IDB should be accessed remotely instead of locally.

    The IDB is in use by another program, but can be accessed via a
    remote command interface.  The exception argument, if any,
    is the remote command URL of the other program."""

    pass



########################################################################
# classes
########################################################################

class AttachmentStore(qm.attachment.AttachmentStore):
    """A repository for attachment data.

    QMTrack's attachment store implementation places attachment data in
    files in a single subdirectory.  To create a new store, simply
    create an empty subdirectory."""

    def __init__(self, path):
        """Create a connection to an attachment store.

        'path' -- The path to the attachment store subdirectory."""

        self.__path = path


    def Store(self, issue, mime_type, description, file_name, data):
        """Store attachment data, and construct an attachment object.

        'issue' -- The issue of which this attachment is part.

        'mime_type' -- The attachment MIME type.

        'description' -- A description of the attachment.

        'file_name' -- The name of the file from which the attachment
        was uploaded.

        'data' -- The attachment data.

        returns -- An 'Attachment' object, with its location set
        correctly."""

        # Construct the path at which we'll store the attachment data.
        data_file_name = self.__MakeDataFileName(issue.GetId())
        data_file_path = os.path.join(self.__path, data_file_name)
        # Store it.
        _builtin_open(data_file_path, "w").write(data)
        # Construct an 'Attachment'.
        return qm.attachment.Attachment(
            mime_type,
            description,
            file_name,
            location=data_file_name)


    def Adopt(self, issue, mime_type, description, file_name, path):
        """Extract attachment data from a file, and remove the file.

        'issue' -- The issue of which this attachment is part.

        'mime_type' -- The attachment MIME type.

        'description' -- A description of the attachment.

        'file_name' -- The name of the file from which the attachment
        was uploaded.

        'path' -- The path to a file that contains the attachment data.
        This function copies the contents of the file and then removes
        the file.

        returns -- An 'Attachment' object, with its location set
        correctlty. 

        postconditions -- The file at 'path' does not exist."""

        # Construct the path at which we'll store the attachment data.
        data_file_name = self.__MakeDataFileName(issue.GetId())
        data_file_path = os.path.join(self.__path, data_file_name)
        # Copy the data file.
        shutil.copy(path, data_file_path)
        # Delete the data file.
        os.unlink(path)
        # Construct an 'Attachment'.
        return qm.attachment.Attachment(
            mime_type,
            description,
            file_name,
            location=data_file_name)


    # Implementation of base class methods.

    def GetData(self, location):
        data_file_path = os.path.join(self.__path, location)
        return _builtin_open(data_file_path, "r").read()


    def GetDataFile(self, location):
        data_file_path = os.path.join(self.__path, location)
        return data_file_path


    def GetSize(self, location):
        data_file_path = os.path.join(self.__path, location)
        return os.stat(data_file_path)[6]


    # Helper functions.

    def __MakeDataFileName(self, iid):
        """Return an unused file path for attachment data for issue 'iid'."""
        
        # Append an integer to the IID.  Increment it until we find a
        # name that isn't used.
        index = 0
        while 1:
            file_name = "%s.%06d" % (iid, index)
            path = os.path.join(self.__path, file_name)
            if os.path.exists(path):
                index = index + 1
                continue
            else:
                break
        return file_name



class _IssueDatabase:
    """An issue database connection.

    This class should not generally be instantiated.  Use 'create_idb'
    to create a new issue database.  Use 'open_idb' to open a connection
    to an existing database."""

    # A list of open issue database connections.  We track instances to
    # make sure all are closed properly when the program exits.
    open_instances = []


    def __init__(self,
                 path,
                 lock,
                 issue_classes,
                 issue_store,
                 attachment_store,
                 configuration,
                 user_database):
        # Set up attributes.
        self.__path = path
        self.__lock = lock
        self.__issue_classes = issue_classes
        self.__issue_store = issue_store
        self.__attachment_store = attachment_store
        self.__configuration = configuration
        self.__user_database = user_database
        # Add ourselves to the list of open instances.
        _IssueDatabase.open_instances.append(self)

        
    def GetPath(self):
        """Return the path to the issue database."""
        
        return self.__path


    def AddIssueClass(self, issue_class):
        """Add an issue class.

        'issue_class' -- An 'IssueClass' object."""

        name = issue_class.GetName()
        qm.common.print_message(2, "Adding issue class %s.\n" % name)
        # Tell the issue store about the new class.  It may have to set
        # things up to store issues of this class.
        self.__issue_store.AddIssueClass(issue_class)
        # Store it in our internal list.
        self.__issue_classes[name] = issue_class
        # If there is no default issue class so far, make this it.
        configuration = self.GetConfiguration()
        if not configuration.has_key("default_class"):
            configuration["default_class"] = name


    def GetIssueClass(self, issue_class_name):
        """Return an issue class.

        'issue_class_name' -- The name of the issue class.

        returns -- An 'IssueClass' object.

        raises -- 'KeyError' if there is no issue class by that name."""

        return self.__issue_classes[issue_class_name]


    def GetIssueClasses(self):
        """Return a sequence of issue classes.

        Do not modify the sequence directly.  Use 'AddIssueClass'
        etc. instead."""
        
        return self.__issue_classes.values()


    def GetDefaultIssueClass(self):
        """Return the default issue class.

        'preconditions' -- There must be at least one issue class."""

        default_issue_class_name = self.GetConfiguration()["default_class"]
        return self.GetIssueClass(default_issue_class_name)


    def GetIssueStore(self):
        """Return the issue store for this IDB."""

        return self.__issue_store


    def GetAttachmentStore(self):
        """Return the attachment store for this IDB."""

        return self.__attachment_store


    def GetConfiguration(self):
        """Return the configuration for this IDB.

        returns -- A map from configuration property names to
        corresponding values."""

        return self.__configuration


    def Close(self):
        """Close the issue database connection.

        postconditions -- This object may no longer be used."""
        
        # Remove this from the list of issue databases to close.
        _IssueDatabase.open_instances.remove(self)
        # Tell the issue store to write its state.
        self.__issue_store.Close()
        del self.__issue_store
        # Write the configuration.
        configuration_path = _get_configuration_path(self.__path)
        _save_configuration(configuration_path, self.__configuration)
        del self.__configuration
        # Write the issue classes.
        issue_classes_path = _get_issue_classes_path(self.__path)
        issue_class.save(issue_classes_path, self.__issue_classes.values())
        del self.__issue_classes
        # Write the user database.
        # FIXME.
        # self.__user_database.Write()
        del self.__user_database
        # Unlock the IDB.
        self.__lock.Unlock()
        del self.__lock
        del self.__path

        qm.common.print_message(2, "IDB closed.\n")



########################################################################
# functions
########################################################################

def _get_issue_classes_path(idb_path):
    """Return the path to the file containing issue classes for an IDB."""

    return os.path.join(idb_path, "issue-classes")


def _get_configuration_path(idb_path):
    """Return the path to the file containing configuration for an IDB."""

    return os.path.join(idb_path, "configuration")


def _get_attachment_store_path(idb_path):
    """Return the path to the attachment store directory."""

    return os.path.join(idb_path, "attachments")


def create(path, issue_store_module_name, configuration={}):
    """Create a new issue database.

    'path' -- The path at which to create the issue database.

    'issue_store_module_name' -- The name of the issue store
    implementation module to use.

    'configuration' -- A map containing initial configuration
    properties. 

    raises -- 'IdbError' if the issue database cannot be created.

    preconditions -- 'path' does not exist.

    postconditions -- 'path' is a directory conaining an empty issue
    database."""

    # Make sure 'path' does not exist.
    if os.path.exists(path):
        raise IdbError, qm.error("idb path exists", path=path)
    # Make sure the parent directory of 'path' is accessible.
    parent_path = os.path.dirname(path)
    if not os.access(parent_path, os.R_OK | os.X_OK):
        raise IdbError, qm.error("idb path inaccessible", path=path)

    # Get the function to create an issue store.
    create_istore = \
        _get_issue_store_function(issue_store_module_name, "create")

    # Create the IDB directory.
    qm.common.print_message(2, "Creating IDB directory %s.\n" % path)
    os.mkdir(path)

    # Create a user database.
    qm.common.print_message(2, "Building user database.\n")
    # FIXME: For now, copy the template.  Instead, 'user' should support
    # programmatic creation of user databases.
    user_db_path = os.path.join(path, "users.xml")
    user_db_template_path = \
        qm.common.get_share_directory("xml", "users.xml.template")
    template = _builtin_open(user_db_template_path, "r").read()
    _builtin_open(user_db_path, "w").write(template)

    # Write an empty issue class file.
    qm.common.print_message(2, "Building issue class database.\n")
    issue_classes_path = _get_issue_classes_path(path)
    issue_class.save(issue_classes_path, [])

    # Create the attachment store directory.
    attachment_store_path = _get_attachment_store_path(path)
    os.mkdir(attachment_store_path)

    # Store the issue store module name in the configuration.
    qm.common.print_message(2, "Building configuration database.\n")
    configuration = configuration.copy()
    configuration["issue_store_module"] = issue_store_module_name
    # Write the configuration.
    configuration_path = _get_configuration_path(path)
    configuration = _save_configuration(configuration_path, configuration)

    # Create the issue store.
    qm.common.print_message(2, "Building issue store.\n")
    istore = create_istore(path, configuration)


def open(path):
    """Open a connection an existing issue database.

    'path' -- The path to the issue database.

    returns -- An '_IssueDatabase' instance.

    raises -- 'AccessIdbRemotelyInstead' if the IDB is in use by another
    QMTrack server.  The exception argument is the server's remote
    command URL.

    raises -- 'IdbError' if the connection cannot be created."""

    # Check that the IDB directory exists and is accessible.
    if os.access(path, os.R_OK | os.X_OK):
        # These tests are relevant only if the parent path is
        # accessible.
        if not os.path.exists(path):
            raise IdbError, qm.error("idb directory missing", path=path)
        elif not os.path.isdir(path):
            raise IdbError, qm.error("idb path wrong", path=path)
    else:
        raise IdbError, qm.error("idb path inaccessible", path=path)
    
    # Construct the path to the file that contains the server URL.
    # (This file exists only if some other process is running a server
    # on this IDB.)
    server_url_path = os.path.join(path, "server.url")

    # Repeatedly try to lock the IDB, until we time out.
    lock = _make_idb_lock(path)
    attempts = 0
    while attempts < _lock_retry_count:
        # If this isn't the first attempt, pause first.
        if attempts != 0:
            time.sleep(_lock_retry_wait)
        # Keep count.
        attempts = attempts + 1
        
        try:
            # Try to take a lock.
            lock.Lock(0)

        except qm.common.MutexLockError:
            # Could not get a lock.  This probably means another
            # instance is running on the same IDB, so let's try to
            # find it.  Don't assume it's there, though, to prevent
            # a race condition.

            # If the URL file exists, make sure it's accessible too.
            if os.path.isfile(server_url_path) \
               and not os.access(server_url_path, os.R_OK):
                raise IdbError, \
                      qm.error("idb server path not accessible",
                               path=path)
                
            # Attempt to load the server URL.
            try:
                server_url = _builtin_open(server_url_path, "r").read()
            except IOError:
                # We couldn't load the server URL.  Maybe it went away
                # since we checked the lock.  Try again.
                continue
            else:
                # Got the server URL.  Clean it up.
                server_url = string.strip(server_url)
                if server_url == "":
                    continue
                # Indicate to the caller that a remote server should be
                # used.
                raise AccessIdbRemotelyInstead, server_url

        else:
            # Got the lock; the IDB is ours.
            try:
                # Load the user database.
                user_db_path = os.path.join(path, "users.xml")
                user_db = qm.user.load_xml_database(user_db_path)

                # Load issue classes.
                issue_classes_path = _get_issue_classes_path(path)
                issue_classes = issue_class.load(issue_classes_path)

                # Load configuration.
                configuration_path = _get_configuration_path(path)
                configuration = _load_configuration(configuration_path)

                # Open the attachment store.
                attachment_store_path = _get_attachment_store_path(path)
                attachment_store = AttachmentStore(attachment_store_path)

                # Open the issue store.  Start by determining and
                # loading the issue store implementation module.
                istore_module_name = configuration["issue_store_module"]
                open_istore = \
                    _get_issue_store_function(istore_module_name, "open")
                # Open the connection.
                istore = open_istore(path, issue_classes, configuration)
            except:
                # Oops, a problem loading the configuration or user
                # database.  Don't leave a lock behind.
                lock.Unlock()
                raise

            # Good to go.  Construct the issue database object.
            qm.common.print_message(2, "IDB at %s opened.\n" % path) 
            # FIXME: Attachment store.
            return _IssueDatabase(path=path,
                                  lock=lock,
                                  issue_classes=issue_classes,
                                  issue_store=istore,
                                  attachment_store=attachment_store,
                                  configuration=configuration,
                                  user_database=user_db)

    # We've exceeded the maximum number of attempts so bail with an
    # exception.
    # FIXME: Detect and remove stale locks automatically?
    raise IdbError, \
          qm.error("idb locked", idb_path=path, lock_path=lock.GetPath())


def destroy(path):
    """Destroy the issue database at 'path'."""

    # Open the IDB.
    idb = open(path)
    # Get the issue store module.
    configuration = idb.GetConfiguration()
    istore_module_name = configuration["issue_store_module"]
    destroy_istore = \
        _get_issue_store_function(istore_module_name, "destroy")
    # Close the IDB.
    idb.Close()
    
    # Lock the IDB.
    lock = _make_idb_lock(path)
    try:
        lock.Lock(0)
    except qm.common.MutexLockError:
        # Could not lock the database.
        raise RuntimeError, qm.error("idb locked")

    # Destroy the issue store.
    qm.common.print_message(2, "Destroying issue store.\n")
    destroy_istore(path)
    # Destroy the attachment store.
    qm.common.print_message(2, "Destroying attachment store.\n")
    attachment_store_path = _get_attachment_store_path(path)
    qm.common.rmdir_recursively(attachment_store_path)
    # Destroy the configuration.
    qm.common.print_message(2, "Destorying configuration database.\n")
    configuration_path = _get_configuration_path(path)
    os.unlink(configuration_path)
    # Destroy the issue class file.
    qm.common.print_message(2, "Destroying issue class database.\n")
    issue_classes_path = _get_issue_classes_path(path)
    os.unlink(issue_classes_path)
    # Destroy the user database.
    # FIXME: Use the 'user' module to do this instead.
    user_db_path = os.path.join(path, "users.xml")
    os.unlink(user_db_path)

    # Remove it, including anything else left behind.
    qm.common.print_message(2, "Removing IDB directory %s.\n" % path)
    qm.common.rmdir_recursively(path)
    # Don't release the lock explicitly; it will vanish with the IDB.


def setup_for_test(idb):
    """Add testing stuff to 'idb'."""

    icl = issue_class.IssueClass(name="test_class",
                                 title="Test Issue Class")
    idb.GetConfiguration()["default_class"] = "test_class"

    field = qm.fields.AttachmentField(
        name="attachments",
        title="File Attachments",
        description=
"""Arbitrary file attachments.

File attachments can contain any information or data relavent to this
issue."""
        )
    field = qm.fields.SetField(field)
    icl.AddField(field)

    field = qm.fields.TextField(
        name="description",
        title="Description",
        description="A detailed description of this issue.",
        structured="true",
        multiline="true")
    icl.AddField(field)

    severity_enum = [
        "high",
        "medium",
        "low",
        ]
    field = qm.fields.EnumerationField(
        name="severity",
        enumerals=severity_enum,
        default_value="medium",
        title="Severity",
        description="The importance of resolving this issue.",
        ordered="true")
    icl.AddField(field)

    field = qm.fields.SetField(qm.fields.UidField(
        name="notify",
        title="People to Notify",
        hidden="true"))
    icl.AddField(field)

    import triggers.notification
    trigger = triggers.notification.NotifyByUidFieldTrigger(
        "notification", "_changed('state')", "notify")
    trigger.SetAutomaticSubscription("user != 'guest'")
    icl.RegisterTrigger(trigger)
    
    idb.AddIssueClass(icl)

    istore = idb.GetIssueStore()
    for counter in range(1, 10):
        i = issue.Issue(icl, iid=("iss%02d" % counter))
        i.SetField("summary",
                   "This is issue number %d." % counter)
        istore.AddIssue(i)


def _load_configuration(path):
    """Load IDB configuration from the file at 'path'.

    returns -- A map containing configuration properties."""

    document = qm.xmlutil.load_xml_file(path)
    configuration = {}
    for element in \
        qm.xmlutil.get_children(document.documentElement, "property"):
        name = element.getAttribute("name")
        value = qm.xmlutil.get_dom_text(element)
        configuration[name] = value
    return configuration


def _save_configuration(path, configuration):
    """Save IDB configuration to the file at 'path'."""

    # Create an XML document.
    document = qm.xmlutil.create_dom_document(
        public_id=idb_configuration_dtd,
        dtd_file_name="idb_configuration.dtd",
        document_element_tag="idb-configuration"
        )
    # Create property elements.
    for name, value in configuration.items():
        configuration_element = qm.xmlutil.create_dom_text_element(
            document, "property", value)
        configuration_element.setAttribute("name", name)
        document.documentElement.appendChild(configuration_element)
    # Write it.
    qm.xmlutil.write_dom_document(document, _builtin_open(path, "w"))


def _get_issue_store_function(issue_store_module_name, function_name):
    """Return a function from an issue store implementation module.

    'issue_store_module_name' -- The name of the issue store
    implementation module.

    'function_name' -- The required function name.  Issue store modules
    provide functions named 'create', 'open', and 'destroy'.

    returns -- A function object.

    raises -- 'IdbError' if the module cannot be imported or the
    requested function is not found."""

    assert function_name in ("create", "open", "destroy")

    # Load the requrested module.
    try:
        istore_module = qm.common.load_module(issue_store_module_name)
    except ImportError, exception:
        raise IdbError, qm.error("issue store module error",
                                 name=istore_module_name,
                                 error=str(exception))
    # Get the function to open an issue store connection.
    try:
        function = getattr(istore_module, function_name)
    except AttributeError:
        raise IdbError, qm.error("issue store module error",
                                 name=istore_module_name,
                                 error="No function 'open'.")

    assert callable(function)
    return function


def _make_idb_lock(path):
    """Create a lock object for the IDB at 'path'."""

    lock_path = os.path.join(path, "lock")
    return qm.common.FileSystemMutex(lock_path)
    

########################################################################
# module configuration
########################################################################

# At exit, close all open issue databases.
qm.common.add_exit_function(
    lambda oi=_IssueDatabase.open_instances: map(lambda idb: idb.Close(), oi))

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
