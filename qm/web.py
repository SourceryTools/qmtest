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
import diagnostic
import DocumentTemplate
import errno
import htmlentitydefs
import md5
import os
import common
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
    available when generating all DTML files.

    This class also has an attribute, 'default_class', which is the
    default 'PageInfo' subclass to use when generating HTML.  By
    default, it is initialized to 'PageInfo' itself, but applications
    may derive a 'PageInfo' subclass and point 'default_class' to it to
    obtain customized behavior."""

    html_header = ""

    html_footer = ""

    table_attributes = 'cellspacing="0" border="0" cellpadding="4"'

    html_stylesheet = "/stylesheets/qm.css"

    common_javascript = '''
    <script language="JavaScript">
    function remove_from_set(select, contents)
    {
      if(select.selectedIndex != -1)
        select.options[select.selectedIndex] = null;
      update_from_select_list(select, contents);
      return false;
    }

    function add_to_set(select, contents, text, value)
    {
      var options = select.options;
      for(var i = 0; i < options.length; ++i)
        if(options[i].value == value)
          return false;
      if(value != "")
        options[options.length] = new Option(text, value);
      update_from_select_list(select, contents);
      return false;
    }

    function update_from_select_list(select, contents)
    {
      var result = "";
      for(var i = 0; i < select.options.length; ++i) {
        if(i > 0)
          result += ",";
        result += select.options[i].value;
      }
      contents.value = result;
    }

    function update_from_select(select, control)
    {
      if(select.selectedIndex != -1)
        control.value = select.options[select.selectedIndex].value;
    }

    var help_window = null;
    function show_help(help_page)
    {
      if(help_window != null && !help_window.closed)
        help_window.close();
      help_window = window.open("", "help",
                                "resizeable,toolbar,scrollbars");
      help_window.document.open("text/html", "replace");
      help_window.document.write(help_page);
      help_window.document.close();
    }

    var debug_window = null;
    function debug(msg)
    {
      if(debug_window == null || debug_window.closed) {
        debug_window = window.open("", "debug", "resizable");
        debug_window.document.open("text/plain", "replace");
      }
      debug_window.document.writeln(msg);
    }

    function move_option(src, dst)
    {
      if(src.selectedIndex == -1)
        return;
      var option = src[src.selectedIndex];
      dst[dst.length] = new Option(option.text, option.value);
      src[src.selectedIndex] = null;
    }

    function swap_option(select, offset)
    {
      var index = select.selectedIndex;
      if(index == -1)
        return;
      var new_index = index + offset;
      if(new_index < 0 || new_index >= select.length)
        return;
      
      var text = select[index].text;
      var value = select[index].value;
      select[index].text = select[new_index].text;
      select[index].value = select[new_index].value;
      select[new_index].text = text;
      select[new_index].value = value;

      select.selectedIndex = new_index;
    }
    </script>
    '''

    def __init__(self, request):
        """Create a new page.

        'request' -- A 'WebRequest' object containing the page
        request."""

        # Remember the request.
        self.request = request


    def GetProgramName(self):
        """Return the name of this application program."""

        return common.program_name


    def FormatStructuredText(self, text):
        """Return 'text' rendered as HTML."""

        return structured_text.to_html(text)


    def MakeUrl(self, script_name, **fields):
        """Create a request and return a URL to it.

        'script_name' -- The script name for the request.

        'fields' -- Additional fields for the request."""

        return apply(make_url, (script_name, self.request), fields)


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
''' % (self.html_stylesheet, self.GetProgramName(), description)


    def GenerateStartBody(self):
        """Return markup to start the body of the HTML document."""

        return "<body>"


    def GenerateEndBody(self):
        """Return markup to end the body of the HTML document."""

        return self.common_javascript + "</body>"


    def MakeLoginForm(self, redirect_request=None):
        if redirect_request is None:
            # No redirection specified, so redirect back to this page.
            redirect_request = self.request
        request = redirect_request.copy("login")
        request["_redirect_url"] = redirect_request.GetUrl()
        # Use a POST method to submit the login form, so that passwords
        # don't appear in web logs.
        form = qm.web.make_form_for_request(request,
                                            method="post",
                                            name="login_form")
        form = form + \
        '''
           <table cellpadding="0" cellspacing="0">
            <tr><td>User name:</td></tr>
            <tr><td>
             <input type="text"
                    size="16"
                    name="_login_user_name"/>
            </td></tr>
            <tr><td>Password:</td></tr>
            <tr><td>
             <input type="password"
                    size="16"
                    name="_login_password"/>
            </td></tr>
            <tr><td>
             <input type="button"
                    value=" Log In "
                    onclick="document.login_form.submit();"/>
            </td></tr>
           </table>
          </form>
        '''
        return form


    def MakeButton(self, title, script_url, **fields):
        """Generate HTML for a button to load a URL.

        'title' -- The button title.

        'script_url' -- The URL of the script.

        'fields' -- Additional fields to add to the script request.

        The resulting HTML must be included in a form."""

        request = apply(WebRequest, [script_url, self.request], fields)
        return make_button_for_request(title, request)


    def MakeUrlButton(self, title, url):
        """Generate HTML for an action button.

        The resulting HTML must be included in a form.  See
        'make_url_button'."""

        return make_button_for_url(title, url)


    def MakeHelpLink(self, tag, label="Help", **substitutions):
        return apply(make_help_link, (tag, label), substitutions)


    def MakeHelpLinkHtml(self, help_text, label="Help"):
        return make_help_link_html(help_text, label)


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


    def UserIsInGroup(self, group_id):
        """Return true if the user is a member of group 'group_id'.

        Checks the group membership of the user associated with the
        current session.

        If there is no group named 'group_id' in the user database,
        returns a false result."""

        user_id = self.request.GetSession().GetUserId()
        try:
            group = user.database.GetGroup(group_id)
        except KeyError:
            # No such group.
            return 0
        else:
            return user_id in group



PageInfo.default_class = PageInfo


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
            try:
                script_output = self.server.ProcessScript(request)
            except NoSessionError, msg:
                script_output = self.server.HandleNoSessionError(request, msg)
            except InvalidSessionError, msg:
                script_output = generate_login_form(request, msg)
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


    def __HandlePageCacheRequest(self, request):
        """Process a retrieval request from the global page cache."""

        # Get the page from the cache.
        page = get_from_cache(request, session_id=None)
        # Send it.
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "public")
        self.end_headers()
        self.wfile.write(page)
        

    def __HandleSessionCacheRequest(self, request):
        """Process a retrieval request from the session page cache."""

        # Extract the session ID.
        session_id = request.GetSessionId()
        if session_id is None:
            # We should never get request for pages from the session
            # cache without a session ID.
            self.send_error(400, "Missing session ID.")
            return
        # Get the page from the cache.
        page = get_from_cache(request, session_id)
        # Send it.
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "private")
        self.end_headers()
        self.wfile.write(page)
        

    def __HandleRequest(self, request):
        """Process a request from a GET or POST operation.

        'request' -- A 'WebRequest' object."""

        if request.GetScriptName() == _page_cache_name:
            # It's a request from the global page cache.
            self.__HandlePageCacheRequest(request)
        elif request.GetScriptName() == _session_cache_name:
            # It's a request from the session page cache.
            self.__HandleSessionCacheRequest(request)
        # Check if this request corresponds to a script.
        elif self.server.IsScript(request):
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
       returned.

    The server also provides a rudimentary manual caching mechanism for
    generated pages.  The application may insert a generated page into
    the page cache, if it is expected not to change.  The application
    can use this mechanism:

      - to supress duplicate generation of the same page,

      - or to pre-generate a page that may be requested later.  This is
        particularly handy if generating the page requires state
        information that would be difficult to reconstruct later.

    Pages may be shared across sessions, or may be specific to a
    particular session.

    The page cache is shared among all 'WebServer' instances.  Use the
    'cache_page' function to insert a page into the cache."""


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


    def HandleNoSessionError(self, request, message):
        """Handler when session is absent."""

        # There's no session specified in this request.  Try to
        # create a session for the default user.
        try:
            user_id = user.authenticator.AuthenticateDefaultUser()
        except user.AuthenticationError:
            # Couldn't get a default user session, so bail.
            return generate_login_form(request, message)
        # Authenticating the default user succeeded.  Create an implicit
        # session with the default user ID.
        session = Session(request, user_id)
        # Redirect to the same page but using the new session ID.
        request.SetSessionId(session.GetId())
        raise HttpRedirect, request.AsUrl()



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
                self.client_address = base.client_address


    def __str__(self):
        str = "WebRequest for %s\n" % self.__url
        for name, value in self.__fields.items():
            str = str + "%s=%s\n" % (name, repr(value))
        return str


    def GetUrl(self):
        """Return the URL of the script that processes this request."""

        return self.__url

    
    def GetScriptName(self):
        """Return the name of the script that processes this request.

        The script name is the final element of the full URL path."""

        return string.split(self.__url, "/")[-1]


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
            raise NoSessionError, qm.error("session required")
        else:
            return get_session(self, session_id)


    def AsUrl(self, last_argument=None):
        """Return the URL representation of this request.

        'fields_at_end' -- If not 'None', the name of the URL query
        arguments that should be placed last in the list of arugmnets
        (other than this, the order of query arguments is not
        defined)."""

        if len(self.keys()) == 0:
            # No query arguments; just use the script URL.
            return self.GetUrl()
        else:
            # Encode query arguments into the URL.
            return "%s?%s" % (self.GetUrl(), urllib.urlencode(self))


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

    def __init__(self, request, user_id, expiration_timeout=21600):
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
        # FIXME: Security: Is this OK?
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
            raise InvalidSessionError, qm.error("session wrong IP")
        # Make sure the session hasn't expired.
        if self.IsExpired():
            raise InvalidSessionError, qm.error("session expired")



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

    script_url = urllib.unquote(script_url)
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


