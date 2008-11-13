====================
XMLRPC Introspection
====================

What's introspection now ?
--------------------------

This Zope 3 package provides an xmlrpcintrospection mechanism,
as defined here:

    http://xmlrpc-c.sourceforge.net/xmlrpc-howto/xmlrpc-howto-api-introspection.html

It registers three new xmlrpc methods:

    - `listMethods()`: Lists all xmlrpc methods (ie views) registered for the
      current object

    - `methodHelp(method_name)`: Returns the method documentation of the given
      method.

    - `methodSignature(method_name)`: Returns the method documentation of the
      given method.


How do I use it ?
-----------------

Basically, if you want to add introspection into your XMLRPCView, you just
have to add a decorator for each method of the view, that specifies the return
type of the method and the argument types.

The decorator is called `xmlrpccallable`

  >>> from zope.app.xmlrpcintrospection.xmlrpcintrospection import xmlrpccallable
  >>> from zope.app.publisher.xmlrpc import XMLRPCView
  >>> class MySuperXMLRPCView(XMLRPCView):
  ...     @xmlrpccallable(str, str, str, str)
  ...     def myMethod(self, a, b, c):
  ...         """ my help """
  ...         return '%s %s, %s, lalalala, you and me, lalalala' % (a, b, c)

`myMethod()` will then be introspectable. (find a full examples below, grep
for (*))


How does it works ?
-------------------

It is based on introspection mechanisms provided by the apidoc package.

***** ripped form xmlrpc doctests *****

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
  ...       class="zope.app.xmlrpcintrospection.README.FolderListing"
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
  HTTP/1.0 200 OK
  ...
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

***** end of ripped form xmlrpc doctests *****

Now we want to provide to that view introspection.
Let's add three new xmlrcp methods, that published
the introspection api.

  >>> ignored = xmlconfig.string("""
  ... <configure
  ...     xmlns="http://namespaces.zope.org/zope"
  ...     xmlns:xmlrpc="http://namespaces.zope.org/xmlrpc"
  ...     >
  ...   <!-- We only need to do this include in this example,
  ...        Normally the include has already been done for us. -->
  ...   <include package="zope.app.publisher.xmlrpc" file="meta.zcml" />
  ...   <xmlrpc:view
  ...     for="zope.interface.Interface"
  ...     methods="listMethods  methodHelp methodSignature"
  ...     class="zope.app.xmlrpcintrospection.xmlrpcintrospection.XMLRPCIntrospection"
  ...     permission="zope.Public"
  ...     />
  ... </configure>
  ... """)

They are linked to XMLRPCIntrospection class, that actually
 knows how to lookup to all interfaces

And call our xmlrpc method, that should list the content method:

  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>listMethods</methodName>
  ... <params>
  ... </params>
  ... </methodCall>
  ... """, handle_errors=False)
  HTTP/1.0 200 OK
  ...
  <?xml version='1.0'?>
  <methodResponse>
  ...
  <value><string>contents</string></value>
  ...
  </methodResponse>
  <BLANKLINE>

Let's try to add another method, to se if it gets listed...

  >>> class FolderListing2:
  ...     def contents2(self):
  ...         return list(self.context.keys())
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
  ...       methods="contents2"
  ...       class="zope.app.xmlrpcintrospection.README.FolderListing2"
  ...       permission="zope.ManageContent"
  ...       />
  ... </configure>
  ... """)
  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>listMethods</methodName>
  ... <params>
  ... </params>
  ... </methodCall>
  ... """, handle_errors=False)
  HTTP/1.0 200 OK
  ...
  <?xml version='1.0'?>
  <methodResponse>
  ...
  <value><string>contents</string></value>
  <value><string>contents2</string></value>
  ...
  </methodResponse>
  <BLANKLINE>

No we want to test methodHelp and methodSignature, to check that it returns,

    - The method doc

    - The list of attributes

In RPC, the list of attributes has to be return in an array of type:

[return type, param1 type, param2 type]

Since in Python we cannot have a static type for the method return type,
we introduce here a new mechanism based on a decorator, that let the xmlrpcview
developer add his own signature.

If the signature is not given, a defaut list is returned:

[None, None, None...]

The decorator append to the function objet two new parameters,
to get back the signature.

  >>> from zope.app.xmlrpcintrospection.xmlrpcintrospection import xmlrpccallable
  >>> class JacksonFiveRPC:
  ...     @xmlrpccallable(str, str, str, str)
  ...     def says(self, a, b, c):
  ...         return '%s %s, %s, lalalala, you and me, lalalala' % (a, b, c)

Let's try to get back the signature:

  >>> JacksonFiveRPC().says.return_type
  <type 'str'>
  >>> JacksonFiveRPC().says.parameters_types
  (<type 'str'>, <type 'str'>, <type 'str'>)

The method is still callable as needed:

  >>> JacksonFiveRPC().says('a', 'b', 'c')
  'a b, c, lalalala, you and me, lalalala'

Let's try out decorated and not decorated methods signatures (*):

  >>> class JacksonFiveRPC:
  ...     @xmlrpccallable(str, str, str, str)
  ...     def says(self, a, b, c):
  ...         return '%s %s, %s, lalalala, you and me, lalalala' % (a, b, c)
  ...     def says_not_decorated(self, a, b, c):
  ...         return '%s %s, %s, lalalala, you and me, lalalala' % (a, b, c)
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
  ...       methods="says says_not_decorated"
  ...       class="zope.app.xmlrpcintrospection.README.JacksonFiveRPC"
  ...       permission="zope.ManageContent"
  ...       />
  ... </configure>
  ... """)

