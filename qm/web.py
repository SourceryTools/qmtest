########################################################################
#
# File:   web.py
# Author: Alex Samuel
# Date:   2001-02-08
#
# Contents:
#   Common code for implementing web user interfaces.
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

"""Common code for implementing web user interfaces."""

########################################################################
# imports
########################################################################

import BaseHTTPServer
import cgi
import errno
import htmlentitydefs
import md5
import os
import qm.common
import qm.user
import re
import SimpleHTTPServer
import SocketServer
import socket
import string
import structured_text
import sys
import time
import traceback
import types
import urllib
import user
import whrandom
import xmlrpclib

########################################################################
# constants
########################################################################

session_id_field = "session"
"""The name of the form field used to store the session ID."""

########################################################################
# exception classes
########################################################################

class AddressInUseError(RuntimeError):
    pass



class PrivilegedPortError(RuntimeError):
    pass



class NoSessionError(RuntimeError):
    pass



class InvalidSessionError(RuntimeError):
    pass




########################################################################
# classes
########################################################################

class PageInfo:
    """Common base class for page info classes.

    We pass page info objects as context when generating HTML from
    DTML.  Members of the page info object are available as DTML
    variables.

    This class contains common variables and functions that are
    available when generating all DTML files."""

    html_header = ""

    html_footer = ""

    table_attributes = 'cellspacing="0" border="0" cellpadding="4"'


    def __init__(self, request):
        """Create a new page.

        'request' -- A 'WebRequest' object containing the page
        request."""

        # Remember the request.
        self.request = request


    def GenerateHtmlHeader(self, description):
        """Return the header for an HTML document."""

        return \
'''<head>
 <meta http-equiv="Content-Type" 
       content="text/html: charset=iso-8859-1"/>
 <meta http-equiv="Content-Style-Type" 
       content="text/css"/>
 <link rel="stylesheet" 
       type="text/css" 
       href="%s"/>
 <meta name="Generator" 
       content="%s"/>
 <title>%s</title>
</head>
''' % (self.html_stylesheet, self.html_generator, description)


    def GenerateStartBody(self):
        """Return markup to start the body of the HTML document."""

        return "<body>"


    def GenerateEndBody(self):
        """Return markup to end the body of the HTML document."""

        return "</body>"


    def MakeLoginForm(self, redirect_request=None):
        if redirect_request is None:
            # No redirection specified, so redirect back to this page.
            redirect_request = self.request
        request = redirect_request.copy("login")
        request["_login_url"] = redirect_request.GetUrl()
        # Use a POST method to submit the login form, so that passwords
        # don't appear in web logs.
        return qm.web.make_form_for_request(request, method="post") \
               + '''
   <table cellpadding="0" cellspacing="0">
    <tr><td>User name:</td></tr>
    <tr><td><input type="text" size="16" name="_login_user_name"></td></tr>
    <tr><td>Password:</td></tr>
    <tr><td><input type="password" size="16" name="_login_password"></td></tr>
    <tr><td><input type="submit" value=" Log In "></td></tr>
   </table>
  </form>
''' 


    def MakeUrlButton(self, *args, **attributes):
        """Generate HTML for a (non-form) action button.

        See 'make_url_button'."""

        return apply(make_url_button, args, attributes)


    def MakeImageUrl(self, image):
        """Generate a URL for an image."""

        return "/images/%s" % image


    def MakeSpacer(self, width=1, height=1):
        """Generate a spacer.

        'width' -- The width of the spacer, in pixels.

        'height' -- The height of the spacer, in pixels.

        returns -- A transparent image of the requested size."""
        
        # 'clear.gif' is an image file containing a single transparent
        # pixel, used for generating fixed spacers
        return '<img border="0" width="%d" height="%d" src="%s"/>' \
               % (width, height, self.MakeImageUrl("clear.gif"))


    def MakeRule(self, color="black"):
        """Generate a plain horizontal rule."""

        return '''
          <table border="0" cellpadding="0" cellspacing="0" width="100%%">
           <tr bgcolor="%s"><td>%s</td></tr>
          </table>
          ''' % (color, self.MakeSpacer())


    def FormatUserId(self, user_id):
        """Generate HTML for a user ID."""

        return '<span class="userid">%s</span>' % user_id



class HttpRedirect(Exception):
    """Exception signalling an HTTP redirect response.

    A script registered with a 'WebServer' instance can raise this
    exception instead of returning HTML source text, to indicate that
    the server should send an HTTP redirect (code 302) response to the
    client instead of the usual code 202 response.

    The exception argument is the URL of the redirect target."""

    pass



class WebRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """Handler for HTTP requests.

    This class groups callback functions that are invoked in response
    to HTTP requests by 'WebServer'.

    Don't define '__init__' or store any persistent information in
    this class or subclasses; a new instance is created for each
    request.  Instead, store the information in the server instance,
    available through the 'server' attribute."""

    def do_GET(self):
        """Process HTTP GET requests."""

        # Parse the query string encoded in the URL, if any.
        script_url, fields = parse_url_query(self.path)
        # Build a request object and hand it off.
        request = apply(WebRequest, (script_url, ), fields)
        # Store the client's IP address with the request.
        request.client_address = self.client_address[0]
        self.__HandleRequest(request)
        self.wfile.flush()
        try:
            self.connection.shutdown(1)
        except:
            # Probably a network error.
            pass


    def do_POST(self):
        """Process HTTP POST requests."""
        
        # Determine the post's content type.
        if self.headers.typeheader is None:
            content_type_header = self.headers.type
        else:
            content_type_header = self.headers.typeheader
        content_type, params = cgi.parse_header(content_type_header)
        # We only know how to handle form-data submissions.
        if content_type == "multipart/form-data":
            # Parse the form data.
            fields = parse_form_query(self.rfile, params)
            # There may be additional query arguments in the URL, so
            # parse that too.
            script_url, url_fields = parse_url_query(self.path)
            # Merge query arguments from the form and from the URL.
            fields.update(url_fields)
            # Create and process a request.
            request = apply(WebRequest, (script_url, ), fields)
            # Store the client's IP address with the request.
            request.client_address = self.client_address[0]
            self.__HandleRequest(request)
        elif content_type == "text/xml":
            # Check if this request corresponds to an XML-RPC invocation.
            if self.server.IsXmlRpcUrl(self.path):
                self.__HandleXmlRpcRequest()
            else:
                self.send_response(400, "Unexpected request.")
        else:
            raise NotImplementedError, \
                  "unknown POST encoding: %s" % content_type
        try:
            self.wfile.flush()
            self.connection.shutdown(1)
        except:
            # Probably a network error.
            pass


    def __HandleScriptRequest(self, request):
        try:
            # Execute the script.  The script returns the HTML
            # text to return to the client.
            script_output = self.server.ProcessScript(request)
        except HttpRedirect, location:
            # The script requested an HTTP redirect response to
            # the client.
            self.send_response(302)
            self.send_header("Location", location)
            self.end_headers()
            return
        except SystemExit:
            self.server.RequestShutdown()
            script_output = "<html><b>Server shut down.</b></html>"
        except:
            # Oops, the script raised an exception.  Show
            # information about the exception instead.
            script_output = format_exception(sys.exc_info())
        # Send its output.
        if isinstance(script_output, types.StringType):
            # The return value from the script is a string.  Assume it's
            # HTML text, and send it appropriate.ly.
            mime_type = "text/html"
            data = script_output
        elif isinstance(script_output, types.TupleType):
            # The return value from the script is a tuple.  Assume the
            # first element is a MIME type and the second is result
            # data.
            mime_type, data = script_output
        else:
            raise ValueError
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", len(data))
        # Since this is a dynamically-generated page, indicate that it
        # should not be cached.  The second header is necessary to support
        # HTTP/1.0 clients.
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        try:
            self.wfile.write(data)
        except IOError:
            # Couldn't write to the client.  Oh well, it's probably a
            # nework problem, or the user cancelled the operation, or
            # the browser crashed...
            pass
        

    def __HandleXmlRpcRequest(self):
        content_length = int(self.headers["Content-length"])
        content = self.rfile.read(content_length)
        arguments, method_name = xmlrpclib.loads(content)
        # Do we have a matching method?
        try:
            method = self.server.GetXmlRpcMethod(method_name)
        except KeyError:
            # No matching method; report the error.
            response = xmlrpclib.Fault(2, "no method: %s" % method_name)
        else:
            try:
                # Invoke the method.
                response = apply(method, arguments, {})
                if not isinstance(response, types.TupleType):
                    response = (response, )
            except:
                # The method raised an exception.  Send an XML-RPC
                # fault response. 
                exc_info = sys.exc_info()
                response = xmlrpclib.Fault(1, "%s : %s"
                                           % (exc_info[0], exc_info[1]))
                # FIXME: For ease of debugging, dump exceptions out.
                sys.stderr.write(qm.format_exception(exc_info))

        # Encode the reponse.
        response_string = xmlrpclib.dumps(response)
        # Send it off.
        self.send_response(200)
        self.send_header("Content-type", "text/xml")
        self.end_headers()
        self.wfile.write(response_string)


    def __HandleFileRequest(self, request, path):
        # There should be no query arguments to a request for an
        # ordinary file.
        if len(request.keys()) > 0:
            self.send_error(400, "Unexpected request.")
            return
        # Open the file.
        try:
            file = open(path, "r")
        except IOError:
            # Send a generic 404 if there's a problem opening the file.
            self.send_error(404, "File not found.")
            return
        # Send the file.
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Cache-Control", "public")
        self.end_headers()
        self.copyfile(file, self.wfile)


    def __HandleRequest(self, request):
        """Process a request from a GET or POST operation.

        'request' -- A 'WebRequest' object."""

        # Check if this request corresponds to a script.
        if self.server.IsScript(request):
            # It is, so run it.
            self.__HandleScriptRequest(request)
        else:
            # Now check if it maps onto a file.  Translate the script URL
            # into a file system path.
            path = self.server.TranslateRequest(request)
            # Is it a file?
            if path is not None and os.path.isfile(path):
                self.__HandleFileRequest(request, path)

            else:
                # The server doesn't know about this URL.
                self.send_error(404, "File not found.")


    def log_message(self, format, *args):
        """Log a message; overrides 'BaseHTTPRequestHandler.log_message'."""

        # Write an Apache-style log entry via the server instance.
        message = "%s - - [%s] %s\n" \
                  % (self.address_string(),
                     self.log_date_time_string(),
                     format%args)
        self.server.LogMessage(message)



