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

import os
import qm
import qm.diagnostic
import qm.track.idb
import qm.fields
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
__gobal_lock = None

# The IDB instance.  Initialized on demand by 'get_idb' when we're in
# local mode; otherwise always 'None'.
__idb = None

# The set of diagnostics for this program.
__diagnostics = None

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
        assert __global_lock.IsLocked()

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
    global __global_lock

    # Make sure another session isn't open.
    assert state["mode"] == "none"

    # Make sure the directory containing 'path' exists and is
    # accessible.
    parent_path = os.path.dirname(path)
    if not os.path.isdir(parent_path):
        raise qm.ConfigurationError, \
              "directory %s containing IDB path does not exit" \
              % parent_path
    if not os.access(parent_path, os.R_OK | os.X_OK):
        raise qm.ConfigurationError, \
              "directory %s containing IDB path is not accesible" \
              % parent_path
    
    # Set up a mutex instance.
    __global_lock = get_idb_lock(path)

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
            __global_lock.Lock(0)

            # Got it; the IDB is ours.  Load the configuration.
            try:
                configuration_path = __get_configuration_path(path)
                __configuration = qm.Configuration(configuration_path)
                __configuration.Load()
            except:
                # Oops, a problem loading the configuration.  Don't
                # hold a lock or leave gunk behind.
                __global_lock.Unlock()
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
            state["mode"] = "remote"
            state["server_url"] = server_url
            state["idb_path"] = path
            return

    # We've exceeded the maximum number of attempts so bail with an
    # exception.
    raise qm.ConfigurationError, \
          "could not open IDB %s after %d attempts" \
          % (path, attempts)


def close_idb():
    """Close the QMTrack session.

    If a session isn't open, do nothing.

    postcondition -- The system is in none mode."""

    global __idb
    global __global_lock
    global __configuration

    mode = state["mode"]
    if mode == "local":
        # We should have the global lock.
        assert __global_lock.IsLocked()
        # Close the IDB, if it was ever initialized.
        if __idb is not None:
            __idb.Close()
            __idb = None
        # Save the configuration.
        __configuration.Save()
        __configuration = None
        # Release the lock.
        __global_lock.Unlock()
        # Clean up state.
        del state["server_url_path"]

    elif mode == "remote":
        # We shouldn't have the lock in remote mode.
        assert not __global_lock.IsLocked()
        # Clean up state.
        del state["server_url"]
        
    else:
        # No session is open.
        return

    # Clean up state.
    del state["idb_path"]
    state["mode"] = "none"


def initialize_idb(path, idb_class_name):
    """Initialize a new IDB.

    'path' -- The path to the new IDB.  The path must not exist.

    'idb_class_name' -- The name of the IDB implementation class to
    use.

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
              "directory %s containing IDB path does not exit" \
              % parent_path
    if not os.access(parent_path, os.R_OK | os.X_OK):
        raise qm.ConfigurationError, \
              "directory %s containing IDB path is not accesible" \
              % parent_path
    # Make sure it doesn't aleady exist.
    if os.path.exists(path):
        raise qm.ConfigurationError, \
              "the IDB path %s already exists" \
              % path
    # Make the directory.
    os.mkdir(path)

    # Create and write a configuration object.
    configuration_path = __get_configuration_path(path)
    configuration = qm.Configuration(configuration_path)
    configuration["idb_class"] = idb_class_name
    configuration.Save()

    # Create a new IDB instance.
    idb = idb_class(path, create_idb=1)
    # Close it immediately.
    idb.Close()


def get_default_class():
    """Return the default issue class for the current IDB."""

    default_class_name = get_configuration()["default_class"]
    return get_idb().GetIssueClass(default_class_name)


def setup_idb_for_test():
    """Add testing stuff to the IDB.

    precondition -- A local session is open."""

    idb = get_idb()

    icl = qm.track.IssueClass("test_class")
    get_configuration()["default_class"] = "test_class"

    field = qm.fields.AttachmentField("attachments")
    field.SetAttribute("title", "File Attachments")
    field = qm.fields.SetField(field)
    icl.AddField(field)

    field = qm.fields.TextField("description")
    field.SetAttribute("title", "Description")
    field.SetAttribute("structured", "true")
    icl.AddField(field)

    severity_enum = {
        "high" : 3,
        "medium" : 2,
        "low" : 1,
        }
    field = qm.fields.EnumerationField("severity", severity_enum, "medium")
    field.SetAttribute("title", "Severity")
    field.SetAttribute("ordered", "true")
    icl.AddField(field)

    idb.AddIssueClass(icl)

    for counter in range(1, 10):
        i = qm.track.Issue(icl, "iss%02d" % counter)
        i.SetField("summary",
                   "This is issue number %d." % counter)
        idb.AddIssue(i)
    

def diagnostic(tag, severity, output, **substitutions):
    """Generate or emit a diagnostic.

    'tag' -- The associated tag.

    'severity' -- A severity code.

    'output' -- A file object to which to write the diagnostic, or
    'None'.

    returns -- The diagnostic."""

    global __diagnostics

    # Perform one-time initialization, if it hasn't been done.
    if __diagnostics is None:
        __diagnostics = qm.diagnostic.DiagnosticSet("diagnostics.txt",
                                                    get_name())
    # Generate or emit the diagnostic.
    return apply(__diagnostics.Generate,
                 (tag, severity, output),
                 substitutions)


def error(tag, output=None, **substitutions):
    """Generate or emit an error diagnostic.

    Like 'diagnostic', with 'severity' set to error."""

    return apply(diagnostic, (tag, "error", output, ), substitutions)

    
def warning(tag, output=None, **substitutions):
    """Generate or emit an error diagnostic.

    Like 'diagnostic', with 'severity' set to warning."""

    return apply(diagnostic, (tag, "warning", output, ), substitutions)

    
# Local helper functions.

def __get_configuration_path(path):
    """Return the path to the configuration file for an IDB.

    'path' -- The IDB path."""

    return os.path.join(path, "configuration")


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
