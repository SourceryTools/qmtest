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
import qm.fields
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
# constants
########################################################################

# Base URL path for QMTrack stuff.
_script_base = "/track/"

########################################################################
# classes
########################################################################

class WebServer(qm.web.WebServer):
    """The QMTrack web server.

    This server enhance the base class version by attaching an
    '_IssueDatabase' instance to each session as the 'idb' attribute."""

    # FIXME: Implement virtual hosting by configuring the server with
    # multiple IDBs.  The server can choose the appropriate one from the
    # host name in the web request.

    def __init__(self,
                 idb,
                 port,
                 address="",
                 log_file=sys.stderr,
                 xml_rpc_path=None):
        """Create a new web server.

        'idb' -- The issue database to serve.

        See 'qm.web.WebServer.__init__' for descriptions of the other
        parameters."""

        # Initialize the base class.
        qm.web.WebServer.__init__(self, port=port, address=address,
                                  log_file=log_file,
                                  xml_rpc_path=xml_rpc_path)
        # Store the IDB.
        self.__idb = idb

        # Register the location of some static stuff.
        self.RegisterPathTranslation(
            "/stylesheets", qm.get_share_directory("web", "stylesheets"))
        self.RegisterPathTranslation(
            "/images", qm.get_share_directory("web", "images"))
        self.RegisterPathTranslation(
            "/static", qm.get_share_directory("web", "static"))
        # Register the QM manual.
        self.RegisterPathTranslation(
            "/manual", qm.get_doc_directory("manual", "html"))
        # Register the remote command handler.
        self.RegisterXmlRpcMethod(do_command_for_xml_rpc, "execute_command")

        # The global temporary attachment store processes attachment
        # data uploads.
        temporary_attachment_store = qm.attachment.temporary_store
        self.RegisterScript(qm.fields.AttachmentField.upload_url,
                            temporary_attachment_store.HandleUploadRequest)

        # The IDB's attachment store processes download requests for
        # attachment data.
        attachment_store = idb.GetAttachmentStore()
        self.RegisterScript(qm.fields.AttachmentField.download_url,
                            attachment_store.HandleDownloadRequest)
                            

        # Bind the server to the specified address.
        try:
            self.Bind()
        except qm.web.AddressInUseError, address:
            raise RuntimeError, \
                  qm.error("address in use", address=address)
        except qm.web.PrivilegedPortError:
            raise RuntimeError, \
                  qm.error("privileged port", port=port)


    def HandleNoSessionError(self, request, message):
        try:
            # Invoke the base class version.  It returns a page only if
            # something went wrong constructing a session; in that case,
            # just pass on the page.
            return qm.web.WebServer.HandleNoSessionError(
                self, request, message)
        except qm.web.HttpRedirect, redirection:
            # The base class version constructed a session, and attached
            # its ID to the request.  Look up that session.
            session = redirection.request.GetSession()
            # Attach the IDB to the session.
            session.idb = self.__idb
            # Continue with the redirection.
            raise


    def HandleLogin(self, request):
        try:
            # Invoke the generic version.  It returns a page only if
            # the login failed; in that case, just pass on the page.
            return qm.web.handle_login(request)
        except qm.web.HttpRedirect, redirection:
            # The generic version constructed a session, and attached
            # its ID to the request.  Look up that session.
            session = redirection.request.GetSession()
            # Attach the IDB to it.
            session.idb = self.__idb
            # Continue with th redirection.
            raise
        


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


def _make_server(idb, port, address="", log_file=None):
    """Start an HTTP server.

    'idb' -- The issue database to serve.

    'port' -- The port number on which to accept HTTP requests.

    'address' -- The local address to which to bind the server.  An
    empty string indicates all local addresses.

    'log_file' -- A file object to which the server will log requests.
    'None' for no logging.

    returns -- A server object.  Use 'run_server' to start the
    server."""

    # Create a new server instance.  Enable XML-RPM.
    server = WebServer(idb, port=port, address=address,
                       log_file=log_file,
                       xml_rpc_path="/xml-rpc")

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