class HTTPServer(BaseHTTPServer.HTTPServer):
    """Workaround for problems in 'BaseHTTPServer.HTTPServer'.

    The Python 1.5.2 library's implementation of
    'BaseHTTPServer.HTTPServer.server_bind' seems to have difficulties
    when the local host address cannot be resolved by 'gethostbyaddr'.
    This may happen for a variety of reasons, such as reverse DNS
    misconfiguration.  This subclass fixes that problem."""

    def server_bind(self):
        """Override 'server_bind' to store the server name."""

        # The problem occurs when an empty host name is specified as the
        # local address to which the socket binds.  Specifying an empty
        # host name causes the socket to bind to 'INADDR_ANY', which
        # indicates that the socket should be bound to all interfaces.
        #
        # If the socket is bound to 'INADDR_ANY', 'gethostname' returns
        # '0.0.0.0'.  In this case, 'BaseHTTPServer' tries unhelpfully
        # to obtain a host name to associate with the socket by calling
        # 'gethostname' and then 'gethostbyaddr' on the result.  This
        # will raise a socket error if reverse lookup on the (primary)
        # host address fails.  So, we use our own method to retrieve the
        # local host name, which fails more gracefully under this
        # circumstance. 

        SocketServer.TCPServer.server_bind(self)
        host, port = self.socket.getsockname()

        # Use the primary host name if we're bound to all interfaces.
        # This is a bit misleading, because the primary host name may
        # not be bound to all interfaces.
        if not host or host == '0.0.0.0':
            host = socket.gethostname()

        # Try the broken 'BaseHTTPServer' implementation.
        try:
            hostname, hostnames, hostaddrs = socket.gethostbyaddr(host)
            if '.' not in hostname:
                for host in hostnames:
                    if '.' in host:
                        hostname = host
                        break
        except socket.error:
            # If it bombs, use our more lenient method.
            hostname = qm.get_host_name()

        self.server_name = hostname
        self.server_port = port
    