Now let's try to get the signature for `says()`:

  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>methodSignature</methodName>
  ... <params>
  ... <param>
  ... <value>says</value>
  ... </param>
  ... </params>
  ... </methodCall>
  ... """, handle_errors=False)
  HTTP/1.0 200 OK
  ...
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><array><data>
  <value><array><data>
  <value><string>str</string></value>
  <value><string>str</string></value>
  <value><string>str</string></value>
  <value><string>str</string></value>
  </data></array></value>
  </data></array></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>

Now let's try to get the signature for says_not_decorated()`:

  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>methodSignature</methodName>
  ... <params>
  ... <param>
  ... <value>says_not_decorated</value>
  ... </param>
  ... </params>
  ... </methodCall>
  ... """, handle_errors=False)
  HTTP/1.0 200 OK
  ...
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><array><data>
  <value><array><data>
  <value><string>undef</string></value>
  <value><string>undef</string></value>
  <value><string>undef</string></value>
  <value><string>undef</string></value>
  </data></array></value>
  </data></array></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>

Last, but not least, the method help:

  >>> class JacksonFiveRPCDocumented:
  ...     @xmlrpccallable(str, str, str, str)
  ...     def says(self, a, b, c):
  ...         """ this is the help for
  ...             says()
  ...         """
  ...         return '%s %s, %s, lalalala, you and me, lalalala' % (a, b, c)
  ...     def says_not_documented(self, a, b, c):
  ...         return '%s %s, %s, lalalala, you and me, lalalala' % (a, b, c)
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
  ...       methods="says says_not_documented"
  ...       class="zope.app.xmlrpcintrospection.README.JacksonFiveRPCDocumented"
  ...       permission="zope.ManageContent"
  ...       />
  ... </configure>
  ... """)
  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>methodHelp</methodName>
  ... <params>
  ... <param>
  ... <value>says</value>
  ... </param>
  ... </params>
  ... </methodCall>
  ... """, handle_errors=False)
  HTTP/1.0 200 OK
  ...
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><string> this is the help for
               says()
           </string></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>
  >>> print http(r"""
  ... POST / HTTP/1.0
  ... Content-Type: text/xml
  ...
  ... <?xml version='1.0'?>
  ... <methodCall>
  ... <methodName>methodHelp</methodName>
  ... <params>
  ... <param>
  ... <value>says_not_documented</value>
  ... </param>
  ... </params>
  ... </methodCall>
  ... """, handle_errors=False)
  HTTP/1.0 200 OK
  ...
  <?xml version='1.0'?>
  <methodResponse>
  <params>
  <param>
  <value><string>undef</string></value>
  </param>
  </params>
  </methodResponse>
  <BLANKLINE>