def make_server(idb, port, address="", log_file=None):
    """Start an HTTP server for interacting with QMTrack.

    'idb' -- The issue database to serve.

    'port' -- The port number on which to accept HTTP requests.

    'address' -- The local address to which to bind the server.  An
    empty string indicates all local addresses.

    'log_file' -- A file object to which the server will log requests.
    'None' for no logging.

    returns -- A server object.  Use 'run_server' to start the server."""

    server = _make_server(idb, port, address, log_file)

    import qm.track.web.index
    import qm.track.web.query
    import qm.track.web.show
    import qm.track.web.summary

    # Register all our web pages.
    for name, function in [
        ( "", qm.track.web.index.handle_index ),
        ( "index", qm.track.web.index.handle_index ),
        ( "login", server.HandleLogin ),
        ( "logout", qm.web.handle_logout ),
        ( "new", qm.track.web.show.handle_new ),
        ( "query", qm.track.web.query.handle_query ),
        ( "show", qm.track.web.show.handle_show ),
        ( "shutdown", handle_shutdown ),
        ( "submit", qm.track.web.show.handle_submit ),
        ( "summary", qm.track.web.summary.handle_summary ),
        ]:
        server.RegisterScript(_script_base + name, function)

    return server


def make_configuration_server(idb, port, address="", log_file=None):
    """Start an HTTP server for configuring an IDB.

    'idb' -- The issue database to configure.

    'port' -- The port number on which to accept HTTP requests.

    'address' -- The local address to which to bind the server.  An
    empty string indicates all local addresses.

    'log_file' -- A file object to which the server will log requests.
    'None' for no logging.

    returns -- A server object.  Use 'run_server' to start the server."""

    server = _make_server(idb, port, address, log_file)

    import qm.track.web
    import qm.track.web.issue_class

    # When we're running the configuration server, use a different
    # navigation bar.
    qm.track.web.DefaultDtmlPage.navigation_bar_template = \
        "configuration-navigation-bar.dtml"

    # Register all our web pages.
    for name, function in [
        ( "add-discussion",
              qm.track.web.issue_class.handle_add_discussion ),
        ( "add-issue-class", qm.track.web.issue_class.handle_add_class ),
        ( "add-issue-field", qm.track.web.issue_class.handle_add_field ),
        ( "config-idb", qm.track.web.issue_class.handle_config_idb ),
        ( "delete-issue-field", qm.track.web.issue_class.handle_delete_field ),
        ( "new-issue-class", qm.track.web.issue_class.handle_new_class ),
        ( "new-issue-field", qm.track.web.issue_class.handle_new_field ),
        ( "show-issue-class", qm.track.web.issue_class.handle_show_class ),
        ( "show-issue-field", qm.track.web.issue_class.handle_show_field ),
        ( "show-notification",
              qm.track.web.issue_class.handle_show_notification ),
        ( "show-subscription",
              qm.track.web.issue_class.handle_show_subscription ),
        ( "shutdown", handle_shutdown ),
        ( "state-model", qm.track.web.issue_class.handle_state_model ),
        ( "submit-issue-class", qm.track.web.issue_class.handle_submit_class ),
        ( "submit-issue-field", qm.track.web.issue_class.handle_submit_field ),
        ( "submit-notification",
              qm.track.web.issue_class.handle_submit_notification ),
        ( "submit-subscription",
              qm.track.web.issue_class.handle_submit_subscription ),
        ]:
        server.RegisterScript(_script_base + name, function)

    return server


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


def execute_locally(command, idb, output_file, error_file):
    """Execute a command.

    'command' -- A 'qm.track.Command' instance to execute.

    'idb' -- The 'Idb' instance on which to run the command.

    'output_file' -- A file object to which normal output is written.

    'error_file' -- A file object to which error messages are written.

    returns -- An integer exit code."""
    
    try:
        command.Execute(idb, output_file)
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
    except RuntimeError, exception:
        # Some other exception.
        error_file.write(qm.structured_text.to_text(str(exception)))
        return 1
    except:
        # For other exceptions, for now, just dump out the
        # stack trace.
        exception = qm.format_exception(sys.exc_info())
        error_file.write(exception)
        return 1
    else:
        return 0


def execute_remotely(command, server_url, output_file, error_file):
    """Execute a command remotely via XML/RPC.

    'command' -- A 'qm.track.Command' instance to execute.

    'server_url' -- The URL of the remote XML/RPC server.

    'output_file' -- A file object to which normal output is written.

    'error_file' -- A file object to which error messages are written.

    returns -- An integer exit code."""

    assert not command.RequiresLocalIdb()
    
    # We're in remote mode.  Make sure this command doesn't require
    # a local connection.
    if command.RequiresLocalIdb():
        raise RuntimeError, \
              qm.track.error("cannot invoke remotely",
                             command=command.GetCommand())
        return 1
    # Connect to the server.
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


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
