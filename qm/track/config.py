########################################################################
#
# File:   config.py
# Author: Alex Samuel
# Date:   2001-02-08
#
# Contents:
#   Persistent QMTrack configuration.
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

########################################################################
# imports
########################################################################

import issue_class
import os
import qm
import qm.common
import qm.diagnostic
import qm.track.idb
import qm.fields
import shutil
import string
import time

########################################################################
# variables
########################################################################

# A mapping to store transient state.  
state = {

    # The name of this application.
    "name": "QMTrack",

    # The current mode.  Can be none, local, or remote.
    "mode": "none",

    # The environment variable containing the path to the IDB.  The
    # path may be overridden.
    "idb_env_var": "QMTRACK_IDB_PATH",

    }

# Global variables private to this module.

# The loaded configuration object; not 'None' only when we're in local
# mode. 
__configuration = None

# The global mutex on the IDB object.  We hold a lock only when we're
# in local mode. 
_global_lock = None

# The IDB instance.  Initialized on demand by 'get_idb' when we're in
# local mode; otherwise always 'None'.
__idb = None

########################################################################
# functions
########################################################################

def get_name():
    """Return the name of the application."""

    return "QMTrack"


def get_configuration():
    """Return the loaded 'Configuration' object.

    precondition -- Running in local mode."""

    global __configuration

    # Make sure we're running local mode.
    mode = state["mode"]
    if mode == "none":
        raise RuntimeError, "accessing configuration before opening IDB"
    elif mode == "remote":
        raise RuntimeError, "accessing configuration in remote mode"
    # The configuration should already have been loaded.
    assert __configuration is not None
    return __configuration


def get_idb():
    """Return the global IDB instance.

    precondition -- Running in local mode."""

    global __idb
    # Actually load/connect to the IDB just in time.
    if __idb is None:
        # The IDB should be accessed directly only when running in
        # local mode.
        mode = state["mode"]
        if mode == "none":
            raise RuntimeError, "accessing IDB before opening"
        elif mode == "remote":
            raise RuntimeError, "accessing IDB in remote mode"
        # Just in case, make sure we're holding the IDB global lock.
        assert _global_lock.IsLocked()

        # Load the IDB.  First, figure out the IDB class.
        idb_class_name = get_configuration()["idb_class"]
        idb_class = qm.track.idb.get_idb_class(idb_class_name)
        # Set up the IDB instance. 
        idb_path = state["idb_path"]
        __idb = idb_class(idb_path)
        
    return __idb


def get_idb_lock(path):
    """Return the mutex protecting the IDB at 'path'."""
    
    return qm.FileSystemMutex(os.path.join(path, "lock"))


def set_remote_mode(server_url):
    """Put the application into remote access mode.

    precondition -- The mode is "none".

    'server_url' -- The URL to the remote XML/RPC server.

    postcondition -- The mode is "remote"."""

    state["mode"] = "remote"
    state["server_url"] = server_url
    state["idb_path"] = None
    return