class WebServer(HTTPServer):
    """A web server that serves ordinary files, dynamic content, and XML-RPC.

    To configure the server to serve ordinary files, register the
    directories containing those files with
    'RegisterPathTranslations'.  An arbitrary number of directories
    may  be specified, and all files in each directory and under it
    are made available.

    To congifure the server to serve dynamic content, register dynamic
    URLs with 'RegisterScript'.  A request matching the URL exactly
    will cause the server to invoke the provided function.

    To configure the server to service XML-RPC requests, pass an
    'xml_rpc_path' to the '__init__' function and register methods
    with 'RegisterXmlRpcMethod'.

    The web server resolves request URLs in a two-step process.

    1. The server checks if the URL matches exactly a script URL.  If
       a match is found, the corresponding function is invoked, and
       its return value is sent to the client.

    2. The server checks whether any registered path translation is a
       prefix of the reqest URL.  If it is, the path is translated
       into a file system path, and the corresponding file is
       returned."""


    def __init__(self,
                 port,
                 address="",
                 log_file=sys.stderr,
                 xml_rpc_path=None):
        """Create a new web server.

        'port' -- The port on which to accept connections.

        'address' -- The local address to which to bind.  An empty
        string means bind to all local addresses.

        'log_file' -- A file object to which to write log messages.
        If it's 'None', no logging.

        'xml_rpc_path' -- The script path at which to accept XML-RPC
        requests.   If 'None', XML-RPC is disabled for this server.

        The server is not started until the 'Bind' and 'Run' methods are
        invoked."""

        self.__port = port
        self.__address = address
        self.__log_file = log_file
        self.__scripts = {}
        self.__translations = {}
        self.__xml_rpc_methods = {}
        self.__xml_rpc_path = xml_rpc_path
        self.__shutdown_requested = 0
        # Don't call the base class __init__ here, since we don't want
        # to create the web server just yet.  Instead, we'll call it
        # when it's time to run the server.


    def GetXmlRpcUrl(self):
        """Return the URL at which this server accepts XML-RPC.

        preconditions -- The server must be bound.

        returns -- The URL, or 'None' if XML-RPC is disabled."""

        if self.__xml_rpc_path is None:
            return None
        else:
            host_name, port = self.GetServerAddress()
            return "http://%s:%d%s" % (host_name, port, self.__xml_rpc_path) 


    def RegisterScript(self, script_path, script):
        """Register a dynamic URL.

        'script_path' -- The URL for this script.  A request must
        match this path exactly.

        'script' -- A callable to invoke to generate the page
        content.  

        If you register

          web_server.RegisterScript('/cgi-bin/myscript', make_page)

        then the URL 'http://my.server.com/cgi-bin/myscript' will
        respond with the output of calling 'make_page'.

        The script is passed a single argument, a 'WebRequest'
        instance.  It returns the HTML source, as a string, of the
        page it generates.  If it returns a tuple instead, the first
        element is taken to be a MIME type and the second is the data.

        The script may instead raise an 'HttpRedirect' instance,
        indicating an HTTP redirect response should be sent to the
        client."""

        self.__scripts[script_path] = script


    def RegisterPathTranslation(self, url_path, file_path):
        """Register a path translation.

        'url_path' -- The path in URL-space to map from.  URLs of
        which 'url_path' is a prefix can be translated.

        'file_path' -- The file system path corresponding to
        'url_path'.  Must be the path to an accessible directory.

        For example, if you register

          web_server.RegisterPathTranslation('/images', '/path/to/pictures')

        the the URL 'http://my.server.com/images/big/tree.gif' will be
        mapped to the file path '/path/to/pictures/big/tree.gif'."""

        if not os.path.isdir(file_path):
            raise ValueError, "%s is not a directory" % file_path
        self.__translations[url_path] = file_path


    def RegisterXmlRpcMethod(self, method, method_name=None):
        """Register an XML-RPC method.

        precoditions -- XML-RPC must be enabled.

        'method' -- The method to call in response to the request.  It
        must be callable.  The request arguments are passed to this
        method's positional parameters.

        'method_name' -- The RPC name to associate with this method.
        If 'None', the name of 'method' is used."""

        assert self.__xml_rpc_path is not None
        assert callable(method)
        # Take the name of 'method' if no name is provided.
        if method_name is None:
            method_name = method.__name__
        # Map it.
        self.__xml_rpc_methods[method_name] = method


    def IsScript(self, request):
        """Return a true value if 'request' corresponds to a script."""

        return self.__scripts.has_key(request.GetUrl())


    def IsXmlRpcUrl(self, url):
        """Return true if 'url' corresponds to an XML-RPC invocation."""

        return self.__xml_rpc_path is not None \
               and url == self.__xml_rpc_path


    def ProcessScript(self, request):
        """Process 'request' as a script.

        'request' -- A 'WebRequest' object.

        returns -- The output of the script."""

        return self.__scripts[request.GetUrl()](request)


    def TranslateRequest(self, request):
        """Translate the URL in 'request' to a file system path.

        'request' -- A 'WebRequest' object.

        returns -- A path to the corresponding file, or 'None' if the
        request URL didn't match any translations."""

        path = request.GetUrl()
        # Loop over translations.
        for url_path, file_path in self.__translations.items():
            # Is this translation a prefix of the URL?
            if path[:len(url_path)] == url_path:
                # Yes.  First cut off the prefix that matched.
                sub_path = path[len(url_path):]
                # Make sure what's left doesn't look like an absolute path.
                if sub_path[0] == os.sep:
                    sub_path = sub_path[1:]
                # Construct the file system path.
                return os.path.join(file_path, sub_path)
        # No match was found.
        return None


    def GetXmlRpcMethod(self, method_name):
        """Return the method corresponding to XML-RPC 'method_name'.

        returns -- A callable object corresponding to 'method_name'.

        raises -- 'KeyError' if there is no mapping for
        'method_name'."""

        return self.__xml_rpc_methods[method_name]


    def Bind(self):
        """Bind the server to the specified address and port.

        Does not start serving."""

        # Initialize the base class here.  This binds the server
        # socket. 
        try:
            # Base class initialization.  Unfortunately, the base
            # class's initializer function (actually, its own base
            # class's initializer function, 'TCPServer.__init__')
            # doesn't provide a way to set options on the server socket
            # after it's created but before it's bound.
            #
            # If the SO_REUSEADDR option is not set before the socket is
            # bound, the bind operation will fail if there is alreay a
            # socket on the same port in the TIME_WAIT state.  This
            # happens most frequently if a server is terminated and then
            # promptly restarted on the same port.  Eventually, the
            # socket is cleaned up and the port number is available
            # again, but it's a big nuisance.  The SO_REUSEADDR option
            # allows the new socket to be bound to the same port
            # immediately.
            #
            # So that we can insert the call to 'setsockopt' between the
            # socket creation and bind, we duplicate the body of
            # 'TCPServer.__init__' here and add the call.
            self.server_address = (self.__address, self.__port)
            self.RequestHandlerClass = WebRequestHandler
            self.socket = socket.socket(self.address_family,
                                        self.socket_type)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_bind()
            self.server_activate()
        except socket.error, error:
            error_number, message = error
            if error_number == errno.EADDRINUSE:
                # The specified address/port is already in use.
                if self.__address == "":
                    address = "port %d" % self.__port
                else:
                    address = "%s:%d" % (self.__address, self.__port)
                raise AddressInUseError, address
            elif error_number == errno.EACCES:
                # Permission denied.
                raise PrivilegedPortError, "port %d" % self.__port
            else:
                # Propagate other exceptions.
                raise


    def Run(self):
        """Start the web server.

        preconditions -- The server must be bound."""

        while not self.__shutdown_requested:
            self.handle_request()


    def RequestShutdown(self):
        """Shut the server down after processing the current request."""

        self.__shutdown_requested = 1


    def LogMessage(self, message):
        """Log a message."""
        
        if self.__log_file is not None:
            self.__log_file.write(message)
            self.__log_file.flush()


    def GetServerAddress(self):
        """Return the host address on which this server is running.

        returns -- A pair '(hostname, port)'."""

        return (self.server_name, self.server_port)



