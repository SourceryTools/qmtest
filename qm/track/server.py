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
import qm.track.cmdline
import qm.track.config
import qm.track.web
import qm.track.web.index
import qm.track.web.query
import qm.track.web.show
import qm.track.web.summary
import qm.web
import StringIO
import sys
import xmlrpclib

########################################################################
# classes
########################################################################

########################################################################
# functions
########################################################################

def do_command_for_xml_rpc(argument_list):
    """Execute a command submitted via XML-RPC.

    preconditions -- An IDB connection in local mode.

    'argument_list' -- The argument list containing the command to
    execute.

    returns -- A triplet '(exit_code, output_text, error_text)'."""

    assert qm.track.state["mode"] == "local"
    # Parse the command.
    try:
        command = qm.track.cmdline.Command(argument_list)
    except qm.trak.cmdine.CommandError, msg:
        # Command error.  Return the error message as the error text.
        return (2, "", msg)
    # Excute the command, capturing output to string files.
    output_file = StringIO.StringIO()
    error_file = StringIO.StringIO()
    exit_code = execute(command, output_file, error_file)
    # Return the exit code and output texts.
    result = (exit_code, output_file.getvalue(), error_file.getvalue())
    return result


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

    # Create a new server instance.  Enable XML-RPM.
    server = qm.web.WebServer(port,
                              log_file=log_file,
                              xml_rpc_path="/xml-rpc")
    # Register all our web pages.
    for name, function in [
        ( "", qm.track.web.index.handle_index ),
        ( "query", qm.track.web.query.handle_query ),
        ( "show", qm.track.web.show.handle_show ),
        ( "submit", qm.track.web.show.handle_submit ),
        ( "summary", qm.track.web.summary.handle_summary ),
        ( "new", qm.track.web.show.handle_new ),
        ]:
        server.RegisterScript(script_base + name, function)
    server.RegisterPathTranslation(script_base + "stylesheets",
                                   os.path.join(web_directory, "stylesheets"))
    server.RegisterPathTranslation("/images",
                                   os.path.join(web_directory, "images"))
    # Register the remote command handler.
    server.RegisterXmlRpcMethod(do_command_for_xml_rpc, "execute_command")

    # Write the URL file.  It contains the XML-RPC URL for this server.
    url_path = qm.track.state["server_url_path"]
    url_file = open(url_path, "w")
    host_name = qm.get_host_name()
    url_file.write(server.GetXmlRpcUrl() + '\n')
    url_file.close()

    try:
        # Start the server.
        server.Run()
    finally:
        # Clean up the URL file.
        os.remove(url_path)


def execute(command, output_file, error_file):
    """Execute a command.

    If the we're in local mode, execute the command on the local IDB.
    If we're in remote mote, pass the command to the remote server for
    execution.

    'command' -- A 'qm.track.Command' instance to execute.

    'output_file' -- A file object to which normal output is written.

    'error_file' -- A file object to which error messages are written.

    returns -- An integer exit code.  Zero indicates success; non-zero
    values indicate failure. """
    
    mode = qm.track.config.state["mode"]

    # Check if this command requires an IDB connection.
    if command.RequiresIdb() and mode == "remote":
        # We're in remote mode.  Make sure this command doesn't require
        # a local connection.
        if command.RequiresLocalIdb():
            raise RuntimeError, \
                  "%s cannot be invoked on a remote IDB" \
                  % command.GetCommand()
        # Connect to the server.
        server_url = qm.track.state["server_url"]
        server = xmlrpclib.Server(server_url)
        # Invoke the command on the server.
        argument_list = command.GetArgumentList()
        result = server.execute_command(argument_list)
        # Unpack the results.
        exit_code, output_text, error_text = result
        # Write the returned texts to corresponding files.
        output_file.write(output_text)
        error_file.write(error_text)
        # All done.
        return exit_code
        
    elif not command.RequiresIdb() or mode == "local":
        try:
            command.Execute(output_file)
            return 0
        except qm.cmdline.CommandError, msg:
            script_name = qm.track.state["script_name"]
            error_file.write("%s: %s\n" % (script_name, msg))
            error_file.write("Invoke %s --help for help with usage.\n"
                             % script_name)
            return 2
        except qm.UserError, msg:
            # A user error should come with a message that is
            # comprehensible to the user.
            error_file.write(str(msg) + "\n")
            return 1
        except qm.ConfigurationError, msg:
            # A configuration error should come with a message that is
            # comprehensible to the user.
            error_file.write(str(msg) + "\n")
            return 1
        except OSError, exception:
            if hasattr(exception, "filename"):
                message = "%s: %s" \
                          % (exception.strerror, exception.filename)
            else:
                message = exception.strerrro
            error_file.write(message + "\n")
            return exception.errno
        except KeyboardInterrupt:
            # User killed the server; let it through.
            raise
        except:
            # For other exceptions, for now, just dump out the
            # stack trace.
            exception = qm.format_exception(sys.exc_info())
            error_file.write(exception)
            return 1


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