def open_idb(path, max_attempts=10, attempt_sleep_time=0.1):
    """Open a QMTrack session.

    precondition -- A session isn't open.

    'path' -- The IDB path.

    'max_attempts' -- The number of times to attempt to open the IDB.

    'attempt_sleep_time' -- The time in seconds to sleep between
    attempts.

    raises -- 'qm.ConfigurationError' if the session cannot be
    opened.

    postcondition -- The system is either in local or in remote mode.
    If in local mode, the confiruation has been loaded successfully.
    If in remote mode, the server URL has been loaded successfully."""

    global __configuration
    global _global_lock

    # Make sure another session isn't open.
    assert state["mode"] == "none"

    # Make sure the IDB directory exists and is accessible.
    if not os.access(path, os.R_OK | os.X_OK):
        parent_path = os.path.dirname(path)
        if os.access(parent_path, os.R_OK | os.X_OK):
            # 'exists' and 'isdir' are relevant only if the parent path
            # is accessible.
            if not os.path.exists(path):
                raise qm.ConfigurationError, \
                      qm.error("idb directory missing", path=path)
            elif not os.path.isdir(path):
                raise qm.ConfigurationError, \
                      qm.error("idb path wrong", path=path)
        else:
            raise qm.ConfigurationError, \
                  qm.error("idb path inaccessible", path=path)
    
    # Set up a mutex instance.
    _global_lock = get_idb_lock(path)

    # The path to the file that contains the server URL.
    server_url_path = os.path.join(path, "server.url")

    # Repeatedly try to open the IDB, until we time out.
    attempts = 0
    while attempts < max_attempts:
        # If this isn't the first attempt, pause first.
        if attempts != 0:
            time.sleep(attempt_sleep_time)
        # Keep count.
        attempts = attempts + 1
        
        try:
            # Try to take a lock.
            _global_lock.Lock(0)

            # Got it; the IDB is ours.
            try:
                # Load the configuration.
                configuration_path = __get_configuration_path(path)
                __configuration = qm.Configuration(configuration_path)
                try:
                    __configuration.Load()
                except IOError, error:
                    raise RuntimeError, \
                          qm.error("idb problem", problem=str(error))
                # Load the user database.
                user_db_path = os.path.join(path, "users.xml")
                qm.user.load_xml_database(user_db_path)
            except:
                # Oops, a problem loading the configuration or user
                # database.  Don't hold a lock or leave gunk behind.
                _global_lock.Unlock()
                __configuration = None
                raise

            # Good to go; put the system into local mode.
            state["mode"] = "local"
            state["idb_path"] = path
            state["server_url_path"] = server_url_path
            return

        except qm.MutexLockError:
            # Could not get a lock.  This probably means another
            # instance is running on the same IDB, so let's try to
            # find it.  Don't assume it's there, though, to prevent
            # a race condition.

            # Do some access checks.  If the path exists, make sure
            # it's accessible.  
            if os.path.isdir(path) \
               and not os.access(path, os.R_OK | os.X_OK):
                raise qm.ConfigurationError, \
                      "IDB path %s is not accesible" % path
            # If the URL file exists, make sure it's accessible too.
            if os.path.isfile(server_url_path) \
               and not os.access(server_url_path, os.R_OK):
                raise qm.ConfigurationError, \
                      "server URL file %s is not accessible" \
                      % server_url_path
                
            # Attempt to load the server URL.
            try:
                server_url = open(server_url_path, "r").read()
                server_url = string.strip(server_url)
            except IOError:
                # We couldn't load the server URL.  Maybe it went away
                # since we checked the lock.  Try again.
                continue

            # All is well.  Put the system into remote mode.
            set_remote_mode(server_url)
            return

    # We've exceeded the maximum number of attempts so bail with an
    # exception.
    raise qm.ConfigurationError, \
          qm.error("idb locked", lock_path=_global_lock.GetPath())


def close_idb():
    """Close the QMTrack session.

    If a session isn't open, do nothing.

    postcondition -- The system is in none mode."""

    global __idb
    global _global_lock
    global __configuration

    mode = state["mode"]
    if mode == "local":
        # Write the user database.
        qm.user.database.Write()
        # We should have the global lock.
        assert _global_lock.IsLocked()
        # Close the IDB, if it was ever initialized.
        if __idb is not None:
            __idb.Close()
            __idb = None
        # Save the configuration.
        __configuration.Save()
        __configuration = None
        # Release the lock.
        _global_lock.Unlock()
        # Clean up state.
        del state["server_url_path"]

    elif mode == "remote":
        # Clean up state.
        del state["server_url"]
        
    else:
        # No session is open.
        return

    # Clean up state.
    del state["idb_path"]
    state["mode"] = "none"


