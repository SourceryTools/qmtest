########################################################################
#
# File:   server.py
# Author: Alex Samuel
# Date:   2001-02-17
#
# Contents:
#   QMTrack server and client functions.
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
import qm.track.config
import qm.track.web
import qm.web

########################################################################
# classes
########################################################################

########################################################################
# functions
########################################################################

def start_server(port, log_file=None):
    """Start an HTTP server.

    preconditions -- An IDB connection in local mode.

    'port' -- The port number on which to accept HTTP requests.

    'log_file' -- A file object to which the server will log requests.
    'None' for no logging.

    Does not return."""

    # FIXME.  Can we hard code less stuff here?

    # Path to the QMTrack web subdirectory.
    web_directory = os.path.join(qm.get_base_directory(), "track", "web")
    # Base URL path for QMTrack stuff.
    script_base = "/track/"

    # Create a new server instance.
    server = qm.web.WebServer()
    # Register all our web pages.
    for name, function in [
        ( "show", qm.track.web.handle_show ),
        ( "submit", qm.track.web.handle_submit ),
        ( "summary", qm.track.web.handle_summary ),
        ( "new", qm.track.web.handle_new ),
        ]:
        server.RegisterScript(script_base + name, function)
    server.RegisterPathTranslation(script_base + "stylesheets",
                                   os.path.join(web_directory, "stylesheets"))

    # Write the URL file.  It contains the URL for this server.
    url_path = qm.track.state["server_url_path"]
    url_file = open(url_path, "w")
    host_name = qm.get_host_name()
    url_file.write("http://%s:%d%s\n" % (host_name, port, script_base))
    url_file.close()

    try:
        # Start the server.
        server.Run(port, log_file)
    finally:
        # Clean up the URL file.
        os.remove(url_path)


def execute(command, output_file):
    """Execute a command.

    If the we're in local mode, execute the command on the local IDB.
    If we're in remote mote, pass the command to the remote server for
    execution.

    'command' -- A 'qm.track.Command' instance to execute.

    'output_file' -- A file object to which normal output is written."""
    
    # FIXME.  Handle exceptions and write to 'error_file'

    # Check if this command requires an IDB connection.
    if command.RequiresIdb():
        # It does.  Make sure we're connected.
        mode = qm.track.config.state["mode"]
        assert mode != "none"

        if mode == "remote":
            # We're in remote mode.  Make sure this command doesn't
            # require a local connection.
            if command.RequiresLocalIdb():
                raise RuntimeError, \
                      "%s cannot be invoked on a remote IDB" \
                      % command.GetCommand()
            # FIXME.  Implement remote execution here.
            raise NotImplementedError, "remote command execution"

        elif mode == "local":
            # We're in local mode.  Execute the command.
            command.Execute(output_file)

    else:
        # The command doesn't require a connection.  Go ahead with it.
        command.Execute(output_file)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