def escape(text):
    """Escape special characters in 'text' for formatting as HTML."""

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


def make_url(script_name, base_request=None, **fields):
    """Create a request and return a URL for it.

    'script_name' -- The script name for the request.

    'base_request' -- If not 'None', the base request for the generated
    request.

    'fields' -- Additional fields to include in the request."""

    request = apply(WebRequest, (script_name, base_request), fields)
    return request.AsUrl()


def make_form_for_request(request, method="get", name=None):
    """Generate an opening form tag for 'request'.

    'request' -- A 'WebRequest' object.

    'method' -- The HTTP method for this form, either "get" or "post".

    'name' -- The name of this form, or 'None'.

    returns -- An opening form tag for the request, plus hidden input
    elements for arguments to the request.

    The caller must add additional inputs, the submit input, and close
    the form tag."""

    if name is not None:
        name_attribute = 'name="%s"' % name
    else:
        name_attribute = ''
    # Generate the form tag.
    if method == "get":
        result = '<form method="get" action="%s" %s>\n' \
                 % (request.GetUrl(), name_attribute)
    elif method == "post":
        result = '''<form %s
                          method="post"
                          enctype="multipart/form-data"
                          action="%s">\n''' \
        % (name_attribute, request.GetUrl())
    else:
        raise ValueError, "unknown method %s" % method
    # Add hidden inputs for the request arguments.
    for name, value in request.items():
        result = result \
                 + '<input type="hidden" name="%s" value="%s">\n' \
                 % (name, value)

    return result


