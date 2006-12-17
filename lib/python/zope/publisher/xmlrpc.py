##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""XML-RPC Publisher

This module contains the XMLRPCRequest and XMLRPCResponse

$Id: xmlrpc.py 69027 2006-07-07 14:39:18Z philikon $
"""
import sys
import xmlrpclib
import datetime
from StringIO import StringIO

import zope.component
import zope.interface
from zope.interface import implements
from zope.publisher.interfaces.xmlrpc import \
        IXMLRPCPublisher, IXMLRPCRequest, IXMLRPCPremarshaller

from zope.publisher.http import HTTPRequest, HTTPResponse, DirectResult
from zope.security.proxy import isinstance

class XMLRPCRequest(HTTPRequest):
    implements(IXMLRPCRequest)

    _args = ()

    def _createResponse(self):
        """Create a specific XML-RPC response object."""
        return XMLRPCResponse()

    def processInputs(self):
        'See IPublisherRequest'
        # Parse the request XML structure

        # XXX using readlines() instead of lines()
        # as twisted's BufferedStream sends back
        # an empty stream here for read() (bug)
        lines = ''.join(self._body_instream.readlines())
        self._args, function = xmlrpclib.loads(lines)

        # Translate '.' to '/' in function to represent object traversal.
        function = function.split('.')

        if function:
            self.setPathSuffix(function)


class TestRequest(XMLRPCRequest):

    def __init__(self, body_instream=None, environ=None, response=None, **kw):

        _testEnv =  {
            'SERVER_URL':         'http://127.0.0.1',
            'HTTP_HOST':          '127.0.0.1',
            'CONTENT_LENGTH':     '0',
            'GATEWAY_INTERFACE':  'TestFooInterface/1.0',
            }

        if environ:
            _testEnv.update(environ)
        if kw:
            _testEnv.update(kw)
        if body_instream is None:
            body_instream = StringIO('')

        super(TestRequest, self).__init__(body_instream, _testEnv, response)


class XMLRPCResponse(HTTPResponse):
    """XMLRPC response.

    This object is responsible for converting all output to valid XML-RPC.
    """

    def setResult(self, result):
        """Sets the result of the response

        Sets the return body equal to the (string) argument "body". Also
        updates the "content-length" return header.

        If the body is a 2-element tuple, then it will be treated
        as (title,body)

        If is_error is true then the HTML will be formatted as a Zope error
        message instead of a generic HTML page.
        """
        body = premarshal(result)
        if isinstance(body, xmlrpclib.Fault):
            # Convert Fault object to XML-RPC response.
            body = xmlrpclib.dumps(body, methodresponse=True)
        else:
            # Marshall our body as an XML-RPC response. Strings will be sent
            # as strings, integers as integers, etc.  We do *not* convert
            # everything to a string first.
            try:
                body = xmlrpclib.dumps((body,), methodresponse=True,
                                       allow_none=True)
            except:
                # We really want to catch all exceptions at this point!
                self.handleException(sys.exc_info())
                return

        super(XMLRPCResponse, self).setResult(
            DirectResult((body,),
                         [('content-type', 'text/xml;charset=utf-8'),
                          ('content-length', str(len(body)))])
            )


    def handleException(self, exc_info):
        """Handle Errors during publsihing and wrap it in XML-RPC XML

        >>> import sys
        >>> resp = XMLRPCResponse()
        >>> try:
        ...     raise AttributeError('xyz')
        ... except:
        ...     exc_info = sys.exc_info()
        ...     resp.handleException(exc_info)

        >>> resp.getStatusString()
        '200 Ok'
        >>> resp.getHeader('content-type')
        'text/xml;charset=utf-8'
        >>> body = ''.join(resp.consumeBody())
        >>> 'Unexpected Zope exception: AttributeError: xyz' in body
        True
        """
        t, value = exc_info[:2]
        s = '%s: %s' % (getattr(t, '__name__', t), value)

        # Create an appropriate Fault object. Unfortunately, we throw away
        # most of the debugging information. More useful error reporting is
        # left as an exercise for the reader.
        Fault = xmlrpclib.Fault
        fault_text = None
        try:
            if isinstance(value, Fault):
                fault_text = value
            elif isinstance(value, Exception):
                fault_text = Fault(-1, "Unexpected Zope exception: " + s)
            else:
                fault_text = Fault(-2, "Unexpected Zope error value: " + s)
        except:
            fault_text = Fault(-3, "Unknown Zope fault type")

        # Do the damage.
        self.setResult(fault_text)
        # XML-RPC prefers a status of 200 ("ok") even when reporting errors.
        self.setStatus(200)

class PreMarshallerBase(object):
    """Abstract base class for pre-marshallers."""
    zope.interface.implements(IXMLRPCPremarshaller)

    def __init__(self, data):
        self.data = data

    def __call__(self):
        raise Exception, "Not implemented"

class DictPreMarshaller(PreMarshallerBase):
    """Pre-marshaller for dicts"""
    zope.component.adapts(dict)

    def __call__(self):
        return dict([(premarshal(k), premarshal(v))
                     for (k, v) in self.data.items()])

class ListPreMarshaller(PreMarshallerBase):
    """Pre-marshaller for list"""
    zope.component.adapts(list)

    def __call__(self):
        return map(premarshal, self.data)

class TuplePreMarshaller(ListPreMarshaller):
    zope.component.adapts(tuple)

class FaultPreMarshaller(PreMarshallerBase):
    """Pre-marshaller for xmlrpc.Fault"""
    zope.component.adapts(xmlrpclib.Fault)

    def __call__(self):
        return xmlrpclib.Fault(
            premarshal(self.data.faultCode),
            premarshal(self.data.faultString),
            )

class DateTimePreMarshaller(PreMarshallerBase):
    """Pre-marshaller for xmlrpc.DateTime"""
    zope.component.adapts(xmlrpclib.DateTime)

    def __call__(self):
        return xmlrpclib.DateTime(self.data.value)

class PythonDateTimePreMarshaller(PreMarshallerBase):
    """Pre-marshaller for datetime.datetime"""
    zope.component.adapts(datetime.datetime)

    def __call__(self):
        return xmlrpclib.DateTime(self.data.isoformat())

def premarshal(data):
    """Premarshal data before handing it to xmlrpclib for marhalling

    The initial purpose of this function is to remove security proxies
    without resorting to removeSecurityProxy.   This way, we can avoid
    inadvertently providing access to data that should be protected.
    """
    premarshaller = IXMLRPCPremarshaller(data, alternate=None)
    if premarshaller is not None:
        return premarshaller()
    return data
