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
import qm.attachment
import qm.cmdline
import qm.platform
import qm.structured_text
import qm.track.cmdline
import qm.track.config
import qm.track.web
import qm.user
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
    except qm.cmdline.CommandError, msg:
        # Command error.  Return the error message as the error text.
        return (2, "", msg)
    # Excute the command, capturing output to string files.
    output_file = StringIO.StringIO()
    error_file = StringIO.StringIO()
    exit_code = execute(command, output_file, error_file)
    # Return the exit code and output texts.
    result = (exit_code, output_file.getvalue(), error_file.getvalue())
    return result


def make_server(port, address="", log_file=None):
    """Start an HTTP server.

    preconditions -- An IDB connection in local mode.

    'port' -- The port number on which to accept HTTP requests.

    'address' -- The local address to which to bind the server.  An
    empty string indicates all local addresses.

    'log_file' -- A file object to which the server will log requests.
    'None' for no logging.

    returns -- A server object.  Use 'run_server' to start the server."""

    import qm.track.web.index
    import qm.track.web.issue_class
    import qm.track.web.query
    import qm.track.web.show
    import qm.track.web.summary

    # FIXME.  Can we hard code less stuff here?

    # Path to the QMTrack web subdirectory.
    web_directory = qm.get_share_directory("web")
    # Base URL path for QMTrack stuff.
    script_base = "/track/"

    # Create a new server instance.  Enable XML-RPM.
    server = qm.web.WebServer(port,
                              address,
                              log_file=log_file,
                              xml_rpc_path="/xml-rpc")
    qm.attachment.register_attachment_upload_script(server)
    # Register all our web pages.
    for name, function in [
        ( "", qm.track.web.index.handle_index ),
        ( "add-discussion",
              qm.track.web.issue_class.handle_add_discussion ),
        ( "add-issue-class", qm.track.web.issue_class.handle_add_class ),
        ( "add-issue-field", qm.track.web.issue_class.handle_add_field ),
        ( "config-idb", qm.track.web.issue_class.handle_config_idb ),
        ( "delete-issue-field", qm.track.web.issue_class.handle_delete_field ),
        ( "download-attachment", qm.track.web.handle_download_attachment ),
        ( "index", qm.track.web.index.handle_index ),
        ( "login", qm.web.handle_login ),
        ( "logout", qm.web.handle_logout ),
        ( "new", qm.track.web.show.handle_new ),
        ( "new-issue-class", qm.track.web.issue_class.handle_new_class ),
        ( "new-issue-field", qm.track.web.issue_class.handle_new_field ),
        ( "query", qm.track.web.query.handle_query ),
        ( "show", qm.track.web.show.handle_show ),
        ( "show-issue-class", qm.track.web.issue_class.handle_show_class ),
        ( "show-issue-field", qm.track.web.issue_class.handle_show_field ),
        ( "show-notification",
              qm.track.web.issue_class.handle_show_notification ),
        ( "show-subscription",
              qm.track.web.issue_class.handle_show_subscription ),
        ( "shutdown", handle_shutdown ),
        ( "submit", qm.track.web.show.handle_submit ),
        ( "submit-issue-class", qm.track.web.issue_class.handle_submit_class ),
        ( "submit-issue-field", qm.track.web.issue_class.handle_submit_field ),
        ( "submit-notification",
              qm.track.web.issue_class.handle_submit_notification ),
        ( "submit-subscription",
              qm.track.web.issue_class.handle_submit_subscription ),
        ( "summary", qm.track.web.summary.handle_summary ),
        ]:
        server.RegisterScript(script_base + name, function)
    server.RegisterPathTranslation(
        "/stylesheets", qm.get_share_directory("web", "stylesheets"))
    server.RegisterPathTranslation(
        "/images", qm.get_share_directory("web", "images"))
    server.RegisterPathTranslation(
        "/static", qm.get_share_directory("web", "static"))
    # Register the QM manual.
    server.RegisterPathTranslation(
        "/manual", qm.get_doc_directory("manual", "html"))
    # Register the remote command handler.
    server.RegisterXmlRpcMethod(do_command_for_xml_rpc, "execute_command")

    # Bind the server to the specified address.
    try:
        server.Bind()
    except qm.web.AddressInUseError, address:
        raise RuntimeError, \
              qm.track.error("address in use", address=address)
    except qm.web.PrivilegedPortError:
        raise RuntimeError, \
              qm.track.error("privileged port", port=port)

    return server


def run_server(server):
    """Start accepting requests.

    'server' -- A server created with 'make_server'.

    Does not return until the server shuts down."""

    # Print the XML-RPM URL for this server, if verbose.
    xml_rpc_url = server.GetXmlRpcUrl()
    qm.common.print_message(1, "XML-RPC URL is %s .\n" % xml_rpc_url)
    # Write the URL file.  It contains the XML-RPC URL for this server.
    url_path = qm.track.state["server_url_path"]
    url_file = open(url_path, "w")
    url_file.write(xml_rpc_url + '\n')
    url_file.close()

    try:
        # Start the server.
        server.Run()
    finally:
        # Clean up the URL file.
        os.remove(url_path)


def handle_shutdown(request):
    """Handle a request to shut down the server."""

    administrators_group = qm.user.database.GetGroup("administrators")
    user_id = request.GetSession().GetUserId()

    if user_id in administrators_group:
        raise SystemExit, None
    else:
        # The user isn't an administrator, so disallow the operation.
        # Show an error page instead.
        message = qm.error("shutdown not allowed")
        return qm.web.generate_error_page(request, message)


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

    try:
        # Check if this command requires an IDB connection.
        if command.RequiresIdb() and mode == "remote":
            # We're in remote mode.  Make sure this command doesn't require
            # a local connection.
            if command.RequiresLocalIdb():
                raise RuntimeError, \
                      qm.track.error("cannot invoke remotely",
                                     command=command.GetCommand())
                return 1
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
        # Run commands locally.
        elif not command.RequiresIdb() or mode == "local":
            command.Execute(output_file)
            return 0
    except qm.cmdline.CommandError, msg:
        script_name = qm.track.state["script_name"]
        msg = qm.structured_text.to_text(str(msg))
        error_file.write("%s: %s" % (script_name, msg))
        error_file.write("Invoke %s --help for help with usage.\n"
                         % script_name)
        return 2
    except RuntimeError, msg:
        msg = qm.structured_text.to_text(str(msg))
        error_file.write(msg)
        return 1
    except qm.UserError, msg:
        # A user error should come with a message that is comprehensible
        # to the user.
        msg = qm.structured_text.to_text(str(msg))
        error_file.write(msg)
        return 1
    except qm.ConfigurationError, msg:
        # A configuration error should come with a message that is
        # comprehensible to the user.
        msg = qm.structured_text.to_text(str(msg))
        error_file.write(msg)
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
    except qm.platform.SignalException:
        # The server was killed by a signal.  Let the exception through.
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