def initialize_idb(path, idb_class_name, test_values=0):
    """Initialize a new IDB.

    'path' -- The path to the new IDB.  The path must not exist.

    'idb_class_name' -- The name of the IDB implementation class to
    use.

    'test_values' -- If true, populate the IDB and user database with
    test values.

    raises -- 'ValueError' if 'idb_class_name' is not recognized as a
    name of an IDB implementation.

    raises -- 'qm.ConfigurationError' if the IDB cannot be
    initialized. 

    postcondition -- The new IDB is created, but a session is not
    opened."""

    # Figure out the IDB class.
    idb_class = qm.track.idb.get_idb_class(idb_class_name)

    # Make sure the directory containing 'path' exists and is
    # accessible.
    parent_path = os.path.dirname(path)
    if not os.path.isdir(parent_path):
        raise qm.ConfigurationError, \
              qm.error("idb parent directory missing",
                       parent_path=parent_path, idb_path=path)
    if not os.access(parent_path, os.R_OK | os.X_OK):
        raise qm.ConfigurationError, \
              qm.error("idb parent directory inaccessible",
                       parent_path=parent_path, idb_path=path)
    # Make sure it doesn't aleady exist.
    if os.path.exists(path):
        raise qm.ConfigurationError, \
              qm.error("idb path exists", idb_path=path)
    # Make the directory.
    os.mkdir(path)

    # Create and write a configuration object.
    configuration_path = __get_configuration_path(path)
    configuration = qm.Configuration(configuration_path)
    configuration["idb_class"] = idb_class_name
    configuration.Save()

    # Copy in the user database template.
    if test_values:
        database_file = "users.xml.test-values"
    else:
        database_file = "users.xml.template"
    user_db_template_path = qm.common.get_share_directory("xml", database_file)
    user_db_path = os.path.join(path, "users.xml")
    shutil.copy(user_db_template_path, user_db_path)

    # Create a new IDB instance.
    idb = idb_class(path, create_idb=1)
    # Close it immediately.
    idb.Close()

    # Add test stuff to the IDB, if requested.
    if test_values:
        open_idb(path)
        setup_idb_for_test()
        close_idb()
        

def get_default_class():
    """Return the default issue class for the current IDB."""

    default_class_name = get_configuration()["default_class"]
    return get_idb().GetIssueClass(default_class_name)


