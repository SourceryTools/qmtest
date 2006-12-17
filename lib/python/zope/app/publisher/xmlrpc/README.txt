XML-RPC views
=============

XML-RPC Methods
---------------

There are two ways to write XML-RPC views. You can write views that
provide "methods" for other objects, and you can write views that have
their own methods.  Let's look at the former case first, since it's a
little bit simpler.

Let's write a view that returns a folder listing:

  >>> class FolderListing:
  ...     def contents(self):
  ...         return list(self.context.keys())

Now we'll register it as a view:

  >>> from zope.configuration import xmlconfig
  >>> ignored = xmlconfig.string("""
  ... <configure
  ...     xmlns="http://namespaces.zope.org/zope"
  ...     xmlns:xmlrpc="http://namespaces.zope.org/xmlrpc"
  ...     >
  ...   <!-- We only need to do this include in this example,
  ...        Normally the include has already been done for us. -->
  ...   <include package="zope.app.publisher.xmlrpc" file="meta.zcml" />
  ...
  ...   <xmlrpc:view
  ...       for="zope.app.folder.folder.IFolder"
  ...       methods="contents"
  ...       class="zope.app.publisher.xmlrpc.README.FolderListing"
  ...       permission="zope.ManageContent"
  ...       />
  ... </configure>
  ... """)

Now, we'll add some items to the root folder:

  >>> print http(r"""
  ... POST /@@contents.html HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 73
  ... Content-Type: application/x-www-form-urlencoded
  ...
  ... type_name=BrowserAdd__zope.app.folder.folder.Folder&new_value=f1""")
  HTTP/1.1 303 See Other
  ...

  >>> print http(r"""
  ... POST /@@contents.html HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 73
  ... Content-Type: application/x-www-form-urlencoded
  ...
  ... type_name=BrowserAdd__zope.app.folder.folder.Folder&new_value=f2""")
  HTTP/1.1 303 See Other
  ...

And call our xmlrpc method:

  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 102
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>contents</methodName>
  ... <params>
  ... </params>
  ... </methodCall>
  ... """)
  HTTP/1.0 200 Ok
  Content-Length: 208
  Content-Type: text/xml;charset=utf-8
  <BLANKLINE>
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><array><data>
  <value><string>f1</string></value>
  <value><string>f2</string></value>
  </data></array></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>


Note that we get an unauthorized error if we don't supply authentication
credentials:

  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Content-Length: 102
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>contents</methodName>
  ... <params>
  ... </params>
  ... </methodCall>
  ... """)
  HTTP/1.0 401 Unauthorized
  Content-Length: 126
  Content-Type: text/xml;charset=utf-8
  WWW-Authenticate: basic realm="Zope"
  <BLANKLINE>
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><string></string></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>

Named XML-RPC Views
-------------------

Now let's look at views that have their own methods or other
subobjects.  Views that have their own methods have names that appear
in URLs and they get traversed to get to their methods, as in::

   .../somefolder/listing/contents

To make this possible, the view has to support traversal, so that,
when it is traversed, it traverses to its attributes.  To support
traversal, you can implement or provide an adapter to
`zope.publisher.interfaces.IPublishTraverse`. It's actually better to
provide an adapter so that accesses to attributes during traversal are
mediated by the security machinery.  (Object methods are always bound
to unproxied objects, but adapters are bound to proxied objects unless
they are trusted adapters.)

The 'zope.app.publisher.xmlrpc' package provides a base class,
`MethodPublisher`,  that provides the necessary traversal support.  In
particulat, it has an adapter that simply traverses to attributes.

If an XML-RPC view isn't going to be public, then it also has to
implement 'zope.location.ILocation' so that security grants can be
acquired for it, at least with Zope's default security policy. The
`MethodPublisher` class does that too.

Let's modify our view class to use `MethodPublisher`:

  >>> from zope.app.publisher.xmlrpc import MethodPublisher

  >>> class FolderListing(MethodPublisher):
  ...
  ...     def contents(self):
  ...         return list(self.context.keys())

Note that `MethodPublisher` also provides a suitable `__init__`
method, so we don't need one any more.  This time, we'll register it
as as a named view:

  >>> ignored = xmlconfig.string("""
  ... <configure
  ...     xmlns="http://namespaces.zope.org/zope"
  ...     xmlns:xmlrpc="http://namespaces.zope.org/xmlrpc"
  ...     >
  ...   <!-- We only need to do this include in this example,
  ...        Normally the include has already been done for us. -->
  ...   <include package="zope.app.publisher.xmlrpc" file="meta.zcml" />
  ...
  ...   <xmlrpc:view
  ...       name="listing"
  ...       for="zope.app.folder.folder.IFolder"
  ...       methods="contents"
  ...       class="zope.app.publisher.xmlrpc.README.FolderListing"
  ...       permission="zope.ManageContent"
  ...       />
  ... </configure>
  ... """)

Now, when we access the `contents`, we do so through the listing view:

  >>> print http(r"""
  ... POST /listing/ HTTP/1.0
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 102
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>contents</methodName>
  ... <params>
  ... </params>
  ... </methodCall>
  ... """)
  HTTP/1.0 200 Ok
  Content-Length: 208
  Content-Type: text/xml;charset=utf-8
  <BLANKLINE>
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><array><data>
  <value><string>f1</string></value>
  <value><string>f2</string></value>
  </data></array></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>