class WebRequest:
    """An object representing a request from the web server.

    A 'WebRequest' object behaves as a dictionary of key, value pairs
    representing query arguments, for instance query fields in a POST,
    or arguments encoded in a URL query string.  It has some other
    methods as well."""

    def __init__(self, script_url, base=None, **fields):
        """Create a new request object.

        'script_url' -- The URL of the script that processes this
        query.
        
        'base' -- A request object from which the session ID will be
        duplicated, or 'None'.

        'fields' -- The query arguments."""

        self.__url = script_url
        self.__fields = fields
        # Copy the session ID from the base.
        if base is not None:
            session = base.GetSessionId()
            if session is not None:
                self.SetSessionId(session)


    def __str__(self):
        str = "WebRequest for %s\n" % self.__url
        for name, value in self.__fields.items():
            str = str + "%s=%s\n" % (name, repr(value))
        return str


    def GetUrl(self):
        """Return the URL of the script that processes this request."""

        return self.__url

    
    def SetSessionId(self, session_id):
        """Set the session ID for this request to 'session_id'."""

        self[session_id_field] = session_id


    def GetSessionId(self):
        """Return the session ID for this request.

        returns -- A session ID, or 'None'."""

        return self.get(session_id_field, None)


    def GetSession(self):
        """Return the session for this request.

        raises -- 'NoSessionError' if no session ID is specified in the
        request.

        raises -- 'InvalidSessionError' if the session ID specified in
        the request is invalid."""

        session_id = self.GetSessionId()
        if session_id is None:
            # There's no session specified in this request.  Try to
            # create a session for the default user.
            try:
                user_id = user.authenticator.AuthenticateDefaultUser()
            except user.AuthenticationError:
                # Couldn't get a default user session, so bail.
                raise NoSessionError, "no sesison for request"
            # Create an implicit session with the default user ID.
            session = Session(self, user_id)
            # Redirect to the same page but using the new session ID.
            self.SetSessionId(session.GetId())
            raise HttpRedirect, make_url_for_request(self)
        else:
            return get_session(self, session_id)


    # Methods to emulate a mapping.

    def __getitem__(self, key):
        return self.__fields[key]


    def __setitem__(self, key, value):
        self.__fields[key] = value


    def __delitem__(self, key):
        del self.__fields[key]


    def get(self, key, default=None):
        return self.__fields.get(key, default)
    

    def keys(self):
        return self.__fields.keys()


    def has_key(self, key):
        return self.__fields.has_key(key)


    def items(self):
        return self.__fields.items()
    

    def copy(self, url=None, **fields):
        """Return a duplicate of this request.

        'url' -- The URL for the request copy.  If 'None', use the
        URL of the source.

        '**fields' -- Additional fields to set in the copy."""

        # Copy the URL unless another was specified.
        if url is None:
            url = self.__url
        # Copy fields, and update with any that were specified
        # additionally. 
        new_fields = self.__fields.copy()
        new_fields.update(fields)
        # Make the request.
        return apply(WebRequest, (url, ), new_fields)