def setup_idb_for_internal_use():
    """Add issue classes for internal use.

    precondition -- A local session is open."""

    import triggers.notification
    import triggers.discussion

    idb = get_idb()

    categories = [
        "common",
        "qmtest",
        "qmtrack",
        "documentation",
        ]
    priority = [
        "high",
        "medium",
        "low",
        ]

    icl = qm.track.IssueClass(name="bug",
                              title="Bug Report",
                              categories=categories)

    icl.GetField("state").SetDefaultValue("submitted")

    field = qm.fields.TextField(
        name="description",
        title="Description",
        description="A complete description of the issue.",
        structured="true")
    icl.AddField(field)

    field = qm.fields.EnumerationField(
        name="priority",
        enumerals=priority,
        default_value="medium",
        title="Priority",
        description="The priority for resolving this issue.",
        ordered="true")
    icl.AddField(field)

    field = qm.fields.AttachmentField(
        name="attachments",
        title="File Attachments",
        description="""
        Files useful for analyzing or reproducing the issue.
        """)
    field = qm.fields.SetField(field)
    icl.AddField(field)

    field = qm.track.issue_class.DiscussionField(
        name="follow_up",
        title="Follow-up",
        description="Follow-up discussion of this issue.",
        structured="true")
    icl.AddField(field)

    trigger = triggers.discussion.DiscussionTrigger(
        name="follow_up_discussion",
        field_name="follow_up")
    icl.RegisterTrigger(trigger)

    field = qm.fields.SetField(qm.fields.UidField(
        name="subscribers",
        title="Subscribers",
        description="""
        User IDs of users subscribed to receive automatic notification
        of changes to this issue.
        """,
        hidden="true"))
    icl.AddField(field)

    trigger = triggers.notification.NotifyByUidFieldTrigger(
        name="subscriber_notification",
        condition="1",
        uid_field_name="subscribers")
    trigger.SetAutomaticSubscription("user != 'guest'")
    icl.RegisterTrigger(trigger)

    trigger = triggers.notification.NotifyFixedTrigger(
        name="new_issue_notification",
        condition="_new",
        recipient_addresses=["samuel-qmtrack@codesourcery.com"])
    icl.RegisterTrigger(trigger)

    idb.AddIssueClass(icl)
    get_configuration()["default_class"] = "bug"


    icl = qm.track.IssueClass(name="enhancement",
                              title="Enhancement Request",
                              categories=categories)

    icl.GetField("state").SetDefaultValue("submitted")

    field = qm.fields.TextField(
        name="description",
        title="Description",
        description="A complete description of the issue.",
        structured="true")
    icl.AddField(field)

    field = qm.fields.EnumerationField(
        name="priority",
        enumerals=priority,
        default_value="medium",
        title="Priority",
        description="The priority for resolving this issue.",
        ordered="true")
    icl.AddField(field)

    field = qm.fields.SetField(qm.fields.UidField(
        name="subscribers",
        title="Subscribers",
        description="""
        User IDs of users subscribed to receive automatic notification
        of changes to this issue.
        """,
        hidden="true"))
    icl.AddField(field)

    trigger = triggers.notification.NotifyByUidFieldTrigger(
        name="subscriber_notification",
        condition="1",
        uid_field_name="subscribers")
    trigger.SetAutomaticSubscription("user != 'guest'")
    icl.RegisterTrigger(trigger)

    field = qm.track.issue_class.DiscussionField(
        name="follow_up",
        title="Follow-up",
        description="Follow-up discussion of this issue.",
        structured="true")
    icl.AddField(field)

    trigger = qm.track.triggers.discussion.DiscussionTrigger(
        name="follow_up_discussion",
        field_name="follow_up")
    icl.RegisterTrigger(trigger)

    idb.AddIssueClass(icl)


def setup_idb_for_test():
    """Add testing stuff to the IDB.

    precondition -- A local session is open."""

    idb = get_idb()

    icl = qm.track.IssueClass(name="test_class",
                              title="Test Issue Class")
    get_configuration()["default_class"] = "test_class"

    field = qm.fields.AttachmentField(
        name="attachments",
        title="File Attachments",
        description="""
        Zero or more file attachments that contain information or data
        relavent to this issue.
        """)
    field = qm.fields.SetField(field)
    icl.AddField(field)

    field = qm.fields.TextField(
        name="description",
        title="Description",
        description="A detailed description of this issue.",
        structured="true")
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
        description="""
        An indication of the importance of resolving this issue.
        """,
        ordered="true")
    icl.AddField(field)

    idb.AddIssueClass(icl)

    field = qm.fields.SetField(qm.fields.UidField(
        name="notify",
        title="People to Notify",
        hidden="true"))
    icl.AddField(field)

    for counter in range(1, 10):
        i = qm.track.Issue(icl, iid=("iss%02d" % counter))
        i.SetField("summary",
                   "This is issue number %d." % counter)
        idb.AddIssue(i)

    import triggers.notification
    trigger = triggers.notification.NotifyByUidFieldTrigger(
        "notification", "_changed('state')", "notify")
    trigger.SetAutomaticSubscription("user != 'guest'")
    icl.RegisterTrigger(trigger)
    

# Local helper functions.

def __get_configuration_path(path):
    """Return the path to the configuration file for an IDB.

    'path' -- The IDB path."""

    return os.path.join(path, "configuration")


########################################################################
# initialization
########################################################################

def __initialize_module():
    # Load QMTrack diagnostics.
    diagnostic_file = qm.get_share_directory("diagnostics", "track.txt")
    qm.diagnostic.diagnostic_set.ReadFromFile(diagnostic_file)
    # Load QMTest help messages.
    help_file = qm.get_share_directory("diagnostics", "track-help.txt")
    qm.diagnostic.help_set.ReadFromFile(help_file)


__initialize_module()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