as before, we will get an error if we don't supply credentials:

  >>> print http(r"""
  ... POST /listing/ HTTP/1.0
  ... Content-Length: 102
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>contents</methodName>
  ... <params>
  ... </params>
  ... </methodCall>
  ... """)
  HTTP/1.0 401 Unauthorized
  Content-Length: 126
  Content-Type: text/xml;charset=utf-8
  WWW-Authenticate: basic realm="Zope"
  <BLANKLINE>
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><string></string></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>

Parameters
----------

Of course, XML-RPC views can take parameters, too:

  >>> class ParameterDemo:
  ...     def __init__(self, context, request):
  ...         self.context = context
  ...         self.request = request
  ...
  ...     def add(self, first, second):
  ...         return first + second

Now we'll register it as a view:

  >>> from zope.configuration import xmlconfig
  >>> ignored = xmlconfig.string("""
  ... <configure
  ...     xmlns="http://namespaces.zope.org/zope"
  ...     xmlns:xmlrpc="http://namespaces.zope.org/xmlrpc"
  ...     >
  ...   <!-- We only need to do this include in this example,
  ...        Normally the include has already been done for us. -->
  ...   <include package="zope.app.publisher.xmlrpc" file="meta.zcml" />
  ...
  ...   <xmlrpc:view
  ...       for="zope.app.folder.folder.IFolder"
  ...       methods="add"
  ...       class="zope.app.publisher.xmlrpc.README.ParameterDemo"
  ...       permission="zope.ManageContent"
  ...       />
  ... </configure>
  ... """)

Then we can issue a remote procedure call with a parameter and get
back, surprise!, the sum:

  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 159
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>add</methodName>
  ... <params>
  ... <param><int>20</int></param>
  ... <param><int>22</int></param>
  ... </params>
  ... </methodCall>
  ... """, handle_errors=False)
  HTTP/1.0 200 Ok
  Content-Length: 122
  Content-Type: text/xml;charset=utf-8
  <BLANKLINE>
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><int>42</int></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>

Faults
------

If you need to raise an error, the prefered way to do it is via an
`xmlrpclib.Fault`:

  >>> import xmlrpclib

  >>> class FaultDemo:
  ...     def __init__(self, context, request):
  ...         self.context = context
  ...         self.request = request
  ...
  ...     def your_fault(self):
  ...         return xmlrpclib.Fault(42, "It's your fault!")

Now we'll register it as a view:

  >>> from zope.configuration import xmlconfig
  >>> ignored = xmlconfig.string("""
  ... <configure
  ...     xmlns="http://namespaces.zope.org/zope"
  ...     xmlns:xmlrpc="http://namespaces.zope.org/xmlrpc"
  ...     >
  ...   <!-- We only need to do this include in this example,
  ...        Normally the include has already been done for us. -->
  ...   <include package="zope.app.publisher.xmlrpc" file="meta.zcml" />
  ...
  ...   <xmlrpc:view
  ...       for="zope.app.folder.folder.IFolder"
  ...       methods="your_fault"
  ...       class="zope.app.publisher.xmlrpc.README.FaultDemo"
  ...       permission="zope.ManageContent"
  ...       />
  ... </configure>
  ... """)

Now, when we call it, we get a proper XML-RPC fault:

  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 104
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>your_fault</methodName>
  ... <params>
  ... </params>
  ... </methodCall>
  ... """, handle_errors=False)
  HTTP/1.0 200 Ok
  Content-Length: 272
  Content-Type: text/xml;charset=utf-8
  <BLANKLINE>
  <?xml version='1.0'?>
  <methodResponse>
  <fault>
  <value><struct>
  <member>
  <name>faultCode</name>
  <value><int>42</int></value>
  </member>
  <member>
  <name>faultString</name>
  <value><string>It's your fault!</string></value>
  </member>
  </struct></value>
  </fault>
  </methodResponse>
  <BLANKLINE>

DateTime values
---------------

Unfortunately, `xmlrpclib` does not support Python 2.3's new
`datetime.datetime` class (it should be made to, really).  DateTime
values need to be encoded as `xmlrpclib.DateTime` instances:

  >>> import xmlrpclib

  >>> class DateTimeDemo:
  ...     def __init__(self, context, request):
  ...         self.context = context
  ...         self.request = request
  ...
  ...     def epoch(self):
  ...         return xmlrpclib.DateTime("19700101T01:00:01")

Now we'll register it as a view:

  >>> from zope.configuration import xmlconfig
  >>> ignored = xmlconfig.string("""
  ... <configure
  ...     xmlns="http://namespaces.zope.org/zope"
  ...     xmlns:xmlrpc="http://namespaces.zope.org/xmlrpc"
  ...     >
  ...   <!-- We only need to do this include in this example,
  ...        Normally the include has already been done for us. -->
  ...   <include package="zope.app.publisher.xmlrpc" file="meta.zcml" />
  ...
  ...   <xmlrpc:view
  ...       for="zope.app.folder.folder.IFolder"
  ...       methods="epoch"
  ...       class="zope.app.publisher.xmlrpc.README.DateTimeDemo"
  ...       permission="zope.ManageContent"
  ...       />
  ... </configure>
  ... """)

Now, when we call it, we get a DateTime value

  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 100
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>epoch</methodName>
  ... <params>
  ... </params>
  ... </methodCall>
  ... """, handle_errors=False)
  HTTP/1.0 200 Ok
  Content-Length: 163
  Content-Type: text/xml;charset=utf-8
  <BLANKLINE>
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><dateTime.iso8601>19700101T01:00:01</dateTime.iso8601></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>