class CGIWebRequest:
    """A 'WebRequest' object initialized from the CGI environment."""

    def __init__(self):
        """Create a new request from the current CGI environment.

        preconditions -- The CGI environment (environment variables
        etc.) must be in place."""

        assert os.environ.has_key("GATEWAY_INTERFACE")
        assert os.environ["GATEWAY_INTERFACE"][:3] == "CGI"

        self.__fields = cgi.FieldStorage()


    def GetUrl(self):
        return os.environ["SCRIPT_NAME"]


    def __getitem__(self, key):
        return self.__fields[key].value


    def keys(self):
        return self.__fields.keys()


    def has_key(self, key):
        return self.__fields.has_key(key)


    def copy(self):
        """Return a copy of the request.

        The copy isn't tied to the CGI environment, so it can be
        modified safely."""

        fields = {}
        for key in self.keys():
            fields[key] = self[key]
        return apply(WebRequest, (self.GetUrl(), ), fields)



class Session:
    """A persistent user session.

    A 'Session' object represents an ongoing user interaction with the
    web server."""

    def __init__(self, request, user_id, expiration_timeout=3600):
        """Create a new session.

        'request' -- A 'WebRequest' object in response to which this
        session is created.

        'user_id' -- The ID of the user owning the session.

        'expiration_timeout -- The expiration time, in seconds.  If a
        session is not accessed for this duration, it is expired and no
        longer usable."""

        self.__user_id = user_id
        self.__expiration_timeout = expiration_timeout
        # Extract the client's IP address from the request.
        self.__client_address = request.client_address

        # Now create a session ID.  Start with a new random number
        # generator.
        generator = whrandom.whrandom()
        # Seed it with the system time.
        generator.seed()
        # FIXME: Is this OK?
        digest = md5.new("%f" % generator.random()).digest()
        # Convert the digest, which is a 16-character string,
        # to a sequence hexadecimal bytes.
        digest = map(lambda ch: hex(ord(ch))[2:], digest)
        # Convert it to a 32-character string.
        self.__id = string.join(digest, "")
        
        self.Touch()

        # Record ourselves in the sessions map.
        sessions[self.__id] = self


    def Touch(self):
        """Update the last access time on the session to now."""
        
        self.__last_access_time = time.time()


    def GetId(self):
        """Return the session ID."""

        return self.__id
    

    def GetUserId(self):
        """Return the ID of the user who owns this session."""

        return self.__user_id


    def GetUser(self):
        """Return the user record for the owning user.

        returns -- A 'qm.user.User' object."""

        return user.database[self.__user_id]
    

    def IsDefaultUser(self):
        """Return true if the owning user is the default user."""

        return self.GetUserId() == user.database.GetDefaultUserId()


    def IsExpired(self):
        """Return true if this session has expired."""

        age = time.time() - self.__last_access_time
        return age > self.__expiration_timeout


    def Validate(self, request):
        """Make sure the session is OK for a request.

        'request' -- A 'WebRequest' object.

        raises -- 'InvalidSessionError' if the session is invalid for
        the request."""

        # Make sure the client IP address in the request matches that
        # for this session.
        if self.__client_address != request.client_address:
            raise InvalidSessionError, "wrong client address"
        # Make sure the session hasn't expired.
        if self.IsExpired():
            raise InvalidSessionError, "session expired"



