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
import os
import qm.common
import SimpleHTTPServer
import string
import sys
import traceback
import types
import urllib
import xmlrpclib

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
        self.__HandleRequest(request)


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
        self.wfile.flush()
        self.connection.shutdown(1)


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
        except:
            # Oops, the script raised an exception.  Show
            # information about the exception instead.
            script_output = format_exception(sys.exc_info())
        # Send its output.
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(script_output)


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



class WebServer(BaseHTTPServer.HTTPServer):
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


    def __init__(self, port, log_file=sys.stderr, xml_rpc_path=None):
        """Create a new web server.

        'port' -- The port on which to accept connections.

        'log_file' -- A file object to which to write log messages.
        If it's 'None', no logging.

        'xml_rpc_path' -- The script path at which to accept XML-RPC
        requests.   If 'None', XML-RPC is disabled for this server.

        The server is not started until the 'Run' method is invoked."""

        self.__port = port
        self.__log_file = log_file
        self.__scripts = {}
        self.__translations = {}
        self.__xml_rpc_methods = {}
        self.__xml_rpc_path = xml_rpc_path
        # Don't call the base class __init__ here, since we don't want
        # to create the web server just yet.  Instead, we'll call it
        # when it's time to run the server.


    def GetXmlRpcUrl(self):
        """Return the URL at which this server accepts XML-RPC.

        returns -- The URL, or 'None' if XML-RPC is disabled."""

        if self.__xml_rpc_path is None:
            return None
        else:
            return "http://%s:%d%s" % (qm.common.get_host_name(),
                                       self.__port, self.__xml_rpc_path) 


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
        page it generates.

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


    def Run(self):
        """Start the web server."""

        # Initialize the base class here.  This causes the server to start.
        BaseHTTPServer.HTTPServer.__init__(self, ('', self.__port), 
                                           WebRequestHandler)
        self.serve_forever()


    def LogMessage(self, message):
        """Log a message."""
        
        if self.__log_file is not None:
            self.__log_file.write(message)
            self.__log_file.flush()



class WebRequest:
    """An object representing a request from the web server.

    A 'WebRequest' object behaves as a dictionary of key, value pairs
    representing query arguments, for instance query fields in a POST,
    or arguments encoded in a URL query string.  It has some other
    methods as well."""

    def __init__(self, script_url, **fields):
        """Create a new request object.

        'script_url' -- The URL of the script that processes this
        query.

        'fields' -- The query arguments."""

        self.__url = script_url
        self.__fields = fields


    def __str__(self):
        str = "WebRequest for %s\n" % self.__url
        for name, value in self.__fields.items():
            str = str + "%s=%s\n" % (name, value)
        return str


    def GetUrl(self):
        """Return the URL of the script that processes this request."""

        return self.__url

    
    def __getitem__(self, key):
        return self.__fields[key]


    def __setitem__(self, key, value):
        self.__fields[key] = value


    def __delitem__(self, key):
        del self.__fields[key]


    def keys(self):
        return self.__fields.keys()


    def has_key(self, key):
        return self.__fields.has_key(key)


    def items(self):
        return self.__fields.items()
    

    def copy(self):
        """Return a duplicate of this request."""

        return apply(WebRequest, (self.__url, ), self.__fields.copy())



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


def escape(text):
    """Escape characters in 'text' for formatting as HTML."""

    if text == "":
        return "&nbsp;"

    # FIXME.  Make this more general, and more efficient.
    text = string.replace(text, "&", "&amp;")
    text = string.replace(text, "<", "&lt;")
    text = string.replace(text, ">", "&gt;")
    text = string.replace(text, '"', "&quot;")
    return text


def format_structured_text(text):
    """Render 'text' as HTML."""

    # FIXME.
    return escape(text)


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
    

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