def make_button_for_request(title, request):
    """Generate HTML for a button.

    Note that the caller is responsible for making sure the resulting
    button is placed within a form element.

    'title' -- The button label.

    'request' -- A 'WebRequest' object to be invoked when the button is
    clicked."""

    return make_button_for_url(title, request.AsUrl())


def make_button_for_url(title, url):
    """Generate HTML for a button.

    Note that the caller is responsible for making sure the resulting
    button is placed within a form element.

    'title' -- The button label.

    'url' -- The URL to load when the button is clicked.."""

    return '''
    <input type="button"
           value=" %s "
           onclick="location = '%s';"/>
    ''' % (title, url)


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
        raise InvalidSessionError, qm.error("session invalid")
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
    '_redirect_url' request field by raising an 'HttpRedirect', passing
    all other request fields along as well.

    If '_redirect_url' is not specified in the request, the value of
    'default_redirect_url' is used instead."""

    # The URL of the page to which to redirect on successful login is
    # stored in the request.  Extract it.
    redirect_url = request.get("_redirect_url", default_redirect_url)

    try:
        user_id = qm.user.authenticator.AuthenticateWebRequest(request)
    except qm.user.AuthenticationError:
        # Incorrect user name or password.  Show the login form.
        message = qm.error("invalid login")
        redirect_request = WebRequest(redirect_url)
        return generate_login_form(redirect_request, message)
    except qm.user.AccountDisabledError:
        # Log in to a disabled account.  Show the login form again.
        message = qm.error("disabled account")
        redirect_request = WebRequest(redirect_url)
        return generate_login_form(redirect_request, message)

    session = Session(request, user_id)
    session_id = session.GetId()

    # Generate a new request for that URL.  Copy other fields from the
    # old request.
    redirect_request = request.copy(redirect_url)
    # Sanitize the request by removing the user name, password, and
    # redirecting URL.
    del redirect_request["_login_user_name"]
    del redirect_request["_login_password"]
    if redirect_request.has_key("_redirect_url"):
        del redirect_request["_redirect_url"]
    # Add the ID of the new session to the request.
    redirect_request.SetSessionId(session_id)
    # Redirect the client to the URL for the redirected page.
    raise HttpRedirect, redirect_request.AsUrl()


def handle_logout(request, default_redirect_url="/"):
    """Handle a logout request.

    prerequisite -- 'request' must be in a valid session, which is
    ended.

    After ending the session, redirect to the URL specified by the
    '_redirect_url' field of 'request'.  If '_redirect_url' is not
    specified in the request, the value of 'default_redirect_url' is
    used instead."""

    # Delete the session.
    session_id = request.GetSessionId()
    del sessions[session_id]
    # Construct a redirecting URL.  The target is contained in the
    # '_redirect_url' field.
    redirect_url = request.get("_redirect_url", default_redirect_url)
    redirect_request = request.copy(redirect_url)
    if redirect_request.has_key("_redirect_url"):
        del redirect_request["_redirect_url"]
    del redirect_request[session_id_field]
    # Redirect to the specified request.
    raise HttpRedirect, redirect_request.AsUrl()


def generate_html_from_dtml(template_name, page_info):
    """Return HTML generated from a DTML tempate.

    'template_name' -- The name of the DTML template file.

    'page_info' -- A 'PageInfo' instance to use as the DTML namespace.

    returns -- The generated HTML source."""
    
    # Construct the path to the template file.  DTML templates are
    # stored in qm/qm/track/web/templates. 
    template_path = os.path.join(qm.get_share_directory(), "dtml", 
                                 template_name)
    # Generate HTML from the template.
    html_file = DocumentTemplate.HTMLFile(template_path)
    return html_file(page_info)


def generate_error_page(request, error_text):
    """Generate a page to indicate a user error.

    'request' -- The request that was being processed when the error
    was encountered.

    'error_text' -- A description of the error, as structured text.

    returns -- The generated HTML source for the page."""

    page_info = PageInfo(request)
    page_info.error_text = qm.web.format_structured_text(error_text)
    return generate_html_from_dtml("error.dtml", page_info)


def generate_login_form(redirect_request, message=None):
    """Show a form for user login.

    'message' -- If not 'None', a message to display to the user."""

    page_info = PageInfo.default_class(redirect_request)
    page_info.message = message
    return generate_html_from_dtml("login_form.dtml", page_info)


def make_set_control(form_name,
                     field_name,
                     add_page,
                     select_name=None,
                     initial_elements=[],
                     request=None,
                     rows=6,
                     width=200,
                     window_width=480,
                     window_height=240):
    """Construct a control for representing a set of items.

    'form_name' -- The name of form in which the control is included.

    'field_name' -- The name of the input control that contains an
    encoded representation of the set's elements.  See
    'encode_set_control_contents' and 'decode_set_control_contents'.

    'select_name' -- The name of the select control that displays the
    elements of the set.  If 'None', a control name is generated
    automatically. 

    'add_request' -- If not 'None', a 'WebRequest' object which is
    invoked when the user selects the "Add..." button to add a new
    element to the set.

    'add_page' -- If not 'None', the HTML source for a popup web page
    that is displayed in response to the "Add..." button.

    'initial_elements' -- The initial elements of the set.

    'rows' -- The number of rows for the select control.

    'width' -- The width of the select control.

    'window_width', 'window_height' -- The width and height of the popup
    window for adding a new element.

    Exactly one of 'add_request' and 'add_page' should be specified.
    """

    # Generate a name for the select control if none was specified.
    if select_name is None:
        select_name = "_set_" + field_name

    # Construct the select control.
    select = '<select name="%s" size="%d" width="%d">\n' \
             % (select_name, rows, width)
    # Add an option for each initial element.
    for text, value in initial_elements:
        select = select + \
                 '<option value="%s">%s</option>\n' % (value, text)
    select = select + '</select>\n'

    # Construct the hidden control contianing the set's elements.  Its
    # initial value is the encoding of the initial elements.
    initial_values = map(lambda x: x[1], initial_elements)
    initial_value = encode_set_control_contents(initial_values)
    contents = '<input type="hidden" name="%s" value="%s"/>' \
               % (field_name, initial_value)

    # Construct a unique name for the JavaScript function for responding
    # to the "Add..." button.
    global _counter
    add_function = "_set_add_%d" % _counter
    _counter = _counter + 1
    # Construct the "Add..." button.
    add_button = make_button_for_popup("Add", add_page, request,
                                       window_width, window_height)
    # Construct the "Remove" button.
    remove_button = '''
    <input type="button"
           size="12"
           value=" Remove "
           onclick="remove_from_set(document.%s.%s, document.%s.%s);"
    />''' % (form_name, select_name, form_name, field_name)

    # Arrange everything in a table to control the layout.
    return contents + '''
    <table border="0" cellpadding="0" cellspacing="0"><tbody>
     <tr valign="top">
      <td>
       %s
      </td>
      <td>&nbsp;</td>
      <td>
       %s
       <br>
       %s
      </td>
     </tr>
    </tbody></table>
    ''' % (select, add_button, remove_button)


def encode_set_control_contents(values):
    """Encode 'values' for a set control.

    'values' -- A sequence of values of elements of the set.

    returns -- The encoded value for the control field."""

    return string.join(values, ",")


def decode_set_control_contents(content_string):
    """Decode the contents of a set control.

    'content_string' -- The text of the form field containing the
    encoded set contents.

    returns -- A sequence of the values of the elements of the set."""

    # Oddly, if the set is empty, there are sometimes spurious spaces in
    # field entry.  This may be browser madness.  Handle it specially.
    if string.strip(content_string) == "":
        return []
    return string.split(content_string, ",")


def make_javascript_string(text):
    """Return 'text' represented as a JavaScript string literal."""

    text = string.replace(text, "\\", r"\\")
    text = string.replace(text, "'", r"\'")
    text = string.replace(text, "\"", r'\"')
    text = string.replace(text, "\n", r"\n")
    # Escape less-than signs so browsers don't look for HTML tags
    # inside the literal. 
    text = string.replace(text, "<", r"\074")
    return "'" + text + "'"


def make_help_link(help_text_tag, label, **substitutions):
    """Make a link to pop up help text.

    'help_text_tag' -- A message tag for the help diagnostic.

    'label' -- The help link label.

    'substitutions' -- Substitutions to the help diagnostic."""
    
    # Construct the help text.
    help_text = apply(diagnostic.help_set.Generate,
                      (help_text_tag, "help", None),
                      substitutions)
    # Convert it to HTML.
    help_text = qm.structured_text.to_html(help_text)
    # Make the link.
    return make_help_link_html(help_text, label)


def make_help_link_html(help_text, label):
    """Make a link to pop up help text.

    'help_text' -- HTML source for the help text.

    'label' -- The help link label."""

    global _counter

    # Wrap the help text in a complete HTML page.
    page_info = PageInfo(WebRequest(""))
    page_info.help_text = help_text
    help_page = generate_html_from_dtml("help.dtml", page_info)
    # Embed the page in a JavaScript string literal.
    help_page = make_javascript_string(help_page)

    # Construct the name for the JavaScript variable which will hold the
    # help page. 
    help_variable_name = "_help_text_%d" % _counter
    _counter = _counter + 1

    # Construct the link.
    return \
    '''<a class="help-link"
          href="javascript: void(0)"
          onclick="show_help(%s);">%s</a>
    <script language="JavaScript">
    var %s = %s;
    </script>
    ''' % (help_variable_name, label, help_variable_name, help_page)


def make_popup_dialog(message, buttons, title=""):
    """Generate JavaScript to show a popup dialog box.

    The popup dialog box displays a message and one or more buttons.
    Each button can have a JavaScript statement (or statements)
    associated with it; if the button is clicked, the statement is
    invoked.  After any button is clicked, the popup window is closed as
    well.

    'message' -- HTML source of the message to display in the popup
    window.

    'buttons' -- A sequence of button specifications.  Each is a pair
    '(caption, script)'.  'caption' is the button caption.  'script' is
    the JavaScript statement to invoke when the button is clicked, or
    'None'.

    'title' -- The popup window title.

    returns -- JavaScript statements to show the dialog box, suiteable
    for use as an event handler."""

    # Construct the popup page.
    page = make_popup_page(message, buttons, title)
    page_url = cache_page(page).AsUrl()
    # Construct the JavaScript variable and function.
    return "window.open('%s', 'popup', 'width=480,height=200,resizable')" \
           % page_url


def make_confirmation_dialog(message, url):
    """Generate JavaScript for a confirmation dialog box.

    'url' -- The location in the main browser window is set to the URL
    if the user confirms the action.

    See 'make_popup_dialog_script' for a description of 'function_name'
    and 'message' and information on how to use the return value."""

    # If the user clicks the "Yes" button, advance the main browser
    # page. 
    open_script = "window.opener.document.location = %s;" \
                  % make_javascript_string(url)
    # Two buttons: "Yes" and "No".  "No" doesn't do anything.
    buttons = [
        ( "Yes", open_script ),
        ( "No", None ),
        ]
    return make_popup_dialog(message, buttons, title="Confirm")


def make_popup_page(message, buttons, title=""):
    """Generate a popup dialog box page.

    See 'make_popup_dialog_script' for an explanation of the
    parameters."""
    
    page = \
    '''<html>
     <head>
      <title>%s</title>
      <meta http-equiv="Content-Style-Type" content="text/css"/>
      <link rel="stylesheet" type="text/css" href="/stylesheets/qm.css"/>
     </head>
     <body class="popup">
      <table border="0" cellpadding="0" cellspacing="8" width="100%%">
       <tr><td>
        %s
       </td></tr>
       <tr><td align="right">
        <form name="navigation">
    ''' % (title, message)
    # Generate the buttons.
    for caption, script in buttons:
        page = page + '''
        <input type="button"
               value=" %s "''' % caption
        # Whether a script was specified for the button, close the popup
        # window. 
        if script is None:
            page = page + '''
               onclick="window.close();"'''
        else:
            page = page + '''
               onclick="%s; window.close();"''' % script
        page = page + '''
               />'''
    # End the page.
    page = page + '''
        </form>
       </td></tr>
      </table>
     </body>
    </html>
    '''
    return page


def make_select(field_name,
                items,
                default_value,
                item_to_text=str,
                item_to_value=str,
                form_name="form"):
    """Construct HTML controls for selecting an item from a list.

    'field_name' -- The name of the form control which will contain the
    currently-selected item.  This is a hidden control; the actual HTML
    select control is given a different name.

    'items' -- A sequence of items.  The items may be of any type.

    'default_value' -- The item which should initially be selected.  The
    value must appear in 'items'.

    'item_to_text' -- A function that returns the text representation of
    an item.

    'item_to_value' -- A function that returns the value representation
    of an item.

    'form_name' -- The name of the form that will contain the returned
    controls. 

    returns -- The HTML text for the controls.  

    For each item, 'item_to_text' and 'item_to_value' are used to
    construct the text and value attributes for the corresponding HTML
    select option."""

    assert default_value in items

    select_name = "_select_" + field_name
    # Add a hidden control with the specified field name.  This
    # input will contain the value of the currently-selected
    # UID.
    result = '<input type="hidden" name="%s" value="%s"/>' \
             % (field_name, item_to_value(default_value))
    # Write the handler to update the hidden control when the
    # selection changes in the select control.
    on_change = "update_from_select(document.%s.%s, " \
                "document.%s.%s)" \
                % (form_name, select_name, form_name, field_name)
    # Generate a '<select>' control droplist.
    result = result + '<select name="%s" onchange="%s">\n' \
             % (select_name, on_change)
    # Generate an '<option>' element for each item.
    for item in items:
        # Specify the 'select' attribute if this item represents the
        # default value.
        if item == default_value:
            is_selected = "selected"
        else:
            is_selected = ""
        result = result + '<option value="%s" %s>%s</option>\n' \
                 % (item_to_value(item), is_selected, item_to_text(item))
    result = result + '</select>\n'
    return result
    

def make_choose_control(field_name,
                        included_label,
                        included_items,
                        excluded_label,
                        excluded_items,
                        item_to_text=str,
                        item_to_value=str,
                        ordered=0):
    """Construct HTML controls for selecting a subset.

    The user is presented with two list boxes next to each other.  The
    box on the left lists items included in the subset.  The box on the
    right lists items excluded from the subset but available for
    inclusion.  Between the boxes are buttons for adding and removing
    items from the subset.

    If 'ordered' is true, buttons are also shown for reordering items in
    the included list.

    'field_name' -- The name of an HTML hidden form field that will
    contain an encoding of the items included in the subset.  The
    encoding consists of the values corresponding to included items, in
    a comma-separated list.

    'included_label' -- HTML source for the label for the left box,
    which displays the included items.

    'included_items' -- Items initially included in the subset.  This is
    a sequence of arbitrary objects or values.

    'excluded_label' -- HTML source for the label for the right box,
    which displays the items available for inclusion but not currently
    included.

    'excluded_items' -- Items not initially included but available for
    inclusion.  This is a sequence of arbitrary objects or values.

    'item_to_text' -- A function that produces a user-visible text
    description of an item.

    'item_to_value' -- A function that produces a value for an item,
    used as the value for an HTML option object.

    'ordered' -- If true, additional controls are displayed to allow the
    user to manipulate the order of items in the included set.

    returns -- HTML source for the items.  Must be placed in a
    form."""
    
    # We'll construct an array of buttons.  Each element is an HTML
    # input control.
    buttons = []
    # Construct the encoding for the items initially included.
    initial_value = string.join(map(item_to_value, included_items), ",")
    # The hidden control that will contain the encoded representation of
    # the included items.
    hidden_control = '<input type="hidden" name="%s" value="%s">' \
                     % (field_name, initial_value)
    # Construct names for the two select controls.
    included_select_name = "_inc_" + field_name
    excluded_select_name = "_exc_" + field_name

    # The select control for included items.  When the user selects an
    # item in this list, deselect the selected item in the excluded
    # list, if any.
    included_select = '''
    <select name="%s"
            width="160"
            size="8"
            onchange="document.form.%s.selectedIndex = -1;">''' \
    % (included_select_name, excluded_select_name)
    # Build options for items initially selected.
    for item in included_items:
        option = '<option value="%s">%s</option>\n' \
                 % (item_to_value(item), item_to_text(item))
        included_select = included_select + option
    included_select = included_select + '</select>\n'

    # The select control for excluded items.  When the user selects an
    # item in this list, deselect the selected item in the included
    # list, if any.
    excluded_select = '''
    <select name="%s"
            width="160"
            size="8"
            onchange="document.form.%s.selectedIndex = -1;">''' \
    % (excluded_select_name, included_select_name)
    # Build options for items initially excluded.
    for item in excluded_items:
        option = '<option value="%s">%s</option>\n' \
                 % (item_to_value(item), item_to_text(item))
        excluded_select = excluded_select + option
    excluded_select = excluded_select + '</select>\n'

    # The Add button.
    button = '''
    <input type="button"
           value=" << Add "
           onclick="move_option(document.form.%s, document.form.%s);
                    update_from_select_list(document.form.%s,
                                            document.form.%s);">
    ''' % (excluded_select_name, included_select_name,
           included_select_name, field_name)
    buttons.append(button)

    # The Remove button.
    button = '''
    <input type="button"
           value=" Remove >> "
           onclick="move_option(document.form.%s, document.form.%s);
                    update_from_select_list(document.form.%s,
                                            document.form.%s);">
    ''' % (included_select_name, excluded_select_name,
           included_select_name, field_name)
    buttons.append(button)

    if ordered:
        # The Move Up button.
        button = '''
        <input type="button"
               value=" Move Up "
               onclick="swap_option(document.form.%s, -1);
                        update_from_select_list(document.form.%s,
                                                document.form.%s);">
        ''' % (included_select_name, included_select_name, field_name)

        buttons.append(button)

        # The Move Down button.
        button = '''
        <input type="button"
               value=" Move Down "
               onclick="swap_option(document.form.%s, 1);
                        update_from_select_list(document.form.%s,
                                                document.form.%s);">
        ''' % (included_select_name, included_select_name, field_name)
        buttons.append(button)

    # Arrange everything properly.
    buttons = string.join(buttons, "\n<br>\n")
    return '''
    %(hidden_control)s
    <table border="0" cellpadding="0" cellspacing="0">
     <tr valign="center">
      <td>
       %(included_label)s:
       <br>
       %(included_select)s
      </td>
      <td align="center">
       %(buttons)s
      </td>
      <td>
       %(excluded_label)s:<br>
       %(excluded_select)s
      </td>
     </tr>
    </table>
    ''' % locals()


_netscape_is_broken = "yea, verily"
if not _netscape_is_broken:

    # It would be nice to embed the popup window's HTML page directly
    # into the containing document.  The following is one way this might
    # be implemented.  Bugs in Netscape prevent this from working
    # correctly for many popup pages, though, and at the moment we're
    # not aware of any workarounds for the bugs.

    def make_button_for_popup(label,
                              html_text,
                              window_width=480,
                              window_height=240):
        """Construct a button for displaying a popup page.

        'label' -- The button label.

        'html_text' -- The HTML source of the popup page.

        'window_width' -- The width, in pixels, of the popup window.

        'window_height' -- The height, in pixels, of the popup window.

        returns -- HTML source for the button.  The button must be placed
        within a form element."""

        # Construct names for the variable which will contain the HTML text,
        # and the function for showing the popup window.
        global _counter
        variable_name = "_page_%d" % _counter
        function_name = "_popup_%d" % _counter
        _counter = _counter + 1
        # The HTML text is encoded in a JavaScript string literal.
        html_text_string = make_javascript_string(html_text)
        # Construct arguments for 'Window.open'.
        window_args = "resizeable,width=%d,height=%s" \
                      % (window_width, window_height)
        # Generate it.
        return """
        <input type="button"
               value=" %(label)s "
               onclick="%(function_name)s();">
        <script language="JavaScript">
        var %(variable_name)s = %(html_text_string)s;
        function %(function_name)s ()
        {
          window.open('javascript: window.opener.%(variable_name)s;',
                      'popup', '%(window_args)s');
        }
        </script>
        """ % locals()


def make_button_for_popup(label,
                          html_text,
                          request=None,
                          window_width=480,
                          window_height=240):
    """Construct a button for displaying a popup page.

    'label' -- The button label.

    'html_text' -- The HTML source of the popup page.

    'window_width' -- The width, in pixels, of the popup window.

    'window_height' -- The height, in pixels, of the popup window.

    returns -- HTML source for the button.  The button must be placed
    within a form element."""

    # Place the page in the page cache.
    if request is None:
        session_id = None
    else:
        session_id = request.GetSessionId()
    page_url = cache_page(html_text, session_id).AsUrl()

    # Construct arguments for 'Window.open'.
    window_args = "resizeable,width=%d,height=%s" \
                  % (window_width, window_height)
    # Generate it.
    return """
    <input type="button"
           value=" %(label)s "
           onclick="window.open('%(page_url)s',
                                'popup',
                                '%(window_args)s');">
    """ % locals()


def cache_page(page_text, session_id=None):
    """Cache an HTML page.

    'page_text' -- The text of the page.

    'session_id' -- The session ID for this page, or 'None'.

    returns -- A 'WebRequest' object with which the cached page can be
    retrieved later.

    If 'session_id' is 'None', the page is placed in the global page
    cache.  Otherwise, it is placed in the session page cache for that
    session."""

    global _page_cache_path
    global _counter

    if _page_cache_path is None:
        # This is the first time we're inserting anything in the cache.
        # Set it up.
        _page_cache_path = common.make_temporary_directory()
        os.mkdir(os.path.join(_page_cache_path, "sessions"), 0700)
        # Clean up the cache at exit.
        cleanup_function = lambda path=_page_cache_path: \
                           common.remove_directory_recursively(path)
        common.add_exit_function(cleanup_function)

    if session_id is None:
        # No path was specified.  Place the file in the top directory.
        dir_path = _page_cache_path
        script_name = _page_cache_name
    else:
        # A session was specified.  Put the file in a subdirectory named
        # after the session.
        dir_path = os.path.join(_page_cache_path, "sessions", session_id)
        script_name = _session_cache_name
        # Create that directory if it doesn't exist.
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path, 0700)

    # Generate a name for the page.
    page_name = str(_counter)
    _counter = _counter + 1
    # Write it.
    page_file_name = os.path.join(dir_path, page_name)
    page_file = open(page_file_name, "w", 0600)
    page_file.write(page_text)
    page_file.close()

    # Return a request for this page.
    request = WebRequest(script_name, page=page_name)
    if session_id is not None:
        request.SetSessionId(session_id)
    return request


def get_from_cache(request, session_id=None):
    """Retrieve a page from the page cache.

    'request' -- The URL requesting the page from the cache.

    'session_id' -- The session ID for the request, or 'None'.

    returns -- The cached page, or a placeholder page if the page was
    not found in the cache.

    If 'session_id' is 'None', the page is retrieved from the global
    page cache.  Otherwise, it is retrieved from the session page cache
    for that session."""
    
    if session_id is None:
        dir_path = _page_cache_path
    else:
        # Construct the path to the directory containing pages in the
        # cache for 'session_id'.
        dir_path = os.path.join(_page_cache_path, "sessions", session_id)

    # Construct the path to the file containing the page.
    page_name = request["page"]
    page_file_name = os.path.join(dir_path, page_name)
    if os.path.isfile(page_file_name):
        # Return the page.
        return open(page_file_name, "r").read()
    else:
        # Oops, no such page.  Generate a placeholder.
        return """
        <html>
         <body>
          <h3>Cache Error</h3>
          <p>You have requested a page that no longer is in the server's
          cache.  The server may have been restarted, or the page may
          have expired.  Please start over.</p>
          <!-- %s -->
         </body>
        </html>
        """ % url


########################################################################
# variables
########################################################################

sessions = {}
"""A mapping from session IDs to 'Session' instances."""

_counter = 0
"""A counter for generating somewhat-unique names."""

_page_cache_path = None
"""The path to the page cache."""

_page_cache_name = "page-cache"
"""The URL prefix for the global page cache."""

_session_cache_name = "session-cache"
"""The URL prefix for the session page cache."""

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