########################################################################
# functions
########################################################################

def parse_url_query(url):
    """Parse a URL-encoded query.

    This function parses query strings encoded in URLs, such as
    '/script.cgi?key1=val1&key2=val2'.  For this example, it would
    return '("/script.cgi", {"key1" : "val1", "key2" : "val2"})'

    'url' -- The URL to parse.

    returns -- A pair containing the the base script path and a
    mapping of query field names to values."""

    # Check if the script path is a URL-encoded query.
    if "?" in url:
        # Yes.  Everything up to the question mark is the script
        # path; stuff after that is the query string.
        script_url, query_string = string.split(url, "?", 1)
        # Parse the query string.
        fields = cgi.parse_qs(query_string)
        # We only handle one instance of each key in the query.
        # 'parse_qs' produces a list of values for each key; check
        # that each list contains only one item, and replace the
        # list with that item.
        for key, value_list in fields.items():
            if len(value_list) != 1:
                # Tell the client that we don't like this query.
                self.send_response(400, "Multiple values in query.")
                return
            fields[key] = value_list[0]
    else:
        # No, it's just an ordinary URL.
        script_url = url
        fields = {}

    return (script_url, fields)


def parse_form_query(input_file, content_type_params):
    """Parse an HTTP form-encoded query.

    'input_file' -- The to read the HTTP query from.

    'content_type_params' -- The parameters of the Content-type
    header.

    returns -- A dictionary mapping query argument names to values."""

    fields = cgi.parse_multipart(input_file, content_type_params)
    # FIXME.  What's the policy here?
    for name, value in fields.items():
        if len(value) == 1:
            fields[name] = value[0]
    return fields
    

def http_return_html(html_text, stream=sys.stdout):
    """Generate an HTTP response consisting of HTML text.

    'html_text' -- The HTML souce text to return.

    'stream' -- The stream to write the response, by default
    'sys.stdout.'."""

    stream.write("Content-type: text/html\n\n")
    stream.write(html_text)


def http_return_exception(exc_info=None, stream=sys.stdout):
    """Generate an HTTP response for an exception.

    'exc_info' -- A three-element tuple containing exception info, of
    the form '(type, value, traceback)'.  If 'None', use the exception
    currently being handled.

    'stream' -- The stream to write the response, by default
    'sys.stdout.'."""

    if exc_info == None:
        exc_info = sys.exc_info()

    stream.write("Content-type: text/html\n\n");
    stream.write(format_exception(exc_info))


def format_exception(exc_info):
    """Format an exception as HTML.

    'exc_info' -- A three-element tuple containing exception info, of
    the form '(type, value, traceback)'.

    returns -- A string containing a complete HTML file displaying the
    exception."""

    # Break up the exection info tuple.
    type, value, trace = exc_info
    # Format the traceback, with a newline separating elements.
    traceback_listing = string.join(traceback.format_tb(trace), "\n")
    # Generate HTML.
    return \
"""
<html>
 <body>
  <p>An error has occurred: <b>%s : %s</b></p>
  <p>Stack trace follows:</p>
  <pre>
%s
  </pre>
 </body>
</html>
""" % (type, value, traceback_listing)


# Build a map from characters for which we have an HTML entity mapping
def escape(text):
    """Escape special characters in 'text' for formatting as HTML."""

    if text == "":
        return "&nbsp;"
    else:
        return structured_text.escape_html_entities(text)


# A regular expression that matches anything that looks like an entity.
__entity_regex = re.compile("&(\w+);")


# A function that returns the replacement for an entity matched by the
# above expression.
def __replacement_for_entity(match):
    entity = match.group(1)
    try:
        return htmlentitydefs.entitydefs[entity]
    except KeyError:
        return "&%s;" % entity


def unescape(text):
    """Undo 'escape' by replacing entities with ordinary characters."""

    return __entity_regex.sub(__replacement_for_entity, text)


def format_structured_text(text):
    """Render 'text' as HTML."""

    if text == "":
        # In case the text is the only contents of a table cell -- in
        # which case an empty string will produce undesirable visual
        # effects -- return a single space anyway.
        return "&nbsp;"
    else:
        return structured_text.to_html(text)


def make_url_for_request(request):
    """Generate a URL corresponding to 'request'.

    'request' -- A 'WebRequest' object.

    returns -- A URL string encoding the request."""

    if len(request.keys()) == 0:
        # No query arguments; just use the script URL.
        return request.GetUrl()
    else:
        # Encode query arguments into the URL.
        return "%s?%s" % (request.GetUrl(), urllib.urlencode(request))
    

def make_form_for_request(request, method="get"):
    """Generate an opening form tag for 'request'.

    'request' -- A 'WebRequest' object.

    'method' -- The HTTP method for this form, either "get" or "post".

    returns -- An opening form tag for the request, plus hidden input
    elements for arguments to the request.

    The caller must add additional inputs, the submit input, and close
    the form tag."""

    # Generate the form tag.
    if method == "get":
        result = '<form method="get" action="%s">\n' % request.GetUrl()
    elif method == "post":
        result = '''<form method="post"
                          enctype="multipart/form-data"
                          action="%s">\n''' % request.GetUrl()
    else:
        raise ValueError, "unknown method %s" % method
    # Add hidden inputs for the request arguments.
    for name, value in request.items():
        result = result \
                 + '<input type="hidden" name="%s" value="%s">\n' \
                 % (name, value)

    return result


def make_url_button(url, text=None, on_click=None):
    """Generate HTML for a (non-form) action button.

    'url' -- The URL to link to.  If 'None', fill in a URL that does
    nothing.

    'text' -- Text to display in this button.

    'on_click' -- If not 'None', the onclick action for this
    button."""

    # If the button doesn't go anywhere, use a do-nothing URL.
    if url is None:
        url = "javascript: void(0)"
    # Generate the onclick attribute to the <a> tag, if required.
    if on_click is None:
        on_click = ""
    else:
        on_click = ' onclick="%s"' % on_click
    # Generate an <a> element, formatted appropriately.
    return '''
      <table cellpadding="4" cellspacing="0" border="1">
       <tr>
        <td><a href="%s" %s><font>%s</font></a></td>
       </tr>
      </table>
      ''' % (url, on_click, text)


def get_session(request, session_id):
    """Retrieve the session corresponding to 'session_id'.

    'request' -- A 'WebRequest' object for which to get the session.

    raises -- 'InvalidSessionError' if the session ID is invalid, or is
    invalid for this 'request'."""

    # Now's as good a time as any to clean up expired sessions.
    __clean_up_expired_sessions()

    try:
        # Obtain the session for this ID.
        session = sessions[session_id]
    except KeyError:
        # No session for this ID (note that it may have expired).
        raise InvalidSessionError, "invalid session ID"
    # Make sure the session is valid for this request.
    session.Validate(request)
    # Update the last access time.
    session.Touch()
    return session


def __clean_up_expired_sessions():
    """Remove any sessions that are expired."""

    for session_id, session in sessions.items():
        if session.IsExpired():
            del sessions[session_id]


def handle_login(request, default_redirect_url="/"):
    """Handle a login request.

    Authenticate the login using the user name and password stored in
    the '_login_user_name' and '_login_password' request fields,
    respectively.

    If authentication succeeds, redirect to the URL stored in the
    '_login_url' request field by raising an 'HttpRedirect', passing all
    other request fields along as well.

    If '_login_url' is not specified in the request, the value of
    'default_redirect_url' is used instead."""

    user_id = qm.user.authenticator.AuthenticateWebRequest(request)

    session = Session(request, user_id)
    session_id = session.GetId()

    # The URL of the page to which to redirect on successful login is
    # stored in the request.  Extract it.
    redirect_url = request.get("_login_url", default_redirect_url)
    # Generate a new request for that URL.  Copy other fields from the
    # old request.
    redirect_request = request.copy(redirect_url)
    # Sanitize the request by removing the user name, password, and
    # redirecting URL.
    del redirect_request["_login_user_name"]
    del redirect_request["_login_password"]
    del redirect_request["_login_url"]
    # Add the ID of the new session to the request.
    redirect_request.SetSessionId(session_id)
    # Generate a URL for the redirected page.
    url = make_url_for_request(redirect_request)
    # Redirect the client to this URL.
    raise HttpRedirect, url


########################################################################
# variables
########################################################################

sessions = {}
"""A mapping from session IDs to 'Session' instances."""

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
